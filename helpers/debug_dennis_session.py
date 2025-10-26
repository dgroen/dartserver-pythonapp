#!/usr/bin/env python3
"""
Diagnostic script to check Dennis's session and authentication state
"""
import os

os.environ["FLASK_ENV"] = "development"

from src.app.app import app
from src.core.database_service import DatabaseService

print("=" * 60)
print("DEBUGGING DENNIS SESSION & AUTHENTICATION")
print("=" * 60)

# Create app context
with app.app_context():
    # 1. Check if Dennis exists in database
    print("\n1️⃣ CHECK DENNIS IN DATABASE:")
    db_service = DatabaseService()
    session = db_service.db_manager.get_session()

    from src.core.database_models import Player

    dennis = session.query(Player).filter(Player.username == "Dennis").first()
    if dennis:
        print(f"   ✅ Found: ID={dennis.id}, name={dennis.name}, username={dennis.username}")
    else:
        print("   ❌ Not found!")
    session.close()

    # 2. Check his games
    print("\n2️⃣ CHECK DENNIS'S GAMES:")
    games = db_service.get_player_game_history(player_id=11, limit=50)
    print(f"   Found {len(games)} games")

    # 3. Test API endpoint WITHOUT authentication
    print("\n3️⃣ TEST API (WITHOUT ACCESS TOKEN):")
    client = app.test_client()

    with client:
        with client.session_transaction() as sess:
            sess["player_id"] = 11
            # NOTE: No access_token set

        response = client.get("/api/player/history")
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            print(f"   ❌ Redirected to: {response.location}")
            print("   REASON: No access_token in session")
        else:
            data = response.get_json()
            print(f"   ✅ Got {len(data.get('games', []))} games")

    # 4. Test API endpoint WITH mock authentication
    print("\n4️⃣ TEST API (WITH MOCK ACCESS TOKEN):")

    with client:
        with client.session_transaction() as sess:
            sess["player_id"] = 11
            sess["access_token"] = "mock_token"  # Dummy token
            sess["user_info"] = {"username": "Dennis", "sub": "11"}

        response = client.get("/api/player/history")
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            print("   Redirected (token validation failed)")
        else:
            data = response.get_json()
            if data.get("success"):
                print(f"   ✅ Success! Got {len(data.get('games', []))} games")
            else:
                print(f"   ❌ Error: {data.get('error')}")

    # 5. Check AUTH_DISABLED setting
    print("\n5️⃣ CHECK AUTH SETTING:")
    from src.core.auth import AUTH_DISABLED

    print(f"   AUTH_DISABLED: {AUTH_DISABLED}")

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print("If status in step 3 is 302 (redirect), then Dennis needs:")
    print("  1. To be logged in with a valid OAuth2 access_token")
    print("  2. The token to be stored in his session")
    print("\nTo enable access_token free testing, set in .env:")
    print("  AUTH_DISABLED=True")
    print("\nTo complete OAuth2 login, Dennis must:")
    print("  1. Visit /login (redirects to WSO2)")
    print("  2. Authenticate at WSO2")
    print("  3. Get redirected back to /callback")
    print("  4. Callback exchanges code for access_token")
    print("  5. access_token is stored in session")
    print("\n" + "=" * 60)
