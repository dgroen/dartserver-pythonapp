# Vision Scoring: How It Works

This document explains the camera-based (computer vision) dart scoring feature end to
end: what runs where, what data it stores and for how long, and what happens to every
image the browser sends. It complements [doc/DARTBOARD_THROW_INTEGRATION.md](DARTBOARD_THROW_INTEGRATION.md),
which covers the electronic-dartboard input path that vision-scoring mirrors on the
publishing side.

## Quick answers

- **Calibration data is not stored in the PostgreSQL database.** It lives as small JSON
  files on a dedicated Docker volume (`vision_calibration_data`), one file per board,
  managed entirely by the `vision-scoring` container. No table in `postgres` holds it.
- **Camera images are never stored.** Every frame the browser uploads (reference frame
  or live frame) is decoded into memory, used for one comparison, and then discarded.
  Nothing is written to disk and nothing is persisted to the database. The only thing
  that outlives a single request is the *numeric score result* of a resolved throw,
  and only until it's confirmed and published (or explicitly cancelled).

## Architecture overview

```
Browser (mobile or desktop)
  │  getUserMedia() camera capture, canvas snapshot every ~N ms
  │  session-authenticated fetch()
  ▼
darts-app (src/app/app_vision.py)         <- Flask blueprint, requires login
  │  proxies the already-authenticated request, adds no new auth of its own
  ▼
vision-scoring container (internal only, not internet-reachable)
  │  src/vision_scoring/server.py  -> sessions.py -> calibration.py / detector.py
  │  1. decode uploaded frame (cv2.imdecode) into an in-memory image
  │  2. compare against the in-memory reference frame (frame-diff)
  │  3. if a new, stable dart-tip blob is found: map pixel -> board mm -> score
  │  4. hold the result in memory (confidence-gated auto-accept / operator confirm)
  │  5. once resolved, publish {"score","multiplier",...} to the API Gateway
  ▼  OAuth2 client-credentials (WSO2), scope vision:write
POST /api/v1/vision/throw  ->  API Gateway (src/api_gateway/app.py)
  ▼  publish routing_key="darts.vision.throw"
RabbitMQ darts_exchange
  ▼
message_router (src/app/app.py) -> on_vision_throw_received()
  ▼
GameManager.process_score({"score","multiplier"})   [unchanged, same as manual/dartboard input]
```

The vision-scoring container is a separate Flask/gunicorn process with no camera of its
own. It only ever sees frames that a browser has already captured and POSTed to it via
the main app's proxy routes — there is no local script, no standalone capture loop, and
nothing runs on the user's own machine outside the browser tab.

## Calibration: what it is and where it lives

Calibration maps this camera's pixel coordinates to real board-plane millimeters for one
physical board setup. The operator does this once (or after moving the camera) via
`/vision/calibrate`: the page shows a captured frame and the operator clicks four known
reference points (e.g. the outer double-ring edge at the 20/3/11/6 boundary).

- The browser sends the four `(pixel_x, pixel_y)` clicks plus their known
  `(mm_x, mm_y)` board-plane equivalents as JSON to
  `POST /api/vision/<board_id>/calibration`.
- `vision-scoring` (`calibration.py: compute_homography`) computes a 3×3 homography
  matrix from those four point pairs with `cv2.findHomography`.
- The result — the homography matrix plus the raw reference points — is written as one
  JSON file: `<calibration_dir>/<board_id>.json`, via `Calibration.save()`
  ([vision-scoring/src/vision_scoring/calibration.py](../vision-scoring/src/vision_scoring/calibration.py)).
- `calibration_dir` is `/app/calibration` inside the container
  (`VISION_CALIBRATION_DIR` env var), which is bind-mounted to the named Docker volume
  `vision_calibration_data` (see `docker-compose-localhost.yml` and
  `docker-compose-vision-test.yml`). This volume is what makes calibration survive a
  container restart/redeploy — it is host/Docker-managed file storage, not a database.
- On startup (or first request for a given `board_id`), `SessionManager.get_or_create`
  checks whether `<board_id>.json` exists and loads it back into memory automatically —
  this is why calibration only needs to be done once per physical setup, not once per
  session or per container restart.
- No calibration data is ever sent to, or stored in, the app's PostgreSQL database
  (`darts_db`). It is board/camera-position configuration, not game or user data, so it
  intentionally lives alongside the service that uses it rather than in the shared app
  database.

Example of what a calibration file actually contains (illustrative):

```json
{
  "board_id": "board-1",
  "homography": [[...], [...], [...]],
  "reference_points_px": [[412.0, 88.0], [901.0, 300.0], [420.0, 700.0], [50.0, 310.0]],
  "reference_points_mm": [[0.0, 170.0], [170.0, 0.0], [0.0, -170.0], [-170.0, 0.0]]
}
```

Only geometry (pixel/millimeter coordinate pairs and the derived matrix) is stored —
no image content.

## Images: capture, use, and disposal

There are two kinds of images the browser ever sends, and both are handled the same
way — decoded, used once, then dropped:

### 1. Reference frame (`POST /api/vision/<board_id>/reference-frame`)

Taken once at the start of a session (or re-taken after all darts are pulled from the
board), this is the "board at rest, no new dart" baseline.

