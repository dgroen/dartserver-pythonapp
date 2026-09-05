"""Confidence-gated pending-throw workflow.

A detected throw is never published immediately. Instead:

  * High-confidence reads (>= confidence_threshold) start a short countdown;
    if nobody cancels/corrects it before the countdown elapses, it auto-accepts.
  * Low-confidence reads never start a countdown -- they sit as "awaiting
    confirmation" until an operator explicitly confirms or corrects them.

This is pure state-machine logic (no Flask, no camera) so it can be unit
tested directly; confirm_ui.py wraps this in a small local web UI.
"""

import time
from dataclasses import dataclass, field
from enum import Enum

from vision_scoring.board_model import ScoreResult


class ThrowStatus(str, Enum):
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    COUNTING_DOWN = "COUNTING_DOWN"
    ACCEPTED = "ACCEPTED"
    CORRECTED = "CORRECTED"
    CANCELLED = "CANCELLED"


@dataclass
class PendingThrow:
    throw_id: str
    result: ScoreResult
    status: ThrowStatus
    created_at: float
    accept_at: float | None = None
    final_result: ScoreResult | None = field(default=None)


class ConfirmGate:
    def __init__(self, confidence_threshold: float = 0.6, countdown_seconds: float = 3.0):
        self._confidence_threshold = confidence_threshold
        self._countdown_seconds = countdown_seconds
        self._throws: dict[str, PendingThrow] = {}
        self._next_id = 0

    def submit(self, result: ScoreResult, now: float | None = None) -> PendingThrow:
        now = now if now is not None else time.time()
        self._next_id += 1
        throw_id = str(self._next_id)

        if result.confidence >= self._confidence_threshold:
            status = ThrowStatus.COUNTING_DOWN
            accept_at = now + self._countdown_seconds
        else:
            status = ThrowStatus.AWAITING_CONFIRMATION
            accept_at = None

        pending = PendingThrow(
            throw_id=throw_id, result=result, status=status, created_at=now, accept_at=accept_at
        )
        self._throws[throw_id] = pending
        return pending

    def tick(self, now: float | None = None) -> list[PendingThrow]:
        """Advance time; auto-accepts any COUNTING_DOWN throw whose countdown
        has elapsed. Returns the list of throws that were just auto-accepted."""
        now = now if now is not None else time.time()
        newly_accepted = []
        for pending in self._throws.values():
            if pending.status == ThrowStatus.COUNTING_DOWN and now >= pending.accept_at:
                pending.status = ThrowStatus.ACCEPTED
                pending.final_result = pending.result
                newly_accepted.append(pending)
        return newly_accepted

    def confirm(self, throw_id: str) -> PendingThrow:
        pending = self._require(throw_id)
        pending.status = ThrowStatus.ACCEPTED
        pending.final_result = pending.result
        return pending

    def correct(self, throw_id: str, corrected_result: ScoreResult) -> PendingThrow:
        pending = self._require(throw_id)
        pending.status = ThrowStatus.CORRECTED
        pending.final_result = corrected_result
        return pending

    def cancel(self, throw_id: str) -> PendingThrow:
        pending = self._require(throw_id)
        pending.status = ThrowStatus.CANCELLED
        return pending

    def get(self, throw_id: str) -> PendingThrow:
        return self._require(throw_id)

    def pending(self) -> list[PendingThrow]:
        return [
            t
            for t in self._throws.values()
            if t.status in (ThrowStatus.AWAITING_CONFIRMATION, ThrowStatus.COUNTING_DOWN)
        ]

    def _require(self, throw_id: str) -> PendingThrow:
        if throw_id not in self._throws:
            raise KeyError(f"Unknown throw_id: {throw_id}")
        return self._throws[throw_id]
