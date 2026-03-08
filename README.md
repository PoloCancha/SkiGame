# ⛷ Ski Mountain

A fully playable skiing game built with Python and `pygame`. Control a skier hurtling down a snowy mountain, dodge obstacles, and see how long you can survive. The longer you last, the higher your score — and the faster things get!

---

## Screenshot

*(Run the game to see it in action — all graphics are drawn with pygame primitives, no image files needed.)*

---

## Installation

Make sure you have Python 3 installed, then install the only dependency:

```bash
pip install pygame
```

---

## How to Run

```bash
python ski_game.py
```

---

## Controls

| Key | Action |
|-----|--------|
| ← / → Arrow Keys | Move skier left / right |
| A / D | Move skier left / right |
| ENTER / SPACE | Start game (from menu) |
| R / ENTER | Restart (from game over screen) |
| ESC | Quit |

---

## Obstacle Types

| Obstacle | Description |
|----------|-------------|
| 🪨 Rock | Dark grey jagged boulder |
| 🌲 Tree | Green pine tree |
| 🎿 Jump Ramp | White/grey angled ramp |
| ⛄ Snowman | Two stacked white circles with face |
| ⛰ Mogul | Small white snow mound |

---

## Scoring

- Your score increases continuously the longer you stay on the slope.
- The difficulty (obstacle speed and spawn rate) increases over time.
- Your best score (high score) is tracked during the session and shown on the game over screen.

---

## Game States

1. **Main Menu** — Title screen with instructions. Press ENTER to start.
2. **Playing** — Dodge obstacles! Score climbs every frame.
3. **Wipeout** — Hit an obstacle? Watch the spin-out animation.
4. **Game Over** — Final score and high score displayed. Press R or ENTER to restart.

---

## Technical Notes

- Target resolution: **800 × 600**
- Frame rate: **60 FPS**
- All graphics use `pygame.draw` primitives — no external image or font files required.
- Uses `pygame.font.SysFont` for text rendering.
