"""Camera calibration: maps camera pixel coordinates to board-plane millimeters.

The phone camera is off-axis (not a top-down view), so a homography is used to
rectify the perspective. Two ways to obtain the reference points that the
homography is computed from:

  * ``auto_detect_reference_points`` - attempts to locate the board's outer
    double-ring edge automatically (Phase B/C; not yet implemented -- returns
    None so callers fall back to manual points).
  * manual reference points - the operator supplies known board-plane
    positions (e.g. the outer edge of the double ring at the 20/3/11/6
    segment boundaries) and their corresponding pixel locations in a
    reference photo. This is always available as a correction/fallback path,
    per the project's calibration design (auto-detect first, manual nudge
    always possible).

A calibration is specific to one physical board + camera position and is
persisted to a small JSON file so it does not need to be redone every session.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from vision_scoring.board_model import RADIUS_DOUBLE_OUTER_MM


@dataclass
class Calibration:
    board_id: str
    homography: np.ndarray  # 3x3, maps pixel (x, y, 1) -> board-plane mm (x, y, w)
    reference_points_px: list[tuple[float, float]] = field(default_factory=list)
    reference_points_mm: list[tuple[float, float]] = field(default_factory=list)

    def pixel_to_board_mm(self, pixel_xy: tuple[float, float]) -> tuple[float, float]:
        px = np.array([[pixel_xy]], dtype=np.float64)  # shape (1, 1, 2)
        mapped = cv2.perspectiveTransform(px, self.homography)
        x_mm, y_mm = mapped[0, 0]
        return float(x_mm), float(y_mm)

    def board_center_px(self) -> tuple[float, float]:
        """Pixel location of the board center (board-plane mm (0, 0)), used by
        the detector to pick the tip end of a new blob. Derived from the
        homography's inverse rather than a separately-entered value."""
        inverse_homography = np.linalg.inv(self.homography)
        origin_mm = np.array([[(0.0, 0.0)]], dtype=np.float64)
        mapped = cv2.perspectiveTransform(origin_mm, inverse_homography)
        x_px, y_px = mapped[0, 0]
        return float(x_px), float(y_px)

    def to_json(self) -> dict:
        return {
            "board_id": self.board_id,
            "homography": self.homography.tolist(),
            "reference_points_px": self.reference_points_px,
            "reference_points_mm": self.reference_points_mm,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Calibration":
        return cls(
            board_id=data["board_id"],
            homography=np.array(data["homography"], dtype=np.float64),
            reference_points_px=[tuple(p) for p in data.get("reference_points_px", [])],
            reference_points_mm=[tuple(p) for p in data.get("reference_points_mm", [])],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2))

    @classmethod
    def load(cls, path: Path) -> "Calibration":
        return cls.from_json(json.loads(path.read_text()))


def compute_homography(
    board_id: str,
    reference_points_px: list[tuple[float, float]],
    reference_points_mm: list[tuple[float, float]],
) -> Calibration:
    """Compute a homography from >=4 matched (pixel, board-plane mm) point pairs."""
    if len(reference_points_px) < 4 or len(reference_points_px) != len(reference_points_mm):
        raise ValueError("Need >=4 matched reference points to compute a homography")

    src = np.array(reference_points_px, dtype=np.float64)
    dst = np.array(reference_points_mm, dtype=np.float64)
    homography, _mask = cv2.findHomography(src, dst, method=0)
    if homography is None:
        raise ValueError("Homography computation failed for the given reference points")

    return Calibration(
        board_id=board_id,
        homography=homography,
        reference_points_px=list(reference_points_px),
        reference_points_mm=list(reference_points_mm),
    )


def auto_detect_reference_points(image: "np.ndarray") -> list[tuple[float, float]] | None:
    """Attempt to auto-detect the outer double-ring edge in a rectified-ish frame.

    Not yet implemented (Phase B/C work) -- returns None so callers always
    fall back to manual reference-point entry, which remains the primary,
    always-available calibration path for the PoC.
    """
    return None


def standard_reference_points_mm(num_points: int = 4) -> list[tuple[float, float]]:
    """Board-plane mm positions of `num_points` evenly-spaced points on the
    outer double-ring edge, useful as manual-calibration click targets."""
    import math

    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = RADIUS_DOUBLE_OUTER_MM * math.sin(angle)
        y = RADIUS_DOUBLE_OUTER_MM * math.cos(angle)
        points.append((x, y))
    return points
