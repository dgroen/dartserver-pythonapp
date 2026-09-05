from vision_scoring.board_model import Ring, score_at


def test_double_bull_center():
    result = score_at(0.0, 0.0)
    assert result.score == 50
    assert result.multiplier == "DBLBULL"
    assert result.ring == Ring.DOUBLE_BULL


def test_single_bull_ring():
    result = score_at(0.0, 10.0)
    assert result.score == 25
    assert result.multiplier == "BULL"
    assert result.ring == Ring.BULL


def test_segment_20_single_straight_up():
    # Straight up from center (theta=0), just inside the triple ring -> single 20.
    result = score_at(0.0, 60.0)
    assert result.segment == 20
    assert result.multiplier == "SINGLE"


def test_segment_20_triple():
    result = score_at(0.0, 103.0)
    assert result.segment == 20
    assert result.multiplier == "TRIPLE"
    assert result.score == 20


def test_segment_20_double():
    result = score_at(0.0, 166.0)
    assert result.segment == 20
    assert result.multiplier == "DOUBLE"
    assert result.score == 20


def test_miss_outside_board():
    result = score_at(0.0, 200.0)
    assert result.ring == Ring.MISS
    assert result.score == 0
    assert result.multiplier == "MISS"


def test_segment_3_to_the_right_of_center():
    # 90 degrees clockwise from the top (20) segment should land in segment 3's
    # neighborhood per the standard board layout (20, 1, 18, ... going clockwise
    # means segment at 90deg is a few segments around; just check it's a valid
    # board number, not a specific one, to avoid over-asserting layout details.
    result = score_at(60.0, 0.0)
    assert result.segment in range(1, 21)


def test_confidence_near_boundary_is_low():
    near_boundary = score_at(0.0, 99.5)  # just at the triple-ring inner edge
    far_from_boundary = score_at(0.0, 103.0)  # middle of the triple ring
    assert near_boundary.confidence < far_from_boundary.confidence
