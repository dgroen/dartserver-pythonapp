"""
Mobile Service Module
Handles dartboard management, API key authentication, and mobile app functionality
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.core.database_models import ApiKey, Dartboard, HotspotConfig, Player

logger = logging.getLogger(__name__)


class MobileService:
    """Service for managing mobile app and dartboard functionality"""

    def __init__(self, db_session: Session):
        """
        Initialize mobile service

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    # Dartboard Management

    def register_dartboard(
        self,
        owner_id: int,
        dartboard_id: str,
        name: str,
        wpa_key: str,
    ) -> dict[str, Any]:
        """
        Register a new dartboard

        Args:
            owner_id: Player ID who owns the dartboard
            dartboard_id: Unique dartboard identifier
            name: Friendly name for the dartboard
            wpa_key: WPA key for hotspot connection

        Returns:
            Dictionary with dartboard information
        """
        try:
            # Check if dartboard already exists
            existing = self.db_session.query(Dartboard).filter_by(dartboard_id=dartboard_id).first()
            if existing:
                return {
                    "success": False,
                    "error": "Dartboard ID already registered",
                }

            # Create new dartboard
            dartboard = Dartboard(
                dartboard_id=dartboard_id,
                name=name,
                owner_id=owner_id,
                wpa_key=wpa_key,
                is_active=True,
            )

            self.db_session.add(dartboard)
            self.db_session.commit()

            logger.info(f"Dartboard registered: {dartboard_id} for player {owner_id}")

            return {
                "success": True,
                "dartboard": {
                    "id": dartboard.id,
                    "dartboard_id": dartboard.dartboard_id,
                    "name": dartboard.name,
                    "is_active": dartboard.is_active,
                    "created_at": dartboard.created_at.isoformat(),
                },
            }

        except Exception as e:
            self.db_session.rollback()
            logging.exception("Error registering dartboard.")
            return {"success": False, "error": str(e)}

    def get_user_dartboards(self, owner_id: int) -> list[dict[str, Any]]:
        """
        Get all dartboards for a user

        Args:
            owner_id: Player ID

        Returns:
            List of dartboard dictionaries
        """
        try:
            dartboards = self.db_session.query(Dartboard).filter_by(owner_id=owner_id).all()

            return [
                {
                    "id": db.id,
                    "dartboard_id": db.dartboard_id,
                    "name": db.name,
                    "is_active": db.is_active,
                    "last_connected": (
                        db.last_connected.isoformat() if db.last_connected else None
                    ),
                    "created_at": db.created_at.isoformat(),
                }
                for db in dartboards
            ]

        except Exception:
            logging.exception("Error getting dartboards")
            return []

    def update_dartboard_connection(self, dartboard_id: str) -> bool:
        """
        Update last connected timestamp for a dartboard

        Args:
            dartboard_id: Dartboard identifier

        Returns:
            True if successful
        """
        try:
            dartboard = (
                self.db_session.query(Dartboard).filter_by(dartboard_id=dartboard_id).first()
            )

            if dartboard:
                dartboard.last_connected = datetime.now(tz=timezone.utc)
                self.db_session.commit()
                return True

            return False

        except Exception:
            self.db_session.rollback()
            logging.exception("Error updating dartboard connection:%s.")
            return False

    def delete_dartboard(self, dartboard_id: int, owner_id: int) -> dict[str, Any]:
        """
        Delete a dartboard

        Args:
            dartboard_id: Dartboard database ID
            owner_id: Player ID (for authorization)

        Returns:
            Dictionary with success status
        """
        try:
            dartboard = (
                self.db_session.query(Dartboard)
                .filter_by(id=dartboard_id, owner_id=owner_id)
                .first()
            )

            if not dartboard:
                return {"success": False, "error": "Dartboard not found"}

            self.db_session.delete(dartboard)
            self.db_session.commit()

            logger.info(f"Dartboard deleted: {dartboard.dartboard_id}")

            return {"success": True}

        except Exception as e:
            self.db_session.rollback()
            logging.exception("Error deleting dartboard.")
            return {"success": False, "error": str(e)}

    # API Key Management

    def create_api_key(self, player_id: int, key_name: str) -> dict[str, Any]:
        """
        Create a new API key for a player

        Args:
            player_id: Player ID
            key_name: Friendly name for the key

        Returns:
            Dictionary with API key information
        """
        try:
            api_key = ApiKey(
                player_id=player_id,
                key_name=key_name,
                api_key=ApiKey.generate_key(),
                is_active=True,
            )

            self.db_session.add(api_key)
            self.db_session.commit()

            logger.info(f"API key created: {key_name} for player {player_id}")

            return {
                "success": True,
                "api_key": {
                    "id": api_key.id,
                    "key_name": api_key.key_name,
                    "api_key": api_key.api_key,
                    "created_at": api_key.created_at.isoformat(),
                },
            }

        except Exception as e:
            self.db_session.rollback()
            logging.exception("Error creating API key")
            return {"success": False, "error": str(e)}

    def get_user_api_keys(self, player_id: int) -> list[dict[str, Any]]:
        """
        Get all API keys for a user

        Args:
            player_id: Player ID

        Returns:
            List of API key dictionaries (without the actual key)
        """
        try:
            api_keys = self.db_session.query(ApiKey).filter_by(player_id=player_id).all()

            return [
                {
                    "id": key.id,
                    "key_name": key.key_name,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat(),
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "api_key_preview": f"{key.api_key[:8]}...{key.api_key[-4:]}",
                }
                for key in api_keys
            ]

        except Exception:
            logging.exception("Error getting API keys.")
            return []

    def validate_api_key(self, api_key: str) -> dict[str, Any] | None:
        """
        Validate an API key and return player information

        Args:
            api_key: API key to validate

        Returns:
            Dictionary with player info if valid, None otherwise
        """
        try:
            key_obj = (
                self.db_session.query(ApiKey).filter_by(api_key=api_key, is_active=True).first()
            )

            if not key_obj:
                return None

            # Update last used timestamp
            key_obj.last_used = datetime.now(tz=timezone.utc)
            self.db_session.commit()

            # Get player info
            player = self.db_session.query(Player).filter_by(id=key_obj.player_id).first()

            if not player:
                return None

            return {
                "player_id": player.id,
                "player_name": player.name,
                "username": player.username,
            }

        except Exception:
            logging.exception("Error validating API key.")
            return None

    def revoke_api_key(self, key_id: int, player_id: int) -> dict[str, Any]:
        """
        Revoke (deactivate) an API key

        Args:
            key_id: API key database ID
            player_id: Player ID (for authorization)

        Returns:
            Dictionary with success status
        """
        try:
            api_key = (
                self.db_session.query(ApiKey).filter_by(id=key_id, player_id=player_id).first()
            )

            if not api_key:
                return {"success": False, "error": "API key not found"}

            api_key.is_active = False
            self.db_session.commit()

            logger.info(f"API key revoked: {api_key.key_name}")

            return {"success": True}

        except Exception as e:
            self.db_session.rollback()
            logging.exception("Error revoking API key.")
            return {"success": False, "error": str(e)}

    # Hotspot Configuration

    def create_hotspot_config(
        self,
        player_id: int,
        dartboard_id: int,
        ssid: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Create hotspot configuration for a dartboard

        Args:
            player_id: Player ID
            dartboard_id: Dartboard database ID
            ssid: Hotspot SSID
            password: Hotspot password

        Returns:
            Dictionary with hotspot configuration
        """
        try:
            # Verify dartboard ownership
            dartboard = (
                self.db_session.query(Dartboard)
                .filter_by(id=dartboard_id, owner_id=player_id)
                .first()
            )

            if not dartboard:
                return {"success": False, "error": "Dartboard not found"}

            # Check if config already exists
            existing = (
                self.db_session.query(HotspotConfig).filter_by(dartboard_id=dartboard_id).first()
            )

            if existing:
                # Update existing config
                existing.ssid = ssid
                existing.password = password
                existing.updated_at = datetime.now(tz=timezone.utc)
                config = existing
            else:
                # Create new config
                config = HotspotConfig(
                    player_id=player_id,
                    dartboard_id=dartboard_id,
                    ssid=ssid,
                    password=password,
                    is_enabled=False,
                )
                self.db_session.add(config)

            self.db_session.commit()

            logger.info(f"Hotspot config created/updated for dartboard {dartboard_id}")

            return {
                "success": True,
                "config": {
                    "id": config.id,
                    "ssid": config.ssid,
                    "password": config.password,
                    "is_enabled": config.is_enabled,
                },
            }

        except Exception as e:
            self.db_session.rollback()
            logging.exception("Error creating hotspot config.")
            return {"success": False, "error": str(e)}

    def toggle_hotspot(self, config_id: int, player_id: int, enabled: bool) -> dict[str, Any]:
        """
        Enable or disable hotspot

        Args:
            config_id: Hotspot config ID
            player_id: Player ID (for authorization)
            enabled: True to enable, False to disable

        Returns:
            Dictionary with success status
        """
        try:
            config = (
                self.db_session.query(HotspotConfig)
                .filter_by(id=config_id, player_id=player_id)
                .first()
            )

            if not config:
                return {"success": False, "error": "Hotspot configuration not found"}

            config.is_enabled = enabled
            config.updated_at = datetime.now(tz=timezone.utc)
            self.db_session.commit()

            logger.info(f"Hotspot {'enabled' if enabled else 'disabled'}: {config.ssid}")

            return {"success": True, "is_enabled": config.is_enabled}

        except Exception as e:
            self.db_session.rollback()
            logging.exception("Error toggling hotspot.")
            return {"success": False, "error": str(e)}

    def get_hotspot_configs(self, player_id: int) -> list[dict[str, Any]]:
        """
        Get all hotspot configurations for a user

        Args:
            player_id: Player ID

        Returns:
            List of hotspot configuration dictionaries
        """
        try:
            configs = self.db_session.query(HotspotConfig).filter_by(player_id=player_id).all()

            result = []
            for config in configs:
                dartboard = (
                    self.db_session.query(Dartboard).filter_by(id=config.dartboard_id).first()
                )

                result.append(
                    {
                        "id": config.id,
                        "dartboard_id": config.dartboard_id,
                        "dartboard_name": dartboard.name if dartboard else "Unknown",
                        "ssid": config.ssid,
                        "password": config.password,
                        "is_enabled": config.is_enabled,
                        "updated_at": config.updated_at.isoformat(),
                    },
                )

            return result

        except Exception:
            logging.exception("Error getting hotspot configs.")
            return []
