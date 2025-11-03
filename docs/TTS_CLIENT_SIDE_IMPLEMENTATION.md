# Client-Side TTS Implementation Guide

## Overview

The Text-to-Speech (TTS) system has been successfully migrated from server-side to client-side playback. Audio is now generated on the server and streamed to clients' browsers for playback.

## Architecture

### Server-Side Components

#### 1. TTS Service (`tts_service.py`)

- **Method**: `speak(text, generate_audio=False)`
  - When `generate_audio=True`: Returns audio bytes (MP3 format)
  - When `generate_audio=False`: Plays audio on server (legacy mode)
- **Method**: `generate_audio_data(text, lang='en')`
  - Generates MP3 audio data using gTTS
  - Returns bytes that can be transmitted to clients

#### 2. Game Manager (`game_manager.py`)

- **Method**: `_emit_sound(sound, text=None)`
  - Generates audio data when text is provided
  - Encodes audio as base64 for WebSocket transmission
  - Emits `play_tts` event with audio data and text

#### 3. REST API Endpoint (`app.py`)

- **Endpoint**: `POST /api/tts/generate`
- **Request Body**:

  ```json
  {
    "text": "Hello, this is a test",
    "lang": "en"
  }
  ```

- **Response**: Audio data (audio/mpeg)
- **Use Case**: On-demand TTS generation, testing, alternative integration

### Client-Side Components

#### 1. Main Display (`static/js/main.js`)

- **Event Listener**: `socket.on('play_tts', ...)`
- **Function**: `playTTSAudio(audioBase64, text)`
  - Decodes base64 audio data
  - Creates Blob with MIME type `audio/mpeg`
  - Generates object URL and plays audio
  - Properly cleans up resources

#### 2. Control Panel (`static/js/control.js`)

- Same implementation as main display
- Ensures TTS works on both interfaces

## Configuration

### Environment Variables (.env)

```bash
# Enable TTS
TTS_ENABLED=true

# Use gTTS for client-side playback (REQUIRED)
TTS_ENGINE=gtts

# Optional settings
TTS_VOICE=default
TTS_SPEED=150
TTS_VOLUME=1.0
```

**Important**: For client-side playback, `TTS_ENGINE` must be set to `gtts`. The `pyttsx3` engine only supports server-side playback.

## Data Flow

1. **Game Event Occurs** → Game logic triggers TTS
2. **Audio Generation** → Server generates MP3 audio using gTTS
3. **Base64 Encoding** → Audio bytes encoded for WebSocket transmission
4. **WebSocket Emission** → `play_tts` event sent to all clients
5. **Client Decoding** → Browser decodes base64 to binary
6. **Blob Creation** → Binary data wrapped in Blob with audio/mpeg type
7. **Audio Playback** → HTML5 Audio API plays the sound
8. **Resource Cleanup** → Object URL revoked after playback

## Technical Details

### Audio Format

- **Format**: MP3 (MPEG Audio Layer 3)
- **MIME Type**: `audio/mpeg`
- **Generator**: Google Text-to-Speech (gTTS)

### Data Transmission

- **Protocol**: WebSocket (SocketIO)
- **Event Name**: `play_tts`
- **Encoding**: Base64 (increases size by ~33%)
- **Payload Structure**:

  ```json
  {
    "audio": "base64_encoded_audio_data",
    "text": "Original text for logging"
  }
  ```

### Browser Compatibility

- Uses HTML5 Audio API (supported by all modern browsers)
- MP3 format widely supported
- Base64 decoding via `atob()` (standard JavaScript)

## Testing

### 1. Test via Game Play

1. Start the application
2. Create a new game
3. Make a throw (e.g., score a triple)
4. Listen for TTS audio in your browser

### 2. Test via REST API

```bash
curl -X POST http://localhost:5000/api/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test", "lang": "en"}' \
  --output test_audio.mp3

# Play the generated audio file
mpg123 test_audio.mp3  # Linux
afplay test_audio.mp3  # macOS
```

