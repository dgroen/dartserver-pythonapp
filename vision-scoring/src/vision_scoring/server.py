"""Internal HTTP API for the vision-scoring container.

Not exposed to the internet: only reachable inside the platform's own docker
network. The platform's main web app (src/app/app_vision.py) is the only
caller, proxying authenticated browser requests here after decoding a
session's identity -- this service itself does no end-user authentication.

Endpoints are all scoped by board_id, since a single deployment may (in
principle) serve more than one physical board/camera setup concurrently.
"""

from dataclasses import asdict

import cv2
import numpy as np
from flask import Flask, current_app, jsonify, request
from vision_scoring.board_model import Ring, ScoreResult
from vision_scoring.calibration import compute_homography
from vision_scoring.config import VisionScoringConfig
from vision_scoring.confirm_state import PendingThrow
from vision_scoring.publisher import PublisherConfig, VisionThrowPublisher
from vision_scoring.sessions import SessionManager


def _sessions() -> SessionManager:
    return current_app.config["SESSIONS"]


def _throw_to_dict(pending: PendingThrow) -> dict:
    return {
        "throw_id": pending.throw_id,
        "status": pending.status.value,
        "result": asdict(pending.result),
        "accept_at": pending.accept_at,
        "final_result": asdict(pending.final_result) if pending.final_result else None,
    }


def _decode_frame(file_storage) -> np.ndarray | None:
    data = np.frombuffer(file_storage.read(), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _decode_uploaded_frame():
    """Shared file-upload handling for the two endpoints that accept an
    image. Returns (frame, None) on success or (None, error_response)."""
    if "frame" not in request.files:
        return None, (jsonify({"error": "missing 'frame' file"}), 400)
    frame = _decode_frame(request.files["frame"])
    if frame is None:
        return None, (jsonify({"error": "could not decode image"}), 400)
    return frame, None


def _make_publish_callback(config: VisionScoringConfig):
    if not config.publishing_enabled():
        return None

    publisher = VisionThrowPublisher(
        PublisherConfig(
            client_id=config.gateway_client_id,
            client_secret=config.gateway_client_secret,
            token_url=config.gateway_token_url,
            gateway_url=config.gateway_url,
            verify_ssl=config.gateway_verify_ssl,
        )
    )

    def publish(board_id: str, pending: PendingThrow) -> None:
        publisher.publish(
            pending.final_result,
            board_id=board_id,
            confirmed_by_human=pending.status.value == "CORRECTED",
        )

    return publish


def health():
    return jsonify({"status": "ok"})


def set_calibration(board_id: str):
    body = request.get_json(force=True)
    try:
        reference_points_px = [tuple(p) for p in body["reference_points_px"]]
        reference_points_mm = [tuple(p) for p in body["reference_points_mm"]]
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": f"invalid calibration payload: {exc}"}), 400

    try:
        calibration = compute_homography(board_id, reference_points_px, reference_points_mm)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    _sessions().set_calibration(board_id, calibration)
    return jsonify({"board_id": board_id, "status": "calibrated"}), 201


def get_calibration(board_id: str):
    session = _sessions().get_or_create(board_id)
    if not session.is_calibrated():
        return jsonify({"calibrated": False})
    return jsonify(
        {
            "calibrated": True,
            "reference_points_px": session.calibration.reference_points_px,
            "reference_points_mm": session.calibration.reference_points_mm,
        }
    )


def set_reference_frame(board_id: str):
    frame, error = _decode_uploaded_frame()
    if error is not None:
        return error

    try:
        _sessions().set_reference_frame(board_id, frame)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify({"board_id": board_id, "status": "reference_frame_set"}), 201


def submit_frame(board_id: str):
    frame, error = _decode_uploaded_frame()
    if error is not None:
        return error

    try:
        pending = _sessions().process_frame(board_id, frame)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    if pending is None:
        return jsonify({"landing": None})
    return jsonify({"landing": _throw_to_dict(pending)})


def list_pending(board_id: str):
    return jsonify([_throw_to_dict(t) for t in _sessions().pending(board_id)])


def confirm_throw(board_id: str, throw_id: str):
    try:
        pending = _sessions().confirm(board_id, throw_id)
    except KeyError:
        return jsonify({"error": "not found"}), 404
    return jsonify(_throw_to_dict(pending))


def correct_throw(board_id: str, throw_id: str):
    body = request.get_json(force=True)
    try:
        corrected_result = ScoreResult(
            score=int(body["score"]),
            multiplier=body["multiplier"],
            ring=Ring(body.get("ring", body["multiplier"])),
            segment=body.get("segment"),
            confidence=1.0,
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": f"invalid correction payload: {exc}"}), 400

    try:
        pending = _sessions().correct(board_id, throw_id, corrected_result)
    except KeyError:
        return jsonify({"error": "not found"}), 404
    return jsonify(_throw_to_dict(pending))


def cancel_throw(board_id: str, throw_id: str):
    try:
        pending = _sessions().cancel(board_id, throw_id)
    except KeyError:
        return jsonify({"error": "not found"}), 404
    return jsonify(_throw_to_dict(pending))


def create_app(config: VisionScoringConfig | None = None) -> Flask:
    config = config or VisionScoringConfig.from_env()
    app = Flask(__name__)

    app.config["SESSIONS"] = SessionManager(
        calibration_dir=config.calibration_dir,
        confidence_threshold=config.confidence_threshold,
        countdown_seconds=config.countdown_seconds,
        on_resolved=_make_publish_callback(config),
    )

    app.add_url_rule("/health", view_func=health)
    app.add_url_rule(
        "/internal/vision/<board_id>/calibration",
        view_func=set_calibration,
        methods=["POST"],
        endpoint="set_calibration",
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/calibration",
        view_func=get_calibration,
        methods=["GET"],
        endpoint="get_calibration",
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/reference-frame",
        view_func=set_reference_frame,
        methods=["POST"],
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/frame",
        view_func=submit_frame,
        methods=["POST"],
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/throws/pending",
        view_func=list_pending,
        methods=["GET"],
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/throws/<throw_id>/confirm",
        view_func=confirm_throw,
        methods=["POST"],
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/throws/<throw_id>/correct",
        view_func=correct_throw,
        methods=["POST"],
    )
    app.add_url_rule(
        "/internal/vision/<board_id>/throws/<throw_id>/cancel",
        view_func=cancel_throw,
        methods=["POST"],
    )

    return app


if __name__ == "__main__":
    _config = VisionScoringConfig.from_env()
    create_app(_config).run(host=_config.host, port=_config.port)
