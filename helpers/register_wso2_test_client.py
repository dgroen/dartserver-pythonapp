#!/usr/bin/env python3
"""
Register OAuth2 client for the test server in WSO2 Identity Server.

This script is intentionally configurable so it can run on the test server
through the deployment pipeline and also be executed manually.
"""

from __future__ import annotations

import argparse
import builtins
import json
import os
import sys
import traceback
from typing import Any

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings()

# Configuration for test server
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://test.letsplaydarts.eu/auth")
WSO2_ADMIN_USER = os.getenv(
    "WSO2_ADMIN_USER",
    os.getenv("WSO2_ADMIN_USERNAME", os.getenv("WSO2_IS_INTROSPECT_USER", "admin")),
)
WSO2_ADMIN_PASS = os.getenv(
    "WSO2_ADMIN_PASS",
    os.getenv(
        "WSO2_ADMIN_PASSWORD",
        os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin"),
    ),
)  # pragma: allowlist secret

WSO2_DCR_AUTH_MODE = os.getenv("WSO2_DCR_AUTH_MODE", "auto").lower()
WSO2_DCR_BEARER_TOKEN = os.getenv("WSO2_DCR_BEARER_TOKEN", "")

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

def _dcr_register_endpoint() -> str:
    return f"{WSO2_IS_URL.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register"


def _dcr_client_endpoint(client_id: str) -> str:
    return f"{WSO2_IS_URL.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register/{client_id}"


