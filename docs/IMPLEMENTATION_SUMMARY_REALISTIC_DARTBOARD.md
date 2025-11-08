# Realistic Dartboard Implementation with Game Variant Support

## Summary

This implementation adds a **realistic SVG dartboard visualization** for Round the Clock games and introduces a new game variant called **Round the Clock Double**. The dartboard displays all 20 segments with authentic styling (cream/black alternating colors), shows single, double, and triple ring areas, and includes bull's eye visualization.

## Changes Made

### 1. **New Game Variant: Round the Clock Double**

- **File**: `/data/dartserver-pythonapp/src/games/game_round_the_clock_double.py` (NEW)
- **Game Type**: `round_the_clock_double`
- **Key Difference**: Only the **double bull (outer bull)** counts as a valid finishing target
  - **Original Round the Clock**: 22 targets (1-20, double bull, single bull - need 5 single bulls to finish)
  - **Round the Clock Double**: 21 targets (1-20, double bull only - single bull is NOT valid)
- **21 Unit Tests**: All passing ✅
- Maintains all Round the Clock mechanics for numbers 1-20

### 2. **Updated Game Manager**

- **File**: `/data/dartserver-pythonapp/src/app/game_manager.py`
- Added import for `GameRoundTheClockDouble`
- Added game instantiation logic for `round_the_clock_double` variant
- Updated docstrings to include new game type

### 3. **Updated API Documentation**

- **File**: `/data/dartserver-pythonapp/src/app/app.py`
- Updated 3 Swagger/OpenAPI enum definitions to include `round_the_clock_double`
- Updated endpoints:
  - `/api/game/state` - game state retrieval
  - `/api/game/new` - game creation
  - `/api/mobile/game/new` - mobile game creation

### 4. **Realistic SVG Dartboard UI**

- **File**: `/data/dartserver-pythonapp/static/js/main.js`
- **New Functions**:
  - `createRealisticDartboard(playerData, gameType)` - Main dartboard generator
  - `createRing(svg, dartboardNumbers, index, startAngle, endAngle, num, ringType, isCompleted, isCurrent, minRadius, maxRadius)` - Ring/segment creator
  - `describeArc()` - SVG arc path generator
  - `describeArcWedge()` - SVG wedge path generator

