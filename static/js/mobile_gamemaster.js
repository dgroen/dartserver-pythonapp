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

    const gameId = document.getElementById('gameId') ? document.getElementById('gameId').value.trim() : '';
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
        // Use multi-game API
        const createPayload = {
            game_type: gameType,
            double_out: doubleOut,
            players: playerNames,
            set_as_active: true
        };
        
        if (gameId) {
            createPayload.game_id = gameId;
        }

        const response = await fetch('/api/games/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(createPayload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to start game');
        }

        const data = await response.json();
        showToast(`Game created: ${data.game_id}`, 'success');
        
        // Reload game state and games list
        loadCurrentGame();
        loadGamesList();

        // Clear form
        if (document.getElementById('gameId')) {
            document.getElementById('gameId').value = '';
        }
        document.getElementById('playerNames').value = '';
        document.getElementById('doubleOut').checked = false;
    } catch (error) {
        console.error('Failed to start game:', error);
        showToast('Failed to start game: ' + error.message, 'error');
    } finally {
        submitBtn.classList.add('loading');
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
            credentials: 'include',  // Include session cookies
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
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

// ========================================
// Multi-Game Management for Mobile
// ========================================

let gamesListRefreshInterval = null;

// Load games list on page load
document.addEventListener('DOMContentLoaded', () => {
    loadGamesList();
    
    // Refresh games list every 5 seconds
    if (gamesListRefreshInterval) {
        clearInterval(gamesListRefreshInterval);
    }
    gamesListRefreshInterval = setInterval(loadGamesList, 5000);
});

async function loadGamesList() {
    try {
        const response = await fetch('/api/games');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayGamesList(data.games, data.active_game_id);
        }
    } catch (error) {
        console.error('Error loading games list:', error);
    }
}

function displayGamesList(games, activeGameId) {
    const gamesList = document.getElementById('activeGamesList');
    if (!gamesList) return;
    
    if (!games || games.length === 0) {
        gamesList.innerHTML = '<div class="empty-state">No games available. Create one below!</div>';
        return;
    }
    
    gamesList.innerHTML = games.map(game => {
        const isActive = game.game_id === activeGameId;
        const statusClass = game.is_started ? 'started' : 'not-started';
        const statusText = game.is_started ? 'Active' : 'Not Started';
        const statusIcon = game.is_started ? '🟢' : '⚪';
        
        return `
            <div class="game-card-mobile ${isActive ? 'active' : ''}" data-game-id="${game.game_id}">
                <div class="game-card-header">
                    <div class="game-card-title">
                        ${isActive ? '▶️ ' : ''}${game.game_id}
                    </div>
                    <div class="game-card-status ${statusClass}">
                        ${statusIcon} ${statusText}
                    </div>
                </div>
                <div class="game-card-body">
                    <div class="game-card-type">${formatGameTypeName(game.game_type || 'N/A')}</div>
                    <div class="game-card-players">
                        👥 ${game.player_count} player${game.player_count !== 1 ? 's' : ''}
                        ${game.players && game.players.length > 0 ? 
                            '<div class="player-names">' + game.players.slice(0, 3).join(', ') + 
                            (game.players.length > 3 ? '...' : '') + '</div>' : ''}
                    </div>
                </div>
                ${!isActive ? '<div class="game-card-action"><button class="btn-switch-game">Switch to This Game</button></div>' : ''}
            </div>
        `;
    }).join('');
    
    // Add click handlers to switch buttons
    gamesList.querySelectorAll('.btn-switch-game').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const gameCard = this.closest('.game-card-mobile');
            const gameId = gameCard.dataset.gameId;
            switchToGame(gameId);
        });
    });
}

async function switchToGame(gameId) {
    try {
        const response = await fetch(`/api/games/${gameId}/activate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(`Switched to game: ${gameId}`, 'success');
            loadGamesList();
            loadCurrentGame();
        } else {
            showToast(`Error switching game: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error switching game:', error);
        showToast('Failed to switch game', 'error');
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