def _build_dcr_headers(include_json: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if include_json:
        headers["Content-Type"] = "application/json"
    if WSO2_DCR_AUTH_MODE == "bearer" and WSO2_DCR_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {WSO2_DCR_BEARER_TOKEN}"
    return headers


def _dcr_request(
    method: str,
    url: str,
    json_payload: dict[str, Any] | None = None,
) -> requests.Response:
    def _send_request(
        request_headers: dict[str, str],
        request_auth: tuple[str, str] | None,
    ) -> requests.Response:
        response: requests.Response | None = None
        for attempt in range(5):
            # pylint: disable=S501
            response = requests.request(
                method,
                url,
                auth=request_auth,
                headers=request_headers,
                json=json_payload,
                verify=False,
                timeout=10,
            )
            if response.status_code not in (502, 503, 504):
                break
            if attempt < 4:
                time.sleep(2)
        assert response is not None
        return response

    headers = _build_dcr_headers(include_json=json_payload is not None)
    auth = None if "Authorization" in headers else (WSO2_ADMIN_USER, WSO2_ADMIN_PASS)

    response = _send_request(headers, auth)

    if (
        response.status_code == 401
        and WSO2_DCR_AUTH_MODE == "auto"
        and WSO2_DCR_BEARER_TOKEN
        and "Authorization" not in headers
    ):
        retry_headers = _build_dcr_headers(include_json=json_payload is not None)
        retry_headers["Authorization"] = f"Bearer {WSO2_DCR_BEARER_TOKEN}"
        return _send_request(retry_headers, None)

    return response


def _check_admin_auth() -> tuple[bool, str]:
    if WSO2_DCR_AUTH_MODE == "bearer" or WSO2_DCR_BEARER_TOKEN:
        return True, "bearer auth configured"

    # pylint: disable=S501
    response = requests.get(
        f"{WSO2_IS_URL}/scim2/Users",
        auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
        headers={"Accept": "application/scim+json"},
        params={"startIndex": 1, "count": 1},
        verify=False,
        timeout=10,
    )
    if response.status_code == 200:
        return True, "ok"
    if response.status_code == 401:
        return False, "Admin credentials are not accepted by WSO2 management APIs (401)."
    return False, f"Unexpected admin auth response from WSO2: {response.status_code}"


def check_existing_client() -> tuple[dict[str, Any] | None, bool]:
    """Check if client already exists.

    Tries admin Basic auth first. In WSO2 IS 7.x the DCR GET endpoint follows
    RFC 7592 and returns 401 when admin credentials are used (only the client's
    own credentials or a registration access token are accepted).  When that
    happens we retry with CLIENT_ID:CLIENT_SECRET so idempotent re-runs work.
    """
    try:
        print("🔍 Checking if client already exists...")
        url = _dcr_client_endpoint(CLIENT_ID)
        response = _dcr_request("GET", url)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found existing client: {data.get('client_name', 'Unknown')}")
            return data, True
        if response.status_code == 404:
            print("ℹ️  Client does not exist - will create new one")
            return None, True

        # WSO2 IS 7.x DCR GET requires the client's own credentials (RFC 7592).
        # Admin Basic auth returns 401 for this endpoint — retry with client creds.
        if response.status_code == 401 and CLIENT_SECRET:
            print(
                f"   ℹ️  Admin auth returned 401 on DCR GET (WSO2 IS 7.x behaviour); "
                "retrying with client credentials..."
            )
            # pylint: disable=S501
            retry = requests.get(
                url,
                auth=(CLIENT_ID, CLIENT_SECRET),
                headers={"Accept": "application/json"},
                verify=False,
                timeout=10,
            )
            if retry.status_code == 200:
                data = retry.json()
                print(f"✅ Found existing client: {data.get('client_name', 'Unknown')}")
                return data, True
            if retry.status_code == 404:
                print("ℹ️  Client does not exist - will create new one")
                return None, True
            # 401 with client creds means client genuinely doesn't exist yet
            # (WSO2 returns 401 instead of 404 when the client_id is unknown)
            if retry.status_code == 401:
                print("ℹ️  Client does not exist (401 on client-credential DCR GET) - will create new one")
                return None, True
            print(f"⚠️  Error checking client (client-cred retry): {retry.status_code}")
            print(f"   Response: {retry.text}")
            return None, False

        print(f"⚠️  Error checking client: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, False

    except Exception as e:
        print(f"⚠️  Error checking client: {e}")
        return None, False


def register_new_client() -> dict[str, Any] | None:
    """Register new OAuth2 client using DCR API"""
    try:
        print("\n📤 Registering new OAuth2 client...")

        payload = {
            "client_name": CLIENT_NAME,
            "ext_param_client_id": CLIENT_ID,
            "ext_param_client_secret": CLIENT_SECRET,
            "grant_types": [
                "authorization_code",
                "refresh_token",
                "password",
                "client_credentials",
            ],
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

        response = _dcr_request("POST", _dcr_register_endpoint(), json_payload=payload)

        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ OAuth2 client registered successfully!")
            print("\n📋 Client Details:")
            print(json.dumps(data, indent=2))
            return data

        print(f"❌ Failed to register client: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    except Exception as e:
        print(f"❌ Error registering client: {e}")
        traceback.print_exc()
        return None
def update_client(client_data) -> dict[str, Any] | None:
    """Update existing OAuth2 client"""
    try:
        print("\n✏️  Updating OAuth2 client configuration...")

        # Update with new configuration
        client_data["redirect_uris"] = REDIRECT_URIS
        client_data["client_name"] = CLIENT_NAME

        grant_types = set(client_data.get("grant_types", []))
        grant_types.update(["authorization_code", "refresh_token", "password", "client_credentials"])
        client_data["grant_types"] = sorted(grant_types)

        print("   Redirect URIs:")
        for uri in REDIRECT_URIS:
            print(f"      - {uri}")

        response = _dcr_request(
            "PUT",
            _dcr_client_endpoint(CLIENT_ID),
            json_payload=client_data,
        )

        if response.status_code in [200, 201]:
            print("✅ OAuth2 client updated successfully!")
            data = response.json()
            print("\n📋 Updated Client Details:")
            print(json.dumps(data, indent=2))
            return data

        print(f"❌ Failed to update client: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    except Exception as e:
        print(f"❌ Error updating client: {e}")
        traceback.print_exc()
        return None


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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit only a JSON object on stdout when successful",
    )
    args = parser.parse_args()

    orig_print = print
    if args.json:

        def stderr_print(*values, **kwargs):
            kwargs.setdefault("file", sys.stderr)
            return orig_print(*values, **kwargs)

        builtins.print = stderr_print

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
    print(f"   DCR Auth Mode: {WSO2_DCR_AUTH_MODE}")
    print()

    admin_auth_ok, admin_auth_message = _check_admin_auth()
    if not admin_auth_ok:
        print("❌ WSO2 admin auth preflight failed")
        print(f"   {admin_auth_message}")
        print("\n🛠️  Recovery options:")
        print("   1. Set valid WSO2 admin credentials (WSO2_ADMIN_USER / WSO2_ADMIN_PASS)")
        print("   2. If this is a disposable test stack, reseed WSO2 DB and restart services:")
        print("      ALLOW_WSO2_RESEED=true bash helpers/setup-test-environment.sh")
        print(
            "   3. If DCR is token-only, set WSO2_DCR_BEARER_TOKEN and optionally "
            "WSO2_DCR_AUTH_MODE=bearer",
        )
        sys.exit(1)

    # Check if client exists
    existing_client, lookup_ok = check_existing_client()
    if not lookup_ok:
        print("❌ Unable to verify existing application state. Refusing to create a new client.")
        sys.exit(1)

    result = update_client(existing_client) if existing_client else register_new_client()

    if result:
        CLIENT_ID = result.get("client_id", CLIENT_ID)
        CLIENT_SECRET = result.get("client_secret", CLIENT_SECRET)
        CLIENT_NAME = result.get("client_name", CLIENT_NAME)
        REDIRECT_URIS = result.get("redirect_uris", REDIRECT_URIS)

        if args.json:
            orig_print(
                json.dumps(
                    {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "client_name": CLIENT_NAME,
                        "redirect_uris": REDIRECT_URIS,
                    },
                ),
            )
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
