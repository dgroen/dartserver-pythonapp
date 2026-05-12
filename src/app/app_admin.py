"""
Admin API endpoints
"""

import logging
import os
from datetime import datetime

import requests
from dartserver_core.auth import (
    get_wso2_active_sessions,
    get_wso2_user_info,
    login_required,
    role_required,
    search_wso2_users,
)
from dartserver_core.database_models import GameResult, GameType, Player, Score
from dartserver_core.database_service import get_session
from flask import Blueprint, jsonify, request
from sqlalchemy import Integer, func

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/users/search", methods=["GET"])
@login_required
@role_required("admin")
def search_users():
    """Search for WSO2 users
    ---
    tags:
      - Admin
    summary: Search users
    description: Search for users in WSO2 by username, email, or name
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query
    responses:
      200:
        description: List of matching users
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            users:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  username:
                    type: string
                  email:
                    type: string
                  name:
                    type: string
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Query parameter required"}), 400

    try:
        users = search_wso2_users(query)
        return jsonify({"status": "success", "users": users})
    except Exception as e:
        logger.exception("Error searching users")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/users", methods=["GET"])
@login_required
@role_required("admin")
def list_all_users():
    """List all WSO2 users
    ---
    tags:
      - Admin
    summary: List all users
    description: Get a list of all users in WSO2
    responses:
      200:
        description: List of all users
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            users:
              type: array
              items:
                type: object
    """
    try:
        # Search with empty query returns all users
        users = search_wso2_users("")
        return jsonify({"status": "success", "users": users})
    except Exception as e:
        logger.exception("Error listing users")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/users", methods=["POST"])
@login_required
@role_required("admin")
def create_user():
    """Create a new WSO2 user
    ---
    tags:
      - Admin
    summary: Create user
    description: Create a new user in WSO2
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
            email:
              type: string
            givenName:
              type: string
            familyName:
              type: string
    responses:
      200:
        description: User created successfully
      400:
        description: Invalid request
      500:
        description: Server error
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    given_name = data.get("givenName")
    family_name = data.get("familyName")

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    try:
        # Create user via SCIM2 API
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        scim_users_url = f"{wso2_url}/scim2/Users"

        # Build SCIM2 user object
        scim_user = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": username,
            "password": password,
        }

        if email:
            scim_user["emails"] = [{"value": email, "type": "work", "primary": True}]

        if given_name or family_name:
            scim_user["name"] = {}
            if given_name:
                scim_user["name"]["givenName"] = given_name
            if family_name:
                scim_user["name"]["familyName"] = family_name

        # Use admin credentials
        auth_user = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
        auth_pass = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")

        response = requests.post(
            scim_users_url,
            json=scim_user,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true",
            timeout=10,
        )

        if response.status_code == 201:
            user_data = response.json()
            logger.info(f"User '{username}' created successfully")
            return jsonify(
                {
                    "status": "success",
                    "message": "User created successfully",
                    "user": {
                        "id": user_data.get("id"),
                        "username": user_data.get("userName"),
                    },
                },
            )
        logger.error(f"Failed to create user: {response.status_code} - {response.text}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to create user: {response.text}",
                },
            ),
            response.status_code,
        )
    except Exception as e:
        logger.exception("Error creating user")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/users/password", methods=["PUT"])
