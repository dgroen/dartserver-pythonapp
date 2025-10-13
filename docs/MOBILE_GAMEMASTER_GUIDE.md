# Mobile Game Master Guide

## 🎯 Overview

The Mobile Game Master interface provides complete control over dart games from your mobile device. This guide covers all features and functionality available to game masters.

---

## 📱 Accessing Game Master

### URL
```
https://your-domain.com/mobile/gamemaster
```

### Requirements
- Active user account
- Game Master role (or admin role)
- Mobile device with modern browser
- Active internet connection

---

## ✨ Features

### 1. **Game Status Monitor**
Real-time display of current game status:
- 🟢 **Online**: Game in progress
- 🔴 **Offline**: No active game
- **Game Type**: 301, 401, 501, or Cricket
- **Current Player**: Who's turn it is

### 2. **Start New Game**
Create and configure a new dart game:

#### Game Types
- **301**: Start with 301 points, first to zero wins
- **401**: Start with 401 points, first to zero wins
- **501**: Start with 501 points, first to zero wins (most common)
- **Cricket**: Strategic game targeting specific numbers

#### Options
- **Double Out**: Require finishing with a double
- **Players**: Add 2 or more players (one per line)

#### Steps
1. Select game type from dropdown
2. Check "Double Out" if required
3. Enter player names (one per line)
4. Tap "🚀 Start Game"

### 3. **Player Management**

#### View Players
- See all players in current game
- Current player highlighted with ▶ indicator
- View each player's current score

#### Add Player During Game
1. Enter new player name in text field
2. Tap "➕ Add Player"
3. Player joins at end of rotation

### 4. **Game Controls**

#### Next Player (⏭️)
- Advance to next player in rotation
- Use when current player finishes their turn
- Automatically cycles through all players

#### Pause Game (⏸️)
- Temporarily pause the game
- Button changes to "▶️ Resume Game"
- Tap again to resume

#### End Game (🛑)
- Terminate current game
- Confirmation required
- Saves game results
- Clears all game state

### 5. **Manual Score Entry**

Submit scores manually when dartboard is offline or for corrections:

#### Score Entry
1. Enter score value (0-60)
2. Select multiplier:
   - **Single**: Normal hit
   - **Double**: 2x score
   - **Triple**: 3x score
   - **Bull**: 25 points
   - **Double Bull**: 50 points
3. Tap "📝 Submit Score"

#### Common Scores
- Single 20: 20 points
- Double 20: 40 points
- Triple 20: 60 points (maximum)
- Bull: 25 points
- Double Bull: 50 points

### 6. **Game State Display**

View complete game state in JSON format:
- All player data
- Current scores
- Game configuration
- Turn information

#### Refresh State
- Tap "🔄 Refresh State" to update
- Automatically updates via WebSocket
- Useful for troubleshooting

---

## 🎮 Typical Game Flow

### Starting a Game
```
1. Open Game Master interface
2. Select game type (e.g., 501)
3. Check "Double Out" if desired
4. Enter player names:
   Alice
   Bob
   Charlie
5. Tap "Start Game"
6. ✅ Game begins with first player
```

### During Game
```
1. Players take turns throwing darts
2. Scores automatically recorded by dartboard
3. Or use Manual Score Entry if needed
4. Tap "Next Player" to advance turns
5. Monitor current player and scores
6. Add players if needed
```

### Ending Game
```
1. Game ends automatically when player reaches zero
2. Or tap "End Game" to terminate early
3. Confirm termination
4. View results in Game Results page
```

---

## 🔧 Advanced Features

### WebSocket Connection
- Real-time updates via WebSocket
- Connection status shown in header
- Automatic reconnection on disconnect
- Toast notifications for all events

### Offline Support
- Page cached for offline access
- Requires online connection for game control
- Service worker provides offline UI

### Touch Optimized
- Large touch targets (44x44px minimum)
- Visual feedback on all interactions
- Smooth animations and transitions
- Optimized for one-handed use

---

## 📊 Game Types Explained

### 301/401/501
**Objective**: Reduce score from starting value to exactly zero

**Rules**:
- Each player starts with X points (301, 401, or 501)
- Subtract dart scores from total
- Must reach exactly zero to win
- If "Double Out" enabled, must finish with a double
- Bust if you go below zero (turn ends, score reverts)

**Strategy**:
- Aim for high scores (triple 20 = 60)
- Plan your finish (leave even number for double out)
- Common finishes: 40 (double 20), 32 (double 16)

### Cricket
**Objective**: Close all numbers (15-20 and bull) before opponent

**Rules**:
- Target numbers: 15, 16, 17, 18, 19, 20, Bull
- Hit each number 3 times to "close" it
- Score points on closed numbers if opponent hasn't closed
- First to close all numbers with most points wins

**Strategy**:
- Close high-value numbers first (20, 19, 18)
- Block opponent by closing their open numbers
- Build point lead on closed numbers

---

## 🎯 Best Practices

### Game Setup
- ✅ Verify all player names before starting
- ✅ Confirm game type and rules
- ✅ Test dartboard connection
- ✅ Ensure good lighting

### During Game
- ✅ Monitor current player indicator
- ✅ Watch for automatic score updates
- ✅ Use manual entry only when needed
- ✅ Keep device charged

### Score Entry
- ✅ Double-check score values
- ✅ Verify multiplier selection
- ✅ Confirm score before submitting
- ✅ Watch for bust conditions

