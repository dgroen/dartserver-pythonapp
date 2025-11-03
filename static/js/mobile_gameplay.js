// Mobile Gameplay JavaScript - Enhanced version matching web app functionality

let socket;
let currentGameState = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    loadActiveGames();

    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', (event) => {
            const tabName = event.currentTarget.getAttribute('data-tab');
            switchTab(tabName, event.currentTarget);
        });
    });
});

// Helper function for API requests
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: 'include',  // Include session cookies
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

// Tab switching functionality
function switchTab(tabName, buttonElement = null) {
    // Update active tab button
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonElement) {
        buttonElement.classList.add('active');
    } else {
        // Find and activate the correct button if not provided
        const targetButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
        }
    }

    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    // Reload data if needed
    if (tabName === 'active-games') {
        loadActiveGames();
    }
}

function initializeSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to game server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from game server');
    });

    socket.on('game_state', (state) => {
        console.log('Game state update:', state);
        currentGameState = state;
        updateGameDisplay(state);
    });

    socket.on('play_sound', (data) => {
        console.log('Play sound:', data.sound);
        // Sound playback can be added here if needed for mobile
    });

    socket.on('play_tts', (data) => {
        console.log('Play TTS:', data.text);
        playTTSAudio(data.audio, data.text);
    });

    socket.on('message', (data) => {
        console.log('Message:', data.text);
        showMessage(data.text);
    });

    socket.on('big_message', (data) => {
        console.log('Big message:', data.text);
        showBigMessage(data.text);
    });
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
                    <span class="result-type">${formatGameType(game.game_type)}</span>
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

function updateGameDisplay(state) {
    // Update game status
    const gameStatus = document.getElementById('gameStatus');
    if (state.is_started) {
        gameStatus.innerHTML = `
            <div class="status-badge status-active">${formatGameType(state.game_type)} - ${state.is_paused ? 'Paused' : 'In Progress'}</div>
        `;
    } else {
        gameStatus.innerHTML = `
            <div class="status-badge">No Active Game</div>
        `;
    }

    // Update game info card
    const gameInfoCard = document.getElementById('gameInfoCard');
    if (state.is_started) {
        gameInfoCard.style.display = 'block';
        document.getElementById('gameTypeDisplay').textContent = formatGameType(state.game_type);
        document.getElementById('gameStatusDisplay').textContent = state.is_paused ? 'Paused' : 'In Progress';
        document.getElementById('currentThrowDisplay').textContent = `${state.current_throw || 1} / 3`;
    } else {
        gameInfoCard.style.display = 'none';
    }

    // Update throwout advice
    displayThrowoutAdvice(state.throwout_advice);

    // Update players display
    displayPlayers(state);
}

function displayPlayers(state) {
    const container = document.getElementById('playersContainer');

    if (!state.is_started || !state.players || state.players.length === 0) {
        container.innerHTML = '<p class="empty-state">No active game</p>';
        return;
    }

    container.innerHTML = '';

    state.players.forEach((player, index) => {
        const playerCard = createPlayerCard(player, index, state);
        container.appendChild(playerCard);
    });
}

function createPlayerCard(player, index, state) {
    const card = document.createElement('div');
    card.className = 'mobile-player-card';

    // Add active class if it's this player's turn
    if (index === state.current_player && state.is_started && !state.is_paused) {
        card.classList.add('active');
    }

    // Add winner class if this player won
    if (playerData.is_winner || (state.winner_index !== undefined && index === state.winner_index)) {
        card.classList.add('winner');
    }

    // Get player data from game state
    let playerData = player;
    if (state.game_data && state.game_data.players && state.game_data.players[index]) {
        playerData = { ...player, ...state.game_data.players[index] };
    }

    // Player header
    const headerDiv = document.createElement('div');
    headerDiv.className = 'player-card-header';
    headerDiv.innerHTML = `
        <div class="player-name">${player.name}</div>
        <div class="player-score">${playerData.score || 0}</div>
    `;
    card.appendChild(headerDiv);

    // Cricket targets (if cricket game)
    if (state.game_type === 'cricket' && playerData.targets) {
        const targetsDiv = createCricketTargets(playerData.targets);
        card.appendChild(targetsDiv);
    }

    // Round the Clock targets (if round_the_clock game)
    if ((state.game_type === 'round_the_clock' || state.game_type === 'round_the_clock_double') && playerData.current_target !== undefined) {
        const rtcDiv = createRoundTheClockDisplay(playerData, state.game_type);
        card.appendChild(rtcDiv);
    }

    return card;
}

