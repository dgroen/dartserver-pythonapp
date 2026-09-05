"""Per-board session state for the HTTP-driven vision-scoring server.

Unlike the old local-loop design, this service has no continuous camera feed
of its own: the platform's web app (browser-driven) posts frames one at a
time, identified by board_id, so state (calibration + detector + pending
throws) must be kept here between requests, keyed by board_id.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from vision_scoring.calibration import Calibration
from vision_scoring.confirm_state import ConfirmGate, PendingThrow
from vision_scoring.detector import DartLandingDetector, Landing
from vision_scoring.scoring import score_pixel

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VisionSession:
    board_id: str
    calibration: Calibration | None = None
    detector: DartLandingDetector | None = None
    gate: ConfirmGate = field(default_factory=ConfirmGate)

    def is_calibrated(self) -> bool:
        return self.calibration is not None

    def has_reference_frame(self) -> bool:
        return self.detector is not None


class SessionManager:
    def __init__(
        self,
        calibration_dir: Path,
        confidence_threshold: float = 0.6,
        countdown_seconds: float = 3.0,
        on_resolved=None,
    ):
        """
        Args:
            on_resolved: called as on_resolved(board_id, pending_throw) whenever
                any board's session resolves a throw (auto-accept, confirm, or
                correct). Each session's ConfirmGate gets its own closure
                binding its board_id, since ConfirmGate itself only knows
                about a single board's throws.
        """
        self._calibration_dir = calibration_dir
        self._confidence_threshold = confidence_threshold
        self._countdown_seconds = countdown_seconds
        self._on_resolved = on_resolved
        self._sessions: dict[str, VisionSession] = {}

    def get_or_create(self, board_id: str) -> VisionSession:
        if board_id not in self._sessions:
            session = VisionSession(
                board_id=board_id,
                gate=ConfirmGate(
                    confidence_threshold=self._confidence_threshold,
                    countdown_seconds=self._countdown_seconds,
                    on_resolved=self._bind_board_id(board_id),
                ),
            )
            calibration_path = self._calibration_path(board_id)
            if calibration_path.exists():
                session.calibration = Calibration.load(calibration_path)
            self._sessions[board_id] = session
        return self._sessions[board_id]

    def set_calibration(self, board_id: str, calibration: Calibration) -> None:
        session = self.get_or_create(board_id)
        session.calibration = calibration
        session.detector = None  # a new calibration invalidates any reference frame
        calibration.save(self._calibration_path(board_id))

    def set_reference_frame(self, board_id: str, frame: "np.ndarray") -> None:
        session = self.get_or_create(board_id)
        if session.calibration is None:
            raise RuntimeError(f"Board '{board_id}' is not calibrated yet")

        if session.detector is None:
            session.detector = DartLandingDetector(
                board_center_px=session.calibration.board_center_px()
            )
        session.detector.set_reference_frame(frame)

    def process_frame(self, board_id: str, frame: "np.ndarray") -> PendingThrow | None:
        session = self.get_or_create(board_id)
        if session.calibration is None:
            raise RuntimeError(f"Board '{board_id}' is not calibrated yet")
        if session.detector is None:
            raise RuntimeError(f"Board '{board_id}' has no reference frame yet")

        landing: Landing | None = session.detector.process_frame(frame)
        if landing is None:
            return None

        result = score_pixel(session.calibration, landing.tip_pixel)
        pending = session.gate.submit(result)
        logger.info(
            "Board %s: throw %s detected score=%s multiplier=%s confidence=%.2f -> %s",
            board_id,
            pending.throw_id,
            result.score,
            result.multiplier,
            result.confidence,
            pending.status.value,
        )
        return pending

    def tick(self, board_id: str) -> list[PendingThrow]:
        return self.get_or_create(board_id).gate.tick()

    def tick_all(self) -> None:
        for session in self._sessions.values():
            session.gate.tick()

    def pending(self, board_id: str) -> list[PendingThrow]:
        self.tick(board_id)
        return self.get_or_create(board_id).gate.pending()

    def confirm(self, board_id: str, throw_id: str) -> PendingThrow:
        return self.get_or_create(board_id).gate.confirm(throw_id)

    def correct(self, board_id: str, throw_id: str, corrected_result) -> PendingThrow:
        return self.get_or_create(board_id).gate.correct(throw_id, corrected_result)

    def cancel(self, board_id: str, throw_id: str) -> PendingThrow:
        return self.get_or_create(board_id).gate.cancel(throw_id)

    def _calibration_path(self, board_id: str) -> Path:
        return self._calibration_dir / f"{board_id}.json"

    def _bind_board_id(self, board_id: str):
        if self._on_resolved is None:
            return None
        return lambda pending: self._on_resolved(board_id, pending)
