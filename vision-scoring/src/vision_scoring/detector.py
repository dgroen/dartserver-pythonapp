"""Frame-diff dart-landing detection.

Maintains a reference ("board is at rest") frame and, on each new frame,
looks for a newly-appeared blob (a dart shaft/flight) via absolute
difference + thresholding. A landing is only reported once the new blob has
held stable (no further change) for a short settle window, which avoids
reading a dart mid-flight/mid-wobble as if it had already landed.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Landing:
    tip_pixel: tuple[float, float]
    blob_area: float


class DartLandingDetector:
    def __init__(
        self,
        board_center_px: tuple[float, float],
        diff_threshold: int = 30,
        min_blob_area: float = 40.0,
        settle_frames: int = 3,
    ):
        """
        Args:
            board_center_px: pixel location of the board center, used to pick
                the tip end of a new blob (the end closest to center).
            diff_threshold: pixel-intensity difference (0-255) above which a
                pixel is considered "changed" versus the reference frame.
            min_blob_area: minimum contour area (px^2) to be treated as a
                dart rather than noise/lighting flicker.
            settle_frames: number of consecutive frames a candidate blob must
                remain essentially unchanged before it's reported as landed.
        """
        self._board_center_px = board_center_px
        self._diff_threshold = diff_threshold
        self._min_blob_area = min_blob_area
        self._settle_frames = settle_frames

        self._reference_gray: np.ndarray | None = None
        self._pending_tip: tuple[float, float] | None = None
        self._pending_area: float = 0.0
        self._stable_count: int = 0

    def set_reference_frame(self, frame_bgr: np.ndarray) -> None:
        """(Re-)baseline against a dart-free frame. Call at startup and again
        after all darts are pulled from the board each round."""
        self._reference_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        self._pending_tip = None
        self._stable_count = 0

    def process_frame(self, frame_bgr: np.ndarray) -> Landing | None:
        """Feed one new frame in. Returns a Landing once a new dart has been
        stably detected, otherwise None. Call set_reference_frame() first."""
        if self._reference_gray is None:
            raise RuntimeError("set_reference_frame() must be called before process_frame()")

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray, self._reference_gray)
        _, thresholded = cv2.threshold(diff, self._diff_threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidate = self._largest_contour_above_min_area(contours)
        if candidate is None:
            self._pending_tip = None
            self._stable_count = 0
            return None

        area = cv2.contourArea(candidate)
        tip = self._tip_nearest_center(candidate)

        if self._pending_tip is not None and self._is_same_blob(tip, self._pending_tip):
            self._stable_count += 1
        else:
            self._stable_count = 1

        self._pending_tip = tip
        self._pending_area = area

        if self._stable_count >= self._settle_frames:
            landing = Landing(tip_pixel=tip, blob_area=area)
            self._pending_tip = None
            self._stable_count = 0
            return landing

        return None

    def _largest_contour_above_min_area(self, contours) -> np.ndarray | None:
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < self._min_blob_area:
            return None
        return largest

    def _tip_nearest_center(self, contour: np.ndarray) -> tuple[float, float]:
        points = contour.reshape(-1, 2).astype(np.float64)
        cx, cy = self._board_center_px
        distances = np.hypot(points[:, 0] - cx, points[:, 1] - cy)
        nearest = points[np.argmin(distances)]
        return float(nearest[0]), float(nearest[1])

    @staticmethod
    def _is_same_blob(
        a: tuple[float, float], b: tuple[float, float], tolerance_px: float = 8.0
    ) -> bool:
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 <= tolerance_px**2
