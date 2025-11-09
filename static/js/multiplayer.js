/**
 * Multiplayer Game Page JavaScript
 * Handles player selection, game setup, and multiplayer game creation
 */

// State management
const multiplayerState = {
    selectedPlayers: new Set(),
    availablePlayers: [],
    gameType: '301',
    doubleOut: false
};

// Initialize multiplayer page
document.addEventListener('DOMContentLoaded', function() {
    initializeMultiplayerPage();
});

async function initializeMultiplayerPage() {
    // Load available players
    await loadAvailablePlayers();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load game types
    const gameTypeSelect = document.getElementById('game-type');
    if (gameTypeSelect && typeof loadGameTypes === 'function') {
        await loadGameTypes(gameTypeSelect, false);
        multiplayerState.gameType = gameTypeSelect.value || '301';
    }
}

function setupEventListeners() {
    // Game type selection
    const gameTypeSelect = document.getElementById('game-type');
    if (gameTypeSelect) {
        gameTypeSelect.addEventListener('change', function(e) {
            multiplayerState.gameType = e.target.value;
        });
    }
    
    // Double out checkbox
    const doubleOutCheckbox = document.getElementById('double-out');
    if (doubleOutCheckbox) {
        doubleOutCheckbox.addEventListener('change', function(e) {
            multiplayerState.doubleOut = e.target.checked;
        });
    }
    
    // Player search
    const playerSearchInput = document.getElementById('player-search');
    if (playerSearchInput) {
        playerSearchInput.addEventListener('input', function(e) {
            filterPlayers(e.target.value);
        });
    }
    
    // Start game button
    const startGameButton = document.getElementById('start-multiplayer-game');
    if (startGameButton) {
        startGameButton.addEventListener('click', startMultiplayerGame);
    }
}

async function loadAvailablePlayers() {
    try {
        const response = await fetch('/api/multiplayer/available-players');
        const data = await response.json();
        
        if (data.success) {
            multiplayerState.availablePlayers = data.players;
            renderAvailablePlayers(data.players);
        } else {
            showError('Failed to load available players: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error loading available players:', error);
        showError('Failed to load available players');
    }
}

function renderAvailablePlayers(players) {
    const container = document.getElementById('available-players-list');
    if (!container) return;
    
    if (!players || players.length === 0) {
        container.innerHTML = '<p class="empty-state">No available players found</p>';
        return;
    }
    
    container.innerHTML = players.map(player => {
        const isSelected = multiplayerState.selectedPlayers.has(player.username);
        const isInGame = player.inActiveGame;
        
        return `
            <div class="player-card ${isSelected ? 'selected' : ''} ${isInGame ? 'in-game' : ''}"
                 data-username="${player.username}"
                 onclick="togglePlayerSelection('${player.username}', ${isInGame})">
                <div class="player-name">${player.name || player.username}</div>
                <div class="player-username">@${player.username}</div>
                <div class="player-status ${isInGame ? 'offline' : ''}">${isInGame ? '🎮 In Game' : '✅ Available'}</div>
            </div>
        `;
    }).join('');
}

function filterPlayers(searchTerm) {
    const filtered = multiplayerState.availablePlayers.filter(player => {
        const term = searchTerm.toLowerCase();
        return (
            player.username.toLowerCase().includes(term) ||
            (player.name && player.name.toLowerCase().includes(term))
        );
    });
    
    renderAvailablePlayers(filtered);
}

function togglePlayerSelection(username, isInGame) {
    // Don't allow selection of players in active games
    if (isInGame) {
        return;
    }
    
    if (multiplayerState.selectedPlayers.has(username)) {
        multiplayerState.selectedPlayers.delete(username);
    } else {
        multiplayerState.selectedPlayers.add(username);
    }
    
    updateUI();
}

function updateUI() {
    // Update available players list
    renderAvailablePlayers(multiplayerState.availablePlayers);
    
    // Update selected players list
    renderSelectedPlayers();
    
    // Update start game button state
    updateStartGameButton();
}

function renderSelectedPlayers() {
    const container = document.getElementById('selected-players-list');
    if (!container) return;
    
    if (multiplayerState.selectedPlayers.size === 0) {
        container.innerHTML = '<p class="empty-state">No players selected yet</p>';
        return;
    }
    
    const selectedPlayersArray = Array.from(multiplayerState.selectedPlayers);
    container.innerHTML = selectedPlayersArray.map(username => {
        const player = multiplayerState.availablePlayers.find(p => p.username === username);
        const displayName = player ? (player.name || username) : username;
        
        return `
            <div class="selected-player-chip">
                <span>${displayName}</span>
                <button class="remove-btn" onclick="removePlayerSelection('${username}')">×</button>
            </div>
        `;
    }).join('');
}

function removePlayerSelection(username) {
    multiplayerState.selectedPlayers.delete(username);
    updateUI();
}

function updateStartGameButton() {
    const button = document.getElementById('start-multiplayer-game');
    if (!button) return;
    
    const minPlayers = 1;
    const hasEnoughPlayers = multiplayerState.selectedPlayers.size >= minPlayers;
    
    button.disabled = !hasEnoughPlayers;
    
    if (hasEnoughPlayers) {
        button.textContent = `Start Game with ${multiplayerState.selectedPlayers.size} Player${multiplayerState.selectedPlayers.size > 1 ? 's' : ''}`;
    } else {
        button.textContent = `Select at least ${minPlayers} player to start`;
    }
}

async function startMultiplayerGame() {
    if (multiplayerState.selectedPlayers.size < 1) {
        showError('Please select at least one player');
        return;
    }
    
    const button = document.getElementById('start-multiplayer-game');
    if (button) {
        button.disabled = true;
        button.textContent = 'Starting game...';
    }
    
    try {
        // Get player names in order
        const playerNames = Array.from(multiplayerState.selectedPlayers);
        
        // Create the game via Socket.IO
        if (typeof socket !== 'undefined') {
            socket.emit('new_game', {
                game_type: multiplayerState.gameType,
                player_names: playerNames,
                double_out: multiplayerState.doubleOut
            });
            
            // Listen for game creation response
            socket.once('game_state', function(state) {
                if (state && state.players && state.players.length > 0) {
                    // Game created successfully, redirect to main game page
                    window.location.href = '/';
                } else {
                    showError('Failed to create game');
                    if (button) {
                        button.disabled = false;
                        updateStartGameButton();
                    }
                }
            });
        } else {
            showError('Socket connection not available');
            if (button) {
                button.disabled = false;
                updateStartGameButton();
            }
        }
    } catch (error) {
        console.error('Error starting multiplayer game:', error);
        showError('Failed to start game: ' + error.message);
        if (button) {
            button.disabled = false;
            updateStartGameButton();
        }
    }
}

function showError(message) {
    console.error(message);
    // Display error to user (could be improved with a toast notification)
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert-message error';
    alertDiv.textContent = message;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.background = 'rgba(255, 0, 0, 0.9)';
    alertDiv.style.color = 'white';
    alertDiv.style.padding = '15px 20px';
    alertDiv.style.borderRadius = '5px';
    alertDiv.style.zIndex = '10000';
    alertDiv.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.3)';
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