### 3. Test via Browser Console

```javascript
// Manually trigger TTS playback
socket.emit("play_tts", {
  audio: "base64_audio_data_here",
  text: "Test message",
});
```

## Troubleshooting

### No Audio Plays

1. **Check TTS is enabled**: Verify `TTS_ENABLED=true` in `.env`
2. **Check engine**: Ensure `TTS_ENGINE=gtts` (not pyttsx3)
3. **Check internet**: gTTS requires internet connection to Google's service
4. **Check browser console**: Look for JavaScript errors
5. **Check autoplay policy**: Some browsers block autoplay until user interaction

### Audio Quality Issues

- gTTS provides high-quality speech synthesis
- Speed can be adjusted via `TTS_SPEED` environment variable
- Language can be changed per request (default: English)

### Performance Concerns

- **Latency**: ~500ms-2s for audio generation (depends on internet speed)
- **Bandwidth**: Base64 encoding increases size by ~33%
- **Caching**: Consider implementing client-side audio cache for repeated phrases

## Browser Autoplay Policy

Modern browsers restrict autoplay of audio. The implementation handles this gracefully:

```javascript
audio.play().catch((e) => {
  console.error("TTS audio play failed:", e);
  URL.revokeObjectURL(audioUrl);
});
```

**Workaround**: Ensure user has interacted with the page (clicked, tapped) before TTS plays.

## Memory Management

The implementation properly manages resources:

1. **Object URLs are created** for each audio playback
2. **URLs are revoked** after playback completes
3. **URLs are revoked** on error to prevent memory leaks
4. **No audio elements accumulate** in the DOM

## Future Enhancements

### Potential Improvements

1. **Client-side caching**: Cache frequently used phrases
2. **Offline support**: Pre-generate common phrases
3. **Voice selection**: Allow users to choose different voices
4. **Volume control**: Add client-side volume adjustment
5. **Queue management**: Queue multiple TTS messages
6. **Compression**: Use more efficient audio formats (Opus, AAC)
7. **Streaming**: Stream audio chunks for faster playback start

### Alternative Approaches

1. **Web Speech API**: Use browser's native TTS (no server generation needed)
2. **WebRTC**: Stream audio via WebRTC for lower latency
3. **Audio sprites**: Pre-generate and combine common phrases

## Dependencies

### Server-Side

- `gTTS` (Google Text-to-Speech): Audio generation
- `Flask-SocketIO`: WebSocket communication
- `base64`: Audio encoding (Python standard library)

### Client-Side

- `socket.io-client`: WebSocket client
- HTML5 Audio API: Audio playback
- `atob()`: Base64 decoding (JavaScript standard)

## Security Considerations

1. **Input validation**: Text is validated before TTS generation
2. **Rate limiting**: Consider adding rate limits to prevent abuse
3. **Content filtering**: Consider filtering inappropriate text
4. **CORS**: Ensure proper CORS configuration for API endpoint

## Performance Metrics

### Typical Performance

- **Audio generation**: 500ms - 2s (depends on text length and internet)
- **Base64 encoding**: <10ms
- **WebSocket transmission**: 50-200ms (depends on network)
- **Client decoding**: <10ms
- **Total latency**: ~1-3 seconds from trigger to playback

### Optimization Tips

1. Keep TTS messages short and concise
2. Pre-generate common phrases during server startup
3. Implement client-side caching
4. Use CDN for static audio files when possible

## Conclusion

The client-side TTS implementation is production-ready and provides:

- ✅ Browser-based audio playback
- ✅ Real-time streaming via WebSocket
- ✅ On-demand generation via REST API
- ✅ Proper error handling
- ✅ Memory leak prevention
- ✅ Cross-browser compatibility
- ✅ High-quality speech synthesis

The system is now ready for deployment and use in production environments.
