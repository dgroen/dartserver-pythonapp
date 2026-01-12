#!/usr/bin/env python3
"""
Idempotent WSO2 client configurator for the API Gateway.

Usage: set environment variables or pass via CLI flags.

This script will ensure the OAuth2 client (by CLIENT_ID) exists and is
configured to allow the `client_credentials` grant and uses
`client_secret_basic` for token endpoint authentication. It can also set
redirect URIs if provided. It verifies the change by requesting a token.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests
import urllib3

urllib3.disable_warnings()


def get_env_or(arg_val: str | None, env_name: str, default: str | None = None) -> str:
    if arg_val:
        return arg_val
    return os.getenv(env_name, default or "")


def dcr_get(ws_url: str, client_id: str, admin_user: str, admin_pass: str) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register/{client_id}"
    return requests.get(
        url,
        auth=(admin_user, admin_pass),
        headers={"Accept": "application/json"},
        verify=False,
        timeout=10,
    )


def dcr_post(
    ws_url: str, payload: dict[str, Any], admin_user: str, admin_pass: str
) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register"
    return requests.post(
        url,
        auth=(admin_user, admin_pass),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        verify=False,
        timeout=10,
    )


def dcr_put(
    ws_url: str, client_id: str, payload: dict[str, Any], admin_user: str, admin_pass: str
) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register/{client_id}"
    return requests.put(
        url,
        auth=(admin_user, admin_pass),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        verify=False,
        timeout=10,
    )


def request_token(
    ws_url: str, client_id: str, client_secret: str, scope: str | None = None
) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/oauth2/token"
    data = {"grant_type": "client_credentials"}
    if scope:
        data["scope"] = scope
    return requests.post(url, auth=(client_id, client_secret), data=data, verify=False, timeout=10)


def main() -> int:
    p = argparse.ArgumentParser(description="Configure WSO2 OAuth2 client for API Gateway")
    p.add_argument("--ws-url", help="WSO2 base URL (e.g. https://localhost:9443)")
    p.add_argument("--admin-user", help="WSO2 admin username")
    p.add_argument("--admin-pass", help="WSO2 admin password")
    p.add_argument("--client-id", help="OAuth2 client id to configure")
    p.add_argument("--client-secret", help="OAuth2 client secret")
    p.add_argument("--redirect-uris", help="Comma-separated redirect URIs to set (optional)")
    p.add_argument("--scope", help="Scope to test token request with (optional)")
    p.add_argument("--dry-run", action="store_true", help="Show actions without applying")
    args = p.parse_args()

    WSO2_IS_URL = get_env_or(args.ws_url, "WSO2_IS_URL", "https://localhost:9443")
    ADMIN_USER = get_env_or(
        args.admin_user, "WSO2_IS_ADMIN_USER", os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
    )
    ADMIN_PASS = get_env_or(
        args.admin_pass, "WSO2_IS_ADMIN_PASS", os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")
    )
    CLIENT_ID = get_env_or(args.client_id, "WSO2_CLIENT_ID", os.getenv("WSO2_CLIENT_ID", ""))
    CLIENT_SECRET = get_env_or(
        args.client_secret, "WSO2_CLIENT_SECRET", os.getenv("WSO2_CLIENT_SECRET", "")
    )
    REDIRECT_URIS = []
    if args.redirect_uris:
        REDIRECT_URIS = [u.strip() for u in args.redirect_uris.split(",") if u.strip()]
    elif os.getenv("WSO2_REDIRECT_URI"):
        # single redirect URL may be provided
        REDIRECT_URIS = [os.getenv("WSO2_REDIRECT_URI")]

    if not CLIENT_ID:
        print("ERROR: CLIENT_ID not provided (set WS02_CLIENT_ID or --client-id)")
        return 2

    print(f"Using WSO2 URL: {WSO2_IS_URL}")
    print(f"Client ID: {CLIENT_ID}")

    # Fetch existing client
    try:
        resp = dcr_get(WSO2_IS_URL, CLIENT_ID, ADMIN_USER, ADMIN_PASS)
    except Exception as e:
        print(f"ERROR: failed to contact WSO2 DCR endpoint: {e}")
        return 3

    if resp.status_code == 200:
        client = resp.json()
        print("Found existing client configuration")
    elif resp.status_code == 404:
        client = None
        print("Client not found, will attempt to create")
    else:
        print(f"Failed to fetch client: {resp.status_code} {resp.text}")
        return 4

    # Prepare desired configuration
    desired = client.copy() if client else {}
    # ensure grant_types
    grants = set(desired.get("grant_types", []))
    grants.update(["client_credentials"])
    # keep authorization_code/refresh_token if present
    desired["grant_types"] = list(grants)
    # ensure token endpoint auth method
    desired["token_endpoint_auth_method"] = (
        desired.get("token_endpoint_auth_method") or "client_secret_basic"
    )
    # set client secret if provided
    if CLIENT_SECRET:
        desired["client_secret"] = CLIENT_SECRET
    # set redirect URIs if provided
    if REDIRECT_URIS:
        desired["redirect_uris"] = REDIRECT_URIS
    # enable PKCE support so Swagger UI can use Authorization Code + PKCE
    # without requiring a client secret in the browser
    desired["ext_pkce_support_plain"] = True
    # do not require PKCE for all clients (keep optional)
    desired["ext_pkce_mandatory"] = False

    # If dry-run, show diff and exit
    if args.dry_run:
        print("Dry-run mode; would apply the following payload:")
        print(json.dumps(desired, indent=2))
        return 0

    # Create or update
    if client is None:
        # ensure required fields for creation
        payload = {
            "client_name": os.getenv("SWAGGER_CLIENT_NAME", "DartsApiGateway"),
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET or "",
            "grant_types": desired["grant_types"],
            "redirect_uris": desired.get("redirect_uris", []),
            "token_endpoint_auth_method": desired.get("token_endpoint_auth_method"),
        }
        print("Registering new client via DCR...")
        r = dcr_post(WSO2_IS_URL, payload, ADMIN_USER, ADMIN_PASS)
        if r.status_code not in (200, 201):
            print(f"Failed to register client: {r.status_code} {r.text}")
            return 5
        print("Client registered")
    else:
        print("Updating existing client via DCR...")
        r = dcr_put(WSO2_IS_URL, CLIENT_ID, desired, ADMIN_USER, ADMIN_PASS)
        if r.status_code not in (200, 201):
            print(f"Failed to update client: {r.status_code} {r.text}")
            return 6
        print("Client updated")

    # Verify by requesting token
    if CLIENT_SECRET:
        print("Requesting client_credentials token to verify configuration...")
        t = request_token(WSO2_IS_URL, CLIENT_ID, CLIENT_SECRET, args.scope)
        if t.status_code == 200:
            print("Token request successful")
            try:
                print(json.dumps(t.json(), indent=2))
            except Exception:
                print(t.text)
            return 0
        print(f"Token request failed: {t.status_code} {t.text}")
        return 7

    print("No CLIENT_SECRET provided; update applied but token verification skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
