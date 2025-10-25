// Dashboard JavaScript
let currentGames = [];

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadGames();
    setupEventListeners();
});

function setupEventListeners() {
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadGames);
    
    // Limit select
    document.getElementById('limit-select').addEventListener('change', loadGames);
    
    // Modal close button
    document.querySelector('.close-btn').addEventListener('click', closeModal);
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('game-detail-modal');
        if (event.target === modal) {
            closeModal();
        }
    });
}

function loadGames() {
    const limit = document.getElementById('limit-select').value;
    const loadingMessage = document.getElementById('loading-message');
    const errorMessage = document.getElementById('error-message');
    const gamesList = document.getElementById('games-list');
    
    // Show loading
    loadingMessage.style.display = 'block';
    errorMessage.style.display = 'none';
    gamesList.innerHTML = '';
    
    // Fetch games from API
    fetch(`/api/game/history?limit=${limit}`)
        .then(response => response.json())
        .then(data => {
            loadingMessage.style.display = 'none';
            
            if (data.status === 'success') {
                currentGames = data.games;
                displayGames(currentGames);
                updateSummaryStats(currentGames);
            } else {
                showError('Failed to load games: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            loadingMessage.style.display = 'none';
            showError('Error loading games: ' + error.message);
        });
}

function displayGames(games) {
    const gamesList = document.getElementById('games-list');
    
    if (games.length === 0) {
        gamesList.innerHTML = '<p style="text-align: center; padding: 40px; color: #a0c4ff;">No games found</p>';
        return;
    }
    
    gamesList.innerHTML = games.map(game => createGameCard(game)).join('');
    
    // Add click event listeners to view buttons
    document.querySelectorAll('.view-btn').forEach((btn, index) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            viewGameDetails(games[index].game_session_id);
        });
    });
    
    // Add click event listeners to game cards
    document.querySelectorAll('.game-card').forEach((card, index) => {
        card.addEventListener('click', () => {
            viewGameDetails(games[index].game_session_id);
        });
    });
}

function createGameCard(game) {
    const gameDate = new Date(game.started_at);
    const finishedDate = game.finished_at ? new Date(game.finished_at) : null;
    const isCompleted = game.finished_at !== null;
    const statusClass = isCompleted ? 'status-completed' : 'status-incomplete';
    const statusText = isCompleted ? 'Completed' : 'Incomplete';
    
    // Calculate duration if finished
    let duration = '';
    if (finishedDate) {
        const durationMs = finishedDate - gameDate;
        const minutes = Math.floor(durationMs / 60000);
        const seconds = Math.floor((durationMs % 60000) / 1000);
        duration = `${minutes}m ${seconds}s`;
    }
    
    return `
        <div class="game-card" data-session-id="${game.game_session_id}">
            <div class="game-icon">🎯</div>
            <div class="game-info">
                <div class="game-header">
                    <span class="game-type">${game.game_type}</span>
                    <span class="game-date">${formatDate(gameDate)}</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="game-details">
                    <div class="detail-item">
                        <span>👥</span>
                        <span>${game.player_count} player${game.player_count > 1 ? 's' : ''}</span>
                    </div>
                    ${game.winner ? `
                        <div class="detail-item">
                            <span>🏆</span>
                            <span class="winner-badge">${game.winner}</span>
                        </div>
                    ` : ''}
                    ${duration ? `
                        <div class="detail-item">
                            <span>⏱️</span>
                            <span>${duration}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
            <button class="view-btn">View Details</button>
        </div>
    `;
}

function formatDate(date) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    };
    return date.toLocaleDateString('en-US', options);
}

function updateSummaryStats(games) {
    // Total games
    document.getElementById('total-games').textContent = games.length;
    
    // Completed games
    const completedGames = games.filter(g => g.finished_at !== null).length;
    document.getElementById('completed-games').textContent = completedGames;
    
    // Most popular game type
    const gameTypeCounts = {};
    games.forEach(g => {
        gameTypeCounts[g.game_type] = (gameTypeCounts[g.game_type] || 0) + 1;
    });
    
    let mostPopular = '-';
    let maxCount = 0;
    Object.entries(gameTypeCounts).forEach(([type, count]) => {
        if (count > maxCount) {
            maxCount = count;
            mostPopular = type;
        }
    });
    document.getElementById('popular-game').textContent = mostPopular;
    
    // Total unique players
    const uniquePlayers = new Set();
    games.forEach(g => {
        if (g.winner) uniquePlayers.add(g.winner);
    });
    document.getElementById('total-players').textContent = uniquePlayers.size || games.reduce((sum, g) => sum + g.player_count, 0);
}

function viewGameDetails(gameSessionId) {
    const modal = document.getElementById('game-detail-modal');
    const detailContent = document.getElementById('game-detail-content');
    
    // Show modal with loading message
    modal.style.display = 'block';
    detailContent.innerHTML = '<p class="loading">Loading game details...</p>';
    
    // Fetch game replay data
    fetch(`/api/game/replay/${gameSessionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayGameDetails(data.game_data);
            } else {
                detailContent.innerHTML = `<p class="error-message">Failed to load game details: ${data.message}</p>`;
            }
        })
        .catch(error => {
            detailContent.innerHTML = `<p class="error-message">Error loading game details: ${error.message}</p>`;
        });
}

