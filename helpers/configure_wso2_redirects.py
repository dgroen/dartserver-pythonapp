#!/usr/bin/env python3
"""
Configure WSO2 Identity Server OAuth2 redirect URIs for the test client.

This helper uses the DCR endpoint directly so the deployment pipeline can
validate and update the OAuth client idempotently with admin credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import requests
import urllib3

urllib3.disable_warnings()

WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://test.letsplaydarts.eu/auth")
WSO2_CLIENT_ID = os.getenv("WSO2_CLIENT_ID", "")
WSO2_ADMIN_USERNAME = os.getenv(
    "WSO2_ADMIN_USERNAME",
    os.getenv("WSO2_ADMIN_USER", os.getenv("WSO2_IS_INTROSPECT_USER", "admin")),
)
WSO2_ADMIN_PASSWORD = os.getenv(
    "WSO2_ADMIN_PASSWORD",
    os.getenv("WSO2_ADMIN_PASS", os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")),
)
WSO2_DCR_AUTH_MODE = os.getenv("WSO2_DCR_AUTH_MODE", "auto").lower()
WSO2_DCR_BEARER_TOKEN = os.getenv("WSO2_DCR_BEARER_TOKEN", "")

CALLBACK_URI = os.getenv("WSO2_REDIRECT_URI", "https://test.letsplaydarts.eu/callback")
POST_LOGOUT_URI = os.getenv("WSO2_POST_LOGOUT_REDIRECT_URI", "https://test.letsplaydarts.eu/")


def dcr_endpoint(client_id: str) -> str:
    return f"{WSO2_IS_URL.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register/{client_id}"


def build_headers(include_json: bool = False) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if include_json:
        headers["Content-Type"] = "application/json"
    if WSO2_DCR_AUTH_MODE == "bearer" and WSO2_DCR_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {WSO2_DCR_BEARER_TOKEN}"
    return headers


def dcr_request(
    method: str,
    url: str,
    admin_user: str,
    admin_pass: str,
    payload: dict[str, Any] | None = None,
) -> requests.Response:
    def send(headers: dict[str, str], auth: tuple[str, str] | None) -> requests.Response:
        response: requests.Response | None = None
        for attempt in range(5):
            response = requests.request(
                method,
                url,
                auth=auth,
                headers=headers,
                json=payload,
                verify=False,
                timeout=10,
            )
            if response.status_code not in (502, 503, 504):
                break
            if attempt < 4:
                time.sleep(2)
        assert response is not None
        return response

    headers = build_headers(include_json=payload is not None)
    auth = None if "Authorization" in headers else (admin_user, admin_pass)
    response = send(headers, auth)

    if (
        response.status_code == 401
        and WSO2_DCR_AUTH_MODE == "auto"
        and WSO2_DCR_BEARER_TOKEN
        and "Authorization" not in headers
    ):
        retry_headers = build_headers(include_json=payload is not None)
        retry_headers["Authorization"] = f"Bearer {WSO2_DCR_BEARER_TOKEN}"
        return send(retry_headers, None)

    return response


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure WSO2 test redirect URIs via DCR")
    parser.add_argument("--ws-url", help="WSO2 base URL")
    parser.add_argument("--client-id", help="OAuth2 client ID")
    parser.add_argument("--admin-user", help="WSO2 admin username")
    parser.add_argument("--admin-pass", help="WSO2 admin password")
    parser.add_argument("--callback-uri", help="Callback URI")
    parser.add_argument("--post-logout-uri", help="Post logout redirect URI")
    args = parser.parse_args()

    global WSO2_IS_URL, WSO2_CLIENT_ID, WSO2_ADMIN_USERNAME, WSO2_ADMIN_PASSWORD
    global CALLBACK_URI, POST_LOGOUT_URI
    if args.ws_url:
        WSO2_IS_URL = args.ws_url
    if args.client_id:
        WSO2_CLIENT_ID = args.client_id
    if args.admin_user:
        WSO2_ADMIN_USERNAME = args.admin_user
    if args.admin_pass:
        WSO2_ADMIN_PASSWORD = args.admin_pass
    if args.callback_uri:
        CALLBACK_URI = args.callback_uri
    if args.post_logout_uri:
        POST_LOGOUT_URI = args.post_logout_uri

    print("=" * 60)
    print("WSO2 Identity Server - Configure Redirect URIs")
    print("=" * 60)
    print()

    if not WSO2_CLIENT_ID:
        print("❌ Error: WSO2_CLIENT_ID must be set")
        return 1

    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Client ID: {WSO2_CLIENT_ID}")
    print(f"   Callback URI: {CALLBACK_URI}")
    print(f"   Post-Logout URI: {POST_LOGOUT_URI}")
    print()

    response = dcr_request(
        "GET",
        dcr_endpoint(WSO2_CLIENT_ID),
        WSO2_ADMIN_USERNAME,
        WSO2_ADMIN_PASSWORD,
    )
    if response.status_code != 200:
        print(f"❌ Failed to fetch client: {response.status_code}")
        print(f"Response: {response.text}")
        return 1

    client_data = response.json()
    current_redirects = client_data.get("redirect_uris", [])
    desired_redirects = [CALLBACK_URI, POST_LOGOUT_URI]

    print(f"📋 Current redirect URIs: {current_redirects}")
    client_data["redirect_uris"] = desired_redirects

    update_response = dcr_request(
        "PUT",
        dcr_endpoint(WSO2_CLIENT_ID),
        WSO2_ADMIN_USERNAME,
        WSO2_ADMIN_PASSWORD,
        payload=client_data,
    )
    if update_response.status_code not in (200, 201):
        print(f"❌ Failed to update client: {update_response.status_code}")
        print(f"Response: {update_response.text}")
        return 1

    updated_client = update_response.json()
    print("✅ Redirect URIs updated successfully")
    print(json.dumps(updated_client.get("redirect_uris", desired_redirects), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())