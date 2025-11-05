# Realistic Dartboard & Round the Clock Double - Usage Guide

## Overview

This guide explains how to use the new realistic dartboard visualization and the new **Round the Clock Double** game variant.

## Features

### 🎯 Realistic SVG Dartboard
- **Authentic Dartboard Layout**: All 20 segments in correct positions (20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5)
- **Alternating Colors**: Cream (#C8A682) and Black (#0a0a0a) segments
- **Ring Areas**: Single, Triple, and Double ring visualization
- **Bull's Eye**: Nested circles showing double bull (outer) and single bull (inner)
- **Interactive Feedback**:
  - Current targets glow cyan and pulse
  - Completed targets fade to gray
  - Smooth animations throughout

### 🎲 Game Variants

#### Original Round the Clock
- **Type**: `round_the_clock`
- **Targets**: 20 numbers (20→1) + Double Bull + Single Bull (×5)
- **Total**: 22 targets
- **Finishing**:
  - Hit double bull for instant win, OR
  - Hit single bull 5 times to win

#### NEW: Round the Clock Double
- **Type**: `round_the_clock_double`
- **Targets**: 20 numbers (20→1) + Double Bull ONLY
- **Total**: 21 targets
- **Finishing**: Hit double bull to win immediately
- **Difference**: Single bull is NOT a valid target (no 5-hit counter)

## Starting a Game

### Via API

#### Round the Clock (Original)
```bash
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "round_the_clock",
    "players": ["Alice", "Bob", "Charlie"]
  }'
```

#### Round the Clock Double (NEW)
```bash
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "round_the_clock_double",
    "players": ["Alice", "Bob", "Charlie"]
  }'
```

### Via Web Interface
1. Open the application
2. Select game type:
   - "Round the Clock" (original - 22 targets)
   - "Round the Clock Double" (new - 21 targets)
3. Enter player names
4. Click "Start Game"
5. Dartboard appears on each player's card

## Visual Indicators

### Current Target
- **Segments**: Cyan (#00CED1) with glowing outline
- **Animation**: Pulsing glow (expands and contracts)
- **Number**: Cyan text, slightly larger
- **Bull**: Orange glow (double) or gold glow (single)

### Completed Targets
- **Segments**: Gray (#555555) background
- **Opacity**: 50% transparent
- **Number**: Muted gray text
- **Meaning**: Already hit and scored

### Upcoming Targets
- **Segments**: Normal color (cream or black)
- **Number**: White text
- **Meaning**: Still to be achieved

## Gameplay

### Round the Clock
1. Start at 20, progress backwards to 1
2. Hit required number to advance
3. At 0 (bull needed):
   - Hit double bull = WIN
   - Hit single bull = +1 counter (need 5 total to win)
4. Skip turn goes to next player

### Round the Clock Double
1. Start at 20, progress backwards to 1
2. Hit required number to advance
3. At 0 (bull needed):
   - Hit double bull = WIN ✨
   - Hit single bull = NO EFFECT (invalid)
4. Skip turn goes to next player

## Multiplayer

Both variants support unlimited players:
- Each player has independent dartboard tracking
- Dartboard shows current progress for that player
- Players take turns sequentially
- Scoring logic identical (different finishing rule)

## Game Progression

### Example: Alice's Turn
```
Turn 1:
  Current: 20
  Result: Hit 20 (single) → Advance to 19
  Dartboard shows: 19 highlighted

Turn 2:
  Current: 19
  Result: Hit 19 (double) → Skip 1, advance to 17
  Dartboard shows: 17 highlighted

...eventually...

Final Turn:
  Current: 0 (need bull)

  Round the Clock:
    - Hit double bull → WIN!
    - Hit single bull → +1 (now need 4 more)
    - Hit single bull → +1 (now need 3 more)
    - Hit single bull → +1 (now need 2 more)
    - Hit single bull → +1 (now need 1 more)
    - Hit single bull → +1 (WINNER!)

  Round the Clock Double:
    - Hit double bull → WIN!
    - Hit single bull → No effect (invalid in this variant)
```

## API Response Examples

### Get Game State - Round the Clock
```json
{
  "status": "success",
  "players": [
    {
      "id": 0,
      "name": "Alice",
      "current_target": 19,
      "is_turn": true,
      "bull_hits": 0
    }
  ],
  "game_type": "round_the_clock",
  "current_player": 0,
  "is_started": true,
  "is_paused": false,
  "is_winner": false
}
```

### Get Game State - Round the Clock Double
```json
{
  "status": "success",
  "players": [
    {
      "id": 0,
      "name": "Bob",
      "current_target": 0,
      "is_turn": true
    }
  ],
  "game_type": "round_the_clock_double",
  "current_player": 0,
  "is_started": true,
  "is_paused": false,
  "is_winner": false
}
```

Note: `bull_hits` only appears in `round_the_clock`, not in `round_the_clock_double`

## Mobile Support

- ✅ Both variants work on mobile
- ✅ Desktop uses SVG dartboard visualization
- ✅ Mobile uses optimized layout (separate templates)
- ✅ Same game logic across all platforms
- ✅ Touch-friendly UI

## Tips & Tricks

### For Players
1. **Current Target Display**: Text shows current number or "BULL"
2. **Dartboard View**: Glowing segments show progress visually
3. **Quick Reference**: Numbers arranged in dartboard order (not numerical)
4. **Pacing**: Watch for glowing animation to know whose turn it is

### For Game Masters
1. **Variant Selection**: Choose appropriate variant for skill level
   - Double Bull only = Shorter, more challenging
   - Both Bulls = Longer, more varied gameplay
2. **Tracking Progress**: Dartboard color-coding makes progress obvious
3. **Broadcasting**: SVG scales responsively for displays

### For Developers
1. **Game Logic**: Classes are independent and testable
2. **API Integration**: RESTful endpoints for both variants
3. **WebSocket Events**: Real-time updates via SocketIO
4. **Customization**: Easy to extend with new variants

## Troubleshooting

### Dartboard Not Showing
- ✅ Ensure browser supports SVG (modern browsers only)
- ✅ Check browser console for JavaScript errors
- ✅ Verify game type is `round_the_clock` or `round_the_clock_double`
- ✅ Refresh page

### Bull Target Not Working
- ✅ For Round the Clock: Need current_target = 0 (bull reached)
- ✅ For Round the Clock Double: Double bull is only valid option
- ✅ Single bull only works in original variant
- ✅ Check multiplier type (BULL vs DBLBULL)

### Animation Lag
- ✅ Modern browser should handle animations smoothly
- ✅ Disable other animations if experiencing lag
- ✅ Clear browser cache
- ✅ Update to latest browser version

## Performance

- **SVG Rendering**: 400×400 viewBox, responsive scaling
- **Animation Framerate**: 60 FPS smooth animations
- **Memory**: Minimal overhead (single SVG element)
- **Update Frequency**: Real-time via WebSocket

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| SVG Dartboard | ✅ | ✅ | ✅ | ✅ |
| Animations | ✅ | ✅ | ✅ | ✅ |
| WebSocket | ✅ | ✅ | ✅ | ✅ |
| Mobile | ✅ | ✅ | ✅ | ✅ |

## Related Files

- Game Logic: `src/games/game_round_the_clock.py`, `src/games/game_round_the_clock_double.py`
- UI Rendering: `static/js/main.js` (lines 296-505)
- Styling: `static/css/style.css` (lines 382-440)
- API Endpoints: `src/app/app.py`
- Game Manager: `src/app/game_manager.py`
- Tests: `tests/unit/test_game_round_the_clock.py`, `tests/unit/test_game_round_the_clock_double.py`

## Questions?

For more details, see:
- `IMPLEMENTATION_SUMMARY_REALISTIC_DARTBOARD.md` - Technical implementation details
- `.zencoder/rules/repo.md` - Project overview
- Game logic files - Source code documentation
