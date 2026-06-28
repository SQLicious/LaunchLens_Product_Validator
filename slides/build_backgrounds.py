"""Generate the deck's atmospheric background plates (slides/assets/bg/*.png).

Emulates the brief-video look: near-black navy base, soft corner glows (warm
amber + cool teal), and a faint blueprint grid. NO text is baked in -- kickers,
headlines, cards and ghost watermarks are added as crisp PowerPoint objects in
build_deck.py, so everything stays editable.

Run: `python slides/build_backgrounds.py`  (needs numpy + Pillow).
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "assets", "bg")
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080

# deep navy base, darker at the top, a touch of teal toward the bottom
NAVY_TOP = np.array([11, 15, 25])      # #0B0F19
NAVY_BOT = np.array([9, 16, 24])       # #091018
GRID = (20, 27, 43)                    # #141B2B faint blueprint lines

AMBER = np.array([245, 166, 48])
TEAL = np.array([45, 212, 167])


def _base():
    yy = np.linspace(0, 1, H)[:, None, None]
    return (NAVY_TOP * (1 - yy) + NAVY_BOT * yy)


def _glow(img, cx, cy, color, strength, radius):
    """Add a soft radial glow centred at (cx,cy) in 0..1 slide coords."""
    gx = np.linspace(0, 1, W)[None, :, None]
    gy = np.linspace(0, 1, H)[:, None, None]
    # account for aspect so the glow stays round-ish
    dist = np.sqrt(((gx - cx) * (W / H)) ** 2 + (gy - cy) ** 2) / radius
    halo = np.clip(1 - dist, 0, 1) ** 2.2
    return img + color * halo * strength


def _grid(draw, step=64, alpha=20, fade_corner=True):
    """Faint grid, optionally fading out away from the top-left."""
    for x in range(0, W, step):
        for y in range(0, H, step):
            a = alpha
            if fade_corner:
                f = max(0.0, 1 - ((x / W) * 0.7 + (y / H) * 0.9))
                a = int(alpha * f)
            if a <= 0:
                continue
            draw.point((x, y), fill=GRID + (a,))
    # light continuous lines only in the upper-left band
    for x in range(0, int(W * 0.55), step):
        draw.line([(x, 0), (x, int(H * 0.5))], fill=GRID + (14,), width=1)
    for y in range(0, int(H * 0.5), step):
        draw.line([(0, y), (int(W * 0.55), y)], fill=GRID + (14,), width=1)


def make(path, glows):
    img = _base()
    for g in glows:
        img = _glow(img, *g)
    # subtle noise to dither away 8-bit banding rings in the soft glows
    img = img + np.random.uniform(-2.0, 2.0, (H, W, 1))
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _grid(ImageDraw.Draw(overlay))
    Image.alpha_composite(base, overlay).convert("RGB").save(path, "PNG")
    return path


# cover -- warm amber glow top-left (matches the brief title frame)
make(os.path.join(OUT, "bg_title.png"), [
    (0.10, 0.08, AMBER, 0.42, 0.95),
    (0.92, 0.95, TEAL, 0.12, 0.7),
])

# content -- soft warm glow upper-right, cool teal lower-left
make(os.path.join(OUT, "bg_content.png"), [
    (0.82, 0.30, AMBER, 0.16, 0.85),
    (0.10, 0.95, TEAL, 0.14, 0.8),
])

# core / verdict -- teal glow lower-right
make(os.path.join(OUT, "bg_core.png"), [
    (0.88, 0.82, TEAL, 0.20, 0.85),
    (0.08, 0.10, AMBER, 0.10, 0.7),
])

print("wrote plates ->", OUT)
for n in sorted(os.listdir(OUT)):
    print("  ", n)
