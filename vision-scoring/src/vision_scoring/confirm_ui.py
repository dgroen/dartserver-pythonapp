"""Local web UI for the confidence-gated confirm workflow (Phase B).

Runs on the same machine as the capture/detector loop. Shows any pending
throw (awaiting confirmation, or counting down to auto-accept) and lets an
operator confirm, correct, or cancel it. This module only wraps ConfirmGate
in HTTP endpoints -- it has no camera or platform (RabbitMQ) integration,
matching Phase B's scope (Phase C wires accepted throws to the API Gateway).
"""

from dataclasses import asdict

from flask import Flask, jsonify, request
from vision_scoring.board_model import Ring, ScoreResult
from vision_scoring.confirm_state import ConfirmGate


def _throw_to_dict(pending) -> dict:
    return {
        "throw_id": pending.throw_id,
        "status": pending.status.value,
        "result": asdict(pending.result),
        "accept_at": pending.accept_at,
        "final_result": asdict(pending.final_result) if pending.final_result else None,
    }


def create_app(gate: ConfirmGate) -> Flask:
    app = Flask(__name__)

    @app.get("/api/throws/pending")
    def list_pending():
        gate.tick()
        return jsonify([_throw_to_dict(t) for t in gate.pending()])

    @app.get("/api/throws/<throw_id>")
    def get_throw(throw_id: str):
        gate.tick()
        try:
            return jsonify(_throw_to_dict(gate.get(throw_id)))
        except KeyError:
            return jsonify({"error": "not found"}), 404

    @app.post("/api/throws/<throw_id>/confirm")
    def confirm_throw(throw_id: str):
        try:
            pending = gate.confirm(throw_id)
        except KeyError:
            return jsonify({"error": "not found"}), 404
        return jsonify(_throw_to_dict(pending))

    @app.post("/api/throws/<throw_id>/correct")
    def correct_throw(throw_id: str):
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
            pending = gate.correct(throw_id, corrected_result)
        except KeyError:
            return jsonify({"error": "not found"}), 404
        return jsonify(_throw_to_dict(pending))

    @app.post("/api/throws/<throw_id>/cancel")
    def cancel_throw(throw_id: str):
        try:
            pending = gate.cancel(throw_id)
        except KeyError:
            return jsonify({"error": "not found"}), 404
        return jsonify(_throw_to_dict(pending))

    return app
