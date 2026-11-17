"""Setsquare: a geometric sans of circles and straight lines."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "A circle, a square and a triangle"

# The o is close to a circle: round_width 1.28 makes it as wide as it is tall. A one-story a, round dots,
# sharp points on A, V and W, and capitals with Roman widths (a wide O next to a narrow E).
BASE = preset("geometric", xh=506, cap=700, asc=754, weight=84, cap_weight=1.05, contrast=0.95, counter=262,
              round_width=1.28, cap_width=1.08, aperture=0.55, classical=0.5, apex=0.25, spacing=1.16,
              word_space=1.15, dot="round")

FAMILY = Family(
    name="Setsquare",
    description="A geometric sans: an o that is close to a circle, a one-story a, sharp points and round dots, "
                "in five weights.",
    base=BASE,
    axes=[
        Axis("wght", "Weight", 300, 400, 700, {
            300: {"weight": 58, "counter": 268},
            700: {"weight": 126, "counter": 262, "contrast": 1.0, "spacing": 1.08, "arm": 1.2, "aperture": 0.8},
        }),
        Axis("slnt", "Slant", -9, 0, 0, {-9: {"slant": 9}}),
    ],
    styles={"Light": {"wght": 300}, "Regular": {}, "Italic": {"slnt": -9}, "Medium": {"wght": 500},
            "Semibold": {"wght": 600}, "Bold": {"wght": 700}, "Bold Italic": {"wght": 700, "slnt": -9}},
    sample=SAMPLE,
    figures="proportional",
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)
