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
- **Phase B (live capture + confidence-gated confirm UI): done.**
  `capture.py` wraps `cv2.VideoCapture` for MJPEG-over-WiFi ingestion with
  reconnect handling; `detector.py` does frame-diff dart-landing detection
  with a settle-frame debounce; `confirm_state.py` is the confidence-gated
  pending-throw state machine (auto-accept countdown above the confidence
  threshold, mandatory operator confirm/correct below it); `confirm_ui.py`
  exposes that state machine as a small local Flask API;
  `scripts/live_pipeline.py` wires all of it into one runnable process.
  Not yet tested against a real phone/board (needs the physical setup).
- **Phase C (full wire-up into Dartserver via the API Gateway): not started.**
  This is also the first phase that will get deployed/tested against the
  `test` branch's live test-server pipeline, once there's a `publisher.py`
  actually talking to the API Gateway.
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
- `src/vision_scoring/capture.py` - MJPEG-over-WiFi phone camera ingestion.
- `src/vision_scoring/detector.py` - frame-diff dart-landing detection.
- `src/vision_scoring/confirm_state.py` - confidence-gated pending-throw state machine.
- `src/vision_scoring/confirm_ui.py` - local Flask API wrapping the confirm state machine.
- `src/vision_scoring/config.py` - env-driven configuration for the live pipeline.
- `src/vision_scoring/publisher.py` - Phase C (not yet implemented): OAuth2 + POST to the API Gateway.
- `scripts/score_from_image.py` - Phase A CLI harness.
- `scripts/live_pipeline.py` - Phase B runnable process (capture -> detect -> score -> confirm UI).
- `calibration/` - per-board calibration JSON files (gitignored; generated locally).