function createCricketTargets(targets) {
    const targetsDiv = document.createElement('div');
    targetsDiv.className = 'cricket-targets';

    const cricketNumbers = [15, 16, 17, 18, 19, 20, 25];
    cricketNumbers.forEach(number => {
        const targetData = targets[number];
        if (targetData) {
            const targetDiv = document.createElement('div');
            targetDiv.className = 'cricket-target';

            if (targetData.status === 1) {
                targetDiv.classList.add('open');
            } else if (targetData.status === 2) {
                targetDiv.classList.add('closed');
            }

            const numberDiv = document.createElement('div');
            numberDiv.className = 'target-number';
            numberDiv.textContent = number === 25 ? 'B' : number;
            targetDiv.appendChild(numberDiv);

            const marksDiv = document.createElement('div');
            marksDiv.className = 'target-marks';
            marksDiv.textContent = '✓'.repeat(targetData.hits);
            targetDiv.appendChild(marksDiv);

            targetsDiv.appendChild(targetDiv);
        }
    });

    return targetsDiv;
}

function createRoundTheClockDisplay(playerData, gameType) {
    const rtcDiv = document.createElement('div');
    rtcDiv.className = 'rtc-container';

    // Current target display
    const currentTargetDiv = document.createElement('div');
    currentTargetDiv.className = 'rtc-current-target';
    
    if (playerData.current_target === 0) {
        // Player needs to hit the bull
        if (gameType === 'round_the_clock') {
            currentTargetDiv.innerHTML = `
                <div class="rtc-target-label">Current Target:</div>
                <div class="rtc-target-value bull">BULL</div>
                <div class="rtc-bull-hits">Bull Hits: ${playerData.bull_hits || 0}/5</div>
            `;
        } else {
            // Round the Clock Double - only double bull counts
            currentTargetDiv.innerHTML = `
                <div class="rtc-target-label">Current Target:</div>
                <div class="rtc-target-value bull">DOUBLE BULL</div>
            `;
        }
    } else {
        currentTargetDiv.innerHTML = `
            <div class="rtc-target-label">Current Target:</div>
            <div class="rtc-target-value">${playerData.current_target}</div>
        `;
    }
    rtcDiv.appendChild(currentTargetDiv);

    // Create simplified dartboard visualization for mobile
    const dartboardDiv = createMobileDartboard(playerData, gameType);
    rtcDiv.appendChild(dartboardDiv);
    
    return rtcDiv;
}

function createMobileDartboard(playerData, gameType) {
    const container = document.createElement('div');
    container.className = 'mobile-dartboard-container';
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 350 350');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', 'auto');
    svg.className = 'mobile-dartboard-svg';
    
    // Dartboard numbers in clockwise order (standard sequence)
    const dartboardNumbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];
    
    const centerX = 175;
    const centerY = 175;
    const innerRadius = 50;
    const outerRadius = 150;
    
    // Create segments for each number
    dartboardNumbers.forEach((num, index) => {
        const startAngle = (index - 0.5) * (360 / 20) - 90;
        const endAngle = (index + 0.5) * (360 / 20) - 90;
        
        // In Round the Clock, you go from 1->20 then bull, so completed means current_target > num
        const isCompleted = playerData.current_target > num && playerData.current_target !== 0;
        const isCurrent = playerData.current_target === num;
        
        createMobileSegment(svg, centerX, centerY, innerRadius, outerRadius, startAngle, endAngle, num, isCompleted, isCurrent, index);
    });
    
    // Add bull's eye
    const bull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    bull.setAttribute('cx', centerX);
    bull.setAttribute('cy', centerY);
    bull.setAttribute('r', '25');
    bull.setAttribute('fill', playerData.current_target === 0 ? '#FFD700' : '#8B4513');
    bull.setAttribute('stroke', '#333');
    bull.setAttribute('stroke-width', '2');
    if (playerData.current_target === 0) {
        bull.setAttribute('class', 'rtc-current-bull-mobile');
    }
    svg.appendChild(bull);
    
    container.appendChild(svg);
    return container;
}

