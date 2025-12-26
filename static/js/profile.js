// Profile Page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadUserProfile();
    loadUserStatistics();
    loadRecentGames();
});

// Load user profile information
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/current');
        if (!response.ok) {
            throw new Error('Failed to load user profile');
        }
        
        const data = await response.json();
        displayUserProfile(data);
    } catch (error) {
        console.error('Error loading user profile:', error);
        document.getElementById('loading-message').style.display = 'none';
        const errorMsg = document.getElementById('error-message');
        errorMsg.textContent = 'Failed to load profile information. Please try again.';
        errorMsg.style.display = 'block';
    }
}

function displayUserProfile(data) {
    document.getElementById('loading-message').style.display = 'none';
    document.getElementById('profile-info').style.display = 'block';
    
    // Display username
    document.getElementById('display-username').textContent = data.username || 'N/A';
    
    // Display email (we'll need to get this from user info API)
    // For now, we'll fetch it separately
    fetchUserEmail();
    
    // Display roles
    if (data.roles && data.roles.length > 0) {
        const rolesHtml = data.roles.map(role => 
            `<span class="role-badge role-${role}">${role}</span>`
        ).join(' ');
        document.getElementById('display-roles').innerHTML = rolesHtml;
    } else {
        document.getElementById('display-roles').textContent = 'No roles assigned';
    }
}

async function fetchUserEmail() {
    try {
        // Try to get user info from session or claims
        // This is available through the user_claims passed to the template
        // For now, we'll show placeholder
        const displayName = document.querySelector('.username')?.textContent?.replace('👤 ', '') || 'User';
        document.getElementById('display-name').textContent = displayName;
        document.getElementById('display-email').textContent = 'Managed by WSO2';
    } catch (error) {
        console.error('Error fetching user email:', error);
        document.getElementById('display-email').textContent = 'N/A';
        document.getElementById('display-name').textContent = 'N/A';
    }
}

// Load user statistics
async function loadUserStatistics() {
    try {
        const response = await fetch('/api/player/statistics');
        if (!response.ok) {
            throw new Error('Failed to load statistics');
        }
        
        const data = await response.json();
        if (data.success && data.statistics) {
            displayStatistics(data.statistics);
        } else {
            throw new Error(data.error || 'No statistics available');
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        document.getElementById('stats-loading').style.display = 'none';
        const errorMsg = document.getElementById('stats-error');
        errorMsg.textContent = 'No statistics available yet. Play some games to see your stats!';
        errorMsg.style.display = 'block';
    }
}

function displayStatistics(stats) {
    document.getElementById('stats-loading').style.display = 'none';
    document.getElementById('statistics').style.display = 'grid';
    
    // Total games
    document.getElementById('total-games').textContent = stats.total_games || 0;
    
    // Games won
    document.getElementById('games-won').textContent = stats.games_won || 0;
    
    // Win rate
    const winRate = stats.total_games > 0 
        ? ((stats.games_won / stats.total_games) * 100).toFixed(1) 
        : 0;
    document.getElementById('win-rate').textContent = `${winRate}%`;
    
    // Average score
    document.getElementById('avg-score').textContent = stats.average_score 
        ? stats.average_score.toFixed(1) 
        : '0';
    
    // Best finish
    document.getElementById('best-finish').textContent = stats.best_finish || '-';
    
    // Total throws
    document.getElementById('total-throws').textContent = stats.total_throws || 0;
}

// Load recent games
async function loadRecentGames() {
    try {
        const response = await fetch('/api/player/history?limit=5');
        if (!response.ok) {
            throw new Error('Failed to load games');
        }
        
        const data = await response.json();
        if (data.success && data.games) {
            displayRecentGames(data.games);
        } else {
            throw new Error(data.error || 'No games available');
        }
    } catch (error) {
        console.error('Error loading recent games:', error);
        document.getElementById('games-loading').style.display = 'none';
        const errorMsg = document.getElementById('games-error');
        errorMsg.textContent = 'No games played yet. Start playing to see your game history!';
        errorMsg.style.display = 'block';
    }
}

function displayRecentGames(games) {
    document.getElementById('games-loading').style.display = 'none';
    
    if (games.length === 0) {
        document.getElementById('games-error').textContent = 'No games played yet.';
        document.getElementById('games-error').style.display = 'block';
        return;
    }
    
    const gamesContainer = document.getElementById('recent-games');
    gamesContainer.innerHTML = games.map(game => {
        const date = new Date(game.started_at || game.finished_at);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        const resultClass = game.is_winner ? 'won' : 'lost';
        const resultText = game.is_winner ? 'Won' : 'Lost';
        
        return `
            <div class="game-item">
                <div class="game-info-left">
                    <div class="game-type">${game.game_type || 'Darts Game'}</div>
                    <div class="game-date">${formattedDate}</div>
                    <div class="game-players">${game.player_count || 1} player(s)</div>
                </div>
                <div class="game-result ${resultClass}">${resultText}</div>
            </div>
        `;
    }).join('');
}
