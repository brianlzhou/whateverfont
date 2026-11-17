"""Knollrise: a color display family in which every letter is a hill on a topographic map.

The person asked for a font like the contour lines on a hiking map. The effect in topo.py, next to this
file, shrinks the outline of each letter by growing distances and draws each step as a thin line, so the
lines run parallel to the edge, ring inside ring, close together near the edge and wider apart toward the
middle of the stroke. Every fifth line, starting with the edge, is a thicker index contour, and one small
triangle marks the highest point of each letter. Knollrise Lines is the same rings in one color.
Each of the four palettes is a kind of map; topo.GROUNDS names the paper each one is drawn for.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from topo import PALETTES, contour_map

SAMPLE = "Summit Ridge"
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE,
              styles={"Regular": {}},
              ascent=975)        # room for the marks of the capitals (Ö Ẫ Ǘ)

# Very heavy, wide and round, so that a stem holds five lines on each side and a ridge between them.
# Every stroke has nearly one thickness (cap_weight, round_weight, and a contrast that undoes the
# engine's thinner bold horizontals), so every stem of a line shows the same lines. Weight 176 is the
# heaviest that stays clean: at 184 the s gets a notch where its spine meets the lower curve.
BASE = preset("rounded", weight=176, contrast=1.15, cap_weight=1.0, round_weight=1.0, width=1.14, counter=340,
              xh=530, spacing=1.06, aperture=0.6, join=0.9, a_story=1)

FAMILY = Family(
    name="Knollrise",
    description="Heavy round letters drawn as hills on a contour map: brown lines ring inside ring on a pale tint.",
    base=BASE,
    recipes=contour_map(latin()),
    palettes=PALETTES,
    **COMMON)

LINES = Family(
    name="Knollrise Lines",
    description="The same contour lines and summit marks in one color, with the paper showing between them.",
    base=BASE,
    recipes=contour_map(latin(), color=False),
    **COMMON)

DIRECTIONS = [FAMILY, LINES]
