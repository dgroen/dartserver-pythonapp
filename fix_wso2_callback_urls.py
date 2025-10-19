#!/usr/bin/env python3
"""
Fix WSO2 IS OAuth2 callback URLs to allow proper redirects
Uses WSO2 IS REST API with basic authentication
"""

import os
import sys

import requests

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()

# Configuration
WSO2_IS_URL = "https://letsplaydarts.eu/auth"

ADMIN_USER = os.environ.get("WSO2_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("WSO2_ADMIN_PASS", "")
CLIENT_ID = os.environ.get("WSO2_CLIENT_ID", "your-default-client-id")

# Callback URL pattern - allows both /callback and / (root)
CALLBACK_PATTERN = (
    "regexp=(https://letsplaydarts\\.eu(/callback|/.*)|http://localhost:5000/callback)"
)

# API endpoint
API_BASE = f"{WSO2_IS_URL}/api/server/v1"
APPLICATIONS_ENDPOINT = f"{API_BASE}/applications"


def get_application_by_client_id():
    """Get application details by OAuth2 client ID using basic auth"""
    try:
        print(f"🔍 Searching for application with client ID: {CLIENT_ID}")
        # pylint: disable=S501
        response = requests.get(
            APPLICATIONS_ENDPOINT,
            auth=(ADMIN_USER, ADMIN_PASS),
            headers={"Accept": "application/json"},
            params={"filter": f"clientId eq {CLIENT_ID}"},
            verify=False,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            applications = data.get("applications", [])

            if applications:
                app = applications[0]
                print(f"✅ Found application: {app.get('name')} (ID: {app.get('id')})")
                return app

            print(f"❌ No application found with client ID: {CLIENT_ID}")
            return None

        print(f"❌ Failed to get application: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    except Exception as e:
        print(f"❌ Error getting application: {e}")
        return None


def update_callback_urls(app_id):
    """Update application callback URLs"""
    try:
        # Get full application details
        print("\n📥 Fetching full application details...")
        # pylint: disable=S501
        response = requests.get(
            f"{APPLICATIONS_ENDPOINT}/{app_id}",
            auth=(ADMIN_USER, ADMIN_PASS),
            headers={"Accept": "application/json"},
            verify=False,
            timeout=10,
        )

        if response.status_code != 200:
            print(f"❌ Failed to get application details: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        app_data = response.json()

        # Find OAuth2 inbound configuration
        inbound_protocols = app_data.get("inboundProtocols", [])
        oauth_config = None

        for protocol in inbound_protocols:
            if protocol.get("type") == "oauth2":
                oauth_config = protocol
                break

        if not oauth_config:
            print("❌ No OAuth2 configuration found")
            return False

        # Show current callback URLs
        current_callbacks = oauth_config.get("callbackURLs", [])
        print("\n📋 Current callback URLs:")
        for cb in current_callbacks:
            print(f"   - {cb}")

        # Update callback URLs
        oauth_config["callbackURLs"] = [CALLBACK_PATTERN]

        print("\n✏️  New callback pattern:")
        print(f"   - {CALLBACK_PATTERN}")
        print("\n   This allows:")
        print("   ✓ https://letsplaydarts.eu/callback (login)")
        print("   ✓ https://letsplaydarts.eu/ (logout)")
        print("   ✓ https://letsplaydarts.eu/* (any path)")
        print("   ✓ http://localhost:5000/callback (local dev)")

        # Update the application
        print("\n📤 Updating application...")
        # pylint: disable=S501
        update_response = requests.put(
            f"{APPLICATIONS_ENDPOINT}/{app_id}",
            auth=(ADMIN_USER, ADMIN_PASS),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=app_data,
            verify=False,
            timeout=10,
        )

        if update_response.status_code in [200, 204]:
            print("✅ Application updated successfully!")
            print("\n🎉 Callback URLs have been configured!")
            print("\nNext steps:")
            print("1. Try logging in again at: https://letsplaydarts.eu/login")
            print("2. You should be redirected properly after authentication")
            return True

        print(f"❌ Failed to update application: {update_response.status_code}")
        print(f"Response: {update_response.text}")
        return False

    except Exception as e:
        print(f"❌ Error updating application: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("=" * 70)
    print("WSO2 Identity Server - Fix OAuth2 Callback URLs")
    print("=" * 70)
    print()
    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Admin User: {ADMIN_USER}")
    print()

    # Get application
    app = get_application_by_client_id()
    if not app:
        print("\n❌ Failed to find application")
        sys.exit(1)

    app_id = app.get("id")

    # Update callback URLs
    success = update_callback_urls(app_id)

    if success:
        print("\n" + "=" * 70)
        print("✅ SUCCESS - Callback URLs updated!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED - Could not update callback URLs")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
