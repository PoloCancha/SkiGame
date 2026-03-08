"""
Ski Mountain Game
A Python skiing game built with pygame.
"""

import pygame
import random
import math
import sys

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
ICY_BLUE = (180, 220, 240)
DARK_BLUE = (100, 160, 200)
MOUNTAIN_WHITE = (230, 240, 250)
MOUNTAIN_BLUE = (160, 200, 225)
SUN_YELLOW = (255, 230, 50)
SUN_GLOW = (255, 245, 150)
DARK_GREY = (60, 60, 60)
MID_GREY = (120, 120, 120)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (101, 67, 33)
RED = (200, 50, 50)
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)
SKIER_BODY = (30, 80, 180)
SKIER_SKIN = (255, 210, 170)
SKI_COLOR = (180, 20, 20)
LIGHT_GREY = (200, 200, 210)
OVERLAY = (0, 0, 80, 180)

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_WIPEOUT = "wipeout"
STATE_GAMEOVER = "gameover"

# Slope x-boundaries (the playable skiing corridor)
SLOPE_LEFT = 80
SLOPE_RIGHT = 720


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def draw_text(surface, text, size, x, y, color=WHITE, center=False):
    font = pygame.font.SysFont("Arial", size, bold=True)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)


# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------

class Snowflake:
    def __init__(self):
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT) if initial else random.randint(-10, -1)
        self.radius = random.randint(1, 3)
        self.speed = random.uniform(1.0, 3.0)
        self.drift = random.uniform(-0.4, 0.4)

    def update(self):
        self.y += self.speed
        self.x += self.drift
        if self.y > SCREEN_HEIGHT:
            self.reset()

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius)


# ---------------------------------------------------------------------------
# Mountain background layer
# ---------------------------------------------------------------------------

class MountainLayer:
    """A single scrolling mountain silhouette layer."""

    def __init__(self, color, height_range, speed, y_offset=0):
        self.color = color
        self.height_range = height_range
        self.speed = speed
        self.tile_height = SCREEN_HEIGHT + 100
        self.scroll_y = 0
        self.y_offset = y_offset
        # Build two vertically-stacked mountain profiles
        self.profile_a = self._build_profile()
        self.profile_b = self._build_profile()

    def _build_profile(self):
        """Return a list of (x, y) points that form the top edge of a mountain silhouette."""
        points = [(0, self.tile_height)]
        x = 0
        while x < SCREEN_WIDTH:
            peak_x = x + random.randint(60, 140)
            peak_y = random.randint(*self.height_range)
            points.append((min(peak_x, SCREEN_WIDTH), peak_y))
            x = peak_x
        points.append((SCREEN_WIDTH, self.tile_height))
        return points

    def update(self):
        self.scroll_y += self.speed
        if self.scroll_y >= self.tile_height:
            self.scroll_y -= self.tile_height

    def draw(self, surface):
        for shift in (self.scroll_y - self.tile_height, self.scroll_y):
            shifted = [(x, y + shift + self.y_offset) for x, y in self.profile_a]
            pygame.draw.polygon(surface, self.color, shifted)


# ---------------------------------------------------------------------------
# Pine tree (decorative side trees)
# ---------------------------------------------------------------------------

