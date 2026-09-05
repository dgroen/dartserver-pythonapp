(function () {
  "use strict";

  const FRAME_INTERVAL_MS = 800;
  const POLL_INTERVAL_MS = 1000;

  const video = document.getElementById("video");
  const canvas = document.getElementById("captureCanvas");
  const ctx = canvas.getContext("2d");
  const boardIdInput = document.getElementById("boardId");
  const calibrationStatus = document.getElementById("calibrationStatus");
  const startCameraBtn = document.getElementById("startCameraBtn");
  const startScoringBtn = document.getElementById("startScoringBtn");
  const stopScoringBtn = document.getElementById("stopScoringBtn");
  const newRoundBtn = document.getElementById("newRoundBtn");
  const pendingThrowsEl = document.getElementById("pendingThrows");

  let frameIntervalId = null;
  let pollIntervalId = null;

  boardIdInput.value = localStorage.getItem("visionBoardId") || "";
  boardIdInput.addEventListener("change", () => {
    localStorage.setItem("visionBoardId", boardIdInput.value.trim());
    checkCalibration();
  });

  function boardId() {
    return boardIdInput.value.trim();
  }

  async function checkCalibration() {
    if (!boardId()) {
      calibrationStatus.textContent = "";
      return;
    }
    try {
      const response = await fetch(`/api/vision/${encodeURIComponent(boardId())}/calibration`);
      const body = await response.json();
      calibrationStatus.textContent = body.calibrated
        ? "✅ Calibrated"
        : "⚠️ Not calibrated yet -- use the Calibrate link below.";
    } catch (err) {
      calibrationStatus.textContent = "Could not check calibration status.";
    }
  }
  checkCalibration();

  startCameraBtn.addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      video.srcObject = stream;
      video.addEventListener(
        "loadedmetadata",
        () => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
        },
        { once: true }
      );
      startScoringBtn.disabled = false;
      newRoundBtn.disabled = false;
    } catch (err) {
      calibrationStatus.textContent = "Could not access camera: " + err.message;
    }
  });

  startScoringBtn.addEventListener("click", () => {
    if (!boardId()) {
      calibrationStatus.textContent = "Enter a Board ID first.";
      return;
    }
    startScoringBtn.disabled = true;
    stopScoringBtn.disabled = false;
    frameIntervalId = setInterval(captureAndSubmitFrame, FRAME_INTERVAL_MS);
    pollIntervalId = setInterval(refreshPendingThrows, POLL_INTERVAL_MS);
  });

  stopScoringBtn.addEventListener("click", () => {
    startScoringBtn.disabled = false;
    stopScoringBtn.disabled = true;
    clearInterval(frameIntervalId);
    clearInterval(pollIntervalId);
  });

  newRoundBtn.addEventListener("click", async () => {
    if (!boardId()) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append("frame", blob, "reference.png");
      try {
        const response = await fetch(
          `/api/vision/${encodeURIComponent(boardId())}/reference-frame`,
          { method: "POST", body: formData }
        );
        if (!response.ok) {
          const body = await response.json();
          calibrationStatus.textContent = "New round failed: " + (body.error || response.status);
        }
      } catch (err) {
        calibrationStatus.textContent = "New round request failed: " + err.message;
      }
    }, "image/png");
  });

  function captureAndSubmitFrame() {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append("frame", blob, "frame.png");
      try {
        const response = await fetch(`/api/vision/${encodeURIComponent(boardId())}/frame`, {
          method: "POST",
          body: formData,
        });
        if (response.status === 409) {
          // Board not calibrated / no reference frame yet -- surface it once.
          const body = await response.json();
          calibrationStatus.textContent = body.error;
        }
      } catch (err) {
        // Transient network hiccups are expected on a periodic loop; ignore.
      }
    }, "image/png");
  }

  async function refreshPendingThrows() {
    if (!boardId()) return;
    try {
      const response = await fetch(`/api/vision/${encodeURIComponent(boardId())}/throws/pending`);
      const throws = await response.json();
      renderThrows(throws);
    } catch (err) {
      // Ignore transient failures; next poll will retry.
    }
  }

  function renderThrows(throwList) {
    if (!throwList.length) {
      pendingThrowsEl.innerHTML = '<p class="vision-empty">No throws detected yet.</p>';
      return;
    }

    pendingThrowsEl.innerHTML = "";
    throwList.forEach((throwItem) => {
      pendingThrowsEl.appendChild(renderThrowCard(throwItem));
    });
  }

  function renderThrowCard(throwItem) {
    const card = document.createElement("div");
    card.className = "vision-throw-card";

    const result = throwItem.result;
    const scoreLine = document.createElement("div");
    scoreLine.className = "vision-throw-score";
    scoreLine.textContent = describeResult(result);
    card.appendChild(scoreLine);

    const meta = document.createElement("div");
    meta.className = "vision-throw-meta";
    meta.textContent =
      "confidence " + Math.round(result.confidence * 100) + "% - " + throwItem.status;
    card.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "vision-throw-actions";

    const confirmBtn = document.createElement("button");
    confirmBtn.className = "btn btn-success btn-small";
    confirmBtn.textContent = "Confirm";
    confirmBtn.addEventListener("click", () => performAction(throwItem.throw_id, "confirm"));
    actions.appendChild(confirmBtn);

    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn btn-danger btn-small";
    cancelBtn.textContent = "Cancel";
    cancelBtn.addEventListener("click", () => performAction(throwItem.throw_id, "cancel"));
    actions.appendChild(cancelBtn);

    const correctBtn = document.createElement("button");
    correctBtn.className = "btn btn-secondary btn-small";
    correctBtn.textContent = "Correct";
    correctBtn.addEventListener("click", () => toggleCorrectForm(card, throwItem.throw_id));
    actions.appendChild(correctBtn);

    card.appendChild(actions);
    return card;
  }

  function describeResult(result) {
    if (result.multiplier === "BULL") return "BULL (25)";
    if (result.multiplier === "DBLBULL") return "BULLSEYE (50)";
    if (result.multiplier === "MISS") return "MISS";
    return result.multiplier + " " + result.score;
  }

  function toggleCorrectForm(card, throwId) {
    let form = card.querySelector(".vision-correct-form");
    if (form) {
      form.remove();
      return;
    }

    form = document.createElement("div");
    form.className = "vision-correct-form";
    form.innerHTML =
      '<input type="number" min="0" max="25" placeholder="score" class="correct-score">' +
      '<select class="correct-multiplier">' +
      '<option value="SINGLE">SINGLE</option>' +
      '<option value="DOUBLE">DOUBLE</option>' +
      '<option value="TRIPLE">TRIPLE</option>' +
      '<option value="BULL">BULL</option>' +
      '<option value="DBLBULL">DBLBULL</option>' +
      "</select>" +
      '<button class="btn btn-primary btn-small submit-correction">Submit</button>';
    card.appendChild(form);

    form.querySelector(".submit-correction").addEventListener("click", () => {
      const score = parseInt(form.querySelector(".correct-score").value, 10);
      const multiplier = form.querySelector(".correct-multiplier").value;
      if (Number.isNaN(score)) return;
      performAction(throwId, "correct", { score, multiplier, ring: multiplier });
    });
  }

  async function performAction(throwId, action, payload) {
    try {
      await fetch(
        `/api/vision/${encodeURIComponent(boardId())}/throws/${encodeURIComponent(throwId)}/${action}`,
        {
          method: "POST",
          headers: payload ? { "Content-Type": "application/json" } : undefined,
          body: payload ? JSON.stringify(payload) : undefined,
        }
      );
      refreshPendingThrows();
    } catch (err) {
      calibrationStatus.textContent = "Action failed: " + err.message;
    }
  }
})();
