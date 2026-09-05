import cv2
import numpy as np
import pytest
from vision_scoring.calibration import compute_homography
from vision_scoring.sessions import SessionManager


def _blank_frame(size: int = 200) -> np.ndarray:
    return np.full((size, size, 3), 200, dtype=np.uint8)


def _frame_with_dot(center_xy: tuple[int, int], size: int = 200, radius: int = 6) -> np.ndarray:
    frame = _blank_frame(size)
    cv2.circle(frame, center_xy, radius, (0, 0, 0), thickness=-1)
    return frame


def _calibration():
    # Board center at pixel (100, 100), 1mm == 1px, no rotation. Pixel-y top
    # of frame (10) is physically "up" -> positive board-plane mm y.
    board_mm = [(-90.0, 0.0), (90.0, 0.0), (0.0, 90.0), (0.0, -90.0)]
    pixel_px = [(10.0, 100.0), (190.0, 100.0), (100.0, 10.0), (100.0, 190.0)]
    return compute_homography("board1", pixel_px, board_mm)


def test_process_frame_before_calibration_raises(tmp_path):
    manager = SessionManager(calibration_dir=tmp_path)
    with pytest.raises(RuntimeError):
        manager.process_frame("board1", _blank_frame())


def test_process_frame_before_reference_frame_raises(tmp_path):
    manager = SessionManager(calibration_dir=tmp_path)
    manager.set_calibration("board1", _calibration())
    with pytest.raises(RuntimeError):
        manager.process_frame("board1", _blank_frame())


def test_full_flow_detects_and_scores_a_throw(tmp_path):
    manager = SessionManager(calibration_dir=tmp_path, confidence_threshold=0.0)
    manager.set_calibration("board1", _calibration())
    manager.set_reference_frame("board1", _blank_frame())

    dart_frame = _frame_with_dot((100, 40))  # straight up from center -> segment 20

    assert manager.process_frame("board1", dart_frame) is None  # settling
    assert manager.process_frame("board1", dart_frame) is None  # settling
    pending = manager.process_frame("board1", dart_frame)  # stable -> landing

    assert pending is not None
    assert pending.result.segment == 20


def test_calibration_persists_across_session_managers(tmp_path):
    manager = SessionManager(calibration_dir=tmp_path)
    manager.set_calibration("board1", _calibration())

    reloaded = SessionManager(calibration_dir=tmp_path)
    session = reloaded.get_or_create("board1")
    assert session.is_calibrated()


def test_on_resolved_receives_correct_board_id(tmp_path):
    resolved = []
    manager = SessionManager(
        calibration_dir=tmp_path,
        confidence_threshold=0.0,
        countdown_seconds=0.0,
        on_resolved=lambda board_id, pending: resolved.append((board_id, pending.throw_id)),
    )
    manager.set_calibration("board1", _calibration())
    manager.set_reference_frame("board1", _blank_frame())

    dart_frame = _frame_with_dot((100, 40))
    manager.process_frame("board1", dart_frame)
    manager.process_frame("board1", dart_frame)
    pending = manager.process_frame("board1", dart_frame)

    manager.tick("board1")  # countdown_seconds=0.0 -> auto-accepts immediately

    assert resolved == [("board1", pending.throw_id)]


def test_pending_ticks_before_returning(tmp_path):
    manager = SessionManager(
        calibration_dir=tmp_path, confidence_threshold=0.0, countdown_seconds=0.0
    )
    manager.set_calibration("board1", _calibration())
    manager.set_reference_frame("board1", _blank_frame())

    dart_frame = _frame_with_dot((100, 40))
    manager.process_frame("board1", dart_frame)
    manager.process_frame("board1", dart_frame)
    pending = manager.process_frame("board1", dart_frame)
    assert pending is not None

    # confidence_threshold=0.0 and countdown_seconds=0.0 -> should auto-accept
    # essentially immediately once pending() calls tick().
    assert manager.pending("board1") == []
