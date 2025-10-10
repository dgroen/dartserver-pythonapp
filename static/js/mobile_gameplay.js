// Mobile Gameplay JavaScript

let socket;
let currentGame = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    loadCurrentGame();
});

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
        showAlert('Connection lost. Reconnecting...', 'error');
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
    showAlert(`Game Over! Winner: ${data.winner.name}`, 'success');

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