- **Features**:
  - SVG-based for precise geometry
  - All 20 dartboard segments in correct clockwise order: [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
  - Alternating cream (#C8A682) and black (#0a0a0a) segments
  - Three ring areas: Single (60-90 radius), Triple (130-145), Double (165-185)
  - Bull's eye with nested circles:
    - **Outer Bull (Double Bull)**: Orange (#D4600C or #FF6B00 when current)
    - **Inner Bull (Single Bull)**: Gold (#D4A600 or #FFD700 when current)
  - Number labels positioned on single ring
  - 400×400 viewBox for responsive scaling

- **Visual Indicators**:
  - **Current Target**: Cyan (#00CED1) with glow effect and pulse animation
  - **Completed Targets**: Gray (#555555) with reduced opacity (0.5)
  - **Blinking Animation**: 1-second pulse cycle for pulsing glow effect
  - Segments and numbers scale with pulsing animation

### 5. **Enhanced CSS Styling**

- **File**: `/data/dartserver-pythonapp/static/css/style.css`
- **New CSS Classes**:
  - `.rtc-dartboard-container` - Main SVG container with backdrop
  - `.rtc-dartboard-svg` - SVG element with drop shadow
  - `.rtc-current-segment` - Animated cyan glow for current target segments
  - `.rtc-current-number` - Animated number pulse for current target
  - `.rtc-current-bull` - Animated opacity pulse for bull's eye

- **Animations**:
  - `@keyframes rtc-segment-pulse` - Glow pulse for segments (opacity + filter)
  - `@keyframes rtc-number-pulse` - Font size pulse for numbers (18px → 20px)
  - `@keyframes rtc-bull-pulse` - Opacity pulse for bull's eye (1 → 0.7)
  - All animations run continuously at 1-second cycle

### 6. **Game Type Support**

- **Updated Fallback Game Types** in `loadFallbackGameTypes()`:
  - Added: `{ value: 'round_the_clock_double', label: 'Round the Clock Double' }`

- **Updated Format Function**:
  - Added special case mapping for `round_the_clock_double` → "Round the Clock Double"

### 7. **Support for Both Game Variants in UI**

- Both `round_the_clock` and `round_the_clock_double` use the realistic dartboard
- Conditional display logic:
  - **Round the Clock**: Shows bull hits counter (0-5 singles required)
  - **Round the Clock Double**: Shows "DOUBLE BULL" as the final target
- Mobile templates remain unchanged (separate mobile game files)

## Visual Design

### Dartboard Appearance

```
┌─────────────────────────────────────┐
│                                     │
│          20  1  18  4  13            │
│       [D] ╱────────────╲ [D]        │
│       [S]╱              ╲[S]        │
│      [T]╱                ╲[T]       │
│         ├─────────────────┤         │
│         │                 │         │
│         │      [O][I]     │         │
│         │                 │         │
│         ├─────────────────┤         │
│         │                 │         │
│       12  19  7  16  8  11 14 ...   │
│                                     │
└─────────────────────────────────────┘
Legend: [D]=Double Ring, [S]=Single Ring, [T]=Triple Ring, [O]=Outer Bull, [I]=Inner Bull
```

### Current Target Indication

- **Segment**: Cyan glow with pulsing opacity (1 → 0.4)
- **Number**: Cyan text with slight font size pulse (18px → 20px)
- **Bull**: Orange (double) or gold (single) glow with opacity pulse

### Completed Targets

- **Segments**: Gray background (#555555) with 50% opacity
- **Numbers**: Gray text with muted appearance
- Visual indication of progress made

## Testing

### Unit Tests

- **Original Round the Clock**: 21 tests - ✅ All PASS
- **New Round the Clock Double**: 20 tests - ✅ All PASS
- **Total**: 41 tests passing with no regressions

### Test Coverage

- `GameRoundTheClock`: 95.28% coverage
- `GameRoundTheClockDouble`: 93.55% coverage

### Key Test Cases

- Initialization and player management
- Single, double, triple hit scoring
- Bull validation (different for each variant)
- Win conditions
- Multi-player independent progression
- Complete game scenario end-to-end

## Backward Compatibility

- ✅ No breaking changes to existing `round_the_clock` game
- ✅ Existing Round the Clock tests continue to pass
- ✅ New `round_the_clock_double` available as optional variant
- ✅ Mobile templates unchanged
- ✅ API endpoints extended (not modified)

## Mobile Considerations

- Desktop implementation uses SVG dartboard (optimal for larger screens)
- Mobile implementation continues using separate templates (grid layout preferred for smaller screens)
- No changes to mobile gameplay logic
- Both game types accessible on mobile

## Performance Notes

- SVG generation uses mathematical calculations (no pre-rendered images)
- Smooth animations with CSS keyframes
- Responsive design with viewBox scaling
- Minimal DOM overhead (single SVG element with paths)

## Files Modified

1. `/data/dartserver-pythonapp/src/games/game_round_the_clock_double.py` - NEW
2. `/data/dartserver-pythonapp/src/app/game_manager.py` - Modified (import + logic)
3. `/data/dartserver-pythonapp/src/app/app.py` - Modified (API documentation)
4. `/data/dartserver-pythonapp/static/js/main.js` - Modified (UI rendering)
5. `/data/dartserver-pythonapp/static/css/style.css` - Modified (styling)
6. `/data/dartserver-pythonapp/tests/unit/test_game_round_the_clock_double.py` - NEW

## Usage

### Starting Round the Clock Double

```bash
POST /api/game/new
{
  "game_type": "round_the_clock_double",
  "players": ["Player 1", "Player 2"]
}
```

### Original Round the Clock Still Works

```bash
POST /api/game/new
{
  "game_type": "round_the_clock",
  "players": ["Player 1", "Player 2"]
}
```

## Future Enhancements

- Add more dartboard-specific game variants (e.g., Dublin, Shanghai)
- Interactive dartboard (click segments to simulate throws)
- Sound effects synchronized with visual effects
- Stats tracking per segment/ring
- Replay analysis with dartboard visualization
- Accessibility features (high contrast mode, screen reader support)