function createMobileSegment(svg, cx, cy, innerRadius, outerRadius, startAngle, endAngle, num, isCompleted, isCurrent, index) {
    const isEvenSegment = index % 2 === 0;
    const baseColor = isEvenSegment ? '#C8A682' : '#2C2C2C';
    const highlightColor = '#00CED1';
    const completedColor = '#555555';
    
    const color = isCompleted ? completedColor : (isCurrent ? highlightColor : baseColor);
    const opacity = isCompleted ? 0.5 : 1;
    
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    
    const pathData = describeArcWedgeMobile(cx, cy, innerRadius, outerRadius, startRad, endRad);
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('fill', color);
    path.setAttribute('opacity', opacity);
    path.setAttribute('stroke', '#333');
    path.setAttribute('stroke-width', '1');
    
    svg.appendChild(path);
    
    // Add number label
    const midAngle = (startAngle + endAngle) / 2;
    const midRad = (midAngle * Math.PI) / 180;
    const labelRadius = outerRadius + 15;
    const labelX = cx + labelRadius * Math.cos(midRad);
    const labelY = cy + labelRadius * Math.sin(midRad);
    
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', labelX);
    text.setAttribute('y', labelY);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('dy', '0.3em');
    text.setAttribute('fill', isCurrent ? '#00CED1' : (isCompleted ? '#888' : '#FFF'));
    text.setAttribute('font-size', '14');
    text.setAttribute('font-weight', 'bold');
    text.textContent = num;
    svg.appendChild(text);
}

function describeArcWedgeMobile(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
    const x1 = cx + innerRadius * Math.cos(startAngle);
    const y1 = cy + innerRadius * Math.sin(startAngle);
    const x2 = cx + outerRadius * Math.cos(startAngle);
    const y2 = cy + outerRadius * Math.sin(startAngle);
    const x3 = cx + outerRadius * Math.cos(endAngle);
    const y3 = cy + outerRadius * Math.sin(endAngle);
    const x4 = cx + innerRadius * Math.cos(endAngle);
    const y4 = cy + innerRadius * Math.sin(endAngle);
    
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    
    return `M ${x1} ${y1} L ${x2} ${y2} A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x3} ${y3} L ${x4} ${y4} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x1} ${y1} Z`;
}

function displayThrowoutAdvice(advice) {
    const adviceElement = document.getElementById('throwoutAdvice');
    const adviceDisplay = document.getElementById('adviceDisplay');

    if (Array.isArray(advice) && advice.length > 0) {
        adviceDisplay.textContent = advice.join(' or ');
        adviceElement.style.display = 'block';
    } else {
        adviceElement.style.display = 'none';
    }
}

function showMessage(text) {
    const messageDisplay = document.getElementById('messageDisplay');
    if (messageDisplay) {
        messageDisplay.style.display = 'block';
        messageDisplay.textContent = text;
        setTimeout(() => {
            messageDisplay.style.display = 'none';
        }, 3000);
    }
}

function showBigMessage(text) {
    const bigMessage = document.getElementById('bigMessage');
    const messageDisplay = document.getElementById('messageDisplay');
    
    if (bigMessage && messageDisplay) {
        messageDisplay.style.display = 'block';
        bigMessage.textContent = text;
        bigMessage.style.fontSize = '1.5rem';
        bigMessage.style.fontWeight = 'bold';
        bigMessage.style.color = 'var(--highlight-color)';
        
        setTimeout(() => {
            if (bigMessage.textContent === text) {
                messageDisplay.style.display = 'none';
                bigMessage.textContent = '';
            }
        }, 3000);
    }
}

function playTTSAudio(audioBase64, text) {
    try {
        // Decode base64 audio data
        const binaryString = atob(audioBase64);
        // More efficient byte array conversion
        const bytes = Uint8Array.from(binaryString, char => char.charCodeAt(0));

        // Create blob from audio data
        const blob = new Blob([bytes], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(blob);

        // Create and play audio element
        const audio = new Audio(audioUrl);

        // Clean up the object URL after playing
        audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };

        // Handle errors
        audio.onerror = (e) => {
            console.error('TTS audio playback error:', e);
            URL.revokeObjectURL(audioUrl);
        };

        // Play the audio
        audio.play().catch(e => {
            console.error('TTS audio play failed:', e);
            URL.revokeObjectURL(audioUrl);
        });

        console.log(`Playing TTS audio: "${text}"`);
    } catch (error) {
        console.error('Error processing TTS audio:', error);
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

// Format game type for display
function formatGameType(gameType) {
    const typeMap = {
        '301': '301',
        '401': '401',
        '501': '501',
        'cricket': 'Cricket',
        'round_the_clock': 'Round the Clock',
        'round_the_clock_double': 'Round the Clock Double'
    };
    return typeMap[gameType] || gameType.toUpperCase();
}
