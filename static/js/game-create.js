// Game Creation Page JavaScript

let players = [];
let selectedUsers = new Set();
let searchTimeout = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    await loadGameTypes(document.getElementById('game-type'));
    setupEventListeners();
    handleGameTypeChange(); // Initialize hard mode visibility
});

function setupEventListeners() {
    const gameTypeSelect = document.getElementById('game-type');
    const playerNameInput = document.getElementById('player-name');
    const addPlayerBtn = document.getElementById('add-player-btn');
    const createGameBtn = document.getElementById('create-game-btn');

    // Game type change handler
    gameTypeSelect.addEventListener('change', handleGameTypeChange);

    // Player search
    playerNameInput.addEventListener('input', handlePlayerSearch);
    playerNameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addPlayer();
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

async function handlePlayerSearch(e) {
    const query = e.target.value.trim();
    const resultsDiv = document.getElementById('player-search-results');
    
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Hide results if query is empty
    if (!query) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        return;
    }
    
    // Debounce search
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/wso2/users/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.users && data.users.length > 0) {
                displaySearchResults(data.users);
            } else {
                resultsDiv.innerHTML = '<div class="search-result-item no-results">No users found</div>';
                resultsDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }, 300);
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
        item.addEventListener('click', function() {
            const username = this.dataset.username;
            const displayName = this.dataset.displayname;
            document.getElementById('player-name').value = displayName || username;
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'none';
        });
    });
}

function addPlayer() {
    const playerNameInput = document.getElementById('player-name');
    const playerName = playerNameInput.value.trim();
    
    if (!playerName) {
        alert('Please enter a player name');
        return;
    }
    
    // Check for duplicates
    if (players.includes(playerName)) {
        alert('Player already added');
        return;
    }
    
    players.push(playerName);
    playerNameInput.value = '';
    document.getElementById('player-search-results').innerHTML = '';
    document.getElementById('player-search-results').style.display = 'none';
    
    updatePlayersList();
}

function removePlayer(index) {
    players.splice(index, 1);
    updatePlayersList();
}

function updatePlayersList() {
    const playersList = document.getElementById('players-list');
    
    if (players.length === 0) {
        playersList.innerHTML = '<p style="color: rgba(255,255,255,0.5); font-style: italic;">No players added yet</p>';
        return;
    }
    
    playersList.innerHTML = players.map((player, index) => `
        <div class="player-item">
            <span class="player-name">${player}</span>
            <button class="btn btn-danger btn-sm" onclick="removePlayer(${index})">Remove</button>
        </div>
    `).join('');
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
        // Create the game session
        const createPayload = {
            game_type: gameType,
            players: players,
            double_out: doubleOut,
            reset_on_miss: resetOnMiss,
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
            body: JSON.stringify(createPayload)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
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
