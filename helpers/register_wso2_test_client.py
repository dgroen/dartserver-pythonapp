#!/usr/bin/env python3
"""
Register OAuth2 client for test server (test.letsplaydarts.eu) in WSO2 Identity Server
Uses DCR (Dynamic Client Registration) API to create/update the OAuth2 application
"""

import json
import sys

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings()

# Configuration for test server
WSO2_IS_URL = "https://wso2is:9443"  # Internal Docker URL
WSO2_ADMIN_USER = "admin"
WSO2_ADMIN_PASS = "admin"  # pragma: allowlist secret

# Test server OAuth2 credentials (from docker-compose-test.yml)
CLIENT_ID = "QG32mHju2Gs5JJTh4RO60982cxsa"
CLIENT_SECRET = "DZfn3qolUxKeXQbJ_7bwhmfZNLWm8wdVwS5_1oR12YAa"  # pragma: allowlist secret
CLIENT_NAME = "DartsTestServer"

# Test server redirect URIs
REDIRECT_URIS = [
    "https://test.letsplaydarts.eu/callback",
    "https://test.letsplaydarts.eu/",
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
        import traceback

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
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("=" * 70)
    print("WSO2 Identity Server - Register Test Server OAuth2 Client")
    print("=" * 70)
    print()
    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Client Name: {CLIENT_NAME}")
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
