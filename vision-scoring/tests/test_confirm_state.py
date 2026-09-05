import pytest
from vision_scoring.board_model import Ring, ScoreResult
from vision_scoring.confirm_state import ConfirmGate, ThrowStatus


def _result(confidence: float) -> ScoreResult:
    return ScoreResult(
        score=20, multiplier="TRIPLE", ring=Ring.TRIPLE, segment=20, confidence=confidence
    )


def test_high_confidence_starts_countdown():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    pending = gate.submit(_result(0.9), now=100.0)
    assert pending.status == ThrowStatus.COUNTING_DOWN
    assert pending.accept_at == pytest.approx(103.0)


def test_low_confidence_awaits_confirmation_with_no_countdown():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    pending = gate.submit(_result(0.2), now=100.0)
    assert pending.status == ThrowStatus.AWAITING_CONFIRMATION
    assert pending.accept_at is None


def test_tick_auto_accepts_after_countdown_elapses():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    pending = gate.submit(_result(0.9), now=100.0)

    assert gate.tick(now=101.0) == []
    assert pending.status == ThrowStatus.COUNTING_DOWN

    accepted = gate.tick(now=103.5)
    assert len(accepted) == 1
    assert accepted[0].throw_id == pending.throw_id
    assert pending.status == ThrowStatus.ACCEPTED
    assert pending.final_result == pending.result


def test_tick_does_not_touch_awaiting_confirmation_throws():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    pending = gate.submit(_result(0.1), now=100.0)
    accepted = gate.tick(now=1000.0)
    assert accepted == []
    assert pending.status == ThrowStatus.AWAITING_CONFIRMATION


def test_operator_can_confirm_a_low_confidence_throw():
    gate = ConfirmGate()
    pending = gate.submit(_result(0.1), now=100.0)
    confirmed = gate.confirm(pending.throw_id)
    assert confirmed.status == ThrowStatus.ACCEPTED
    assert confirmed.final_result == confirmed.result


def test_operator_can_correct_a_throw():
    gate = ConfirmGate()
    pending = gate.submit(_result(0.1), now=100.0)
    corrected_result = _result(1.0)
    corrected = gate.correct(pending.throw_id, corrected_result)
    assert corrected.status == ThrowStatus.CORRECTED
    assert corrected.final_result is corrected_result


def test_operator_can_cancel_a_counting_down_throw_before_it_auto_accepts():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    pending = gate.submit(_result(0.9), now=100.0)
    gate.cancel(pending.throw_id)
    assert pending.status == ThrowStatus.CANCELLED

    # Cancelled throws must not be auto-accepted by a later tick.
    accepted = gate.tick(now=200.0)
    assert accepted == []
    assert pending.status == ThrowStatus.CANCELLED


def test_pending_lists_only_unresolved_throws():
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0)
    high = gate.submit(_result(0.9), now=100.0)
    low = gate.submit(_result(0.1), now=100.0)
    gate.confirm(low.throw_id)

    pending_ids = {t.throw_id for t in gate.pending()}
    assert pending_ids == {high.throw_id}


def test_unknown_throw_id_raises_key_error():
    gate = ConfirmGate()
    with pytest.raises(KeyError):
        gate.confirm("does-not-exist")


def test_on_resolved_called_on_auto_accept():
    resolved = []
    gate = ConfirmGate(confidence_threshold=0.6, countdown_seconds=3.0, on_resolved=resolved.append)
    pending = gate.submit(_result(0.9), now=100.0)
    gate.tick(now=103.5)
    assert resolved == [pending]


def test_on_resolved_called_on_confirm_and_correct_but_not_cancel():
    resolved = []
    gate = ConfirmGate(on_resolved=resolved.append)

    confirmed = gate.submit(_result(0.1), now=100.0)
    gate.confirm(confirmed.throw_id)

    corrected = gate.submit(_result(0.1), now=100.0)
    gate.correct(corrected.throw_id, _result(1.0))

    cancelled = gate.submit(_result(0.1), now=100.0)
    gate.cancel(cancelled.throw_id)

    assert resolved == [confirmed, corrected]
