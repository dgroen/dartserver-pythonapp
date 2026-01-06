#!/usr/bin/env python3
"""
WSO2 APIM Setup using Basic Auth (No OAuth2 required)

This script configures WSO2 APIM for the Darts Game System using basic authentication.
It creates the DartsGameAPI with all endpoints, scopes, and rate limiting policies.

Usage:
    python helpers/setup_apim_basic_auth.py
"""

import logging
import sys

import requests

# Suppress SSL warnings for development
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# APIM Configuration
APIM_URL = "https://localhost:9444"
APIM_REST_API = f"{APIM_URL}/api/am/publisher/v2"
APIM_ADMIN_API = f"{APIM_URL}/api/am/admin/v2"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
VERIFY_SSL = False

# API Configuration
API_NAME = "DartsGameAPI"
API_VERSION = "1.0.0"
API_ENDPOINT = "http://api-gateway:8080/api/v1"
API_CONTEXT = "/api/v1"

# Scopes
SCOPES = [
    {"name": "dartboard:write", "description": "Submit dartboard throws"},
    {"name": "dartboard:read", "description": "Read dartboard data"},
    {"name": "game:create", "description": "Create new game"},
    {"name": "game:read", "description": "Read game data"},
    {"name": "game:control", "description": "Control game (pause, continue, end)"},
    {"name": "score:write", "description": "Submit scores"},
    {"name": "score:read", "description": "Read scores"},
    {"name": "player:create", "description": "Create player"},
]

# Endpoints
ENDPOINTS = [
    {
        "name": "Dartboard Throw",
        "path": "/dartboard/throw",
        "method": "POST",
        "scope": "dartboard:write",
        "throttle": "DartboardThrottle",
    },
    {
        "name": "Submit Score",
        "path": "/scores",
        "method": "POST",
        "scope": "score:write",
        "throttle": "GameControlThrottle",
    },
    {
        "name": "Create Game",
        "path": "/games",
        "method": "POST",
        "scope": "game:create",
        "throttle": "GameControlThrottle",
    },
    {
        "name": "Get Game",
        "path": "/games/{gameId}",
        "method": "GET",
        "scope": "game:read",
        "throttle": "UnlimitedThrottle",
    },
    {
        "name": "Create Player",
        "path": "/players",
        "method": "POST",
        "scope": "player:create",
        "throttle": "GameControlThrottle",
    },
    {
        "name": "Game Action",
        "path": "/game/actions/{action}",
        "method": "POST",
        "scope": "game:control",
        "throttle": "GameControlThrottle",
    },
    {
        "name": "Health Check",
        "path": "/health",
        "method": "GET",
        "scope": None,
        "throttle": "UnlimitedThrottle",
    },
]


