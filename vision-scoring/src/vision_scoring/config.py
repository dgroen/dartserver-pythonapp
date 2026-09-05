"""Env-driven configuration for the Phase B live pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VisionScoringConfig:
    camera_url: str
    calibration_path: Path
    board_center_px: tuple[float, float]
    confidence_threshold: float = 0.6
    countdown_seconds: float = 3.0
    confirm_ui_host: str = "0.0.0.0"
    confirm_ui_port: int = 5900

    @classmethod
    def from_env(cls) -> "VisionScoringConfig":
        return cls(
            camera_url=_require_env("VISION_CAMERA_URL"),
            calibration_path=Path(_require_env("VISION_CALIBRATION_PATH")),
            board_center_px=(
                float(os.environ.get("VISION_BOARD_CENTER_X", "0")),
                float(os.environ.get("VISION_BOARD_CENTER_Y", "0")),
            ),
            confidence_threshold=float(os.environ.get("VISION_CONFIDENCE_THRESHOLD", "0.6")),
            countdown_seconds=float(os.environ.get("VISION_COUNTDOWN_SECONDS", "3.0")),
            confirm_ui_host=os.environ.get("VISION_CONFIRM_UI_HOST", "0.0.0.0"),
            confirm_ui_port=int(os.environ.get("VISION_CONFIRM_UI_PORT", "5900")),
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value
