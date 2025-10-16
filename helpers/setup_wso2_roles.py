#!/usr/bin/env python3
"""
WSO2 Identity Server Role and Group Configuration Script
This script configures roles and groups for the Darts Game application via SCIM2 API
"""

import sys

import requests

# WSO2 IS Configuration
WSO2_IS_URL = "https://letsplaydarts.eu/auth"
WSO2_ADMIN_USER = "admin"
WSO2_ADMIN_PASSWORD = "admin"

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()


class WSO2RoleManager:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = (username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_user_by_username(self, username):
        """Get user by username using SCIM2 API"""
        url = f"{self.base_url}/scim2/Users"
        params = {"filter": f'userName eq "{username}"'}

        print(f"🔍 Searching for user: {username}")
        response = requests.get(
            url, auth=self.auth, headers=self.headers, params=params, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("totalResults", 0) > 0:
                user = data["Resources"][0]
                print(f"✅ Found user: {user['userName']} (ID: {user['id']})")
                return user
            print(f"❌ User '{username}' not found")
            return None
        print(f"❌ Error searching for user: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    def get_group_by_name(self, group_name):
        """Get group by name using SCIM2 API"""
        url = f"{self.base_url}/scim2/Groups"
        params = {"filter": f'displayName eq "{group_name}"'}

        print(f"🔍 Searching for group: {group_name}")
        response = requests.get(
            url, auth=self.auth, headers=self.headers, params=params, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("totalResults", 0) > 0:
                group = data["Resources"][0]
                print(f"✅ Found group: {group['displayName']} (ID: {group['id']})")
                return group
            print(f"⚠️  Group '{group_name}' not found")
            return None
        print(f"❌ Error searching for group: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    def create_group(self, group_name):
        """Create a new group using SCIM2 API"""
        url = f"{self.base_url}/scim2/Groups"

        payload = {
            "displayName": group_name,
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        }

        print(f"➕ Creating group: {group_name}")
        response = requests.post(
            url, auth=self.auth, headers=self.headers, json=payload, verify=False
        )

        if response.status_code == 201:
            group = response.json()
            print(f"✅ Created group: {group['displayName']} (ID: {group['id']})")
            return group
        print(f"❌ Error creating group: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    def add_user_to_group(self, user_id, user_name, group_id, group_name):
        """Add user to group using SCIM2 PATCH operation"""
        url = f"{self.base_url}/scim2/Groups/{group_id}"

        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "members",
                    "value": [
                        {
                            "value": user_id,
                            "display": user_name,
                        },
                    ],
                },
            ],
        }

        print(f"👤 Adding user '{user_name}' to group '{group_name}'")
        response = requests.patch(
            url, auth=self.auth, headers=self.headers, json=payload, verify=False
        )

        if response.status_code in [200, 204]:
            print("✅ Successfully added user to group")
            return True
        print(f"❌ Error adding user to group: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    def get_user_groups(self, user_id):
        """Get all groups for a user"""
        url = f"{self.base_url}/scim2/Users/{user_id}"

        print(f"🔍 Fetching groups for user ID: {user_id}")
        response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)

        if response.status_code == 200:
            user = response.json()
            groups = user.get("groups", [])
            if groups:
                print(f"✅ User is member of {len(groups)} group(s):")
                for group in groups:
                    print(f"   - {group.get('display', 'N/A')}")
            else:
                print("⚠️  User is not member of any groups")
            return groups
        print(f"❌ Error fetching user groups: {response.status_code}")
        print(f"   Response: {response.text}")
        return []

    def setup_user_roles(self, username, roles):
        """Setup roles for a user by adding them to appropriate groups"""
        print(f"\n{'='*60}")
        print(f"🎯 Setting up roles for user: {username}")
        print(f"   Roles to assign: {', '.join(roles)}")
        print(f"{'='*60}\n")

        # Step 1: Get user
        user = self.get_user_by_username(username)
        if not user:
            print(f"\n❌ Cannot proceed: User '{username}' not found")
            return False

        user_id = user["id"]

        # Step 2: Process each role
        success = True
        for role in roles:
            print(f"\n--- Processing role: {role} ---")

            # Check if group exists
            group = self.get_group_by_name(role)

            # Create group if it doesn't exist
            if not group:
                group = self.create_group(role)
                if not group:
                    print(f"❌ Failed to create group '{role}'")
                    success = False
                    continue

            group_id = group["id"]

            # Add user to group
            if not self.add_user_to_group(user_id, username, group_id, role):
                success = False

        # Step 3: Verify final group membership
        print(f"\n{'='*60}")
        print(f"📋 Final Group Membership for '{username}':")
        print(f"{'='*60}")
        self.get_user_groups(user_id)

        return success


def main():
    print(
        """
╔══════════════════════════════════════════════════════════════╗
║   WSO2 Identity Server - Darts Game Role Configuration      ║
╚══════════════════════════════════════════════════════════════╝
    """
    )

    # Initialize manager
    manager = WSO2RoleManager(WSO2_IS_URL, WSO2_ADMIN_USER, WSO2_ADMIN_PASSWORD)

    # Configure roles for Dennis
    username = "Dennis"
    roles = ["gamemaster"]  # Add more roles as needed: ["gamemaster", "admin", "player"]

    # Setup roles
    success = manager.setup_user_roles(username, roles)

    # Final status
    print(f"\n{'='*60}")
    if success:
        print("✅ Role configuration completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Logout from the Darts application: https://letsplaydarts.eu/logout")
        print("   2. Login again: https://letsplaydarts.eu/login")
        print("   3. Check debug endpoint: https://letsplaydarts.eu/debug/auth")
        print("   4. Access control panel: https://letsplaydarts.eu/control")
    else:
        print("⚠️  Role configuration completed with some errors")
        print("   Please check the output above for details")
    print(f"{'='*60}\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
