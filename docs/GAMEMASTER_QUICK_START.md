# 🎮 Mobile Game Master - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1️⃣ Access the Interface
Open your mobile browser and navigate to:
```
http://your-server:5000/mobile/gamemaster
```

### 2️⃣ Start a Game
1. Select game type (301, 401, 501, or Cricket)
2. Enter player names (one per line)
3. Click **"Start Game"**

### 3️⃣ Control the Game
- Click **"Next Player"** to advance turns
- Use **"Manual Score"** to enter scores
- Click **"End Game"** when finished

---

## 🎯 Common Tasks

### Starting a 501 Game
```
1. Game Type: 501
2. Double Out: ☑ (checked)
3. Players:
   Alice
   Bob
4. Click "Start Game"
```

### Adding a Player Mid-Game
```
1. Scroll to "Players" section
2. Enter player name
3. Click "Add Player"
```

### Submitting a Score
```
1. Scroll to "Manual Score Entry"
2. Enter score (e.g., 60)
3. Select multiplier (e.g., Triple)
4. Click "Submit Score"
   → Result: 180 points
```

### Advancing to Next Player
```
1. Click "Next Player" button
2. Watch active player change
3. Status card updates automatically
```

---

## 🎨 Visual Guide

### What You'll See

#### Status Card (Top)
```
┌─────────────────────────────┐
│ 🎮 Game Status              │
│ ● Online | Game: 501        │
│ Current: Alice              │
└─────────────────────────────┘
```
- **Green dot** = Connected
- **Gray dot** = Disconnected
- Shows current game type and player

#### Active Player (Red Glow)
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ▶ Alice      Score: 321   ┃  ← Current player
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  Bob          Score: 501     ← Waiting
```

#### Toast Notifications
```
┌─────────────────────────────┐
│ ✅ Game started!            │  ← Success (green)
└─────────────────────────────┘

┌─────────────────────────────┐
│ ❌ Error: Need 2+ players   │  ← Error (red)
└─────────────────────────────┘
```

---

## ⚡ Keyboard Shortcuts

Currently, all actions require button clicks. Future versions may include:
- `Space` - Next player
- `S` - Submit score
- `P` - Pause game
- `E` - End game

---

## 🔧 Troubleshooting

### Problem: Can't start game
**Solution**: Ensure you have at least 2 players entered

### Problem: Buttons are grayed out
**Solution**: No active game - start a new game first

### Problem: "Disconnected" status
**Solution**: Check your internet connection and refresh the page

### Problem: Scores not updating
**Solution**: Check WebSocket connection (green dot in status card)

---

## 📱 Mobile Tips

### Best Practices
- ✅ Use in **portrait mode** for best experience
- ✅ Keep screen **brightness up** for outdoor use
- ✅ Enable **"Keep screen on"** during games
- ✅ Use **WiFi** for stable connection

### Touch Gestures
- **Tap** - Select/activate
- **Scroll** - Navigate sections
- **Long press** - (No special actions currently)

---

## 🎮 Game Types Explained

### 301 / 401 / 501
- Start with 301/401/501 points
- Subtract scores to reach exactly 0
- **Double Out**: Must finish on a double

### Cricket
- Hit numbers 15-20 and bullseye
- Close numbers by hitting 3 times
- Score points on closed numbers

---

## 🎯 Pro Tips

### For Efficient Game Management
1. **Pre-enter players** before game starts
2. **Use manual score** for quick corrections
3. **Keep status card visible** to track current player
4. **Watch toast notifications** for confirmation

### For Smooth Gameplay
1. **Advance player immediately** after throw
2. **Double-check scores** before submitting
3. **Pause game** during breaks
4. **End game properly** to save results

---

## 📊 Understanding the Interface

### Sections (Top to Bottom)

1. **Header** - Navigation and title
2. **Status Card** - Current game info
3. **Start New Game** - Game setup form
4. **Players** - Active players list
5. **Game Controls** - Next, Pause, End
6. **Manual Score** - Score entry form
7. **Game State** - Technical details (optional)

### Button States

| State | Appearance | Meaning |
|-------|------------|---------|
| **Active** | Blue, bright | Ready to click |
| **Disabled** | Gray, dim | Not available |
| **Loading** | Spinning icon | Processing |
| **Hover** | Lifted up | Ready to tap |

---

## 🔔 Notification Types

| Icon | Color | Meaning |
|------|-------|---------|
| ✅ | Green | Success - action completed |
| ❌ | Red | Error - action failed |
| ⚠️ | Orange | Warning - check input |
| ℹ️ | Blue | Info - status update |

---

## 🎉 Quick Reference Card

### Essential Actions
```
Start Game:     Select type → Enter players → Start
Next Player:    Click "Next Player" button
Add Player:     Enter name → Click "Add Player"
Manual Score:   Enter score → Select multiplier → Submit
Pause Game:     Click "Pause Game" button
End Game:       Click "End Game" → Confirm
```

### Status Indicators
```
● Green  = Connected & ready
● Gray   = Disconnected
▶ Symbol = Current player
Red Glow = Active player card
```

### Score Multipliers
```
Single:      1x (e.g., 20 = 20)
Double:      2x (e.g., 20 = 40)
Triple:      3x (e.g., 20 = 60)
Bull:        25 points
Double Bull: 50 points
```

---

## 📞 Need Help?

### Documentation
- **Full Guide**: `/docs/MOBILE_GAMEMASTER_GUIDE.md`
- **UI Reference**: `/docs/MOBILE_GAMEMASTER_UI_REFERENCE.md`
- **Implementation**: `/docs/MOBILE_GAMEMASTER_IMPLEMENTATION.md`

### Common Questions

**Q: Can I use this on a tablet?**  
A: Yes! The interface is responsive and works on all screen sizes.

**Q: Does it work offline?**  
A: No, you need an active internet connection for real-time updates.

**Q: Can multiple game masters control the same game?**  
A: Yes! All connected game masters see real-time updates.

**Q: What happens if I lose connection?**  
A: The interface will show "Disconnected" and attempt to reconnect automatically.

---

## 🎊 You're Ready!

You now know everything you need to control dart games from your mobile device. 

**Happy Game Mastering!** 🎯📱

---

**Version**: 1.0  
**Last Updated**: 2025  
**Status**: ✅ Production Ready