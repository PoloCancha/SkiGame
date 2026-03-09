
"""
Ski Mountain Game
A Python skiing game built with tkinter - works on Python 3.14+, no extra installs needed!

Features:
- Scrolling mountain background with parallax layers and snowflakes
- Skier character with left/right/up/down movement and a spacebar jump
- Five obstacle types: rock, tree, ramp, snowman, mogul
- Increasing speed and difficulty over time
- OBSTACLE_SIZES dictionary (required advanced data structure) maps each obstacle
  type to its size parameters, used in Obstacle._set_size
- try/except error handling in the game loop and at the entry point
"""

import tkinter as tk
import random
import math
import sys
import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
FRAME_DELAY = 1000 // FPS  # ms

# Colors (hex strings for tkinter)
WHITE = "#FFFFFF"
OFF_WHITE = "#E6F0FF"
ICY_BLUE = "#B4DCFF"
SKY_BLUE = "#87CEEB"
DEEP_SKY = "#64B4E6"
YELLOW = "#FFDC32"
DARK_GREY = "#464647"
GREY = "#82828C"
GREEN = "#228B22"
DARK_GREEN = "#006400"
BLACK = "#141420"
RED = "#C83232"
BROWN = "#8B5A2B"
LIGHT_BLUE = "#C8E6FF"
MOUNTAIN_COLOR = "#D2E1F5"
MOUNTAIN_SHADOW = "#AAC3E1"
ORANGE = "#FF8C00"
SKIN = "#FFD2AA"
BLUE = "#1414B4"
DARK_BLUE = "#282890"
MOUNTAIN_FAR = "#5878A8"    # Far mountains: deep blue-grey
MOUNTAIN_MID = "#8AAAC8"    # Mid mountains: medium blue-grey
MOUNTAIN_NEAR = "#C8DCEE"   # Near mountains: light blue-grey
SNOW_GROUND = "#EEF6FF"     # Snow strip at the bottom of the screen
HUD_BG = "#00286E"          # HUD rounded-rectangle background

# Jump parameters
JUMP_DURATION = 45   # frames
JUMP_HEIGHT = 50     # pixels upward at peak
JUMP_SCALE_MIN = 0.7 # minimum scale at peak

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
# Advanced data structure (dictionary) – required by project rubric.
# Maps each obstacle type to its size-generation parameters so that
# Obstacle._set_size can look up values rather than use a long if/elif chain.
#   "size"    -> (min, max) for the random base size
#   "w_scale" -> multiplier applied to size to get width (None = width equals size)
#   "h_scale" -> multiplier applied to size to get height (None = h = size + 20)
#   "w"       -> (min, max) when width is chosen independently of height
#   "h"       -> (min, max) when height is chosen independently of width
# ---------------------------------------------------------------------------
OBSTACLE_SIZES = {
    OBS_ROCK:    {"size": (18, 32),  "w_scale": 2,    "h_scale": 1},
    OBS_TREE:    {"size": (28, 50),  "w_scale": 1,    "h_scale": None},   # h = size + 20
    OBS_RAMP:    {"w": (60, 90),     "h": (20, 35)},
    OBS_SNOWMAN: {"size": (16, 26),  "w_scale": 2,    "h_scale": 4},
    OBS_MOGUL:   {"w": (50, 80),     "h": (18, 30)},
}


# ---------------------------------------------------------------------------
# Helper: polygon / shape drawing on tkinter Canvas
# ---------------------------------------------------------------------------

def hex_color(r, g, b):
    """Convert integer RGB components to a tkinter-compatible hex color string.

    Parameters:
        r (int): Red component (0–255).
        g (int): Green component (0–255).
        b (int): Blue component (0–255).

    Returns:
        str: Hex color string in the form ``"#rrggbb"``.
    """
    return f"#{r:02x}{g:02x}{b:02x}"

