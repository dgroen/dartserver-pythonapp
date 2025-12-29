#!/usr/bin/env python3
"""
Dartboard Client Simulator

This script simulates a dartboard hardware client for testing the API Gateway.
It can simulate:
- Single throws
- Complete games
- Multiple concurrent dartboards
- Token management and renewal

Usage:
    python dartboard_simulator.py --client-id CLIENT_ID --client-secret SECRET
    python dartboard_simulator.py --simulate-game
    python dartboard_simulator.py --concurrent-boards 3
"""

import argparse
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests


class DartboardClient:
    """Simulates a dartboard hardware client with OAuth2 authentication"""

    def __init__(self, client_id, client_secret, token_url, gateway_url, board_type="carromco"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.gateway_url = gateway_url
        self.board_type = board_type
        self.access_token = None
        self.token_expires_at = None
        self.throw_count = 0
        self.success_count = 0
        self.error_count = 0

    def get_access_token(self):
        """Obtain a new access token using client credentials"""
        print(f"[{self.client_id}] Obtaining access token...")
        try:
            response = requests.post(
                self.token_url,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials", "scope": "dartboard:write"},
                verify=False,  # Disable SSL verification for testing
                timeout=10,
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data["expires_in"]
                # Refresh token 60 seconds before expiration
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                print(
                    f"[{self.client_id}] ✓ Token obtained (expires in {expires_in}s)",
                )
                return True
            print(f"[{self.client_id}] ✗ Failed to obtain token: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        except Exception as e:
            print(f"[{self.client_id}] ✗ Error obtaining token: {e}")
            return False

    def ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            return self.get_access_token()
        return True

    def submit_throw(self, master_pin, slave_pin, max_retries=3):
        """Submit a dartboard throw"""
        self.throw_count += 1

        for attempt in range(max_retries):
            if not self.ensure_valid_token():
                print(f"[{self.client_id}] Failed to obtain valid token")
                time.sleep(1)
                continue

            try:
                response = requests.post(
                    f"{self.gateway_url}/api/v1/dartboard/throw",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "masterPin": master_pin,
                        "slavePin": slave_pin,
                        "boardType": self.board_type,
                    },
                    verify=False,  # Disable SSL verification for testing
                    timeout=10,
                )

                if response.status_code == 201:
                    result = response.json()
                    print(
                        f"[{self.client_id}] ✓ Throw {self.throw_count}: "
                        f"pins({master_pin},{slave_pin}) submitted successfully",
                    )
                    self.success_count += 1
                    return True
                if response.status_code == 401:
                    # Token expired, retry with new token
                    print(f"[{self.client_id}] Token expired, refreshing...")
                    self.access_token = None
                    continue
                print(
                    f"[{self.client_id}] ✗ Failed to submit throw: "
                    f"{response.status_code} {response.text}",
                )
                self.error_count += 1
                return False
            except Exception as e:
                print(f"[{self.client_id}] ✗ Error submitting throw: {e}")
                self.error_count += 1
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

        print(f"[{self.client_id}] Max retries exceeded")
        return False

    def print_stats(self):
        """Print statistics"""
        success_rate = (
            (self.success_count / self.throw_count * 100) if self.throw_count > 0 else 0
        )
        print(f"\n[{self.client_id}] Statistics:")
        print(f"  Total throws: {self.throw_count}")
        print(f"  Successful: {self.success_count}")
        print(f"  Failed: {self.error_count}")
        print(f"  Success rate: {success_rate:.1f}%")


# Predefined pin combinations for testing (examples)
SAMPLE_THROWS = [
    (4, 13),  # Triple 20
    (5, 10),  # Double 15
    (7, 13),  # Double Bull
    (3, 14),  # Single 19
    (6, 11),  # Single 5
]


def simulate_single_throw(client):
    """Simulate a single random throw"""
    master_pin, slave_pin = random.choice(SAMPLE_THROWS)
    client.submit_throw(master_pin, slave_pin)


def simulate_game(client, num_rounds=10):
    """Simulate a complete game with multiple rounds"""
    print(f"\n[{client.client_id}] Starting game simulation ({num_rounds} rounds)...")

    for round_num in range(1, num_rounds + 1):
        print(f"\n[{client.client_id}] --- Round {round_num} ---")

        # Simulate 3 throws per round
        for throw_num in range(1, 4):
            master_pin, slave_pin = random.choice(SAMPLE_THROWS)
            success = client.submit_throw(master_pin, slave_pin)

            if not success:
                print(f"[{client.client_id}] Failed throw in round {round_num}")

            # Small delay between throws
            time.sleep(0.5)

        # Delay between rounds
        time.sleep(1)

    client.print_stats()


def simulate_concurrent_boards(
    num_boards,
    client_id_prefix,
    client_secret,
    token_url,
    gateway_url,
):
    """Simulate multiple concurrent dartboards"""
    print(f"\nSimulating {num_boards} concurrent dartboards...")

    def run_board(board_num):
        client_id = f"{client_id_prefix}_{board_num:03d}"
        client = DartboardClient(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            gateway_url=gateway_url,
        )

        # Each board simulates a short game
        for _ in range(5):
            master_pin, slave_pin = random.choice(SAMPLE_THROWS)
            client.submit_throw(master_pin, slave_pin)
            time.sleep(random.uniform(0.1, 0.5))

        client.print_stats()
        return client

    with ThreadPoolExecutor(max_workers=num_boards) as executor:
        futures = [executor.submit(run_board, i) for i in range(1, num_boards + 1)]
        clients = [f.result() for f in futures]

    # Print summary
    total_throws = sum(c.throw_count for c in clients)
    total_success = sum(c.success_count for c in clients)
    print(f"\n=== Summary ===")
    print(f"Total throws: {total_throws}")
    print(f"Total successful: {total_success}")
    print(f"Overall success rate: {total_success/total_throws*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Dartboard Client Simulator")

    # Connection settings
    parser.add_argument(
        "--client-id",
        default="dartboard_test_client",
        help="OAuth2 client ID",
    )
    parser.add_argument(
        "--client-secret",
        default="test_secret",
        help="OAuth2 client secret",
    )
    parser.add_argument(
        "--token-url",
        default="http://localhost:9443/oauth2/token",
        help="OAuth2 token endpoint URL",
    )
    parser.add_argument(
        "--gateway-url",
        default="http://localhost:8080",
        help="API Gateway base URL",
    )
    parser.add_argument(
        "--board-type",
        default="carromco",
        help="Dartboard type",
    )

    # Simulation modes
    parser.add_argument(
        "--single-throw",
        action="store_true",
        help="Simulate a single throw",
    )
    parser.add_argument(
        "--simulate-game",
        action="store_true",
        help="Simulate a complete game",
    )
    parser.add_argument(
        "--num-rounds",
        type=int,
        default=10,
        help="Number of rounds in simulated game",
    )
    parser.add_argument(
        "--concurrent-boards",
        type=int,
        help="Simulate multiple concurrent dartboards",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously (Ctrl+C to stop)",
    )

    args = parser.parse_args()

    # Disable SSL warnings
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("=" * 60)
    print("Dartboard Client Simulator")
    print("=" * 60)
    print(f"Gateway URL: {args.gateway_url}")
    print(f"Token URL: {args.token_url}")
    print(f"Client ID: {args.client_id}")
    print("=" * 60)

    # Create client
    client = DartboardClient(
        client_id=args.client_id,
        client_secret=args.client_secret,
        token_url=args.token_url,
        gateway_url=args.gateway_url,
        board_type=args.board_type,
    )

    try:
        if args.concurrent_boards:
            simulate_concurrent_boards(
                num_boards=args.concurrent_boards,
                client_id_prefix=args.client_id,
                client_secret=args.client_secret,
                token_url=args.token_url,
                gateway_url=args.gateway_url,
            )
        elif args.simulate_game:
            simulate_game(client, num_rounds=args.num_rounds)
        elif args.continuous:
            print("\nRunning continuously (Ctrl+C to stop)...")
            while True:
                simulate_single_throw(client)
                time.sleep(2)
        else:
            # Default: single throw
            simulate_single_throw(client)
            client.print_stats()

    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user")
        client.print_stats()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
