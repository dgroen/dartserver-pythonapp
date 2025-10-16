// Mobile Gameplay JavaScript

let socket;
let currentGame = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    loadCurrentGame();
    loadActiveGames();

    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
});

// Helper function for API requests
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
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

    displayScoreboard(game.players);
}

function displayNoGame() {
    document.getElementById('gameStatus').innerHTML = `
        <div class="status-badge">No Active Game</div>
    `;
    document.getElementById('currentPlayerCard').style.display = 'none';
    document.getElementById('scoreboardContent').innerHTML = `
        <p class="empty-state">Start a game to see scores</p>
    `;
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
    }
}

function updateCurrentPlayer(data) {
    document.getElementById('currentPlayerName').textContent = data.player.name;
    document.getElementById('currentPlayerScore').textContent = data.player.score;

    if (currentGame) {
        displayScoreboard(data.players || currentGame.players);
    }
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
