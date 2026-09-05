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
    board_id: str | None = None
    # Publisher settings (Phase C). Left unset in Phase B usage (no platform
    # wiring), required once live_pipeline.py is run with publishing enabled.
    gateway_client_id: str | None = None
    gateway_client_secret: str | None = None
    gateway_token_url: str | None = None
    gateway_url: str | None = None
    gateway_verify_ssl: bool = True

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
            board_id=os.environ.get("VISION_BOARD_ID"),
            gateway_client_id=os.environ.get("VISION_GATEWAY_CLIENT_ID"),
            gateway_client_secret=os.environ.get("VISION_GATEWAY_CLIENT_SECRET"),
            gateway_token_url=os.environ.get("VISION_GATEWAY_TOKEN_URL"),
            gateway_url=os.environ.get("VISION_GATEWAY_URL"),
            gateway_verify_ssl=os.environ.get("VISION_GATEWAY_VERIFY_SSL", "true").lower()
            == "true",
        )

    def publishing_enabled(self) -> bool:
        return bool(
            self.gateway_client_id
            and self.gateway_client_secret
            and self.gateway_token_url
            and self.gateway_url
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value
