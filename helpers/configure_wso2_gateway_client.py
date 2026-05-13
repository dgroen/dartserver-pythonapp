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
import builtins
import json
import os
import sys
from typing import Any

import requests
import urllib3

urllib3.disable_warnings()

DCR_AUTH_MODE = os.getenv("WSO2_DCR_AUTH_MODE", "auto").lower()
DCR_BEARER_TOKEN = os.getenv("WSO2_DCR_BEARER_TOKEN", "")


def _dcr_headers(include_json: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if include_json:
        headers["Content-Type"] = "application/json"
    if DCR_AUTH_MODE == "bearer" and DCR_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {DCR_BEARER_TOKEN}"
    return headers


def _dcr_request(
    method: str,
    url: str,
    admin_user: str,
    admin_pass: str,
    payload: dict[str, Any] | None = None,
) -> requests.Response:
    headers = _dcr_headers(include_json=payload is not None)
    auth = None if "Authorization" in headers else (admin_user, admin_pass)

    response = requests.request(
        method,
        url,
        auth=auth,
        headers=headers,
        json=payload,
        verify=False,
        timeout=10,
    )

    if (
        response.status_code == 401
        and DCR_AUTH_MODE == "auto"
        and DCR_BEARER_TOKEN
        and "Authorization" not in headers
    ):
        retry_headers = _dcr_headers(include_json=payload is not None)
        retry_headers["Authorization"] = f"Bearer {DCR_BEARER_TOKEN}"
        return requests.request(
            method,
            url,
            headers=retry_headers,
            json=payload,
            verify=False,
            timeout=10,
        )

    return response


def get_env_or(arg_val: str | None, env_name: str, default: str | None = None) -> str:
    if arg_val:
        return arg_val
    return os.getenv(env_name, default or "")


def dcr_get(ws_url: str, client_id: str, admin_user: str, admin_pass: str, client_secret: str = "") -> requests.Response:
    url = f"{ws_url.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register/{client_id}"
    resp = _dcr_request("GET", url, admin_user, admin_pass)
    # WSO2 IS 7.x DCR GET follows RFC 7592 and returns 401 for admin Basic auth.
    # Retry with client credentials (client_id:client_secret) so idempotent runs work.
    if resp.status_code == 401 and client_secret:
        print(
            "   ℹ️  Admin auth returned 401 on DCR GET (WSO2 IS 7.x behaviour); "
            "retrying with client credentials..."
        )
        url2 = url  # same URL
        resp2 = requests.get(
            url2,
            auth=(client_id, client_secret),
            headers={"Accept": "application/json"},
            verify=False,
            timeout=10,
        )
        return resp2
    return resp


def dcr_post(
    ws_url: str,
    payload: dict[str, Any],
    admin_user: str,
    admin_pass: str,
) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register"
    return _dcr_request("POST", url, admin_user, admin_pass, payload=payload)


def dcr_put(
    ws_url: str,
    client_id: str,
    payload: dict[str, Any],
    admin_user: str,
    admin_pass: str,
) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/api/identity/oauth2/dcr/v1.1/register/{client_id}"
    return _dcr_request("PUT", url, admin_user, admin_pass, payload=payload)


def request_token(
    ws_url: str,
    client_id: str,
    client_secret: str,
    scope: str | None = None,
) -> requests.Response:
    url = f"{ws_url.rstrip('/')}/oauth2/token"
    data = {"grant_type": "client_credentials"}
    if scope:
        data["scope"] = scope
    return requests.post(url, auth=(client_id, client_secret), data=data, verify=False, timeout=10)


def main() -> int:  # noqa: PLR0911
    p = argparse.ArgumentParser(description="Configure WSO2 OAuth2 client for API Gateway")
    p.add_argument("--ws-url", help="WSO2 base URL (e.g. https://localhost:9443)")
    p.add_argument("--admin-user", help="WSO2 admin username")
    p.add_argument("--admin-pass", help="WSO2 admin password")
    p.add_argument("--client-id", help="OAuth2 client id to configure")
    p.add_argument("--client-secret", help="OAuth2 client secret")
    p.add_argument("--redirect-uris", help="Comma-separated redirect URIs to set (optional)")
    p.add_argument("--scope", help="Scope to test token request with (optional)")
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit only a JSON object on stdout when successful",
    )
    p.add_argument("--dry-run", action="store_true", help="Show actions without applying")
    args = p.parse_args()

    orig_print = print
    if args.json:

        def stderr_print(*values, **kwargs):
            kwargs.setdefault("file", sys.stderr)
            return orig_print(*values, **kwargs)

        builtins.print = stderr_print

    wso2_is_url = get_env_or(args.ws_url, "WSO2_IS_URL", "https://localhost:9443")
    admin_user = get_env_or(
        args.admin_user,
        "WSO2_IS_ADMIN_USER",
        os.getenv(
            "WSO2_ADMIN_USER",
            os.getenv(
                "WSO2_ADMIN_USERNAME",
                os.getenv("WSO2_IS_INTROSPECT_USER", "admin"),
            ),
        ),
    )
    admin_pass = get_env_or(
        args.admin_pass,
        "WSO2_IS_ADMIN_PASS",
        os.getenv(
            "WSO2_ADMIN_PASS",
            os.getenv(
                "WSO2_ADMIN_PASSWORD",
                os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin"),
            ),
        ),
    )
    client_id = get_env_or(
        args.client_id,
        "WSO2_IS_CLIENT_ID",
        os.getenv("WSO2_GATEWAY_CLIENT_ID", os.getenv("WSO2_CLIENT_ID", "")),
    )
    client_secret = get_env_or(
        args.client_secret,
        "WSO2_IS_CLIENT_SECRET",
        os.getenv("WSO2_GATEWAY_CLIENT_SECRET", os.getenv("WSO2_CLIENT_SECRET", "")),
    )
    redirect_uris = []
    if args.redirect_uris:
        redirect_uris = [u.strip() for u in args.redirect_uris.split(",") if u.strip()]
    elif os.getenv("WSO2_REDIRECT_URI"):
        # single redirect URL may be provided
        redirect_uris = [os.getenv("WSO2_REDIRECT_URI")]

    if not client_id:
        print("ERROR: CLIENT_ID not provided (set WS02_CLIENT_ID or --client-id)")
        return 2

    print(f"Using WSO2 URL: {wso2_is_url}")
    print(f"Client ID: {client_id}")
    print(f"DCR auth mode: {DCR_AUTH_MODE}")

    # Fetch existing client
    try:
        resp = dcr_get(wso2_is_url, client_id, admin_user, admin_pass, client_secret)
    except Exception as e:
        print(f"ERROR: failed to contact WSO2 DCR endpoint: {e}")
        return 3

    if resp.status_code == 200:
        client = resp.json()
        print("Found existing client configuration")
    elif resp.status_code == 404:
        client = None
        print("Client not found (404); will attempt to create")
    elif resp.status_code in (401, 403):
        # WSO2 IS 7.x returns 401 (not 404) for unknown client_id when using client
        # credentials — treat as "client not found" since admin SCIM auth is valid.
        if resp.status_code == 401:
            client = None
            print("Client not found (401 on client-credential GET = unknown client_id); will attempt to create")
        else:
            print(
                "Failed to lookup existing client due authorization error "
                f"(status {resp.status_code}); refusing to create a new client",
            )
            print(f"Response: {resp.text}")
            return 4
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
    if client_secret:
        desired["client_secret"] = client_secret
    # set redirect URIs if provided
    if redirect_uris:
        desired["redirect_uris"] = redirect_uris
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
            "ext_param_client_id": client_id,
            "ext_param_client_secret": client_secret or "",
            "grant_types": desired["grant_types"],
            "redirect_uris": desired.get("redirect_uris", []),
            "token_endpoint_auth_method": desired.get("token_endpoint_auth_method"),
        }
        print("Registering new client via DCR...")
        r = dcr_post(wso2_is_url, payload, admin_user, admin_pass)
        if r.status_code not in (200, 201):
            if client_secret:
                print(
                    "DCR create failed "
                    f"({r.status_code}); checking whether client already exists",
                )
                token_check = request_token(
                    wso2_is_url,
                    client_id,
                    client_secret,
                    args.scope,
                )
                if token_check.status_code == 200:
                    print("Client already usable; continuing")
                else:
                    print(f"Failed to register client: {r.status_code} {r.text}")
                    return 5
            else:
                print(f"Failed to register client: {r.status_code} {r.text}")
                return 5
        print("Client registered")
    else:
        print("Updating existing client via DCR...")
        r = dcr_put(wso2_is_url, client_id, desired, admin_user, admin_pass)
        if r.status_code not in (200, 201):
            print(f"Failed to update client: {r.status_code} {r.text}")
            return 6
        print("Client updated")

    # Verify by requesting token
    if client_secret:
        print("Requesting client_credentials token to verify configuration...")
        t = request_token(wso2_is_url, client_id, client_secret, args.scope)
        if t.status_code == 200:
            print("Token request successful")
            try:
                print(json.dumps(t.json(), indent=2))
            except Exception:
                print(t.text)
            if args.json:
                orig_print(
                    json.dumps(
                        {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "redirect_uris": desired.get("redirect_uris", []),
                        },
                    ),
                )
            return 0
        print(f"Token request failed: {t.status_code} {t.text}")
        return 7

    print("No CLIENT_SECRET provided; update applied but token verification skipped.")
    if args.json:
        orig_print(
            json.dumps(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": desired.get("redirect_uris", []),
                },
            ),
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