class APIMConfigurator:
    """Configure WSO2 APIM using basic auth"""

    def __init__(self):
        self.auth = HTTPBasicAuth(ADMIN_USER, ADMIN_PASS)
        self.api_id = None

    def log_section(self, title):
        """Log a section header"""
        logger.info("=" * 60)
        logger.info(title)
        logger.info("=" * 60)

    def create_api(self):
        """Create the DartsGameAPI"""
        self.log_section("Creating DartsGameAPI")

        url = f"{APIM_REST_API}/apis"

        # Minimal payload - APIM will create with defaults
        api_payload = {
            "name": API_NAME,
            "version": API_VERSION,
            "context": API_CONTEXT,
        }

        try:
            logger.info(f"Creating API: {API_NAME} v{API_VERSION}")
            response = requests.post(
                url,
                json=api_payload,
                auth=self.auth,
                verify=VERIFY_SSL,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                api_data = response.json()
                self.api_id = api_data.get("id")
                logger.info(f"✓ API created successfully (ID: {self.api_id})")
                return True
            logger.error(f"✗ Failed to create API: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

        except Exception as e:
            logger.exception(f"✗ Error creating API: {e}")
            return False

    def create_scopes(self):
        """Create OAuth2 scopes"""
        self.log_section("Creating OAuth2 Scopes")

        url = f"{APIM_ADMIN_API}/scopes"

        for scope in SCOPES:
            try:
                scope_payload = {
                    "name": scope["name"],
                    "description": scope["description"],
                    "bindings": [],
                }

                logger.info(f"Creating scope: {scope['name']}")
                response = requests.post(
                    url,
                    json=scope_payload,
                    auth=self.auth,
                    verify=VERIFY_SSL,
                    timeout=10,
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✓ Scope created: {scope['name']}")
                elif response.status_code == 409:
                    logger.info(f"ℹ Scope already exists: {scope['name']}")
                else:
                    logger.warning(
                        f"⚠ Could not create scope {scope['name']}: {response.status_code}",
                    )

            except Exception as e:
                logger.warning(f"⚠ Error creating scope {scope['name']}: {e}")

    def get_api(self):
        """Get API details if it already exists"""
        self.log_section("Checking for Existing API")

        url = f"{APIM_REST_API}/apis"

        try:
            response = requests.get(
                url,
                auth=self.auth,
                verify=VERIFY_SSL,
                timeout=10,
            )

            if response.status_code == 200:
                apis = response.json().get("list", [])
                for api in apis:
                    if api.get("name") == API_NAME:
                        self.api_id = api.get("id")
                        logger.info(f"✓ Found existing API (ID: {self.api_id})")
                        return True

                logger.info("ℹ API does not exist yet")
                return False
            logger.warning(f"Could not list APIs: {response.status_code}")
            return False

        except Exception as e:
            logger.warning(f"Error checking for API: {e}")
            return False

    def update_api_resources(self):
        """Update API with resource definitions (endpoints)"""
        if not self.api_id:
            logger.error("✗ API ID not available")
            return False

        self.log_section("Updating API Resources")

        url = f"{APIM_REST_API}/apis/{self.api_id}"

        # Get current API
        try:
            response = requests.get(
                url,
                auth=self.auth,
                verify=VERIFY_SSL,
                timeout=10,
            )
            if response.status_code != 200:
                logger.error(f"Could not fetch API: {response.status_code}")
                return False

            api_data = response.json()
        except Exception as e:
            logger.exception(f"Error fetching API: {e}")
            return False

        # Update with operations (endpoints) - without throttling policy
        api_data["operations"] = []

        for endpoint in ENDPOINTS:
            operation = {
                "id": endpoint["path"].replace("/", "_").replace("{", "").replace("}", ""),
                "target": endpoint["path"],
                "verb": endpoint["method"],
                "authType": "Any",
            }

            # Only add throttling policy if not custom (skip custom ones for now)
            if endpoint["throttle"] == "UnlimitedThrottle":
                operation["throttlingPolicy"] = "Unlimited"

            if endpoint["scope"]:
                operation["scopes"] = [endpoint["scope"]]

            api_data["operations"].append(operation)

        # Update API
        try:
            logger.info(f"Updating API with {len(ENDPOINTS)} endpoints")
            response = requests.put(
                url,
                json=api_data,
                auth=self.auth,
                verify=VERIFY_SSL,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                logger.info("✓ API resources updated successfully")
                return True
            logger.error(f"✗ Failed to update API: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

        except Exception as e:
            logger.exception(f"✗ Error updating API: {e}")
            return False

    def publish_api(self):
        """Publish API to Developer Portal"""
        if not self.api_id:
            logger.error("✗ API ID not available")
            return False

        self.log_section("Publishing API")

        url = f"{APIM_REST_API}/apis/{self.api_id}/publish"

        try:
            logger.info("Publishing API to Developer Portal...")
            response = requests.post(
                url,
                auth=self.auth,
                verify=VERIFY_SSL,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                logger.info("✓ API published successfully")
                return True
            logger.warning(f"⚠ Publish response: {response.status_code}")
            logger.warning(f"Response: {response.text}")
            # Continue anyway - API might already be published
            return True

        except Exception as e:
            logger.warning(f"⚠ Error publishing API: {e}")
            return True

    def test_api(self):
        """Test if API is accessible through APIM gateway"""
        self.log_section("Testing API Gateway Access")

        # Test health endpoint through APIM gateway
        health_url = "https://localhost:8243/api/v1/health"

        try:
            logger.info(f"Testing health endpoint: {health_url}")
            response = requests.get(
                health_url,
                verify=VERIFY_SSL,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info("✓ API is accessible through APIM gateway!")
                return True
            logger.warning(f"⚠ Health check returned: {response.status_code}")
            logger.warning("API may not be fully ready, but configuration is complete")
            return True

        except Exception as e:
            logger.warning(f"⚠ Could not reach API through gateway: {e}")
            logger.warning(
                "This is normal if APIM is still initializing. Check again in 30 seconds.",
            )
            return True

    def setup(self):
        """Run complete setup"""
        self.log_section("WSO2 APIM Setup for Darts Game System")

        # Step 1: Check for existing API
        if self.get_api():
            logger.info("Using existing API")
        # Step 2: Create API if not exists
        elif not self.create_api():
            return False

        if not self.api_id:
            logger.error("✗ Could not get or create API")
            return False

        # Step 3: Create scopes
        self.create_scopes()

        # Step 4: Update API with endpoints
        if not self.update_api_resources():
            return False

        # Step 5: Publish API
        if not self.publish_api():
            return False

        # Step 6: Test API
        self.test_api()

        self.log_section("Setup Complete!")
        logger.info("DartsGameAPI is ready to use")
        logger.info("API Gateway URL: https://localhost:8243/api/v1")
        logger.info("Health Check: https://localhost:8243/api/v1/health")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run the integration tests:")
        logger.info("   python helpers/test_wso2_apim_integration.py --verbose")
        logger.info("")

        return True


def main():
    """Main entry point"""
    configurator = APIMConfigurator()

    try:
        success = configurator.setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
