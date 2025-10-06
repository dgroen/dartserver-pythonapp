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

// Audio elements (optional - can be added later)
const audioCache = {};

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
    updateGameDisplay(state);
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
    alertMessage.textContent = data.text;
});

// Big message event
socket.on('big_message', (data) => {
    console.log('Big message:', data.text);
    bigMessage.textContent = data.text;
    
    // Auto-clear after 3 seconds
    setTimeout(() => {
        if (bigMessage.textContent === data.text) {
            bigMessage.textContent = '';
        }
    }, 3000);
});

function updateGameDisplay(state) {
    // Update game info
    gameTypeDisplay.textContent = state.game_type.toUpperCase();
    gameStatusDisplay.textContent = state.is_started ? 
        (state.is_paused ? 'Paused' : 'In Progress') : 'Not Started';
    currentThrowDisplay.textContent = state.current_throw || 1;
    
    // Update players
    playersContainer.innerHTML = '';
    
    if (state.players && state.players.length > 0) {
        state.players.forEach((player, index) => {
            const playerCard = createPlayerCard(player, index, state);
            playersContainer.appendChild(playerCard);
        });
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