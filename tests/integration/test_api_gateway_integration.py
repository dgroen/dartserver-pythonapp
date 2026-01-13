"""
Integration tests for API Gateway
Tests multi-game flows, concurrent games, and complete game scenarios
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from src.api_gateway.app import app as gateway_app


@pytest.fixture
def client():
    """Create test client for API Gateway"""
    gateway_app.config["TESTING"] = True

    # Provide a thin thread-safe wrapper around Flask's test_client.
    # Concurrent tests call `client.post` from multiple threads; creating
    # a fresh `test_client()` per request avoids leaking request contexts
    # across threads which causes "Working outside of request context".
    class ThreadSafeTestClient:
        def __init__(self, app):
            self._app = app

        def post(self, *args, **kwargs):
            with self._app.test_client() as c:
                return c.post(*args, **kwargs)

        def get(self, *args, **kwargs):
            with self._app.test_client() as c:
                return c.get(*args, **kwargs)

        def put(self, *args, **kwargs):
            with self._app.test_client() as c:
                return c.put(*args, **kwargs)

        def delete(self, *args, **kwargs):
            with self._app.test_client() as c:
                return c.delete(*args, **kwargs)

        def patch(self, *args, **kwargs):
            with self._app.test_client() as c:
                return c.patch(*args, **kwargs)

        def open(self, *args, **kwargs):
            with self._app.test_client() as c:
                return c.open(*args, **kwargs)

    return ThreadSafeTestClient(gateway_app)


@pytest.fixture
def mock_jwt_validation():
    """Mock JWT validation to return valid claims"""
    with patch("src.api_gateway.app.validate_jwt_token") as mock:
        mock.return_value = {
            "sub": "test-user",
            "client_id": "dartboard-001",
            "scope": "dartboard:write score:write game:write game:control player:write",
        }
        yield mock


@pytest.fixture
def auth_headers():
    """Return valid authorization headers"""
    return {"Authorization": "Bearer test-token-123"}


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ publisher to track messages"""
    messages = []

    def publish_side_effect(routing_key, message):
        messages.append({"routing_key": routing_key, "message": message})
        return True

    with patch("src.api_gateway.app.rabbitmq_publisher.publish") as mock:
        mock.side_effect = publish_side_effect
        yield {"mock": mock, "messages": messages}


