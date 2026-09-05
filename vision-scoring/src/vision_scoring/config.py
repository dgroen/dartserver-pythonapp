"""Env-driven configuration for the vision-scoring internal HTTP server.

This service has no direct camera access: frames arrive via HTTP POST from
the platform's own web app (which the browser talks to), one board/session
at a time, identified by board_id. See sessions.py and server.py.
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VisionScoringConfig:
    host: str = "0.0.0.0"
    port: int = 5901
    calibration_dir: Path = Path("calibration")
    confidence_threshold: float = 0.6
    countdown_seconds: float = 3.0
    # Publisher settings: submits resolved throws to the platform's API
    # Gateway (POST /api/v1/vision/throw). Left unset disables publishing
    # (resolved throws are logged only) -- useful for local dev without a
    # full platform stack running.
    gateway_client_id: str | None = None
    gateway_client_secret: str | None = None
    gateway_token_url: str | None = None
    gateway_url: str | None = None
    gateway_verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "VisionScoringConfig":
        return cls(
            host=os.environ.get("VISION_HOST", "0.0.0.0"),
            port=int(os.environ.get("VISION_PORT", "5901")),
            calibration_dir=Path(os.environ.get("VISION_CALIBRATION_DIR", "calibration")),
            confidence_threshold=float(os.environ.get("VISION_CONFIDENCE_THRESHOLD", "0.6")),
            countdown_seconds=float(os.environ.get("VISION_COUNTDOWN_SECONDS", "3.0")),
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
