"""Hopstep: a human alphabet. Every letter is a dancing figure. See BRIEF.md."""

from whateverfont import Family, Params

import body
from poses import LETTERS, SIGNS

SAMPLE = "DANCE"
BASE = Params(kerning=0)
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE,
              ascent=980, descent=-160)

# Six colors. The letters are sorted so that neighbors in English words seldom share a color (a search
# over the letter pairs of a word list leaves about 2% of neighbors alike), and so that no two neighbors
# in the alphabet do. A lowercase letter takes the next color.
GROUPS = {"c0": "BFSXZ", "c1": "DKMTV", "c2": "AJOQ", "c3": "CGPW", "c4": "EIUY", "c5": "HLNR"}
KEYS = {c: key for key, letters in GROUPS.items() for c in letters}
MIRRORED = "AHIMOTUVWXY"        # a mirror still reads as the same letter

INK = "#161616"
BRIGHT = ["#FF8A1F", "#EE3B33", "#FFD21A", "#2A7DE1", "#F25CA8", "#22AE5A"]
GROUND = "#141416"              # the board the chalk palette is drawn for


def palette(ink, colors):
    if isinstance(colors, str):
        colors = [colors] * 6
    return {"ink": ink} | {f"c{i}": c for i, c in enumerate(colors)}


PALETTES = {
    # Flat bright colors in a thick black line.
    "Bright": palette(INK, BRIGHT),
    # White chalk on a black board: the line only. The bodies take the color of the board.
    "Chalk": palette("#F4F1E8", GROUND),
    # A poster on black: the same bright colors in a white line.
    "Poster": palette("#FFFFFF", BRIGHT),
    # One quiet color for every figure.
    "Quiet": palette("#2B2B33", "#E7DCC6"),
}

COLOR = Family(
    name="Hopstep",
    description="A human alphabet: every letter is a figure caught mid-dance, in a thick black line and flat "
                "bright color. Palettes: Bright, Chalk, Poster, Quiet.",
    base=BASE, recipes=body.recipes(LETTERS, KEYS, MIRRORED, SIGNS), styles={"Regular": {}},
    palettes=PALETTES, **COMMON)

SOLID = Family(
    name="Hopstep Solid",
    description="The same figures in one color: solid bodies, with a white line where one limb crosses another.",
    base=BASE, recipes=body.recipes(LETTERS, KEYS, MIRRORED, SIGNS, style="solid"), styles={"Regular": {}}, **COMMON)

LINE = Family(
    name="Hopstep Line",
    description="The same figures as a line drawing in one color: the line and the dashes only.",
    base=BASE, recipes=body.recipes(LETTERS, KEYS, MIRRORED, SIGNS, style="line"), styles={"Regular": {}}, **COMMON)

FAMILY = COLOR
DIRECTIONS = [COLOR, SOLID, LINE]
