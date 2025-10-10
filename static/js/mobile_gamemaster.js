// Mobile Gamemaster JavaScript

let socket;
let currentGame = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    loadCurrentGame();
    
    document.getElementById('newGameForm').addEventListener('submit', startNewGame);
    document.getElementById('nextPlayerBtn').addEventListener('click', nextPlayer);
    document.getElementById('endGameBtn').addEventListener('click', endGame);
});

function initializeSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to game server');
    });
    
    socket.on('game_update', (data) => {
        currentGame = data.game;
        updateGameDisplay(data.game);
    });
    
    socket.on('game_end', (data) => {
        handleGameEnd(data);
    });
}

async function loadCurrentGame() {
    try {
        const response = await apiRequest('/api/game/current');
        if (response.game) {
            currentGame = response.game;
            updateGameDisplay(response.game);
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
    const playerNames = document.getElementById('playerNames').value
        .split('\n')
        .map(name => name.trim())
        .filter(name => name.length > 0);
    
    if (playerNames.length < 2) {
        showAlert('Please enter at least 2 players', 'error');
        return;
    }
    
    try {
        const response = await apiRequest('/api/game/start', {
            method: 'POST',
            body: JSON.stringify({
                game_type: gameType,
                double_out: doubleOut,
                players: playerNames
            })
        });
        
        currentGame = response.game;
        updateGameDisplay(response.game);
        showAlert('Game started!', 'success');
        
        // Clear form
        document.getElementById('playerNames').value = '';
    } catch (error) {
        console.error('Failed to start game:', error);
        showAlert('Failed to start game: ' + error.message, 'error');
    }
}

async function nextPlayer() {
    if (!currentGame) {
        showAlert('No active game', 'error');
        return;
    }
    
    try {
        await apiRequest('/api/game/next-player', {
            method: 'POST'
        });
        showAlert('Next player', 'success');
    } catch (error) {
        console.error('Failed to advance to next player:', error);
        showAlert('Failed to advance to next player', 'error');
    }
}

async function endGame() {
    if (!currentGame) {
        showAlert('No active game', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to end the current game?')) {
        return;
    }
    
    try {
        await apiRequest('/api/game/end', {
            method: 'POST'
        });
        showAlert('Game ended', 'success');
        displayNoGame();
    } catch (error) {
        console.error('Failed to end game:', error);
        showAlert('Failed to end game', 'error');
    }
}

function updateGameDisplay(game) {
    if (!game) {
        displayNoGame();
        return;
    }
    
    displayPlayers(game.players);
    
    // Enable control buttons
    document.getElementById('nextPlayerBtn').disabled = false;
    document.getElementById('endGameBtn').disabled = false;
}

function displayNoGame() {
    currentGame = null;
    document.getElementById('playersList').innerHTML = '<p class="empty-state">No active game</p>';
    document.getElementById('nextPlayerBtn').disabled = true;
    document.getElementById('endGameBtn').disabled = true;
}

function displayPlayers(players) {
    if (!players || players.length === 0) {
        document.getElementById('playersList').innerHTML = '<p class="empty-state">No players</p>';
        return;
    }
    
    const playersHtml = players.map((player, index) => `
        <div class="item ${player.is_current ? 'active' : ''}">
            <div class="item-info">
                <div class="item-title">
                    ${player.is_current ? '▶ ' : ''}${player.name}
                </div>
                <div class="item-subtitle">Score: ${player.score}</div>
            </div>
        </div>
    `).join('');
    
    document.getElementById('playersList').innerHTML = playersHtml;
}

function handleGameEnd(data) {
    showAlert(`Game Over! Winner: ${data.winner.name}`, 'success');
    displayNoGame();
}