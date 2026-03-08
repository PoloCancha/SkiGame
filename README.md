# 🎿 Ski Mountain Game

A fully playable skiing game built with Python and `pygame`. Control a skier down a snowy mountain, dodge obstacles, and see how long you can survive!

---

## 📸 Features

- Scrolling mountain background with layered silhouettes
- Animated skier with wipeout effect on collision
- 5 distinct obstacle types drawn with `pygame.draw` primitives — no image files needed
- Falling snowflakes and pine trees along the slope
- Continuous score that increases the longer you survive
- Difficulty scaling: obstacles get faster and spawn more frequently over time
- High score tracking within a session
- Main Menu, Playing, and Game Over screens

---

## 🛠 Installation

Make sure you have **Python 3.7+** installed, then install the only dependency:

```bash
pip install pygame
```

Or use the `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

```bash
python ski_game.py
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| ← Left Arrow / A | Move skier left |
| → Right Arrow / D | Move skier right |
| ENTER | Start game (from menu) / Restart (from game over) |
| R | Restart after game over |

---

## 🪨 Obstacle Types

| Obstacle | Description |
|----------|-------------|
| **Rock** | Dark grey jagged boulder |
| **Tree** | Green layered pine tree |
| **Jump Ramp** | White/grey angled ramp |
| **Snowman** | Two stacked white circles with face and hat |
| **Mogul** | Small white snow mound |

---

## 🏆 Scoring

- Your **score increases continuously** the longer you survive
- Obstacles speed up over time, making survival harder
- Your **best score** for the session is shown on the Game Over screen

---

## 📁 File Structure

```
ski_game.py       # Main game (all logic, no external assets)
requirements.txt  # Just: pygame
README.md         # This file
```