function displayGameDetails(gameData) {
    const detailContent = document.getElementById('game-detail-content');
    
    const startDate = new Date(gameData.started_at);
    const finishDate = gameData.finished_at ? new Date(gameData.finished_at) : null;
    
    // Calculate statistics for each player
    const playerStats = gameData.players.map(player => {
        const playerThrows = gameData.throws.filter(t => t.player_order === player.player_order);
        
        const totalScore = playerThrows.reduce((sum, t) => sum + t.actual_score, 0);
        const throwCount = playerThrows.length;
        const avgScore = throwCount > 0 ? (totalScore / throwCount).toFixed(2) : 0;
        
        const doubles = playerThrows.filter(t => t.multiplier === 'DOUBLE').length;
        const triples = playerThrows.filter(t => t.multiplier === 'TRIPLE').length;
        const busts = playerThrows.filter(t => t.is_bust).length;
        
        return {
            ...player,
            throws: playerThrows,
            totalScore,
            throwCount,
            avgScore,
            doubles,
            triples,
            busts
        };
    });
    
    let html = `
        <div class="detail-section">
            <h3>Game Information</h3>
            <div class="game-details">
                <div class="detail-item"><strong>Game Type:</strong> ${gameData.game_type}</div>
                <div class="detail-item"><strong>Started:</strong> ${formatDate(startDate)}</div>
                ${finishDate ? `<div class="detail-item"><strong>Finished:</strong> ${formatDate(finishDate)}</div>` : ''}
                <div class="detail-item"><strong>Double Out:</strong> ${gameData.double_out_enabled ? 'Yes' : 'No'}</div>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Players & Statistics</h3>
            <div class="players-grid">
                ${playerStats.map(player => `
                    <div class="player-card">
                        <div class="player-name">
                            ${player.is_winner ? '🏆 ' : ''}${player.player_name}
                        </div>
                        <div class="player-stats">
                            <div class="stat-row">
                                <span>Start Score:</span>
                                <strong>${player.start_score || '-'}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Final Score:</span>
                                <strong>${player.final_score}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Total Throws:</span>
                                <strong>${player.throwCount}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Average Score:</span>
                                <strong>${player.avgScore}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Doubles:</span>
                                <strong>${player.doubles}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Triples:</span>
                                <strong>${player.triples}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Busts:</span>
                                <strong>${player.busts}</strong>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Throw History</h3>
            <table class="throws-table">
                <thead>
                    <tr>
                        <th>Turn</th>
                        <th>Throw</th>
                        <th>Player</th>
                        <th>Score</th>
                        <th>Multiplier</th>
                        <th>Total</th>
                        <th>Before</th>
                        <th>After</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    ${gameData.throws.map(t => {
                        let notes = [];
                        if (t.is_finish) notes.push('<span class="throw-finish">FINISH</span>');
                        if (t.is_bust) notes.push('<span class="throw-bust">BUST</span>');
                        
                        return `
                            <tr>
                                <td>${t.turn_number}</td>
                                <td>${t.throw_in_turn}</td>
                                <td>${t.player_name}</td>
                                <td>${t.base_score}</td>
                                <td>${t.multiplier}</td>
                                <td><strong>${t.actual_score}</strong></td>
                                <td>${t.score_before}</td>
                                <td>${t.score_after}</td>
                                <td>${notes.join(' ')}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    detailContent.innerHTML = html;
}

function closeModal() {
    document.getElementById('game-detail-modal').style.display = 'none';
}

function showError(message) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}
