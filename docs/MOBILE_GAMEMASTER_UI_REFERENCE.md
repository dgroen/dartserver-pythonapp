# 📱 Mobile Game Master - UI Reference Guide

## Visual Layout Overview

This document provides a visual reference for the Mobile Game Master interface.

---

## 🎨 Screen Layout

```
┌─────────────────────────────────────┐
│  ☰  👑 Game Master                  │  ← Header (Gradient)
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 🎮 Game Status                │ │  ← Status Card
│  │ ● Online | Game: 501          │ │
│  │ Current: Player 1             │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 🎯 Start New Game             │ │  ← Start Game Section
│  │                               │ │
│  │ Game Type: [501 ▼]           │ │
│  │ ☑ Double Out                  │ │
│  │                               │ │
│  │ Players (one per line):       │ │
│  │ ┌─────────────────────────┐  │ │
│  │ │ Player 1                │  │ │
│  │ │ Player 2                │  │ │
│  │ │                         │  │ │
│  │ └─────────────────────────┘  │ │
│  │                               │ │
│  │      [  Start Game  ]         │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 👥 Players                    │ │  ← Players Section
│  │                               │ │
│  │ ▶ Player 1        Score: 501 │ │  ← Active (Red glow)
│  │   Player 2        Score: 501 │ │
│  │                               │ │
│  │ Add Player:                   │ │
│  │ [Player Name] [Add Player]    │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 🎮 Game Controls              │ │  ← Controls Section
│  │                               │ │
│  │ [  Next Player  ]             │ │
│  │ [  Pause Game   ]             │ │
│  │ [  End Game     ]             │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 🎯 Manual Score Entry         │ │  ← Score Entry
│  │                               │ │
│  │ Score: [60]                   │ │
│  │ Multiplier: [Single ▼]        │ │
│  │                               │ │
│  │      [  Submit Score  ]       │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 📊 Game State                 │ │  ← Game State
│  │                               │ │
│  │ {                             │ │
│  │   "game_type": "501",         │ │
│  │   "players": [...],           │ │
│  │   ...                         │ │
│  │ }                             │ │
│  │                               │ │
│  │      [  Refresh  ]            │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘

        ┌─────────────────┐
        │ ✅ Success!     │  ← Toast Notification
        └─────────────────┘
```

---

## 🎨 Color Scheme

### Primary Colors

```
┌──────────────────────────────────────┐
│ Header Gradient                      │
│ #1e3c72 ──────────────► #2a5298     │  Deep Blue Gradient
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Highlight Color                      │
│ #e94560                              │  Vibrant Red/Pink
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Success                              │
│ #4CAF50                              │  Green
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Warning                              │
│ #f39c12                              │  Orange
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Danger                               │
│ #dc3545                              │  Red
└──────────────────────────────────────┘
```

### Background Effects

```
┌──────────────────────────────────────┐
│ Card Background                      │
│ rgba(255, 255, 255, 0.1)            │  Semi-transparent white
│ backdrop-filter: blur(10px)          │  Glassmorphism
└──────────────────────────────────────┘
```

---

## 🎯 Interactive Elements

### Buttons

#### Primary Button (Active)

```
┌─────────────────────────────────────┐
│         Start Game                  │  Blue gradient
│                                     │  White text
└─────────────────────────────────────┘
```

#### Primary Button (Hover)

```
┌─────────────────────────────────────┐
│         Start Game                  │  Lifted (translateY -5px)
│                                     │  Stronger shadow
└─────────────────────────────────────┘
```

#### Secondary Button

```
┌─────────────────────────────────────┐
│         Refresh                     │  Transparent bg
│                                     │  White border
└─────────────────────────────────────┘
```

#### Disabled Button

```
┌─────────────────────────────────────┐
│         Next Player                 │  Gray
│                                     │  50% opacity
└─────────────────────────────────────┘
```

### Form Inputs

