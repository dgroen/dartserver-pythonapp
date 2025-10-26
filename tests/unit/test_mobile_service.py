"""Unit tests for mobile_service module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.app.mobile_service import MobileService
from src.core.database_models import ApiKey, Dartboard, HotspotConfig, Player


class TestMobileService:
    """Test MobileService class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mobile_service(self, mock_db_session):
        """Create a mobile service instance with mock session."""
        return MobileService(mock_db_session)

    # Dartboard Management Tests

    def test_register_dartboard_success(self, mobile_service, mock_db_session):
        """Test successful dartboard registration."""
        # Mock query to return None (no existing dartboard)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        # Mock the add method to capture the dartboard object
        added_dartboard = None

        def capture_add(obj):
            nonlocal added_dartboard
            added_dartboard = obj
            # Set required attributes
            obj.id = 1
            obj.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        mock_db_session.add.side_effect = capture_add

        result = mobile_service.register_dartboard(
            owner_id=1,
            dartboard_id="DB123",
            name="My Dartboard",
            wpa_key="password123",
        )

        assert result["success"] is True
        assert "dartboard" in result
        assert result["dartboard"]["dartboard_id"] == "DB123"
        assert result["dartboard"]["name"] == "My Dartboard"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_register_dartboard_already_exists(self, mobile_service, mock_db_session):
        """Test registering a dartboard that already exists."""
        # Mock query to return existing dartboard
        existing_dartboard = MagicMock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            existing_dartboard
        )

        result = mobile_service.register_dartboard(
            owner_id=1,
            dartboard_id="DB123",
            name="My Dartboard",
            wpa_key="password123",
        )

        assert result["success"] is False
        assert "already registered" in result["error"]
        mock_db_session.add.assert_not_called()

    def test_register_dartboard_exception(self, mobile_service, mock_db_session):
        """Test dartboard registration with database exception."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_session.commit.side_effect = Exception("Database error")

        result = mobile_service.register_dartboard(
            owner_id=1,
            dartboard_id="DB123",
            name="My Dartboard",
            wpa_key="password123",
        )

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_get_user_dartboards_success(self, mobile_service, mock_db_session):
        """Test getting user dartboards."""
        # Create mock dartboards
        mock_dartboard1 = MagicMock()
        mock_dartboard1.id = 1
        mock_dartboard1.dartboard_id = "DB123"
        mock_dartboard1.name = "Dartboard 1"
        mock_dartboard1.is_active = True
        mock_dartboard1.last_connected = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_dartboard1.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        mock_dartboard2 = MagicMock()
        mock_dartboard2.id = 2
        mock_dartboard2.dartboard_id = "DB456"
        mock_dartboard2.name = "Dartboard 2"
        mock_dartboard2.is_active = False
        mock_dartboard2.last_connected = None
        mock_dartboard2.created_at = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [
            mock_dartboard1,
            mock_dartboard2,
        ]

        result = mobile_service.get_user_dartboards(owner_id=1)

        assert len(result) == 2
        assert result[0]["dartboard_id"] == "DB123"
        assert result[0]["name"] == "Dartboard 1"
        assert result[0]["is_active"] is True
        assert result[1]["dartboard_id"] == "DB456"
        assert result[1]["last_connected"] is None

    def test_get_user_dartboards_exception(self, mobile_service, mock_db_session):
        """Test getting user dartboards with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = mobile_service.get_user_dartboards(owner_id=1)

        assert result == []

    def test_update_dartboard_connection_success(self, mobile_service, mock_db_session):
        """Test updating dartboard connection timestamp."""
        mock_dartboard = MagicMock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_dartboard
        )

        result = mobile_service.update_dartboard_connection(dartboard_id="DB123")

        assert result is True
        assert mock_dartboard.last_connected is not None
        mock_db_session.commit.assert_called_once()

    def test_update_dartboard_connection_not_found(self, mobile_service, mock_db_session):
        """Test updating connection for non-existent dartboard."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = mobile_service.update_dartboard_connection(dartboard_id="DB123")

        assert result is False
        mock_db_session.commit.assert_not_called()

    def test_update_dartboard_connection_exception(self, mobile_service, mock_db_session):
        """Test updating dartboard connection with exception."""
        mock_dartboard = MagicMock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_dartboard
        )
        mock_db_session.commit.side_effect = Exception("Database error")

        result = mobile_service.update_dartboard_connection(dartboard_id="DB123")

        assert result is False
        mock_db_session.rollback.assert_called_once()

    def test_delete_dartboard_success(self, mobile_service, mock_db_session):
        """Test successful dartboard deletion."""
        mock_dartboard = MagicMock()
        mock_dartboard.dartboard_id = "DB123"
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_dartboard
        )

        result = mobile_service.delete_dartboard(dartboard_id=1, owner_id=1)

        assert result["success"] is True
        mock_db_session.delete.assert_called_once_with(mock_dartboard)
        mock_db_session.commit.assert_called_once()

    def test_delete_dartboard_not_found(self, mobile_service, mock_db_session):
        """Test deleting non-existent dartboard."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = mobile_service.delete_dartboard(dartboard_id=1, owner_id=1)

        assert result["success"] is False
        assert "not found" in result["error"]
        mock_db_session.delete.assert_not_called()

    def test_delete_dartboard_exception(self, mobile_service, mock_db_session):
        """Test dartboard deletion with exception."""
        mock_dartboard = MagicMock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_dartboard
        )
        mock_db_session.delete.side_effect = Exception("Database error")

        result = mobile_service.delete_dartboard(dartboard_id=1, owner_id=1)

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    # API Key Management Tests

    @patch("database_models.ApiKey.generate_key")
    def test_create_api_key_success(self, mock_generate_key, mobile_service, mock_db_session):
        """Test successful API key creation."""
        mock_generate_key.return_value = "test_api_key_123"

        # Mock the add method to capture the API key object
        def capture_add(obj):
            # Set required attributes
            obj.id = 1
            obj.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        mock_db_session.add.side_effect = capture_add

        result = mobile_service.create_api_key(player_id=1, key_name="My API Key")

        assert result["success"] is True
        assert "api_key" in result
        assert result["api_key"]["key_name"] == "My API Key"
        assert result["api_key"]["api_key"] == "test_api_key_123"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_api_key_exception(self, mobile_service, mock_db_session):
        """Test API key creation with exception."""
        mock_db_session.commit.side_effect = Exception("Database error")

        result = mobile_service.create_api_key(player_id=1, key_name="My API Key")

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_get_user_api_keys_success(self, mobile_service, mock_db_session):
        """Test getting user API keys."""
        # Create mock API keys
        mock_key1 = MagicMock()
        mock_key1.id = 1
        mock_key1.key_name = "Key 1"
        mock_key1.is_active = True
        mock_key1.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_key1.last_used = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
        mock_key1.api_key = "abcdefgh12345678ijklmnop"

        mock_key2 = MagicMock()
        mock_key2.id = 2
        mock_key2.key_name = "Key 2"
        mock_key2.is_active = False
        mock_key2.created_at = datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
        mock_key2.last_used = None
        mock_key2.api_key = "xyz12345abcdefghijklmnop"

        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [
            mock_key1,
            mock_key2,
        ]

        result = mobile_service.get_user_api_keys(player_id=1)

        assert len(result) == 2
        assert result[0]["key_name"] == "Key 1"
        assert result[0]["is_active"] is True
        assert "abcdefgh" in result[0]["api_key_preview"]
        assert "mnop" in result[0]["api_key_preview"]
        assert result[1]["last_used"] is None

    def test_get_user_api_keys_exception(self, mobile_service, mock_db_session):
        """Test getting user API keys with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = mobile_service.get_user_api_keys(player_id=1)

        assert result == []

    def test_validate_api_key_success(self, mobile_service, mock_db_session):
        """Test successful API key validation."""
        # Mock API key
        mock_key = MagicMock()
        mock_key.player_id = 1

        # Mock player
        mock_player = MagicMock()
        mock_player.id = 1
        mock_player.name = "Test Player"
        mock_player.username = "testuser"

        # Setup query mock to return different values for different queries
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ApiKey:
                mock_query.filter_by.return_value.first.return_value = mock_key
            elif model == Player:
                mock_query.filter_by.return_value.first.return_value = mock_player
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        result = mobile_service.validate_api_key(api_key="test_key_123")

        assert result is not None
        assert result["player_id"] == 1
        assert result["player_name"] == "Test Player"
        assert result["username"] == "testuser"
        assert mock_key.last_used is not None
        mock_db_session.commit.assert_called_once()

    def test_validate_api_key_not_found(self, mobile_service, mock_db_session):
        """Test validating non-existent API key."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = mobile_service.validate_api_key(api_key="invalid_key")

        assert result is None

    def test_validate_api_key_player_not_found(self, mobile_service, mock_db_session):
        """Test validating API key with non-existent player."""
        # Mock API key exists
        mock_key = MagicMock()
        mock_key.player_id = 1

        # Setup query mock to return key but no player
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ApiKey:
                mock_query.filter_by.return_value.first.return_value = mock_key
            elif model == Player:
                mock_query.filter_by.return_value.first.return_value = None
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        result = mobile_service.validate_api_key(api_key="test_key_123")

        assert result is None

    def test_validate_api_key_exception(self, mobile_service, mock_db_session):
        """Test API key validation with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = mobile_service.validate_api_key(api_key="test_key_123")

        assert result is None

    def test_revoke_api_key_success(self, mobile_service, mock_db_session):
        """Test successful API key revocation."""
        mock_key = MagicMock()
        mock_key.key_name = "Test Key"
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_key

        result = mobile_service.revoke_api_key(key_id=1, player_id=1)

        assert result["success"] is True
        assert mock_key.is_active is False
        mock_db_session.commit.assert_called_once()

    def test_revoke_api_key_not_found(self, mobile_service, mock_db_session):
        """Test revoking non-existent API key."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = mobile_service.revoke_api_key(key_id=1, player_id=1)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_revoke_api_key_exception(self, mobile_service, mock_db_session):
        """Test API key revocation with exception."""
        mock_key = MagicMock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_key
        mock_db_session.commit.side_effect = Exception("Database error")

        result = mobile_service.revoke_api_key(key_id=1, player_id=1)

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    # Hotspot Configuration Tests

    def test_create_hotspot_config_new(self, mobile_service, mock_db_session):
        """Test creating new hotspot configuration."""
        # Mock dartboard exists
        mock_dartboard = MagicMock()
        mock_dartboard.id = 1

        # Setup query mock to return dartboard but no existing config
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Dartboard:
                mock_query.filter_by.return_value.first.return_value = mock_dartboard
            elif model == HotspotConfig:
                mock_query.filter_by.return_value.first.return_value = None
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        # Mock the add method to set required attributes
        def capture_add(obj):
            obj.id = 1

        mock_db_session.add.side_effect = capture_add

        result = mobile_service.create_hotspot_config(
            player_id=1,
            dartboard_id=1,
            ssid="MyDartboard",
            password="password123",
        )

        assert result["success"] is True
        assert "config" in result
        assert result["config"]["ssid"] == "MyDartboard"
        assert result["config"]["password"] == "password123"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_hotspot_config_update_existing(self, mobile_service, mock_db_session):
        """Test updating existing hotspot configuration."""
        # Mock dartboard exists
        mock_dartboard = MagicMock()
        mock_dartboard.id = 1

        # Mock existing config
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.ssid = "OldSSID"
        mock_config.password = "oldpass"
        mock_config.is_enabled = False

        # Setup query mock
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Dartboard:
                mock_query.filter_by.return_value.first.return_value = mock_dartboard
            elif model == HotspotConfig:
                mock_query.filter_by.return_value.first.return_value = mock_config
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        result = mobile_service.create_hotspot_config(
            player_id=1,
            dartboard_id=1,
            ssid="NewSSID",
            password="newpass",
        )

        assert result["success"] is True
        assert mock_config.ssid == "NewSSID"
        assert mock_config.password == "newpass"
        assert mock_config.updated_at is not None
        mock_db_session.add.assert_not_called()  # Should not add, only update
        mock_db_session.commit.assert_called_once()

    def test_create_hotspot_config_dartboard_not_found(self, mobile_service, mock_db_session):
        """Test creating hotspot config for non-existent dartboard."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = mobile_service.create_hotspot_config(
            player_id=1,
            dartboard_id=1,
            ssid="MyDartboard",
            password="password123",
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_create_hotspot_config_exception(self, mobile_service, mock_db_session):
        """Test hotspot config creation with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = mobile_service.create_hotspot_config(
            player_id=1,
            dartboard_id=1,
            ssid="MyDartboard",
            password="password123",
        )

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_toggle_hotspot_enable(self, mobile_service, mock_db_session):
        """Test enabling hotspot."""
        mock_config = MagicMock()
        mock_config.ssid = "MyDartboard"
        mock_config.is_enabled = False
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        result = mobile_service.toggle_hotspot(config_id=1, player_id=1, enabled=True)

        assert result["success"] is True
        assert result["is_enabled"] is True
        assert mock_config.is_enabled is True
        assert mock_config.updated_at is not None
        mock_db_session.commit.assert_called_once()

    def test_toggle_hotspot_disable(self, mobile_service, mock_db_session):
        """Test disabling hotspot."""
        mock_config = MagicMock()
        mock_config.ssid = "MyDartboard"
        mock_config.is_enabled = True
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        result = mobile_service.toggle_hotspot(config_id=1, player_id=1, enabled=False)

        assert result["success"] is True
        assert result["is_enabled"] is False
        assert mock_config.is_enabled is False

    def test_toggle_hotspot_not_found(self, mobile_service, mock_db_session):
        """Test toggling non-existent hotspot."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = mobile_service.toggle_hotspot(config_id=1, player_id=1, enabled=True)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_toggle_hotspot_exception(self, mobile_service, mock_db_session):
        """Test hotspot toggle with exception."""
        mock_config = MagicMock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_config
        mock_db_session.commit.side_effect = Exception("Database error")

        result = mobile_service.toggle_hotspot(config_id=1, player_id=1, enabled=True)

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_get_hotspot_configs_success(self, mobile_service, mock_db_session):
        """Test getting hotspot configurations."""
        # Mock config
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.dartboard_id = 1
        mock_config.ssid = "MyDartboard"
        mock_config.password = "password123"
        mock_config.is_enabled = True
        mock_config.updated_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        # Mock dartboard
        mock_dartboard = MagicMock()
        mock_dartboard.name = "Test Dartboard"

        # Setup query mock
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == HotspotConfig:
                mock_query.filter_by.return_value.all.return_value = [mock_config]
            elif model == Dartboard:
                mock_query.filter_by.return_value.first.return_value = mock_dartboard
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        result = mobile_service.get_hotspot_configs(player_id=1)

        assert len(result) == 1
        assert result[0]["ssid"] == "MyDartboard"
        assert result[0]["dartboard_name"] == "Test Dartboard"
        assert result[0]["is_enabled"] is True

    def test_get_hotspot_configs_dartboard_not_found(self, mobile_service, mock_db_session):
        """Test getting hotspot configs when dartboard is deleted."""
        # Mock config
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.dartboard_id = 1
        mock_config.ssid = "MyDartboard"
        mock_config.password = "password123"
        mock_config.is_enabled = True
        mock_config.updated_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        # Setup query mock
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == HotspotConfig:
                mock_query.filter_by.return_value.all.return_value = [mock_config]
            elif model == Dartboard:
                mock_query.filter_by.return_value.first.return_value = None
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        result = mobile_service.get_hotspot_configs(player_id=1)

        assert len(result) == 1
        assert result[0]["dartboard_name"] == "Unknown"

    def test_get_hotspot_configs_exception(self, mobile_service, mock_db_session):
        """Test getting hotspot configs with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = mobile_service.get_hotspot_configs(player_id=1)

        assert result == []
