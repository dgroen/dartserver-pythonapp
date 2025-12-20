// Helper function to format game type names for display
function formatGameTypeName(name) {
    // Handle special cases
    const specialNames = {
        'round_the_clock': 'Round the Clock',
        'round_the_clock_double': 'Round the Clock Double',
        'cricket': 'Cricket'
    };

    if (specialNames[name]) {
        return specialNames[name];
    }

    // For numbered games (301, 401, 501, etc.), just return uppercase
    return name.toUpperCase();
}

// Helper function to load game types dynamically into select elements
async function loadGameTypes(selectElement, includeAllOption = false) {
    // Only prevent double-loading if we're already in the middle of loading
    if (selectElement.dataset.loading === 'true') {
        return;
    }

    // Mark as loading
    selectElement.dataset.loading = 'true';

    try {
        const response = await fetch('/api/game/types');
        const data = await response.json();

        if (data.status === 'success' && data.game_types) {
            // Clear existing options
            selectElement.innerHTML = '';

            // Add "All" option if requested (for filters)
            if (includeAllOption) {
                const allOption = document.createElement('option');
                allOption.value = 'all';
                allOption.textContent = 'All Games';
                selectElement.appendChild(allOption);
            }

            // Add game type options
            data.game_types.forEach(gameType => {
                const option = document.createElement('option');
                option.value = gameType.name;
                option.textContent = formatGameTypeName(gameType.name);
                selectElement.appendChild(option);
            });

            // Set default selection if not a filter
            if (!includeAllOption && data.game_types.length > 0) {
                // Default to 501 if available, otherwise first option
                const defaultGameType = data.game_types.find(gt => gt.name === '501');
                if (defaultGameType) {
                    selectElement.value = '501';
                } else {
                    selectElement.value = data.game_types[0].name;
                }

                // Trigger change event so any listeners (like hard mode visibility) can react
                selectElement.dispatchEvent(new Event('change'));
            }

            // Mark as loaded and no longer loading
            selectElement.dataset.loaded = 'true';
            selectElement.dataset.loading = 'false';
        } else {
            selectElement.dataset.loading = 'false';
            // Fallback to hardcoded values
            loadFallbackGameTypes(selectElement, includeAllOption);
        }
    } catch (error) {
        console.error('Error loading game types:', error);
        selectElement.dataset.loading = 'false';
        // Fallback to hardcoded values
        loadFallbackGameTypes(selectElement, includeAllOption);
    }
}

// Fallback to hardcoded game types if API fails
function loadFallbackGameTypes(selectElement, includeAllOption = false) {
    selectElement.innerHTML = '';

    if (includeAllOption) {
        const allOption = document.createElement('option');
        allOption.value = 'all';
        allOption.textContent = 'All Games';
        selectElement.appendChild(allOption);
    }

    const fallbackTypes = [
        { value: '301', label: '301' },
        { value: '401', label: '401' },
        { value: '501', label: '501' },
        { value: 'cricket', label: 'Cricket' },
        { value: 'round_the_clock', label: 'Round the Clock' },
        { value: 'round_the_clock_double', label: 'Round the Clock Double' }
    ];

    fallbackTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type.value;
        option.textContent = type.label;
        selectElement.appendChild(option);
    });

    // Set default selection if not a filter
    if (!includeAllOption && fallbackTypes.length > 0) {
        selectElement.value = '501'; // Default to 501
    }
}

// Connect to SocketIO
const socket = io();

// DOM Elements
const playersContainer = document.getElementById('players-container');
const bigMessage = document.getElementById('big-message');
const alertMessage = document.getElementById('alert-message');
const gameTypeDisplay = document.getElementById('game-type');
const gameStatusDisplay = document.getElementById('game-status');
const currentThrowDisplay = document.getElementById('current-throw');
const videoContainer = document.getElementById('video-container');
const effectVideo = document.getElementById('effect-video');
const throwoutAdviceElement = document.getElementById('throwoutAdvice');
const adviceDisplay = document.getElementById('adviceDisplay');
const nextPlayerButtonContainer = document.getElementById('nextPlayerButtonContainer');
const nextPlayerButton = document.getElementById('nextPlayerButton');

// Game state tracking
let currentGame = null;
let currentUser = null;

// Audio elements (optional - can be added later)
const audioCache = {};

