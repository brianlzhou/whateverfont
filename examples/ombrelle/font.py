"""Ombrelle: letters painted in whole dots of pure color, lit by an afternoon sun from the upper left.

The `dotted` effect (seurat.py, next to this file) fills each letter with a row of dots along its edge
and dots inside it, on an underpainting. Each dot takes its color from the light: warm on the side that
faces the sun, the local color in the middle, cool violet-blue in the shadow, with orange sprinkled into
the blue. Pale dots spill out on the shadow side. Ombrelle Initials sets each capital on a square of
dotted lawn, with its cast shadow, inside a painted border of dots.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

import seurat

# The figures in those paintings are upright, simple and solid. A heavy geometric sans gives strokes wide
# enough for three or four dots across, and plain round forms that light and shadow can model.
BASE = preset("geometric", weight=148, width=1.06, counter=312, xh=520, apex=0.5, roundness=0.4,
              spacing=1.06)

PALETTES = {
    # A sunlit park: grass greens, yellow sun, violet-blue shadow with orange in it, on cream.
    "Afternoon": seurat.palette(
        "#2E5A45", ["#3A3488", "#4A63B4", "#33906E", "#56A445", "#A6C93E", "#F0C63C", "#F6DE78"],
        "#EA772C", "#D6CBEA",
        ground="#EDE2C3", field=["#CFC3E2", "#BFD69A", "#EFD98A", "#FAF0CC"], shade="#7F78C2",
        rim="#2A2F6E", border=["#E8742C", "#C9503A", "#3A4FA8", "#2A2A78"]),
    # Evening water in a harbor: blues, with pink and gold light from the sunset, on a peach sky.
    "Harbor": seurat.palette(
        "#25457E", ["#2A2A6E", "#3550A8", "#2C7FB8", "#3FA3C2", "#8C7FC9", "#E78AA6", "#F5B455"],
        "#EC6A2C", "#C9C3E8",
        ground="#EDD0C2", field=["#B9B4E0", "#A6CFDC", "#F0B8C2", "#FBE2C6"], shade="#6E6BB8",
        rim="#1F2456", border=["#EC6A2C", "#D8577A", "#3550A8", "#24246A"]),
    # A circus under gaslight: reds, oranges and yellows, blue-violet shadow, on a night ground.
    "Circus": seurat.palette(
        "#8C2336", ["#4A43A6", "#7A4AA8", "#C2353A", "#E2553A", "#EE8A2E", "#F6C238", "#FBE7A0"],
        "#F39A2E", "#3B3684",
        ground="#2A2560", field=["#2F2A6C", "#3E3584", "#55429A", "#6E4FA6"], shade="#16133A",
        rim="#5E1A2C", border=["#F6C238", "#EE8A2E", "#E2553A", "#C2353A"]),
}

# The paper each palette is made for: a page or a web site should set this background. Afternoon and
# Harbor also read on white. Circus is made for its night ground.
GROUNDS = {"Afternoon": "#F3EBD5", "Harbor": "#F4DED2", "Circus": "#1F1B47"}

COMMON = dict(base=BASE, styles={"Regular": {}}, palettes=PALETTES, ascent=955,
              designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou")

FAMILY = Family(
    name="Ombrelle",
    description="Letters in whole dots of pure color, lit from the upper left: warm sun on one side, "
                "violet-blue shadow with orange sprinkled in on the other.",
    recipes=seurat.dotted(latin()),
    sample="Sunday on the Island",
    **COMMON,
)

INITIALS = Family(
    name="Ombrelle Initials",
    description="Every capital stands on a square of dotted lawn and casts a long afternoon shadow, inside a "
                "painted border of dots: blue beside the sun, orange beside the shade. The rest is Ombrelle.",
    recipes=seurat.initials(latin()),
    sample="A Sunday On The Island",
    **COMMON,
)

DIRECTIONS = [FAMILY, INITIALS]
