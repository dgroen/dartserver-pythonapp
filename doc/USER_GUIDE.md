# User Guide

## Getting Started

### Accessing the Application

1. Navigate to the application URL in your browser
2. If authentication is enabled, you'll see a login page
3. Enter your credentials to log in
4. You'll be redirected to the game board

### User Roles

```
┌─────────────────────────────────────────────────────────┐
│ ROLE-BASED ACCESS CONTROL                               │
├─────────────────────────────────────────────────────────┤
│ 🟢 Player                                               │
│    • View game board                                    │
│    • Submit dart scores                                 │
│    • View current game state                            │
│                                                         │
│ 🟡 Game Master                                          │
│    • All Player permissions                             │
│    • Create and manage games                            │
│    • Add/remove players                                 │
│    • Control game flow                                  │
│    • Access control panel                               │
│                                                         │
│ 🔴 Admin                                                │
│    • All permissions                                    │
│    • Full system access                                │
│    • User management (via WSO2)                         │
└─────────────────────────────────────────────────────────┘
```

## Playing a Game

### Starting a New Game

1. **Access Control Panel**
   - Click "Control" or navigate to /control
   - Requires Game Master role

2. **Create Game**
   - Select game type: 301, 401, 501, or Cricket
   - Enter player names
   - Click "Start Game"

3. **Game Board**
   - Real-time score display
   - Current player highlighted
   - Automatic UI refresh

### Submitting Scores

#### Via RabbitMQ (Automated)
- Send JSON message to RabbitMQ exchange
- Format: {"score": 20, "multiplier": "TRIPLE", "user": "Player 1"}
- Multipliers: SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL

#### Via Web Interface (Manual)
- Use the score entry interface
- Select score and multiplier
- Submit to record dart

#### Via REST API
- POST /api/score
- JSON: {"score": 20, "multiplier": "TRIPLE"}

### Game Rules

#### 301/401/501
- Start with target points (301/401/501)
- Each dart score subtracts from total
- First to reach exactly 0 wins
- Going below 0 = "bust" (score resets)
- Last dart must be double (if enabled)

#### Cricket
- Hit numbers: 15, 16, 17, 18, 19, 20, Bull
- Each number needs 3 hits to "open"
- Unopened numbers: 1 point per hit
- Opened numbers: Regular points
- Closed numbers: No points
- Highest score wins

### Real-Time Updates

- All connected clients automatically refresh
- Score updates appear instantly
- Game state synchronized across devices
- WebSocket connection status shown

## Features

### Game Board
- **Scoreboard**: Current scores for all players
- **Turn Indicator**: Shows current player
- **Game Info**: Type, rules, status
- **History**: Recent scores and moves

### Control Panel
- **Game Management**: Start, pause, end games
- **Player Management**: Add, remove players
- **Manual Entry**: Enter scores manually
- **Game History**: View previous games
- **Settings**: Configure game options

### Mobile Support
- Responsive web interface
- Works on tablets and phones
- Touch-optimized controls
- Mobile game master interface

### Sound & Announcements
- Text-to-speech announcements
- Sound effects (optional)
- Scoring feedback

## Frequently Asked Questions

**Q: How do I reset a game?**
A: Use the Control Panel → End Game → Start New Game

**Q: Can I play with more than 6 players?**
A: Currently limited to 6 players for performance

**Q: What if I enter the wrong score?**
A: In manual mode, only Game Masters can correct scores

**Q: How do I log out?**
A: Click your profile name → Logout

**Q: Does the app work offline?**
A: Scores require connectivity for real-time sync

**Q: Can I export game history?**
A: Export functionality available in Control Panel

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| N | New game |
| P | Next player |
| S | Submit score |
| C | Control panel |
| ? | Help |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't log in | Check credentials in authentication system |
| Game won't start | Ensure all players are valid |
| Scores not updating | Check WebSocket connection |
| Can't submit score | Verify your role permissions |

## Tips & Tricks

- **Fast Entry**: Use keyboard shortcuts for rapid scoring
- **Multiple Devices**: Connect multiple screens for optimal viewing
- **Broadcast**: Project on big screen for audience
- **Mobile**: Use mobile interface for mobile game master on phone

## Getting Help

- API Documentation: /apidocs
- System Status: /api/health
- Support: Contact system administrator
