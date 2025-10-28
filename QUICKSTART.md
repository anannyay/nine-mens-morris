# Quick Start Guide

## 🚀 Get Playing in 2 Minutes

### Easy Way (MacOS/Linux)
```bash
./run.sh
```
The script automatically creates venv, installs dependencies, and launches the game!

### Manual Way (All Platforms)

#### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Launch the Game
```bash
python main.py
```

**Note:** Remember to activate the virtual environment (`source venv/bin/activate`) each time you want to play!

### 3. Navigate the Welcome Screen
When the game opens, you'll see three options:
- **Learn AI** - Understand how your AI opponent thinks
- **View Rules** - Learn the game rules
- **Start Game** - Jump right in!

---

## 🎮 First Time Playing?

### Recommended Path

**Step 1:** Click "View Rules"
- Spend 2 minutes reading the 4 rule cards
- Understand the three phases: Placing → Moving → Flying
- Learn about mills (3 in a row)

**Step 2:** Click "Learn AI" (on welcome screen)
- See how the minimax algorithm works
- Understand why the AI makes certain moves
- Learn about the three difficulty levels

**Step 3:** Click "Start Game"
- You're White, you go first!
- The game starts in "Placing" phase
- Click any empty point to place your piece

---

## 🎯 Your First Game

### Turn 1-9: Placing Phase
1. Click an empty position to place a piece
2. Try to form a line of 3 (a "mill")
3. When you form a mill, click an opponent piece to remove it
4. AI will do the same!

**Tip:** Control the center positions - they're part of more mills!

### Turn 10+: Moving Phase
1. Click one of your pieces to select it
2. Valid destinations will highlight in gold
3. Click the destination to move
4. Keep forming mills to capture opponent pieces

**Tip:** Break and reform the same mill to capture repeatedly!

### Flying Phase (if you reach 3 pieces)
1. With only 3 pieces left, you can jump anywhere
2. This is a huge advantage!
3. Form mills from unexpected positions

---

## ⌨️ Essential Keyboard Shortcuts

While playing:
- **H** - Hint (see what the AI would do)
- **U** - Undo your last move
- **N** - Start a new game
- **ESC** - Return to welcome screen

---

## 🤖 Playing Against AI

### Enable AI
```bash
# Start with AI opponent
python main.py --ai

# Choose AI difficulty
python main.py --ai --difficulty easy
python main.py --ai --difficulty medium
python main.py --ai --difficulty hard
```

### In-Game AI Toggle
Press **A** to toggle AI on/off during the game

### Change Difficulty
- Press **E** for Easy
- Press **M** for Medium  
- Press **H** for Hard

---

## 📖 Learning Resources

After your first game, check out:

1. **README.md** - Complete documentation
2. **AI_EXPLAINED.md** - Deep dive into how the AI works
3. **FEATURES.md** - All UI features explained

---

## 💡 Pro Tips for Beginners

### Strategy Tips
1. **Control the center** - Center points are in more mills
2. **Create "two-in-a-row"** - Set up multiple mill threats
3. **Block opponent mills** - Defense is important!
4. **Plan 2 moves ahead** - Think like the AI
5. **Flying phase is decisive** - Protect your last 3 pieces

### Learning Tips
1. **Use hints liberally** (H key) - Learn from the AI
2. **Experiment with undo** (U key) - Try different moves
3. **Start on Easy** - Build confidence
4. **Watch the AI** - See what moves it makes
5. **Play multiple games** - Pattern recognition is key

### UI Tips
1. **Hover over positions** - See interactive feedback
2. **Watch mill indicators** - Green/red rings show active mills
3. **Drag pieces** - In moving phase, drag instead of click
4. **Check the sidebar** - Always shows current game state
5. **Read control panel** - Reminder of all shortcuts

---

## 🎨 Visual Guide

### Screen Layout (Game)

```
┌─────────────────────────────────────────────────────────┐
│  White's Turn | Phase: Placing                          │
│                                                           │
│   ┌─────────────────┐         ┌─────────────────────┐  │
│   │                 │         │  GAME STATUS         │  │
│   │                 │         │  - Turn: White       │  │
│   │   GAME BOARD    │         │  - Phase: Placing    │  │
│   │                 │         │  - Pieces: W:9 B:9   │  │
│   │   (3 squares)   │         ├─────────────────────┤  │
│   │                 │         │  CONTROLS            │  │
│   │                 │         │  H: Hint             │  │
│   │                 │         │  U: Undo             │  │
│   └─────────────────┘         │  N: New game         │  │
│                                │  A: Toggle AI        │  │
│                                ├─────────────────────┤  │
│                                │  AI STATUS           │  │
│                                │  AI: ON (Black)      │  │
│                                │  Difficulty: Medium  │  │
│                                └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Welcome Screen Layout

```
┌─────────────────────────────────────────────────────────┐
│           NINE MEN'S MORRIS                              │
│        Strategic Board Game with AI                      │
│                                                           │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│   │  GAME   │    │  THREE  │    │  MILLS  │            │
│   │OBJECTIVE│    │ PHASES  │    │CAPTURING│            │
│   │         │    │         │    │         │            │
│   │ • Form  │    │ 1.Place │    │ • Form  │            │
│   │   mills │    │ 2.Move  │    │   3 in  │            │
│   │ • Capture│    │ 3.Fly   │    │   row   │            │
│   └─────────┘    └─────────┘    └─────────┘            │
│                                                           │
│     [Learn AI]  [View Rules]  [Start Game]              │
│                                                           │
│     Press ESC to return to welcome screen anytime       │
└─────────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Game Won't Launch
```bash
# Make sure pygame is installed
pip install pygame

# Try running directly
python -m morris.enhanced_ui
```

### Performance Issues
```bash
# Use classic UI (lighter)
python main.py --classic

# Or set AI to Easy (faster)
python main.py --ai --difficulty easy
```

### Display Issues
```bash
# Check your screen resolution (minimum 1200x800)
# The game window is 1200x800 pixels
```

---

## 🎯 Your First Hour Plan

### Minutes 0-5: Setup
- Install dependencies
- Launch game
- Navigate welcome screen

### Minutes 5-10: Learn
- Read the rules cards
- Read AI explanation cards
- Understand the three phases

### Minutes 10-30: Play Solo
- Start a game without AI
- Practice placing pieces
- Experiment with mills
- Use undo freely to explore

### Minutes 30-45: Challenge Easy AI
- Enable AI on Easy mode
- Use hints to learn
- Analyze AI moves
- Play 2-3 games

### Minutes 45-60: Level Up
- Try Medium difficulty
- Read AI_EXPLAINED.md for strategy
- Apply what you learned
- Challenge yourself!

---

## 🏆 First Milestones

- ✅ Place all 9 pieces
- ✅ Form your first mill
- ✅ Capture an opponent piece
- ✅ Complete a full game
- ✅ Beat Easy AI
- ✅ Beat Medium AI
- ✅ Reach flying phase with 3 pieces
- ✅ Beat Hard AI (ultimate challenge!)

---

## 🤝 Need Help?

Check these resources in order:

1. **In-Game Help**: Press ESC → View Rules
2. **README.md**: Complete feature documentation
3. **AI_EXPLAINED.md**: Understand the AI strategy
4. **FEATURES.md**: UI feature walkthrough

---

**Ready to play? Launch the game and enjoy!** 🎮

```bash
python main.py
```

