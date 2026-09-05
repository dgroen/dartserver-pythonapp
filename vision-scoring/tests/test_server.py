import io

import cv2
import numpy as np
import pytest
from vision_scoring.config import VisionScoringConfig
from vision_scoring.server import create_app


def _blank_frame_bytes(size: int = 200, value: int = 200) -> bytes:
    frame = np.full((size, size, 3), value, dtype=np.uint8)
    ok, buf = cv2.imencode(".png", frame)
    assert ok
    return buf.tobytes()


def _dart_frame_bytes(center_xy: tuple[int, int], size: int = 200) -> bytes:
    frame = np.full((size, size, 3), 200, dtype=np.uint8)
    cv2.circle(frame, center_xy, 6, (0, 0, 0), thickness=-1)
    ok, buf = cv2.imencode(".png", frame)
    assert ok
    return buf.tobytes()


@pytest.fixture()
def client(tmp_path):
    config = VisionScoringConfig(calibration_dir=tmp_path, confidence_threshold=0.0)
    app = create_app(config)
    with app.test_client() as client:
        yield client


def _calibrate(client, board_id="board1"):
    board_mm = [(-90.0, 0.0), (90.0, 0.0), (0.0, 90.0), (0.0, -90.0)]
    pixel_px = [(10.0, 100.0), (190.0, 100.0), (100.0, 10.0), (100.0, 190.0)]
    return client.post(
        f"/internal/vision/{board_id}/calibration",
        json={"reference_points_px": pixel_px, "reference_points_mm": board_mm},
    )


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_calibration_round_trip(client):
    response = _calibrate(client)
    assert response.status_code == 201

    get_response = client.get("/internal/vision/board1/calibration")
    assert get_response.get_json()["calibrated"] is True


def test_calibration_rejects_bad_payload(client):
    response = client.post(
        "/internal/vision/board1/calibration",
        json={"reference_points_px": [(0, 0)]},
    )
    assert response.status_code == 400


def test_frame_before_calibration_returns_409(client):
    response = client.post(
        "/internal/vision/board1/frame",
        data={"frame": (io.BytesIO(_blank_frame_bytes()), "frame.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409


def test_reference_frame_before_calibration_returns_409(client):
    response = client.post(
        "/internal/vision/board1/reference-frame",
        data={"frame": (io.BytesIO(_blank_frame_bytes()), "frame.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409


def test_frame_missing_file_returns_400(client):
    _calibrate(client)
    response = client.post("/internal/vision/board1/frame", data={})
    assert response.status_code == 400


def test_full_flow_detects_confirms_and_lists_throws(client):
    _calibrate(client)
    client.post(
        "/internal/vision/board1/reference-frame",
        data={"frame": (io.BytesIO(_blank_frame_bytes()), "frame.png")},
        content_type="multipart/form-data",
    )

    dart_bytes = _dart_frame_bytes((100, 40))
    for _ in range(2):
        response = client.post(
            "/internal/vision/board1/frame",
            data={"frame": (io.BytesIO(dart_bytes), "frame.png")},
            content_type="multipart/form-data",
        )
        assert response.get_json()["landing"] is None

    landing_response = client.post(
        "/internal/vision/board1/frame",
        data={"frame": (io.BytesIO(dart_bytes), "frame.png")},
        content_type="multipart/form-data",
    )
    landing = landing_response.get_json()["landing"]
    assert landing is not None
    throw_id = landing["throw_id"]

    pending_response = client.get("/internal/vision/board1/throws/pending")
    pending_ids = {t["throw_id"] for t in pending_response.get_json()}
    assert throw_id in pending_ids

    confirm_response = client.post(f"/internal/vision/board1/throws/{throw_id}/confirm")
    assert confirm_response.get_json()["status"] == "ACCEPTED"

    pending_after = client.get("/internal/vision/board1/throws/pending").get_json()
    assert pending_after == []


def test_correct_throw(client):
    _calibrate(client)
    client.post(
        "/internal/vision/board1/reference-frame",
        data={"frame": (io.BytesIO(_blank_frame_bytes()), "frame.png")},
        content_type="multipart/form-data",
    )
    dart_bytes = _dart_frame_bytes((100, 40))
    for _ in range(3):
        response = client.post(
            "/internal/vision/board1/frame",
            data={"frame": (io.BytesIO(dart_bytes), "frame.png")},
            content_type="multipart/form-data",
        )
    throw_id = response.get_json()["landing"]["throw_id"]

    correct_response = client.post(
        f"/internal/vision/board1/throws/{throw_id}/correct",
        json={"score": 5, "multiplier": "SINGLE", "ring": "SINGLE", "segment": 5},
    )
    assert correct_response.status_code == 200
    body = correct_response.get_json()
    assert body["status"] == "CORRECTED"
    assert body["final_result"]["score"] == 5


def test_confirm_unknown_throw_returns_404(client):
    _calibrate(client)
    response = client.post("/internal/vision/board1/throws/does-not-exist/confirm")
    assert response.status_code == 404


def test_boards_are_isolated_from_each_other(client):
    _calibrate(client, board_id="board1")
    _calibrate(client, board_id="board2")
    client.post(
        "/internal/vision/board1/reference-frame",
        data={"frame": (io.BytesIO(_blank_frame_bytes()), "frame.png")},
        content_type="multipart/form-data",
    )
    # board2 never got a reference frame -- submitting to it must still 409.
    response = client.post(
        "/internal/vision/board2/frame",
        data={"frame": (io.BytesIO(_blank_frame_bytes()), "frame.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409
