# AI Algorithm Deep Dive: How Your Opponent Thinks

## 🧠 The Brain Behind the Board

Your AI opponent uses a sophisticated decision-making algorithm that's also used in chess engines, checkers programs, and many other strategy games. Let's break it down step by step.

---

## 🎯 Core Concept: Minimax Algorithm

### The Idea in Plain English

Imagine you're playing tic-tac-toe and thinking: "If I move here, they'll move there, then I'll move here..." The minimax algorithm does exactly this, but systematically explores EVERY possibility.

**The name "minimax" comes from:**
- **Maximize**: The AI tries to maximize its own score
- **Minimize**: The AI assumes you'll minimize its score (by maximizing yours)

### How It Works: A Simple Example

Let's say it's the AI's turn (playing as Black):

```
Current Position: AI needs to place a piece

Possible Moves:
├── Move A: Place at position 5
│   ├── Your response 1: Place at position 7 → Score: -50
│   ├── Your response 2: Place at position 9 → Score: +100
│   └── Your response 3: Place at position 11 → Score: -20
│   Best for you (worst for AI): -50
│
├── Move B: Place at position 12
│   ├── Your response 1: Place at position 7 → Score: +150
│   ├── Your response 2: Place at position 9 → Score: +200
│   └── Your response 3: Place at position 11 → Score: +180
│   Best for you (worst for AI): +150
│
└── Move C: Place at position 18
    ├── Your response 1: Place at position 7 → Score: +250
    ├── Your response 2: Place at position 9 → Score: +300
    └── Your response 3: Place at position 11 → Score: +280
    Best for you (worst for AI): +250
```

**AI's Decision Process:**
1. For Move A, the worst outcome (assuming you play optimally) is -50
2. For Move B, the worst outcome is +150
3. For Move C, the worst outcome is +250
4. **AI chooses Move C** because even in the worst case, it gets the best score (+250)

This is "minimax" - the AI maximizes the minimum score it can guarantee.

---

## 🌳 The Game Tree

### What Is a Game Tree?

A game tree is a diagram showing all possible moves and counter-moves:

```
                    [Current Position]
                           |
        +------------------+------------------+
        |                  |                  |
    [AI Move 1]       [AI Move 2]       [AI Move 3]
        |                  |                  |
    +---+---+          +---+---+          +---+---+
    |   |   |          |   |   |          |   |   |
[You 1][You 2][You 3] ...
```

### Depth: How Far to Look Ahead

**Depth** is how many "half-moves" (plies) the AI considers:

- **Depth 1**: AI looks at its own moves only (Easy)
  - "If I move here, what's the immediate score?"
  
- **Depth 3**: AI → You → AI (Medium)
  - "If I move here, you move there, then I move there..."
  
- **Depth 5**: AI → You → AI → You → AI (Hard)
  - "Two full turns ahead with counter-moves"

**Why More Depth = Smarter AI:**
- Can see traps and opportunities further ahead
- Plans multi-move combinations
- Avoids moves that look good now but lose later

**Cost of Depth:**
- Depth 1: ~24 positions evaluated (trivial)
- Depth 3: ~500-5,000 positions (fast)
- Depth 5: ~10,000-50,000 positions (1-3 seconds)
- Depth 7: ~millions of positions (too slow)

---

## ✂️ Alpha-Beta Pruning: The Optimization

### The Problem

Without optimization, minimax evaluates EVERY possible position, even ones that don't matter.

### The Solution

Alpha-beta pruning "prunes" (cuts off) branches of the game tree that can't possibly affect the final decision.

### Real-World Analogy

You're shopping for a TV:

```
Store A: Best TV costs $500
Store B: Worst TV costs $600
Store C: Not yet visited

Decision: No need to visit Store B!
```

Why? Because even Store B's best TV is worse than Store A's. You can "prune" Store B from your search.

### How It Works in the Game

```
AI is evaluating Move A, currently best score is +100

Move B's first possibility gives +50
  → Since +50 < +100, and you'll pick your best response
  → Move B can't possibly be better than Move A
  → Skip evaluating Move B's other possibilities!
```

### Two Values Tracked

- **Alpha (α)**: Best score the maximizing player (AI) can guarantee
- **Beta (β)**: Best score the minimizing player (You) can guarantee

**Pruning Rule:**
```
If α ≥ β:
    Stop searching this branch
    (It won't affect the final decision)
```

