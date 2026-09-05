#!/usr/bin/env python3
"""Phase B: live capture -> detect -> score -> confidence-gated confirm UI.

Ties capture.py, detector.py, scoring.py, and confirm_ui.py together into one
runnable process. No platform (RabbitMQ/API Gateway) integration yet -- that
is Phase C. Run this on the machine with the phone on its local WiFi.

Requires env vars: VISION_CAMERA_URL, VISION_CALIBRATION_PATH,
VISION_BOARD_CENTER_X, VISION_BOARD_CENTER_Y (pixel location of the board
center in the camera's frame, used to pick the tip end of a new blob).

Usage:
    VISION_CAMERA_URL=http://192.168.1.50:8080/video \
    VISION_CALIBRATION_PATH=calibration/board1.json \
    VISION_BOARD_CENTER_X=512 VISION_BOARD_CENTER_Y=384 \
    python live_pipeline.py
"""

import logging
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vision_scoring.calibration import Calibration  # noqa: E402
from vision_scoring.capture import CaptureConfig, PhoneCameraCapture  # noqa: E402
from vision_scoring.config import VisionScoringConfig  # noqa: E402
from vision_scoring.confirm_state import ConfirmGate  # noqa: E402
from vision_scoring.confirm_ui import create_app  # noqa: E402
from vision_scoring.detector import DartLandingDetector  # noqa: E402
from vision_scoring.scoring import score_pixel  # noqa: E402

logger = logging.getLogger(__name__)


def run_capture_loop(config: VisionScoringConfig, gate: ConfirmGate) -> None:
    calibration = Calibration.load(config.calibration_path)
    detector = DartLandingDetector(board_center_px=config.board_center_px)
    capture = PhoneCameraCapture(CaptureConfig(url=config.camera_url))

    first_frame = None
    while first_frame is None:
        first_frame = capture.read()
        if first_frame is None:
            time.sleep(0.5)
    detector.set_reference_frame(first_frame)
    logger.info("Reference frame captured; watching for darts.")

    while True:
        frame = capture.read()
        if frame is None:
            continue

        landing = detector.process_frame(frame)
        if landing is None:
            continue

        result = score_pixel(calibration, landing.tip_pixel)
        pending = gate.submit(result)
        logger.info(
            "Detected throw %s: score=%s multiplier=%s confidence=%.2f -> %s",
            pending.throw_id,
            result.score,
            result.multiplier,
            result.confidence,
            pending.status.value,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = VisionScoringConfig.from_env()
    gate = ConfirmGate(
        confidence_threshold=config.confidence_threshold, countdown_seconds=config.countdown_seconds
    )

    capture_thread = threading.Thread(target=run_capture_loop, args=(config, gate), daemon=True)
    capture_thread.start()

    app = create_app(gate)
    app.run(host=config.confirm_ui_host, port=config.confirm_ui_port)


if __name__ == "__main__":
    main()
