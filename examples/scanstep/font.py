"""Scanstep: a pixel font on one fixed grid, like the text of an 8-bit video game.

Every glyph is whole square pixels, eight to the em: stems two pixels wide, horizontal strokes one
pixel tall, capitals seven rows, the x-height five. The effect and the drawings are in pixels.py, next
to this file. Scanstep is the plain one-color family. Scanstep Color has the same pixels with a hard
shadow one pixel down and to the right and a darker lower part, in four palettes.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from pixels import pixelate, with_space

SAMPLE = "PRESS START"

# The letters under the pixels. Only a glyph without a drawing in pixels.py would be sampled from them,
# so the numbers set how such a glyph falls on the grid: stems of 125 units (two cells of the sampling
# grid), monoline, square ends, squared rounds, and the heights on the rows of the grid. The heights
# are also the ones the font reports (x-height 625, capitals 875) and the ones the marks attach to.
BASE = preset("technical", weight=125, contrast=1.0, cap_weight=1.0, round_weight=1.0, join=1.0,
              xh=625, cap=875, asc=875, desc=-250, overshoot=0, counter=200, superness=0.9,
              roundness=0.0, apex=1.0, kerning=0)

# The line: ten rows above the baseline (marks over capitals end on row 9) and three below (the
# descenders take two, the comma below Ș and Ķ the third), thirteen rows in all.
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
              styles={"Regular": {}}, ascent=1250, descent=-375)

PLAIN = Family(
    name="Scanstep",
    description="A pixel font on one fixed grid, eight pixels to the em, like the text of an 8-bit game.",
    base=BASE,
    recipes=with_space(pixelate(latin())),
    sample="Score 004200  Lives x3",
    **COMMON,
)

#                face        lower       shadow
PALETTES = {
    # a title screen: gold letters that turn orange at the foot, a deep red shadow, on night blue
    "Title": {"face": "#FFE45C", "lower": "#FF8A1E", "shadow": "#B3123C"},
    # a dungeon: bone and stone on black, with a purple shadow
    "Dungeon": {"face": "#E9E1CC", "lower": "#9E937D", "shadow": "#4B2D63"},
    # a handheld's green screen: the four greens of the display
    "Handheld": {"face": "#3B6634", "lower": "#16361A", "shadow": "#86A43C"},
    # a printed manual: red letters on cream paper, with a shadow a few shades darker than the paper
    "Manual": {"face": "#DE3A2C", "lower": "#981D1A", "shadow": "#CDB287"},
}

# The ground each palette is drawn for, and the color of plain text beside it: (ground, ink).
GROUNDS = {
    "Title": ("#141A4A", "#FFE45C"),
    "Dungeon": ("#121014", "#E9E1CC"),
    "Handheld": ("#B6C65A", "#16361A"),
    "Manual": ("#F4EAD2", "#2A2422"),
}

COLOR = Family(
    name="Scanstep Color",
    description="The Scanstep pixels with a hard shadow and a darker foot, in four palettes: a title "
                "screen, a dungeon, a handheld's green screen and a printed manual.",
    base=BASE,
    # one more pixel of white after each glyph, so the shadow does not touch the next letter
    recipes=with_space(pixelate(latin(), layers=True, gap=2), width=5),
    palettes=PALETTES,
    sample=SAMPLE,
    **COMMON,
)

# The color family is the one to show first (Title palette on its night blue); the plain family is the
# one to set text in any color.
FAMILY = COLOR
DIRECTIONS = [COLOR, PLAIN]