// Initialize
socket.on('connect', () => {
    console.log('Connected to server');
    loadCurrentUser();
    // Load current game state on connect
    loadCurrentGameState();
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Load current user information
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/user/current', {
            credentials: 'include'
        });
        const data = await response.json();
        if (data.success) {
            currentUser = data;
            console.log('Current user loaded:', currentUser);
        }
    } catch (error) {
        console.error('Failed to load current user:', error);
    }
}

// Initialize Next Player button if it exists
if (nextPlayerButton) {
    nextPlayerButton.addEventListener('click', handleNextPlayerClick);
}

// Handle Next Player button click
function handleNextPlayerClick() {
    console.log('Button clicked!');
    console.log('currentGame:', currentGame);

    if (!socket || !currentGame) {
        console.error('Cannot continue: no active game or socket connection');
        return;
    }

    console.log('Game is_paused:', currentGame.is_paused);

    // If game is paused (waiting for continue), just emit next_player
    if (currentGame.is_paused) {
        console.log('Emitting next_player event');
        socket.emit('next_player');
        return;
    }

    // Game is active - end turn early (record remaining throws as misses)
    // For single-player games, skip confirmation
    const isSinglePlayer = currentGame.players && currentGame.players.length === 1;

    console.log('Game is active, ending turn early. Single player:', isSinglePlayer);

    if (isSinglePlayer) {
        socket.emit('end_turn_early');
    } else {
        // Confirm action for multi-player games
        if (confirm('End your turn early? Any remaining throws will be recorded as misses.')) {
            socket.emit('end_turn_early');
        }
    }
}

// Update visibility of Next Player button based on user role and current player
function updateNextPlayerButton(state) {
    if (!nextPlayerButtonContainer || !state) {
        return;
    }

    // Don't show button if no game or no user info
    if (!currentUser || !state.is_started) {
        nextPlayerButtonContainer.style.display = 'none';
        return;
    }

    // Show button if user is gamemaster (always)
    const isGamemaster = currentUser.roles && currentUser.roles.includes('gamemaster');
    if (isGamemaster) {
        nextPlayerButtonContainer.style.display = 'block';
        updateButtonText(state);
        return;
    }

    // Show button if user is the current player
    const currentPlayerIndex = state.current_player;
    if (currentPlayerIndex !== undefined && state.players && state.players[currentPlayerIndex]) {
        const currentPlayerDbId = state.players[currentPlayerIndex].db_id;
        const userPlayerId = currentUser.player_id;

        if (currentPlayerDbId && userPlayerId && currentPlayerDbId === userPlayerId) {
            nextPlayerButtonContainer.style.display = 'block';
            updateButtonText(state);
            return;
        }
    }

    // Hide button otherwise
    nextPlayerButtonContainer.style.display = 'none';
}

// Update button text based on game state
function updateButtonText(state) {
    const buttonHint = document.getElementById('buttonHint');

    if (state.is_paused) {
        // Game is paused - button continues to next player
        if (nextPlayerButton) {
            nextPlayerButton.textContent = '▶️ Continue Game';
        }
        if (buttonHint) {
            buttonHint.textContent = 'Continue to next player';
        }
    } else {
        // Game is active - button ends turn early
        if (nextPlayerButton) {
            nextPlayerButton.textContent = '⏭️ End Turn Early';
        }
        if (buttonHint) {
            buttonHint.textContent = 'Skip remaining throws (records as misses)';
        }
    }
}

// Game state update
socket.on('game_state', (state) => {
    console.log('Game state:', state);
    currentGame = state;
    updateGameDisplay(state);
    updateNextPlayerButton(state);
});

// Sound event
socket.on('play_sound', (data) => {
    console.log('Play sound:', data.sound);
    playSound(data.sound);
});

// TTS audio event
socket.on('play_tts', (data) => {
    console.log('Play TTS:', data.text);
    playTTSAudio(data.audio, data.text);
});

// Video event
socket.on('play_video', (data) => {
    console.log('Play video:', data.video, 'angle:', data.angle);
    playVideo(data.video, data.angle);
});

// Message event
socket.on('message', (data) => {
    console.log('Message:', data.text);
    if (alertMessage) {
        alertMessage.textContent = data.text;
    }
});

// Big message event
socket.on('big_message', (data) => {
    console.log('Big message:', data.text);
    if (bigMessage) {
        bigMessage.textContent = data.text;

        // Auto-clear after 3 seconds
        setTimeout(() => {
            if (bigMessage.textContent === data.text) {
                bigMessage.textContent = '';
            }
        }, 3000);
    }
});

