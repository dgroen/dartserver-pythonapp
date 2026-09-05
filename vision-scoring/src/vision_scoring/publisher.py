"""OAuth2 client-credentials publisher: posts accepted throws to the API Gateway.

Mirrors the authentication flow used by scripts/dartboard_simulator.py
(the electronic-dartboard test client) against the platform's API Gateway,
just targeting the new /api/v1/vision/throw endpoint with the vision:write
scope instead of dartboard:write.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
from vision_scoring.board_model import ScoreResult
from vision_scoring.scoring import to_throw_payload

logger = logging.getLogger(__name__)


@dataclass
class PublisherConfig:
    client_id: str
    client_secret: str
    token_url: str
    gateway_url: str
    verify_ssl: bool = True
    request_timeout_seconds: float = 10.0


class VisionThrowPublisher:
    def __init__(self, config: PublisherConfig):
        self._config = config
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    def _get_access_token(self) -> bool:
        try:
            response = requests.post(
                self._config.token_url,
                auth=(self._config.client_id, self._config.client_secret),
                data={"grant_type": "client_credentials", "scope": "vision:write"},
                verify=self._config.verify_ssl,
                timeout=self._config.request_timeout_seconds,
            )
        except requests.RequestException:
            logger.exception("Error obtaining access token")
            return False

        if response.status_code != 200:
            logger.error(
                "Failed to obtain access token: %s %s", response.status_code, response.text
            )
            return False

        token_data = response.json()
        self._access_token = token_data["access_token"]
        # Refresh 60 seconds before expiration.
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=token_data["expires_in"] - 60
        )
        return True

    def _ensure_valid_token(self) -> bool:
        if not self._access_token or datetime.now(timezone.utc) >= self._token_expires_at:
            return self._get_access_token()
        return True

    def publish(
        self,
        result: ScoreResult,
        session_id: str | None = None,
        board_id: str | None = None,
        confirmed_by_human: bool = False,
        max_retries: int = 3,
    ) -> bool:
        """Submit an accepted throw result to the API Gateway. Returns True on success."""
        payload = {
            **to_throw_payload(result),
            "confidence": result.confidence,
            "sessionId": session_id,
            "boardId": board_id,
            "confirmedByHuman": confirmed_by_human,
        }

        for attempt in range(max_retries):
            if not self._ensure_valid_token():
                logger.warning("Failed to obtain a valid token (attempt %d)", attempt + 1)
                continue

            try:
                response = requests.post(
                    f"{self._config.gateway_url}/api/v1/vision/throw",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    verify=self._config.verify_ssl,
                    timeout=self._config.request_timeout_seconds,
                )
            except requests.RequestException:
                logger.exception("Error submitting throw (attempt %d)", attempt + 1)
                continue

            if response.status_code == 201:
                return True
            if response.status_code == 401:
                # Token expired/rejected; force a refresh and retry.
                self._access_token = None
                continue

            logger.error("Failed to submit throw: %s %s", response.status_code, response.text)
            return False

        logger.error("Max retries exceeded submitting throw: %s", payload)
        return False
