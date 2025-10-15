#!/usr/bin/env python3
"""
WSO2 Identity Server - Interactive Role Management
This script provides an interactive CLI for managing user roles
"""

import argparse
import sys

import requests

# WSO2 IS Configuration
WSO2_IS_URL = "https://letsplaydarts.eu/auth"
WSO2_ADMIN_USER = "admin"
WSO2_ADMIN_PASSWORD = "admin"

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()


class WSO2Manager:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = (username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_user_by_username(self, username):
        """Get user by username"""
        url = f"{self.base_url}/scim2/Users"
        params = {"filter": f'userName eq "{username}"'}
        response = requests.get(
            url, auth=self.auth, headers=self.headers, params=params, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("totalResults", 0) > 0:
                return data["Resources"][0]
        return None

    def get_group_by_name(self, group_name):
        """Get group by name"""
        url = f"{self.base_url}/scim2/Groups"
        params = {"filter": f'displayName eq "{group_name}"'}
        response = requests.get(
            url, auth=self.auth, headers=self.headers, params=params, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("totalResults", 0) > 0:
                return data["Resources"][0]
        return None

    def create_group(self, group_name):
        """Create a new group"""
        url = f"{self.base_url}/scim2/Groups"
        payload = {
            "displayName": group_name,
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        }
        response = requests.post(
            url, auth=self.auth, headers=self.headers, json=payload, verify=False
        )

        if response.status_code == 201:
            return response.json()
        return None

    def add_user_to_group(self, user_id, user_name, group_id):
        """Add user to group"""
        url = f"{self.base_url}/scim2/Groups/{group_id}"
        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "members",
                    "value": [{"value": user_id, "display": user_name}],
                },
            ],
        }
        response = requests.patch(
            url, auth=self.auth, headers=self.headers, json=payload, verify=False
        )
        return response.status_code in [200, 204]

    def remove_user_from_group(self, user_id, group_id):
        """Remove user from group"""
        url = f"{self.base_url}/scim2/Groups/{group_id}"
        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "remove",
                    "path": f'members[value eq "{user_id}"]',
                },
            ],
        }
        response = requests.patch(
            url, auth=self.auth, headers=self.headers, json=payload, verify=False
        )
        return response.status_code in [200, 204]

    def list_user_groups(self, user_id):
        """List all groups for a user"""
        url = f"{self.base_url}/scim2/Users/{user_id}"
        response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)

        if response.status_code == 200:
            user = response.json()
            return user.get("groups", [])
        return []


def add_role(manager, username, role):
    """Add a role to a user"""
    print(f"\n🎯 Adding role '{role}' to user '{username}'")

    # Get user
    user = manager.get_user_by_username(username)
    if not user:
        print(f"❌ User '{username}' not found")
        return False

    user_id = user["id"]
    print(f"✅ Found user: {username} (ID: {user_id})")

    # Get or create group
    group = manager.get_group_by_name(role)
    if not group:
        print(f"⚠️  Group '{role}' not found, creating it...")
        group = manager.create_group(role)
        if not group:
            print(f"❌ Failed to create group '{role}'")
            return False
        print(f"✅ Created group: {role}")
    else:
        print(f"✅ Found group: {role}")

    group_id = group["id"]

    # Add user to group
    if manager.add_user_to_group(user_id, username, group_id):
        print(f"✅ Successfully added '{username}' to '{role}'")
        return True
    print("❌ Failed to add user to group")
    return False


def remove_role(manager, username, role):
    """Remove a role from a user"""
    print(f"\n🎯 Removing role '{role}' from user '{username}'")

    # Get user
    user = manager.get_user_by_username(username)
    if not user:
        print(f"❌ User '{username}' not found")
        return False

    user_id = user["id"]
    print(f"✅ Found user: {username} (ID: {user_id})")

    # Get group
    group = manager.get_group_by_name(role)
    if not group:
        print(f"❌ Group '{role}' not found")
        return False

    group_id = group["id"]
    print(f"✅ Found group: {role}")

    # Remove user from group
    if manager.remove_user_from_group(user_id, group_id):
        print(f"✅ Successfully removed '{username}' from '{role}'")
        return True
    print("❌ Failed to remove user from group")
    return False


def list_roles(manager, username):
    """List all roles for a user"""
    print(f"\n🎯 Listing roles for user '{username}'")

    # Get user
    user = manager.get_user_by_username(username)
    if not user:
        print(f"❌ User '{username}' not found")
        return False

    user_id = user["id"]
    print(f"✅ Found user: {username} (ID: {user_id})")

    # Get groups
    groups = manager.list_user_groups(user_id)

    if groups:
        print(f"\n📋 User is member of {len(groups)} group(s):")
        for i, group in enumerate(groups, 1):
            print(f"   {i}. {group.get('display', 'N/A')}")
    else:
        print("\n⚠️  User is not member of any groups")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Manage WSO2 Identity Server roles for Darts Game users",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add gamemaster role to Dennis
  python3 manage_user_roles.py add Dennis gamemaster
  
  # Remove admin role from Dennis
  python3 manage_user_roles.py remove Dennis admin
  
  # List all roles for Dennis
  python3 manage_user_roles.py list Dennis
  
Available roles:
  - gamemaster: Access to control panel and game management
  - admin: Full system access
  - player: Basic game participation
        """,
    )

    parser.add_argument(
        "action",
        choices=["add", "remove", "list"],
        help="Action to perform",
    )
    parser.add_argument(
        "username",
        help="Username to manage",
    )
    parser.add_argument(
        "role",
        nargs="?",
        help="Role to add/remove (not needed for 'list' action)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.action in ["add", "remove"] and not args.role:
        parser.error(f"'{args.action}' action requires a role argument")

    print(
        """
╔══════════════════════════════════════════════════════════════╗
║   WSO2 Identity Server - Role Management CLI                ║
╚══════════════════════════════════════════════════════════════╝
    """
    )

    # Initialize manager
    manager = WSO2Manager(WSO2_IS_URL, WSO2_ADMIN_USER, WSO2_ADMIN_PASSWORD)

    # Perform action
    success = False
    if args.action == "add":
        success = add_role(manager, args.username, args.role)
    elif args.action == "remove":
        success = remove_role(manager, args.username, args.role)
    elif args.action == "list":
        success = list_roles(manager, args.username)

    # Show next steps
    if success and args.action in ["add", "remove"]:
        print(f"\n{'='*60}")
        print("📝 Next steps:")
        print("   1. Logout: https://letsplaydarts.eu/logout")
        print("   2. Login: https://letsplaydarts.eu/login")
        print("   3. Debug: https://letsplaydarts.eu/debug/auth")
        print(f"{'='*60}\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
