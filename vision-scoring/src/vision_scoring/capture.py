"""Phone camera ingestion via MJPEG-over-WiFi (e.g. an "IP Webcam"-style app).

Deliberately thin: cv2.VideoCapture already understands MJPEG/HTTP streams,
so this module's job is just lifecycle management (open/close/reconnect) and
giving the rest of the pipeline something it can unit test against (a
FrameSource protocol) without needing a real camera or network.
"""

import logging
import time
from dataclasses import dataclass
from typing import Protocol

import numpy as np

logger = logging.getLogger(__name__)


class FrameSource(Protocol):
    def read(self) -> np.ndarray | None: ...

    def release(self) -> None: ...


@dataclass
class CaptureConfig:
    url: str
    reconnect_delay_seconds: float = 2.0
    max_consecutive_failures_before_reconnect: int = 5


class PhoneCameraCapture:
    """Wraps cv2.VideoCapture(url) with basic reconnect-on-failure handling."""

    def __init__(self, config: CaptureConfig):
        self._config = config
        self._capture = None
        self._consecutive_failures = 0
        self._open()

    def _open(self) -> None:
        import cv2

        logger.info("Opening camera stream: %s", self._config.url)
        self._capture = cv2.VideoCapture(self._config.url)
        self._consecutive_failures = 0

    def read(self) -> np.ndarray | None:
        if self._capture is None:
            self._open()

        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._consecutive_failures += 1
            logger.warning(
                "Failed to read frame (%d consecutive failures)", self._consecutive_failures
            )
            if self._consecutive_failures >= self._config.max_consecutive_failures_before_reconnect:
                self.release()
                time.sleep(self._config.reconnect_delay_seconds)
                self._open()
            return None

        self._consecutive_failures = 0
        return frame

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self) -> "PhoneCameraCapture":
        return self

    def __exit__(self, *_exc_info) -> None:
        self.release()