- `app_vision.py` proxies the uploaded file straight through to
  `vision-scoring`'s `/internal/vision/<board_id>/reference-frame` — the browser's file
  bytes pass through the main app without being written to disk there either.
- `vision-scoring`'s `server.py: set_reference_frame` decodes it with `cv2.imdecode`
  into a numpy array, then hands it to
  `DartLandingDetector.set_reference_frame()`
  ([vision-scoring/src/vision_scoring/detector.py](../vision-scoring/src/vision_scoring/detector.py)),
  which converts it to grayscale and keeps **only that grayscale numpy array** in the
  detector object's memory (`self._reference_gray`).
- The original uploaded image bytes are never written anywhere and are garbage
  collected as soon as the request handler returns.

### 2. Live frames (`POST /api/vision/<board_id>/frame`)

Sent repeatedly (e.g. every second or so) while the browser is watching the board for a
new throw.

- Same proxy path, decoded the same way (`server.py: submit_frame` →
  `cv2.imdecode`).
- `DartLandingDetector.process_frame()` computes a pixel-diff (`cv2.absdiff`) between
  this frame and the in-memory reference frame, looks for a new stable blob (a dart), and
  either returns nothing (nothing changed / not yet stable) or a `Landing` — just a pixel
  coordinate and a contour area, two numbers.
- The uploaded frame's pixel data itself is discarded the moment `process_frame()`
  returns. Nothing about the image survives past that single function call — not the
  frame, not a thumbnail, not a hash of it.
- If a landing was detected, `sessions.py: process_frame` converts that pixel
  coordinate to a score (`{"score","multiplier","confidence",...}`) and hands it to the
  confidence gate (`confirm_state.py`) as a `PendingThrow`, held in memory only, keyed by
  a generated `throw_id`.

### What persists, and for how long

The only thing that outlives a single HTTP request is the **numeric result** of a
detected throw (score, multiplier, ring, segment, confidence) — never the pixels that
produced it. That `PendingThrow` lives purely in the `vision-scoring` process's memory
(inside `SessionManager`/`ConfirmGate`) until one of:

- **Auto-accepted** after its confidence-gated countdown expires (high confidence), or
- **Confirmed** or **corrected** by the operator via the confirm/correct UI, or
- **Cancelled** by the operator.

At that point it is published (`publisher.py`) to the API Gateway as a normal
`{"score","multiplier",...}` event and immediately dropped from memory. If the
`vision-scoring` container restarts before a throw is resolved, that in-flight pending
throw is lost — this is accepted as a low-risk trade-off since it only affects a single
unresolved throw, not calibration or historical game data (which live in `GameManager`/
Postgres exactly as they do for manual or dartboard-based scoring).

## Why this design

- **Privacy / storage minimalism**: since the camera can be pointed at a room the same
  way it's pointed at a dartboard, the system is deliberately built to need no image
  retention at all — every frame is a disposable, momentary "is there a new dart here?"
  check, not a recording.
- **No local software**: everything above the `vision-scoring` container's HTTP
  boundary is a browser tab (mobile or desktop) talking to the platform the same way
  every other Dartserver page does — there is no separate app or script running on the
  operator's phone or PC, and no image ever leaves the platform's own Docker network.
- **Single source of truth for game state**: like the electronic-dartboard integration,
  the resolved score is the only thing that reaches the rest of the platform
  (`GameManager.process_score`), so the game engine, UI, and WebSocket broadcast code
  need zero awareness that vision-scoring exists.

## Related files

| Concern | File |
|---|---|
| Internal HTTP API (frame upload, calibration, confirm/correct) | [vision-scoring/src/vision_scoring/server.py](../vision-scoring/src/vision_scoring/server.py) |
| Per-board in-memory session + calibration load/save | [vision-scoring/src/vision_scoring/sessions.py](../vision-scoring/src/vision_scoring/sessions.py) |
| Homography calibration math + JSON persistence | [vision-scoring/src/vision_scoring/calibration.py](../vision-scoring/src/vision_scoring/calibration.py) |
| Frame-diff dart-landing detection | [vision-scoring/src/vision_scoring/detector.py](../vision-scoring/src/vision_scoring/detector.py) |
| Confidence-gated auto-accept / confirm / correct state machine | [vision-scoring/src/vision_scoring/confirm_state.py](../vision-scoring/src/vision_scoring/confirm_state.py) |
| Publishing resolved throws to the API Gateway | [vision-scoring/src/vision_scoring/publisher.py](../vision-scoring/src/vision_scoring/publisher.py) |
| Env-driven config, incl. `VISION_CALIBRATION_DIR` | [vision-scoring/src/vision_scoring/config.py](../vision-scoring/src/vision_scoring/config.py) |
| Authenticated proxy blueprint (browser ↔ internal service) | [src/app/app_vision.py](../src/app/app_vision.py) |
| Browser camera capture + calibration UI | [static/js/vision-scoring.js](../static/js/vision-scoring.js), [static/js/vision-calibrate.js](../static/js/vision-calibrate.js) |
| Docker volume for calibration JSON files | `docker-compose-localhost.yml`, `docker-compose-vision-test.yml` (`vision_calibration_data`) |