def draw_pine_tree(canvas, x, y, size, tag=""):
    """Draw a stylised pine tree on *canvas* centred at (*x*, *y*).

    The tree consists of a brown rectangular trunk topped with three
    overlapping green triangles that create a layered canopy effect.

    Parameters:
        canvas (tk.Canvas): The tkinter canvas to draw on.
        x (int): Horizontal centre of the tree base.
        y (int): Vertical position of the tree base (bottom of trunk).
        size (int): Approximate overall height of the canopy in pixels.
        tag (str): Optional tkinter item tag applied to every shape drawn.

    Returns:
        None
    """
    trunk_w = max(4, size // 6)
    trunk_h = max(8, size // 3)
    # Trunk
    canvas.create_rectangle(
        x - trunk_w // 2, y - trunk_h,
        x + trunk_w // 2, y,
        fill=BROWN, outline="", tags=tag
    )
    # Three layered triangles
    layers = [(1.0, 1.0, GREEN), (0.7, 0.85, DARK_GREEN), (0.45, 0.7, GREEN)]
    for frac, width_frac, color in layers:
        pts = [
            x, y - trunk_h - int(size * frac),
            x - int(size * width_frac) // 2, y - trunk_h - int(size * (frac - 0.35)),
            x + int(size * width_frac) // 2, y - trunk_h - int(size * (frac - 0.35)),
        ]
        canvas.create_polygon(pts, fill=color, outline="", tags=tag)

def draw_rock(canvas, x, y, size, offsets, tag=""):
    """Draw an irregular boulder shape on *canvas* centred at (*x*, *y*).

    Eight points are placed around an ellipse and perturbed by *offsets*
    to give a natural, jagged rock appearance.

    Parameters:
        canvas (tk.Canvas): The tkinter canvas to draw on.
        x (int): Horizontal centre of the rock.
        y (int): Vertical centre of the rock.
        size (int): Approximate radius of the rock in pixels.
        offsets (list[float]): Eight angular perturbation values (radians)
            that randomise each vertex position.
        tag (str): Optional tkinter item tag applied to every shape drawn.

    Returns:
        None
    """
    num_pts = 8
    pts = []
    for i in range(num_pts):
        angle = (2 * math.pi / num_pts) * i + offsets[i]
        dist = size * 0.85
        pts.append(x + math.cos(angle) * dist)
        pts.append(y + math.sin(angle) * dist * 0.55)
    canvas.create_polygon(pts, fill=DARK_GREY, outline=GREY, width=2, tags=tag)

def draw_ramp(canvas, x, y, w, h, tag=""):
    """Draw a ski jump ramp (angled wedge) on *canvas*.

    The ramp is a quadrilateral with a flat bottom and a slanted top
    surface, coloured off-white with a grey outline.

    Parameters:
        canvas (tk.Canvas): The tkinter canvas to draw on.
        x (int): Horizontal centre of the ramp base.
        y (int): Vertical position of the ramp base (bottom edge).
        w (int): Total width of the ramp in pixels.
        h (int): Height of the ramp in pixels.
        tag (str): Optional tkinter item tag applied to every shape drawn.

    Returns:
        None
    """
    pts = [
        x - w // 2, y,
        x + w // 2, y,
        x + w // 2 - 5, y - h,
        x - w // 2 + w // 3, y - h,
    ]
    canvas.create_polygon(pts, fill=OFF_WHITE, outline=GREY, width=2, tags=tag)

def draw_snowman(canvas, x, y, size, tag=""):
    """Draw a two-ball snowman with hat, eyes, and carrot nose on *canvas*.

    Parameters:
        canvas (tk.Canvas): The tkinter canvas to draw on.
        x (int): Horizontal centre of the snowman's base ball.
        y (int): Vertical position of the bottom of the base ball.
        size (int): Radius of the base ball in pixels; the head is
            proportionally smaller (≈ 65 % of *size*).
        tag (str): Optional tkinter item tag applied to every shape drawn.

    Returns:
        None
    """
    r_bot = size
    r_top = int(size * 0.65)
    # Bottom ball
    canvas.create_oval(x - r_bot, y - r_bot, x + r_bot, y + r_bot,
                       fill=WHITE, outline=GREY, width=2, tags=tag)
    # Head
    head_y = y - r_bot - r_top + 4
    canvas.create_oval(x - r_top, head_y - r_top, x + r_top, head_y + r_top,
                       fill=WHITE, outline=GREY, width=2, tags=tag)
    # Eyes
    canvas.create_oval(x - r_top//3 - 3, head_y - r_top//4 - 3,
                       x - r_top//3 + 3, head_y - r_top//4 + 3,
                       fill=BLACK, outline="", tags=tag)
    canvas.create_oval(x + r_top//3 - 3, head_y - r_top//4 - 3,
                       x + r_top//3 + 3, head_y - r_top//4 + 3,
                       fill=BLACK, outline="", tags=tag)
    # Nose
    canvas.create_polygon(
        x, head_y,
        x + r_top // 2, head_y + 2,
        x, head_y + 4,
        fill=ORANGE, outline="", tags=tag
    )
    # Hat brim
    canvas.create_rectangle(x - r_top, head_y - r_top - 4,
                             x + r_top, head_y - r_top + 2,
                             fill=BLACK, outline="", tags=tag)
    # Hat top
    canvas.create_rectangle(x - r_top + 4, head_y - r_top - 4 - int(r_top * 0.7),
                             x + r_top - 4, head_y - r_top - 4,
                             fill=BLACK, outline="", tags=tag)

def draw_mogul(canvas, x, y, w, h, tag=""):
    """Draw a snow mogul (rounded snow mound) on *canvas*.

    The mogul is rendered as a white ellipse with a light-blue outline.

    Parameters:
        canvas (tk.Canvas): The tkinter canvas to draw on.
        x (int): Horizontal centre of the mogul.
        y (int): Vertical centre of the mogul.
        w (int): Total width of the mogul in pixels.
        h (int): Half-height of the mogul (the ellipse extends *h* pixels
            above and below *y*).
        tag (str): Optional tkinter item tag applied to every shape drawn.

    Returns:
        None
    """
    canvas.create_oval(x - w // 2, y - h, x + w // 2, y + h,
                       fill=WHITE, outline=LIGHT_BLUE, width=2, tags=tag)

def draw_skier(canvas, x, y, angle=0, scale=1.0, tag=""):
    """Draw skier as a collection of shapes. angle is in degrees (wipeout spin)."""
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    def rot(px, py):
        """Scale and rotate point (px,py) around (x,y)."""
        dx, dy = (px - x) * scale, (py - y) * scale
        return (x + dx * cos_a - dy * sin_a,
                y + dx * sin_a + dy * cos_a)

    def rpt(*pts):
        """Rotate a list of (px,py) tuples and flatten."""
        result = []
        for px, py in pts:
            rx, ry = rot(px, py)
            result += [rx, ry]
        return result

    lw_pole = max(1, int(2 * scale))
    lw_limb = max(1, int(5 * scale))

    # Skis
    canvas.create_polygon(
        rpt((x-14, y+14), (x+12, y+14), (x+14, y+18), (x-14, y+18)),
        fill=BLUE, outline="", tags=tag)
    canvas.create_polygon(
        rpt((x-12, y+19), (x+13, y+19), (x+15, y+23), (x-12, y+23)),
        fill=BLUE, outline="", tags=tag)

    # Poles
    lx1, ly1 = rot(x - 10, y + 6)
    lx2, ly2 = rot(x - 22, y + 22)
    canvas.create_line(lx1, ly1, lx2, ly2, fill=GREY, width=lw_pole, tags=tag)
    rx1, ry1 = rot(x + 6, y + 6)
    rx2, ry2 = rot(x + 18, y + 22)
    canvas.create_line(rx1, ry1, rx2, ry2, fill=GREY, width=lw_pole, tags=tag)

    # Body
    canvas.create_polygon(
        rpt((x-8, y), (x+8, y), (x+10, y+14), (x-10, y+14)),
        fill=RED, outline="", tags=tag)

    # Arms
    ax1, ay1 = rot(x - 8, y + 4)
    ax2, ay2 = rot(x - 18, y + 10)
    canvas.create_line(ax1, ay1, ax2, ay2, fill=RED, width=lw_limb, tags=tag)
    bx1, by1 = rot(x + 8, y + 4)
    bx2, by2 = rot(x + 18, y + 10)
    canvas.create_line(bx1, by1, bx2, by2, fill=RED, width=lw_limb, tags=tag)

    # Legs
    lleg1 = rot(x - 5, y + 14)
    lleg2 = rot(x - 8, y + 22)
    canvas.create_line(lleg1[0], lleg1[1], lleg2[0], lleg2[1],
                       fill=DARK_BLUE, width=lw_limb, tags=tag)
    rleg1 = rot(x + 5, y + 14)
    rleg2 = rot(x + 8, y + 22)
    canvas.create_line(rleg1[0], rleg1[1], rleg2[0], rleg2[1],
                       fill=DARK_BLUE, width=lw_limb, tags=tag)

    # Head
    hx, hy = rot(x, y - 6)
    hr = max(4, int(8 * scale))
    canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr,
                       fill=SKIN, outline="", tags=tag)

    # Helmet
    hel_pts = []
    for i in range(13):
        a = math.pi - (math.pi / 12) * i
        px = x + math.cos(a) * 9
        py = (y - 6) + math.sin(a) * 9
        rx, ry = rot(px, py)
        hel_pts += [rx, ry]
    rx0, ry0 = rot(x - 9, y - 6)
    rx1, ry1 = rot(x + 9, y - 6)
    hel_pts += [rx1, ry1, rx0, ry0]
    canvas.create_polygon(hel_pts, fill=BLUE, outline="", tags=tag)

    # Goggles
    canvas.create_polygon(
        rpt((x-7, y-9), (x-1, y-9), (x-1, y-5), (x-7, y-5)),
        fill=ORANGE, outline="", tags=tag)
    canvas.create_polygon(
        rpt((x+1, y-9), (x+7, y-9), (x+7, y-5), (x+1, y-5)),
        fill=ORANGE, outline="", tags=tag)


# ---------------------------------------------------------------------------
# Obstacle class
# ---------------------------------------------------------------------------

class Obstacle:
    def __init__(self, speed):
        """Initialise a new obstacle with a randomly chosen type and position.

        The obstacle is spawned just above the top of the screen at a random
        horizontal position in the central play area, with randomised dimensions
        appropriate to its type.

        Parameters:
            speed (float): Downward scroll speed in pixels per frame.

        Returns:
            None
        """
        self.kind = random.choice([OBS_ROCK, OBS_TREE, OBS_RAMP, OBS_SNOWMAN, OBS_MOGUL])
        self.x = random.randint(180, SCREEN_WIDTH - 180)
        self.y = random.randint(-80, -20)
        self.speed = speed
        self._set_size()
        self._rock_offsets = [random.uniform(-0.25, 0.25) for _ in range(8)]

    def _set_size(self):
        """Set ``self.w``, ``self.h``, and ``self.size`` from the OBSTACLE_SIZES dictionary.

        Looks up the size parameters for ``self.kind`` in the module-level
        ``OBSTACLE_SIZES`` constant (the required dictionary data structure) and
        uses them to generate randomised but type-appropriate dimensions.

        Parameters:
            None

        Returns:
            None
        """
        params = OBSTACLE_SIZES[self.kind]
        if "size" in params:
            self.size = random.randint(*params["size"])
            w_scale = params["w_scale"]
            h_scale = params["h_scale"]
            self.w = self.size * w_scale
            self.h = self.size + 20 if h_scale is None else self.size * h_scale
        else:
            self.w = random.randint(*params["w"])
            self.h = random.randint(*params["h"])
            self.size = self.w

    def update(self):
        """Move the obstacle downward by its speed for one frame.

        Parameters:
            None

        Returns:
            None
        """
        self.y += self.speed

    def is_off_screen(self):
        """Return True if the obstacle has scrolled past the bottom of the screen.

        Parameters:
            None

        Returns:
            bool: True when ``self.y`` exceeds the screen height by a small margin.
        """
        return self.y > SCREEN_HEIGHT + 120

    def get_rect(self):
        """Return a tight axis-aligned bounding rectangle for collision detection.

        The rectangle is inset slightly from the visual edges to give more
        forgiving hitboxes.

        Parameters:
            None

        Returns:
            tuple[int, int, int, int]: ``(x1, y1, x2, y2)`` bounding box, or
            ``None`` if the obstacle type is unrecognised.
        """
        if self.kind == OBS_ROCK:
            return (self.x - self.size + 4, self.y - self.size // 2 + 4,
                    self.x + self.size - 4, self.y + self.size // 2 - 4)
        elif self.kind == OBS_TREE:
            return (self.x - self.size // 3, self.y - self.h + 10,
                    self.x + self.size // 3, self.y)
        elif self.kind == OBS_RAMP:
            return (self.x - self.w // 2 + 6, self.y - self.h + 2,
                    self.x + self.w // 2 - 6, self.y)
        elif self.kind == OBS_SNOWMAN:
            r = self.size
            return (self.x - r + 4, self.y - r * 4 + 4,
                    self.x + r - 4, self.y + r - 4)
        elif self.kind == OBS_MOGUL:
            return (self.x - self.w // 2 + 6, self.y - self.h // 2 + 4,
                    self.x + self.w // 2 - 6, self.y + self.h // 2)

    def draw(self, canvas, tag=""):
        """Draw the obstacle on *canvas* using the appropriate drawing function.

        Delegates to one of ``draw_rock``, ``draw_pine_tree``, ``draw_ramp``,
        ``draw_snowman``, or ``draw_mogul`` depending on ``self.kind``.

        Parameters:
            canvas (tk.Canvas): The tkinter canvas to draw on.
            tag (str): Optional tkinter item tag applied to every shape drawn.

        Returns:
            None
        """
        if self.kind == OBS_ROCK:
            draw_rock(canvas, self.x, self.y, self.size, self._rock_offsets, tag)
        elif self.kind == OBS_TREE:
            draw_pine_tree(canvas, self.x, self.y, self.size, tag)
        elif self.kind == OBS_RAMP:
            draw_ramp(canvas, self.x, self.y, self.w, self.h, tag)
        elif self.kind == OBS_SNOWMAN:
            draw_snowman(canvas, self.x, self.y, self.size, tag)
        elif self.kind == OBS_MOGUL:
            draw_mogul(canvas, self.x, self.y, self.w, self.h, tag)


def rects_overlap(r1, r2):
    """r1, r2 are (x1,y1,x2,y2) tuples."""
    return not (r1[2] < r2[0] or r1[0] > r2[2] or
                r1[3] < r2[1] or r1[1] > r2[3])

# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------

class Snowflake:
    def __init__(self, spawning=True):
        """Initialise a snowflake at a random position and call reset to set attributes.

        Parameters:
            spawning (bool): When True the flake starts above the screen edge;
                when False it may start anywhere on screen (used to pre-populate
                the initial snowfall).

        Returns:
            None
        """
        self.reset(spawning)

    def reset(self, spawning=True):
        """Randomise position, size, speed, drift, and colour for this snowflake.

        Called on initialisation and whenever a flake scrolls off screen so
        that it can re-enter from the top.

        Parameters:
            spawning (bool): When True the flake is placed just above the top
                edge; when False it is placed at a random vertical position
                anywhere on screen.

        Returns:
            None
        """
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(-20, -5) if spawning else random.uniform(0, SCREEN_HEIGHT)
        self.size = random.randint(2, 5)
        self.speed = random.uniform(1.0, 3.5)
        self.drift = random.uniform(-0.4, 0.4)
        # Vary colour slightly for visual interest (pure white → faint icy-blue)
        bri = random.randint(210, 255)
        blue_bump = random.randint(0, 45)
        self.color = hex_color(bri, bri, min(255, bri + blue_bump))

    def update(self):
        """Advance the snowflake one frame: fall downward and drift sideways.

        If the flake moves off the bottom or either side of the screen it is
        reset so it re-enters from the top.

        Parameters:
            None

        Returns:
            None
        """
        self.y += self.speed
        self.x += self.drift
        if self.y > SCREEN_HEIGHT + 10 or self.x < -10 or self.x > SCREEN_WIDTH + 10:
            self.reset(spawning=True)

# ---------------------------------------------------------------------------
# Mountain background layer
# ---------------------------------------------------------------------------

class BackgroundLayer:
    def __init__(self, color, num_peaks, height_range, speed_factor):
        """Initialise a scrolling mountain silhouette layer.

        Parameters:
            color (str): Fill colour for the mountain polygon (hex string).
            num_peaks (int): Approximate number of mountain peaks across the
                screen width.
            height_range (tuple[int, int]): ``(min_y, max_y)`` range for random
                peak heights (in pixels from the top of the screen).
            speed_factor (float): Fraction of the base game speed at which this
                layer scrolls; use smaller values for distant layers to create
                a parallax effect.

        Returns:
            None
        """
        self.color = color
        self.speed_factor = speed_factor
        self.scroll_y = 0
        self._build(num_peaks, height_range)

    def _build(self, num_peaks, height_range):
        """Generate the mountain polygon point list for this layer.

        Creates a closed polygon that spans twice the screen height so that
        seamless vertical tiling is possible during scrolling.

        Parameters:
            num_peaks (int): Number of peaks across the screen width.
            height_range (tuple[int, int]): ``(min_y, max_y)`` pixel range for
                random peak heights from the top of the screen.

        Returns:
            None
        """
        h_lo, h_hi = height_range
        step = SCREEN_WIDTH // num_peaks
        self.tile_height = SCREEN_HEIGHT * 2
        pts = [(0, self.tile_height)]
        x = 0
        while x <= SCREEN_WIDTH + step:
            pts.append((x, random.randint(h_lo, h_hi)))
            x += step
        pts.append((SCREEN_WIDTH, self.tile_height))
        self.points = pts

    def update(self, base_speed):
        """Advance the scroll position by one frame.

        Parameters:
            base_speed (float): Current game speed in pixels per frame; the
                layer moves at ``base_speed * self.speed_factor``.

        Returns:
            None
        """
        self.scroll_y = (self.scroll_y + base_speed * self.speed_factor) % self.tile_height

    def draw(self, canvas, tag=""):
        """Draw the mountain layer on *canvas*, tiling vertically to fill the screen.

        Three copies of the polygon are drawn (above, at, and below the current
        scroll offset) so there are no visible seams during scrolling.

        Parameters:
            canvas (tk.Canvas): The tkinter canvas to draw on.
            tag (str): Optional tkinter item tag applied to every shape drawn.

        Returns:
            None
        """
        offset = self.scroll_y
        for dy in [-self.tile_height, 0, self.tile_height]:
            flat = []
            for px, py in self.points:
                flat += [px, py + offset + dy]
            canvas.create_polygon(flat, fill=self.color, outline="", tags=tag)

# ---------------------------------------------------------------------------
# SideTree
# ---------------------------------------------------------------------------

class SideTree:
    def __init__(self, side):
        """Initialise a decorative tree on one side of the ski slope.

        Parameters:
            side (str): ``'left'`` or ``'right'`` — determines the horizontal
                region in which the tree is placed.

        Returns:
            None
        """
        self.side = side
        self.reset(spawning=False)

    def reset(self, spawning=True):
        """Randomise this tree's size, position, and scroll speed.

        Parameters:
            spawning (bool): When True the tree is placed just above the top
                edge; when False it is placed at a random vertical position
                on screen (used for initial population).

        Returns:
            None
        """
        self.size = random.randint(25, 55)
        if self.side == 'left':
            self.x = random.randint(20, 140)
        else:
            self.x = random.randint(SCREEN_WIDTH - 140, SCREEN_WIDTH - 20)
        self.y = random.randint(-80, -10) if spawning else random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(1.5, 3.0)

    def update(self, base_speed):
        """Move the tree downward for one frame and reset it when off screen.

        Parameters:
            base_speed (float): Current game speed; the tree scrolls at
                ``base_speed * self.speed``.

        Returns:
            None
        """
        self.y += base_speed * self.speed
        if self.y > SCREEN_HEIGHT + 80:
            self.reset(spawning=True)

# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------

class SkiGame:
    BASE_SPEED = 3.0
    SPEED_INCREASE = 0.0008
    SPAWN_INTERVAL_START = 120
    SPAWN_INTERVAL_MIN = 45

    def __init__(self):
        """Set up the tkinter window, canvas, key bindings, and start the game loop.

        Creates the main window, initialises the background scenery and
        snowflakes, sets the game state to the menu screen, and enters the
        tkinter event loop.

        Parameters:
            None

        Returns:
            None
        """
        self.root = tk.Tk()
        self.root.title("Ski Mountain Game")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                                bg=SKY_BLUE, highlightthickness=0)
        self.canvas.pack()

        self.keys = set()
        self.root.bind("<KeyPress>", self._key_press)
        self.root.bind("<KeyRelease>", self._key_release)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        self.high_score = 0
        self._init_background()
        self.state = STATE_MENU
        self._new_game()
        self._loop()
        self.root.mainloop()

    def _quit(self):
        """Destroy the window and exit the process cleanly.

        Bound to the window close (X) button via ``WM_DELETE_WINDOW``.

        Parameters:
            None

        Returns:
            None
        """
        self.root.destroy()
        sys.exit()

    def _key_press(self, event):
        """Handle a key-press event: update held-key set and trigger state changes.

        Records the pressed key in ``self.keys`` and handles one-shot actions:
        starting the game from the menu, restarting after game-over, and
        initiating a jump while playing.

        Parameters:
            event (tk.Event): The tkinter key-press event object.

        Returns:
            None
        """
        self.keys.add(event.keysym.lower())
        # State transitions
        if self.state == STATE_MENU and event.keysym == "Return":
            self.state = STATE_PLAYING
        elif self.state == STATE_GAMEOVER and event.keysym in ("r", "Return"):
            self._new_game()
            self.state = STATE_PLAYING
        # Jump
        elif (self.state == STATE_PLAYING and event.keysym == "space"
              and not self.jump_active and self.skier_alive):
            self.jump_active = True
            self.jump_frame = 0

    def _key_release(self, event):
        """Handle a key-release event: remove the key from the held-key set.

        Parameters:
            event (tk.Event): The tkinter key-release event object.

        Returns:
            None
        """
        self.keys.discard(event.keysym.lower())

    def _init_background(self):
        """Create the three parallax mountain layers, side trees, and snowflakes.

        This is called once during ``__init__`` so that the background elements
        are available before the first game loop iteration.

        Parameters:
            None

        Returns:
            None
        """
        self.bg_layers = [
            BackgroundLayer(MOUNTAIN_FAR,  4, (150, 320), 0.3),
            BackgroundLayer(MOUNTAIN_MID,  5, (220, 420), 0.6),
            BackgroundLayer(MOUNTAIN_NEAR, 6, (300, 500), 1.0),
        ]
        self.side_trees = (
            [SideTree('left') for _ in range(4)] +
            [SideTree('right') for _ in range(4)]
        )
        self.snowflakes = [Snowflake(spawning=False) for _ in range(80)]

    def _new_game(self):
        """Reset all per-game state for a fresh round.

        Resets the skier position, angle, and jump state; clears obstacles;
        and resets the score, speed, and spawn timer back to their starting
        values.  Background elements (layers, trees, snowflakes) are not
        reset so the scenery continues smoothly between games.

        Parameters:
            None

        Returns:
            None
        """
        self.skier_x = SCREEN_WIDTH // 2
        self.skier_y = SCREEN_HEIGHT // 3  # start at the top of the vertical play area
        self.skier_angle = 0
        self.skier_alive = True
        self.wipeout_timer = 0

        # Jump state
        self.jump_active = False
        self.jump_frame = 0

        self.obstacles = []
        self.score = 0.0
        self.speed = self.BASE_SPEED
        self.spawn_interval = self.SPAWN_INTERVAL_START
        self.spawn_timer = self.spawn_interval
        self.frame = 0

    def _loop(self):
        """Schedule and execute one game-loop iteration.

        Calls ``_update`` and ``_draw``, measures how long they took, then
        uses ``root.after`` to schedule the next iteration so that the frame
        rate targets ``FPS``.  A ``try/except`` guard ensures that a single
        bad frame (e.g. a drawing error) prints the error and continues rather
        than crashing the whole game.

        Parameters:
            None

        Returns:
            None
        """
        start = time.time()
        try:
            self._update()
            self._draw()
        except Exception as e:
            print(f"[SkiGame] Frame error: {e}")
        elapsed = int((time.time() - start) * 1000)
        delay = max(1, FRAME_DELAY - elapsed)
        self.root.after(delay, self._loop)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self):
        """Dispatch per-frame logic to the appropriate state handler.

        Delegates to ``_update_playing`` or ``_update_wipeout`` based on
        ``self.state``.  While in the menu only snowflakes are animated.

        Parameters:
            None

        Returns:
            None
        """
        if self.state == STATE_PLAYING:
            self._update_playing()
        elif self.state == STATE_WIPEOUT:
            self._update_wipeout()
        elif self.state == STATE_MENU:
            for flake in self.snowflakes:
                flake.update()

    def _update_playing(self):
        """Advance one frame of active gameplay.

        Increments the frame counter and score, increases speed and adjusts
        the obstacle spawn rate over time, processes keyboard input for skier
        movement, updates the jump arc, scrolls background layers and side
        trees, spawns and moves obstacles, and checks for collisions.

        Parameters:
            None

        Returns:
            None
        """
        self.frame += 1
        self.speed += self.SPEED_INCREASE
        self.spawn_interval = max(
            self.SPAWN_INTERVAL_MIN,
            self.SPAWN_INTERVAL_START - self.frame // 10
        )
        self.score += self.speed * 0.05

        # Skier horizontal movement
        if 'left' in self.keys or 'a' in self.keys:
            self.skier_x -= 5
        if 'right' in self.keys or 'd' in self.keys:
            self.skier_x += 5
        self.skier_x = max(50, min(SCREEN_WIDTH - 50, self.skier_x))

        # Skier vertical movement (up/down within top-1/3 to bottom-2/3 of screen)
        if 'up' in self.keys or 'w' in self.keys:
            self.skier_y -= 4
        if 'down' in self.keys or 's' in self.keys:
            self.skier_y += 4
        min_y = SCREEN_HEIGHT // 3
        max_y = (SCREEN_HEIGHT * 2) // 3
        self.skier_y = max(min_y, min(max_y, self.skier_y))

        # Jump arc update
        if self.jump_active:
            self.jump_frame += 1
            if self.jump_frame >= JUMP_DURATION:
                self.jump_active = False
                self.jump_frame = 0

        # Background scroll
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

        for obs in self.obstacles:
            obs.update()
        self.obstacles = [o for o in self.obstacles if not o.is_off_screen()]

        # Collision (disabled during jump)
        if not self.jump_active:
            skier_rect = (self.skier_x - 14, self.skier_y - 20,
                          self.skier_x + 14, self.skier_y + 20)
            for obs in self.obstacles:
                if rects_overlap(skier_rect, obs.get_rect()):
                    self.skier_alive = False
                    self.wipeout_timer = 90
                    self.state = STATE_WIPEOUT
                    if int(self.score) > self.high_score:
                        self.high_score = int(self.score)
                    break

    def _update_wipeout(self):
        """Advance one frame of the wipeout animation.

        Decrements the wipeout timer and spins the skier; scrolls background
        elements at half speed to simulate the skier slowing down.  When the
        timer reaches zero, transitions to the game-over state.

        Parameters:
            None

        Returns:
            None
        """
        self.wipeout_timer -= 1
        self.skier_angle += 12

        for layer in self.bg_layers:
            layer.update(self.speed * 0.5)
        for tree in self.side_trees:
            tree.update(self.speed * 0.5)
        for flake in self.snowflakes:
            flake.update()

        if self.wipeout_timer <= 0:
            self.state = STATE_GAMEOVER

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self):
        """Clear the canvas and redraw every visible element for the current frame.

        Dispatches to the appropriate combination of helper draw methods based
        on ``self.state``.

        Parameters:
            None

        Returns:
            None
        """
        self.canvas.delete("all")
        if self.state == STATE_MENU:
            self._draw_background()
            self._draw_snowflakes()
            self._draw_menu_overlay()
        elif self.state in (STATE_PLAYING, STATE_WIPEOUT):
            self._draw_background()
            self._draw_snowflakes()
            self._draw_obstacles()
            self._draw_skier()
            self._draw_hud()
        elif self.state == STATE_GAMEOVER:
            self._draw_background()
            self._draw_snowflakes()
            self._draw_gameover_overlay()

    def _draw_sky_gradient(self):
        """Fill the canvas background with a smooth top-to-bottom sky gradient.

        Draws one horizontal line per pixel row, interpolating linearly from
        a deep navy blue at the top to an icy light blue at the horizon.

        Parameters:
            None

        Returns:
            None
        """
        # Draw sky as horizontal gradient lines — deep blue at top, icy light blue at bottom
        r1, g1, b1 = 0x1E, 0x50, 0x96  # Deep navy-blue at the very top
        r2, g2, b2 = 0xC8, 0xE8, 0xFF  # Icy light blue at the horizon
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            self.canvas.create_line(0, y, SCREEN_WIDTH, y,
                                    fill=hex_color(r, g, b), tags="bg")

    def _draw_background(self):
        """Draw the complete background: sky gradient, mountains, sun, side trees, snow strip.

        Calls ``_draw_sky_gradient``, draws all parallax mountain layers, adds
        the sun with rays, renders the decorative side trees, and places the
        snow ground strip at the bottom of the screen.

        Parameters:
            None

        Returns:
            None
        """
        self._draw_sky_gradient()

        # Mountain layers
        for layer in self.bg_layers:
            layer.draw(self.canvas, tag="bg")

        # Sun
        self.canvas.create_oval(660, 30, 740, 110, fill=YELLOW, outline="", tags="bg")
        self.canvas.create_oval(668, 38, 732, 102,
                                fill="#FFF064", outline="", tags="bg")
        for i in range(12):
            ang = math.radians(i * 30)
            x1 = int(700 + math.cos(ang) * 44)
            y1 = int(70 + math.sin(ang) * 44)
            x2 = int(700 + math.cos(ang) * 58)
            y2 = int(70 + math.sin(ang) * 58)
            self.canvas.create_line(x1, y1, x2, y2,
                                    fill=YELLOW, width=3, tags="bg")

        # Side trees
        for tree in self.side_trees:
            draw_pine_tree(self.canvas, tree.x, int(tree.y), tree.size, tag="bg")

        # Snow ground strip at the bottom
        self.canvas.create_rectangle(
            0, SCREEN_HEIGHT - 28, SCREEN_WIDTH, SCREEN_HEIGHT,
            fill=SNOW_GROUND, outline="", tags="bg"
        )
        self.canvas.create_rectangle(
            0, SCREEN_HEIGHT - 28, SCREEN_WIDTH, SCREEN_HEIGHT - 20,
            fill=WHITE, outline="", tags="bg"
        )

    def _draw_snowflakes(self):
        """Draw all snowflakes as small filled circles on the canvas.

        Parameters:
            None

        Returns:
            None
        """
        for flake in self.snowflakes:
            r = flake.size
            self.canvas.create_oval(
                flake.x - r, flake.y - r, flake.x + r, flake.y + r,
                fill=flake.color, outline="", tags="flake"
            )

    def _draw_obstacles(self):
        """Draw every active obstacle on the canvas.

        Iterates over ``self.obstacles`` and calls each obstacle's ``draw``
        method with the ``"obs"`` tag.

        Parameters:
            None

        Returns:
            None
        """
        for obs in self.obstacles:
            obs.draw(self.canvas, tag="obs")

    def _draw_skier(self):
        """Draw the skier character, including jump arc and shadow when airborne.

        During a jump the skier is raised by a sine-curve offset, scaled down
        slightly to simulate perspective, and a shadow ellipse is drawn beneath
        to reinforce the sense of height.  During a wipeout the skier rotates
        via ``self.skier_angle``.

        Parameters:
            None

        Returns:
            None
        """
        angle = self.skier_angle if not self.skier_alive else 0

        if self.jump_active:
            t = self.jump_frame / JUMP_DURATION  # 0.0 → 1.0
            arc = math.sin(math.pi * t)           # peaks at 0.5
            jump_offset = int(arc * JUMP_HEIGHT)
            scale = 1.0 - (1.0 - JUMP_SCALE_MIN) * arc

            # Shadow on the ground (shrinks as skier rises)
            sw = max(8, int(28 * (1.0 - arc * 0.6)))
            sh = max(3, int(8 * (1.0 - arc * 0.6)))
            sx, sy = self.skier_x, self.skier_y + 18
            self.canvas.create_oval(
                sx - sw, sy - sh, sx + sw, sy + sh,
                fill=DARK_GREY, outline="", stipple="gray25", tags="skier"
            )
            draw_skier(self.canvas, self.skier_x,
                       self.skier_y - jump_offset,
                       angle=angle, scale=scale, tag="skier")
        else:
            draw_skier(self.canvas, self.skier_x, self.skier_y,
                       angle=angle, tag="skier")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, fill, tag=""):
        """Draw a rounded rectangle on the canvas."""
        self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tag)
        self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tag)
        self.canvas.create_oval(x1, y1, x1 + 2*r, y1 + 2*r, fill=fill, outline="", tags=tag)
        self.canvas.create_oval(x2 - 2*r, y1, x2, y1 + 2*r, fill=fill, outline="", tags=tag)
        self.canvas.create_oval(x1, y2 - 2*r, x1 + 2*r, y2, fill=fill, outline="", tags=tag)
        self.canvas.create_oval(x2 - 2*r, y2 - 2*r, x2, y2, fill=fill, outline="", tags=tag)

    def _draw_hud(self):
        """Draw the heads-up display: score, best score, speed, and jump indicator.

        All HUD elements use rounded-rectangle backgrounds for readability.

        Parameters:
            None

        Returns:
            None
        """
        score_text = f"Score: {int(self.score)}"
        # Score box (top-right)
        self._draw_rounded_rect(
            SCREEN_WIDTH - 170, 6, SCREEN_WIDTH - 6, 36,
            r=8, fill=HUD_BG, tag="hud"
        )
        self.canvas.create_text(SCREEN_WIDTH - 88, 21,
                                anchor="center", text=score_text,
                                font=("Arial", 16, "bold"), fill=WHITE, tags="hud")
        # Best score (below)
        self._draw_rounded_rect(
            SCREEN_WIDTH - 150, 42, SCREEN_WIDTH - 6, 66,
            r=8, fill=HUD_BG, tag="hud"
        )
        self.canvas.create_text(SCREEN_WIDTH - 78, 54,
                                anchor="center", text=f"Best: {self.high_score}",
                                font=("Arial", 14), fill=YELLOW, tags="hud")
        # Speed (top-left)
        self._draw_rounded_rect(6, 6, 150, 30, r=8, fill=HUD_BG, tag="hud")
        self.canvas.create_text(78, 18,
                                anchor="center", text=f"Speed: {self.speed:.1f}",
                                font=("Arial", 14), fill=WHITE, tags="hud")
        # Jump indicator
        if self.jump_active:
            self._draw_rounded_rect(6, 38, 100, 60, r=8, fill="#005000", tag="hud")
            self.canvas.create_text(53, 49,
                                    anchor="center", text="JUMP!",
                                    font=("Arial", 13, "bold"), fill="#50FF50", tags="hud")

    def _draw_menu_overlay(self):
        """Draw the main-menu overlay panel with title and control instructions.

        Displays a semi-transparent dark panel in the centre of the screen
        with the game title, a short description, control hints, and the
        prompt to press ENTER to start.

        Parameters:
            None

        Returns:
            None
        """
        # Semi-transparent panel (simulate with a filled rectangle + stipple)
        self.canvas.create_rectangle(
            SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2 - 200,
            SCREEN_WIDTH // 2 + 280, SCREEN_HEIGHT // 2 + 160,
            fill="#001E50", stipple="gray50", outline="", tags="overlay"
        )
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 165,
                                text="SKI MOUNTAIN GAME",
                                font=("Arial", 38, "bold"), fill=WHITE, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 110,
                                text="Dodge obstacles and survive!",
                                font=("Arial", 18), fill=ICY_BLUE, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 75,
                                text="← → / A D  — move left & right",
                                font=("Arial", 15), fill=WHITE, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 48,
                                text="↑ ↓ / W S  — move up & down",
                                font=("Arial", 15), fill=WHITE, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 21,
                                text="SPACE  — jump over obstacles",
                                font=("Arial", 15), fill=WHITE, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30,
                                text="Press ENTER to Start",
                                font=("Arial", 24, "bold"), fill=YELLOW, tags="overlay")

    def _draw_gameover_overlay(self):
        """Draw the game-over overlay panel showing the player's score and best score.

        Displays a semi-transparent red panel with a ``WIPEOUT!`` heading,
        the final score, the all-time best score, and instructions to restart.

        Parameters:
            None

        Returns:
            None
        """
        self.canvas.create_rectangle(
            SCREEN_WIDTH // 2 - 260, SCREEN_HEIGHT // 2 - 170,
            SCREEN_WIDTH // 2 + 260, SCREEN_HEIGHT // 2 + 130,
            fill="#500000", stipple="gray50", outline="", tags="overlay"
        )
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140,
                                text="WIPEOUT!", font=("Arial", 48, "bold"),
                                fill=RED, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 65,
                                text=f"Score: {int(self.score)}",
                                font=("Arial", 28, "bold"), fill=WHITE, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20,
                                text=f"Best: {self.high_score}",
                                font=("Arial", 28, "bold"), fill=YELLOW, tags="overlay")
        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60,
                                text="Press R or ENTER to Restart",
                                font=("Arial", 22, "bold"), fill=ICY_BLUE, tags="overlay")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        SkiGame()
    except Exception as e:
        print(f"[SkiGame] Failed to start: {e}")
        sys.exit(1)
