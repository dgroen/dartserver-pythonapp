"""
Example client for electronic dartboard
Demonstrates how to authenticate with WSO2 IS and submit scores via API Gateway
"""

import time

import requests

# Disable SSL warnings for development (remove in production)
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DartboardClient:
    """Client for electronic dartboard to interact with Darts Game API"""

    def __init__(
        self,
        api_gateway_url: str,
        wso2_token_url: str,
        client_id: str,
        client_secret: str,
    ):
        """
        Initialize dartboard client

        Args:
            api_gateway_url: Base URL of API Gateway (e.g., http://localhost:8080)
            wso2_token_url: WSO2 IS token endpoint (e.g., https://localhost:9443/oauth2/token)
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
        """
        self.api_gateway_url = api_gateway_url.rstrip("/")
        self.wso2_token_url = wso2_token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: str | None = None
        self.token_expiry: float = 0

    def get_access_token(self) -> str:
        """
        Obtain access token from WSO2 IS using client credentials grant

        Returns:
            Access token string

        Raises:
            Exception: If token request fails
        """
        # Check if we have a valid token
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token

        # Request new token
        print("Requesting new access token...")
        try:
            response = requests.post(
                self.wso2_token_url,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                data={
                    "grant_type": "client_credentials",
                    "scope": "score:write game:read",
                },
                verify=False,  # Set to True in production with proper certificates  # noqa: S501
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            # Set expiry with 60 second buffer
            self.token_expiry = time.time() + expires_in - 60

            print(f"Access token obtained, expires in {expires_in} seconds")
            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"Failed to obtain access token: {e}")
            raise

    def submit_score(
        self,
        score: int,
        multiplier: str,
        player_id: str | None = None,
        game_id: str | None = None,
    ) -> dict:
        """
        Submit a score to the API Gateway

        Args:
            score: Score value (0-60)
            multiplier: Multiplier type (SINGLE, DOUBLE, TRIPLE)
            player_id: Optional player identifier
            game_id: Optional game identifier

        Returns:
            API response as dictionary

        Raises:
            Exception: If score submission fails
        """
        # Get valid access token
        token = self.get_access_token()

        # Prepare request
        url = f"{self.api_gateway_url}/api/v1/scores"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "score": score,
            "multiplier": multiplier.upper(),
        }
        if player_id:
            payload["player_id"] = player_id
        if game_id:
            payload["game_id"] = game_id

        # Submit score
        print(f"Submitting score: {multiplier} {score}")
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            print(f"Score submitted successfully: {result}")
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token might be invalid, clear it and retry once
                print("Token invalid, retrying with new token...")
                self.access_token = None
                token = self.get_access_token()
                headers["Authorization"] = f"Bearer {token}"
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            print(f"Failed to submit score: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Failed to submit score: {e}")
            raise

    def check_health(self) -> bool:
        """
        Check if API Gateway is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.api_gateway_url}/health"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            health_data = response.json()
            print(f"API Gateway health: {health_data}")
            return health_data.get("status") == "healthy"
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


def simulate_dartboard():
    """Simulate an electronic dartboard sending scores"""

    # Configuration (replace with your actual values)
    config = {
        "api_gateway_url": "http://localhost:8080",
        "wso2_token_url": "https://localhost:9443/oauth2/token",
        "client_id": "YOUR_CLIENT_ID",  # Replace with actual client ID
        "client_secret": "YOUR_CLIENT_SECRET",  # Replace with actual client secret
    }

    # Initialize client
    client = DartboardClient(**config)

    # Check health
    print("Checking API Gateway health...")
    if not client.check_health():
        print("API Gateway is not healthy, exiting...")
        return

    # Simulate dart throws
    print("\nSimulating dart throws...")

    throws = [
        {"score": 20, "multiplier": "TRIPLE"},  # Triple 20
        {"score": 20, "multiplier": "TRIPLE"},  # Triple 20
        {"score": 20, "multiplier": "TRIPLE"},  # Triple 20 (180!)
        {"score": 19, "multiplier": "SINGLE"},  # Single 19
        {"score": 5, "multiplier": "DOUBLE"},  # Double 5
        {"score": 0, "multiplier": "SINGLE"},  # Miss
        {"score": 25, "multiplier": "DOUBLE"},  # Bull's eye
    ]

    for i, throw in enumerate(throws, 1):
        print(f"\n--- Throw {i} ---")
        try:
            result = client.submit_score(
                score=throw["score"],
                multiplier=throw["multiplier"],
                player_id="dartboard-001",
                game_id="game-123",
            )
            print(f"Result: {result['status']}")
        except Exception as e:
            print(f"Error: {e}")

        # Wait a bit between throws
        time.sleep(1)

    print("\nSimulation complete!")


if __name__ == "__main__":
    print("=== Electronic Dartboard Client Example ===\n")
    print("This example demonstrates how to:")
    print("1. Authenticate with WSO2 Identity Server")
    print("2. Obtain OAuth2 access token")
    print("3. Submit scores to API Gateway")
    print("4. Handle token expiration and renewal\n")

    print("IMPORTANT: Update the configuration with your actual credentials!\n")

    # To run simulation, uncomment the following line:
    # simulate_dartboard()  # noqa: ERA001

    print("\nTo run the simulation:")
    print("1. Update the config dictionary with your credentials")
    print("2. Uncomment the simulate_dartboard() call")
    print("3. Run this script: python examples/dartboard_client.py")
