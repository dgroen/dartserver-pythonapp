#!/usr/bin/env python3
"""
Fix WSO2 OAuth2 Callback URLs for Localhost Development
This script updates WSO2 to allow localhost:5000 as a valid callback URL
"""

import logging
import sys
from urllib.parse import urljoin

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configuration
WSO2_URL = "https://localhost:9443"
WSO2_ADMIN_USER = "admin"
WSO2_ADMIN_PASS = "admin"
LOCALHOST_CALLBACK = "http://localhost:5000/callback"


def verify_ssl(proceed: bool = False) -> bool:
    """Check if we should verify SSL for WSO2 (usually false for localhost)"""
    return proceed


def get_wso2_service_providers(verify_ssl: bool = False) -> dict | None:
    """
    Get list of service providers from WSO2
    API: GET /api/server/v1/service-providers
    """
    try:
        logger.info("Connecting to WSO2 Identity Server...")
        url = urljoin(WSO2_URL, "/api/server/v1/service-providers")

        response = requests.get(
            url,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            verify=verify_ssl,
            timeout=10,
        )

        if response.status_code == 200:
            providers = response.json()
            logger.info(f"✓ Found {len(providers.get('applications', []))} service providers")
            return providers
        logger.error(f"Failed to get service providers: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None

    except Exception:
        logger.exception("Error connecting to WSO2")
        logger.info("\n💡 Make sure WSO2 is running at https://localhost:9443")
        logger.info("   Try: docker-compose -f docker-compose-wso2.yml up -d")
        return None


def find_darts_app(providers: dict) -> dict | None:
    """Find the darts application in service providers"""
    apps = providers.get("applications", [])

    logger.info("\nAvailable Service Providers:")
    for app in apps:
        print(f"  - {app.get('name')} (ID: {app.get('id', 'unknown')})")

    # Look for the darts app
    for app in apps:
        name = app.get("name", "").lower()
        if "dart" in name or "localhost" in name or "darts" in name.lower():
            logger.info(f"\n✓ Found Darts app: {app.get('name')}")
            return app

    # If not found, ask user to select
    if apps:
        logger.info("\n❌ Could not auto-detect Darts application")
        logger.info("Available options:")
        for i, app in enumerate(apps):
            print(f"  [{i}] {app.get('name')}")

        try:
            choice = int(input("\nSelect application number (or -1 to cancel): "))
            if choice >= 0 and choice < len(apps):
                return apps[choice]
        except ValueError:
            pass

    return None


def update_callback_urls(app_id: str, new_callback: str, verify_ssl: bool = False) -> bool:
    """
    Update the callback URLs for a service provider
    API: PATCH /api/server/v1/service-providers/{id}
    """
    try:
        logger.info(f"\nUpdating callback URL for application {app_id}...")
        url = urljoin(WSO2_URL, f"/api/server/v1/service-providers/{app_id}")

        # First, get the current configuration
        response = requests.get(
            url,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            verify=verify_ssl,
            timeout=10,
        )

        if response.status_code != 200:
            logger.error(f"Failed to get current configuration: {response.status_code}")
            return False

        app_config = response.json()

        # Find or create inboundProtocolConfiguration
        if "inboundProtocolConfiguration" not in app_config:
            app_config["inboundProtocolConfiguration"] = {}

        if "oidc" not in app_config["inboundProtocolConfiguration"]:
            app_config["inboundProtocolConfiguration"]["oidc"] = {}

        oidc = app_config["inboundProtocolConfiguration"]["oidc"]

        # Update callback URLs
        if "callbackURLs" not in oidc:
            oidc["callbackURLs"] = []

        # Add localhost callback if not already present
        if new_callback not in oidc["callbackURLs"]:
            oidc["callbackURLs"].append(new_callback)
            logger.info(f"  ✓ Added: {new_callback}")
        else:
            logger.info(f"  i Already present: {new_callback}")

        # Also support regex pattern if the field allows it
        logger.info(f"\n  Configured callback URLs: {oidc['callbackURLs']}")

        # Update via PATCH
        response = requests.patch(
            url,
            json=app_config,
            auth=(WSO2_ADMIN_USER, WSO2_ADMIN_PASS),
            verify=verify_ssl,
            timeout=10,
        )

        if response.status_code in [200, 201]:
            logger.info("✓ Configuration updated successfully!")
            return True
        logger.error(f"Failed to update configuration: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return False

    except Exception:
        logger.exception("Error updating callback URLs")
        return False


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("WSO2 Localhost Callback URL Fixer")
    print("=" * 60)

    # Step 1: Get service providers
    providers = get_wso2_service_providers(verify_ssl=False)
    if not providers:
        logger.error("\n❌ Could not connect to WSO2. Aborting.")
        sys.exit(1)

    # Step 2: Find darts app
    app = find_darts_app(providers)
    if not app:
        logger.error("\n❌ Could not find Darts application. Aborting.")
        sys.exit(1)

    app_id = app.get("id")
    app_name = app.get("name")

    # Step 3: Update callback URLs
    if update_callback_urls(app_id, LOCALHOST_CALLBACK, verify_ssl=False):
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"\nWSO2 application '{app_name}' has been updated")
        print(f"Callback URL: {LOCALHOST_CALLBACK}")
        print("\nYou can now test localhost login:")
        print("  1. Visit: http://localhost:5000")
        print("  2. Click: Login with WSO2")
        print("  3. Enter: your WSO2 credentials")
        print("  4. Success! You should be logged in ✓")
        print("\nIf you still see issues:")
        print("  - Clear browser cookies and cache")
        print("  - Try incognito/private mode")
        print("  - Check server logs for errors")
        sys.exit(0)
    else:
        logger.error("\n❌ Failed to update callback URLs")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⊘ Cancelled by user")
        sys.exit(1)
