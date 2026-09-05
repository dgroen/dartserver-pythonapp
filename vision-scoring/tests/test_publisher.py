from unittest.mock import MagicMock, patch

from vision_scoring.board_model import Ring, ScoreResult
from vision_scoring.publisher import PublisherConfig, VisionThrowPublisher


def _config() -> PublisherConfig:
    return PublisherConfig(
        client_id="test-client",
        client_secret="test-secret",
        token_url="https://wso2is/oauth2/token",
        gateway_url="https://gateway",
    )


def _token_response(expires_in: int = 3600) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"access_token": "abc123", "expires_in": expires_in}
    return response


def _throw_response(status_code: int = 201) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = ""
    return response


def _result(confidence: float = 0.9) -> ScoreResult:
    return ScoreResult(
        score=20, multiplier="TRIPLE", ring=Ring.TRIPLE, segment=20, confidence=confidence
    )


def test_publish_succeeds_with_valid_token():
    with patch("requests.post", side_effect=[_token_response(), _throw_response(201)]) as mock_post:
        publisher = VisionThrowPublisher(_config())
        success = publisher.publish(_result(), session_id="s1", board_id="board1")

    assert success is True
    token_call, throw_call = mock_post.call_args_list
    assert throw_call.kwargs["json"]["score"] == 20
    assert throw_call.kwargs["json"]["multiplier"] == "TRIPLE"
    assert throw_call.kwargs["json"]["sessionId"] == "s1"
    assert throw_call.kwargs["headers"]["Authorization"] == "Bearer abc123"


def test_publish_reuses_token_across_calls():
    with patch(
        "requests.post", side_effect=[_token_response(), _throw_response(201), _throw_response(201)]
    ) as mock_post:
        publisher = VisionThrowPublisher(_config())
        publisher.publish(_result())
        publisher.publish(_result())

    # Only one token request should have been made across two publishes.
    token_requests = [
        c for c in mock_post.call_args_list if "grant_type" in c.kwargs.get("data", {})
    ]
    assert len(token_requests) == 1


def test_publish_refreshes_token_on_401():
    with patch(
        "requests.post",
        side_effect=[
            _token_response(),
            _throw_response(401),
            _token_response(),
            _throw_response(201),
        ],
    ):
        publisher = VisionThrowPublisher(_config())
        success = publisher.publish(_result())

    assert success is True


def test_publish_returns_false_when_token_request_fails():
    failing_token_response = MagicMock(status_code=401, text="unauthorized")
    with patch("requests.post", return_value=failing_token_response):
        publisher = VisionThrowPublisher(_config())
        success = publisher.publish(_result(), max_retries=1)

    assert success is False


def test_publish_returns_false_on_persistent_server_error():
    with patch("requests.post", side_effect=[_token_response(), _throw_response(500)]):
        publisher = VisionThrowPublisher(_config())
        success = publisher.publish(_result())

    assert success is False


def test_normalizes_miss_before_publishing():
    miss_result = ScoreResult(
        score=0, multiplier="MISS", ring=Ring.MISS, segment=None, confidence=1.0
    )
    with patch("requests.post", side_effect=[_token_response(), _throw_response(201)]) as mock_post:
        publisher = VisionThrowPublisher(_config())
        publisher.publish(miss_result)

    _token_call, throw_call = mock_post.call_args_list
    assert throw_call.kwargs["json"]["score"] == 0
    assert throw_call.kwargs["json"]["multiplier"] == "SINGLE"
