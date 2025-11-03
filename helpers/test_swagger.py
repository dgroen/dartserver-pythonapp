#!/usr/bin/env python3
"""Test script to verify Swagger API documentation is working"""

import time

import requests

# Wait for server to be ready
print("Waiting for server to start...")
time.sleep(3)

base_url = "http://localhost:5000"

# Test 1: Check if Swagger UI is accessible
print("\n1. Testing Swagger UI endpoint...")
try:
    response = requests.get(f"{base_url}/api/docs/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Swagger UI is accessible")
    else:
        print("   ✗ Failed to access Swagger UI")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Check if API spec is available
print("\n2. Testing API specification endpoint...")
try:
    response = requests.get(f"{base_url}/apispec.json")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        spec = response.json()
        print("   ✓ API spec available")
        print(f"   Title: {spec.get('info', {}).get('title')}")
        print(f"   Version: {spec.get('info', {}).get('version')}")
        print(f"   Endpoints: {len(spec.get('paths', {}))}")
    else:
        print("   ✗ Failed to get API spec")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Test GET /api/game/state
print("\n3. Testing GET /api/game/state...")
try:
    response = requests.get(f"{base_url}/api/game/state")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   ✓ Game state retrieved")
        print(f"   Game type: {data.get('game_type')}")
        print(f"   Players: {len(data.get('players', []))}")
    else:
        print("   ✗ Failed to get game state")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Test POST /api/game/new
print("\n4. Testing POST /api/game/new...")
try:
    payload = {
        "game_type": "301",
        "players": ["Alice", "Bob"],
        "double_out": False,
    }
    response = requests.post(f"{base_url}/api/game/new", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   ✓ New game started")
        print(f"   Message: {data.get('message')}")
    else:
        print("   ✗ Failed to start new game")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Test GET /api/players
print("\n5. Testing GET /api/players...")
try:
    response = requests.get(f"{base_url}/api/players")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        players = response.json()
        print("   ✓ Players retrieved")
        print(f"   Number of players: {len(players)}")
        for player in players:
            print(f"   - {player.get('name')} (ID: {player.get('id')})")
    else:
        print("   ✗ Failed to get players")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 6: Test POST /api/score
print("\n6. Testing POST /api/score...")
try:
    payload = {
        "score": 20,
        "multiplier": "TRIPLE",
    }
    response = requests.post(f"{base_url}/api/score", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   ✓ Score submitted")
        print(f"   Message: {data.get('message')}")
    else:
        print("   ✗ Failed to submit score")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
print("=" * 50)
print(f"\nSwagger UI available at: {base_url}/api/docs/")
print(f"API Specification at: {base_url}/apispec.json")
