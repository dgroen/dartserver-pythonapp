// Mobile Results JavaScript

let allResults = [];
let filteredResults = [];
let playerStats = {};

document.addEventListener('DOMContentLoaded', () => {
    // Load initial data
    loadPlayerHistory();
    loadPlayerStatistics();
    loadActiveGames();

    // Filter change event
    document.getElementById('gameTypeFilter').addEventListener('change', filterResults);

    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
});

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
    if (tabName === 'active') {
        loadActiveGames();
    }
}

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

// Load player statistics
async function loadPlayerStatistics() {
    try {
        const response = await apiRequest('/api/player/statistics');
        if (response.success && response.statistics) {
            playerStats = response.statistics;
            updateStatBadges();
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// Update stat badges
function updateStatBadges() {
    const container = document.getElementById('statBadges');
    if (!container) return;

    container.innerHTML = `
        <div class="stat-badge">
            <div class="stat-value">${playerStats.total_games || 0}</div>
            <div class="stat-label">Games</div>
        </div>
        <div class="stat-badge">
            <div class="stat-value">${playerStats.wins || 0}</div>
            <div class="stat-label">Wins</div>
        </div>
    `;
}

// Load player game history
async function loadPlayerHistory() {
    try {
        const response = await apiRequest('/api/player/history');
        allResults = response.games || [];
        filteredResults = allResults;
        displayResults(filteredResults);
    } catch (error) {
        console.error('Failed to load history:', error);
        document.getElementById('resultsList').innerHTML = `
            <p class="empty-state">Failed to load game history</p>
        `;
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

// Filter results by game type
function filterResults() {
    const gameType = document.getElementById('gameTypeFilter').value;

    if (gameType === '') {
        filteredResults = allResults;
    } else {
        filteredResults = allResults.filter(result => result.game_type === gameType);
    }

    displayResults(filteredResults);
}

// Display game results
function displayResults(results) {
    const container = document.getElementById('resultsList');

    if (!results || results.length === 0) {
        container.innerHTML = '<p class="empty-state">No game results found</p>';
        return;
    }

    const resultsHtml = results.map(result => {
        const finished_at = result.finished_at || result.started_at;
        const resultClass = result.is_winner ? 'win' : 'loss';
        const resultEmoji = result.is_winner ? '✓' : '✗';

        const playersHtml = result.players
            .map((player, index) => `
                <div class="result-player ${player.is_winner ? 'winner' : ''}">
                    <span>${player.is_winner ? '🏆 ' : ''}${player.name}</span>
                    <span>${player.final_score}</span>
                </div>
            `)
            .join('');

        return `
            <div class="result-card">
                <div class="result-header">
                    <span class="result-type">${result.game_type}</span>
                    <span class="result-date">${formatDate(finished_at)}</span>
                </div>
                <div class="result-players">
                    ${playersHtml}
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = resultsHtml;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const isToday = date.toDateString() === today.toDateString();
    const isYesterday = date.toDateString() === yesterday.toDateString();

    if (isToday) {
        return 'Today ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (isYesterday) {
        return 'Yesterday ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleDateString();
    }
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
