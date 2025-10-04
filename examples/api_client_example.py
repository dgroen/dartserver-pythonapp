#!/usr/bin/env python3
"""
WSO2 API Gateway Client Example

This script demonstrates how to interact with the Darts API Gateway
using OAuth2 authentication.

Usage:
    python api_client_example.py
"""

import json

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DartsAPIClient:
    """Client for interacting with the Darts API Gateway"""

    def __init__(
        self,
        api_gateway_url: str = "http://localhost:8080",
        wso2_token_url: str = "https://localhost:9443/oauth2/token",  # noqa: S107
        client_id: str = "L2rvop0o4DfJsqpqsh44cUgVn_ga",
        client_secret: str = "VhNFUK083Q2iUsu8GCWfcJTVCX8a",  # noqa: S107
    ):
        """
        Initialize the API client

        Args:
            api_gateway_url: Base URL of the API Gateway
            wso2_token_url: WSO2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
        """
        self.api_gateway_url = api_gateway_url.rstrip("/")
        self.wso2_token_url = wso2_token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens = {}  # Cache tokens by scope

    def get_access_token(self, scope: str) -> str | None:
        """
        Get an OAuth2 access token with the specified scope

        Args:
            scope: Required scope (e.g., "score:write")

        Returns:
            Access token string or None if failed
        """
        # Check if we have a cached token for this scope
        if scope in self.tokens:
            # TODO: Add token expiration check
            return self.tokens[scope]

        try:
            response = requests.post(
                self.wso2_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=False,  # Disable SSL verification for self-signed certs  # noqa: S501
            )

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                self.tokens[scope] = access_token
                return access_token
            print(f"Failed to get token: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        except Exception as e:
            print(f"Error getting access token: {e}")
            return None

    def check_health(self) -> bool:
        """
        Check if the API Gateway is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.api_gateway_url}/health")
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def submit_score(
        self,
        score: int,
        multiplier: str,
        player_id: str | None = None,
        game_id: str | None = None,
    ) -> dict | None:
        """
        Submit a dart score

        Args:
            score: Score value (0-60)
            multiplier: "SINGLE", "DOUBLE", or "TRIPLE"
            player_id: Optional player identifier
            game_id: Optional game identifier

        Returns:
            Response data or None if failed
        """
        token = self.get_access_token("score:write")
        if not token:
            print("Failed to get access token")
            return None

        try:
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/scores",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "score": score,
                    "multiplier": multiplier,
                    "player_id": player_id,
                    "game_id": game_id,
                },
            )

            if response.status_code in [200, 201]:
                return response.json()
            print(f"Failed to submit score: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        except Exception as e:
            print(f"Error submitting score: {e}")
            return None

    def create_game(
        self,
        game_type: str,
        players: list,
        double_out: bool = False,
    ) -> dict | None:
        """
        Create a new game

        Args:
            game_type: Game type ("301", "401", "501", "cricket")
            players: List of player names
            double_out: Whether double-out rule is enabled

        Returns:
            Response data or None if failed
        """
        token = self.get_access_token("game:write")
        if not token:
            print("Failed to get access token")
            return None

        try:
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/games",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "game_type": game_type,
                    "players": players,
                    "double_out": double_out,
                },
            )

            if response.status_code in [200, 201]:
                return response.json()
            print(f"Failed to create game: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        except Exception as e:
            print(f"Error creating game: {e}")
            return None

    def add_player(self, name: str) -> dict | None:
        """
        Add a new player

        Args:
            name: Player name

        Returns:
            Response data or None if failed
        """
        token = self.get_access_token("player:write")
        if not token:
            print("Failed to get access token")
            return None

        try:
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/players",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"name": name},
            )

            if response.status_code in [200, 201]:
                return response.json()
            print(f"Failed to add player: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        except Exception as e:
            print(f"Error adding player: {e}")
            return None


def main():
    """Example usage of the Darts API Client"""

    print("=" * 60)
    print("Darts API Gateway Client Example")
    print("=" * 60)
    print()

    # Initialize client
    client = DartsAPIClient()

    # 1. Health Check
    print("1. Checking API Gateway health...")
    if client.check_health():
        print("   ✓ API Gateway is healthy")
    else:
        print("   ✗ API Gateway is not responding")
        return
    print()

    # 2. Create a game
    print("2. Creating a new game...")
    game_result = client.create_game(
        game_type="301",
        players=["Alice", "Bob", "Charlie"],
        double_out=False,
    )
    if game_result:
        print("   ✓ Game created successfully")
        print(f"   Response: {json.dumps(game_result, indent=2)}")
    else:
        print("   ✗ Failed to create game")
    print()

    # 3. Add a player
    print("3. Adding a new player...")
    player_result = client.add_player("David")
    if player_result:
        print("   ✓ Player added successfully")
        print(f"   Response: {json.dumps(player_result, indent=2)}")
    else:
        print("   ✗ Failed to add player")
    print()

    # 4. Submit scores
    print("4. Submitting dart scores...")

    scores = [
        {"score": 20, "multiplier": "TRIPLE", "player_id": "alice"},
        {"score": 19, "multiplier": "TRIPLE", "player_id": "bob"},
        {"score": 18, "multiplier": "TRIPLE", "player_id": "charlie"},
        {"score": 25, "multiplier": "DOUBLE", "player_id": "alice"},
    ]

    for i, score_data in enumerate(scores, 1):
        result = client.submit_score(
            score=score_data["score"],
            multiplier=score_data["multiplier"],
            player_id=score_data["player_id"],
            game_id="game-001",
        )
        if result:
            print(f"   ✓ Score {i} submitted: {score_data['score']} x {score_data['multiplier']}")
        else:
            print(f"   ✗ Failed to submit score {i}")
    print()

    # 5. Summary
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  - View the game board at http://localhost:5000")
    print("  - Check RabbitMQ messages at http://localhost:15672")
    print("  - Review API Gateway logs: docker logs darts-api-gateway")
    print()


if __name__ == "__main__":
    main()
