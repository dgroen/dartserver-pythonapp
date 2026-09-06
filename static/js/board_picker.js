/**
 * Board picker - lets a player say which physical board they throw from.
 *
 * A board (camera or electronic dartboard) is an exclusive physical resource:
 * confirming one locks it to this player for this game so its throws are
 * attributed correctly. The prompt appears once per login session - later
 * games silently reuse the confirmed board - but the "change board" control
 * stays available.
 *
 * Used by both the desktop game page and the mobile gameplay page.
 */
(function () {
  "use strict";

  const KIND_ICONS = { vision: "📷", electronic: "🎯" };

  let container = null;
  let state = { boards: [], lastBoardId: null, confirmedBoardId: null };

  function boardLabel(board) {
    const icon = KIND_ICONS[board.kind] || "🎯";
    return `${icon} ${board.display_name || board.external_id}`;
  }

  async function fetchBoards() {
    const response = await fetch("/api/boards", { credentials: "same-origin" });
    if (!response.ok) throw new Error(`Failed to load boards (${response.status})`);
    const data = await response.json();
    state = {
      boards: data.boards || [],
      lastBoardId: data.last_board_id,
      confirmedBoardId: data.confirmed_board_id,
    };
    return state;
  }

  async function confirmBoard(boardId) {
    const response = await fetch("/api/game/board-confirm", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board_id: boardId }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.message || "Could not confirm that board");
    }
    state.confirmedBoardId = boardId;
    return data;
  }

  function confirmedBoard() {
    return state.boards.find((b) => b.id === state.confirmedBoardId) || null;
  }

  /** The always-available summary line with its "Change" control. */
  function renderSummary() {
    if (!container) return;
    container.innerHTML = "";

    if (!state.boards.length) {
      // Nothing registered yet: manual entry only, so say nothing at all.
      return;
    }

    const bar = document.createElement("div");
    bar.className = "board-picker-bar";

    const label = document.createElement("span");
    label.className = "board-picker-label";
    const current = confirmedBoard();
    label.textContent = current
      ? `Board: ${boardLabel(current)}`
      : "No board confirmed - throws from a board won't be counted";
    bar.appendChild(label);

    const changeBtn = document.createElement("button");
    changeBtn.type = "button";
    changeBtn.className = "btn btn-secondary btn-small board-picker-change";
    changeBtn.textContent = current ? "Change board" : "Choose board";
    changeBtn.addEventListener("click", () => openPicker());
    bar.appendChild(changeBtn);

    container.appendChild(bar);
  }

  function openPicker() {
    const overlay = document.createElement("div");
    overlay.className = "board-picker-overlay";

    const dialog = document.createElement("div");
    dialog.className = "board-picker-dialog";
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-label", "Choose your board");

    const heading = document.createElement("h3");
    heading.textContent = "Which board are you throwing from?";
    dialog.appendChild(heading);

    const error = document.createElement("p");
    error.className = "board-picker-error";
    error.hidden = true;
    dialog.appendChild(error);

    const list = document.createElement("div");
    list.className = "board-picker-list";

    // Pre-select the board this player used last, falling back to what they
    // already confirmed in this session.
    const preselected = state.confirmedBoardId || state.lastBoardId;

    state.boards.forEach((board) => {
      const option = document.createElement("label");
      option.className = "board-picker-option";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "board-picker-choice";
      radio.value = String(board.id);
      radio.checked = board.id === preselected;
      // Someone else's board is a physical device we cannot share.
      radio.disabled = board.in_use && !board.in_use_by_me;
      option.appendChild(radio);

      const text = document.createElement("span");
      text.textContent = boardLabel(board) + (radio.disabled ? " (in use)" : "");
      option.appendChild(text);

      list.appendChild(option);
    });
    dialog.appendChild(list);

    const actions = document.createElement("div");
    actions.className = "board-picker-actions";

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "btn btn-secondary btn-small";
    cancelBtn.textContent = "Not now";
    cancelBtn.addEventListener("click", () => overlay.remove());
    actions.appendChild(cancelBtn);

    const confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.className = "btn btn-primary btn-small";
    confirmBtn.textContent = "Confirm";
    confirmBtn.addEventListener("click", async () => {
      const chosen = list.querySelector("input:checked");
      if (!chosen) {
        error.textContent = "Pick a board first.";
        error.hidden = false;
        return;
      }
      confirmBtn.disabled = true;
      try {
        await confirmBoard(parseInt(chosen.value, 10));
        overlay.remove();
        await refresh();
      } catch (e) {
        error.textContent = e.message;
        error.hidden = false;
        confirmBtn.disabled = false;
      }
    });
    actions.appendChild(confirmBtn);

    dialog.appendChild(actions);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
  }

  async function refresh() {
    await fetchBoards();
    renderSummary();
  }

  /**
   * Mount the picker into `containerId`.
   *
   * Prompts only when this login session has no confirmed board yet and there
   * is at least one board to choose - so the second and later games in a
   * session never re-prompt.
   */
  async function init(containerId) {
    container = document.getElementById(containerId);
    if (!container) return;

    try {
      await refresh();
    } catch (e) {
      console.warn("Board picker unavailable:", e);
      return;
    }

    if (!state.confirmedBoardId && state.boards.length) {
      openPicker();
    }
  }

  window.BoardPicker = { init, refresh, openPicker, confirmBoard };
})();
