#!/usr/bin/env python3
"""Live capture -> detect -> score -> confidence-gated confirm -> (Phase C) publish.

Ties capture.py, detector.py, scoring.py, confirm_ui.py, and (when configured)
publisher.py together into one runnable process. Run this on the machine
with the phone on its local WiFi.

Publishing to the Dartserver API Gateway is optional: if the
VISION_GATEWAY_* env vars are not set, resolved throws are logged only (this
is how Phase B was exercised, with no platform wiring). Set them to also
submit accepted/corrected throws to /api/v1/vision/throw (Phase C).

Requires env vars: VISION_CAMERA_URL, VISION_CALIBRATION_PATH,
VISION_BOARD_CENTER_X, VISION_BOARD_CENTER_Y (pixel location of the board
center in the camera's frame, used to pick the tip end of a new blob).

Usage:
    VISION_CAMERA_URL=http://192.168.1.50:8080/video \
    VISION_CALIBRATION_PATH=calibration/board1.json \
    VISION_BOARD_CENTER_X=512 VISION_BOARD_CENTER_Y=384 \
    VISION_GATEWAY_CLIENT_ID=... VISION_GATEWAY_CLIENT_SECRET=... \
    VISION_GATEWAY_TOKEN_URL=https://wso2is/oauth2/token \
    VISION_GATEWAY_URL=https://api-gateway \
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
from vision_scoring.confirm_state import ConfirmGate, PendingThrow  # noqa: E402
from vision_scoring.confirm_ui import create_app  # noqa: E402
from vision_scoring.detector import DartLandingDetector  # noqa: E402
from vision_scoring.publisher import PublisherConfig, VisionThrowPublisher  # noqa: E402
from vision_scoring.scoring import score_pixel  # noqa: E402

logger = logging.getLogger(__name__)


def _make_publish_callback(config: VisionScoringConfig):
    if not config.publishing_enabled():
        logger.warning(
            "VISION_GATEWAY_* env vars not fully set; resolved throws will be logged only "
            "(not published to the Dartserver API Gateway)."
        )
        return lambda pending: None

    publisher = VisionThrowPublisher(
        PublisherConfig(
            client_id=config.gateway_client_id,
            client_secret=config.gateway_client_secret,
            token_url=config.gateway_token_url,
            gateway_url=config.gateway_url,
            verify_ssl=config.gateway_verify_ssl,
        )
    )

    def publish(pending: PendingThrow) -> None:
        confirmed_by_human = pending.status.value == "CORRECTED"
        success = publisher.publish(
            pending.final_result,
            board_id=config.board_id,
            confirmed_by_human=confirmed_by_human,
        )
        if not success:
            logger.error("Failed to publish resolved throw %s", pending.throw_id)

    return publish


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


def run_ticker_loop(gate: ConfirmGate, interval_seconds: float = 0.5) -> None:
    """Periodically calls gate.tick() so a countdown auto-accepts (and
    publishes) even if no one is actively polling the confirm UI."""
    while True:
        gate.tick()
        time.sleep(interval_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = VisionScoringConfig.from_env()
    gate = ConfirmGate(
        confidence_threshold=config.confidence_threshold,
        countdown_seconds=config.countdown_seconds,
        on_resolved=_make_publish_callback(config),
    )

    threading.Thread(target=run_capture_loop, args=(config, gate), daemon=True).start()
    threading.Thread(target=run_ticker_loop, args=(gate,), daemon=True).start()

    app = create_app(gate)
    app.run(host=config.confirm_ui_host, port=config.confirm_ui_port)


if __name__ == "__main__":
    main()
