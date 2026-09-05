import numpy as np
from vision_scoring.detector import DartLandingDetector


def _blank_frame(size: int = 200) -> np.ndarray:
    return np.full((size, size, 3), 200, dtype=np.uint8)


def _frame_with_dot(center_xy: tuple[int, int], size: int = 200, radius: int = 6) -> np.ndarray:
    import cv2

    frame = _blank_frame(size)
    cv2.circle(frame, center_xy, radius, (0, 0, 0), thickness=-1)
    return frame


def _board_center(size: int = 200) -> tuple[float, float]:
    return size / 2, size / 2


def test_no_landing_on_unchanged_frames():
    size = 200
    detector = DartLandingDetector(board_center_px=_board_center(size), settle_frames=3)
    detector.set_reference_frame(_blank_frame(size))

    for _ in range(5):
        assert detector.process_frame(_blank_frame(size)) is None


def test_landing_reported_after_settle_frames():
    size = 200
    detector = DartLandingDetector(board_center_px=_board_center(size), settle_frames=3)
    detector.set_reference_frame(_blank_frame(size))

    dart_frame = _frame_with_dot((120, 80), size=size)

    assert detector.process_frame(dart_frame) is None  # frame 1: not yet stable
    assert detector.process_frame(dart_frame) is None  # frame 2: not yet stable
    landing = detector.process_frame(dart_frame)  # frame 3: stable
    assert landing is not None
    # Tip is the point of the blob nearest the board center, not the blob's
    # own centroid, so it should sit within one dot-radius of (120, 80).
    distance_from_dot_center = (landing.tip_pixel[0] - 120) ** 2 + (landing.tip_pixel[1] - 80) ** 2
    assert distance_from_dot_center <= 8**2


def test_landing_reset_after_reference_frame_rebaseline():
    size = 200
    detector = DartLandingDetector(board_center_px=_board_center(size), settle_frames=2)
    detector.set_reference_frame(_blank_frame(size))

    dart_frame = _frame_with_dot((90, 150), size=size)
    detector.process_frame(dart_frame)
    landing = detector.process_frame(dart_frame)
    assert landing is not None

    # Re-baseline against a frame that now includes the dart (simulating the
    # dart staying in the board); subsequent identical frames should not
    # re-report the same dart as a new landing.
    detector.set_reference_frame(dart_frame)
    assert detector.process_frame(dart_frame) is None
    assert detector.process_frame(dart_frame) is None


def test_transient_noise_does_not_trigger_landing():
    size = 200
    detector = DartLandingDetector(board_center_px=_board_center(size), settle_frames=3)
    detector.set_reference_frame(_blank_frame(size))

    # A blob appears for one frame then vanishes (e.g. lighting flicker) --
    # should never accumulate enough stable frames to report a landing.
    detector.process_frame(_frame_with_dot((50, 50), size=size))
    detector.process_frame(_blank_frame(size))
    result = detector.process_frame(_blank_frame(size))
    assert result is None


def test_tip_selected_is_nearest_point_to_board_center():
    size = 200
    detector = DartLandingDetector(board_center_px=(0.0, 0.0), settle_frames=1)
    detector.set_reference_frame(_blank_frame(size))

    dart_frame = _frame_with_dot((150, 150), size=size, radius=10)
    landing = detector.process_frame(dart_frame)
    assert landing is not None
    # The nearest point of a circle centered at (150,150) to (0,0) should be
    # roughly radius closer than the center itself, i.e. tip < 150 in both axes.
    assert landing.tip_pixel[0] < 150
    assert landing.tip_pixel[1] < 150
