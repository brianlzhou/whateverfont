"""Drippelgang: a Halloween display family. Every letter is dipped head first in goo, and the goo drips.

The `dipped` effect (goo.py, next to this file) coats the top of each letter, runs drips down the
strokes and hangs drops below them. Drippelgang is the color font with four palettes. Drippelgang Ink
is the same letters and goo in one color. See BRIEF.md.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from goo import PALETTES, dipped

SAMPLE = "Trick or Treat!"
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE)

BASE = preset("rounded", weight=138, cap_weight=1.06, xh=530, counter=300, width=0.98, spacing=1.08)

SET = latin()

FAMILY = Family(
    name="Drippelgang",
    description="Round, heavy letters dipped head first in goo, with drips and drops: for a Halloween poster.",
    base=BASE,
    recipes=dipped(SET),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=955,          # the puffed goo on the marks of Ẫ Ǘ; the drops stay above goo.FLOOR (-250)
    **COMMON)

INK = Family(
    name="Drippelgang Ink",
    description="The same dipped letters in one color, for a print in one ink or a program without color fonts.",
    base=BASE,
    recipes=dipped(SET, layered=False),
    styles={"Regular": {}},
    ascent=955,
    **COMMON)

DIRECTIONS = [FAMILY, INK]
