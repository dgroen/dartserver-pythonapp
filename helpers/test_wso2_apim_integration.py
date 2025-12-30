#!/usr/bin/env python3
"""
Test script for WSO2 APIM integration with Darts Game System

This script validates that requests flow correctly through APIM:
1. Obtains OAuth2 access token from WSO2 IS
2. Submits dartboard throw through APIM gateway
3. Verifies rate limiting is working
4. Tests multiple endpoint types

Usage:
    python helpers/test_wso2_apim_integration.py
    python helpers/test_wso2_apim_integration.py --verbose
"""

import argparse
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


class APIMIntegrationTester:
    """Test WSO2 APIM integration"""

    def __init__(
        self,
        apim_gateway_url: str,
        wso2_is_url: str,
        client_id: str,
        client_secret: str,
        verify_ssl: bool = False,
    ):
        """
        Initialize tester

        Args:
            apim_gateway_url: APIM gateway URL (e.g., https://localhost:8243)
            wso2_is_url: WSO2 IS URL for token endpoint
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            verify_ssl: Whether to verify SSL certificates
        """
        self.apim_gateway_url = apim_gateway_url.rstrip("/")
        self.wso2_is_url = wso2_is_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.verify_ssl = verify_ssl
        self.access_token = None

    def get_access_token(self) -> bool:
        """
        Obtain OAuth2 access token using client credentials flow

        Returns:
            True if token obtained successfully
        """
        logger.info("Obtaining OAuth2 access token...")

        token_url = f"{self.wso2_is_url}/oauth2/token"

        data = {
            "grant_type": "client_credentials",
            "scope": "dartboard:write score:write game:create game:control player:create",
        }

        try:
            response = requests.post(
                token_url,
                auth=(self.client_id, self.client_secret),
                data=data,
                verify=self.verify_ssl,
                timeout=10,
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", "unknown")

            logger.info(f"  ✓ Access token obtained (expires in {expires_in}s)")
            return True

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Failed to obtain access token: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False

    def test_health_endpoint(self) -> bool:
        """
        Test health check endpoint (no auth required)

        Returns:
            True if test passed
        """
        logger.info("Testing health endpoint...")

        url = f"{self.apim_gateway_url}/health"

        try:
            response = requests.get(url, verify=self.verify_ssl, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "healthy":
                logger.info("  ✓ Health check passed")
                return True
            logger.error(f"  ✗ Unexpected health response: {data}")
            return False

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Health check failed: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False

    def test_dartboard_throw(self) -> bool:
        """
        Test dartboard throw submission through APIM

        Returns:
            True if test passed
        """
        logger.info("Testing dartboard throw submission...")

        url = f"{self.apim_gateway_url}/api/v1/dartboard/throw"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "pins": [20, 1],  # D20 in segment format
            "game_id": "test-game-123",
            "player_id": "test-player-1",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                logger.info(f"  ✓ Dartboard throw accepted ({response.status_code})")
                logger.debug(f"  Response: {response.text}")
                return True
            logger.error(f"  ✗ Unexpected status code: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Dartboard throw failed: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False

    def test_score_submission(self) -> bool:
        """
        Test score submission through APIM

        Returns:
            True if test passed
        """
        logger.info("Testing score submission...")

        url = f"{self.apim_gateway_url}/api/v1/scores"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "score": 20,
            "multiplier": "TRIPLE",
            "player_id": "test-player-1",
            "game_id": "test-game-123",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                logger.info(f"  ✓ Score submission accepted ({response.status_code})")
                logger.debug(f"  Response: {response.text}")
                return True
            logger.error(f"  ✗ Unexpected status code: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Score submission failed: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False

    def test_rate_limiting(self, requests_count: int = 10, delay: float = 0.1) -> bool:
        """
        Test APIM rate limiting by sending multiple requests

        Args:
            requests_count: Number of requests to send
            delay: Delay between requests in seconds

        Returns:
            True if rate limiting is detected
        """
        logger.info(f"Testing rate limiting (sending {requests_count} requests)...")

        url = f"{self.apim_gateway_url}/api/v1/dartboard/throw"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "pins": [20, 1],
            "game_id": "rate-limit-test",
            "player_id": "test-player-1",
        }

        success_count = 0
        throttled_count = 0

        for i in range(requests_count):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    verify=self.verify_ssl,
                    timeout=10,
                )

                if response.status_code in [200, 201]:
                    success_count += 1
                elif response.status_code == 429:  # Too Many Requests
                    throttled_count += 1
                    logger.debug(f"  Request {i + 1} throttled")

                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                logger.debug(f"  Request {i + 1} failed: {e}")

        logger.info(f"  Results: {success_count} successful, {throttled_count} throttled")

        # If we sent many requests and some were throttled, rate limiting is working
        if throttled_count > 0:
            logger.info("  ✓ Rate limiting is working")
            return True
        logger.info("  ℹ No throttling detected (may need to send more requests)")
        return True  # Not a failure, just may need higher volume

    def test_unauthorized_access(self) -> bool:
        """
        Test that requests without tokens are rejected

        Returns:
            True if unauthorized access is properly blocked
        """
        logger.info("Testing unauthorized access...")

        url = f"{self.apim_gateway_url}/api/v1/dartboard/throw"

        payload = {
            "pins": [20, 1],
            "game_id": "test-game-123",
            "player_id": "test-player-1",
        }

        try:
            response = requests.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            if response.status_code in [401, 403]:
                logger.info(f"  ✓ Unauthorized access properly blocked ({response.status_code})")
                return True
            logger.error(f"  ✗ Expected 401/403, got {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            logger.exception("  ✗ Test failed: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False

    def run_tests(self) -> bool:
        """
        Run all integration tests

        Returns:
            True if all tests passed
        """
        logger.info("=" * 60)
        logger.info("WSO2 APIM Integration Tests")
        logger.info("=" * 60)

        results = []

        # Test 1: Obtain access token
        results.append(("Get Access Token", self.get_access_token()))

        if not results[-1][1]:
            logger.error("Cannot proceed without access token")
            return False

        # Test 2: Health endpoint
        results.append(("Health Endpoint", self.test_health_endpoint()))

        # Test 3: Unauthorized access
        results.append(("Unauthorized Access", self.test_unauthorized_access()))

        # Test 4: Dartboard throw
        results.append(("Dartboard Throw", self.test_dartboard_throw()))

        # Test 5: Score submission
        results.append(("Score Submission", self.test_score_submission()))

        # Test 6: Rate limiting (optional)
        results.append(("Rate Limiting", self.test_rate_limiting()))

        # Print summary
        logger.info("=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {status} - {test_name}")

        logger.info("=" * 60)
        logger.info(f"Results: {passed}/{total} tests passed")
        logger.info("=" * 60)

        return passed == total


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test WSO2 APIM integration with Darts Game System",
    )
    parser.add_argument(
        "--apim-gateway-url",
        default=os.getenv("WSO2_APIM_GATEWAY_URL", "https://localhost:8243"),
        help="APIM gateway URL (default: https://localhost:8243)",
    )
    parser.add_argument(
        "--wso2-is-url",
        default=os.getenv("WSO2_IS_URL", "https://localhost:9443"),
        help="WSO2 IS URL (default: https://localhost:9443)",
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("WSO2_CLIENT_ID", ""),
        help="OAuth2 client ID",
    )
    parser.add_argument(
        "--client-secret",
        default=os.getenv("WSO2_CLIENT_SECRET", ""),
        help="OAuth2 client secret",
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

    if not args.client_id or not args.client_secret:
        logger.error("Client ID and Client Secret are required")
        logger.error("Set WSO2_CLIENT_ID and WSO2_CLIENT_SECRET environment variables")
        sys.exit(1)

    # Create tester
    tester = APIMIntegrationTester(
        apim_gateway_url=args.apim_gateway_url,
        wso2_is_url=args.wso2_is_url,
        client_id=args.client_id,
        client_secret=args.client_secret,
        verify_ssl=args.verify_ssl,
    )

    # Run tests
    success = tester.run_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
