#!/usr/bin/env python3
"""
Configure WSO2 Identity Server OAuth2 application redirect URIs for test.

This script updates the application through the WSO2 Applications API and
works on the test server with default test values.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import requests
from dotenv import load_dotenv

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()  # type: ignore

# Load environment variables
load_dotenv()

# WSO2 IS Configuration
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://test.letsplaydarts.eu/auth")
WSO2_CLIENT_ID = os.getenv("WSO2_CLIENT_ID", "")
WSO2_CLIENT_SECRET = os.getenv("WSO2_CLIENT_SECRET", "")
WSO2_ADMIN_USERNAME = os.getenv("WSO2_ADMIN_USERNAME", os.getenv("WSO2_ADMIN_USER", "admin"))
WSO2_ADMIN_PASSWORD = os.getenv("WSO2_ADMIN_PASSWORD", os.getenv("WSO2_ADMIN_PASS", "admin"))
WSO2_IS_VERIFY_SSL = os.getenv("WSO2_IS_VERIFY_SSL", "False").lower() == "true"

# Redirect URIs to register
CALLBACK_URI = os.getenv("WSO2_REDIRECT_URI", "https://letsplaydarts.eu/callback")
POST_LOGOUT_URI = os.getenv("WSO2_POST_LOGOUT_REDIRECT_URI", "https://letsplaydarts.eu/")

API_BASE = f"{WSO2_IS_URL}/api/server/v1"
APPLICATIONS_ENDPOINT = f"{API_BASE}/applications"


def get_access_token():
    """Get access token using client credentials"""
    token_url = f"{WSO2_IS_URL}/oauth2/token"

    try:
        response = requests.post(
            token_url,
            auth=(WSO2_CLIENT_ID, WSO2_CLIENT_SECRET),
            data={
                "grant_type": "client_credentials",
                "scope": "internal_application_mgt_view internal_application_mgt_update",
            },
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code == 200:
            return response.json().get("access_token")
        print(f"❌ Failed to get access token: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return None


def get_application_by_client_id(access_token):
    """Get application details by OAuth2 client ID"""
    try:
        # Search for application by client ID
        response = requests.get(
            APPLICATIONS_ENDPOINT,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            params={
                "filter": f"clientId eq {WSO2_CLIENT_ID}",
            },
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code == 200:
            applications = response.json().get("applications", [])
            if applications:
                return applications[0]
            print(f"❌ No application found with client ID: {WSO2_CLIENT_ID}")
            return None
        print(f"❌ Failed to get application: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error getting application: {e}")
        return None


def update_application_redirect_uris(access_token, app_id):
    """Update application redirect URIs to include both callback and post-logout URIs"""
    try:
        # Get full application details
        response = requests.get(
            f"{APPLICATIONS_ENDPOINT}/{app_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code != 200:
            print(f"❌ Failed to get application details: {response.status_code}")
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

        # Update callback URLs
        current_callbacks = oauth_config.get("callbackURLs", [])
        print(f"\n📋 Current callback URLs: {current_callbacks}")

        oauth_config["callbackURLs"] = [CALLBACK_URI, POST_LOGOUT_URI]

        print("✅ New callback URLs:")
        print(f"   - {CALLBACK_URI}")
        print(f"   - {POST_LOGOUT_URI}")

        # Update the application
        update_response = requests.put(
            f"{APPLICATIONS_ENDPOINT}/{app_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=app_data,
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if update_response.status_code in [200, 204]:
            print("✅ Application updated successfully!")
            return True
        print(f"❌ Failed to update application: {update_response.status_code}")
        print(f"Response: {update_response.text}")
        return False

    except Exception as e:
        print(f"❌ Error updating application: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Configure WSO2 application redirect URIs for test",
    )
    parser.add_argument("--ws-url", help="WSO2 base URL")
    parser.add_argument("--client-id", help="OAuth2 client ID")
    parser.add_argument("--client-secret", help="OAuth2 client secret")
    parser.add_argument("--admin-user", help="WSO2 admin username")
    parser.add_argument("--admin-pass", help="WSO2 admin password")
    parser.add_argument("--callback-uri", help="Callback URI")
    parser.add_argument("--post-logout-uri", help="Post logout redirect URI")
    args = parser.parse_args()

    global WSO2_IS_URL, WSO2_CLIENT_ID, WSO2_CLIENT_SECRET
    global WSO2_ADMIN_USERNAME, WSO2_ADMIN_PASSWORD
    global CALLBACK_URI, POST_LOGOUT_URI, API_BASE, APPLICATIONS_ENDPOINT
    if args.ws_url:
        WSO2_IS_URL = args.ws_url
    if args.client_id:
        WSO2_CLIENT_ID = args.client_id
    if args.client_secret:
        WSO2_CLIENT_SECRET = args.client_secret
    if args.admin_user:
        WSO2_ADMIN_USERNAME = args.admin_user
    if args.admin_pass:
        WSO2_ADMIN_PASSWORD = args.admin_pass
    if args.callback_uri:
        CALLBACK_URI = args.callback_uri
    if args.post_logout_uri:
        POST_LOGOUT_URI = args.post_logout_uri
    API_BASE = f"{WSO2_IS_URL}/api/server/v1"
    APPLICATIONS_ENDPOINT = f"{API_BASE}/applications"

    print("=" * 60)
    print("WSO2 Identity Server - Configure Redirect URIs")
    print("=" * 60)
    print()

    # Validate configuration
    if not WSO2_CLIENT_ID or not WSO2_CLIENT_SECRET:
        print("❌ Error: WSO2_CLIENT_ID and WSO2_CLIENT_SECRET must be set")
        print("Please check your .env file")
        sys.exit(1)

    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Client ID: {WSO2_CLIENT_ID}")
    print(f"   Callback URI: {CALLBACK_URI}")
    print(f"   Post-Logout URI: {POST_LOGOUT_URI}")
    print()

    # Wait for WSO2 IS to be ready
    print("⏳ Waiting for WSO2 IS to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(
                f"{WSO2_IS_URL}/carbon/admin/login.jsp",
                verify=WSO2_IS_VERIFY_SSL,
                timeout=5,
            )
            if response.status_code == 200:
                print("✅ WSO2 IS is ready!")
                break
        except Exception:
            pass

        if i < max_retries - 1:
            print(f"   Retry {i+1}/{max_retries}...")
            time.sleep(2)
        else:
            print("❌ WSO2 IS is not responding. Please check if it's running.")
            sys.exit(1)

    print()

    # Note: The REST API approach requires proper authentication
    # For now, we'll provide manual instructions
    print("🔧 Attempting redirect update via WSO2 Applications API...")
    access_token = get_access_token()
    if not access_token:
        print("❌ Could not obtain access token")
        sys.exit(1)

    app = get_application_by_client_id(access_token)
    if not app:
        print("❌ Failed to find application")
        sys.exit(1)

    success = update_application_redirect_uris(access_token, app.get("id"))
    if success:
        print()
        print("✅ Redirect URIs updated successfully")
        print(f"   - {CALLBACK_URI}")
        print(f"   - {POST_LOGOUT_URI}")
        sys.exit(0)

    print("❌ Failed to update redirect URIs")
    sys.exit(1)


if __name__ == "__main__":
    main()
