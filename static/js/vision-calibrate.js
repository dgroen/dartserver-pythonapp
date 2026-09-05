(function () {
  "use strict";

  // Board-plane mm coordinates for the 4 guided calibration clicks, in the
  // order the UI asks for them. Matches the standard dartboard's outer
  // double-ring radius (170mm) at the 12/3/6/9 o'clock positions -- kept in
  // sync with RADIUS_DOUBLE_OUTER_MM in vision-scoring/src/vision_scoring/board_model.py.
  const RADIUS_DOUBLE_OUTER_MM = 170.0;
  const CALIBRATION_STEPS = [
    { label: "Click the OUTER edge of the double ring at the TOP (12 o'clock)", mm: [0, RADIUS_DOUBLE_OUTER_MM] },
    { label: "Click the OUTER edge of the double ring on the RIGHT (3 o'clock)", mm: [RADIUS_DOUBLE_OUTER_MM, 0] },
    { label: "Click the OUTER edge of the double ring at the BOTTOM (6 o'clock)", mm: [0, -RADIUS_DOUBLE_OUTER_MM] },
    { label: "Click the OUTER edge of the double ring on the LEFT (9 o'clock)", mm: [-RADIUS_DOUBLE_OUTER_MM, 0] },
  ];

  const video = document.getElementById("video");
  const boardIdInput = document.getElementById("boardId");
  const startCameraBtn = document.getElementById("startCameraBtn");
  const captureBtn = document.getElementById("captureBtn");
  const clickCard = document.getElementById("clickCard");
  const clickInstruction = document.getElementById("clickInstruction");
  const canvas = document.getElementById("captureCanvas");
  const resetPointsBtn = document.getElementById("resetPointsBtn");
  const statusCard = document.getElementById("statusCard");
  const statusMessage = document.getElementById("statusMessage");
  const ctx = canvas.getContext("2d");

  let clickedPointsPx = [];

  boardIdInput.value = localStorage.getItem("visionBoardId") || "";

  function boardId() {
    const value = boardIdInput.value.trim();
    if (value) localStorage.setItem("visionBoardId", value);
    return value;
  }

  function showStatus(message) {
    statusCard.hidden = false;
    statusMessage.textContent = message;
  }

  startCameraBtn.addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      video.srcObject = stream;
      captureBtn.disabled = false;
    } catch (err) {
      showStatus("Could not access camera: " + err.message);
    }
  });

  captureBtn.addEventListener("click", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    clickedPointsPx = [];
    clickCard.hidden = false;
    updateInstruction();
  });

  function updateInstruction() {
    if (clickedPointsPx.length >= CALIBRATION_STEPS.length) return;
    clickInstruction.textContent =
      (clickedPointsPx.length + 1) + "/" + CALIBRATION_STEPS.length + ": " +
      CALIBRATION_STEPS[clickedPointsPx.length].label;
  }

  canvas.addEventListener("click", (event) => {
    if (clickedPointsPx.length >= CALIBRATION_STEPS.length) return;
    if (!boardId()) {
      showStatus("Enter a Board ID first.");
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    clickedPointsPx.push([x, y]);

    ctx.fillStyle = "red";
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, 2 * Math.PI);
    ctx.fill();

    if (clickedPointsPx.length >= CALIBRATION_STEPS.length) {
      clickInstruction.textContent = "Submitting calibration...";
      submitCalibration();
    } else {
      updateInstruction();
    }
  });

  resetPointsBtn.addEventListener("click", () => {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    clickedPointsPx = [];
    updateInstruction();
  });

  async function submitCalibration() {
    const referencePointsMm = CALIBRATION_STEPS.map((step) => step.mm);

    try {
      const response = await fetch(`/api/vision/${encodeURIComponent(boardId())}/calibration`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reference_points_px: clickedPointsPx,
          reference_points_mm: referencePointsMm,
        }),
      });
      if (!response.ok) {
        const body = await response.json();
        showStatus("Calibration failed: " + (body.error || response.status));
        return;
      }

      await submitReferenceFrame();
      showStatus("Calibration saved for board '" + boardId() + "'. You can now go to Vision Scoring.");
    } catch (err) {
      showStatus("Calibration request failed: " + err.message);
    }
  }

  function submitReferenceFrame() {
    return new Promise((resolve, reject) => {
      canvas.toBlob(async (blob) => {
        try {
          const formData = new FormData();
          formData.append("frame", blob, "reference.png");
          const response = await fetch(
            `/api/vision/${encodeURIComponent(boardId())}/reference-frame`,
            { method: "POST", body: formData }
          );
          if (!response.ok) {
            const body = await response.json();
            reject(new Error(body.error || String(response.status)));
            return;
          }
          resolve();
        } catch (err) {
          reject(err);
        }
      }, "image/png");
    });
  }
})();
