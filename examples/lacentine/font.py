"""Lacentine: a Valentine's Day display face. Each letter is cut from colored card and glued on a paper
doily cut to its shape, with a scalloped edge and a row of punched hearts. See BRIEF.md.

The `doily` effect is in lace.py, next to this file.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from lace import PALETTES, doily

SAMPLE = "Be Mine, Valentine"
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE,
              figures="proportional")           # a display face: "Feb 14" without the gap of a tabular 1

# Soft, round and heavy enough to hold its own inside the doily.
BASE = preset("rounded", weight=142, counter=305, width=1.04, xh=520, spacing=1.0)

FAMILY = Family(
    name="Lacentine",
    description="Soft round letters, each glued on a paper doily with a scalloped edge and punched hearts.",
    base=BASE.but(spacing=0.45),        # only the kerning reads this: the doily sets the sidebearings
    recipes=doily(latin()),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=1000, descent=-330,          # the doily reaches about 119 units past the letter
    **COMMON)

CARD = Family(
    name="Lacentine Card",
    description="The same soft letters without the doily, in one color: for the rest of the card.",
    base=BASE,
    styles={"Regular": {}},
    **COMMON)

DIRECTIONS = [FAMILY, CARD]
