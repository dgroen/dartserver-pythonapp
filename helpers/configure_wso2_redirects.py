#!/usr/bin/env python3
"""
Script to configure WSO2 Identity Server OAuth2 Application Redirect URIs
Automates callback regex/post-logout configuration via server/v1 applications API.
"""

import os
import sys
import time
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()  # type: ignore

# Load environment variables
load_dotenv()

# WSO2 IS Configuration
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://localhost:9443")
WSO2_CLIENT_ID = os.getenv("WSO2_CLIENT_ID", "")  # used to locate the app
WSO2_APP_NAME = os.getenv("WSO2_APP_NAME", "DartsApp")
WSO2_ADMIN_USERNAME = os.getenv("WSO2_ADMIN_USERNAME", "admin")
WSO2_ADMIN_PASSWORD = os.getenv("WSO2_ADMIN_PASSWORD", "admin")
WSO2_IS_VERIFY_SSL = os.getenv("WSO2_IS_VERIFY_SSL", "False").lower() == "true"

# Redirect URIs to register
CALLBACK_URI = os.getenv("WSO2_REDIRECT_URI", "https://localhost:5000/callback")
POST_LOGOUT_URI = os.getenv("WSO2_POST_LOGOUT_REDIRECT_URI", "https://localhost:5000/")

# API endpoints
API_BASE = f"{WSO2_IS_URL}/api/server/v1"
APPLICATIONS_ENDPOINT = f"{API_BASE}/applications"


def build_regex_pattern(callback_uri: str) -> str:
    """Build a regex callback pattern that accepts both callback and post-logout URLs."""
    parsed = urlparse(callback_uri)
    host_port = parsed.netloc
    scheme = parsed.scheme or "https"
    return f"regexp={scheme}://{host_port}(/callback|/)"


def find_application(session, auth):
    """Find application by clientId (preferred) or by name."""
    params = {}
    if WSO2_CLIENT_ID:
        params["filter"] = f'clientId eq "{WSO2_CLIENT_ID}"'
    else:
        params["filter"] = f'name eq "{WSO2_APP_NAME}"'
    params["limit"] = 50

    response = session.get(
        APPLICATIONS_ENDPOINT,
        auth=auth,
        params=params,
        verify=WSO2_IS_VERIFY_SSL,
        timeout=10,
    )

    if response.status_code == 200:
        apps = response.json().get("applications", [])
        if apps:
            return apps[0]
        # Fallback: fetch all and match by name
        response_all = session.get(
            APPLICATIONS_ENDPOINT,
            auth=auth,
            params={"limit": 100},
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )
        if response_all.status_code == 200:
            for app in response_all.json().get("applications", []):
                if app.get("name") == WSO2_APP_NAME:
                    return app
        return None

    print(f"❌ Failed to list applications: {response.status_code}")
    print(f"Response: {response.text}")
    return None


def create_application(session, auth, pattern):
    """Create a simple OAuth2 application if it does not exist."""
    payload = {
        "name": WSO2_APP_NAME,
        "description": "Darts application OAuth",
        "templateId": "custom",
        "inboundProtocolConfiguration": {
            "oidc": {
                "grantTypes": ["authorization_code", "refresh_token"],
                "callbackURLs": [pattern],
            },
        },
    }

    response = session.post(
        APPLICATIONS_ENDPOINT,
        auth=auth,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        verify=WSO2_IS_VERIFY_SSL,
        timeout=10,
    )

    if response.status_code in (200, 201):
        try:
            app = response.json()
        except Exception:
            print("❌ Failed to parse create response:", response.text)
            return None
        print(f"✓ Created application {app.get('name')} (ID: {app.get('id')})")
        return app

    print(f"❌ Failed to create application: {response.status_code}")
    print(f"Response: {response.text}")
    return None


def update_application_redirect_uris(session, auth, app_id, new_pattern):
    """Update application redirect URIs to include both callback and post-logout URIs."""
    response = session.get(
        f"{APPLICATIONS_ENDPOINT}/{app_id}/inbound-protocols/oidc",
        auth=auth,
        verify=WSO2_IS_VERIFY_SSL,
        timeout=10,
    )

    if response.status_code != 200:
        print(f"❌ Failed to get OIDC inbound config: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    oidc_config = response.json()
    current_callbacks = oidc_config.get("callbackURLs", [])
    print(f"\n📋 Current callback URLs: {current_callbacks}")

    oidc_config["callbackURLs"] = [new_pattern]
    print(f"✅ New callback pattern: {new_pattern}")

    update_response = session.put(
        f"{APPLICATIONS_ENDPOINT}/{app_id}/inbound-protocols/oidc",
        auth=auth,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=oidc_config,
        verify=WSO2_IS_VERIFY_SSL,
        timeout=10,
    )

    if update_response.status_code in [200, 204]:
        print("✅ Application updated successfully!")
        return True

    print(f"❌ Failed to update application: {update_response.status_code}")
    print(f"Response: {update_response.text}")
    return False


def main():
    """Main function"""
    print("=" * 60)
    print("WSO2 Identity Server - Configure Redirect URIs")
    print("=" * 60)
    print()

    print("🔧 Configuration:")
    print(f"   WSO2 IS URL: {WSO2_IS_URL}")
    print(f"   Admin User : {WSO2_ADMIN_USERNAME}")
    print(f"   Client ID  : {WSO2_CLIENT_ID or '(search by app name)'}")
    print(f"   App Name   : {WSO2_APP_NAME}")
    print(f"   Callback   : {CALLBACK_URI}")
    print(f"   PostLogout : {POST_LOGOUT_URI}")
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
            print(f"   Retry {i + 1}/{max_retries}...")
            time.sleep(2)
        else:
            print("❌ WSO2 IS is not responding. Please check if it's running.")
            sys.exit(1)

    print()

    session = requests.Session()
    auth = (WSO2_ADMIN_USERNAME, WSO2_ADMIN_PASSWORD)

    pattern = build_regex_pattern(CALLBACK_URI)

    app = find_application(session, auth)
    if not app:
        print("ℹ No existing application found; creating one...")
        app = create_application(session, auth, pattern)
        if not app:
            sys.exit(1)

    app_id = app.get("id")
    app_name = app.get("name")
    print(f"✓ Target application: {app_name} (ID: {app_id})")

    if not update_application_redirect_uris(session, auth, app_id, pattern):
        sys.exit(1)

    print()
    print("All done. Verify login and logout flows against the updated callback regex.")


if __name__ == "__main__":
    main()
