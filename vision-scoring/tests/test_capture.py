from unittest.mock import MagicMock, patch

import numpy as np
from vision_scoring.capture import CaptureConfig, PhoneCameraCapture


def _fake_video_capture(read_results):
    """Builds a MagicMock standing in for cv2.VideoCapture, whose .read()
    yields the given (ok, frame) tuples in order, then repeats the last one."""
    mock_capture = MagicMock()
    results = list(read_results)

    def _read():
        if results:
            return results.pop(0)
        return results[-1] if read_results else (False, None)

    mock_capture.read.side_effect = _read
    return mock_capture


def test_read_returns_frame_on_success():
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    with patch("cv2.VideoCapture", return_value=_fake_video_capture([(True, frame)])):
        capture = PhoneCameraCapture(CaptureConfig(url="http://phone/video"))
        result = capture.read()
    assert result is not None
    assert result.shape == (10, 10, 3)


def test_read_returns_none_on_transient_failure_without_reconnect():
    with patch("cv2.VideoCapture", return_value=_fake_video_capture([(False, None)])):
        capture = PhoneCameraCapture(
            CaptureConfig(url="http://phone/video", max_consecutive_failures_before_reconnect=5)
        )
        result = capture.read()
    assert result is None


def test_reconnects_after_too_many_consecutive_failures():
    fake_capture = _fake_video_capture([(False, None)] * 10)
    with patch("cv2.VideoCapture", return_value=fake_capture) as mock_ctor:
        capture = PhoneCameraCapture(
            CaptureConfig(
                url="http://phone/video",
                reconnect_delay_seconds=0.0,
                max_consecutive_failures_before_reconnect=3,
            )
        )
        for _ in range(3):
            capture.read()

        # After hitting the failure threshold, a reconnect should have opened
        # a fresh VideoCapture (constructor called again beyond the initial open).
        assert mock_ctor.call_count >= 2


def test_release_is_idempotent():
    with patch("cv2.VideoCapture", return_value=_fake_video_capture([])):
        capture = PhoneCameraCapture(CaptureConfig(url="http://phone/video"))
        capture.release()
        capture.release()  # should not raise
