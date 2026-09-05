# vision-scoring

Camera-based dart scoring service for Dartserver. A standalone project (own
`pyproject.toml`, own dependencies) that turns a phone camera feed of a
dartboard into `{"score", "multiplier"}` events, which then flow through
Dartserver's existing API Gateway -> RabbitMQ -> game engine pipeline
unchanged, the same way an electronic dartboard's throws do today.

See `../doc/` for the full architecture plan.

## Status

- **Phase A (static-image calibration + manual harness): done.**
  `board_model.py` and `calibration.py` implement the homography +
  analytic ring/segment lookup; `scripts/score_from_image.py` scores a
  single (image-independent) pixel coordinate against a stored calibration.
- **Phase B (live capture + confidence-gated confirm UI): not started.**
- **Phase C (full wire-up into Dartserver via the API Gateway): not started.**
- **Phase D (robustness) / Phase E (optional YOLO upgrade): not started.**

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Layout

- `src/vision_scoring/board_model.py` - analytic dartboard ring/segment geometry.
- `src/vision_scoring/calibration.py` - homography-based pixel -> board-plane mm mapping.
- `src/vision_scoring/scoring.py` - combines calibration + board model into a throw payload.
- `src/vision_scoring/capture.py`, `detector.py`, `confirm_ui.py`, `publisher.py` - Phase B/C (not yet implemented).
- `scripts/score_from_image.py` - Phase A CLI harness.
- `calibration/` - per-board calibration JSON files (gitignored; generated locally).
