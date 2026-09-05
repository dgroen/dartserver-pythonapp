# vision-scoring

Camera-based dart scoring for Dartserver. This service does no capture of its
own and is never run locally by a player/operator: the browser (mobile phone
or desktop, via the platform's own web app at `/vision` and `/vision/calibrate`)
captures frames from the device's camera and posts them to the platform,
which proxies them to this internal container. It turns those frames into
`{"score", "multiplier"}` events, which then flow through Dartserver's
existing API Gateway -> RabbitMQ -> game engine pipeline unchanged, the same
way an electronic dartboard's throws do today.

This container is **not reachable from outside the platform's own docker
network** -- `src/app/app_vision.py` (in the main `dartserver-pythonapp`
project) is the only caller, after the browser's normal session auth has
already approved the request. See `../doc/` for the full architecture plan.

## Status

- **Phase A (static-image calibration + manual harness): done.**
  `board_model.py` and `calibration.py` implement the homography +
  analytic ring/segment lookup; `scripts/score_from_image.py` scores a
  single (image-independent) pixel coordinate against a stored calibration.
- **Phase B (live capture + confidence-gated confirm UI): done, reworked.**
  Originally built as a local script pulling an MJPEG stream from a phone
  running an "IP Webcam"-style app. Reworked so there is no locally-run
  process at all: `detector.py` (frame-diff dart-landing detection),
  `confirm_state.py` (confidence-gated pending-throw state machine) are
  unchanged, but frame ingestion is now HTTP-driven (`server.py`,
  `sessions.py`) rather than a local capture loop -- see "Architecture" below.
- **Phase C (full wire-up into Dartserver via the API Gateway): done.**
  `publisher.py` implements the OAuth2 client-credentials flow (mirrors
  `scripts/dartboard_simulator.py`) and POSTs resolved throws to
  `POST /api/v1/vision/throw` (`src/api_gateway/app.py`, scope
  `vision:write`), which publishes to `darts_exchange` with routing key
  `darts.vision.throw`. `src/app/app.py`'s `message_router` gained a
  `source == "vision"` branch and `on_vision_throw_received()`, calling
  `GameManager.process_score()` exactly like the other input methods --
  `GameManager` and the game engines are unchanged.
- **Browser-driven architecture (supersedes the original local-script
  design): done.** See "Architecture" below. Calibration and live scoring
  are both regular pages in the existing mobile/desktop web app, served by a
  new `src/app/app_vision.py` blueprint (`GET /vision`, `GET /vision/calibrate`,
  plus authenticated proxy routes under `/api/vision/*`). This container
  exposes an internal-only HTTP API (`server.py`) that those proxy routes
  call; `sessions.py` keeps per-board_id state (calibration, detector,
  pending throws) between HTTP requests, since there's no continuous local
  camera loop anymore.
  Not yet deployed anywhere -- deploying/testing this against the real
  `test` environment goes through a PR into the `test` branch (which
  triggers `deploy-unified.yml`'s live test-server deployment), not a direct
  merge.
- **Phase D (robustness) / Phase E (optional YOLO upgrade): not started.**

## Architecture

```
Browser (phone or desktop, at /vision or /vision/calibrate)
    | getUserMedia camera + periodic canvas.toBlob() snapshot
    v
darts-app (main platform, session-authenticated)
    | src/app/app_vision.py proxies to the internal container
    v
vision-scoring container (this project, internal docker network only)
    | server.py -> sessions.py -> detector.py / calibration.py / board_model.py
    | on a resolved throw: publisher.py
    v
POST /api/v1/vision/throw (API Gateway, OAuth2 vision:write)
    v
RabbitMQ darts_exchange (darts.vision.throw) -> GameManager.process_score()
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

Run the server directly (without gunicorn) for local development:

```bash
VISION_CALIBRATION_DIR=./calibration python -m vision_scoring.server
```

## Layout

- `src/vision_scoring/board_model.py` - analytic dartboard ring/segment geometry.
- `src/vision_scoring/calibration.py` - homography-based pixel -> board-plane mm mapping.
- `src/vision_scoring/scoring.py` - combines calibration + board model into a throw payload.
- `src/vision_scoring/detector.py` - frame-diff dart-landing detection.
- `src/vision_scoring/confirm_state.py` - confidence-gated pending-throw state machine.
- `src/vision_scoring/sessions.py` - per-board_id session state (calibration/detector/gate).
- `src/vision_scoring/server.py` - internal HTTP API (the container's entrypoint).
- `src/vision_scoring/config.py` - env-driven configuration.
- `src/vision_scoring/publisher.py` - OAuth2 client-credentials + POST to the API Gateway.
- `scripts/score_from_image.py` - Phase A CLI harness (still useful for offline debugging).
- `calibration/` - per-board calibration JSON files, persisted via a docker volume in production.

## Platform-side pieces (in the main `dartserver-pythonapp` project, not here)

- `src/app/app_vision.py` - `/vision`, `/vision/calibrate` pages + authenticated proxy routes.
- `templates/vision_scoring.html`, `templates/vision_calibrate.html` - the pages themselves.
- `static/js/vision-scoring.js`, `static/js/vision-calibrate.js` - camera capture + UI logic.
- `static/css/vision.css` - shared styling for both pages.
