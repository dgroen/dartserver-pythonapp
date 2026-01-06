#!/usr/bin/env python3
"""
Register DartsApp OAuth2 client in WSO2 Identity Server
"""

import json
import sys

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings()

# Configuration
WSO2_IS_URL = "https://localhost:9443"
WSO2_ADMIN_USER = "admin"
WSO2_ADMIN_PASS = "admin"

# DartsApp OAuth2 configuration
CLIENT_NAME = "DartsApp"
CLIENT_DESCRIPTION = "Darts Game Web Application"
REDIRECT_URIS = [
    "http://localhost:5000/callback",
    "https://localhost:5000/callback",
    "http://localhost:5000/",
    "https://localhost:5000/",
]

# DCR API endpoint
DCR_REGISTER_ENDPOINT = f"{WSO2_IS_URL}/api/identity/oauth2/dcr/v1.1/register"
APPLICATIONS_ENDPOINT = f"{WSO2_IS_URL}/api/server/v1/applications"


def fetch_oidc_credentials(app_id: str) -> tuple[str | None, str | None]:
    """Fetch clientId/clientSecret via application inbound OIDC config."""
    try:
        response = requests.get(
            f"{APPLICATIONS_ENDPOINT}/{app_id}/inbound-protocols/oidc",
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            headers={"Accept": "application/json"},
            verify=False,
            timeout=10,
        )
        if response.status_code != 200:
            print(f"❌ Failed to fetch OIDC config: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None, None
        data = response.json()
        return data.get("clientId"), data.get("clientSecret")
    except Exception as exc:
        print(f"❌ Error fetching OIDC config: {exc}")
        return None, None


def register_darts_app():
    """Register DartsApp OAuth2 client"""
    print("🔍 Checking if DartsApp already exists...")

    # Check existing applications
    try:
        response = requests.get(
            f"{WSO2_IS_URL}/api/server/v1/applications",
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            headers={"Accept": "application/json"},
            verify=False,
            timeout=10,
        )

        if response.status_code == 200:
            apps = response.json().get("applications", [])
            for app in apps:
                if app.get("name") == CLIENT_NAME:
                    app_id = app.get("id")
                    print(f"✅ DartsApp already exists (ID: {app_id})")
                    client_id, client_secret = fetch_oidc_credentials(app_id)
                    if client_id:
                        print(f"   Client ID: {client_id}")
                    if client_secret:
                        print(f"   Client Secret: {client_secret}")
                    if not client_id:
                        print("   ⚠ No OIDC client configured; add inbound OIDC and rerun")
                    return True
        else:
            print(f"❌ Failed to check existing applications: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking existing applications: {e}")
        return False

    print("📤 Registering DartsApp OAuth2 client...")

    # Register new client
    payload = {
        "client_name": CLIENT_NAME,
        "redirect_uris": REDIRECT_URIS,
        "grant_types": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_method": "client_secret_basic",
    }

    try:
        response = requests.post(
            DCR_REGISTER_ENDPOINT,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            verify=False,
            timeout=10,
        )

        if response.status_code == 201:
            client_data = response.json()
            print("✅ DartsApp registered successfully!")
            print(f"   Client ID: {client_data.get('client_id')}")
            print(f"   Client Secret: {client_data.get('client_secret')}")
            return True
        print(f"❌ Failed to register DartsApp: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error registering DartsApp: {e}")
        return False


def main():
    print("WSO2 Identity Server - Register DartsApp OAuth2 Client")
    print("=" * 60)

    success = register_darts_app()

    if success:
        print("\n✅ DartsApp OAuth2 client registration completed successfully!")
        print("\nNext steps:")
        print("1. The DartsApp is now registered in WSO2 IS")
        print("2. You can now configure callback URLs if needed")
        print("3. Update your application configuration with the client credentials")
        return 0
    print("\n❌ FAILED - Could not register DartsApp OAuth2 client")
    return 1


if __name__ == "__main__":
    sys.exit(main())
