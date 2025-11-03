#!/usr/bin/env python3
"""
WSO2 Identity Server Role Verification Script
This script verifies the current role and group configuration for users
"""

import sys

import requests

# WSO2 IS Configuration
WSO2_IS_URL = "https://letsplaydarts.eu/auth"
WSO2_ADMIN_USER = "admin"
WSO2_ADMIN_PASSWORD = "admin"  # pragma: allowlist secret

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()


def get_user_info(username):
    """Get detailed user information including groups"""
    url = f"{WSO2_IS_URL}/scim2/Users"
    params = {"filter": f'userName eq "{username}"'}
    auth = (WSO2_ADMIN_USER, WSO2_ADMIN_PASSWORD)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.get(url, auth=auth, headers=headers, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("totalResults", 0) > 0:
            return data["Resources"][0]
    return None


def get_all_groups():
    """Get all groups in the system"""
    url = f"{WSO2_IS_URL}/scim2/Groups"
    auth = (WSO2_ADMIN_USER, WSO2_ADMIN_PASSWORD)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.get(url, auth=auth, headers=headers, verify=False)

    if response.status_code == 200:
        data = response.json()
        return data.get("Resources", [])
    return []


def main():
    print(
        """
╔══════════════════════════════════════════════════════════════╗
║   WSO2 Identity Server - Role Verification                  ║
╚══════════════════════════════════════════════════════════════╝
    """,
    )

    username = "Dennis"

    # Get user info
    print(f"🔍 Fetching information for user: {username}\n")
    user = get_user_info(username)

    if not user:
        print(f"❌ User '{username}' not found")
        return 1

    # Display user information
    print(f"{'='*60}")
    print("👤 User Information")
    print(f"{'='*60}")
    print(f"Username:  {user.get('userName', 'N/A')}")
    print(f"User ID:   {user.get('id', 'N/A')}")

    # Safely get email
    emails = user.get("emails", [])
    if emails and isinstance(emails, list) and len(emails) > 0:
        email_obj = emails[0]
        email = email_obj.get("value", "N/A") if isinstance(email_obj, dict) else str(email_obj)
    else:
        email = "N/A"
    print(f"Email:     {email}")
    print(f"Active:    {user.get('active', 'N/A')}")

    # Display groups
    groups = user.get("groups", [])
    print(f"\n{'='*60}")
    print(f"🎭 Group Membership ({len(groups)} groups)")
    print(f"{'='*60}")

    if groups:
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group.get('display', 'N/A')}")
            print(f"   └─ Group ID: {group.get('value', 'N/A')}")
    else:
        print("⚠️  User is not a member of any groups")

    # Display all available groups
    print(f"\n{'='*60}")
    print("📋 All Available Groups in System")
    print(f"{'='*60}")

    all_groups = get_all_groups()
    if all_groups:
        for i, group in enumerate(all_groups, 1):
            group_name = group.get("displayName", "N/A")
            group.get("id", "N/A")
            members = group.get("members", [])
            member_count = len(members)

            # Check if Dennis is a member
            is_member = any(m.get("display") == username for m in members)
            status = "✅" if is_member else "  "

            print(f"{status} {i}. {group_name} ({member_count} members)")
            if is_member:
                print(f"      └─ {username} is a member")
    else:
        print("⚠️  No groups found in the system")

    # Display expected roles for Darts application
    print(f"\n{'='*60}")
    print("🎯 Darts Application Role Requirements")
    print(f"{'='*60}")

    expected_roles = {
        "gamemaster": "Access to control panel and game management",
        "admin": "Full system access",
        "player": "Basic game participation",
    }

    user_group_names = [g.get("display", "").lower() for g in groups]

    for role, description in expected_roles.items():
        has_role = role.lower() in user_group_names
        status = "✅" if has_role else "❌"
        print(f"{status} {role:12} - {description}")

    # Final recommendation
    print(f"\n{'='*60}")
    print("💡 Recommendations")
    print(f"{'='*60}")

    if "gamemaster" in user_group_names or "admin" in user_group_names:
        print("✅ User has sufficient permissions for control panel access")
        print("\n📝 Next steps:")
        print("   1. Logout: https://letsplaydarts.eu/logout")
        print("   2. Login: https://letsplaydarts.eu/login")
        print("   3. Debug: https://letsplaydarts.eu/debug/auth")
        print("   4. Control: https://letsplaydarts.eu/control")
    else:
        print("⚠️  User needs 'gamemaster' or 'admin' role for control panel")
        print("\n📝 To add roles, run:")
        print("   python3 setup_wso2_roles.py")

    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
