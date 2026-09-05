import numpy as np
import pytest
from vision_scoring.calibration import Calibration, compute_homography


def _synthetic_calibration() -> Calibration:
    # A simple synthetic mapping: pixel space scaled by 0.5 and offset, no
    # rotation/perspective, just enough to exercise the homography math with
    # known ground truth.
    board_mm = [(-170.0, 0.0), (170.0, 0.0), (0.0, -170.0), (0.0, 170.0)]
    pixel_px = [(-340.0, 0.0), (340.0, 0.0), (0.0, -340.0), (0.0, 340.0)]
    return compute_homography("test-board", pixel_px, board_mm)


def test_compute_homography_round_trip():
    calibration = _synthetic_calibration()
    x_mm, y_mm = calibration.pixel_to_board_mm((340.0, 0.0))
    assert x_mm == pytest.approx(170.0, abs=1e-6)
    assert y_mm == pytest.approx(0.0, abs=1e-6)


def test_compute_homography_requires_four_points():
    with pytest.raises(ValueError):
        compute_homography("test-board", [(0, 0), (1, 1)], [(0, 0), (1, 1)])


def test_board_center_px_derived_from_offset_homography():
    # Board center (0,0 mm) sits at pixel (500, 400) here -- an off-center
    # camera framing, unlike the origin-centered synthetic calibration above.
    board_mm = [(-170.0, 0.0), (170.0, 0.0), (0.0, -170.0), (0.0, 170.0)]
    pixel_px = [(160.0, 400.0), (840.0, 400.0), (500.0, 60.0), (500.0, 740.0)]
    calibration = compute_homography("test-board", pixel_px, board_mm)

    x_px, y_px = calibration.board_center_px()
    assert x_px == pytest.approx(500.0, abs=1e-6)
    assert y_px == pytest.approx(400.0, abs=1e-6)


def test_calibration_save_and_load_round_trip(tmp_path):
    calibration = _synthetic_calibration()
    path = tmp_path / "board1.json"
    calibration.save(path)

    loaded = Calibration.load(path)
    assert loaded.board_id == calibration.board_id
    assert np.allclose(loaded.homography, calibration.homography)

    x_mm, y_mm = loaded.pixel_to_board_mm((340.0, 0.0))
    assert x_mm == pytest.approx(170.0, abs=1e-6)
