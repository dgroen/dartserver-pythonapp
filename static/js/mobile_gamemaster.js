// Mobile Gamemaster JavaScript

let socket;
let currentGame = null;
let isPaused = false;

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    loadCurrentGame();
    setupEventListeners();
});

function setupEventListeners() {
    // Form submissions
    document.getElementById('newGameForm').addEventListener('submit', startNewGame);
    document.getElementById('manualScoreForm').addEventListener('submit', submitManualScore);

    // Button clicks
    document.getElementById('nextPlayerBtn').addEventListener('click', nextPlayer);
    document.getElementById('pauseBtn').addEventListener('click', togglePause);
    document.getElementById('endGameBtn').addEventListener('click', endGame);
    document.getElementById('addPlayerBtn').addEventListener('click', addPlayer);
    document.getElementById('refreshStateBtn').addEventListener('click', refreshGameState);
}

function initializeSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ Connected to game server');
        showToast('Connected to server', 'success');
    });

    socket.on('disconnect', () => {
        console.log('❌ Disconnected from game server');
        showToast('Disconnected from server', 'warning');
    });

    socket.on('game_update', (data) => {
        console.log('📡 Game update received:', data);
        currentGame = data.game;
        updateGameDisplay(data.game);
    });

    socket.on('game_started', (data) => {
        console.log('🎮 Game started:', data);
        currentGame = data.game;
        updateGameDisplay(data.game);
        showToast('Game started!', 'success');
    });

    socket.on('game_end', (data) => {
        console.log('🏁 Game ended:', data);
        handleGameEnd(data);
    });

    socket.on('score_update', (data) => {
        console.log('📊 Score update:', data);
        if (currentGame) {
            loadCurrentGame(); // Refresh game state
        }
    });

    socket.on('player_added', (data) => {
        console.log('👤 Player added:', data);
        showToast(`Player "${data.player_name}" added successfully`, 'success');
        loadCurrentGame();
    });

    socket.on('player_removed', (data) => {
        console.log('👤 Player removed:', data);
        showToast(`Player removed`, 'info');
        loadCurrentGame();
    });

    socket.on('error', (error) => {
        console.error('❌ Socket error:', error);
        showToast(error.message || 'An error occurred', 'error');
    });
}

async function loadCurrentGame() {
    try {
        const response = await fetch('/api/game/current', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.game && Object.keys(data.game).length > 0) {
            currentGame = data.game;
            updateGameDisplay(data.game);
        } else {
            displayNoGame();
        }
    } catch (error) {
        console.error('Failed to load current game:', error);
        displayNoGame();
    }
}

