#!/usr/bin/env python3
"""
WSO2 API Manager Setup Script for Darts Game System

This script automates the configuration of WSO2 APIM to expose the Darts API Gateway:
1. Creates throttling policies for dartboard and game endpoints
2. Defines the Darts API with all endpoints from the API Gateway
3. Publishes the API to the APIM Developer Portal
4. Creates applications and subscriptions

Prerequisites:
- WSO2 API Manager 4.x running and accessible
- Admin credentials configured in environment variables
- API Gateway service deployed and accessible

Usage:
    python helpers/setup_wso2_apim.py
    python helpers/setup_wso2_apim.py --verbose
    python helpers/setup_wso2_apim.py --apim-url https://localhost:9444
"""

import argparse
import base64
import logging
import os
import sys
import time

import requests

# Suppress SSL warnings for development
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WSO2APIMConfigurator:
    """Configure WSO2 API Manager for Darts Game System"""

    def __init__(
        self,
        apim_url: str,
        username: str,
        password: str,
        api_gateway_url: str,
        verify_ssl: bool = False,
    ):
        """
        Initialize APIM configurator

        Args:
            apim_url: WSO2 APIM base URL (e.g., https://localhost:9444)
            username: Admin username
            password: Admin password
            api_gateway_url: Backend API Gateway URL (e.g., http://api-gateway:8080)
            verify_ssl: Whether to verify SSL certificates
        """
        self.apim_url = apim_url.rstrip("/")
        self.username = username
        self.password = password
        self.api_gateway_url = api_gateway_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.access_token = None
        self.api_id = None

        # API Manager endpoints
        self.publisher_api_url = f"{self.apim_url}/api/am/publisher/v4"
        self.devportal_api_url = f"{self.apim_url}/api/am/devportal/v3"
        self.admin_api_url = f"{self.apim_url}/api/am/admin/v4"
        self.token_url = f"{self.apim_url}/oauth2/token"

    def authenticate(self) -> bool:
        """
        Authenticate with WSO2 APIM and obtain access token

        Returns:
            True if authentication successful
        """
        logger.info("Authenticating with WSO2 APIM...")

        # Use password grant type for admin operations
        auth_string = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "scope": "apim:api_create apim:api_view apim:api_publish apim:subscribe apim:admin",
        }

        try:
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                verify=self.verify_ssl,
                timeout=30,
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            logger.info("✓ Authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.exception("✗ Authentication failed: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """Make authenticated request to APIM"""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        if "json" in kwargs and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        return requests.request(
            method,
            url,
            headers=headers,
            verify=self.verify_ssl,
            timeout=30,
            **kwargs,
        )

    def create_throttling_policies(self) -> bool:
        """
        Create custom throttling policies for different endpoint types

        Returns:
            True if policies created successfully
        """
        logger.info("Creating throttling policies...")

        policies = [
            {
                "policyName": "DartboardThrottle",
                "displayName": "Dartboard Throttle Policy",
                "description": "Rate limit for dartboard hardware throws (high volume)",
                "isDeployed": True,
                "defaultLimit": {
                    "type": "REQUESTCOUNTLIMIT",
                    "requestCount": {
                        "timeUnit": "min",
                        "unitTime": 1,
                        "requestCount": 1000,  # 1000 requests per minute
                    },
                },
            },
            {
                "policyName": "GameControlThrottle",
                "displayName": "Game Control Throttle Policy",
                "description": "Rate limit for game control operations",
                "isDeployed": True,
                "defaultLimit": {
                    "type": "REQUESTCOUNTLIMIT",
                    "requestCount": {
                        "timeUnit": "min",
                        "unitTime": 1,
                        "requestCount": 100,  # 100 requests per minute
                    },
                },
            },
            {
                "policyName": "UnlimitedThrottle",
                "displayName": "Unlimited",
                "description": "No rate limiting",
                "isDeployed": True,
                "defaultLimit": {
                    "type": "REQUESTCOUNTLIMIT",
                    "requestCount": {
                        "timeUnit": "min",
                        "unitTime": 1,
                        "requestCount": 999999999,
                    },
                },
            },
        ]

        success = True
        for policy in policies:
            try:
                # Check if policy already exists
                url = f"{self.admin_api_url}/throttling/policies/advanced/{policy['policyName']}"
                response = self._make_request("GET", url)

                if response.status_code == 200:
                    logger.info(f"  Policy '{policy['policyName']}' already exists, updating...")
                    response = self._make_request("PUT", url, json=policy)
                    response.raise_for_status()
                    logger.info(f"  ✓ Updated policy '{policy['policyName']}'")
                else:
                    # Create new policy
                    url = f"{self.admin_api_url}/throttling/policies/advanced"
                    response = self._make_request("POST", url, json=policy)
                    response.raise_for_status()
                    logger.info(f"  ✓ Created policy '{policy['policyName']}'")

            except requests.exceptions.RequestException as e:
                logger.exception("  ✗ Failed to create policy '%s': %s", policy["policyName"], e)
                if hasattr(e, "response") and e.response is not None:
                    logger.error(f"  Response: {e.response.text}")
                success = False

        return success

    def create_api(self) -> bool:
        """
        Create the Darts API in WSO2 APIM

        Returns:
            True if API created successfully
        """
        logger.info("Creating Darts API definition...")

        # Define API structure
        api_definition = {
            "name": "DartsGameAPI",
            "context": "/api",
            "version": "v1",
            "provider": "admin",
            "lifeCycleStatus": "CREATED",
            "isDefaultVersion": True,
            "type": "HTTP",
            "transport": ["http", "https"],
            "tags": ["darts", "game", "dartboard"],
            "policies": ["Unlimited"],
            "visibility": "PUBLIC",
            "visibleRoles": [],
            "endpointConfig": {
                "endpoint_type": "http",
                "sandbox_endpoints": {
                    "url": self.api_gateway_url,
                },
                "production_endpoints": {
                    "url": self.api_gateway_url,
                },
            },
            "gatewayEnvironments": ["Production and Sandbox"],
            "operations": [
                # Dartboard endpoint - highest rate limit
                {
                    "target": "/v1/dartboard/throw",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "DartboardThrottle",
                    "scopes": ["dartboard:write"],
                },
                # Score submission
                {
                    "target": "/v1/scores",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "GameControlThrottle",
                    "scopes": ["score:write"],
                },
                # Game management
                {
                    "target": "/v1/games",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "GameControlThrottle",
                    "scopes": ["game:create"],
                },
                # Player management
                {
                    "target": "/v1/players",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "GameControlThrottle",
                    "scopes": ["player:create"],
                },
                # Game actions
                {
                    "target": "/v1/game/actions/end-turn",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "GameControlThrottle",
                    "scopes": ["game:control"],
                },
                {
                    "target": "/v1/game/actions/continue",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "GameControlThrottle",
                    "scopes": ["game:control"],
                },
                {
                    "target": "/v1/game/actions/pause",
                    "verb": "POST",
                    "authType": "Application & Application User",
                    "throttlingPolicy": "GameControlThrottle",
                    "scopes": ["game:control"],
                },
                # Health check - no auth required
                {
                    "target": "/health",
                    "verb": "GET",
                    "authType": "None",
                    "throttlingPolicy": "Unlimited",
                },
            ],
            "scopes": [
                {
                    "name": "dartboard:write",
                    "displayName": "Write Dartboard Throws",
                    "description": "Submit dartboard throw data",
                },
                {
                    "name": "score:write",
                    "displayName": "Write Scores",
                    "description": "Submit manual scores",
                },
                {
                    "name": "game:create",
                    "displayName": "Create Games",
                    "description": "Create new game sessions",
                },
                {
                    "name": "game:control",
                    "displayName": "Control Games",
                    "description": "Control game flow (pause, continue, end turn)",
                },
                {
                    "name": "player:create",
                    "displayName": "Create Players",
                    "description": "Create player profiles",
                },
            ],
            "corsConfiguration": {
                "corsConfigurationEnabled": True,
                "accessControlAllowOrigins": ["*"],
                "accessControlAllowCredentials": False,
                "accessControlAllowHeaders": [
                    "authorization",
                    "Access-Control-Allow-Origin",
                    "Content-Type",
                    "SOAPAction",
                ],
                "accessControlAllowMethods": [
                    "GET",
                    "PUT",
                    "POST",
                    "DELETE",
                    "PATCH",
                    "OPTIONS",
                ],
            },
        }

        try:
            # Check if API already exists
            search_url = f"{self.publisher_api_url}/apis?query=name:DartsGameAPI"
            response = self._make_request("GET", search_url)
            response.raise_for_status()

            existing_apis = response.json()
            if existing_apis.get("count", 0) > 0:
                # API exists, get its ID
                self.api_id = existing_apis["list"][0]["id"]
                logger.info(f"  API already exists with ID: {self.api_id}, updating...")

                # Update existing API
                update_url = f"{self.publisher_api_url}/apis/{self.api_id}"
                response = self._make_request("PUT", update_url, json=api_definition)
                response.raise_for_status()
                logger.info("  ✓ Updated Darts API")
            else:
                # Create new API
                create_url = f"{self.publisher_api_url}/apis"
                response = self._make_request("POST", create_url, json=api_definition)
                response.raise_for_status()

                api_response = response.json()
                self.api_id = api_response["id"]
                logger.info(f"  ✓ Created Darts API with ID: {self.api_id}")

            return True

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Failed to create API: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False

    def publish_api(self) -> bool:
        """
        Publish the API to the Developer Portal

        Returns:
            True if API published successfully
        """
        if not self.api_id:
            logger.error("Cannot publish API - no API ID available")
            return False

        logger.info("Publishing API to Developer Portal...")

        try:
            # Change lifecycle to PUBLISHED
            url = f"{self.publisher_api_url}/apis/change-lifecycle"
            params = {
                "apiId": self.api_id,
                "action": "Publish",
            }

            response = self._make_request("POST", url, params=params)
            response.raise_for_status()

            logger.info("  ✓ API published successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Failed to publish API: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
                # If already published, consider it a success
                if "already in PUBLISHED state" in e.response.text:
                    logger.info("  ✓ API was already published")
                    return True
            return False

    def wait_for_apim_ready(self, max_retries: int = 30, retry_delay: int = 5) -> bool:
        """
        Wait for APIM to be ready and responding

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            True if APIM is ready
        """
        logger.info(f"Waiting for WSO2 APIM at {self.apim_url} to be ready...")

        health_url = f"{self.apim_url}/api/am/publisher/v4/apis?limit=1"

        for attempt in range(1, max_retries + 1):
            try:
                # Try to authenticate first
                if self.authenticate():
                    # Then try a simple API call
                    response = self._make_request("GET", health_url)
                    if response.status_code in [200, 401]:  # 401 is ok, just means we need auth
                        logger.info(f"  ✓ WSO2 APIM is ready (attempt {attempt}/{max_retries})")
                        return True
            except Exception as e:
                logger.debug(f"  Attempt {attempt}/{max_retries} failed: {e}")

            if attempt < max_retries:
                logger.info(f"  APIM not ready yet, retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        logger.error(f"  ✗ WSO2 APIM did not become ready after {max_retries} attempts")
        return False

    def setup(self) -> bool:
        """
        Run complete APIM setup

        Returns:
            True if setup completed successfully
        """
        logger.info("=" * 60)
        logger.info("WSO2 API Manager Setup for Darts Game System")
        logger.info("=" * 60)

        # Wait for APIM to be ready
        if not self.wait_for_apim_ready():
            return False

        # Authenticate
        if not self.authenticate():
            return False

        # Create throttling policies
        if not self.create_throttling_policies():
            logger.warning("Some throttling policies failed to create, continuing...")

        # Create API
        if not self.create_api():
            return False

        # Publish API
        if not self.publish_api():
            return False

        logger.info("=" * 60)
        logger.info("✓ WSO2 APIM setup completed successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Access APIM Publisher Portal:")
        logger.info(f"   {self.apim_url}/publisher")
        logger.info("2. Access APIM Developer Portal:")
        logger.info(f"   {self.apim_url}/devportal")
        logger.info("3. Create an application and subscribe to the Darts API")
        logger.info("4. Generate keys for your dartboard client")
        logger.info("5. Test the API using the gateway URL:")
        logger.info(f"   {self.apim_url.replace('9444', '8243')}/api/v1/dartboard/throw")
        logger.info("")

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Configure WSO2 API Manager for Darts Game System",
    )
    parser.add_argument(
        "--apim-url",
        default=os.getenv("WSO2_APIM_URL", "https://localhost:9444"),
        help="WSO2 APIM URL (default: https://localhost:9444)",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("WSO2_ADMIN_USERNAME", "admin"),
        help="APIM admin username (default: admin)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("WSO2_ADMIN_PASSWORD", "admin"),
        help="APIM admin password (default: admin)",
    )
    parser.add_argument(
        "--api-gateway-url",
        default=os.getenv("API_GATEWAY_URL", "http://api-gateway:8080"),
        help="Backend API Gateway URL (default: http://api-gateway:8080)",
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        default=os.getenv("WSO2_VERIFY_SSL", "false").lower() == "true",
        help="Verify SSL certificates",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create configurator
    configurator = WSO2APIMConfigurator(
        apim_url=args.apim_url,
        username=args.username,
        password=args.password,
        api_gateway_url=args.api_gateway_url,
        verify_ssl=args.verify_ssl,
    )

    # Run setup
    success = configurator.setup()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
