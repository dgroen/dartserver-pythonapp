"""Integration tests for dartserver-services package."""

from dartserver_services import DartboardService, TTSService


class TestDartboardServiceIntegration:
    """Test dartboard service functionality."""

    def test_dartboard_initialization(self):
        """Test DartboardService initialization."""
        service = DartboardService()
        assert service is not None

    def test_add_zone_mapping(self):
        """Test adding zone mappings."""
        service = DartboardService()
        service.add_zone_mapping(0, 20)
        assert service.calculate_score(0) == 20

    def test_export_mappings(self):
        """Test exporting dartboard mappings."""
        service = DartboardService()
        service.add_zone_mapping(0, 20)
        service.add_zone_mapping(1, 5)
        mappings = service.export_mappings()
        assert isinstance(mappings, dict)


class TestTTSServiceIntegration:
    """Test text-to-speech service functionality."""

    def test_tts_initialization(self):
        """Test TTSService initialization."""
        service = TTSService(engine="offline")
        assert service is not None

    def test_get_voices(self):
        """Test retrieving available voices."""
        service = TTSService(engine="offline")
        voices = service.get_voices()
        assert voices is not None

    def test_get_supported_languages(self):
        """Test retrieving supported languages."""
        service = TTSService(engine="offline")
        languages = service.get_supported_languages()
        assert languages is not None
        assert len(languages) > 0


class TestMobileServiceIntegration:
    """Test mobile service functionality."""

    def test_mobile_initialization(self):
        """Test MobileService initialization."""
        # Note: requires database service
        # service = MobileService(db_service)
        # assert service is not None
        pass


class TestServicesExports:
    """Test that all expected exports are available."""

    def test_dartboard_service_export(self):
        """Test DartboardService is exported."""
        from dartserver_services import DartboardService

        assert DartboardService is not None

    def test_tts_service_export(self):
        """Test TTSService is exported."""
        from dartserver_services import TTSService

        assert TTSService is not None

    def test_mobile_service_export(self):
        """Test MobileService is exported."""
        from dartserver_services import MobileService

        assert MobileService is not None

    def test_rabbitmq_consumer_export(self):
        """Test RabbitMQConsumer is exported."""
        from dartserver_services import RabbitMQConsumer

        assert RabbitMQConsumer is not None