class SideTree:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else random.choice(
            list(range(0, SLOPE_LEFT - 10)) + list(range(SLOPE_RIGHT + 10, SCREEN_WIDTH))
        )
        self.y = y if y is not None else random.randint(-20, SCREEN_HEIGHT)
        self.size = random.randint(22, 38)
        self.speed = 2.5

    def update(self):
        self.y += self.speed

    def draw(self, surface):
        x, y, s = self.x, self.y, self.size
        # Trunk
        pygame.draw.rect(surface, BROWN, (x - 3, y + s // 2, 6, s // 3))
        # Three tiers of foliage
        for i, (w_fac, h_off) in enumerate([(1.0, 0), (0.75, s // 4), (0.5, s // 2)]):
            pts = [
                (x, y - s // 2 + h_off - s // 4),
                (x - int(s * w_fac * 0.6), y + h_off),
                (x + int(s * w_fac * 0.6), y + h_off),
            ]
            pygame.draw.polygon(surface, DARK_GREEN if i % 2 == 0 else GREEN, pts)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 60


# ---------------------------------------------------------------------------
# Obstacles
# ---------------------------------------------------------------------------

OBSTACLE_TYPES = ["rock", "tree", "ramp", "snowman", "mogul"]


class Obstacle:
    BASE_SPEED = 3.0

    def __init__(self, speed_multiplier=1.0):
        self.kind = random.choice(OBSTACLE_TYPES)
        self.x = random.randint(SLOPE_LEFT + 30, SLOPE_RIGHT - 30)
        self.y = -40
        self.speed = self.BASE_SPEED * speed_multiplier + random.uniform(-0.3, 0.3)
        self._init_shape()

    def _init_shape(self):
        if self.kind == "rock":
            self.w, self.h = 38, 28
        elif self.kind == "tree":
            self.w, self.h = 36, 50
        elif self.kind == "ramp":
            self.w, self.h = 60, 22
        elif self.kind == "snowman":
            self.w, self.h = 30, 52
        elif self.kind == "mogul":
            self.w, self.h = 44, 20

    def update(self):
        self.y += self.speed

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 60

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        if self.kind == "rock":
            self._draw_rock(surface, x, y)
        elif self.kind == "tree":
            self._draw_tree(surface, x, y)
        elif self.kind == "ramp":
            self._draw_ramp(surface, x, y)
        elif self.kind == "snowman":
            self._draw_snowman(surface, x, y)
        elif self.kind == "mogul":
            self._draw_mogul(surface, x, y)

    def _draw_rock(self, surface, x, y):
        pts = [
            (x - 18, y + 12),
            (x - 14, y - 6),
            (x - 4, y - 14),
            (x + 8, y - 13),
            (x + 18, y - 2),
            (x + 16, y + 12),
        ]
        pygame.draw.polygon(surface, DARK_GREY, pts)
        pygame.draw.polygon(surface, MID_GREY, pts, 2)
        # Highlight
        pygame.draw.line(surface, (140, 140, 140), (x - 10, y - 8), (x + 4, y - 12), 2)

    def _draw_tree(self, surface, x, y):
        pygame.draw.rect(surface, BROWN, (x - 4, y + 10, 8, 16))
        tiers = [(32, 0), (24, 12), (16, 24)]
        for w, dy in tiers:
            pts = [(x, y - 24 + dy - 8), (x - w // 2, y + dy), (x + w // 2, y + dy)]
            pygame.draw.polygon(surface, GREEN, pts)
            pygame.draw.polygon(surface, DARK_GREEN, pts, 1)

    def _draw_ramp(self, surface, x, y):
        pts = [
            (x - 30, y + 10),
            (x + 30, y + 10),
            (x + 30, y - 10),
            (x - 10, y - 10),
        ]
        pygame.draw.polygon(surface, LIGHT_GREY, pts)
        pygame.draw.polygon(surface, WHITE, pts, 2)
        # Arrow hint
        pygame.draw.line(surface, (180, 100, 50), (x - 20, y + 5), (x + 20, y - 5), 2)

    def _draw_snowman(self, surface, x, y):
        # Bottom sphere
        pygame.draw.circle(surface, WHITE, (x, y + 16), 16)
        pygame.draw.circle(surface, LIGHT_GREY, (x, y + 16), 16, 1)
        # Top sphere (head)
        pygame.draw.circle(surface, WHITE, (x, y - 8), 12)
        pygame.draw.circle(surface, LIGHT_GREY, (x, y - 8), 12, 1)
        # Eyes
        pygame.draw.circle(surface, BLACK, (x - 4, y - 10), 2)
        pygame.draw.circle(surface, BLACK, (x + 4, y - 10), 2)
        # Carrot nose
        pygame.draw.polygon(surface, ORANGE, [(x, y - 8), (x + 7, y - 7), (x, y - 6)])
        # Buttons
        for by in [y + 10, y + 16, y + 22]:
            pygame.draw.circle(surface, BLACK, (x, by), 2)

    def _draw_mogul(self, surface, x, y):
        pygame.draw.ellipse(surface, WHITE, (x - 22, y - 10, 44, 20))
        pygame.draw.ellipse(surface, LIGHT_GREY, (x - 22, y - 10, 44, 20), 1)
        # Shadow / depth
        pygame.draw.ellipse(surface, (200, 210, 220), (x - 16, y - 4, 32, 10))


# ---------------------------------------------------------------------------
# Skier
# ---------------------------------------------------------------------------

class Skier:
    WIDTH = 28
    HEIGHT = 40
    SPEED = 5.0

    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = 120
        self.angle = 0.0          # for wipeout spin
        self.wipeout_timer = 0
        self.alive = True

    def get_rect(self):
        return pygame.Rect(
            self.x - self.WIDTH // 2 + 4,
            self.y - self.HEIGHT // 2 + 4,
            self.WIDTH - 8,
            self.HEIGHT - 8,
        )

    def handle_input(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.SPEED
        self.x = clamp(self.x, SLOPE_LEFT + self.WIDTH // 2, SLOPE_RIGHT - self.WIDTH // 2)

    def wipeout(self):
        self.alive = False
        self.wipeout_timer = 90  # 1.5 seconds at 60fps

    def update_wipeout(self):
        if self.wipeout_timer > 0:
            self.wipeout_timer -= 1
            self.angle += 8
        return self.wipeout_timer <= 0

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)

        if not self.alive:
            # Draw spinning skier
            angle_rad = math.radians(self.angle)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

            def rot(dx, dy):
                rx = dx * cos_a - dy * sin_a
                ry = dx * sin_a + dy * cos_a
                return (cx + int(rx), cy + int(ry))

            # Skis (crossed during wipeout)
            pygame.draw.line(surface, SKI_COLOR, rot(-14, 4), rot(14, -4), 3)
            pygame.draw.line(surface, SKI_COLOR, rot(-14, -4), rot(14, 4), 3)
            # Body
            body_pts = [rot(-6, -14), rot(6, -14), rot(8, 14), rot(-8, 14)]
            pygame.draw.polygon(surface, SKIER_BODY, body_pts)
            # Head
            pygame.draw.circle(surface, SKIER_SKIN, rot(0, -20), 8)
        else:
            # Skis
            pygame.draw.line(surface, SKI_COLOR, (cx - 12, cy + 14), (cx - 8, cy + 22), 3)
            pygame.draw.line(surface, SKI_COLOR, (cx + 8, cy + 14), (cx + 12, cy + 22), 3)
            # Body (jacket)
            body_pts = [
                (cx - 8, cy - 10),
                (cx + 8, cy - 10),
                (cx + 10, cy + 12),
                (cx - 10, cy + 12),
            ]
            pygame.draw.polygon(surface, SKIER_BODY, body_pts)
            # Arms / poles
            pygame.draw.line(surface, SKIER_BODY, (cx - 10, cy - 4), (cx - 18, cy + 10), 2)
            pygame.draw.line(surface, SKIER_BODY, (cx + 10, cy - 4), (cx + 18, cy + 10), 2)
            # Pole tips
            pygame.draw.circle(surface, DARK_GREY, (cx - 18, cy + 10), 3)
            pygame.draw.circle(surface, DARK_GREY, (cx + 18, cy + 10), 3)
            # Head
            pygame.draw.circle(surface, SKIER_SKIN, (cx, cy - 16), 9)
            # Helmet
            pygame.draw.arc(surface, RED, (cx - 9, cy - 26, 18, 16), 0, math.pi, 4)
            # Goggles
            pygame.draw.rect(surface, DARK_GREY, (cx - 7, cy - 18, 14, 5), border_radius=2)
            # Scarf
            pygame.draw.rect(surface, ORANGE, (cx - 6, cy - 8, 12, 4))


# ---------------------------------------------------------------------------
# Main Game class
# ---------------------------------------------------------------------------

class SkiGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("⛷  Ski Mountain")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.high_score = 0
        self.state = STATE_MENU

        self._init_background()
        self._new_game()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _init_background(self):
        """Create persistent background elements."""
        self.mountain_layers = [
            MountainLayer(MOUNTAIN_BLUE, (180, 320), 0.4, y_offset=0),
            MountainLayer(MOUNTAIN_WHITE, (220, 380), 0.8, y_offset=30),
        ]
        self.snowflakes = [Snowflake() for _ in range(120)]
        # Side trees (persistent pool, recycled)
        self.side_trees = []
        for _ in range(20):
            self.side_trees.append(SideTree())

    def _new_game(self):
        self.skier = Skier()
        self.obstacles = []
        self.score = 0.0
        self.speed_mult = 1.0
        self.spawn_interval = 90   # frames between spawns
        self.spawn_timer = 0
        self.difficulty_timer = 0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if self.state == STATE_MENU:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = STATE_PLAYING
                        self._new_game()
                elif self.state == STATE_GAMEOVER:
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        self.state = STATE_PLAYING
                        self._new_game()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self):
        # Always animate background
        for layer in self.mountain_layers:
            layer.update()
        for flake in self.snowflakes:
            flake.update()

        # Side trees
        for tree in self.side_trees:
            tree.update()
        self.side_trees = [t for t in self.side_trees if not t.is_off_screen()]
        while len(self.side_trees) < 20:
            self.side_trees.append(SideTree(y=-random.randint(10, 80)))

        if self.state == STATE_PLAYING:
            self._update_playing()
        elif self.state == STATE_WIPEOUT:
            self._update_wipeout()

    def _update_playing(self):
        keys = pygame.key.get_pressed()
        self.skier.handle_input(keys)

        # Score
        self.score += 0.05 * self.speed_mult

        # Difficulty ramp
        self.difficulty_timer += 1
        if self.difficulty_timer % 600 == 0:           # every 10 seconds
            self.speed_mult = min(self.speed_mult + 0.15, 3.0)
            self.spawn_interval = max(30, self.spawn_interval - 8)

        # Spawn obstacles
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.obstacles.append(Obstacle(speed_multiplier=self.speed_mult))

        # Update obstacles
        for obs in self.obstacles:
            obs.update()
        self.obstacles = [o for o in self.obstacles if not o.is_off_screen()]

        # Collision detection
        skier_rect = self.skier.get_rect()
        for obs in self.obstacles:
            if skier_rect.colliderect(obs.get_rect()):
                self.skier.wipeout()
                self.state = STATE_WIPEOUT
                if self.score > self.high_score:
                    self.high_score = self.score
                break

    def _update_wipeout(self):
        for obs in self.obstacles:
            obs.update()
        done = self.skier.update_wipeout()
        if done:
            self.state = STATE_GAMEOVER

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self):
        self._draw_background()
        self._draw_side_trees()
        self._draw_slope_edges()

        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state in (STATE_PLAYING, STATE_WIPEOUT):
            self._draw_obstacles()
            self.skier.draw(self.screen)
            self._draw_hud()
        elif self.state == STATE_GAMEOVER:
            self._draw_obstacles()
            self.skier.draw(self.screen)
            self._draw_gameover()

        self._draw_snowflakes()
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Background drawing
    # ------------------------------------------------------------------

    def _draw_background(self):
        # Sky gradient (approximate using two rects)
        self.screen.fill(ICY_BLUE)
        pygame.draw.rect(self.screen, DARK_BLUE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        pygame.draw.rect(self.screen, ICY_BLUE, (0, SCREEN_HEIGHT // 3, SCREEN_WIDTH, SCREEN_HEIGHT * 2 // 3))

        # Sun
        sun_x, sun_y = 90, 70
        pygame.draw.circle(self.screen, SUN_GLOW, (sun_x, sun_y), 36)
        pygame.draw.circle(self.screen, SUN_YELLOW, (sun_x, sun_y), 28)
        # Sun rays
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = sun_x + int(30 * math.cos(angle))
            y1 = sun_y + int(30 * math.sin(angle))
            x2 = sun_x + int(46 * math.cos(angle))
            y2 = sun_y + int(46 * math.sin(angle))
            pygame.draw.line(self.screen, SUN_YELLOW, (x1, y1), (x2, y2), 3)

        # Mountain layers
        for layer in self.mountain_layers:
            layer.draw(self.screen)

        # Snow ground
        pygame.draw.rect(self.screen, WHITE, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))

    def _draw_slope_edges(self):
        """Draw the ski slope corridor markers."""
        edge_surf = pygame.Surface((8, SCREEN_HEIGHT), pygame.SRCALPHA)
        edge_surf.fill((180, 200, 220, 120))
        # Left edge
        self.screen.blit(edge_surf, (SLOPE_LEFT - 8, 0))
        # Right edge
        self.screen.blit(edge_surf, (SLOPE_RIGHT, 0))
        # Dashed center line
        dash_len = 20
        for y in range(0, SCREEN_HEIGHT, dash_len * 2):
            pygame.draw.rect(self.screen, (220, 230, 240),
                             (SCREEN_WIDTH // 2 - 2, y, 4, dash_len))

    def _draw_side_trees(self):
        for tree in self.side_trees:
            tree.draw(self.screen)

    def _draw_snowflakes(self):
        for flake in self.snowflakes:
            flake.draw(self.screen)

    def _draw_obstacles(self):
        for obs in self.obstacles:
            obs.draw(self.screen)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self):
        score_int = int(self.score)
        draw_text(self.screen, f"Score: {score_int}", 26, SCREEN_WIDTH - 160, 14)
        draw_text(self.screen, f"Best:  {int(self.high_score)}", 20, SCREEN_WIDTH - 160, 46, color=(220, 240, 255))
        # Speed indicator
        bars = int((self.speed_mult - 1.0) / 2.0 * 10)
        draw_text(self.screen, "Speed", 16, 14, 14, color=(200, 220, 240))
        for i in range(10):
            color = (50 + i * 20, 200 - i * 15, 50) if i < bars else (80, 80, 100)
            pygame.draw.rect(self.screen, color, (14 + i * 12, 34, 10, 16))

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------

    def _draw_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 30, 80, 160))
        self.screen.blit(overlay, (0, 0))

        draw_text(self.screen, "⛷  SKI MOUNTAIN", 56, SCREEN_WIDTH // 2, 160, color=WHITE, center=True)
        draw_text(self.screen, "Dodge the obstacles and survive as long as you can!",
                  20, SCREEN_WIDTH // 2, 240, color=(200, 230, 255), center=True)

        draw_text(self.screen, "Controls:", 22, SCREEN_WIDTH // 2, 300, color=SUN_YELLOW, center=True)
        draw_text(self.screen, "← → Arrow Keys  or  A / D", 20, SCREEN_WIDTH // 2, 330,
                  color=(200, 230, 255), center=True)

        draw_text(self.screen, "Obstacles: Rock  •  Tree  •  Jump Ramp  •  Snowman  •  Mogul",
                  17, SCREEN_WIDTH // 2, 380, color=(190, 220, 245), center=True)

        # Blinking prompt
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            draw_text(self.screen, "Press ENTER to Start", 30, SCREEN_WIDTH // 2, 460,
                      color=SUN_YELLOW, center=True)

    def _draw_gameover(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 60, 200))
        self.screen.blit(overlay, (0, 0))

        draw_text(self.screen, "WIPEOUT!", 64, SCREEN_WIDTH // 2, 160, color=RED, center=True)
        draw_text(self.screen, f"Score: {int(self.score)}", 36,
                  SCREEN_WIDTH // 2, 260, color=WHITE, center=True)
        draw_text(self.screen, f"Best: {int(self.high_score)}", 28,
                  SCREEN_WIDTH // 2, 310, color=SUN_YELLOW, center=True)

        if (pygame.time.get_ticks() // 600) % 2 == 0:
            draw_text(self.screen, "Press R or ENTER to Restart", 28,
                      SCREEN_WIDTH // 2, 400, color=WHITE, center=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    game = SkiGame()
    game.run()