function updateGameDisplay(state) {
    // Update game info (only if elements exist on this page)
    if (gameTypeDisplay) {
        gameTypeDisplay.textContent = state.game_type.toUpperCase();
    }
    if (gameStatusDisplay) {
        gameStatusDisplay.textContent = state.is_started ?
            (state.is_paused ? 'Paused' : 'In Progress') : 'Not Started';
    }
    if (currentThrowDisplay) {
        currentThrowDisplay.textContent = state.current_throw || 1;
    }

    // Update players (only if container exists)
    if (playersContainer) {
        playersContainer.innerHTML = '';

        if (state.players && state.players.length > 0) {
            state.players.forEach((player, index) => {
                const playerCard = createPlayerCard(player, index, state);
                playersContainer.appendChild(playerCard);
            });
        }
    }

    // Update throwout advice display
    displayThrowoutAdvice(state.throwout_advice);
}

function displayThrowoutAdvice(advice) {
    // Only update if elements exist on this page
    if (!adviceDisplay || !throwoutAdviceElement) {
        return;
    }

    if (Array.isArray(advice) && advice.length > 0) {
        adviceDisplay.textContent = advice.join(' or ');
        throwoutAdviceElement.style.display = 'block';
    } else {
        throwoutAdviceElement.style.display = 'none';
    }
}