@login_required
@role_required("admin")
def set_user_password():
    """Set user password
    ---
    tags:
      - Admin
    summary: Set user password
    description: Set or update a user's password
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Password updated successfully
      400:
        description: Invalid request
      500:
        description: Server error
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    try:
        # First, find the user ID
        user_info = get_wso2_user_info(username)
        if not user_info or not user_info.get("id"):
            return jsonify({"status": "error", "message": "User not found"}), 404

        user_id = user_info["id"]

        # Update password via SCIM2 API
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        scim_user_url = f"{wso2_url}/scim2/Users/{user_id}"

        scim_update = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "value": {"password": password}}],
        }

        auth_user = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
        auth_pass = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")

        response = requests.patch(
            scim_user_url,
            json=scim_update,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true",
            timeout=10,
        )

        if response.status_code in [200, 204]:
            logger.info(f"Password updated for user '{username}'")
            return jsonify({"status": "success", "message": "Password updated successfully"})
        logger.error(f"Failed to update password: {response.status_code} - {response.text}")
        return (
            jsonify(
                {"status": "error", "message": f"Failed to update password: {response.text}"},
            ),
            response.status_code,
        )
    except Exception as e:
        logger.exception("Error setting password")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/users/<user_id>/roles", methods=["GET"])
@login_required
@role_required("admin")
def get_user_roles(user_id):
    """Get user roles
    ---
    tags:
      - Admin
    summary: Get user roles
    description: Get list of roles assigned to a user
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: User roles retrieved
    """
    try:
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        scim_user_url = f"{wso2_url}/scim2/Users/{user_id}"

        auth_user = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
        auth_pass = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")

        response = requests.get(
            scim_user_url,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true",
            timeout=10,
        )

        if response.status_code == 200:
            user_data = response.json()
            roles = []

            # Extract roles from groups
            if "groups" in user_data and isinstance(user_data["groups"], list):
                for group in user_data["groups"]:
                    if isinstance(group, dict):
                        display_name = group.get("display", "")
                        # Extract role name from display (e.g., "PRIMARY/admin" -> "admin")
                        if "/" in display_name:
                            role_name = display_name.split("/")[-1].lower()
                        else:
                            role_name = display_name.lower()

                        if role_name in ["admin", "gamemaster", "player"]:
                            roles.append(role_name)

            return jsonify({"status": "success", "roles": roles})
        return (
            jsonify(
                {"status": "error", "message": "Failed to get user roles"},
            ),
            response.status_code,
        )
    except Exception as e:
        logger.exception("Error getting user roles")
        return jsonify({"status": "error", "message": str(e)}), 500


def _extract_role_name(display_name: str) -> str:
    """Extract role name from WSO2 group display name.

    Args:
        display_name: Group display name (e.g., "PRIMARY/admin" or "admin")

    Returns:
        Lowercase role name (e.g., "admin")
    """
    if "/" in display_name:
        return display_name.split("/")[-1].lower()
    return display_name.lower()


@admin_bp.route("/users/<user_id>/roles", methods=["PUT"])
@login_required
@role_required("admin")
def update_user_roles(user_id):
    """Update user roles
    ---
    tags:
      - Admin
    summary: Update user roles
    description: Update the roles assigned to a user
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - roles
          properties:
            roles:
              type: array
              items:
                type: string
    responses:
      200:
        description: Roles updated successfully
    """
    data = request.get_json()
    new_roles = data.get("roles", [])

    try:
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        auth_user = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
        auth_pass = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")
        verify_ssl = os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true"

        # First, get current user to find existing groups and username
        scim_user_url = f"{wso2_url}/scim2/Users/{user_id}"
        user_response = requests.get(
            scim_user_url,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=verify_ssl,
            timeout=10,
        )

        if user_response.status_code != 200:
            return (
                jsonify(
                    {"status": "error", "message": "Failed to fetch user"},
                ),
                user_response.status_code,
            )

        user_data = user_response.json()
        username = user_data.get("userName", "")
        current_groups = user_data.get("groups", [])

        # Extract current role names
        current_roles = set()
        for group in current_groups:
            display_name = group.get("display", "")
            role_name = _extract_role_name(display_name)
            if role_name in ["admin", "gamemaster", "player"]:
                current_roles.add(role_name)

        # Get all available groups to map role names to group IDs
        scim_groups_url = f"{wso2_url}/scim2/Groups"
        groups_response = requests.get(
            scim_groups_url,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=verify_ssl,
            timeout=10,
        )

        if groups_response.status_code != 200:
            return (
                jsonify(
                    {"status": "error", "message": "Failed to fetch groups"},
                ),
                groups_response.status_code,
            )

        groups_data = groups_response.json()
        role_to_group = {}

        if "Resources" in groups_data:
            for group in groups_data["Resources"]:
                display_name = group.get("displayName", "")
                group_id = group.get("id")
                role_name = _extract_role_name(display_name)

                if role_name in ["admin", "gamemaster", "player"]:
                    role_to_group[role_name] = {"id": group_id, "display": display_name}

        # Determine roles to add and remove
        new_roles_set = set(new_roles)
        roles_to_add = new_roles_set - current_roles
        roles_to_remove = current_roles - new_roles_set

        # Track failed operations for error reporting
        failed_operations = []

        # Add user to new groups
        for role in roles_to_add:
            if role not in role_to_group:
                logger.warning(f"Role '{role}' not found in WSO2, skipping")
                failed_operations.append(f"Role '{role}' not found")
                continue

            group_id = role_to_group[role]["id"]
            scim_group_url = f"{wso2_url}/scim2/Groups/{group_id}"

            # Add user to group using PATCH on the Group resource
            patch_payload = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                "Operations": [
                    {
                        "op": "add",
                        "path": "members",
                        "value": [{"value": user_id, "display": username}],
                    },
                ],
            }

            add_response = requests.patch(
                scim_group_url,
                json=patch_payload,
                auth=(auth_user, auth_pass),
                headers={"Content-Type": "application/scim+json"},
                verify=verify_ssl,
                timeout=10,
            )

            if add_response.status_code not in [200, 204]:
                error_msg = f"Failed to add role '{role}': {add_response.text}"
                logger.error(error_msg)
                failed_operations.append(error_msg)

        # Remove user from old groups
        for role in roles_to_remove:
            if role not in role_to_group:
                continue

            group_id = role_to_group[role]["id"]
            scim_group_url = f"{wso2_url}/scim2/Groups/{group_id}"

            # Remove user from group using PATCH on the Group resource
            patch_payload = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                "Operations": [
                    {
                        "op": "remove",
                        "path": f'members[value eq "{user_id}"]',
                    },
                ],
            }

            remove_response = requests.patch(
                scim_group_url,
                json=patch_payload,
                auth=(auth_user, auth_pass),
                headers={"Content-Type": "application/scim+json"},
                verify=verify_ssl,
                timeout=10,
            )

            if remove_response.status_code not in [200, 204]:
                error_msg = f"Failed to remove role '{role}': {remove_response.text}"
                logger.error(error_msg)
                failed_operations.append(error_msg)

        # Report results
        if failed_operations:
            logger.warning(
                f"Role update completed with errors for user {user_id}: {failed_operations}",
            )
            return (
                jsonify(
                    {
                        "status": "partial",
                        "message": "Some role changes failed",
                        "errors": failed_operations,
                    },
                ),
                207,  # Multi-Status
            )

        logger.info(
            f"Roles updated for user {user_id}: added {roles_to_add}, removed {roles_to_remove}",
        )
        return jsonify({"status": "success", "message": "Roles updated successfully"})
    except Exception as e:
        logger.exception("Error updating user roles")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/users/<user_id>/status", methods=["PUT"])
@login_required
@role_required("admin")
def update_user_status(user_id):
    """Activate/Deactivate user
    ---
    tags:
      - Admin
    summary: Update user status
    description: Activate or deactivate a user account
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - active
          properties:
            active:
              type: boolean
    responses:
      200:
        description: Status updated successfully
    """
    data = request.get_json()
    active = data.get("active", True)

    try:
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        scim_user_url = f"{wso2_url}/scim2/Users/{user_id}"
        auth_user = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
        auth_pass = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")
        verify_ssl = os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true"

        # Use PATCH operation with path-based operation for better compatibility
        scim_update = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "active",
                    "value": active,
                },
            ],
        }

        response = requests.patch(
            scim_user_url,
            json=scim_update,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=verify_ssl,
            timeout=10,
        )

        if response.status_code in [200, 204]:
            status_text = "activated" if active else "deactivated"
            logger.info(f"User {user_id} {status_text}")
            return jsonify({"status": "success", "message": f"User {status_text} successfully"})

        # If path-based operation fails, try value-based operation as fallback
        logger.warning(
            f"Path-based PATCH failed ({response.status_code}), trying value-based PATCH",
        )
        scim_update_fallback = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "value": {"active": active}}],
        }

        response = requests.patch(
            scim_user_url,
            json=scim_update_fallback,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=verify_ssl,
            timeout=10,
        )

        if response.status_code in [200, 204]:
            status_text = "activated" if active else "deactivated"
            logger.info(f"User {user_id} {status_text} (using fallback method)")
            return jsonify({"status": "success", "message": f"User {status_text} successfully"})

        logger.error(f"Failed to update status: {response.status_code} - {response.text}")
        return (
            jsonify(
                {"status": "error", "message": f"Failed to update status: {response.text}"},
            ),
            response.status_code,
        )
    except Exception as e:
        logger.exception("Error updating user status")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/tts/test", methods=["POST"])
@login_required
@role_required("admin")
def test_tts():
    """Test TTS generation
    ---
    tags:
      - Admin
    summary: Test TTS
    description: Test server-side TTS generation
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
    responses:
      200:
        description: TTS audio generated
    """
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"status": "error", "message": "Text required"}), 400

    # For now, return a placeholder response
    # In production, this would integrate with actual TTS service
    return jsonify(
        {
            "status": "success",
            "message": "TTS testing endpoint - integration pending",
            "audio_url": None,
        },
    )


@admin_bp.route("/games/paused", methods=["GET"])
@login_required
@role_required("admin")
def get_paused_games():
    """Get list of paused games
    ---
    tags:
      - Admin
    summary: Get paused games
    description: Get all games that haven't finished yet
    responses:
      200:
        description: List of paused games
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            games:
              type: array
              items:
                type: object
    """
    try:
        with get_session() as session:
            # Query for games without a finished_at timestamp
            paused_games = (
                session.query(GameResult)
                .filter(GameResult.finished_at.is_(None))
                .join(Player, GameResult.player_id == Player.id)
                .join(GameType, GameResult.game_type_id == GameType.id)
                .all()
            )

            games_list = []
            for game in paused_games:
                games_list.append(
                    {
                        "id": game.id,
                        "game_session_id": game.game_session_id,
                        "game_type": game.game_type.name if game.game_type else None,
                        "player_name": game.player.name if game.player else None,
                        "player_id": game.player_id,
                        "started_at": game.started_at.isoformat() if game.started_at else None,
                        "final_score": game.final_score,
                        "start_score": game.start_score,
                    },
                )

            logger.info(f"Retrieved {len(games_list)} paused games")
            return jsonify({"status": "success", "games": games_list})
    except Exception as e:
        logger.exception("Error retrieving paused games")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/games/paused", methods=["DELETE"])
@login_required
@role_required("admin")
def remove_paused_games():
    """Remove all paused games
    ---
    tags:
      - Admin
    summary: Remove paused games
    description: Delete all games that haven't finished yet
    responses:
      200:
        description: Paused games removed
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            deleted_count:
              type: integer
    """
    try:
        with get_session() as session:
            # Find all paused games (no finished_at)
            paused_games = session.query(GameResult).filter(GameResult.finished_at.is_(None)).all()

            deleted_count = len(paused_games)

            # Delete associated scores first (cascade should handle this, but being explicit)
            for game in paused_games:
                session.query(Score).filter(Score.game_result_id == game.id).delete()

            # Delete the game results
            session.query(GameResult).filter(GameResult.finished_at.is_(None)).delete()

            session.commit()
            logger.info(f"Deleted {deleted_count} paused games")
            return jsonify({"status": "success", "deleted_count": deleted_count})
    except Exception as e:
        logger.exception("Error deleting paused games")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/games/archive", methods=["POST"])
@login_required
@role_required("admin")
def archive_games():
    """Archive games by user and date range
    ---
    tags:
      - Admin
    summary: Archive games
    description: Archive games for a specific user within a date range
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - start_date
            - end_date
          properties:
            username:
              type: string
            start_date:
              type: string
              format: date
            end_date:
              type: string
              format: date
    responses:
      200:
        description: Games archived
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            archived_count:
              type: integer
    """
    data = request.get_json()
    username = data.get("username")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not username or not start_date_str or not end_date_str:
        return (
            jsonify(
                {"status": "error", "message": "Username, start_date, and end_date required"},
            ),
            400,
        )

    try:
        # Parse dates
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        # Add end of day to end_date
        end_date = end_date.replace(hour=23, minute=59, second=59)

        with get_session() as session:
            # Find the player by username
            player = session.query(Player).filter(Player.username == username).first()

            if not player:
                return (
                    jsonify(
                        {"status": "error", "message": f"Player '{username}' not found"},
                    ),
                    404,
                )

            # Query games in date range for this player
            games_to_archive = (
                session.query(GameResult)
                .filter(
                    GameResult.player_id == player.id,
                    GameResult.started_at >= start_date,
                    GameResult.started_at <= end_date,
                )
                .all()
            )

            archived_count = len(games_to_archive)

            # Note: In a real implementation, you might want to move these to an archive table
            # or mark them as archived. For now, we'll just return the count.
            # If actual archiving is needed, implement the logic here.

            logger.info(f"Found {archived_count} games to archive for user {username}")
            return jsonify(
                {
                    "status": "success",
                    "archived_count": archived_count,
                    "message": f"Found {archived_count} games in the specified date range",
                },
            )
    except ValueError as e:
        return jsonify({"status": "error", "message": f"Invalid date format: {e!s}"}), 400
    except Exception as e:
        logger.exception("Error archiving games")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/active-sessions", methods=["GET"])
@login_required
@role_required("admin")
def get_active_sessions():
    """Get active user sessions
    ---
    tags:
      - Admin
    summary: Get active sessions
    description: Get list of currently active user sessions from WSO2 Identity Server
    responses:
      200:
        description: List of active sessions
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            sessions:
              type: array
              items:
                type: object
                properties:
                  username:
                    type: string
                  session_id:
                    type: string
                  login_time:
                    type: string
                  last_activity:
                    type: string
                  ip:
                    type: string
                  user_agent:
                    type: string
                  applications:
                    type: array
                    items:
                      type: string
    """
    try:
        sessions = get_wso2_active_sessions()
        logger.info(f"Retrieved {len(sessions)} active sessions from WSO2 IS")
        return jsonify(
            {
                "status": "success",
                "sessions": sessions,
            },
        )
    except Exception as e:
        logger.exception("Error retrieving active sessions")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/statistics", methods=["GET"])
@login_required
@role_required("admin")
def get_user_statistics():
    """Get user statistics
    ---
    tags:
      - Admin
    summary: Get user statistics
    description: Get aggregated statistics for all users with optional date filters
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        description: Start date for filtering
      - name: end_date
        in: query
        type: string
        format: date
        description: End date for filtering
    responses:
      200:
        description: User statistics
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            statistics:
              type: array
              items:
                type: object
                properties:
                  username:
                    type: string
                  total_games:
                    type: integer
                  games_won:
                    type: integer
                  win_rate:
                    type: number
                  avg_score:
                    type: number
                  best_score:
                    type: integer
                  total_throws:
                    type: integer
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        with get_session() as session:
            # Base query
            query = (
                session.query(
                    Player.username,
                    func.count(GameResult.id).label("total_games"),
                    func.sum(func.cast(GameResult.is_winner, Integer)).label("games_won"),
                    func.avg(GameResult.final_score).label("avg_score"),
                    func.max(GameResult.final_score).label("best_score"),
                    func.count(Score.id).label("total_throws"),
                )
                .join(GameResult, Player.id == GameResult.player_id)
                .outerjoin(Score, GameResult.id == Score.game_result_id)
            )

            # Apply date filters if provided
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str)
                query = query.filter(GameResult.started_at >= start_date)

            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str)
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query = query.filter(GameResult.started_at <= end_date)

            # Group by player
            query = query.group_by(Player.id, Player.username)

            results = query.all()

            statistics = []
            for row in results:
                username, total_games, games_won, avg_score, best_score, total_throws = row

                # Calculate win rate
                win_rate = (games_won / total_games * 100) if total_games > 0 else 0

                statistics.append(
                    {
                        "username": username or "Unknown",
                        "total_games": total_games or 0,
                        "games_won": games_won or 0,
                        "win_rate": float(win_rate),
                        "avg_score": float(avg_score) if avg_score else 0,
                        "best_score": best_score or 0,
                        "total_throws": total_throws or 0,
                    },
                )

            logger.info(f"Retrieved statistics for {len(statistics)} users")
            return jsonify({"status": "success", "statistics": statistics})
    except ValueError as e:
        return jsonify({"status": "error", "message": f"Invalid date format: {e!s}"}), 400
    except Exception as e:
        logger.exception("Error retrieving statistics")
        return jsonify({"status": "error", "message": str(e)}), 500
