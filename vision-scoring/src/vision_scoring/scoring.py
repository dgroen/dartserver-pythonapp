"""Combine a calibration and the board model to score a detected dart-tip pixel."""

from vision_scoring.board_model import ScoreResult, score_at
from vision_scoring.calibration import Calibration


def score_pixel(calibration: Calibration, tip_pixel_xy: tuple[float, float]) -> ScoreResult:
    """Map a dart-tip pixel coordinate to a {"score","multiplier"} result."""
    x_mm, y_mm = calibration.pixel_to_board_mm(tip_pixel_xy)
    return score_at(x_mm, y_mm)


def to_throw_payload(result: ScoreResult) -> dict:
    """Shape expected by GameManager.process_score / the existing platform."""
    return {"score": result.score, "multiplier": result.multiplier}
