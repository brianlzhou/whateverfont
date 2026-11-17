"""Tally Mono: a monospaced face for code and terminals."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "def tally(items): return sum(1 for i in items if i)"

# Every glyph is 600 units wide. Squared rounds and a tall x-height keep small sizes clear;
# a little roundness on the corners takes the edge off ten hours of reading.
BASE = preset("mono", weight=88, superness=0.33, roundness=0.42, xh=542, counter=294, aperture=0.6)

FAMILY = Family(
    name="Tally Mono",
    description="A calm monospaced face for code: a dotted zero, barred i, l and 1, and operators drawn wide.",
    base=BASE,
    axes=[
        Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 56}, 700: {"weight": 126}}),
        Axis("slnt", "Slant", -10, 0, 0, {-10: {"slant": 10}}),
    ],
    styles={"Regular": {}, "Italic": {"slnt": -10}, "Bold": {"wght": 700}, "Bold Italic": {"wght": 700, "slnt": -10}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)
