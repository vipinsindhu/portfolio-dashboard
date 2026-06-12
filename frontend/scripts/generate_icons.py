"""Generate PWA app icons: indigo rounded square with a rising chart line.

Run from the frontend directory:  python scripts/generate_icons.py
Outputs to public/icons/ (copied into dist/ by vite build).
"""

import os

from PIL import Image, ImageDraw

INDIGO = (85, 104, 211, 255)        # --primary-color #5568d3
INDIGO_DARK = (68, 86, 199, 255)
WHITE = (255, 255, 255, 255)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "icons")


def draw_icon(size, maskable=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Maskable icons must fill the full canvas (the OS applies its own mask);
    # regular icons get a rounded square with transparent corners.
    if maskable:
        draw.rectangle([0, 0, size, size], fill=INDIGO)
        pad = size * 0.24  # safe zone for OS masks
    else:
        radius = size * 0.22
        draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=INDIGO)
        pad = size * 0.20

    # Rising chart line with three points
    w = size - 2 * pad
    points = [
        (pad, pad + w * 0.85),
        (pad + w * 0.38, pad + w * 0.48),
        (pad + w * 0.62, pad + w * 0.62),
        (pad + w, pad + w * 0.05),
    ]
    line_width = max(3, int(size * 0.055))
    draw.line(points, fill=WHITE, width=line_width, joint="curve")
    dot_r = max(3, int(size * 0.045))
    for x, y in points:
        draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=WHITE)

    # Arrowhead on the last segment
    ax, ay = points[-1]
    ah = size * 0.10
    draw.polygon(
        [(ax - ah * 0.9, ay - ah * 0.1), (ax + ah * 0.15, ay - ah * 0.35), (ax - ah * 0.1, ay + ah * 0.8)],
        fill=WHITE,
    )
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    specs = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, True),  # iOS dislikes transparency
    ]
    for name, size, maskable in specs:
        path = os.path.join(OUT_DIR, name)
        draw_icon(size, maskable=maskable).save(path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
