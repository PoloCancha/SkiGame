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
OFF_WHITE = (230, 240, 255)
ICY_BLUE = (180, 220, 255)
SKY_BLUE = (135, 206, 235)
DEEP_SKY = (100, 180, 230)
YELLOW = (255, 220, 50)
DARK_GREY = (70, 70, 75)
GREY = (130, 130, 140)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BLACK = (20, 20, 30)
RED = (200, 50, 50)
BROWN = (139, 90, 43)
LIGHT_BLUE = (200, 230, 255)
MOUNTAIN_COLOR = (210, 225, 245)
MOUNTAIN_SHADOW = (170, 195, 225)
ORANGE = (255, 140, 0)
SKIN = (255, 210, 170)

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_WIPEOUT = "wipeout"
STATE_GAMEOVER = "gameover"

# Obstacle types
OBS_ROCK = "rock"
OBS_TREE = "tree"
OBS_RAMP = "ramp"
OBS_SNOWMAN = "snowman"
OBS_MOGUL = "mogul"


# ---------------------------------------------------------------------------
# Helper drawing functions
# ---------------------------------------------------------------------------

def draw_pine_tree(surface, x, y, size, color=GREEN, dark_color=DARK_GREEN):
    """Draw a pine tree centered at (x, y) with given trunk-base height."""
    trunk_w = max(4, size // 6)
    trunk_h = max(8, size // 3)
    # Trunk
    pygame.draw.rect(surface, BROWN,
                     (x - trunk_w // 2, y - trunk_h, trunk_w, trunk_h))
    # Three layered triangles
    for i, (frac, width_frac) in enumerate([(1.0, 1.0), (0.7, 0.85), (0.45, 0.7)]):
        pts = [
            (x, y - trunk_h - int(size * frac)),
            (x - int(size * width_frac) // 2, y - trunk_h - int(size * (frac - 0.35))),
            (x + int(size * width_frac) // 2, y - trunk_h - int(size * (frac - 0.35))),
        ]
        pygame.draw.polygon(surface, color if i % 2 == 0 else dark_color, pts)


def draw_skier(surface, x, y, angle=0, wipeout_frame=0):
    """Draw the skier at (x, y). angle rotates the whole figure (wipeout)."""
    # Build all parts on a temporary surface so we can rotate as a unit
    size = 60
    tmp = pygame.Surface((size * 2, size * 2), pygame.SRCCOLORKEY)
    tmp.set_colorkey(BLACK)
    tmp.fill(BLACK)
    cx, cy = size, size  # centre of temp surface

    # --- Skis ---
    ski_len = 26
    ski_w = 4
    ski_color = (20, 20, 180)
    # Left ski
    pygame.draw.rect(tmp, ski_color,
                     (cx - 14, cy + 12, ski_len, ski_w), border_radius=2)
    # Right ski (slightly offset)
    pygame.draw.rect(tmp, ski_color,
                     (cx - 12, cy + 16, ski_len, ski_w), border_radius=2)

    # --- Poles ---
    pygame.draw.line(tmp, GREY, (cx - 10, cy + 5), (cx - 22, cy + 20), 2)
    pygame.draw.line(tmp, GREY, (cx + 6, cy + 5), (cx + 18, cy + 20), 2)

    # --- Body / Jacket (red) ---
    body_pts = [
        (cx - 8, cy),
        (cx + 8, cy),
        (cx + 10, cy + 14),
        (cx - 10, cy + 14),
    ]
    pygame.draw.polygon(tmp, RED, body_pts)

    # --- Arms ---
    pygame.draw.line(tmp, RED, (cx - 8, cy + 4), (cx - 18, cy + 10), 5)
    pygame.draw.line(tmp, RED, (cx + 8, cy + 4), (cx + 18, cy + 10), 5)

    # --- Legs ---
    pygame.draw.line(tmp, (40, 40, 140), (cx - 5, cy + 14), (cx - 8, cy + 22), 5)
    pygame.draw.line(tmp, (40, 40, 140), (cx + 5, cy + 14), (cx + 8, cy + 22), 5)

    # --- Head ---
    pygame.draw.circle(tmp, SKIN, (cx, cy - 6), 8)
    # Helmet
    pygame.draw.arc(tmp, (20, 20, 180),
                    pygame.Rect(cx - 8, cy - 14, 16, 16), 0, math.pi, 4)
    pygame.draw.line(tmp, (20, 20, 180), (cx - 8, cy - 6), (cx + 8, cy - 6), 4)
    # Goggles
    pygame.draw.rect(tmp, ORANGE, (cx - 7, cy - 8, 6, 4), border_radius=2)
    pygame.draw.rect(tmp, ORANGE, (cx + 1, cy - 8, 6, 4), border_radius=2)
    pygame.draw.line(tmp, ORANGE, (cx - 1, cy - 6), (cx + 1, cy - 6), 2)

    # Wipeout wobble: add an extra random tilt per frame
    effective_angle = angle
    if wipeout_frame > 0:
        effective_angle += math.sin(wipeout_frame * 0.5) * 30

    if effective_angle != 0:
        tmp = pygame.transform.rotate(tmp, -effective_angle)

    rect = tmp.get_rect(center=(int(x), int(y)))
    surface.blit(tmp, rect)


def draw_ramp(surface, x, y, w, h):
    """Draw a jump ramp (trapezoid)."""
    pts = [
        (x - w // 2, y),
        (x + w // 2, y),
        (x + w // 2 - 5, y - h),
        (x - w // 2 + w // 3, y - h),
    ]
    pygame.draw.polygon(surface, OFF_WHITE, pts)
    pygame.draw.polygon(surface, GREY, pts, 2)


def draw_snowman(surface, x, y, size):
    """Draw a snowman with two circles."""
    r_bot = size
    r_top = int(size * 0.65)
    # Bottom
    pygame.draw.circle(surface, WHITE, (x, y), r_bot)
    pygame.draw.circle(surface, GREY, (x, y), r_bot, 2)
    # Top (head)
    head_y = y - r_bot - r_top + 4
    pygame.draw.circle(surface, WHITE, (x, head_y), r_top)
    pygame.draw.circle(surface, GREY, (x, head_y), r_top, 2)
    # Eyes
    pygame.draw.circle(surface, BLACK, (x - r_top // 3, head_y - r_top // 4), 3)
    pygame.draw.circle(surface, BLACK, (x + r_top // 3, head_y - r_top // 4), 3)
    # Smile
    pygame.draw.arc(surface, BLACK,
                    pygame.Rect(x - r_top // 2, head_y - r_top // 4,
                                r_top, r_top // 2),
                    math.pi, 2 * math.pi, 2)
    # Carrot nose
    pygame.draw.polygon(surface, ORANGE, [
        (x, head_y),
        (x + r_top // 2, head_y + 2),
        (x, head_y + 4),
    ])
    # Hat
    hat_y = head_y - r_top
    pygame.draw.rect(surface, BLACK,
                     (x - r_top + 2, hat_y - int(r_top * 0.7),
                      (r_top - 2) * 2, int(r_top * 0.7)))
    pygame.draw.rect(surface, BLACK,
                     (x - r_top, hat_y - 4, r_top * 2, 6))


def draw_mogul(surface, x, y, w, h):
    """Draw a snow mogul (elliptical mound)."""
    rect = pygame.Rect(x - w // 2, y - h, w, h * 2)
    pygame.draw.ellipse(surface, WHITE, rect)
    pygame.draw.ellipse(surface, LIGHT_BLUE, rect, 2)


# ---------------------------------------------------------------------------
# Scrolling background layer
# ---------------------------------------------------------------------------

class BackgroundLayer:
    """A single repeating mountain silhouette layer."""

    def __init__(self, color, num_peaks, height_range, speed_factor):
        self.color = color
        self.speed_factor = speed_factor
        self.scroll_y = 0
        self._build(num_peaks, height_range)

    def _build(self, num_peaks, height_range):
        """Generate a mountain silhouette spanning 2x screen height."""
        h_lo, h_hi = height_range
        self.points = []
        # We'll create points for a polygon that tiles vertically
        step = SCREEN_WIDTH // num_peaks
        self.tile_height = SCREEN_HEIGHT * 2
        pts = [(0, self.tile_height)]
        x = 0
        while x <= SCREEN_WIDTH + step:
            peak_y = random.randint(h_lo, h_hi)
            pts.append((x, peak_y))
            x += step
        pts.append((SCREEN_WIDTH, self.tile_height))
        self.points = pts

    def update(self, base_speed):
        self.scroll_y = (self.scroll_y + base_speed * self.speed_factor) % self.tile_height

    def draw(self, surface):
        offset = self.scroll_y
        for dy in [-self.tile_height, 0, self.tile_height]:
            translated = [(px, py + offset + dy) for px, py in self.points]
            pygame.draw.polygon(surface, self.color, translated)


# ---------------------------------------------------------------------------
# Side tree
# ---------------------------------------------------------------------------

class SideTree:
    def __init__(self, side):
        self.side = side  # 'left' or 'right'
        self.reset(spawning=False)

    def reset(self, spawning=True):
        self.size = random.randint(25, 55)
        if self.side == 'left':
            self.x = random.randint(20, 140)
        else:
            self.x = random.randint(SCREEN_WIDTH - 140, SCREEN_WIDTH - 20)
        if spawning:
            self.y = random.randint(-80, -10)
        else:
            self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(1.5, 3.0)

    def update(self, base_speed):
        self.y += base_speed * self.speed
        if self.y > SCREEN_HEIGHT + 80:
            self.reset(spawning=True)

    def draw(self, surface):
        draw_pine_tree(surface, self.x, self.y, self.size)


# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------

class Snowflake:
    def __init__(self, spawning=True):
        self.reset(spawning)

    def reset(self, spawning=True):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(-20, -5) if spawning else random.uniform(0, SCREEN_HEIGHT)
        self.size = random.randint(2, 5)
        self.speed = random.uniform(1.0, 3.5)
        self.drift = random.uniform(-0.4, 0.4)
        self.alpha = random.randint(160, 255)

    def update(self):
        self.y += self.speed
        self.x += self.drift
        if self.y > SCREEN_HEIGHT + 10 or self.x < -10 or self.x > SCREEN_WIDTH + 10:
            self.reset(spawning=True)

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size)


# ---------------------------------------------------------------------------
# Obstacle
# ---------------------------------------------------------------------------

class Obstacle:
    # Stable jagged offsets per rock instance so they don't flicker
    def __init__(self, speed):
        self.kind = random.choice([OBS_ROCK, OBS_TREE, OBS_RAMP,
                                   OBS_SNOWMAN, OBS_MOGUL])
        self.x = random.randint(180, SCREEN_WIDTH - 180)
        self.y = random.randint(-80, -20)
        self.speed = speed
        self._set_size()
        # Pre-generate rock offsets to avoid per-frame randomness
        self._rock_offsets = [random.uniform(-0.25, 0.25) for _ in range(8)]

    def _set_size(self):
        if self.kind == OBS_ROCK:
            self.size = random.randint(18, 32)
            self.w, self.h = self.size * 2, self.size
        elif self.kind == OBS_TREE:
            self.size = random.randint(28, 50)
            self.w, self.h = self.size, self.size + 20
        elif self.kind == OBS_RAMP:
            self.w = random.randint(60, 90)
            self.h = random.randint(20, 35)
            self.size = self.w
        elif self.kind == OBS_SNOWMAN:
            self.size = random.randint(16, 26)
            self.w, self.h = self.size * 2, self.size * 4
        elif self.kind == OBS_MOGUL:
            self.w = random.randint(50, 80)
            self.h = random.randint(18, 30)
            self.size = self.w

    def update(self):
        self.y += self.speed

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 120

    def get_rect(self):
        """Return a conservative collision bounding box."""
        if self.kind == OBS_ROCK:
            return pygame.Rect(self.x - self.size + 4,
                               self.y - self.size // 2 + 4,
                               self.size * 2 - 8,
                               self.size - 8)
        elif self.kind == OBS_TREE:
            return pygame.Rect(self.x - self.size // 3,
                               self.y - self.h + 10,
                               self.size // 3 * 2,
                               self.h - 10)
        elif self.kind == OBS_RAMP:
            return pygame.Rect(self.x - self.w // 2 + 6,
                               self.y - self.h + 2,
                               self.w - 12,
                               self.h - 2)
        elif self.kind == OBS_SNOWMAN:
            r = self.size
            return pygame.Rect(self.x - r + 4,
                               self.y - r * 4 + 4,
                               r * 2 - 8,
                               r * 4 - 8)
        elif self.kind == OBS_MOGUL:
            return pygame.Rect(self.x - self.w // 2 + 6,
                               self.y - self.h // 2 + 4,
                               self.w - 12,
                               self.h // 2)

    def draw(self, surface):
        if self.kind == OBS_ROCK:
            # Use stable offsets
            r = self.size
            pts = []
            num_pts = 8
            for i in range(num_pts):
                angle = (2 * math.pi / num_pts) * i + self._rock_offsets[i]
                dist = r * 0.85
                pts.append((self.x + int(math.cos(angle) * dist),
                             self.y + int(math.sin(angle) * dist * 0.55)))
            pygame.draw.polygon(surface, DARK_GREY, pts)
            pygame.draw.polygon(surface, GREY, pts, 2)

        elif self.kind == OBS_TREE:
            draw_pine_tree(surface, self.x, self.y, self.size)

        elif self.kind == OBS_RAMP:
            draw_ramp(surface, self.x, self.y, self.w, self.h)

        elif self.kind == OBS_SNOWMAN:
            draw_snowman(surface, self.x, self.y, self.size)

        elif self.kind == OBS_MOGUL:
            draw_mogul(surface, self.x, self.y, self.w, self.h)


# ---------------------------------------------------------------------------
# Skier (player)
# ---------------------------------------------------------------------------

class Skier:
    SPEED = 5
    WIPEOUT_FRAMES = 90  # frames for wipeout animation

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = 120
        self.angle = 0
        self.wipeout_timer = 0
        self.alive = True

    def start_wipeout(self):
        self.alive = False
        self.wipeout_timer = self.WIPEOUT_FRAMES

    def update(self, keys):
        if not self.alive:
            self.wipeout_timer -= 1
            self.angle += 12
            return

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.SPEED

        # Clamp to play area (slightly inset from screen edges)
        self.x = max(50, min(SCREEN_WIDTH - 50, self.x))

    def get_rect(self):
        return pygame.Rect(self.x - 14, self.y - 20, 28, 40)

    def draw(self, surface):
        wf = self.WIPEOUT_FRAMES - self.wipeout_timer if not self.alive else 0
        draw_skier(surface, self.x, self.y,
                   angle=self.angle if not self.alive else 0,
                   wipeout_frame=wf)


# ---------------------------------------------------------------------------
# Main Game class
# ---------------------------------------------------------------------------

class SkiGame:
    BASE_SPEED = 3.0
    SPEED_INCREASE = 0.0008     # per frame
    SPAWN_INTERVAL_START = 120  # frames between obstacle spawns
    SPAWN_INTERVAL_MIN = 45

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🎿 Ski Mountain Game")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 22)

        self.high_score = 0
        self._init_background()
        self.state = STATE_MENU
        self._new_game()

    def _init_background(self):
        # Mountain layers (back → front, slower → faster)
        self.bg_layers = [
            BackgroundLayer(DEEP_SKY, 5, (80, 200), 0.0),   # sky (static)
            BackgroundLayer(MOUNTAIN_SHADOW, 4, (150, 320), 0.3),
            BackgroundLayer(MOUNTAIN_COLOR, 5, (220, 420), 0.6),
            BackgroundLayer(OFF_WHITE, 6, (300, 500), 1.0),
        ]
        self.side_trees = (
            [SideTree('left') for _ in range(8)] +
            [SideTree('right') for _ in range(8)]
        )
        self.snowflakes = [Snowflake(spawning=False) for _ in range(80)]

    def _new_game(self):
        self.skier = Skier()
        self.obstacles = []
        self.score = 0.0
        self.speed = self.BASE_SPEED
        self.spawn_interval = self.SPAWN_INTERVAL_START
        self.spawn_timer = self.spawn_interval
        self.frame = 0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self.clock.tick(FPS)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event)

            self._update()
            self._draw()
            pygame.display.flip()

    def _handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == STATE_MENU:
            if event.key == pygame.K_RETURN:
                self.state = STATE_PLAYING
        elif self.state == STATE_GAMEOVER:
            if event.key in (pygame.K_r, pygame.K_RETURN):
                self._new_game()
                self.state = STATE_PLAYING

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self):
        if self.state == STATE_PLAYING:
            self._update_playing()
        elif self.state == STATE_WIPEOUT:
            self._update_wipeout()

    def _update_playing(self):
        self.frame += 1
        self.speed += self.SPEED_INCREASE
        self.spawn_interval = max(
            self.SPAWN_INTERVAL_MIN,
            self.SPAWN_INTERVAL_START - self.frame // 10
        )
        self.score += self.speed * 0.05

        keys = pygame.key.get_pressed()
        self.skier.update(keys)

        # Scroll background
        for layer in self.bg_layers:
            layer.update(self.speed)
        for tree in self.side_trees:
            tree.update(self.speed)
        for flake in self.snowflakes:
            flake.update()

        # Spawn obstacles
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.obstacles.append(Obstacle(self.speed * random.uniform(0.85, 1.15)))
            self.spawn_timer = self.spawn_interval

        # Update obstacles
        for obs in self.obstacles:
            obs.update()
        self.obstacles = [o for o in self.obstacles if not o.is_off_screen()]

        # Collision check
        skier_rect = self.skier.get_rect()
        for obs in self.obstacles:
            if skier_rect.colliderect(obs.get_rect()):
                self.skier.start_wipeout()
                self.state = STATE_WIPEOUT
                if int(self.score) > self.high_score:
                    self.high_score = int(self.score)
                break

    def _update_wipeout(self):
        keys = pygame.key.get_pressed()
        self.skier.update(keys)  # runs wipeout animation

        # Scroll background / snowflakes during wipeout
        for layer in self.bg_layers:
            layer.update(self.speed * 0.5)
        for tree in self.side_trees:
            tree.update(self.speed * 0.5)
        for flake in self.snowflakes:
            flake.update()

        if self.skier.wipeout_timer <= 0:
            self.state = STATE_GAMEOVER

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self):
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state in (STATE_PLAYING, STATE_WIPEOUT):
            self._draw_game()
        elif self.state == STATE_GAMEOVER:
            self._draw_gameover()

    def _draw_background(self):
        # Sky gradient (top of screen)
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(SKY_BLUE[0] + (ICY_BLUE[0] - SKY_BLUE[0]) * t)
            g = int(SKY_BLUE[1] + (ICY_BLUE[1] - SKY_BLUE[1]) * t)
            b = int(SKY_BLUE[2] + (ICY_BLUE[2] - SKY_BLUE[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Mountain layers
        for layer in self.bg_layers[1:]:  # skip sky layer
            layer.draw(self.screen)

        # Sun
        pygame.draw.circle(self.screen, YELLOW, (700, 70), 40)
        pygame.draw.circle(self.screen, (255, 240, 100), (700, 70), 32)
        # Sun rays
        for i in range(12):
            ang = math.radians(i * 30)
            x1 = int(700 + math.cos(ang) * 44)
            y1 = int(70 + math.sin(ang) * 44)
            x2 = int(700 + math.cos(ang) * 56)
            y2 = int(70 + math.sin(ang) * 56)
            pygame.draw.line(self.screen, YELLOW, (x1, y1), (x2, y2), 3)

        # Side trees
        for tree in self.side_trees:
            tree.draw(self.screen)

    def _draw_game(self):
        self._draw_background()

        # Snowflakes
        for flake in self.snowflakes:
            flake.draw(self.screen)

        # Obstacles
        for obs in self.obstacles:
            obs.draw(self.screen)

        # Skier
        self.skier.draw(self.screen)

        # HUD – score
        score_surf = self.font_med.render(f"Score: {int(self.score)}", True, WHITE)
        score_shadow = self.font_med.render(f"Score: {int(self.score)}", True, BLACK)
        self.screen.blit(score_shadow, (SCREEN_WIDTH - score_surf.get_width() - 14, 14))
        self.screen.blit(score_surf, (SCREEN_WIDTH - score_surf.get_width() - 16, 12))

        hi_surf = self.font_small.render(f"Best: {self.high_score}", True, YELLOW)
        self.screen.blit(hi_surf, (SCREEN_WIDTH - hi_surf.get_width() - 16, 52))

        # Speed indicator
        speed_txt = self.font_small.render(
            f"Speed: {self.speed:.1f}", True, WHITE)
        self.screen.blit(speed_txt, (16, 12))

    def _draw_menu(self):
        self._draw_background()
        for flake in self.snowflakes:
            flake.update()
            flake.draw(self.screen)

        # Title panel
        panel = pygame.Surface((560, 320), pygame.SRCALPHA)
        panel.fill((0, 30, 80, 180))
        self.screen.blit(panel, (SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2 - 180))

        title1 = self.font_large.render("🎿 SKI MOUNTAIN", True, WHITE)
        title2 = self.font_large.render("GAME", True, ICY_BLUE)
        self.screen.blit(title1, (SCREEN_WIDTH // 2 - title1.get_width() // 2,
                                  SCREEN_HEIGHT // 2 - 160))
        self.screen.blit(title2, (SCREEN_WIDTH // 2 - title2.get_width() // 2,
                                  SCREEN_HEIGHT // 2 - 100))

        instructions = [
            "Dodge obstacles and survive as long as you can!",
            "← → or A / D to move",
            "",
            "Press ENTER to Start",
        ]
        for i, line in enumerate(instructions):
            color = YELLOW if line.startswith("Press") else WHITE
            font = self.font_med if line.startswith("Press") else self.font_small
            surf = font.render(line, True, color)
            self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - 20 + i * 34))

    def _draw_gameover(self):
        self._draw_background()
        for flake in self.snowflakes:
            flake.update()
            flake.draw(self.screen)

        # Panel
        panel = pygame.Surface((520, 300), pygame.SRCALPHA)
        panel.fill((80, 0, 0, 190))
        self.screen.blit(panel, (SCREEN_WIDTH // 2 - 260, SCREEN_HEIGHT // 2 - 170))

        over_surf = self.font_large.render("WIPEOUT!", True, RED)
        self.screen.blit(over_surf,
                         (SCREEN_WIDTH // 2 - over_surf.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 155))

        score_surf = self.font_med.render(f"Score: {int(self.score)}", True, WHITE)
        hi_surf = self.font_med.render(f"Best:  {self.high_score}", True, YELLOW)
        restart_surf = self.font_med.render("Press R or ENTER to Restart", True, ICY_BLUE)

        self.screen.blit(score_surf,
                         (SCREEN_WIDTH // 2 - score_surf.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 75))
        self.screen.blit(hi_surf,
                         (SCREEN_WIDTH // 2 - hi_surf.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(restart_surf,
                         (SCREEN_WIDTH // 2 - restart_surf.get_width() // 2,
                          SCREEN_HEIGHT // 2 + 50))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    game = SkiGame()
    game.run()
