#!/usr/bin/env python3
"""
Register OAuth2 client for the test server in WSO2 Identity Server.

This script is intentionally configurable so it can run on the test server
through the deployment pipeline and also be executed manually.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings()

# Configuration for test server
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://test.letsplaydarts.eu/auth")
WSO2_ADMIN_USER = os.getenv("WSO2_ADMIN_USER", os.getenv("WSO2_IS_INTROSPECT_USER", "admin"))
WSO2_ADMIN_PASS = os.getenv(
    "WSO2_ADMIN_PASS",
    os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin"),
)  # pragma: allowlist secret

# Test server OAuth2 credentials (from test env)
CLIENT_ID = os.getenv("WSO2_CLIENT_ID", "QG32mHju2Gs5JJTh4RO60982cxsa")
CLIENT_SECRET = os.getenv(
    "WSO2_CLIENT_SECRET",
    "DZfn3qolUxKeXQbJ_7bwhmfZNLWm8wdVwS5_1oR12YAa",
)  # pragma: allowlist secret
CLIENT_NAME = os.getenv("WSO2_CLIENT_NAME", "DartsTestServer")

# Test server redirect URIs
REDIRECT_URIS = [
    os.getenv("WSO2_REDIRECT_URI", "https://test.letsplaydarts.eu/callback"),
    os.getenv("WSO2_POST_LOGOUT_REDIRECT_URI", "https://test.letsplaydarts.eu/"),
]

# DCR API endpoints
DCR_REGISTER_ENDPOINT = f"{WSO2_IS_URL}/api/identity/oauth2/dcr/v1.1/register"
DCR_CLIENT_ENDPOINT = f"{WSO2_IS_URL}/api/identity/oauth2/dcr/v1.1/register/{CLIENT_ID}"


def check_existing_client():
    """Check if client already exists"""
    try:
        print("🔍 Checking if client already exists...")
        # pylint: disable=S501
        response = requests.get(
            DCR_CLIENT_ENDPOINT,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            headers={"Accept": "application/json"},
            verify=False,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found existing client: {data.get('client_name', 'Unknown')}")
            return data
        if response.status_code == 404:
            print("ℹ️  Client does not exist - will create new one")
            return None
        print(f"⚠️  Error checking client: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    except Exception as e:
        print(f"⚠️  Error checking client: {e}")
        return None


def register_new_client():
    """Register new OAuth2 client using DCR API"""
    try:
        print("\n📤 Registering new OAuth2 client...")

        payload = {
            "client_name": CLIENT_NAME,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_types": ["authorization_code", "refresh_token", "password"],
            "redirect_uris": REDIRECT_URIS,
            "token_endpoint_auth_method": "client_secret_basic",
            "require_auth_time": False,
            "default_max_age": 3600,
        }

        print(f"   Client ID: {CLIENT_ID}")
        print(f"   Client Name: {CLIENT_NAME}")
        print("   Redirect URIs:")
        for uri in REDIRECT_URIS:
            print(f"      - {uri}")

        # pylint: disable=S501
        response = requests.post(
            DCR_REGISTER_ENDPOINT,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=payload,
            verify=False,
            timeout=10,
        )

        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ OAuth2 client registered successfully!")
            print("\n📋 Client Details:")
            print(json.dumps(data, indent=2))
            return True

        print(f"❌ Failed to register client: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    except Exception as e:
        print(f"❌ Error registering client: {e}")
        traceback.print_exc()
        return False


def update_client(client_data):
    """Update existing OAuth2 client"""
    try:
        print("\n✏️  Updating OAuth2 client configuration...")

        # Update with new configuration
        client_data["redirect_uris"] = REDIRECT_URIS
        client_data["client_name"] = CLIENT_NAME

        if "grant_types" not in client_data or "authorization_code" not in client_data.get(
            "grant_types",
            [],
        ):
            client_data["grant_types"] = ["authorization_code", "refresh_token", "password"]

        print("   Redirect URIs:")
        for uri in REDIRECT_URIS:
            print(f"      - {uri}")

        # pylint: disable=S501
        response = requests.put(
            DCR_CLIENT_ENDPOINT,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=client_data,
            verify=False,
            timeout=10,
        )

        if response.status_code in [200, 201]:
            print("✅ OAuth2 client updated successfully!")
            data = response.json()
            print("\n📋 Updated Client Details:")
            print(json.dumps(data, indent=2))
            return True

        print(f"❌ Failed to update client: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    except Exception as e:
        print(f"❌ Error updating client: {e}")
        traceback.print_exc()
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Register or update the test-server OAuth2 client in WSO2",
    )
    parser.add_argument("--ws-url", help="WSO2 base URL")
    parser.add_argument("--admin-user", help="WSO2 admin username")
    parser.add_argument("--admin-pass", help="WSO2 admin password")
    parser.add_argument("--client-id", help="OAuth2 client id")
    parser.add_argument("--client-secret", help="OAuth2 client secret")
    parser.add_argument("--client-name", help="OAuth2 client display name")
    parser.add_argument(
        "--redirect-uri",
        action="append",
        help="Redirect URI to include; can be repeated",
    )
    args = parser.parse_args()

    global WSO2_IS_URL, WSO2_ADMIN_USER, WSO2_ADMIN_PASS
    global CLIENT_ID, CLIENT_SECRET, CLIENT_NAME, REDIRECT_URIS
    if args.ws_url:
        WSO2_IS_URL = args.ws_url
    if args.admin_user:
        WSO2_ADMIN_USER = args.admin_user
    if args.admin_pass:
        WSO2_ADMIN_PASS = args.admin_pass
    if args.client_id:
        CLIENT_ID = args.client_id
    if args.client_secret:
        CLIENT_SECRET = args.client_secret
    if args.client_name:
        CLIENT_NAME = args.client_name
    if args.redirect_uri:
        REDIRECT_URIS = args.redirect_uri

    print("=" * 70)
    print("WSO2 Identity Server - Register Test Server OAuth2 Client")
    print("=" * 70)
    print()
    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Client Name: {CLIENT_NAME}")
    print(f"   Redirect URIs: {REDIRECT_URIS}")
    print()

    # Check if client exists
    existing_client = check_existing_client()

    success = update_client(existing_client) if existing_client else register_new_client()

    if success:
        print("\n" + "=" * 70)
        print("✅ SUCCESS - Test Server OAuth2 Client is configured!")
        print("=" * 70)
        print("\n🚀 You can now:")
        print("   - Deploy the Docker containers")
        print("   - Login at: https://test.letsplaydarts.eu/login")
        print("   - Access the dashboard at: https://test.letsplaydarts.eu/dashboard")
        print()
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED - Could not register OAuth2 client")
        print("=" * 70)
        print("\n📝 Troubleshooting:")
        print(
            "   1. Ensure WSO2 containers are running: "
            "docker-compose -f docker-compose-wso2.yml up -d",
        )
        print("   2. Wait for WSO2 to be fully initialized (check logs)")
        print("   3. Verify WSO2 is accessible: curl -k https://wso2is:9443/carbon/")
        print("   4. Check admin credentials are correct (default: admin/admin)")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
