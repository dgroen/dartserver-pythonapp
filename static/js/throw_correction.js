/**
 * Correct the last throw from the game page.
 *
 * Camera and electronic-board detections can be wrong. Clicking a segment on
 * the interactive dartboard asks whether to replace the last recorded throw
 * (SCD2-versioned server side) or register the click as a brand-new throw.
 *
 * Used by the desktop game page; the mobile page posts to the same endpoint
 * from its own inline form.
 */
(function () {
  "use strict";

  function describe(selection) {
    if (selection.multiplier === "BULL") return "BULL (25)";
    if (selection.multiplier === "DBLBULL") return "BULLSEYE (50)";
    return `${selection.multiplier} ${selection.score}`;
  }

  async function submit(selection, mode) {
    const response = await fetch("/api/game/throw/correct", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        score: selection.score,
        multiplier: selection.multiplier,
        mode,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.message || "Could not apply that throw");
    }
    return data;
  }

  function showStatus(container, message, isError) {
    let status = container.querySelector(".throw-correction-status");
    if (!status) {
      status = document.createElement("p");
      status.className = "throw-correction-status";
      container.appendChild(status);
    }
    status.textContent = message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function openChoice(container, selection) {
    const overlay = document.createElement("div");
    overlay.className = "throw-correction-overlay";

    const dialog = document.createElement("div");
    dialog.className = "throw-correction-dialog";
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");

    const heading = document.createElement("h3");
    heading.textContent = describe(selection);
    dialog.appendChild(heading);

    const question = document.createElement("p");
    question.textContent = "Replace the last throw, or register this as a new throw?";
    dialog.appendChild(question);

    const error = document.createElement("p");
    error.className = "throw-correction-error";
    error.hidden = true;
    dialog.appendChild(error);

    const actions = document.createElement("div");
    actions.className = "throw-correction-actions";

    function addButton(label, className, mode) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = className;
      button.textContent = label;
      button.addEventListener("click", async () => {
        actions.querySelectorAll("button").forEach((b) => (b.disabled = true));
        try {
          await submit(selection, mode);
          overlay.remove();
          showStatus(
            container,
            mode === "replace"
              ? `Last throw corrected to ${describe(selection)}`
              : `Registered ${describe(selection)}`,
            false
          );
        } catch (e) {
          error.textContent = e.message;
          error.hidden = false;
          actions.querySelectorAll("button").forEach((b) => (b.disabled = false));
        }
      });
      actions.appendChild(button);
    }

    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "btn btn-secondary btn-small";
    cancel.textContent = "Cancel";
    cancel.addEventListener("click", () => overlay.remove());
    actions.appendChild(cancel);

    addButton("Register as new throw", "btn btn-secondary btn-small", "new");
    addButton("Replace last throw", "btn btn-primary btn-small", "replace");

    dialog.appendChild(actions);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
  }

  function init(containerId) {
    const container = document.getElementById(containerId);
    if (!container || !window.DartboardVisual) return;

    const heading = document.createElement("div");
    heading.className = "throw-correction-heading";
    heading.textContent = "Wrong score? Click where the dart actually landed.";

    const boardHost = document.createElement("div");
    boardHost.className = "throw-correction-board";

    container.innerHTML = "";
    container.appendChild(heading);
    container.appendChild(boardHost);

    window.DartboardVisual.render(boardHost, {
      mode: "interactive",
      size: 300,
      onSelect: (selection) => openChoice(container, selection),
    });
  }

  window.ThrowCorrection = { init, submit };
})();