class TestCompleteGameFlow:
    """Test complete game flow from creation to finish"""

    def test_complete_301_game_flow(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test complete 301 game flow with multiple players"""
        messages = mock_rabbitmq["messages"]

        # Step 1: Create game
        response = client.post(
            "/api/v1/games",
            json={
                "game_type": "301",
                "players": ["Alice", "Bob"],
                "double_out": False,
            },
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 201
        assert len(messages) == 1
        assert messages[0]["routing_key"] == "darts.games.create"
        assert messages[0]["message"]["action"] == "new_game"

        # Step 2: Player 1 throws (simulate dartboard)
        response = client.post(
            "/api/v1/dartboard/throw",
            json={"masterPin": 4, "slavePin": 13, "boardType": "carromco"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 201
        assert len(messages) == 2
        assert messages[1]["routing_key"] == "darts.dartboard.throw"

        # Step 3: Player 1 throws again
        response = client.post(
            "/api/v1/dartboard/throw",
            json={"masterPin": 5, "slavePin": 10, "boardType": "carromco"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 201

        # Step 4: End turn early
        response = client.post(
            "/api/v1/game/actions/end-turn",
            json={"game_id": "game-123"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 200
        end_turn_msg = next((m for m in messages if m["message"].get("action") == "end_turn"), None)
        assert end_turn_msg["routing_key"] == "darts.game.action"

        # Step 5: Continue game
        response = client.post(
            "/api/v1/game/actions/continue",
            json={"game_id": "game-123"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify message sequence
        assert len(messages) >= 5
        actions = [m["message"].get("action") for m in messages]
        assert "new_game" in actions
        assert "end_turn" in actions
        assert "continue" in actions

    def test_game_pause_resume_flow(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test pausing and resuming a game"""
        messages = mock_rabbitmq["messages"]

        # Create game
        client.post(
            "/api/v1/games",
            json={
                "game_type": "501",
                "players": ["Player1", "Player2", "Player3"],
            },
            headers=auth_headers,
            content_type="application/json",
        )

        # Pause game
        response = client.post(
            "/api/v1/game/actions/pause",
            json={"game_id": "game-456"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 200

        # Continue (resume) game
        response = client.post(
            "/api/v1/game/actions/continue",
            json={"game_id": "game-456"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify pause and continue actions
        actions = [m["message"].get("action") for m in messages]
        assert "pause" in actions
        assert "continue" in actions


class TestMultiGameScenarios:
    """Test multiple concurrent games"""

    def test_two_simultaneous_games(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test two games running simultaneously"""
        messages = mock_rabbitmq["messages"]

        # Create first game
        response1 = client.post(
            "/api/v1/games",
            json={
                "game_type": "301",
                "players": ["Alice", "Bob"],
            },
            headers=auth_headers,
            content_type="application/json",
        )
        assert response1.status_code == 201

        # Create second game
        response2 = client.post(
            "/api/v1/games",
            json={
                "game_type": "cricket",
                "players": ["Charlie", "Dave"],
            },
            headers=auth_headers,
            content_type="application/json",
        )
        assert response2.status_code == 201

        # Submit scores for both games
        client.post(
            "/api/v1/scores",
            json={"score": 20, "multiplier": "TRIPLE", "game_id": "game-1"},
            headers=auth_headers,
            content_type="application/json",
        )

        client.post(
            "/api/v1/scores",
            json={"score": 15, "multiplier": "DOUBLE", "game_id": "game-2"},
            headers=auth_headers,
            content_type="application/json",
        )

        # Verify both games created
        game_creates = [m for m in messages if m["message"].get("action") == "new_game"]
        assert len(game_creates) == 2

        # Verify scores submitted
        score_submits = [m for m in messages if m["routing_key"] == "darts.scores.api"]
        assert len(score_submits) == 2

    def test_concurrent_game_creation(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test creating multiple games concurrently"""

        def create_game(game_num):
            return client.post(
                "/api/v1/games",
                json={
                    "game_type": "301",
                    "players": [f"Player{game_num}A", f"Player{game_num}B"],
                },
                headers=auth_headers,
                content_type="application/json",
            )

        # Create 5 games concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_game, i) for i in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 201 for r in responses)

        # Should have 5 game creation messages
        game_creates = [
            m for m in mock_rabbitmq["messages"] if m["message"].get("action") == "new_game"
        ]
        assert len(game_creates) == 5


class TestDartboardSimulation:
    """Test dartboard hardware simulation"""

    def test_simulate_complete_game_dartboard(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Simulate a complete game using dartboard throws"""
        messages = mock_rabbitmq["messages"]

        # Create game
        client.post(
            "/api/v1/games",
            json={
                "game_type": "301",
                "players": ["Player 1"],
            },
            headers=auth_headers,
            content_type="application/json",
        )

        # Simulate dartboard throws (triple 20, triple 20, triple 20)
        throws = [
            {"masterPin": 4, "slavePin": 13, "boardType": "carromco"},  # T20
            {"masterPin": 4, "slavePin": 13, "boardType": "carromco"},  # T20
            {"masterPin": 4, "slavePin": 13, "boardType": "carromco"},  # T20
        ]

        for throw in throws:
            response = client.post(
                "/api/v1/dartboard/throw",
                json=throw,
                headers=auth_headers,
                content_type="application/json",
            )
            assert response.status_code == 201

        # End turn
        response = client.post(
            "/api/v1/game/actions/end-turn",
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify all throws were submitted
        throw_messages = [m for m in messages if m["routing_key"] == "darts.dartboard.throw"]
        assert len(throw_messages) == 3

    def test_multiple_dartboard_clients(
        self,
        client,
        mock_rabbitmq,
        auth_headers,
    ):
        """Test multiple dartboard clients submitting throws"""

        # Mock different client IDs for different dartboards
        def mock_validation_factory(client_id):
            def mock_validation(token):
                return {
                    "sub": f"dartboard-{client_id}",
                    "client_id": client_id,
                    "scope": "dartboard:write",
                }

            return mock_validation

        messages = mock_rabbitmq["messages"]

        # Simulate 3 different dartboards
        for i in range(1, 4):
            with patch(
                "src.api_gateway.app.validate_jwt_token",
                side_effect=mock_validation_factory(f"dartboard-00{i}"),
            ):
                response = client.post(
                    "/api/v1/dartboard/throw",
                    json={
                        "masterPin": i,
                        "slavePin": 10 + i,
                        "boardType": "carromco",
                    },
                    headers=auth_headers,
                    content_type="application/json",
                )
                assert response.status_code == 201

        # Verify throws from different clients
        throw_messages = [m for m in messages if m["routing_key"] == "darts.dartboard.throw"]
        assert len(throw_messages) == 3

        # Verify different client IDs
        client_ids = [m["message"]["client_id"] for m in throw_messages]
        assert "dartboard-001" in client_ids
        assert "dartboard-002" in client_ids
        assert "dartboard-003" in client_ids


class TestManualScoreEntry:
    """Test manual score entry for testing"""

    def test_manual_score_entry_multiple_players(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test manually entering scores for multiple players"""

        # Create game
        client.post(
            "/api/v1/games",
            json={
                "game_type": "cricket",
                "players": ["Player1", "Player2", "Player3"],
            },
            headers=auth_headers,
            content_type="application/json",
        )

        # Manually enter scores for different players
        scores = [
            {"score": 20, "multiplier": "TRIPLE", "player_id": 1},
            {"score": 19, "multiplier": "DOUBLE", "player_id": 2},
            {"score": 18, "multiplier": "SINGLE", "player_id": 3},
        ]

        for score in scores:
            response = client.post(
                "/api/v1/scores",
                json=score,
                headers=auth_headers,
                content_type="application/json",
            )
            assert response.status_code == 201

        # Verify all scores submitted
        messages = mock_rabbitmq["messages"]
        score_messages = [m for m in messages if m["routing_key"] == "darts.scores.api"]
        assert len(score_messages) == 3


class TestButtonActions:
    """Test all button actions available in the UI"""

    def test_all_button_actions(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test all game control button actions"""
        messages = mock_rabbitmq["messages"]

        # Create game
        client.post(
            "/api/v1/games",
            json={"game_type": "301", "players": ["Player1", "Player2"]},
            headers=auth_headers,
            content_type="application/json",
        )

        # Test all button actions
        actions = [
            ("/api/v1/game/actions/end-turn", "end_turn"),
            ("/api/v1/game/actions/pause", "pause"),
            ("/api/v1/game/actions/continue", "continue"),
        ]

        for endpoint, expected_action in actions:
            response = client.post(
                endpoint,
                json={"game_id": "test-game"},
                headers=auth_headers,
                content_type="application/json",
            )
            assert response.status_code == 200

            # Verify action was published
            action_msg = next(
                (m for m in reversed(messages) if m["message"].get("action") == expected_action),
                None,
            )
            assert action_msg is not None
            assert action_msg["routing_key"] == "darts.game.action"


class TestPerformanceAndLoad:
    """Test performance with high load"""

    def test_rapid_score_submission(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test rapid score submissions"""
        start_time = time.time()

        # Submit 100 scores rapidly
        for i in range(100):
            response = client.post(
                "/api/v1/scores",
                json={"score": i % 21, "multiplier": "SINGLE"},
                headers=auth_headers,
                content_type="application/json",
            )
            assert response.status_code == 201

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

        # All scores should be published
        messages = mock_rabbitmq["messages"]
        score_messages = [m for m in messages if m["routing_key"] == "darts.scores.api"]
        assert len(score_messages) == 100

    def test_concurrent_throw_submissions(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test concurrent throw submissions from multiple dartboards"""

        def submit_throw(pin_offset):
            return client.post(
                "/api/v1/dartboard/throw",
                json={
                    "masterPin": 4 + pin_offset,
                    "slavePin": 13 + pin_offset,
                    "boardType": "carromco",
                },
                headers=auth_headers,
                content_type="application/json",
            )

        # Submit 20 throws concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_throw, i % 5) for i in range(20)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 201 for r in responses)

        # All throws should be published
        messages = mock_rabbitmq["messages"]
        throw_messages = [m for m in messages if m["routing_key"] == "darts.dartboard.throw"]
        assert len(throw_messages) == 20
