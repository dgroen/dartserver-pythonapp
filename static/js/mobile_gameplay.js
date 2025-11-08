// Mobile Gameplay JavaScript

let socket;
let currentGame = null;
let currentUser = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    loadCurrentUser();
    loadCurrentGame();
    loadActiveGames();

    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Next Player button handler
    document.getElementById('nextPlayerButton').addEventListener('click', () => {
        handleNextPlayerClick();
    });
});

// Helper function for API requests
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: 'include',  // Include session cookies
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    if (!response.ok && response.status === 401) {
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    return response.json();
}

// Load current user information
async function loadCurrentUser() {
    try {
        const response = await apiRequest('/api/user/current');
        if (response.success) {
            currentUser = response;
            console.log('Current user loaded:', currentUser);
        }
    } catch (error) {
        console.error('Failed to load current user:', error);
    }
}

// Handle Next Player button click
function handleNextPlayerClick() {
    console.log('Button clicked!');
    console.log('currentGame:', currentGame);
    
    if (!socket || !currentGame) {
        console.error('Cannot continue: no active game or socket connection');
        return;
    }

    console.log('Game is_paused:', currentGame.is_paused);
    
    // If game is paused (waiting for continue), just emit next_player
    if (currentGame.is_paused) {
        console.log('Emitting next_player event');
        socket.emit('next_player');
        return;
    }

    // Game is active - end turn early (record remaining throws as misses)
    // For single-player games, skip confirmation
    const isSinglePlayer = currentGame.players && currentGame.players.length === 1;
    
    console.log('Game is active, ending turn early. Single player:', isSinglePlayer);
    
    if (isSinglePlayer) {
        socket.emit('end_turn_early');
    } else {
        // Confirm action for multi-player games
        if (confirm('End your turn early? Any remaining throws will be recorded as misses.')) {
            socket.emit('end_turn_early');
        }
    }
}

// Tab switching functionality
function switchTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    // Reload data if needed
    if (tabName === 'active-games') {
        loadActiveGames();
    }
}

function initializeSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to game server');
    });

    socket.on('game_update', (data) => {
        updateGameDisplay(data);
    });

    socket.on('score_update', (data) => {
        updateScoreDisplay(data);
    });

    socket.on('player_change', (data) => {
        updateCurrentPlayer(data);
    });

    socket.on('game_state', (data) => {
        handleGameState(data);
    });

    socket.on('game_end', (data) => {
        handleGameEnd(data);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from game server');
    });
}

async function loadCurrentGame() {
    try {
        const response = await apiRequest('/api/game/current');
        if (response.game) {
            currentGame = response.game;
            displayGame(response.game);
        } else {
            displayNoGame();
        }
    } catch (error) {
        console.error('Failed to load current game:', error);
        displayNoGame();
    }
}

// Load active games
async function loadActiveGames() {
    try {
        const response = await apiRequest('/api/active-games');
        if (response.success && response.games) {
            displayActiveGames(response.games);
        } else {
            document.getElementById('activeGamesList').innerHTML = `
                <p class="empty-state">No active games</p>
            `;
        }
    } catch (error) {
        console.error('Failed to load active games:', error);
        document.getElementById('activeGamesList').innerHTML = `
            <p class="empty-state">Failed to load active games</p>
        `;
    }
}

