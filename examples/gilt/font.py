"""Gilt: a color display family after the gold robes in Klimt's The Kiss.

The letters are heavy, so that a stem is wide enough to carry ornament. The `klimt` effect (klimt.py,
next to this file) sets each letter with upright gold tiles in courses, then mixes in the motifs of the
two robes: runs of black and white rectangles, small spirals, and colored circles with rings.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from klimt import PALETTES, klimt

SAMPLE = "Anna & Felix"

FAMILY = Family(
    name="Gilt",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Roman capitals with an even mix of tiles, rectangles, spirals and circles: for the heading.",
    base=preset("flare", weight=144, contrast=0.62, counter=310, width=1.05, flare=0.0, spacing=1.08),
    recipes=klimt(latin(), circles=1.25, spirals=0.85, blocks=1.5),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=955,          # room for the marks of heavy capitals (Ż Ǘ)
    sample=SAMPLE,
)

ROBE = Family(
    name="Gilt Robe",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Wide, squared Secession poster letters with the man's robe, black and white: for a label.",
    base=preset("geometric", weight=150, superness=0.5, counter=310, width=1.04, spacing=1.08),
    recipes=klimt(latin(), tile=(36.0, 62.0), courses=(64.0, 84.0, 104.0, 124.0),
                  circles=0.3, spirals=1.1, blocks=1.8, seed=3),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=970,          # room for the marks of heavy capitals (Ż Ǘ)
    sample=SAMPLE,
)

BLOOM = Family(
    name="Gilt Bloom",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Soft round letters with the woman's robe, small tiles and many colored circles.",
    base=preset("rounded", weight=150, counter=310, spacing=1.08),
    recipes=klimt(latin(), tile=(30.0, 52.0), courses=(40.0, 50.0, 60.0, 72.0),
                  share=(0.13, 0.06), circles=2.2, spirals=0.3, blocks=0.3, seed=5),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=960,          # room for the marks of heavy capitals (Ż Ǘ)
    sample=SAMPLE,
)

DIRECTIONS = [FAMILY, ROBE, BLOOM]