function createPlayerCard(player, index, state) {
    const card = document.createElement('div');
    card.className = 'player-card';

    // Add active class if it's this player's turn
    if (index === state.current_player && state.is_started && !state.is_paused) {
        card.classList.add('active');
    }

    // Add winner class if this player won
    if (state.is_winner && index === state.current_player) {
        card.classList.add('winner');
    }

    // Player name
    const nameDiv = document.createElement('div');
    nameDiv.className = 'player-name';
    nameDiv.textContent = player.name;
    card.appendChild(nameDiv);

    // Get player data from game state
    let playerData = player;
    if (state.game_data && state.game_data.players && state.game_data.players[index]) {
        playerData = state.game_data.players[index];
    }

    // Player score
    const scoreDiv = document.createElement('div');
    scoreDiv.className = 'player-score';
    scoreDiv.textContent = playerData.score || 0;
    card.appendChild(scoreDiv);

    // Cricket targets (if cricket game)
    if (state.game_type === 'cricket' && playerData.targets) {
        const targetsDiv = document.createElement('div');
        targetsDiv.className = 'cricket-targets';

        const cricketTargets = [15, 16, 17, 18, 19, 20, 25];
        cricketTargets.forEach(target => {
            const targetData = playerData.targets[target];
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
                numberDiv.textContent = target === 25 ? 'B' : target;
                targetDiv.appendChild(numberDiv);

                const marksDiv = document.createElement('div');
                marksDiv.className = 'target-marks';
                marksDiv.textContent = '✓'.repeat(targetData.hits);
                targetDiv.appendChild(marksDiv);

                targetsDiv.appendChild(targetDiv);
            }
        });

        card.appendChild(targetsDiv);
    }

    // Round the Clock targets (if round_the_clock or round_the_clock_double game)
    if ((state.game_type === 'round_the_clock' || state.game_type === 'round_the_clock_double') && playerData.current_target !== undefined) {
        const rtcDiv = document.createElement('div');
        rtcDiv.className = 'rtc-container';

        // Current target display
        const currentTargetDiv = document.createElement('div');
        currentTargetDiv.className = 'rtc-current-target';

        if (playerData.current_target === 0) {
            // Player needs to hit the bull
            if (state.game_type === 'round_the_clock') {
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

        // Realistic SVG Dartboard
        const svgDartboard = createRealisticDartboard(playerData, state.game_type);
        rtcDiv.appendChild(svgDartboard);

        card.appendChild(rtcDiv);
    }

// Function to create a realistic dartboard SVG
function createRealisticDartboard(playerData, gameType) {
    const container = document.createElement('div');
    container.className = 'rtc-dartboard-container';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 450 450');
    svg.setAttribute('width', '450');
    svg.setAttribute('height', '450');
    svg.className = 'rtc-dartboard-svg';

    // Dartboard numbers in clockwise order (standard sequence)
    const dartboardNumbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];

    // Create SVG segments for each of the 20 numbers
    dartboardNumbers.forEach((num, index) => {
        const startAngle = (index - 0.5) * (360 / 20) - 90; // -90 to start at top
        const endAngle = (index + 0.5) * (360 / 20) - 90;

        // Check if this segment is completed or current
        let isCompleted = false;
        let isCurrent = playerData.current_target === num;

        if (playerData.current_target < num) {
            isCompleted = true;
        }

        // Create double ring (outer)
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'double', isCompleted, isCurrent, 170, 185);

        // Create single ring (outer singles) - wider like inner singles
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'single-outer', isCompleted, isCurrent, 135, 170);

        // Create triple ring - same width as double
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'triple', isCompleted, isCurrent, 120, 135);

        // Create single ring (inner singles) - connects to bull's eye
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'single-inner', isCompleted, isCurrent, 16, 120);
    });

    // Add outer single ring (between double and edge)
    const outerRingPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    outerRingPath.setAttribute('d', describeArc(225, 225, 190, 0, 360));
    outerRingPath.setAttribute('fill', 'none');
    outerRingPath.setAttribute('stroke', '#333');
    outerRingPath.setAttribute('stroke-width', '4');
    svg.appendChild(outerRingPath);

    // Add bull's eye
    // Outer bull (double bull) - should be glowing if current
    const doubleBull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    doubleBull.setAttribute('cx', '225');
    doubleBull.setAttribute('cy', '225');
    doubleBull.setAttribute('r', '16');
    doubleBull.setAttribute('fill', playerData.current_target === 0 && gameType === 'round_the_clock_double' ? '#FF6B00' : '#D4600C');
    doubleBull.setAttribute('class', playerData.current_target === 0 ? 'rtc-current-bull' : '');
    if (playerData.current_target === 0 && gameType === 'round_the_clock_double') {
        doubleBull.setAttribute('filter', 'url(#bullGlow)');
    }
    svg.appendChild(doubleBull);

    // Inner bull (single bull)
    const singleBull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    singleBull.setAttribute('cx', '225');
    singleBull.setAttribute('cy', '225');
    singleBull.setAttribute('r', '8');
    singleBull.setAttribute('fill', playerData.current_target === 0 && gameType === 'round_the_clock' ? '#FFD700' : '#D4A600');
    singleBull.setAttribute('class', playerData.current_target === 0 && gameType === 'round_the_clock' ? 'rtc-current-bull' : '');
    if (playerData.current_target === 0 && gameType === 'round_the_clock') {
        singleBull.setAttribute('filter', 'url(#bullGlow)');
    }
    svg.appendChild(singleBull);

    // Add glow filter for current targets
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
    filter.setAttribute('id', 'bullGlow');
    const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
    feGaussianBlur.setAttribute('stdDeviation', '3');
    feGaussianBlur.setAttribute('result', 'coloredBlur');
    filter.appendChild(feGaussianBlur);
    const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
    const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
    feMergeNode1.setAttribute('in', 'coloredBlur');
    const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
    feMergeNode2.setAttribute('in', 'SourceGraphic');
    feMerge.appendChild(feMergeNode1);
    feMerge.appendChild(feMergeNode2);
    filter.appendChild(feMerge);
    defs.appendChild(filter);
    svg.appendChild(defs);

    container.appendChild(svg);
    return container;
}

function createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, ringType, isCompleted, isCurrent, minRadius, maxRadius) {
    // Colors for dartboard segments (alternating cream and black)
    const isEvenSegment = index % 2 === 0;
    const baseColor = isEvenSegment ? '#C8A682' : '#0a0a0a'; // Cream or black
    const highlightColor = '#00CED1'; // Cyan for current
    const completedColor = '#555555'; // Gray for completed

    const color = isCompleted ? completedColor : (isCurrent ? highlightColor : baseColor);
    const opacity = isCompleted ? 0.5 : 1;

    // Create wedge path for this segment
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const pathData = describeArcWedge(225, 225, minRadius, maxRadius, startRad, endRad);

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('fill', color);
    path.setAttribute('opacity', opacity);
    path.setAttribute('stroke', '#333');
    path.setAttribute('stroke-width', '2');

    if (isCurrent) {
        path.setAttribute('class', 'rtc-current-segment');
    }

    svg.appendChild(path);

    // Add number labels outside the board (for double ring only)
    if (ringType === 'double') {
        const midAngle = (startAngle + endAngle) / 2;
        const midRad = (midAngle * Math.PI) / 180;
        const labelRadius = 205; // Outside the dartboard
        const labelX = 225 + labelRadius * Math.cos(midRad);
        const labelY = 225 + labelRadius * Math.sin(midRad);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', labelX);
        text.setAttribute('y', labelY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dy', '0.3em');
        text.setAttribute('fill', isCompleted ? '#888' : (isCurrent ? '#00CED1' : '#000'));
        text.setAttribute('font-size', '18');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('class', isCurrent ? 'rtc-current-number' : '');
        text.textContent = num;
        svg.appendChild(text);
    }
}

function describeArc(cx, cy, radius, startAngle, endAngle) {
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    const x1 = cx + radius * Math.cos(startRad);
    const y1 = cy + radius * Math.sin(startRad);
    const x2 = cx + radius * Math.cos(endRad);
    const y2 = cy + radius * Math.sin(endRad);

    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

    return `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
}

function describeArcWedge(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
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

// Function to create a realistic dartboard SVG
function createRealisticDartboard(playerData, gameType) {
    const container = document.createElement('div');
    container.className = 'rtc-dartboard-container';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 450 450');
    svg.setAttribute('width', '450');
    svg.setAttribute('height', '450');
    svg.className = 'rtc-dartboard-svg';

    // Dartboard numbers in clockwise order (standard sequence)
    const dartboardNumbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];

    // Create SVG segments for each of the 20 numbers
    dartboardNumbers.forEach((num, index) => {
        const startAngle = (index - 0.5) * (360 / 20) - 90; // -90 to start at top
        const endAngle = (index + 0.5) * (360 / 20) - 90;

        // Check if this segment is completed or current
        let isCompleted = false;
        let isCurrent = playerData.current_target === num;

        if (playerData.current_target < num) {
            isCompleted = true;
        }

        // Create double ring (outer)
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'double', isCompleted, isCurrent, 170, 185);

        // Create single ring (outer singles) - wider like inner singles
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'single-outer', isCompleted, isCurrent, 135, 170);

        // Create triple ring - same width as double
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'triple', isCompleted, isCurrent, 120, 135);

        // Create single ring (inner singles) - connects to bull's eye
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'single-inner', isCompleted, isCurrent, 16, 120);
    });

    // Add outer single ring (between double and edge)
    const outerRingPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    outerRingPath.setAttribute('d', describeArc(225, 225, 190, 0, 360));
    outerRingPath.setAttribute('fill', 'none');
    outerRingPath.setAttribute('stroke', '#333');
    outerRingPath.setAttribute('stroke-width', '4');
    svg.appendChild(outerRingPath);

    // Add bull's eye
    // Outer bull (double bull) - should be glowing if current
    const doubleBull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    doubleBull.setAttribute('cx', '225');
    doubleBull.setAttribute('cy', '225');
    doubleBull.setAttribute('r', '16');
    doubleBull.setAttribute('fill', playerData.current_target === 0 && gameType === 'round_the_clock_double' ? '#FF6B00' : '#D4600C');
    doubleBull.setAttribute('class', playerData.current_target === 0 ? 'rtc-current-bull' : '');
    if (playerData.current_target === 0 && gameType === 'round_the_clock_double') {
        doubleBull.setAttribute('filter', 'url(#bullGlow)');
    }
    svg.appendChild(doubleBull);

    // Inner bull (single bull)
    const singleBull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    singleBull.setAttribute('cx', '225');
    singleBull.setAttribute('cy', '225');
    singleBull.setAttribute('r', '8');
    singleBull.setAttribute('fill', playerData.current_target === 0 && gameType === 'round_the_clock' ? '#FFD700' : '#D4A600');
    singleBull.setAttribute('class', playerData.current_target === 0 && gameType === 'round_the_clock' ? 'rtc-current-bull' : '');
    if (playerData.current_target === 0 && gameType === 'round_the_clock') {
        singleBull.setAttribute('filter', 'url(#bullGlow)');
    }
    svg.appendChild(singleBull);

    // Add glow filter for current targets
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
    filter.setAttribute('id', 'bullGlow');
    const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
    feGaussianBlur.setAttribute('stdDeviation', '3');
    feGaussianBlur.setAttribute('result', 'coloredBlur');
    filter.appendChild(feGaussianBlur);
    const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
    const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
    feMergeNode1.setAttribute('in', 'coloredBlur');
    const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
    feMergeNode2.setAttribute('in', 'SourceGraphic');
    feMerge.appendChild(feMergeNode1);
    feMerge.appendChild(feMergeNode2);
    filter.appendChild(feMerge);
    defs.appendChild(filter);
    svg.appendChild(defs);

    container.appendChild(svg);
    return container;
}

function createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, ringType, isCompleted, isCurrent, minRadius, maxRadius) {
    // Colors for dartboard segments (alternating cream and black)
    const isEvenSegment = index % 2 === 0;
    const baseColor = isEvenSegment ? '#C8A682' : '#0a0a0a'; // Cream or black
    const highlightColor = '#00CED1'; // Cyan for current
    const completedColor = '#555555'; // Gray for completed

    const color = isCompleted ? completedColor : (isCurrent ? highlightColor : baseColor);
    const opacity = isCompleted ? 0.5 : 1;

    // Create wedge path for this segment
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const pathData = describeArcWedge(225, 225, minRadius, maxRadius, startRad, endRad);

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('fill', color);
    path.setAttribute('opacity', opacity);
    path.setAttribute('stroke', '#333');
    path.setAttribute('stroke-width', '2');

    if (isCurrent) {
        path.setAttribute('class', 'rtc-current-segment');
    }

    svg.appendChild(path);

    // Add number labels outside the board (for double ring only)
    if (ringType === 'double') {
        const midAngle = (startAngle + endAngle) / 2;
        const midRad = (midAngle * Math.PI) / 180;
        const labelRadius = 205; // Outside the dartboard
        const labelX = 225 + labelRadius * Math.cos(midRad);
        const labelY = 225 + labelRadius * Math.sin(midRad);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', labelX);
        text.setAttribute('y', labelY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dy', '0.3em');
        text.setAttribute('fill', isCompleted ? '#888' : (isCurrent ? '#00CED1' : '#000'));
        text.setAttribute('font-size', '18');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('class', isCurrent ? 'rtc-current-number' : '');
        text.textContent = num;
        svg.appendChild(text);
    }
}

function describeArc(cx, cy, radius, startAngle, endAngle) {
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    const x1 = cx + radius * Math.cos(startRad);
    const y1 = cy + radius * Math.sin(startRad);
    const x2 = cx + radius * Math.cos(endRad);
    const y2 = cy + radius * Math.sin(endRad);

    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

    return `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
}

function describeArcWedge(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
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

// Function to create a realistic dartboard SVG
function createRealisticDartboard(playerData, gameType) {
    const container = document.createElement('div');
    container.className = 'rtc-dartboard-container';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 450 450');
    svg.setAttribute('width', '450');
    svg.setAttribute('height', '450');
    svg.className = 'rtc-dartboard-svg';

    // Dartboard numbers in clockwise order (standard sequence)
    const dartboardNumbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];

    // Create SVG segments for each of the 20 numbers
    dartboardNumbers.forEach((num, index) => {
        const startAngle = (index - 0.5) * (360 / 20) - 90; // -90 to start at top
        const endAngle = (index + 0.5) * (360 / 20) - 90;

        // Check if this segment is completed or current
        let isCompleted = false;
        let isCurrent = playerData.current_target === num;

        if (playerData.current_target < num) {
            isCompleted = true;
        }

        // Create double ring (outer)
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'double', isCompleted, isCurrent, 170, 185);

        // Create single ring (outer singles) - wider like inner singles
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'single-outer', isCompleted, isCurrent, 135, 170);

        // Create triple ring - same width as double
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'triple', isCompleted, isCurrent, 120, 135);

        // Create single ring (inner singles) - connects to bull's eye
        createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, 'single-inner', isCompleted, isCurrent, 16, 120);
    });

    // Add outer single ring (between double and edge)
    const outerRingPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    outerRingPath.setAttribute('d', describeArc(225, 225, 190, 0, 360));
    outerRingPath.setAttribute('fill', 'none');
    outerRingPath.setAttribute('stroke', '#333');
    outerRingPath.setAttribute('stroke-width', '4');
    svg.appendChild(outerRingPath);

    // Add bull's eye
    // Outer bull (double bull) - should be glowing if current
    const doubleBull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    doubleBull.setAttribute('cx', '225');
    doubleBull.setAttribute('cy', '225');
    doubleBull.setAttribute('r', '16');
    doubleBull.setAttribute('fill', playerData.current_target === 0 && gameType === 'round_the_clock_double' ? '#FF6B00' : '#D4600C');
    doubleBull.setAttribute('class', playerData.current_target === 0 ? 'rtc-current-bull' : '');
    if (playerData.current_target === 0 && gameType === 'round_the_clock_double') {
        doubleBull.setAttribute('filter', 'url(#bullGlow)');
    }
    svg.appendChild(doubleBull);

    // Inner bull (single bull)
    const singleBull = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    singleBull.setAttribute('cx', '225');
    singleBull.setAttribute('cy', '225');
    singleBull.setAttribute('r', '8');
    singleBull.setAttribute('fill', playerData.current_target === 0 && gameType === 'round_the_clock' ? '#FFD700' : '#D4A600');
    singleBull.setAttribute('class', playerData.current_target === 0 && gameType === 'round_the_clock' ? 'rtc-current-bull' : '');
    if (playerData.current_target === 0 && gameType === 'round_the_clock') {
        singleBull.setAttribute('filter', 'url(#bullGlow)');
    }
    svg.appendChild(singleBull);

    // Add glow filter for current targets
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
    filter.setAttribute('id', 'bullGlow');
    const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
    feGaussianBlur.setAttribute('stdDeviation', '3');
    feGaussianBlur.setAttribute('result', 'coloredBlur');
    filter.appendChild(feGaussianBlur);
    const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
    const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
    feMergeNode1.setAttribute('in', 'coloredBlur');
    const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
    feMergeNode2.setAttribute('in', 'SourceGraphic');
    feMerge.appendChild(feMergeNode1);
    feMerge.appendChild(feMergeNode2);
    filter.appendChild(feMerge);
    defs.appendChild(filter);
    svg.appendChild(defs);

    container.appendChild(svg);
    return container;
}

function createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, ringType, isCompleted, isCurrent, minRadius, maxRadius) {
    // Colors for dartboard segments (alternating cream and black)
    const isEvenSegment = index % 2 === 0;
    const baseColor = isEvenSegment ? '#C8A682' : '#0a0a0a'; // Cream or black
    const highlightColor = '#00CED1'; // Cyan for current
    const completedColor = '#555555'; // Gray for completed

    const color = isCompleted ? completedColor : (isCurrent ? highlightColor : baseColor);
    const opacity = isCompleted ? 0.5 : 1;

    // Create wedge path for this segment
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const pathData = describeArcWedge(225, 225, minRadius, maxRadius, startRad, endRad);

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('fill', color);
    path.setAttribute('opacity', opacity);
    path.setAttribute('stroke', '#333');
    path.setAttribute('stroke-width', '2');

    if (isCurrent) {
        path.setAttribute('class', 'rtc-current-segment');
    }

    svg.appendChild(path);

    // Add number labels outside the board (for double ring only)
    if (ringType === 'double') {
        const midAngle = (startAngle + endAngle) / 2;
        const midRad = (midAngle * Math.PI) / 180;
        const labelRadius = 205; // Outside the dartboard
        const labelX = 225 + labelRadius * Math.cos(midRad);
        const labelY = 225 + labelRadius * Math.sin(midRad);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', labelX);
        text.setAttribute('y', labelY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dy', '0.3em');
        text.setAttribute('fill', isCompleted ? '#888' : (isCurrent ? '#00CED1' : '#000'));
        text.setAttribute('font-size', '18');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('class', isCurrent ? 'rtc-current-number' : '');
        text.textContent = num;
        svg.appendChild(text);
    }
}

function describeArc(cx, cy, radius, startAngle, endAngle) {
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    const x1 = cx + radius * Math.cos(startRad);
    const y1 = cy + radius * Math.sin(startRad);
    const x2 = cx + radius * Math.cos(endRad);
    const y2 = cy + radius * Math.sin(endRad);

    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

    return `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
}

function describeArcWedge(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
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

    return card;
}

function playSound(soundName) {
    // This is a placeholder - you can implement actual audio playback
    // using the audio files from the public/audio directory
    console.log(`Playing sound: ${soundName}`);

    // Example implementation:
    // const audio = new Audio(`/audio/${soundName}.mp3`);
    // audio.play().catch(e => console.log('Audio play failed:', e));
}

function playTTSAudio(audioBase64, text) {
    try {
        // Decode base64 audio data
        const binaryString = atob(audioBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

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

function playVideo(videoName, angle) {
    // This is a placeholder - you can implement actual video playback
    console.log(`Playing video: ${videoName} at angle: ${angle}`);

    // Example implementation:
    // effectVideo.src = `/_gfx/${videoName}`;
    // effectVideo.style.transform = `rotate(${angle}deg)`;
    // videoContainer.classList.remove('hidden');
    //
    // effectVideo.onended = () => {
    //     videoContainer.classList.add('hidden');
    // };
}

// Keyboard shortcuts (optional)
document.addEventListener('keydown', (e) => {
    // Space bar to advance to next player
    if (e.code === 'Space') {
        e.preventDefault();
        socket.emit('next_player');
    }
});

// ========================================
// Games Sidebar Management
// ========================================

let currentGameId = null;
let gamesRefreshInterval = null;

// Initialize games sidebar
function initGamesSidebar() {
    const newGameBtn = document.getElementById('btn-new-game');
    if (newGameBtn) {
        newGameBtn.addEventListener('click', () => {
            window.location.href = '/game/create';
        });
    }
    
    // Load initial game state
    loadCurrentGameState();
    
    // Load games list
    loadGamesList();
    
    // Refresh games list every 5 seconds
    if (gamesRefreshInterval) {
        clearInterval(gamesRefreshInterval);
    }
    gamesRefreshInterval = setInterval(loadGamesList, 5000);
}

// Load and display list of games
async function loadGamesList() {
    try {
        const response = await fetch('/api/games');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayGamesList(data.games, data.active_game_id);
        }
    } catch (error) {
        console.error('Error loading games list:', error);
    }
}

// Display games in sidebar
function displayGamesList(games, activeGameId) {
    const gamesList = document.getElementById('games-list');
    if (!gamesList) return;
    
    if (!games || games.length === 0) {
        gamesList.innerHTML = '<div class="no-games">No games available.<br>Click + to create one!</div>';
        return;
    }
    
    currentGameId = activeGameId;
    
    gamesList.innerHTML = games.map(game => {
        const isActive = game.game_id === activeGameId;
        const statusClass = game.is_started ? 'started' : 'not-started';
        const statusText = game.is_started ? 'Active' : 'Not Started';
        
        // Format player info with scores
        let playersHtml = '';
        if (game.players && game.players.length > 0) {
            const playerList = game.players.slice(0, 3).map(p => {
                if (typeof p === 'string') {
                    return p;
                } else if (p.name) {
                    // Show score if available
                    return p.score !== undefined ? `${p.name} (${p.score})` : p.name;
                }
                return 'Unknown';
            });
            playersHtml = '<br>' + playerList.join('<br>');
            if (game.players.length > 3) {
                playersHtml += '<br>...';
            }
        }
        
        return `
            <div class="game-item ${isActive ? 'active' : ''}" data-game-id="${game.game_id}">
                <div class="game-item-header">
                    <span class="game-item-id">${game.game_id}</span>
                    <span class="game-item-status ${statusClass}">${statusText}</span>
                </div>
                <div class="game-item-info">
                    <div class="game-item-type">${formatGameTypeName(game.game_type || 'N/A')}</div>
                    <div class="game-item-players">
                        👥 ${game.player_count} player${game.player_count !== 1 ? 's' : ''}
                        ${playersHtml}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add click handlers to game items
    gamesList.querySelectorAll('.game-item').forEach(item => {
        item.addEventListener('click', function() {
            const gameId = this.dataset.gameId;
            switchToGame(gameId);
        });
    });
}

// Switch to a different game
async function switchToGame(gameId) {
    if (gameId === currentGameId) {
        console.log('Already viewing this game');
        return;
    }
    
    try {
        const response = await fetch(`/api/games/${gameId}/activate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log(`Switched to game: ${gameId}`);
            currentGameId = gameId;
            
            // Reload game state immediately after switching
            await loadCurrentGameState();
            
            // Reload games list to update active status
            loadGamesList();
        } else {
            console.error('Error switching game:', data.message);
        }
    } catch (error) {
        console.error('Error switching game:', error);
    }
}

// Load current game state from API
async function loadCurrentGameState() {
    try {
        const response = await fetch('/api/game/state');
        const state = await response.json();
        
        if (state && Object.keys(state).length > 0) {
            console.log('Loaded game state:', state);
            currentGame = state;
            updateGameDisplay(state);
            updateNextPlayerButton(state);
        }
    } catch (error) {
        console.error('Error loading game state:', error);
    }
}

// Initialize games sidebar on page load
if (document.getElementById('games-sidebar')) {
    document.addEventListener('DOMContentLoaded', initGamesSidebar);
}
