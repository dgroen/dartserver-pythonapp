from vision_scoring.board_model import Ring, ScoreResult
from vision_scoring.calibration import compute_homography
from vision_scoring.scoring import score_pixel, to_throw_payload


def test_to_throw_payload_normalizes_miss_to_single_zero():
    miss = ScoreResult(score=0, multiplier="MISS", ring=Ring.MISS, segment=None, confidence=1.0)
    assert to_throw_payload(miss) == {"score": 0, "multiplier": "SINGLE"}


def test_to_throw_payload_passes_through_normal_scores():
    triple_20 = ScoreResult(
        score=20, multiplier="TRIPLE", ring=Ring.TRIPLE, segment=20, confidence=0.9
    )
    assert to_throw_payload(triple_20) == {"score": 20, "multiplier": "TRIPLE"}


def test_score_pixel_combines_calibration_and_board_model():
    board_mm = [(-170.0, 0.0), (170.0, 0.0), (0.0, -170.0), (0.0, 170.0)]
    pixel_px = [(-340.0, 0.0), (340.0, 0.0), (0.0, -340.0), (0.0, 340.0)]
    calibration = compute_homography("test-board", pixel_px, board_mm)

    result = score_pixel(calibration, (0.0, -300.0))
    assert result.multiplier == "SINGLE"
    assert result.score in range(1, 21)
