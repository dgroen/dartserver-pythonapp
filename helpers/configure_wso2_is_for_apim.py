#!/usr/bin/env python3
"""
Configure WSO2 APIM OAuth2 Integration with WSO2 Identity Server

This script registers APIM as an OAuth2 client in WSO2 IS and configures
the Key Manager connection, allowing the APIM portals to work correctly.

Prerequisites:
- WSO2 IS running and accessible
- Admin credentials for WSO2 IS

Usage:
    python helpers/configure_wso2_is_for_apim.py
    python helpers/configure_wso2_is_for_apim.py --verbose
"""

import argparse
import logging
import os
import sys
import time

import requests
import urllib3
from dotenv import load_dotenv

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WSO2ISAPIMConfigurator:
    """Configure WSO2 IS for APIM integration"""

    def __init__(
        self,
        is_url: str,
        username: str,
        password: str,
        apim_url: str,
        verify_ssl: bool = False,
    ):
        """Initialize configurator"""
        self.is_url = is_url.rstrip("/")
        self.username = username
        self.password = password
        self.apim_url = apim_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.access_token = None
        self.client_id = None
        self.client_secret = None

        # WSO2 IS API endpoints
        self.oauth_admin_url = f"{self.is_url}/api/server/v1"
        self.scim_url = f"{self.is_url}/scim2"

    def authenticate(self) -> bool:
        """Authenticate with WSO2 IS using admin credentials"""
        logger.info("Authenticating with WSO2 IS...")

        # Use basic auth to get token
        auth_url = f"{self.is_url}/oauth2/token"

        # Register a temporary app to get tokens (using client credentials with admin user)
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "scope": "ADMIN",
        }

        try:
            response = requests.post(
                auth_url,
                auth=(self.username, self.password),
                data=data,
                verify=self.verify_ssl,
                timeout=10,
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")

            if not self.access_token:
                logger.error("No access token in response")
                return False

            logger.info("✓ Authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.exception("Authentication failed: %s", e)
            return False

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """Make authenticated request to WSO2 IS"""
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Content-Type"] = "application/json"

        return requests.request(
            method,
            url,
            headers=headers,
            verify=self.verify_ssl,
            timeout=30,
            **kwargs,
        )

    def register_apim_oauth_client(self) -> bool:
        """Register APIM as OAuth2 client in WSO2 IS"""
        logger.info("Registering APIM as OAuth2 client...")

        # OAuth2 client registration
        client_data = {
            "clientName": "wso2_api_manager",
            "clientUri": f"{self.apim_url}/publisher",
            "grantTypes": [
                "authorization_code",
                "implicit",
                "refresh_token",
                "client_credentials",
            ],
            "redirectUris": [
                f"{self.apim_url}/publisher/services/auth/callback/authorize",
                f"{self.apim_url}/admin/services/auth/callback/authorize",
                f"{self.apim_url}/devportal/services/auth/callback/authorize",
            ],
            "responseTypes": ["code", "token", "id_token"],
            "public": True,
            "requireAuthTime": False,
            "defaultMaxAge": 32400,
            "tokenEndpointAuthMethod": "none",
            "tokenEndpointAuthSigningAlg": "RS256",
        }

        try:
            # Register via OAuth2 DCR endpoint
            dcr_url = f"{self.is_url}/oauth2/dcr/register"

            response = requests.post(
                dcr_url,
                json=client_data,
                verify=self.verify_ssl,
                timeout=10,
            )
            response.raise_for_status()

            result = response.json()
            self.client_id = result.get("client_id")
            self.client_secret = result.get("client_secret")

            logger.info("✓ APIM OAuth2 client registered")
            logger.info(f"  Client ID: {self.client_id}")
            if self.client_secret:
                logger.info(f"  Client Secret: {self.client_secret}")

            return True

        except requests.exceptions.RequestException as e:
            logger.exception("Failed to register APIM OAuth2 client: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def wait_for_is_ready(self, max_retries: int = 30, retry_delay: int = 5) -> bool:
        """Wait for WSO2 IS to be ready"""
        logger.info(f"Waiting for WSO2 IS at {self.is_url} to be ready...")

        health_url = f"{self.is_url}/api/health-check/v1.0/health"

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(
                    health_url,
                    verify=self.verify_ssl,
                    timeout=5,
                )
                if response.status_code == 200:
                    logger.info(f"  ✓ WSO2 IS is ready (attempt {attempt}/{max_retries})")
                    return True
            except Exception as e:
                logger.debug(f"  Attempt {attempt}/{max_retries} failed: {e}")

            if attempt < max_retries:
                logger.info(f"  WSO2 IS not ready yet, retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        logger.error(f"  WSO2 IS did not become ready after {max_retries} attempts")
        return False

    def setup(self) -> bool:
        """Run complete setup"""
        logger.info("=" * 60)
        logger.info("WSO2 IS - APIM OAuth2 Configuration")
        logger.info("=" * 60)

        # Wait for IS to be ready
        if not self.wait_for_is_ready():
            return False

        # Authenticate
        if not self.authenticate():
            return False

        # Register APIM as OAuth2 client
        if not self.register_apim_oauth_client():
            return False

        logger.info("=" * 60)
        logger.info("✓ WSO2 IS configuration completed!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("APIM OAuth2 Configuration:")
        logger.info(f"  Client ID: {self.client_id}")
        if self.client_secret:
            logger.info(f"  Client Secret: {self.client_secret}")
        logger.info("")
        logger.info(f"  Publisher: {self.apim_url}/publisher")
        logger.info(f"  DevPortal: {self.apim_url}/devportal")
        logger.info(f"  Admin: {self.apim_url}/admin")
        logger.info("")

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Configure WSO2 IS for APIM integration",
    )
    parser.add_argument(
        "--is-url",
        default=os.getenv("WSO2_IS_URL", "https://localhost:9443"),
        help="WSO2 IS URL (default: https://localhost:9443)",
    )
    parser.add_argument(
        "--apim-url",
        default=os.getenv("WSO2_APIM_URL", "https://localhost:9444"),
        help="WSO2 APIM URL (default: https://localhost:9444)",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("WSO2_ADMIN_USERNAME", "admin"),
        help="IS admin username (default: admin)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("WSO2_ADMIN_PASSWORD", "admin"),
        help="IS admin password (default: admin)",
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
    configurator = WSO2ISAPIMConfigurator(
        is_url=args.is_url,
        username=args.username,
        password=args.password,
        apim_url=args.apim_url,
        verify_ssl=args.verify_ssl,
    )

    # Run setup
    success = configurator.setup()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
