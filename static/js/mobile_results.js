// Mobile Results JavaScript

let allResults = [];
let filteredResults = [];

document.addEventListener('DOMContentLoaded', () => {
    loadResults();

    document.getElementById('gameTypeFilter').addEventListener('change', filterResults);
});

async function loadResults() {
    try {
        const response = await apiRequest('/api/game/results');
        allResults = response.results || [];
        filteredResults = allResults;
        displayResults(filteredResults);
    } catch (error) {
        console.error('Failed to load results:', error);
        document.getElementById('resultsList').innerHTML = `
            <p class="empty-state">Failed to load game results</p>
        `;
    }
}

function filterResults() {
    const gameType = document.getElementById('gameTypeFilter').value;

    if (gameType === '') {
        filteredResults = allResults;
    } else {
        filteredResults = allResults.filter(result => result.game_type === gameType);
    }

    displayResults(filteredResults);
}

function displayResults(results) {
    const container = document.getElementById('resultsList');

    if (results.length === 0) {
        container.innerHTML = '<p class="empty-state">No game results found</p>';
        return;
    }

    const resultsHtml = results.map(result => `
        <div class="result-card">
            <div class="result-header">
                <span class="result-type">${result.game_type}</span>
                <span class="result-date">${formatDate(result.ended_at || result.created_at)}</span>
            </div>

            ${result.players ? `
                <div class="result-players">
                    ${result.players.map((player, index) => `
                        <div class="result-player ${index === 0 ? 'winner' : ''}">
                            <span>${index === 0 ? '🏆 ' : ''}${player.name}</span>
                            <span>${player.final_score || player.score}</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            ${result.duration ? `
                <div class="item-subtitle" style="margin-top: 1rem;">
                    Duration: ${formatDuration(result.duration)}
                </div>
            ` : ''}
        </div>
    `).join('');

    container.innerHTML = resultsHtml;
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}
