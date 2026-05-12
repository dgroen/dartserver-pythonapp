// Game Creation Page JavaScript

let players = []; // array of { name: string, username?: string }
let selectedUsers = new Set();
let searchTimeout = null;
let selectedUser = null;
let selectedSearchIndex = -1;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function () {
    await loadGameTypes(document.getElementById('game-type'));
    setupEventListeners();
    handleGameTypeChange(); // Initialize hard mode visibility

    // Check for pre-filled players from query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const playersParam = urlParams.get('players');
    if (playersParam) {
        const playerNames = playersParam.split(',').map(name => name.trim()).filter(name => name.length > 0);
        playerNames.forEach(name => {
            addPlayer({ name: name, username: null });
        });
    }
});

function setupEventListeners() {
    const gameTypeSelect = document.getElementById('game-type');
    const playerNameInput = document.getElementById('player-name');
    const addPlayerBtn = document.getElementById('add-player-btn');
    const createGameBtn = document.getElementById('create-game-btn');

    // Game type change handler
    gameTypeSelect.addEventListener('change', handleGameTypeChange);

    // Player search (adapted from control.js)
    playerNameInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(searchTimeout);
        selectedSearchIndex = -1;
        selectedUser = null;

        const resultsDiv = document.getElementById('player-search-results');
        if (query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/api/wso2/users/search?q=${encodeURIComponent(query)}`, { credentials: 'include' });
                const data = await response.json();

                if (data.success && data.users && data.users.length > 0) {
                    const html = data.users.map(user => `
                        <div class="search-result-item" data-username="${user.username}" data-displayname="${(user.name || user.username).replace(/"/g, '')}">
                            <div class="search-result-name">${user.name || user.username}</div>
                            <div class="search-result-email">${user.email || user.username}</div>
                        </div>
                    `).join('');
                    resultsDiv.innerHTML = html;
                    resultsDiv.style.display = 'block';

                    // attach click handlers
                    resultsDiv.querySelectorAll('.search-result-item').forEach((item, idx) => {
                        item.addEventListener('click', function () {
                            const username = this.dataset.username;
                            const displayName = this.dataset.displayname || username;
                            selectedUser = { username, displayName };
                            document.getElementById('player-name').value = displayName;
                            resultsDiv.style.display = 'none';
                            selectedSearchIndex = -1;
                        });
                    });
                } else {
                    resultsDiv.innerHTML = '<div class="search-result-item no-results">No users found</div>';
                    resultsDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Error searching users:', error);
                resultsDiv.style.display = 'none';
            }
        }, 300);
    });

    // Keyboard navigation for search results
    playerNameInput.addEventListener('keydown', (e) => {
        const resultsDiv = document.getElementById('player-search-results');
        const results = resultsDiv ? resultsDiv.querySelectorAll('.search-result-item') : [];
        if (!results || results.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedSearchIndex = Math.min(selectedSearchIndex + 1, results.length - 1);
            updateSearchSelection(results);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedSearchIndex = Math.max(selectedSearchIndex - 1, -1);
            updateSearchSelection(results);
        } else if (e.key === 'Enter' && selectedSearchIndex >= 0) {
            e.preventDefault();
            results[selectedSearchIndex].click();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            resultsDiv.style.display = 'none';
            selectedSearchIndex = -1;
        }
    });

    // Add player button
    addPlayerBtn.addEventListener('click', addPlayer);

    // Create game button
    createGameBtn.addEventListener('click', createGame);
}

function handleGameTypeChange() {
    const gameType = document.getElementById('game-type').value;
    const hardModeContainer = document.getElementById('hard-mode-container');

    // Show hard mode option only for Round the Clock games
    if (gameType === 'round_the_clock' || gameType === 'round_the_clock_double') {
        hardModeContainer.style.display = 'block';
    } else {
        hardModeContainer.style.display = 'none';
    }
}

function handlePlayerSearch(e) {
    // legacy handler left intentionally empty; new search logic attached in setupEventListeners
}

function displaySearchResults(users) {
    const resultsDiv = document.getElementById('player-search-results');

    resultsDiv.innerHTML = users.map(user => `
        <div class="search-result-item" data-username="${user.username}" data-displayname="${user.displayName}">
            <div class="search-result-name">${user.displayName || user.username}</div>
            <div class="search-result-username">@${user.username}</div>
        </div>
    `).join('');

    resultsDiv.style.display = 'block';

    // Add click handlers to results
    resultsDiv.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function () {
            const username = this.dataset.username;
            const displayName = this.dataset.displayname;
            document.getElementById('player-name').value = displayName || username;
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'none';
        });
    });
}

function updateSearchSelection(results) {
    results.forEach((r, i) => {
        if (i === selectedSearchIndex) {
            r.classList.add('selected');
            r.scrollIntoView({ block: 'nearest' });
        } else {
            r.classList.remove('selected');
        }
    });
}

function addPlayer() {
    const playerNameInput = document.getElementById('player-name');
    const name = playerNameInput.value.trim();

    if (!name) {
        alert('Please enter a player name');
        return;
    }

    // Check for duplicates (by display name)
    if (players.some(p => p.name === name)) {
        alert('Player already added');
        return;
    }

    // If user was selected from search, store username as well
    const entry = selectedUser && selectedUser.displayName === name ? { name, username: selectedUser.username } : { name };
    players.push(entry);
    playerNameInput.value = '';
    selectedUser = null;
    selectedSearchIndex = -1;
    const resultsDiv = document.getElementById('player-search-results');
    if (resultsDiv) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
    }

    updatePlayersList();
}

function removePlayer(index) {
    players.splice(index, 1);
    updatePlayersList();
}

function updatePlayersList() {
    const playersList = document.getElementById('players-list');

    if (players.length === 0) {
        playersList.innerHTML = '<div class="empty-players">No players added yet</div>';
        return;
    }

    playersList.innerHTML = '';
    players.forEach((player, index) => {
        const item = document.createElement('div');
        item.className = 'player-item';

        const info = document.createElement('div');
        info.className = 'player-info';
        info.innerHTML = `<strong>${player.name}</strong>` + (player.username ? ` <span style="color:#666;font-size:0.9em">(@${player.username})</span>` : '');

        const actions = document.createElement('div');
        actions.className = 'player-actions';

        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn btn-danger';
        removeBtn.textContent = 'Remove';
        removeBtn.onclick = () => removePlayer(index);

        actions.appendChild(removeBtn);
        item.appendChild(info);
        item.appendChild(actions);
        playersList.appendChild(item);
    });
}

async function createGame() {
    const gameId = document.getElementById('game-id').value.trim();
    const gameType = document.getElementById('game-type').value;
    const doubleOut = document.getElementById('double-out').checked;
    const resetOnMiss = document.getElementById('reset-on-miss') ? document.getElementById('reset-on-miss').checked : false;

    if (players.length === 0) {
        alert('Please add at least one player');
        return;
    }

    const createGameBtn = document.getElementById('create-game-btn');
    createGameBtn.disabled = true;
    createGameBtn.textContent = '⏳ Creating Game...';

    try {
        // Resolve any display names to usernames where possible before creating the game.
        const resolvedPlayers = await Promise.all(players.map(async (p) => {
            if (p.username) return p.username;

            // Try to resolve via WSO2 search endpoint (may return user with username)
            try {
                const resp = await fetch(`/api/wso2/users/search?q=${encodeURIComponent(p.name)}`, { credentials: 'include' });
                const jd = await resp.json();
                if (jd && jd.success && Array.isArray(jd.users) && jd.users.length > 0) {
                    // Prefer exact display name match, then username match, otherwise first result
                    const exact = jd.users.find(u => (u.name && u.name.toLowerCase() === p.name.toLowerCase()) || (u.username && u.username.toLowerCase() === p.name.toLowerCase()));
                    const chosen = exact || jd.users[0];
                    return chosen.username || p.name;
                }
            } catch (e) {
                console.warn('Failed to resolve player name', p.name, e);
            }

            // Could not resolve, return the original name (server may accept it)
            return p.name;
        }));

        // If any resolvedPlayers entries equal their original display names and we expect usernames,
        // the server may reject them. We will attempt to detect unresolved names and warn the user.
        const unresolved = resolvedPlayers.filter((rp, idx) => rp === players[idx].name && !players[idx].username);
        if (unresolved.length > 0) {
            alert('Could not resolve these players to system usernames: ' + unresolved.join(', ') + '.\nPlease select the user from search results or enter their username.');
            createGameBtn.disabled = false;
            createGameBtn.textContent = '🚀 Create and Start Game';
            return;
        }

        // Ensure players exist in the DB by creating them if necessary (POST /api/players)
        for (const p of resolvedPlayers) {
            try {
                await fetch('/api/players', {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: p })
                });
            } catch (e) {
                console.warn('Failed to ensure player exists:', p, e);
            }
        }

        // Create the game session. Send resolved usernames (or names if already usernames).
        const createPayload = {
            game_type: gameType,
            players: resolvedPlayers,
            double_out: doubleOut,
            reset_on_miss: resetOnMiss
        };

        if (gameId) {
            createPayload.game_id = gameId;
        }

        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(createPayload)
        });
        const data = await response.json();

        if (data.success || data.status === 'success') {
            alert(`Game created successfully! Game ID: ${data.game_id}`);
            // Redirect to main game page
            window.location.href = '/';
        } else {
            alert(`Error creating game: ${data.message}`);
            createGameBtn.disabled = false;
            createGameBtn.textContent = '🚀 Create and Start Game';
        }
    } catch (error) {
        console.error('Error creating game:', error);
        alert('Failed to create game. Please try again.');
        createGameBtn.disabled = false;
        createGameBtn.textContent = '🚀 Create and Start Game';
    }
}

// Re-use the loadGameTypes function from main.js
async function loadGameTypes(selectElement) {
    try {
        const response = await fetch('/api/game/types');
        const data = await response.json();

        if (data.status === 'success' && data.game_types) {
            selectElement.innerHTML = '';

            data.game_types.forEach(gameType => {
                const option = document.createElement('option');
                option.value = gameType.name;
                option.textContent = formatGameTypeName(gameType.name);
                selectElement.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading game types:', error);
    }
}

function formatGameTypeName(name) {
    const specialNames = {
        'round_the_clock': 'Round the Clock',
        'round_the_clock_double': 'Round the Clock Double',
        'cricket': 'Cricket'
    };

    if (specialNames[name]) {
        return specialNames[name];
    }

    return name.toUpperCase();
}
