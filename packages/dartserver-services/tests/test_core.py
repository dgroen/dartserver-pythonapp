"""Integration tests for dartserver_services package."""


def test_import_rabbitmq_consumer():
    """Test that RabbitMQConsumer can be imported."""
    from dartserver_services import RabbitMQConsumer

    assert RabbitMQConsumer is not None


def test_import_tts_service():
    """Test that TTSService can be imported."""
    from dartserver_services import TTSService

    assert TTSService is not None


def test_import_dartboard_service():
    """Test that DartboardService can be imported."""
    from dartserver_services import DartboardService

    assert DartboardService is not None


def test_import_mobile_service():
    """Test that MobileService can be imported."""
    from dartserver_services import MobileService

    assert MobileService is not None


def test_import_all_exports():
    """Test that all exports are available."""
    from dartserver_services import (
        DartboardMappingError,
        DartboardService,
        MobileService,
        RabbitMQConsumer,
        TTSService,
    )

    assert all(
        [
            DartboardMappingError,
            DartboardService,
            MobileService,
            RabbitMQConsumer,
            TTSService,
        ]
    )


def test_rabbitmq_consumer_initialization():
    """Test RabbitMQConsumer initialization."""
    from dartserver_services import RabbitMQConsumer

    config = {
        "host": "localhost",
        "user": "guest",
        "password": "guest",
        "exchange": "darts",
        "topic": "darts.scores.#",
        "port": 5672,
        "vhost": "/",
    }

    def callback(msg):
        return None

    consumer = RabbitMQConsumer(config, callback)

    assert consumer.config == config
    assert consumer.callback == callback
    assert consumer.connection is None


def test_tts_service_initialization():
    """Test TTSService initialization."""
    from dartserver_services import TTSService

    tts = TTSService(engine="pyttsx3", speed=150, volume=0.8)

    assert tts.engine_name == "pyttsx3"
    assert tts.speed == 150
    assert tts.volume == 0.8
    assert tts.language == "en"


def test_dartboard_service_constants():
    """Test DartboardService constants."""
    from dartserver_services import DartboardService

    assert "SINGLE" in DartboardService.MULTIPLIER_MAP
    assert "DOUBLE" in DartboardService.MULTIPLIER_MAP
    assert "TRIPLE" in DartboardService.MULTIPLIER_MAP
    assert 25 in DartboardService.VALID_ZONES
    assert 20 in DartboardService.VALID_ZONES
    assert 1 in DartboardService.VALID_ZONES


def test_dartboard_service_calculate_score():
    """Test DartboardService score calculation."""
    from dartserver_services import DartboardService

    # Test single
    assert DartboardService.calculate_score(20, "SINGLE") == 20

    # Test double
    assert DartboardService.calculate_score(20, "DOUBLE") == 40

    # Test triple
    assert DartboardService.calculate_score(20, "TRIPLE") == 60

    # Test bull
    assert DartboardService.calculate_score(25, "BULL") == 25

    # Test double bull
    assert DartboardService.calculate_score(25, "DBLBULL") == 50


def test_dartboard_service_validate_zone():
    """Test DartboardService zone validation."""
    from dartserver_services import DartboardService

    # Valid zones
    assert DartboardService.validate_zone_mapping(20, "SINGLE", 20)
    assert DartboardService.validate_zone_mapping(20, "DOUBLE", 20)
    assert DartboardService.validate_zone_mapping(25, "BULL", 25)
    assert DartboardService.validate_zone_mapping(25, "DBLBULL", 25)

    # Invalid zones
    assert not DartboardService.validate_zone_mapping(25, "SINGLE", 20)
    assert not DartboardService.validate_zone_mapping(20, "BULL", 20)
    assert not DartboardService.validate_zone_mapping(30, "SINGLE", 30)


def test_dartboard_service_legacy_conversion():
    """Test legacy score/multiplier to zone conversion."""
    from dartserver_services import DartboardService

    result = DartboardService.convert_legacy_to_zone(None, None, score=20, multiplier="SINGLE")

    assert result["zone_number"] == 20
    assert result["multiplier_type"] == "SINGLE"
    assert result["base_value"] == 20
    assert result["score"] == 20
