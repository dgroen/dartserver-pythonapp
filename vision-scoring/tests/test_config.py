import pytest
from vision_scoring.config import VisionScoringConfig


def test_from_env_reads_required_and_defaults(monkeypatch):
    monkeypatch.setenv("VISION_CAMERA_URL", "http://192.168.1.50:8080/video")
    monkeypatch.setenv("VISION_CALIBRATION_PATH", "/tmp/board1.json")
    monkeypatch.delenv("VISION_CONFIDENCE_THRESHOLD", raising=False)

    config = VisionScoringConfig.from_env()

    assert config.camera_url == "http://192.168.1.50:8080/video"
    assert str(config.calibration_path) == "/tmp/board1.json"
    assert config.confidence_threshold == 0.6
    assert config.countdown_seconds == 3.0


def test_from_env_reads_overridden_values(monkeypatch):
    monkeypatch.setenv("VISION_CAMERA_URL", "http://phone/video")
    monkeypatch.setenv("VISION_CALIBRATION_PATH", "/tmp/board1.json")
    monkeypatch.setenv("VISION_BOARD_CENTER_X", "512")
    monkeypatch.setenv("VISION_BOARD_CENTER_Y", "384")
    monkeypatch.setenv("VISION_CONFIDENCE_THRESHOLD", "0.8")
    monkeypatch.setenv("VISION_COUNTDOWN_SECONDS", "5")

    config = VisionScoringConfig.from_env()

    assert config.board_center_px == (512.0, 384.0)
    assert config.confidence_threshold == 0.8
    assert config.countdown_seconds == 5.0


def test_from_env_raises_when_required_var_missing(monkeypatch):
    monkeypatch.delenv("VISION_CAMERA_URL", raising=False)
    monkeypatch.delenv("VISION_CALIBRATION_PATH", raising=False)

    with pytest.raises(RuntimeError):
        VisionScoringConfig.from_env()