### Performance Gain

With perfect move ordering (best moves first):
- Alpha-beta can search **10x deeper** in the same time
- Or search the **same depth 10x faster**
- This is why Medium and Hard modes use it

---

## 📊 Position Evaluation: Scoring a Board

### The Evaluation Function

When the AI reaches the end of its search depth, it needs to ask: "Is this position good or bad?"

The evaluation function returns a score:

```python
def evaluate(state, maximizing_player):
    score = 0
    
    # 1. Piece count (most important)
    score += 100 * (my_pieces - opponent_pieces)
    
    # 2. Mobility (legal moves available)
    score += 2 * (my_moves - opponent_moves)
    
    # 3. Board presence
    score += 1 * (9 - pieces_still_in_hand)
    
    # 4. Win/loss states
    if winning:
        score += 10000
    if losing:
        score -= 10000
    
    return score
```

### Breaking Down Each Component

#### 1. Piece Count Difference (×100)
```
My pieces: 7
Your pieces: 5
Difference: +2
Score contribution: +200

This is HUGE because:
- Each piece is a potential mill
- Fewer pieces = easier to block
- Below 3 pieces = instant loss
```

#### 2. Mobility (×2)
```
My legal moves: 8
Your legal moves: 3
Difference: +5
Score contribution: +10

Good mobility means:
- More options to form mills
- Harder for opponent to trap you
- Can respond to threats flexibly
```

#### 3. Board Presence
```
Pieces in hand: 2
Score contribution: +7

Being further in the game is slightly valuable:
- More board control
- Closer to moving phase
- More strategic options
```

#### 4. Win/Loss States (±10,000)
```
If I've won: +10,000 (override everything)
If I've lost: -10,000 (avoid at all costs)

These dominate the evaluation:
- Winning is always best
- Losing is always worst
- Pursue wins, avoid losses
```

### Example Evaluation

```
Position A:
- My pieces: 6, Your pieces: 4 → +200
- My moves: 12, Your moves: 5 → +14
- In hand: 0 → +9
- Total: +223 (Good for AI)

Position B:
- My pieces: 5, Your pieces: 7 → -200
- My moves: 3, Your moves: 15 → -24
- In hand: 1 → +8
- Total: -216 (Bad for AI)

AI prefers Position A!
```

---

## 🎮 Putting It All Together

### The Complete Algorithm Flow

```
1. AI's turn starts

2. Generate all legal moves (e.g., 12 possible moves)

3. For each move:
   a. Make the move on a copy of the board
   b. Call minimax recursively to depth N
   c. At each depth:
      - Generate opponent's responses
      - Recursively evaluate those
      - Track alpha/beta for pruning
   d. At leaf nodes (depth 0), call evaluate()
   e. Backpropagate scores up the tree

4. Select the move with the best score

5. Execute that move
```

### Concrete Example: Depth 3

```
AI's turn (Depth 3):

Move to position 12:
├─ You move to 7 (Depth 2):
│  ├─ AI moves to 3 (Depth 1):
│  │  └─ Evaluate: +150
│  ├─ AI moves to 8 (Depth 1):
│  │  └─ Evaluate: +120
│  └─ AI's best: +150
│  └─ [Return +150]
│
├─ You move to 9 (Depth 2):
│  ├─ AI moves to 3 (Depth 1):
│  │  └─ Evaluate: +200
│  ├─ AI moves to 8 (Depth 1):
│  │  └─ Evaluate: +180
│  └─ AI's best: +200
│  └─ [Return +200]
│
└─ Your worst-case (best for you): +150
└─ [Return +150 to root]

This move guarantees +150 score
```

---

## 🎚️ Difficulty Levels Explained

### Easy (Depth 1, 50% Random)

```python
Search depth: 1 move ahead only
Alpha-beta: No (not needed for depth 1)
Randomness: 50% chance of random move

Characteristics:
- Sees only immediate consequences
- Misses 2-move combinations
- Makes "human-like" mistakes
- Fast (instant response)

Example blunder:
Move looks good now (+50 score)
But next turn you form a mill (-100)
Easy AI doesn't see it coming!
```

### Medium (Depth 3, Alpha-Beta)

```python
Search depth: 3 half-moves (1.5 full turns)
Alpha-beta: Yes
Randomness: None

Characteristics:
- Sees your immediate response + its counter
- Catches simple tactics
- Avoids obvious traps
- Thinks 0.1-0.5 seconds

Example skill:
You threaten a mill at position 7
AI sees: "If I don't block, they form mill next turn"
AI blocks position 7 proactively
```

