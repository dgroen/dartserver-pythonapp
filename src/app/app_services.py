"""
Service endpoints (Dartboard, TTS, Mobile services)
"""

import json
import logging
import os
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    Response,
    send_from_directory,
    session,
)
from flask import current_app as _flask_current_app

# Module-level `current_app` placeholder so unit tests can patch
# `src.app.app_services.current_app` without requiring an app context.
current_app = None


def _app():
    """Return the test-patched app if present, otherwise Flask's current_app."""
    return current_app if current_app is not None else _flask_current_app


from src.core.auth import login_required, permission_required, role_required
from src.core.dartboard_service import DartboardMappingError, DartboardService
from src.core.database_service import get_session
from src.app.mobile_service import MobileService

services_bp = Blueprint("services", __name__)
logger = logging.getLogger(__name__)

# Get root directory for mobile templates
_app_dir = Path(__file__).resolve().parent
_root_dir = _app_dir.parent.parent


# API key authentication decorator
def api_key_required(f):
    """Decorator to require API key authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"success": False, "error": "API key required"}), 401

        # Verify API key
        mobile_service = get_mobile_service()
        if not mobile_service.verify_api_key(api_key):
            return jsonify({"success": False, "error": "Invalid API key"}), 403

        return f(*args, **kwargs)

    return decorated_function


def get_mobile_service():
    """Get or create MobileService instance"""
    if not hasattr(_app(), "mobile_service"):
        _app().mobile_service = MobileService(_app().game_manager.db_service)

    return _app().mobile_service


@services_bp.route("/api/Throw/zone", methods=["POST"])
# @login_required
# @permission_required("score:submit")
def submit_score_zone():
    """Submit a score via dartboard zone mapping (New generic format)
    ---
    tags:
      - Score
    summary: Submit a dart score using zone mapping
    description: |
        Submits a dart throw using GPIO pin combination and dartboard type.
        The server looks up the zone information based on the dartboard type and pin combination.
        This is the preferred format for new dartboards.
    parameters:
      - in: body
        name: body
        description: Pin-based score information
        required: true
        schema:
          type: object
          required:
            - masterPin
            - slavePin
            - boardType
          properties:
            masterPin:
              type: integer
              description: Master (row) GPIO pin number
              example: 4
            slavePin:
              type: integer
              description: Slave (column) GPIO pin number
              example: 13
            boardType:
              type: string
              description: Dartboard type identifier (e.g., 'carromco', 'winmau')
              example: carromco
            user:
              type: string
              description: Optional player identifier
              example: dgroen
    responses:
      200:
        description: Score submitted successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Score submitted
            zone_info:
              type: object
              properties:
                zone_number:
                  type: integer
                  example: 20
                multiplier_type:
                  type: string
                  example: TRIPLE
                base_value:
                  type: integer
                  example: 20
                score:
                  type: integer
                  example: 60
      400:
        description: Invalid request or zone not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
    """
    try:
        data = request.json
        master_pin = data.get("masterPin")
        slave_pin = data.get("slavePin")
        board_type = data.get("boardType", "").lower()

        # Validate input
        if not isinstance(master_pin, int) or not isinstance(slave_pin, int):
            return (
                jsonify({"status": "error", "message": "masterPin and slavePin must be integers"}),
                400,
            )

        if not board_type:
            return jsonify({"status": "error", "message": "boardType is required"}), 400

        # Get database session
        session = get_session()

        try:
            # Look up zone information
            zone_info = DartboardService.get_zone_from_pins(
                session,
                board_type,
                master_pin,
                slave_pin,
            )

            # Emit WebSocket event for admin dartboard testing page (even if zone not found)
            _app().socketio.emit(
                "dartboard_test_received",
                {
                    "masterPin": master_pin,
                    "slavePin": slave_pin,
                    "boardType": board_type,
                    "zoneInfo": zone_info,
                },
                namespace="/",
            )

            if not zone_info:
                logger.warning(
                    f"Zone mapping not found - Received pinout: masterPin={master_pin}, "
                    f"slavePin={slave_pin}, boardType={board_type}",
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": (
                                f"Zone mapping not found for pins ({master_pin}, {slave_pin}) "
                                f"on board type '{board_type}'"
                            ),
                        },
                    ),
                    400,
                )

            # Process the score using the zone information
            # Pass the base_value and multiplier_type - game logic handles the calculation
            _app().game_manager.process_score(
                {
                    "score": zone_info["base_value"],
                    "multiplier": zone_info["multiplier_type"],
                },
            )

            return jsonify(
                {
                    "status": "success",
                    "message": "Score submitted",
                    "zone_info": zone_info,
                },
            )
        finally:
            session.close()

    except Exception as e:
        logger.exception("Error submitting zone-based score")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/dartboard/types", methods=["GET"])
def get_dartboard_types():
    """Get all registered dartboard types
    ---
    tags:
      - Dartboard
    summary: Get dartboard types
    description: Returns all registered and active dartboard types
    responses:
      200:
        description: List of dartboard types
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            types:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  brand:
                    type: string
                  model:
                    type: string
                  description:
                    type: string
    """
    try:
        session = get_session()
        try:
            types = DartboardService.list_dartboard_types(session)
            return jsonify(
                {
                    "status": "success",
                    "types": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "brand": t.brand,
                            "model": t.model,
                            "description": t.description,
                        }
                        for t in types
                    ],
                },
            )
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error getting dartboard types")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/dartboard/types/<board_type>/mappings", methods=["GET"])
def get_dartboard_mappings(board_type):
    """Get zone mappings for a dartboard type
    ---
    tags:
      - Dartboard
    summary: Get dartboard zone mappings
    description: Returns all zone mappings for a specific dartboard type
    parameters:
      - in: path
        name: board_type
        type: string
        required: true
        description: Dartboard type name (e.g., 'carromco')
    responses:
      200:
        description: List of zone mappings
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            board_type:
              type: string
            mappings:
              type: array
              items:
                type: object
                properties:
                  master_pin:
                    type: integer
                  slave_pin:
                    type: integer
                  zone_number:
                    type: integer
                  multiplier_type:
                    type: string
                  base_value:
                    type: integer
      404:
        description: Dartboard type not found
    """
    try:
        session = get_session()
        try:
            mappings = DartboardService.get_dartboard_type_mappings(session, board_type.lower())
            if mappings is None:
                return (
                    jsonify(
                        {"status": "error", "message": f"Dartboard type '{board_type}' not found"},
                    ),
                    404,
                )

            return jsonify(
                {
                    "status": "success",
                    "board_type": board_type,
                    "mappings": [
                        {
                            "master_pin": m.master_pin,
                            "slave_pin": m.slave_pin,
                            "zone_number": m.zone_number,
                            "multiplier_type": m.multiplier_type,
                            "base_value": m.base_value,
                        }
                        for m in mappings
                    ],
                },
            )
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error getting dartboard mappings")
        return jsonify({"status": "error", "message": str(e)}), 400


# ==================== ADMIN DARTBOARD TESTING ENDPOINTS ====================


@services_bp.route("/api/admin/dartboard/matrix/<board_type>", methods=["GET"])
@login_required
@role_required("admin")
def get_dartboard_matrix(board_type):
    """Get matrix visualization for a dartboard type
    ---
    tags:
      - Admin/Dartboard
    summary: Get dartboard matrix visualization
    description: Returns the GPIO pin matrix for a dartboard type with current mappings
    parameters:
      - in: path
        name: board_type
        type: string
        description: Dartboard type name (e.g., 'carromco')
    responses:
      200:
        description: Matrix visualization data
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            dartboard_type:
              type: object
            master_pins:
              type: array
              items:
                type: integer
            slave_pins:
              type: array
              items:
                type: integer
            matrix:
              type: array
      404:
        description: Dartboard type not found
    """
    try:
        session = get_session()
        try:
            result = DartboardService.get_matrix_visualization(session, board_type.lower())
            if not result or result[0] is None:
                return (
                    jsonify(
                        {"status": "error", "message": f"Dartboard type '{board_type}' not found"},
                    ),
                    404,
                )

            dartboard_type_dict, master_pins, slave_pins, matrix = result

            return jsonify(
                {
                    "status": "success",
                    "dartboard_type": dartboard_type_dict,
                    "master_pins": master_pins,
                    "slave_pins": slave_pins,
                    "matrix": matrix,
                },
            )
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error getting dartboard matrix")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/admin/dartboard/mapping", methods=["POST"])
@login_required
@role_required("admin")
def update_dartboard_mapping():
    """Update or create a dartboard zone mapping
    ---
    tags:
      - Admin/Dartboard
    summary: Update dartboard mapping
    description: Update an existing zone mapping or create a new one
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - boardType
            - masterPin
            - slavePin
            - zoneNumber
            - multiplierType
            - baseValue
          properties:
            boardType:
              type: string
              example: carromco
            masterPin:
              type: integer
              example: 4
            slavePin:
              type: integer
              example: 13
            zoneNumber:
              type: integer
              example: 20
            multiplierType:
              type: string
              enum: ['SINGLE', 'DOUBLE', 'TRIPLE', 'BULL', 'DBLBULL']
              example: TRIPLE
            baseValue:
              type: integer
              example: 20
    responses:
      200:
        description: Mapping updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
      400:
        description: Invalid request or validation error
    """
    try:
        data = request.json
        board_type = data.get("boardType", "").lower()
        master_pin = data.get("masterPin")
        slave_pin = data.get("slavePin")
        zone_number = data.get("zoneNumber")
        multiplier_type = data.get("multiplierType", "").upper()
        base_value = data.get("baseValue")

        # Validate input
        if not all(
            [
                board_type,
                master_pin is not None,
                slave_pin is not None,
                zone_number is not None,
                multiplier_type,
                base_value is not None,
            ],
        ):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        session = get_session()
        try:
            DartboardService.update_zone_mapping(
                session,
                board_type,
                int(master_pin),
                int(slave_pin),
                int(zone_number),
                multiplier_type,
                int(base_value),
            )
            return jsonify(
                {
                    "status": "success",
                    "message": f"Mapping for pins ({master_pin}, {slave_pin}) updated successfully",
                },
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.exception("Dartboard mapping error")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error updating dartboard mapping")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/admin/dartboard/import", methods=["POST"])
@login_required
@role_required("admin")
def import_dartboard_mappings():
    """Bulk import dartboard mappings from CSV
    ---
    tags:
      - Admin/Dartboard
    summary: Bulk import mappings
    description: Import multiple zone mappings at once
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - boardType
            - mappings
          properties:
            boardType:
              type: string
              example: carromco
            mappings:
              type: array
              items:
                type: object
                required:
                  - masterPin
                  - slavePin
                  - zoneNumber
                  - multiplierType
                  - baseValue
                properties:
                  masterPin:
                    type: integer
                  slavePin:
                    type: integer
                  zoneNumber:
                    type: integer
                  multiplierType:
                    type: string
                  baseValue:
                    type: integer
    responses:
      200:
        description: Mappings imported successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            created:
              type: integer
            updated:
              type: integer
      400:
        description: Invalid request or import error
    """
    try:
        data = request.json
        board_type = data.get("boardType", "").lower()
        mappings = data.get("mappings", [])

        if not board_type or not mappings:
            return (
                jsonify({"status": "error", "message": "boardType and mappings are required"}),
                400,
            )

        session = get_session()
        try:
            # Convert CSV-like format to mapping data format
            mapping_data = []
            for mapping in mappings:
                mapping_data.append(
                    {
                        "master_pin": mapping.get("masterPin"),
                        "slave_pin": mapping.get("slavePin"),
                        "zone_number": mapping.get("zoneNumber"),
                        "multiplier_type": mapping.get("multiplierType"),
                        "base_value": mapping.get("baseValue"),
                    },
                )

            created, updated = DartboardService.bulk_import_mappings(
                session,
                board_type,
                mapping_data,
            )

            return jsonify(
                {
                    "status": "success",
                    "message": (
                        f"Imported {created} new mappings and updated {updated} existing mappings"
                    ),
                    "created": created,
                    "updated": updated,
                },
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.exception("Dartboard import error")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error importing dartboard mappings")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/admin/dartboard/type", methods=["POST"])
@login_required
@role_required("admin")
def create_dartboard_type():
    """Create a new dartboard type
    ---
    tags:
      - Admin/Dartboard
    summary: Create new dartboard type
    description: Register a new dartboard type that can then be configured with zone mappings
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - name
            - brand
          properties:
            name:
              type: string
              description: Unique identifier for the dartboard type (lowercase, no spaces)
              example: granboard
            brand:
              type: string
              description: Brand name of the dartboard
              example: Gran Board
            model:
              type: string
              description: Model name or number (optional)
              example: Gran Board 3
            description:
              type: string
              description: Description of the dartboard (optional)
              example: Electronic dartboard with Bluetooth connectivity
            masterPins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for master (row) lines
              example: [2, 4, 5, 16, 17, 18, 19]
            slavePins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for slave (column) lines
              example: [12, 13, 14, 25, 26, 27, 32, 33]
    responses:
      201:
        description: Dartboard type created successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
            dartboard_type:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                brand:
                  type: string
                model:
                  type: string
                description:
                  type: string
                master_pins:
                  type: array
                  items:
                    type: integer
                slave_pins:
                  type: array
                  items:
                    type: integer
      400:
        description: Invalid request or dartboard type already exists
    """
    try:
        data = request.json or {}
        name = data.get("name", "").lower().strip()
        brand = data.get("brand", "").strip()
        model = data.get("model", "").strip() if data.get("model") else None
        description = data.get("description", "").strip() if data.get("description") else None
        master_pins = data.get("masterPins")
        slave_pins = data.get("slavePins")

        # Validate required fields
        error_msg = None
        status_code = 400

        if not name:
            error_msg = "Name is required"
        elif not brand:
            error_msg = "Brand is required"
        elif not name.replace("_", "").replace("-", "").isalnum():
            error_msg = "Name must contain only letters, numbers, hyphens and underscores"
        elif master_pins is not None and (
            not isinstance(master_pins, list) or not all(isinstance(p, int) for p in master_pins)
        ):
            error_msg = "masterPins must be an array of integers"
        elif slave_pins is not None and (
            not isinstance(slave_pins, list) or not all(isinstance(p, int) for p in slave_pins)
        ):
            error_msg = "slavePins must be an array of integers"

        if error_msg:
            return jsonify({"status": "error", "message": error_msg}), status_code

        session = get_session()
        try:
            dartboard_type = DartboardService.register_dartboard_type(
                session,
                name=name,
                brand=brand,
                model=model,
                description=description,
                master_pins=master_pins,
                slave_pins=slave_pins,
            )
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"Dartboard type '{name}' created successfully",
                        "dartboard_type": {
                            "id": dartboard_type.id,
                            "name": dartboard_type.name,
                            "brand": dartboard_type.brand,
                            "model": dartboard_type.model,
                            "description": dartboard_type.description,
                            "master_pins": master_pins,
                            "slave_pins": slave_pins,
                        },
                    },
                ),
                201,
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.warning("Dartboard type creation failed: %s", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error creating dartboard type")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/admin/dartboard/type/<board_type>/pins", methods=["PUT"])
@login_required
@role_required("admin")
def update_dartboard_pins(board_type):
    """Update GPIO pin configuration for a dartboard type
    ---
    tags:
      - Admin/Dartboard
    summary: Update dartboard GPIO pins
    description: Update the master and slave GPIO pin configuration for an existing dartboard type
    parameters:
      - in: path
        name: board_type
        type: string
        required: true
        description: Dartboard type name
      - in: body
        name: body
        schema:
          type: object
          properties:
            masterPins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for master (row) lines
              example: [2, 4, 5, 16, 17, 18, 19]
            slavePins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for slave (column) lines
              example: [12, 13, 14, 25, 26, 27, 32, 33]
    responses:
      200:
        description: Pins updated successfully
      400:
        description: Invalid request
      404:
        description: Dartboard type not found
    """
    try:
        data = request.json
        master_pins = data.get("masterPins")
        slave_pins = data.get("slavePins")

        # Validate pin arrays if provided
        if master_pins is not None and (
            not isinstance(master_pins, list) or not all(isinstance(p, int) for p in master_pins)
        ):
            return (
                jsonify({"status": "error", "message": "masterPins must be an array of integers"}),
                400,
            )
        if slave_pins is not None and (
            not isinstance(slave_pins, list) or not all(isinstance(p, int) for p in slave_pins)
        ):
            return (
                jsonify({"status": "error", "message": "slavePins must be an array of integers"}),
                400,
            )

        session = get_session()
        try:
            dartboard_type = DartboardService.update_dartboard_pins(
                session,
                board_type.lower(),
                master_pins=master_pins,
                slave_pins=slave_pins,
            )
            return jsonify(
                {
                    "status": "success",
                    "message": f"Pins updated for '{board_type}'",
                    "dartboard_type": {
                        "id": dartboard_type.id,
                        "name": dartboard_type.name,
                        "master_pins": master_pins,
                        "slave_pins": slave_pins,
                    },
                },
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.warning("Dartboard pin update failed: %s", str(e))
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Error updating dartboard pins")
        return jsonify({"status": "error", "message": str(e)}), 400


@services_bp.route("/api/admin/dartboard/available-pins", methods=["GET"])
@login_required
@role_required("admin")
def get_available_pins():
    """Get list of available GPIO pins for dartboard configuration
    ---
    tags:
      - Admin/Dartboard
    summary: Get available GPIO pins
    description: Returns a list of common ESP32 GPIO pins that can be used for dartboard matrices
    responses:
      200:
        description: List of available pins
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            pins:
              type: array
              items:
                type: integer
              example: [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]
    """
    return jsonify(
        {
            "status": "success",
            "pins": DartboardService.AVAILABLE_GPIO_PINS,
        },
    )


@services_bp.route("/api/tts/config", methods=["GET"])
def get_tts_config():
    """Get TTS configuration
    ---
    tags:
      - TTS
    summary: Get TTS configuration
    description: Returns the current TTS configuration including speed, voice, and enabled status
    responses:
      200:
        description: TTS configuration
        schema:
          type: object
          properties:
            enabled:
              type: boolean
              description: Whether TTS is enabled
            engine:
              type: string
              description: TTS engine name
            speed:
              type: integer
              description: Speech speed (words per minute)
            volume:
              type: number
              description: Volume level (0.0 to 1.0)
            voice:
              type: string
              description: Current voice type
    """
    return jsonify(
        {
            "enabled": _app().game_manager.tts.is_enabled(),
            "engine": _app().game_manager.tts.engine_name,
            "speed": _app().game_manager.tts.speed,
            "volume": _app().game_manager.tts.volume,
            "voice": _app().game_manager.tts.voice_type,
            "language": _app().game_manager.tts.language,
        },
    )


@services_bp.route("/api/tts/config", methods=["POST"])
def update_tts_config():
    """Update TTS configuration
    ---
    tags:
      - TTS
    summary: Update TTS configuration
    description: Updates TTS settings such as speed, voice, and enabled status
    parameters:
      - in: body
        name: body
        description: TTS configuration
        required: true
        schema:
          type: object
          properties:
            enabled:
              type: boolean
              description: Enable or disable TTS
              example: true
            speed:
              type: integer
              description: Speech speed (words per minute, typically 100-200)
              example: 150
            volume:
              type: number
              description: Volume level (0.0 to 1.0)
              example: 1.0
            voice:
              type: string
              description: Voice type identifier
              example: default
    responses:
      200:
        description: Configuration updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: TTS configuration updated
    """
    data = request.json

    if "enabled" in data:
        if data["enabled"]:
            _app().game_manager.tts.enable()
        else:
            _app().game_manager.tts.disable()

    if "speed" in data:
        _app().game_manager.tts.set_speed(int(data["speed"]))

    if "volume" in data:
        _app().game_manager.tts.set_volume(float(data["volume"]))

    if "voice" in data:
        _app().game_manager.tts.set_voice(data["voice"])

    if "language" in data:
        _app().game_manager.tts.set_language(data["language"])

    return jsonify({"status": "success", "message": "TTS configuration updated"})


@services_bp.route("/api/tts/voices", methods=["GET"])
def get_tts_voices():
    """Get available TTS voices
    ---
    tags:
      - TTS
    summary: Get available TTS voices
    description: Returns a list of available voices for the current TTS engine
    responses:
      200:
        description: List of available voices
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Voice ID
              name:
                type: string
                description: Voice name
              languages:
                type: array
                items:
                  type: string
                description: Supported languages
              gender:
                type: string
                description: Voice gender
    """
    voices = _app().game_manager.tts.get_available_voices()
    return jsonify(voices)


@services_bp.route("/api/tts/languages", methods=["GET"])
def get_tts_languages():
    """Get supported TTS languages
    ---
    tags:
      - TTS
    summary: Get supported TTS languages
    description: Returns a list of all supported languages for TTS
    responses:
      200:
        description: Dictionary of supported languages
        schema:
          type: object
          additionalProperties:
            type: string
          example:
            en: English
            nl: Dutch
            de: German
            fr: French
            es: Spanish
    """
    from dartserver_services.tts_service import TTSService  # noqa: PLC0415

    languages = TTSService.get_supported_languages()
    return jsonify(languages)


@services_bp.route("/api/tts/test", methods=["POST"])
def test_tts():
    """Test TTS with custom text
    ---
    tags:
      - TTS
    summary: Test TTS
    description: Speaks the provided text using the current TTS configuration
    parameters:
      - in: body
        name: body
        description: Text to speak
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              description: Text to speak
              example: Hello, this is a test
    responses:
      200:
        description: TTS test completed
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: TTS test completed
    """
    data = request.json
    text = data.get("text", "This is a test")

    success = _app().game_manager.tts.speak(text)

    if success:
        return jsonify({"status": "success", "message": "TTS test completed"})
    return jsonify({"status": "error", "message": "TTS test failed"}), 500


@services_bp.route("/api/tts/generate", methods=["POST"])
def generate_tts_audio():
    """Generate TTS audio data
    ---
    tags:
      - TTS
    summary: Generate TTS audio
    description: Generates audio data for the provided text using the current TTS configuration
    parameters:
      - in: body
        name: body
        description: Text to convert to speech
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              description: Text to convert to speech
              example: Hello, this is a test
            lang:
              type: string
              description: Language code (for gTTS)
              example: en
              default: en
    responses:
      200:
        description: Audio data generated successfully
        content:
          audio/mpeg:
            schema:
              type: string
              format: binary
      400:
        description: Bad request
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Text is required
      500:
        description: TTS generation failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Failed to generate audio
    """
    data = request.json
    text = data.get("text")
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"status": "error", "message": "Text is required"}), 400

    audio_data = _app().game_manager.tts.generate_audio_data(text, lang)

    if audio_data:
        return Response(audio_data, mimetype="audio/mpeg")
    return jsonify({"status": "error", "message": "Failed to generate audio"}), 500


@services_bp.route("/api/admin/tts/player", methods=["GET"])
@role_required("admin")
def tts_player():
    """TTS player UI for testing
    ---
    tags:
      - TTS
    summary: TTS Audio Player
    description: Interactive HTML page for testing TTS with built-in audio player (admin only)
    parameters:
      - in: query
        name: text
        type: string
        description: Text to generate audio for
        example: "Hello, this is a test"
        required: false
    responses:
      200:
        description: HTML page with audio player
        content:
          text/html:
            schema:
              type: string
      403:
        description: Forbidden - admin role required
    """
    text = request.args.get("text", "Hello, this is a test message")
    return render_template(
        "tts_player.html",
        initial_text=text,
    )


# SocketIO Events


@services_bp.route("/mobile")
@login_required
def mobile_app():
    """Mobile app main page
    ---
    tags:
      - UI
    summary: Mobile app interface
    description: Mobile-optimized PWA interface for dartboard management
    responses:
      200:
        description: Mobile app HTML page
    """
    return render_template("mobile.html")


@services_bp.route("/mobile/gameplay")
@login_required
def mobile_gameplay():
    """Mobile gameplay page
    ---
    tags:
      - UI
    summary: Mobile gameplay interface
    description: Mobile interface for active gameplay
    responses:
      200:
        description: Mobile gameplay HTML page
    """
    return render_template("mobile_gameplay.html")


@services_bp.route("/mobile/gamemaster")
@login_required
@role_required("gamemaster")
def mobile_gamemaster():
    """Mobile game master control page
    ---
    tags:
      - UI
    summary: Mobile game master interface
    description: Mobile interface for game master controls
    responses:
      200:
        description: Mobile game master HTML page
    """
    return render_template("mobile_gamemaster.html")


@services_bp.route("/mobile/dartboard-setup")
@login_required
def mobile_dartboard_setup():
    """Mobile dartboard setup page
    ---
    tags:
      - UI
    summary: Mobile dartboard setup interface
    description: Mobile interface for dartboard configuration
    responses:
      200:
        description: Mobile dartboard setup HTML page
    """
    return render_template("mobile_dartboard_setup.html")


@services_bp.route("/mobile/results")
@login_required
def mobile_results():
    """Mobile game results page
    ---
    tags:
      - UI
    summary: Mobile game results interface
    description: Mobile interface for viewing game history
    responses:
      200:
        description: Mobile game results HTML page
    """
    return render_template("mobile_results.html")


@services_bp.route("/mobile/account")
@login_required
def mobile_account():
    """Mobile account management page
    ---
    tags:
      - UI
    summary: Mobile account management interface
    description: Mobile interface for account settings, API keys, and dartboards
    responses:
      200:
        description: Mobile account management HTML page
    """
    return render_template("mobile_account.html")


@services_bp.route("/mobile/hotspot")
@login_required
def mobile_hotspot():
    """Mobile hotspot control page
    ---
    tags:
      - UI
    summary: Mobile hotspot control interface
    description: Mobile interface for managing dartboard hotspot connections
    responses:
      200:
        description: Mobile hotspot control HTML page
    """
    return render_template("mobile_hotspot.html")


# API Key Management Endpoints


@services_bp.route("/api/mobile/apikeys", methods=["GET"])
@login_required
def get_api_keys():
    """Get user's API keys
    ---
    tags:
      - Mobile
    summary: Get API keys
    description: Returns all API keys for the authenticated user
    responses:
      200:
        description: List of API keys
        schema:
          type: object
          properties:
            success:
              type: boolean
            api_keys:
              type: array
              items:
                type: object
    """
    mobile_service = get_mobile_service()
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    api_keys = mobile_service.get_user_api_keys(player_id)
    return jsonify({"success": True, "api_keys": api_keys})


@services_bp.route("/api/mobile/apikeys", methods=["POST"])
@login_required
def create_api_key():
    """Create new API key
    ---
    tags:
      - Mobile
    summary: Create API key
    description: Creates a new API key for the authenticated user
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            key_name:
              type: string
              description: Friendly name for the API key
    responses:
      200:
        description: API key created
        schema:
          type: object
          properties:
            success:
              type: boolean
            api_key:
              type: object
    """
    data = request.json
    key_name = data.get("key_name", "Default Key")
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    mobile_service = get_mobile_service()
    result = mobile_service.create_api_key(player_id, key_name)
    return jsonify(result)


@services_bp.route("/api/mobile/apikeys/<int:key_id>", methods=["DELETE"])
@login_required
def revoke_api_key(key_id):
    """Revoke API key
    ---
    tags:
      - Mobile
    summary: Revoke API key
    description: Revokes (deactivates) an API key
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
    responses:
      200:
        description: API key revoked
        schema:
          type: object
          properties:
            success:
              type: boolean
    """
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    mobile_service = get_mobile_service()
    result = mobile_service.revoke_api_key(key_id, player_id)
    return jsonify(result)


# Dartboard Management Endpoints


@services_bp.route("/api/mobile/dartboards", methods=["GET"])
@login_required
def get_dartboards():
    """Get user's dartboards
    ---
    tags:
      - Mobile
    summary: Get dartboards
    description: Returns all dartboards for the authenticated user
    responses:
      200:
        description: List of dartboards
        schema:
          type: object
          properties:
            success:
              type: boolean
            dartboards:
              type: array
              items:
                type: object
    """
    mobile_service = get_mobile_service()
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    dartboards = mobile_service.get_user_dartboards(player_id)
    return jsonify({"success": True, "dartboards": dartboards})


@services_bp.route("/api/mobile/dartboards", methods=["POST"])
@login_required
def register_dartboard():
    """Register new dartboard
    ---
    tags:
      - Mobile
    summary: Register dartboard
    description: Registers a new dartboard for the authenticated user
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            dartboard_id:
              type: string
              description: Unique dartboard identifier
            name:
              type: string
              description: Friendly name for the dartboard
            wpa_key:
              type: string
              description: WPA key for hotspot connection
    responses:
      200:
        description: Dartboard registered
        schema:
          type: object
          properties:
            success:
              type: boolean
            dartboard:
              type: object
    """
    data = request.json
    dartboard_id = data.get("dartboard_id")
    name = data.get("name")
    wpa_key = data.get("wpa_key")
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    if not all([dartboard_id, name, wpa_key]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    mobile_service = get_mobile_service()
    result = mobile_service.register_dartboard(player_id, dartboard_id, name, wpa_key)
    return jsonify(result)


@services_bp.route("/api/mobile/dartboards/<int:dartboard_id>", methods=["DELETE"])
@login_required
def delete_dartboard(dartboard_id):
    """Delete dartboard
    ---
    tags:
      - Mobile
    summary: Delete dartboard
    description: Deletes a dartboard
    parameters:
      - in: path
        name: dartboard_id
        type: integer
        required: true
    responses:
      200:
        description: Dartboard deleted
        schema:
          type: object
          properties:
            success:
              type: boolean
    """
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    mobile_service = get_mobile_service()
    result = mobile_service.delete_dartboard(dartboard_id, player_id)
    return jsonify(result)


# Hotspot Configuration Endpoints


@services_bp.route("/api/mobile/hotspot", methods=["GET"])
@login_required
def get_hotspot_configs():
    """Get hotspot configurations
    ---
    tags:
      - Mobile
    summary: Get hotspot configurations
    description: Returns all hotspot configurations for the authenticated user
    responses:
      200:
        description: List of hotspot configurations
        schema:
          type: object
          properties:
            success:
              type: boolean
            configs:
              type: array
              items:
                type: object
    """
    mobile_service = get_mobile_service()
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    configs = mobile_service.get_hotspot_configs(player_id)
    return jsonify({"success": True, "configs": configs})


@services_bp.route("/api/mobile/hotspot", methods=["POST"])
@login_required
def create_hotspot_config():
    """Create hotspot configuration
    ---
    tags:
      - Mobile
    summary: Create hotspot configuration
    description: Creates or updates hotspot configuration for a dartboard
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            dartboard_id:
              type: integer
              description: Dartboard database ID
            ssid:
              type: string
              description: Hotspot SSID
            password:
              type: string
              description: Hotspot password
    responses:
      200:
        description: Hotspot configuration created
        schema:
          type: object
          properties:
            success:
              type: boolean
            config:
              type: object
    """
    data = request.json
    dartboard_id = data.get("dartboard_id")
    ssid = data.get("ssid")
    password = data.get("password")
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    if not all([dartboard_id, ssid, password]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    mobile_service = get_mobile_service()
    result = mobile_service.create_hotspot_config(player_id, dartboard_id, ssid, password)
    return jsonify(result)


@services_bp.route("/api/mobile/hotspot/<int:config_id>/toggle", methods=["POST"])
@login_required
def toggle_hotspot(config_id):
    """Toggle hotspot on/off
    ---
    tags:
      - Mobile
    summary: Toggle hotspot
    description: Enables or disables a hotspot configuration
    parameters:
      - in: path
        name: config_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            enabled:
              type: boolean
              description: True to enable, False to disable
    responses:
      200:
        description: Hotspot toggled
        schema:
          type: object
          properties:
            success:
              type: boolean
            is_enabled:
              type: boolean
    """
    data = request.json
    enabled = data.get("enabled", False)
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    mobile_service = get_mobile_service()
    result = mobile_service.toggle_hotspot(config_id, player_id, enabled)
    return jsonify(result)


# Dartboard API Endpoints (authenticated with API key)


@services_bp.route("/api/dartboard/connect", methods=["POST"])
@api_key_required
def dartboard_connect():
    """Dartboard connection endpoint
    ---
    tags:
      - Mobile
    summary: Dartboard connect
    description: Called by dartboard when it connects (requires API key)
    parameters:
      - in: header
        name: X-API-Key
        type: string
        required: true
        description: API key for authentication
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            dartboard_id:
              type: string
              description: Dartboard identifier
    responses:
      200:
        description: Connection acknowledged
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    data = request.json
    dartboard_id = data.get("dartboard_id")

    if not dartboard_id:
        return jsonify({"success": False, "error": "Missing dartboard_id"}), 400

    mobile_service = get_mobile_service()
    success = mobile_service.update_dartboard_connection(dartboard_id)

    if success:
        return jsonify({"success": True, "message": "Connection acknowledged"})
    return jsonify({"success": False, "error": "Dartboard not found"}), 404


@services_bp.route("/api/dartboard/score", methods=["POST"])
@api_key_required
def dartboard_submit_score():
    """Dartboard score submission endpoint
    ---
    tags:
      - Mobile
    summary: Submit score from dartboard
    description: Called by dartboard to submit scores (requires API key)
    parameters:
      - in: header
        name: X-API-Key
        type: string
        required: true
        description: API key for authentication
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            score:
              type: integer
              description: Base score value
            multiplier:
              type: string
              description: Multiplier type
    responses:
      200:
        description: Score submitted
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    data = request.json
    # Process score through game manager
    _app().game_manager.process_score(data)
    return jsonify({"success": True, "message": "Score submitted"})