### Troubleshooting
- ✅ Refresh game state if scores seem wrong
- ✅ Check WebSocket connection status
- ✅ Verify dartboard is online
- ✅ Restart game if major issues occur

---

## 🐛 Troubleshooting

### Game Won't Start
**Problem**: "Start Game" button doesn't work

**Solutions**:
1. Verify at least 2 players entered
2. Check internet connection
3. Refresh page and try again
4. Check browser console for errors

### Scores Not Updating
**Problem**: Dartboard hits not reflected in scores

**Solutions**:
1. Check dartboard connection status
2. Verify WebSocket connection (green dot)
3. Use manual score entry as backup
4. Refresh game state

### Can't Advance to Next Player
**Problem**: "Next Player" button disabled

**Solutions**:
1. Verify game is active (green status)
2. Check WebSocket connection
3. Refresh page
4. End game and start new one if stuck

### WebSocket Disconnected
**Problem**: Red connection indicator

**Solutions**:
1. Check internet connection
2. Wait for automatic reconnection
3. Refresh page if doesn't reconnect
4. Check server status

### Manual Score Not Working
**Problem**: Score submission fails

**Solutions**:
1. Verify game is active
2. Check score value is valid (0-60)
3. Ensure WebSocket connected
4. Try refreshing page

---

## 🔐 Permissions

### Required Permissions
- **game:create** - Start new games
- **game:manage** - Control game flow
- **player:add** - Add players to game
- **score:write** - Submit manual scores

### Role Requirements
- **Game Master** role - Full access to all features
- **Admin** role - Full access to all features
- **Player** role - Limited access (view only)

---

## 📱 Mobile Optimization

### Supported Devices
- ✅ iPhone (iOS 12+)
- ✅ Android phones (Android 5.0+)
- ✅ Tablets (iPad, Android tablets)
- ✅ Any device with modern browser

### Supported Browsers
- ✅ Chrome for Android
- ✅ Safari for iOS
- ✅ Samsung Internet
- ✅ Firefox for Android
- ✅ Edge for Android

### Screen Sizes
- Optimized for 320px - 768px width
- Responsive layout adapts to screen
- Portrait and landscape supported
- Touch targets 44x44px minimum

---

## 🎨 UI Elements

### Status Indicators
- 🟢 **Green Dot**: Game active / Connected
- 🔴 **Red Dot**: No game / Disconnected
- ⏸️ **Pause Icon**: Game paused
- ▶ **Play Icon**: Current player

### Buttons
- 🚀 **Start Game**: Begin new game
- ⏭️ **Next Player**: Advance turn
- ⏸️ **Pause**: Pause/resume game
- 🛑 **End Game**: Terminate game
- ➕ **Add Player**: Add new player
- 📝 **Submit Score**: Enter manual score
- 🔄 **Refresh**: Update game state

### Toast Notifications
- 🟢 **Green**: Success messages
- 🔴 **Red**: Error messages
- 🟡 **Yellow**: Warning messages
- 🔵 **Blue**: Info messages

---

## 📈 Tips & Tricks

### Efficiency
1. **Use Keyboard**: On tablets, use keyboard for faster player entry
2. **Swipe Navigation**: Swipe from edge to open menu
3. **Quick Actions**: Tap status card to refresh
4. **Shortcuts**: Long-press buttons for additional options (future)

### Game Management
1. **Pre-configure**: Set up player list before game night
2. **Templates**: Save common game configurations (future)
3. **Quick Start**: Use default settings for faster setup
4. **Backup**: Keep paper scorecard as backup

### Score Tracking
1. **Verify**: Always verify automatic scores
2. **Manual Entry**: Use for corrections, not primary input
3. **Patterns**: Watch for scoring patterns to detect issues
4. **History**: Check game state JSON for detailed history

---

## 🔗 Related Pages

- [Mobile App Home](/mobile) - Main mobile interface
- [Gameplay](/mobile/gameplay) - Player view
- [Results](/mobile/results) - Game history
- [Dartboard Setup](/mobile/dartboard-setup) - Hardware configuration

---

## 📞 Support

### Getting Help
- Check this guide first
- Review troubleshooting section
- Check server logs for errors
- Contact system administrator

### Reporting Issues
Include:
- Device type and OS version
- Browser name and version
- Steps to reproduce issue
- Screenshots if applicable
- Error messages from console

---

## 🎉 Quick Reference

### Essential Actions
| Action | Steps |
|--------|-------|
| Start Game | Select type → Enter players → Tap Start |
| Next Player | Tap ⏭️ Next Player button |
| Manual Score | Enter value → Select multiplier → Submit |
| Add Player | Enter name → Tap ➕ Add Player |
| End Game | Tap 🛑 End Game → Confirm |

### Keyboard Shortcuts (Future)
| Key | Action |
|-----|--------|
| N | Next player |
| P | Pause/Resume |
| E | End game |
| R | Refresh state |
| M | Focus manual score |

---

## 📝 Version History

### Version 2.0 (Current)
- ✅ Complete UI redesign with gradient background
- ✅ Glassmorphism effects
- ✅ Real-time WebSocket integration
- ✅ Enhanced player management
- ✅ Manual score entry
- ✅ Game state display
- ✅ Toast notifications
- ✅ Mobile-optimized controls

### Version 1.0
- Basic game master functionality
- Simple player management
- Manual score entry
- Basic game controls

---

**Document Version**: 2.0  
**Last Updated**: 2025  
**Status**: ✅ Production Ready