### Hard (Depth 5, Alpha-Beta)

```python
Search depth: 5 half-moves (2.5 full turns)
Alpha-beta: Yes
Randomness: None

Characteristics:
- Plans complex multi-move sequences
- Sets up traps 2-3 moves ahead
- Evaluates positional play
- Thinks 0.5-3 seconds

Example brilliance:
Turn 1: AI moves piece from 12→7 (looks pointless)
Turn 2: You move your piece
Turn 3: AI forms mill using piece at 7
This was a 3-move plan you didn't see!
```

---

## 🧪 Code Walkthrough

### The Minimax Function

```python
def minimax(state, depth, alpha, beta, maximizing_player, use_alpha_beta):
    # Base case: reached search depth or game over
    if depth == 0 or state.winner is not None:
        return evaluate(state, maximizing_player), None
    
    # Get all legal moves
    moves = state.legal_moves()
    
    # AI's turn (maximizing)
    if state.to_move == maximizing_player:
        best_val = -infinity
        for move in moves:
            # Try this move
            child = state.clone()
            child.apply_move(move)
            
            # Recursively evaluate
            val, _ = minimax(child, depth-1, alpha, beta, 
                           maximizing_player, use_alpha_beta)
            
            # Track best move
            if val > best_val:
                best_val = val
                best_move = move
            
            # Alpha-beta pruning
            if use_alpha_beta:
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break  # Prune!
        
        return best_val, best_move
    
    # Opponent's turn (minimizing)
    else:
        best_val = +infinity
        for move in moves:
            child = state.clone()
            child.apply_move(move)
            val, _ = minimax(child, depth-1, alpha, beta,
                           maximizing_player, use_alpha_beta)
            
            if val < best_val:
                best_val = val
                best_move = move
            
            if use_alpha_beta:
                beta = min(beta, best_val)
                if beta <= alpha:
                    break  # Prune!
        
        return best_val, best_move
```

---

## 💡 Why This Approach Works

### 1. Mathematical Soundness
- Proven optimal for two-player zero-sum games
- If both players play perfectly, outcome is predetermined
- Used in checkers, chess, Go (with modifications)

### 2. Practical Performance
- Alpha-beta makes deep search feasible
- Evaluation heuristic captures game essence
- Adjustable depth allows difficulty scaling

### 3. Strategic Quality
- Plans ahead like human experts
- Balances multiple objectives (pieces, mobility)
- Avoids short-term gains with long-term costs

---

## 🎯 Learning from the AI

### Use the Hint System (Press H)

When you're stuck or learning:
1. Press 'H' to see what the AI would do
2. Compare with your intended move
3. Ask: "Why is the AI's move better?"
4. Analyze: Does it block a threat? Set up a mill?

### Typical AI Strategies You'll See

**Early Game (Placing):**
- Controls center positions (0, 3, 9, 10, 14, 15, 21, 24)
- Creates multiple "two-in-a-row" threats
- Blocks your potential mills

**Mid Game (Moving):**
- Forms and breaks mills repeatedly
- Restricts your mobility
- Maintains material advantage

**Late Game (Flying):**
- Exploits flying mobility ruthlessly
- Forms mills from unexpected positions
- Traps your remaining pieces

---

## 🚀 Advanced Topics

### Transposition Tables
(Not implemented in this version, but common in advanced engines)

Cache previously evaluated positions to avoid re-computing them.

### Opening Books
(Not implemented in this version)

Precomputed optimal opening moves from expert games.

### Iterative Deepening
(Not implemented in this version)

Start with depth 1, then 2, then 3... Stop when time runs out.

### Neural Networks
(Modern approach, not used here)

Train a neural network to evaluate positions instead of using a handcrafted heuristic.

---

## 📚 Further Reading

If you want to dive deeper into game AI:

1. **Minimax Algorithm**: Foundation of game AI
2. **Alpha-Beta Pruning**: Essential optimization
3. **Monte Carlo Tree Search**: Alternative approach (used in Go)
4. **Deep Learning for Games**: AlphaGo, AlphaZero
5. **Chess Programming**: stockfish, komodo engines

---

**Now you understand your opponent! May your understanding lead to victory!** 🏆

