import pytest
from vision_scoring.board_model import Ring, ScoreResult
from vision_scoring.confirm_state import ConfirmGate
from vision_scoring.confirm_ui import create_app


@pytest.fixture()
def client():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    app = create_app(gate)
    app.config["GATE"] = gate  # convenience handle for tests
    with app.test_client() as client:
        client.gate = gate
        yield client


def _submit(client, confidence: float):
    result = ScoreResult(
        score=20, multiplier="TRIPLE", ring=Ring.TRIPLE, segment=20, confidence=confidence
    )
    return client.gate.submit(result)


def test_list_pending_returns_awaiting_and_counting_down(client):
    _submit(client, 0.9)
    _submit(client, 0.1)

    response = client.get("/api/throws/pending")
    assert response.status_code == 200
    statuses = {t["status"] for t in response.get_json()}
    assert statuses == {"COUNTING_DOWN", "AWAITING_CONFIRMATION"}


def test_confirm_endpoint_accepts_a_throw(client):
    pending = _submit(client, 0.1)
    response = client.post(f"/api/throws/{pending.throw_id}/confirm")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ACCEPTED"


def test_confirm_unknown_throw_returns_404(client):
    response = client.post("/api/throws/does-not-exist/confirm")
    assert response.status_code == 404


def test_correct_endpoint_overrides_the_result(client):
    pending = _submit(client, 0.1)
    response = client.post(
        f"/api/throws/{pending.throw_id}/correct",
        json={"score": 5, "multiplier": "SINGLE", "ring": "SINGLE", "segment": 5},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "CORRECTED"
    assert body["final_result"]["score"] == 5
    assert body["final_result"]["multiplier"] == "SINGLE"


def test_correct_endpoint_rejects_invalid_payload(client):
    pending = _submit(client, 0.1)
    response = client.post(f"/api/throws/{pending.throw_id}/correct", json={"multiplier": "SINGLE"})
    assert response.status_code == 400


def test_cancel_endpoint_removes_throw_from_pending(client):
    pending = _submit(client, 0.9)
    client.post(f"/api/throws/{pending.throw_id}/cancel")

    response = client.get("/api/throws/pending")
    assert response.get_json() == []
