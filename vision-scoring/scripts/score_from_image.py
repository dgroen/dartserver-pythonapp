#!/usr/bin/env python3
"""Phase A manual test harness.

Given a calibration file and a dart-tip pixel coordinate, prints the computed
{"score", "multiplier"} result. Used to validate calibration.py/board_model.py
against a labeled set of still images before any live-capture code exists.

Usage:
    python score_from_image.py --calibration calibration/board1.json --x 512 --y 300
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vision_scoring.calibration import Calibration  # noqa: E402
from vision_scoring.scoring import score_pixel, to_throw_payload  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration", required=True, type=Path, help="Path to calibration JSON")
    parser.add_argument("--x", required=True, type=float, help="Dart-tip pixel x coordinate")
    parser.add_argument("--y", required=True, type=float, help="Dart-tip pixel y coordinate")
    args = parser.parse_args()

    calibration = Calibration.load(args.calibration)
    result = score_pixel(calibration, (args.x, args.y))

    print(
        json.dumps(
            {
                **to_throw_payload(result),
                "ring": result.ring.value,
                "segment": result.segment,
                "confidence": round(result.confidence, 3),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
