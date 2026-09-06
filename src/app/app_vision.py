"""
Camera vision-scoring endpoints.

Renders the calibration and live-scoring pages (served to mobile and desktop
browsers alike, like the rest of the mobile web app) and proxies their
authenticated requests to the internal vision-scoring container, which does
the actual OpenCV work. The vision-scoring service is not reachable from
outside the platform's own docker network -- this blueprint is the only
thing that talks to it, after this app's own session auth has already
approved the request.
"""

import logging
import os

import requests
from dartserver_core.auth import login_required
from dartserver_core.database_service import get_database_service
from flask import Blueprint, jsonify, render_template, request

vision_bp = Blueprint("vision", __name__)
logger = logging.getLogger(__name__)

VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://vision-scoring:5901")
_REQUEST_TIMEOUT_SECONDS = 10


def _proxy_error(exc: Exception):
    logger.exception("Error proxying request to vision-scoring service")
    return jsonify({"error": "vision-scoring service unavailable", "message": str(exc)}), 502


@vision_bp.route("/vision")
@login_required
def vision_scoring_page():
    """Live camera vision-scoring page (mobile and desktop)."""
    return render_template("vision_scoring.html")


@vision_bp.route("/vision/calibrate")
@login_required
def vision_calibrate_page():
    """Camera calibration page: click reference points on a captured frame."""
    return render_template("vision_calibrate.html")


def _register_vision_board(board_id):
    """Add a calibrated camera board to the board registry.

    The vision-scoring container has no database access of its own, so this
    proxy is where a vision board first becomes a known, persisted identity.
    """
    try:
        db_service = get_database_service()
        if db_service is not None:
            db_service.get_or_create_board(board_id, kind="vision")
    except Exception:
        # Registration is best-effort; never fail a calibration save over it
        logger.exception(f"Could not register vision board '{board_id}'")


@vision_bp.route("/api/vision/<board_id>/calibration", methods=["GET", "POST"])
@login_required
def vision_calibration(board_id):
    try:
        if request.method == "GET":
            response = requests.get(
                f"{VISION_SERVICE_URL}/internal/vision/{board_id}/calibration",
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
        else:
            response = requests.post(
                f"{VISION_SERVICE_URL}/internal/vision/{board_id}/calibration",
                json=request.get_json(force=True),
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
    except requests.RequestException as exc:
        return _proxy_error(exc)

    if request.method == "POST" and response.status_code < 400:
        _register_vision_board(board_id)

    return jsonify(response.json()), response.status_code


@vision_bp.route("/api/vision/<board_id>/reference-frame", methods=["POST"])
@login_required
def vision_reference_frame(board_id):
    if "frame" not in request.files:
        return jsonify({"error": "missing 'frame' file"}), 400
    frame_file = request.files["frame"]
    try:
        response = requests.post(
            f"{VISION_SERVICE_URL}/internal/vision/{board_id}/reference-frame",
            files={"frame": (frame_file.filename, frame_file.stream, frame_file.mimetype)},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _proxy_error(exc)
    return jsonify(response.json()), response.status_code


@vision_bp.route("/api/vision/<board_id>/frame", methods=["POST"])
@login_required
def vision_frame(board_id):
    if "frame" not in request.files:
        return jsonify({"error": "missing 'frame' file"}), 400
    frame_file = request.files["frame"]
    try:
        response = requests.post(
            f"{VISION_SERVICE_URL}/internal/vision/{board_id}/frame",
            files={"frame": (frame_file.filename, frame_file.stream, frame_file.mimetype)},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _proxy_error(exc)
    return jsonify(response.json()), response.status_code


@vision_bp.route("/api/vision/<board_id>/throws/pending", methods=["GET"])
@login_required
def vision_pending_throws(board_id):
    try:
        response = requests.get(
            f"{VISION_SERVICE_URL}/internal/vision/{board_id}/throws/pending",
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _proxy_error(exc)
    return jsonify(response.json()), response.status_code


@vision_bp.route("/api/vision/<board_id>/throws/<throw_id>/<action>", methods=["POST"])
@login_required
def vision_throw_action(board_id, throw_id, action):
    if action not in ("confirm", "correct", "cancel"):
        return jsonify({"error": "unknown action"}), 404
    correction_payload = request.get_json(force=True) if action == "correct" else None
    try:
        response = requests.post(
            f"{VISION_SERVICE_URL}/internal/vision/{board_id}/throws/{throw_id}/{action}",
            json=correction_payload,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _proxy_error(exc)
    return jsonify(response.json()), response.status_code
