// Dashboard JavaScript
let currentGames = [];

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function () {
    // Load users list for admin filter if user is admin
    if (window.userIsAdmin) {
        loadUsersList();
    }
    loadGames();
    setupEventListeners();
});

function setupEventListeners() {
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadGames);

    // Limit select
    document.getElementById('limit-select').addEventListener('change', loadGames);

    // User select (if admin)
    if (window.userIsAdmin) {
        const userSelect = document.getElementById('user-select');
        if (userSelect) {
            userSelect.addEventListener('change', loadGames);
        }
    }

    // Modal close button
    document.querySelector('.close-btn').addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', function (event) {
        const modal = document.getElementById('game-detail-modal');
        if (event.target === modal) {
            closeModal();
        }
    });
}

function loadUsersList() {
    // Fetch list of users who have played games
    fetch('/api/players?source=database', {
        credentials: 'include'  // Include session cookies
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const userSelect = document.getElementById('user-select');
                if (userSelect) {
                    // Add users to dropdown
                    data.players.forEach(player => {
                        if (player.username) {
                            const option = document.createElement('option');
                            option.value = player.username;
                            option.textContent = player.name + ' (' + player.username + ')';
                            userSelect.appendChild(option);
                        }
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error loading users list:', error);
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

    // Build URL with parameters
    let url = `/api/game/history?limit=${limit}`;

    // Add user filter for admin
    if (window.userIsAdmin) {
        const userSelect = document.getElementById('user-select');
        if (userSelect && userSelect.value) {
            url += `&user=${encodeURIComponent(userSelect.value)}`;
        }
    }

    // Fetch games from API
    fetch(url, {
        credentials: 'include'  // Include session cookies
    })
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

    // After rendering cards, fetch replay data for each game to ensure
    // player counts and preview details match replay (fixes resumed-game mismatch).
    updateCardPreviews(games);

    // Add click event listeners to view buttons
    document.querySelectorAll('.view-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const gameSessionId = btn.getAttribute('data-session-id');
            viewGameDetails(gameSessionId);
        });
    });

    // Add click event listeners to resume buttons
    document.querySelectorAll('.resume-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const gameSessionId = btn.getAttribute('data-session-id');
            resumeGame(gameSessionId);
        });
    });

    // Add click event listeners to remove buttons
    document.querySelectorAll('.remove-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const gameSessionId = btn.getAttribute('data-session-id');
            removeGame(gameSessionId);
        });
    });

    // Add click event listeners to game cards
    document.querySelectorAll('.game-card').forEach((card) => {
        card.addEventListener('click', () => {
            const gameSessionId = card.getAttribute('data-session-id');
            viewGameDetails(gameSessionId);
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

    // Calculate game age in days for incomplete games
    const now = new Date();
    const ageInDays = (now - gameDate) / (1000 * 60 * 60 * 24);
    const isOlderThanOneDay = ageInDays >= 1;

    // Game options badges
    const optionsBadges = [];
    if (game.double_out_enabled) {
        optionsBadges.push('<span class="option-badge">🎯 Double Out</span>');
    }
    if (game.reset_on_miss) {
        optionsBadges.push('<span class="option-badge hard-mode">💀 Hard Mode</span>');
    }
    const optionsHtml = optionsBadges.length > 0
        ? `<div class="game-options">${optionsBadges.join('')}</div>`
        : '';

    // Action buttons for incomplete games
    let actionButtons = '';
    if (!isCompleted) {
        actionButtons = '<div class="game-actions">';

        // View Details button - placed above resume
        actionButtons += `
            <button class="action-btn view-btn" data-session-id="${game.game_session_id}" title="View details">
                🔍 Details
            </button>
        `;

        // Resume button - visible for incomplete games
        actionButtons += `
            <button class="action-btn resume-btn" data-session-id="${game.game_session_id}" title="Resume game">
                ▶️ Resume
            </button>
        `;

        // Remove button - only visible for games older than 1 day
        if (isOlderThanOneDay) {
            actionButtons += `
                <button class="action-btn remove-btn" data-session-id="${game.game_session_id}" title="Remove game">
                    🗑️ Remove
                </button>
            `;
        }

        actionButtons += '</div>';
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
                        <div class="detail-item detail-players">
                            <span>👥</span>
                            <span class="player-count">${game.player_count} player${game.player_count > 1 ? 's' : ''}</span>
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
                ${optionsHtml}
                ${actionButtons}
                </div>
            </div>
    `;
}

// Fetch replay data for each game card and update the DOM preview where applicable.
function updateCardPreviews(games) {
    if (!Array.isArray(games) || games.length === 0) return;

    games.forEach(game => {
        // Fire-and-forget async update per card
        (async () => {
            try {
                const resp = await fetch(`/api/game/replay/${game.game_session_id}`, {
                    credentials: 'include'
                });
                if (!resp.ok) return;
                const data = await resp.json();
                if (!data || data.status !== 'success' || !data.game_data) return;

                const replay = data.game_data;
                const card = document.querySelector(`.game-card[data-session-id="${game.game_session_id}"]`);
                if (!card) return;

                // Update player count from replay players if present
                if (Array.isArray(replay.players)) {
                    const count = replay.players.length;
                    const span = card.querySelector('.player-count');
                    if (span) {
                        span.textContent = `${count} player${count > 1 ? 's' : ''}`;
                    }
                    // Insert/update small players preview list
                    try {
                        let preview = card.querySelector('.card-players-preview');
                        if (!preview) {
                            preview = document.createElement('div');
                            preview.className = 'card-players-preview';
                            const details = card.querySelector('.game-details');
                            if (details) details.appendChild(preview);
                        }

                        // Build compact HTML for players (name and optional score)
                        const playersHtml = replay.players.map(p => {
                            const name = p.player_name || p.name || 'Unknown';
                            const score = (p.final_score !== undefined && p.final_score !== null) ? p.final_score : (p.current_score !== undefined ? p.current_score : null);
                            return score !== null ? `${name} (${score})` : name;
                        }).slice(0, 4);

                        preview.innerHTML = '<div class="preview-label">Players:</div><div class="preview-list">' + playersHtml.join('<br>') + (replay.players.length > 4 ? '<br>...' : '') + '</div>';
                    } catch (e) {
                        // ignore preview build errors
                    }
                }

                // Update winner display if available
                if (replay.players) {
                    const winner = replay.players.find(p => p.is_winner === true);
                    if (winner) {
                        const winnerBadge = card.querySelector('.winner-badge');
                        if (winnerBadge) {
                            winnerBadge.textContent = winner.player_name;
                        } else {
                            // Insert winner badge into details if not present
                            const details = card.querySelector('.game-details');
                            if (details) {
                                const div = document.createElement('div');
                                div.className = 'detail-item';
                                div.innerHTML = `<span>🏆</span><span class="winner-badge">${winner.player_name}</span>`;
                                details.appendChild(div);
                            }
                        }
                    }
                }
            } catch (e) {
                // Non-fatal: leave card as-is
                console.warn('Error updating game card preview for', game.game_session_id, e);
            }
        })();
    });
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

    // Total unique players (based on winners only, or placeholder if no winners)
    const uniquePlayers = new Set();
    games.forEach(g => {
        if (g.winner) uniquePlayers.add(g.winner);
    });
    // Show count of unique winners, or '-' if no completed games
    document.getElementById('total-players').textContent = uniquePlayers.size > 0 ? uniquePlayers.size : '-';
}

function viewGameDetails(gameSessionId) {
    const modal = document.getElementById('game-detail-modal');
    const detailContent = document.getElementById('game-detail-content');

    // Show modal with loading message
    modal.style.display = 'block';
    detailContent.innerHTML = '<p class="loading">Loading game details...</p>';

    // Fetch game replay data
    fetch(`/api/game/replay/${gameSessionId}`, {
        credentials: 'include'  // Include session cookies
    })
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
        const avgScore = throwCount > 0 ? (totalScore / throwCount).toFixed(2) : '0.00';

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

function resumeGame(gameSessionId) {
    if (!confirm('Resume this game? This will load the game state and you can continue playing.')) {
        return;
    }

    // Show loading indicator
    const btn = document.querySelector(`.resume-btn[data-session-id="${gameSessionId}"]`);
    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ Loading...';
    btn.disabled = true;

    fetch(`/api/game/resume/${gameSessionId}`, {
        method: 'POST',
        credentials: 'include'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Redirect to the game board
                window.location.href = data.redirect_url || '/';
            } else {
                alert('Failed to resume game: ' + (data.message || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            alert('Error resuming game: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function removeGame(gameSessionId) {
    if (!confirm('Are you sure you want to remove this game? This action cannot be undone.')) {
        return;
    }

    // Show loading indicator
    const btn = document.querySelector(`.remove-btn[data-session-id="${gameSessionId}"]`);
    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ Removing...';
    btn.disabled = true;

    fetch(`/api/game/${gameSessionId}`, {
        method: 'DELETE',
        credentials: 'include'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Reload the games list
                loadGames();
            } else {
                alert('Failed to remove game: ' + (data.message || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            alert('Error removing game: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}