// Display active games
function displayActiveGames(games) {
    const container = document.getElementById('activeGamesList');

    if (!games || games.length === 0) {
        container.innerHTML = '<p class="empty-state">No active games right now</p>';
        return;
    }

    const gamesHtml = games.map(game => {
        const startDate = new Date(game.started_at);
        const timeAgo = formatTimeAgo(startDate);

        const leaderboardHtml = game.players
            .sort((a, b) => (b.current_score || 0) - (a.current_score || 0))
            .map((player, index) => `
                <div class="leaderboard-row">
                    <span class="leaderboard-position">${index + 1}.</span>
                    <span class="leaderboard-name">${player.player_name}</span>
                    <span class="leaderboard-score">${player.current_score}</span>
                </div>
            `)
            .join('');

        return `
            <div class="result-card">
                <div class="result-header">
                    <span class="result-type">${game.game_type}</span>
                    <span class="result-date">Started ${timeAgo}</span>
                </div>
                <div class="leaderboard-section">
                    <div class="leaderboard-title">Current Standings (${game.player_count} players)</div>
                    ${leaderboardHtml}
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = gamesHtml;
}

function displayGame(game) {
    document.getElementById('gameStatus').innerHTML = `
        <div class="status-badge status-active">${game.game_type} - In Progress</div>
    `;

    if (game.current_player) {
        document.getElementById('currentPlayerCard').style.display = 'block';
        document.getElementById('currentPlayerName').textContent = game.current_player.name;
        document.getElementById('currentPlayerScore').textContent = game.current_player.score;
    }

    // Show or hide Next Player button based on user role and current player
    updateNextPlayerButton(game);

    displayScoreboard(game.players);
}

function displayNoGame() {
    document.getElementById('gameStatus').innerHTML = `
        <div class="status-badge">No Active Game</div>
    `;
    document.getElementById('currentPlayerCard').style.display = 'none';
    document.getElementById('nextPlayerButtonContainer').style.display = 'none';
    document.getElementById('scoreboardContent').innerHTML = `
        <p class="empty-state">Start a game to see scores</p>
    `;
}

// Update visibility of Next Player button based on user role and current player
function updateNextPlayerButton(game) {
    const buttonContainer = document.getElementById('nextPlayerButtonContainer');
    const nextPlayerBtn = document.getElementById('nextPlayerButton');
    const buttonHint = document.getElementById('buttonHint');
    
    // Don't show button if no game or no user info
    if (!game || !currentUser || !game.is_started) {
        buttonContainer.style.display = 'none';
        return;
    }

    // Show button if user is gamemaster (always)
    const isGamemaster = currentUser.roles && currentUser.roles.includes('gamemaster');
    if (isGamemaster) {
        buttonContainer.style.display = 'block';
        updateButtonText(game, nextPlayerBtn, buttonHint);
        return;
    }

    // Show button if user is the current player
    const currentPlayerIndex = game.current_player;
    if (currentPlayerIndex !== undefined && game.players && game.players[currentPlayerIndex]) {
        const currentPlayerDbId = game.players[currentPlayerIndex].db_id;
        const userPlayerId = currentUser.player_id;
        
        if (currentPlayerDbId && userPlayerId && currentPlayerDbId === userPlayerId) {
            buttonContainer.style.display = 'block';
            updateButtonText(game, nextPlayerBtn, buttonHint);
            return;
        }
    }

    // Hide button otherwise
    buttonContainer.style.display = 'none';
}

// Update button text based on game state
function updateButtonText(game, buttonElement, hintElement) {
    if (!buttonElement) return;
    
    if (game.is_paused) {
        // Game is paused - button continues to next player
        buttonElement.textContent = '▶️ Continue Game';
        if (hintElement) {
            hintElement.textContent = 'Continue to next player';
        }
    } else {
        // Game is active - button ends turn early
        buttonElement.textContent = '⏭️ End Turn Early';
        if (hintElement) {
            hintElement.textContent = 'Skip remaining throws (records as misses)';
        }
    }
}

function displayScoreboard(players) {
    if (!players || players.length === 0) {
        document.getElementById('scoreboardContent').innerHTML = `
            <p class="empty-state">No players</p>
        `;
        return;
    }

    const scoreboardHtml = players.map((player, index) => `
        <div class="score-row ${player.is_current ? 'active' : ''}">
            <span>${index + 1}. ${player.name}</span>
            <span>${player.score}</span>
        </div>
    `).join('');

    document.getElementById('scoreboardContent').innerHTML = scoreboardHtml;
}

function updateGameDisplay(data) {
    currentGame = data.game;
    displayGame(data.game);
}

function updateScoreDisplay(data) {
    if (data.throw) {
        document.getElementById('lastThrow').style.display = 'block';
        document.getElementById('throwDisplay').textContent = formatThrow(data.throw);
    }

    if (currentGame) {
        displayScoreboard(data.players || currentGame.players);
        // Update button visibility in case throw count changed
        updateNextPlayerButton(currentGame);
    }
}

function updateCurrentPlayer(data) {
    document.getElementById('currentPlayerName').textContent = data.player.name;
    document.getElementById('currentPlayerScore').textContent = data.player.score;

    if (currentGame) {
        displayScoreboard(data.players || currentGame.players);
        // Update button visibility for new current player
        updateNextPlayerButton(currentGame);
    }
}

function handleGameState(data) {
    // Update current game state
    currentGame = data;
    
    // Handle game state updates which may include throwout advice
    if (data.throwout_advice) {
        displayThrowoutAdvice(data.throwout_advice);
    } else {
        hideThrowoutAdvice();
    }
    
    // Update button visibility
    updateNextPlayerButton(data);
}

function displayThrowoutAdvice(advice) {
    const adviceElement = document.getElementById('throwoutAdvice');
    const adviceDisplay = document.getElementById('adviceDisplay');

    if (Array.isArray(advice) && advice.length > 0) {
        adviceDisplay.textContent = advice.join(' or ');
        adviceElement.style.display = 'block';
    } else {
        adviceElement.style.display = 'none';
    }
}

function hideThrowoutAdvice() {
    const adviceElement = document.getElementById('throwoutAdvice');
    adviceElement.style.display = 'none';
}

function handleGameEnd(data) {
    console.log('Game ended');

    setTimeout(() => {
        loadCurrentGame();
    }, 3000);
}

function formatThrow(throwData) {
    if (typeof throwData === 'string') {
        return throwData;
    }

    if (throwData.multiplier && throwData.value) {
        const multiplierText = throwData.multiplier === 2 ? 'Double' : throwData.multiplier === 3 ? 'Triple' : '';
        return `${multiplierText} ${throwData.value}`;
    }

    return throwData.score || '-';
}

// Format time ago
function formatTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) {
        return 'just now';
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m ago`;
    } else if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        return `${hours}h ago`;
    } else {
        return date.toLocaleDateString();
    }
}
