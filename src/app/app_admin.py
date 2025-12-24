"""
Admin API endpoints
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from src.core.auth import login_required, role_required
from src.core.database_models import GameResult, Player, Score
from src.core.database_service import get_session

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
    from src.core.auth import search_wso2_users

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
    from src.core.auth import search_wso2_users

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
    import os

    import requests

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
                }
            )
        else:
            logger.error(f"Failed to create user: {response.status_code} - {response.text}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to create user: {response.text}",
                    }
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
    import os

    import requests

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    try:
        # First, find the user ID
        from src.core.auth import get_wso2_user_info

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
        else:
            logger.error(f"Failed to update password: {response.status_code} - {response.text}")
            return (
                jsonify({"status": "error", "message": f"Failed to update password: {response.text}"}),
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
    import os

    import requests

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
        else:
            return jsonify({"status": "error", "message": "Failed to get user roles"}), response.status_code
    except Exception as e:
        logger.exception("Error getting user roles")
        return jsonify({"status": "error", "message": str(e)}), 500


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
    import os

    import requests

    data = request.get_json()
    roles = data.get("roles", [])

    try:
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        auth_user = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
        auth_pass = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")

        # First, get current user to find existing groups
        scim_user_url = f"{wso2_url}/scim2/Users/{user_id}"
        response = requests.get(
            scim_user_url,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true",
            timeout=10,
        )

        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to fetch user"}), response.status_code

        # Get all available groups to map role names to group IDs
        scim_groups_url = f"{wso2_url}/scim2/Groups"
        groups_response = requests.get(
            scim_groups_url,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true",
            timeout=10,
        )

        if groups_response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to fetch groups"}), groups_response.status_code

        groups_data = groups_response.json()
        role_to_group_id = {}

        if "Resources" in groups_data:
            for group in groups_data["Resources"]:
                display_name = group.get("displayName", "")
                group_id = group.get("id")
                # Map role names (e.g., "PRIMARY/admin" -> "admin": group_id)
                if "/" in display_name:
                    role_name = display_name.split("/")[-1].lower()
                else:
                    role_name = display_name.lower()

                if role_name in ["admin", "gamemaster", "player"]:
                    role_to_group_id[role_name] = group_id

        # Build groups array for update
        new_groups = []
        for role in roles:
            if role in role_to_group_id:
                new_groups.append({"value": role_to_group_id[role]})

        # Update user with new groups
        scim_update = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "value": {"groups": new_groups}}],
        }

        update_response = requests.patch(
            scim_user_url,
            json=scim_update,
            auth=(auth_user, auth_pass),
            headers={"Content-Type": "application/scim+json"},
            verify=os.getenv("WSO2_IS_VERIFY_SSL", "true").lower() == "true",
            timeout=10,
        )

        if update_response.status_code in [200, 204]:
            logger.info(f"Roles updated for user {user_id}")
            return jsonify({"status": "success", "message": "Roles updated successfully"})
        else:
            logger.error(f"Failed to update roles: {update_response.status_code} - {update_response.text}")
            return (
                jsonify({"status": "error", "message": f"Failed to update roles: {update_response.text}"}),
                update_response.status_code,
            )
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
    import os

    import requests

    data = request.get_json()
    active = data.get("active", True)

    try:
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://localhost:9443")
        scim_user_url = f"{wso2_url}/scim2/Users/{user_id}"

        scim_update = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "value": {"active": active}}],
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
            status_text = "activated" if active else "deactivated"
            logger.info(f"User {user_id} {status_text}")
            return jsonify({"status": "success", "message": f"User {status_text} successfully"})
        else:
            logger.error(f"Failed to update status: {response.status_code} - {response.text}")
            return (
                jsonify({"status": "error", "message": f"Failed to update status: {response.text}"}),
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
        }
    )
