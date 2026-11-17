"""Draw site/card.png, the picture that a link to the site shows in a message or a post.

Run from the repository root, after the examples are built:

    python scripts/build_card.py

A link preview wants a picture of 1200 by 630. This one sets the four words of the site's title in four of the
example fonts, each on the ground of its palette, with the engine's own renderer (whateverfont.proof). The
picture is in the repository, so the site's build only copies it. Run this again when one of the four fonts
changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from whateverfont import proof      # noqa: E402

OUT = ROOT / "site" / "card.png"
SIZE = (1200, 630)
#: Two rows of two tiles: (word, family, palette, ground, ink). The grounds are the ones of the site's poster.
ROWS = [
    [("Whatever", "Starry Initials", "Night", "#0A0F24", "#9DC1E6"),
     ("Font", "Cabochon", "Jade", "#7A1418", "#8ACDA3")],
    [("You", "Cutout Color", "Paper", "#FBF7EC", "#1F53B5"),
     ("Want.", "Last Bell Snow", "Mitten", "#12372A", "#F6F1E7")],
]
PAD = 64            # the least room on each side of a word, in pixels of the picture
TALLEST = 190       # the largest size of the letters
SCALE = 2           # the picture is drawn at twice its size and made smaller, for smooth edges


def font_file(family: str) -> Path:
    """The built font of an example family."""
    for index in sorted((ROOT / "examples").glob("*/fonts/index.json")):
        for f in json.loads(index.read_text(encoding="utf-8"))["families"]:
            if f["name"] == family:
                return index.parent.parent / f["ttf"]["Regular"]
    raise SystemExit(f"no example family is named {family!r}: build the examples first")


def word(r: proof.Renderer, text: str, px: float, ground: str, ink: str) -> Image.Image:
    """The word on its ground, cut to its ink."""
    paper = proof.rgb(ground)
    canvas = Image.new("RGB", (int(r.width(text, px) + px * 2), int(px * 3)), paper)
    r.draw(canvas, px, px * 2, text, px, ink=proof.rgb(ink))
    box = ImageChops.difference(canvas, Image.new("RGB", canvas.size, paper)).getbbox()
    return canvas.crop(box)


def main() -> None:
    W, H = SIZE[0] * SCALE, SIZE[1] * SCALE
    tall = H // len(ROWS)
    rows = [[(text, proof.Renderer(font_file(family), palette=palette), ground, ink)
             for text, family, palette, ground, ink in row] for row in ROWS]
    # one size for every word: the largest at which the widest row still has its room
    px = TALLEST * SCALE
    for row in rows:
        ink_width = sum(r.width(text, 1000) for text, r, _, _ in row)
        px = min(px, (W - 2 * PAD * SCALE * len(row)) / ink_width * 1000)
    card = Image.new("RGB", (W, H), "white")
    for k, row in enumerate(rows):
        words = [word(r, text, px, ground, ink) for text, r, ground, ink in row]
        spare = (W - sum(w.width for w in words)) / len(row)        # each tile gets the same room around its word
        x = 0.0
        for (text, r, ground, ink), picture in zip(row, words):
            wide = picture.width + spare
            left, right = round(x), round(x + wide) if row[-1][0] != text else W
            card.paste(Image.new("RGB", (right - left, tall), proof.rgb(ground)), (left, k * tall))
            card.paste(picture, (left + (right - left - picture.width) // 2, k * tall + (tall - picture.height) // 2))
            x += wide
    card = card.resize(SIZE, Image.LANCZOS)
    card.save(OUT, optimize=True)
    print(f"{OUT.relative_to(ROOT)}: {SIZE[0]} by {SIZE[1]}, {OUT.stat().st_size / 1000:.0f} kB")


if __name__ == "__main__":
    main()
