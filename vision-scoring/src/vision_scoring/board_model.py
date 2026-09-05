"""Analytic dartboard geometry: ring/segment lookup from polar board-plane coordinates.

Standard WDF/PDC dartboard dimensions (millimeters, radius from board center).
Once a camera has been calibrated (see calibration.py) and a landing point has
been rectified into board-plane (x, y) millimeters, these boundaries are used
directly rather than re-detecting the printed wire pattern on every frame.
"""

import math
from dataclasses import dataclass
from enum import Enum


class Ring(str, Enum):
    DOUBLE_BULL = "DBLBULL"
    BULL = "BULL"
    TRIPLE = "TRIPLE"
    DOUBLE = "DOUBLE"
    SINGLE = "SINGLE"
    MISS = "MISS"


# Radii in millimeters, from board center outward.
RADIUS_DOUBLE_BULL_MM = 6.35
RADIUS_BULL_MM = 15.9
RADIUS_TRIPLE_INNER_MM = 99.0
RADIUS_TRIPLE_OUTER_MM = 107.0
RADIUS_DOUBLE_INNER_MM = 162.0
RADIUS_DOUBLE_OUTER_MM = 170.0

# Segment numbers in clockwise order starting from the segment centered at
# angle 0 (straight up). Standard non-sequential dartboard layout.
SEGMENT_ORDER = [
    20,
    1,
    18,
    4,
    13,
    6,
    10,
    15,
    2,
    17,
    3,
    19,
    7,
    16,
    8,
    11,
    14,
    9,
    12,
    5,
]
SEGMENT_WIDTH_DEG = 360.0 / len(SEGMENT_ORDER)


@dataclass(frozen=True)
class ScoreResult:
    score: int
    multiplier: str
    ring: Ring
    segment: int | None
    confidence: float


def segment_at_angle(theta_deg: float) -> int:
    """Return the segment number for an angle in degrees, 0 = up, clockwise-positive."""
    normalized = theta_deg % 360.0
    index = round(normalized / SEGMENT_WIDTH_DEG) % len(SEGMENT_ORDER)
    return SEGMENT_ORDER[index]


def _distance_to_nearest_segment_boundary_deg(theta_deg: float) -> float:
    """Segment centers sit at multiples of SEGMENT_WIDTH_DEG (0, 18, 36, ...),
    so boundaries sit halfway between them. Distance is measured as how far
    theta_deg is from the nearest boundary, in [0, SEGMENT_WIDTH_DEG/2]."""
    half_width = SEGMENT_WIDTH_DEG / 2
    normalized = theta_deg % 360.0
    offset_from_center = ((normalized + half_width) % SEGMENT_WIDTH_DEG) - half_width
    return half_width - abs(offset_from_center)


def _ring_and_confidence(radius_mm: float) -> tuple[Ring, float]:
    """Map a radius to a ring, plus a 0..1 confidence based on distance to the
    nearest ring boundary (closer to a boundary line -> lower confidence)."""
    boundaries = [
        RADIUS_DOUBLE_BULL_MM,
        RADIUS_BULL_MM,
        RADIUS_TRIPLE_INNER_MM,
        RADIUS_TRIPLE_OUTER_MM,
        RADIUS_DOUBLE_INNER_MM,
        RADIUS_DOUBLE_OUTER_MM,
    ]
    if radius_mm <= RADIUS_DOUBLE_BULL_MM:
        ring = Ring.DOUBLE_BULL
    elif radius_mm <= RADIUS_BULL_MM:
        ring = Ring.BULL
    elif radius_mm <= RADIUS_TRIPLE_INNER_MM:
        ring = Ring.SINGLE
    elif radius_mm <= RADIUS_TRIPLE_OUTER_MM:
        ring = Ring.TRIPLE
    elif radius_mm <= RADIUS_DOUBLE_INNER_MM:
        ring = Ring.SINGLE
    elif radius_mm <= RADIUS_DOUBLE_OUTER_MM:
        ring = Ring.DOUBLE
    else:
        ring = Ring.MISS

    nearest_boundary_dist = min(abs(radius_mm - b) for b in boundaries)
    # 5mm of clearance from a boundary is treated as "fully confident" on the
    # ring axis; this is combined with segment-angle confidence by the caller.
    ring_confidence = min(1.0, nearest_boundary_dist / 5.0)
    return ring, ring_confidence


def score_at(x_mm: float, y_mm: float) -> ScoreResult:
    """Map a board-plane point (millimeters, origin at board center) to a score."""
    radius_mm = math.hypot(x_mm, y_mm)
    theta_deg = math.degrees(math.atan2(x_mm, y_mm))  # 0 = up, clockwise-positive

    ring, ring_confidence = _ring_and_confidence(radius_mm)

    if ring == Ring.MISS:
        return ScoreResult(
            score=0, multiplier=Ring.MISS.value, ring=ring, segment=None, confidence=1.0
        )

    if ring in (Ring.DOUBLE_BULL, Ring.BULL):
        score = 50 if ring == Ring.DOUBLE_BULL else 25
        multiplier = Ring.DOUBLE_BULL.value if ring == Ring.DOUBLE_BULL else Ring.BULL.value
        return ScoreResult(
            score=score, multiplier=multiplier, ring=ring, segment=None, confidence=ring_confidence
        )

    segment = segment_at_angle(theta_deg)
    boundary_dist_deg = _distance_to_nearest_segment_boundary_deg(theta_deg)
    segment_confidence = min(1.0, boundary_dist_deg / (SEGMENT_WIDTH_DEG / 4))
    confidence = min(ring_confidence, segment_confidence)

    multiplier = (
        Ring.TRIPLE.value
        if ring == Ring.TRIPLE
        else (Ring.DOUBLE.value if ring == Ring.DOUBLE else Ring.SINGLE.value)
    )
    return ScoreResult(
        score=segment, multiplier=multiplier, ring=ring, segment=segment, confidence=confidence
    )
