#!/usr/bin/env python3
"""Quick test to verify RabbitMQ consumer is working with valid pin mappings"""

import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get token
print("Getting OAuth token...")
token_response = requests.post(
    "https://localhost:9443/oauth2/token",
    auth=("local_client_id", "local_client_secret"),
    data={"grant_type": "client_credentials", "scope": "dartboard:write"},
    verify=False,  # noqa: S501 - Disable SSL verification for testing
    timeout=10,
)
token = token_response.json()["access_token"]
print("✓ Got token")

# Send throw with VALID pins (from database: master=15, slave=13 = SINGLE 12)
print("\nSending throw with valid pins (15, 13) = SINGLE 12...")
response = requests.post(
    "http://localhost:8080/api/v1/dartboard/throw",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
    json={
        "masterPin": 15,
        "slavePin": 13,
        "boardType": "carromco",
    },
    verify=False,  # noqa: S501 - Disable SSL verification for testing
    timeout=10,
)

if response.status_code == 201:
    print("✓ Throw submitted successfully!")
    print(f"  Response: {response.json()}")
else:
    print(f"✗ Failed: {response.status_code}")
    print(f"  {response.text}")

print("\nNow check the Flask logs:")
print("docker logs darts-app 2>&1 | tail -20")