#### Text Input (Normal)

```
┌─────────────────────────────────────┐
│ Player Name                         │  Glassmorphism bg
│                                     │  White text
└─────────────────────────────────────┘
```

#### Text Input (Focus)

```
┌─────────────────────────────────────┐
│ Player Name█                        │  Blue glow
│                                     │  Highlighted border
└─────────────────────────────────────┘
```

#### Select Dropdown

```
┌─────────────────────────────────────┐
│ 501                              ▼  │  Glassmorphism bg
└─────────────────────────────────────┘
```

### Player Items

#### Inactive Player

```
┌─────────────────────────────────────┐
│   Player 2              Score: 501  │  Normal state
└─────────────────────────────────────┘
```

#### Active Player

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ▶ Player 1              Score: 501 ┃  Red border & glow
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 🔔 Toast Notifications

### Success Toast

```
┌─────────────────────────────────────┐
│ ✅ Game started successfully!       │  Green background
└─────────────────────────────────────┘
```

### Error Toast

```
┌─────────────────────────────────────┐
│ ❌ Failed to start game             │  Red background
└─────────────────────────────────────┘
```

### Warning Toast

```
┌─────────────────────────────────────┐
│ ⚠️ Please add at least 2 players    │  Orange background
└─────────────────────────────────────┘
```

### Info Toast

```
┌─────────────────────────────────────┐
│ ℹ️ Connecting to server...          │  Blue background
└─────────────────────────────────────┘
```

---

## 📱 Responsive Breakpoints

### Mobile Portrait (< 768px)

```
┌─────────────┐
│   Header    │  Full width
├─────────────┤
│   Status    │  Single column
├─────────────┤
│ Start Game  │  Stacked sections
├─────────────┤
│   Players   │  Full width cards
├─────────────┤
│  Controls   │  Full width buttons
├─────────────┤
│   Score     │  Full width form
└─────────────┘
```

### Tablet/Desktop (≥ 768px)

```
┌─────────────────────────────────┐
│           Header                │  Full width
├─────────────────────────────────┤
│  ┌─────────┐  ┌──────────────┐ │
│  │ Status  │  │ Start Game   │ │  Two columns
│  └─────────┘  └──────────────┘ │
│  ┌─────────┐  ┌──────────────┐ │
│  │ Players │  │   Controls   │ │  Side by side
│  └─────────┘  └──────────────┘ │
└─────────────────────────────────┘
```

---

## 🎭 Animation States

### Loading State

```
┌─────────────────────────────────────┐
│         ⟳ Starting Game...          │  Spinning icon
│                                     │  Disabled state
└─────────────────────────────────────┘
```

### Transition States

```
Button Press:    scale(0.98)     ← Pressed down
Button Hover:    translateY(-5px) ← Lifted up
Toast Enter:     translateY(20px) → translateY(0)
Toast Exit:      opacity(1) → opacity(0)
```

---

## 🎨 Status Indicators

### Online Status

```
● Online    ← Green pulsing dot
```

### Offline Status

```
● Offline   ← Gray static dot
```

### Game Active

```
🎮 Game: 501 | Current: Player 1
```

### No Game

```
🎮 No active game
```

---

## 📐 Spacing & Sizing

### Touch Targets

```
Minimum Size: 44x44px
Recommended: 48x48px
Large Buttons: 100% width × 48px height
```

### Padding

```
Section Padding:  1.5rem (24px)
Card Padding:     1rem (16px)
Button Padding:   1rem 1.5rem (16px 24px)
Input Padding:    0.75rem (12px)
```

### Gaps

```
Section Gap:      1rem (16px)
Element Gap:      0.75rem (12px)
Form Gap:         0.5rem (8px)
```

### Border Radius

```
Cards:            15px
Buttons:          8px
Inputs:           8px
Toast:            8px
```

---

## 🎬 User Flow Examples

### Starting a New Game

