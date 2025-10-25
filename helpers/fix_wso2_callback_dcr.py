#!/usr/bin/env python3
"""
Fix WSO2 IS OAuth2 callback URLs using DCR (Dynamic Client Registration) API
This API allows updating OAuth2 client configuration
"""

import sys

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings()

# Configuration
WSO2_IS_URL = "https://letsplaydarts.eu/auth"

ADMIN_USER = "admin"
ADMIN_PASS = "admin"  # pragma: allowlist secret
CLIENT_ID = "z9tDR_MVfS_rHKBlqZ_6Re_TaJga"
CLIENT_SECRET = "lQCbqtHliRy3j_POcCRxm9j7Cj7VqTx6ehRXnNaesUca"  # pragma: allowlist secret

# Callback URLs - list of allowed redirect URIs
CALLBACK_URLS = [
    "https://letsplaydarts.eu/callback",
    "https://letsplaydarts.eu/",
    "http://localhost:5000/callback",
]

# DCR API endpoint
DCR_ENDPOINT = f"{WSO2_IS_URL}/api/identity/oauth2/dcr/v1.1/register/{CLIENT_ID}"


def get_client_info():
    """Get current OAuth2 client configuration"""
    try:
        print("🔍 Fetching current client configuration...")
        # pylint: disable=S501
        response = requests.get(
            DCR_ENDPOINT,
            auth=(ADMIN_USER, ADMIN_PASS),
            headers={"Accept": "application/json"},
            verify=False,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found client: {data.get('client_name', 'Unknown')}")

            current_redirects = data.get("redirect_uris", [])
            print("\n📋 Current redirect URIs:")
            if current_redirects:
                for uri in current_redirects:
                    print(f"   - {uri}")
            else:
                print("   (none configured)")

            return data

        print(f"❌ Failed to get client info: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    except Exception as e:
        print(f"❌ Error getting client info: {e}")
        return None


def update_client_redirects(client_data):
    """Update OAuth2 client redirect URIs"""
    try:
        print("\n✏️  New redirect URIs:")
        for uri in CALLBACK_URLS:
            print(f"   - {uri}")

        # Update redirect URIs
        client_data["redirect_uris"] = CALLBACK_URLS

        # Also update grant types to ensure authorization_code is included
        if "grant_types" not in client_data:
            client_data["grant_types"] = ["authorization_code", "refresh_token"]

        print("\n📤 Updating client configuration...")

        response = requests.put(
            DCR_ENDPOINT,
            auth=(ADMIN_USER, ADMIN_PASS),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=client_data,
            verify=False,
            timeout=10,
        )

        if response.status_code in [200, 201]:
            print("✅ Client configuration updated successfully!")

            updated_data = response.json()
            print("\n📋 Updated redirect URIs:")
            for uri in updated_data.get("redirect_uris", []):
                print(f"   ✓ {uri}")

            print("\n🎉 Callback URLs have been configured!")
            print("\nYou can now:")
            print("   ✓ Login at: https://letsplaydarts.eu/login")
            print("   ✓ Logout at: https://letsplaydarts.eu/logout")
            print("   ✓ Develop locally at: http://localhost:5000")
            return True

        print(f"❌ Failed to update client: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"❌ Error updating client: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("=" * 70)
    print("WSO2 Identity Server - Fix OAuth2 Callback URLs (DCR API)")
    print("=" * 70)
    print()
    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Admin User: {ADMIN_USER}")
    print()

    # Get current client configuration
    client_data = get_client_info()
    if not client_data:
        print("\n❌ Failed to get client configuration")
        sys.exit(1)

    # Update redirect URIs
    success = update_client_redirects(client_data)

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
