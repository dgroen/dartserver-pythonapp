// Connect to SocketIO
const socket = io();

// DOM Elements
const gameTypeSelect = document.getElementById('game-type');
const newGameBtn = document.getElementById('new-game-btn');
const playersList = document.getElementById('players-list');
const playerNameInput = document.getElementById('player-name');
const addPlayerBtn = document.getElementById('add-player-btn');
const nextPlayerBtn = document.getElementById('next-player-btn');
const pauseBtn = document.getElementById('pause-btn');
const scoreValueInput = document.getElementById('score-value');
const multiplierSelect = document.getElementById('multiplier');
const submitScoreBtn = document.getElementById('submit-score-btn');
const gameStateJson = document.getElementById('game-state-json');

let currentGameState = null;

// Initialize
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Game state update
socket.on('game_state', (state) => {
    console.log('Game state:', state);
    currentGameState = state;
    updateDisplay(state);
});

// Event Listeners
newGameBtn.addEventListener('click', () => {
    const gameType = gameTypeSelect.value;
    const playerNames = [];
    
    // Get player names from the list
    const playerItems = playersList.querySelectorAll('.player-item');
    playerItems.forEach(item => {
        const name = item.querySelector('.player-info').textContent.split(':')[1].trim();
        playerNames.push(name);
    });
    
    // If no players, use defaults
    if (playerNames.length === 0) {
        playerNames.push('Player 1', 'Player 2');
    }
    
    socket.emit('new_game', {
        game_type: gameType,
        players: playerNames
    });
});

addPlayerBtn.addEventListener('click', () => {
    const name = playerNameInput.value.trim();
    if (name) {
        socket.emit('add_player', { name: name });
        playerNameInput.value = '';
    } else {
        socket.emit('add_player', {});
    }
});

nextPlayerBtn.addEventListener('click', () => {
    socket.emit('next_player');
});

pauseBtn.addEventListener('click', () => {
    // Toggle pause state
    // This would need to be implemented in the backend
    console.log('Pause/Resume clicked');
});

submitScoreBtn.addEventListener('click', () => {
    const score = parseInt(scoreValueInput.value);
    const multiplier = multiplierSelect.value;
    
    if (isNaN(score) || score < 0) {
        alert('Please enter a valid score');
        return;
    }
    
    socket.emit('manual_score', {
        score: score,
        multiplier: multiplier
    });
});

// Allow Enter key to add player
playerNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addPlayerBtn.click();
    }
});

// Allow Enter key to submit score
scoreValueInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        submitScoreBtn.click();
    }
});

function updateDisplay(state) {
    // Update players list
    updatePlayersList(state);
    
    // Update game state JSON
    gameStateJson.textContent = JSON.stringify(state, null, 2);
}

function updatePlayersList(state) {
    playersList.innerHTML = '';
    
    if (state.players && state.players.length > 0) {
        state.players.forEach((player, index) => {
            const playerItem = document.createElement('div');
            playerItem.className = 'player-item';
            
            if (index === state.current_player && state.is_started) {
                playerItem.classList.add('active');
            }
            
            const playerInfo = document.createElement('div');
            playerInfo.className = 'player-info';
            
            let score = 0;
            if (state.game_data && state.game_data.players && state.game_data.players[index]) {
                score = state.game_data.players[index].score;
            }
            
            playerInfo.innerHTML = `
                <strong>${player.name}</strong>: ${score}
            `;
            
            const playerActions = document.createElement('div');
            playerActions.className = 'player-actions';
            
            const skipBtn = document.createElement('button');
            skipBtn.className = 'btn btn-secondary';
            skipBtn.textContent = 'Skip To';
            skipBtn.style.marginRight = '5px';
            skipBtn.onclick = () => {
                socket.emit('skip_to_player', { player_id: index });
            };
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-danger';
            removeBtn.textContent = 'Remove';
            removeBtn.onclick = () => {
                if (confirm(`Remove ${player.name}?`)) {
                    socket.emit('remove_player', { player_id: index });
                }
            };
            
            playerActions.appendChild(skipBtn);
            playerActions.appendChild(removeBtn);
            
            playerItem.appendChild(playerInfo);
            playerItem.appendChild(playerActions);
            
            playersList.appendChild(playerItem);
        });
    } else {
        playersList.innerHTML = '<p>No players yet. Add players to start a game.</p>';
    }
}

// Quick score buttons (optional enhancement)
const quickScores = [20, 40, 60, 26, 41, 45, 60, 81, 100, 140, 180];
const quickScoresContainer = document.createElement('div');
quickScoresContainer.style.marginTop = '10px';
quickScoresContainer.style.display = 'flex';
quickScoresContainer.style.flexWrap = 'wrap';
quickScoresContainer.style.gap = '5px';

quickScores.forEach(score => {
    const btn = document.createElement('button');
    btn.className = 'btn btn-secondary';
    btn.textContent = score;
    btn.style.padding = '5px 10px';
    btn.style.fontSize = '0.9em';
    btn.onclick = () => {
        scoreValueInput.value = score;
    };
    quickScoresContainer.appendChild(btn);
});

// Add quick scores to manual score section
const manualScoreSection = document.querySelector('.control-section:nth-child(4)');
if (manualScoreSection) {
    manualScoreSection.appendChild(quickScoresContainer);
}