```
1. User opens /mobile/gamemaster
   ↓
2. Sees status card (No active game)
   ↓
3. Scrolls to "Start New Game"
   ↓
4. Selects game type (501)
   ↓
5. Toggles double-out (optional)
   ↓
6. Enters player names:
   Player 1
   Player 2
   ↓
7. Clicks "Start Game"
   ↓
8. Button shows loading state
   ↓
9. Toast: "✅ Game started successfully!"
   ↓
10. Status card updates: "Game: 501"
    ↓
11. Players list populates
    ↓
12. Player 1 highlighted (active)
    ↓
13. Control buttons enabled
```

### Advancing to Next Player

```
1. Game is active, Player 1 is current
   ↓
2. User clicks "Next Player"
   ↓
3. Button briefly disabled
   ↓
4. WebSocket emits 'next_player'
   ↓
5. Server responds with game_update
   ↓
6. Player 2 becomes highlighted
   ↓
7. Status card updates: "Current: Player 2"
   ↓
8. Toast: "✅ Advanced to Player 2"
```

### Submitting Manual Score

```
1. User scrolls to "Manual Score Entry"
   ↓
2. Enters score: 60
   ↓
3. Selects multiplier: Triple
   ↓
4. Clicks "Submit Score"
   ↓
5. Form validates (0-60 range)
   ↓
6. WebSocket emits 'manual_score'
   ↓
7. Server processes score
   ↓
8. Receives score_update event
   ↓
9. Player score updates in list
   ↓
10. Toast: "✅ Score submitted: 180"
    ↓
11. Form resets
```

---

## 🎯 Visual Hierarchy

### Priority Levels

#### Level 1: Critical Actions

- **Start Game** button (largest, most prominent)
- **Next Player** button (primary action during game)
- **Active Player** indicator (red glow, impossible to miss)

#### Level 2: Important Information

- **Status Card** (always visible at top)
- **Player List** (shows current game state)
- **Game Controls** (pause, end game)

#### Level 3: Secondary Actions

- **Add Player** (available but not primary)
- **Manual Score** (advanced feature)
- **Refresh** button (utility)

#### Level 4: Reference Information

- **Game State JSON** (for debugging/advanced users)
- **Helper text** (form hints)

---

## 🎨 Glassmorphism Effect

The interface uses glassmorphism for a modern, layered look:

```css
Background: rgba(255, 255, 255, 0.1)
Backdrop Filter: blur(10px)
Border: 1px solid rgba(255, 255, 255, 0.2)
Box Shadow: 0 8px 32px rgba(0, 0, 0, 0.1)
```

This creates a frosted glass effect that:

- ✅ Looks modern and premium
- ✅ Maintains readability
- ✅ Creates visual depth
- ✅ Matches mobile app design

---

## 📱 Mobile-Specific Features

### Touch Feedback

- **Tap**: Button scales down (0.98)
- **Hold**: No additional effect (prevents accidental actions)
- **Swipe**: Smooth scrolling with momentum

### Keyboard Handling

- **Input Focus**: Keyboard slides up
- **Form Submit**: Keyboard dismisses
- **Scroll**: Page adjusts to keep input visible

### Orientation Support

- **Portrait**: Single column layout (default)
- **Landscape**: May show two columns on larger screens
- **Rotation**: Layout adjusts smoothly

---

## 🎉 Summary

The Mobile Game Master interface features:

1. **Beautiful gradient design** with glassmorphism
2. **Clear visual hierarchy** for easy navigation
3. **Touch-optimized controls** for mobile devices
4. **Real-time status indicators** for game state
5. **Smooth animations** for professional feel
6. **Color-coded feedback** via toast notifications
7. **Responsive layout** for all screen sizes
8. **Accessible design** with large touch targets

---

**UI Version**: 1.0  
**Design System**: Mobile App Gradient Theme  
**Status**: ✅ Complete & Polished