async function startNewGame(e) {
    e.preventDefault();

    const gameType = document.getElementById('gameType').value;
    const doubleOut = document.getElementById('doubleOut').checked;
    const playerNamesText = document.getElementById('playerNames').value;

    const playerNames = playerNamesText
        .split('\n')
        .map(name => name.trim())
        .filter(name => name.length > 0);

    if (playerNames.length < 1) {
        showToast('Please enter at least 1 player', 'error');
        return;
    }

    // Show loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                game_type: gameType,
                double_out: doubleOut,
                players: playerNames
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to start game');
        }

        const data = await response.json();
        currentGame = data.game;
        updateGameDisplay(data.game);
        showToast('Game started successfully!', 'success');

        // Clear form
        document.getElementById('playerNames').value = '';
        document.getElementById('doubleOut').checked = false;
    } catch (error) {
        console.error('Failed to start game:', error);
        showToast('Failed to start game: ' + error.message, 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

function nextPlayer() {
    if (!currentGame) {
        showToast('No active game', 'error');
        return;
    }

    if (!socket || !socket.connected) {
        showToast('Not connected to server', 'error');
        return;
    }

    try {
        socket.emit('next_player');
        showToast('Moving to next player...', 'info');
    } catch (error) {
        console.error('Failed to advance to next player:', error);
        showToast('Failed to advance to next player', 'error');
    }
}

async function togglePause() {
    if (!currentGame) {
        showToast('No active game', 'error');
        return;
    }

    isPaused = !isPaused;
    const pauseBtn = document.getElementById('pauseBtn');
    const icon = pauseBtn.querySelector('.btn-icon');

    if (isPaused) {
        icon.textContent = '▶️';
        pauseBtn.innerHTML = '<span class="btn-icon">▶️</span>Resume Game';
        showToast('Game paused', 'info');
    } else {
        icon.textContent = '⏸️';
        pauseBtn.innerHTML = '<span class="btn-icon">⏸️</span>Pause Game';
        showToast('Game resumed', 'info');
    }

    // TODO: Implement actual pause/resume API call if backend supports it
}

async function endGame() {
    if (!currentGame) {
        showToast('No active game', 'error');
        return;
    }

    if (!confirm('Are you sure you want to end the current game?')) {
        return;
    }

    try {
        const response = await fetch('/api/game/end', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to end game');
        }

        showToast('Game ended successfully', 'success');
        displayNoGame();
    } catch (error) {
        console.error('Failed to end game:', error);
        showToast('Failed to end game: ' + error.message, 'error');
    }
}

function addPlayer() {
    if (!currentGame) {
        showToast('No active game', 'error');
        return;
    }

    if (!socket || !socket.connected) {
        showToast('Not connected to server', 'error');
        return;
    }

    const playerName = document.getElementById('newPlayerName').value.trim();

    if (!playerName) {
        showToast('Please enter a player name', 'error');
        return;
    }

    try {
        socket.emit('add_player', {
            player_name: playerName
        });

        showToast(`Adding player "${playerName}"...`, 'info');
        document.getElementById('newPlayerName').value = '';
    } catch (error) {
        console.error('Failed to add player:', error);
        showToast('Failed to add player: ' + error.message, 'error');
    }
}

function submitManualScore(e) {
    e.preventDefault();

    if (!currentGame) {
        showToast('No active game', 'error');
        return;
    }

    if (!socket || !socket.connected) {
        showToast('Not connected to server', 'error');
        return;
    }

    const scoreValue = parseInt(document.getElementById('scoreValue').value);
    const multiplier = document.getElementById('multiplier').value;

    if (isNaN(scoreValue) || scoreValue < 0) {
        showToast('Invalid score value', 'error');
        return;
    }

    try {
        // Emit manual score via WebSocket
        socket.emit('manual_score', {
            score: scoreValue,
            multiplier: multiplier,
            timestamp: new Date().toISOString()
        });

        showToast(`Score submitted: ${scoreValue} (${multiplier})`, 'success');
    } catch (error) {
        console.error('Failed to submit score:', error);
        showToast('Failed to submit score: ' + error.message, 'error');
    }
}

async function refreshGameState() {
    const refreshBtn = document.getElementById('refreshStateBtn');
    refreshBtn.classList.add('loading');
    refreshBtn.disabled = true;

    try {
        await loadCurrentGame();
        showToast('Game state refreshed', 'success');
    } catch (error) {
        showToast('Failed to refresh game state', 'error');
    } finally {
        refreshBtn.classList.remove('loading');
        refreshBtn.disabled = false;
    }
}

function updateGameDisplay(game) {
    if (!game || Object.keys(game).length === 0) {
        displayNoGame();
        return;
    }

    // Update status card
    const statusDot = document.getElementById('gameStatusDot');
    const statusText = document.getElementById('gameStatusText');
    const gameInfo = document.getElementById('gameInfo');
    const gameTypeDisplay = document.getElementById('gameTypeDisplay');
    const currentPlayerDisplay = document.getElementById('currentPlayerDisplay');

    statusDot.className = 'status-dot online';
    statusText.textContent = 'Game in progress';
    gameInfo.style.display = 'block';
    gameTypeDisplay.textContent = game.game_type || 'Unknown';

    // Find current player
    const currentPlayer = game.players?.find(p => p.is_current);
    currentPlayerDisplay.textContent = currentPlayer ? currentPlayer.name : 'Unknown';

    // Display players
    displayPlayers(game.players);

    // Update game state JSON
    document.getElementById('gameStateJson').textContent = JSON.stringify(game, null, 2);

    // Enable control buttons
    document.getElementById('nextPlayerBtn').disabled = false;
    document.getElementById('pauseBtn').disabled = false;
    document.getElementById('endGameBtn').disabled = false;
    document.getElementById('submitScoreBtn').disabled = false;

    // Show add player section
    document.getElementById('addPlayerSection').style.display = 'block';
}

function displayNoGame() {
    currentGame = null;

    // Update status card
    const statusDot = document.getElementById('gameStatusDot');
    const statusText = document.getElementById('gameStatusText');
    const gameInfo = document.getElementById('gameInfo');

    statusDot.className = 'status-dot offline';
    statusText.textContent = 'No active game';
    gameInfo.style.display = 'none';

    // Clear players list
    document.getElementById('playersList').innerHTML = '<p class="empty-state">No active game</p>';

    // Update game state JSON
    document.getElementById('gameStateJson').textContent = 'No game data';

    // Disable control buttons
    document.getElementById('nextPlayerBtn').disabled = true;
    document.getElementById('pauseBtn').disabled = true;
    document.getElementById('endGameBtn').disabled = true;
    document.getElementById('submitScoreBtn').disabled = true;

    // Hide add player section
    document.getElementById('addPlayerSection').style.display = 'none';
}

function displayPlayers(players) {
    const playersList = document.getElementById('playersList');

    if (!players || players.length === 0) {
        playersList.innerHTML = '<p class="empty-state">No players</p>';
        return;
    }

    const playersHtml = players.map((player, index) => `
        <div class="player-item ${player.is_current ? 'active' : ''}">
            <div class="player-info">
                <div class="player-name">${player.name}</div>
                <div class="player-score">Score: ${player.score !== undefined ? player.score : 'N/A'}</div>
            </div>
        </div>
    `).join('');

    playersList.innerHTML = playersHtml;
}

function handleGameEnd(data) {
    const winner = data.winner || data.game?.winner;
    const winnerName = winner?.name || 'Unknown';

    showToast(`🏆 Game Over! Winner: ${winnerName}`, 'success');

    setTimeout(() => {
        displayNoGame();
    }, 2000);
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;

    // Trigger reflow to restart animation
    void toast.offsetWidth;

    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Helper function for API requests (fallback if not in mobile.js)
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}
