from vision_scoring.config import VisionScoringConfig


def test_from_env_uses_defaults_when_nothing_set(monkeypatch):
    for var in (
        "VISION_HOST",
        "VISION_PORT",
        "VISION_CALIBRATION_DIR",
        "VISION_CONFIDENCE_THRESHOLD",
        "VISION_COUNTDOWN_SECONDS",
        "VISION_GATEWAY_CLIENT_ID",
        "VISION_GATEWAY_CLIENT_SECRET",
        "VISION_GATEWAY_TOKEN_URL",
        "VISION_GATEWAY_URL",
    ):
        monkeypatch.delenv(var, raising=False)

    config = VisionScoringConfig.from_env()

    assert config.host == "0.0.0.0"
    assert config.port == 5901
    assert str(config.calibration_dir) == "calibration"
    assert config.confidence_threshold == 0.6
    assert config.countdown_seconds == 3.0
    assert config.publishing_enabled() is False


def test_from_env_reads_overridden_values(monkeypatch):
    monkeypatch.setenv("VISION_PORT", "6000")
    monkeypatch.setenv("VISION_CONFIDENCE_THRESHOLD", "0.8")
    monkeypatch.setenv("VISION_COUNTDOWN_SECONDS", "5")
    monkeypatch.setenv("VISION_GATEWAY_CLIENT_ID", "client-1")
    monkeypatch.setenv("VISION_GATEWAY_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("VISION_GATEWAY_TOKEN_URL", "https://wso2is/oauth2/token")
    monkeypatch.setenv("VISION_GATEWAY_URL", "https://api-gateway")

    config = VisionScoringConfig.from_env()

    assert config.port == 6000
    assert config.confidence_threshold == 0.8
    assert config.countdown_seconds == 5.0
    assert config.publishing_enabled() is True


def test_publishing_enabled_false_when_partially_configured(monkeypatch):
    monkeypatch.setenv("VISION_GATEWAY_CLIENT_ID", "client-1")
    monkeypatch.delenv("VISION_GATEWAY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("VISION_GATEWAY_TOKEN_URL", raising=False)
    monkeypatch.delenv("VISION_GATEWAY_URL", raising=False)

    config = VisionScoringConfig.from_env()

    assert config.publishing_enabled() is False
