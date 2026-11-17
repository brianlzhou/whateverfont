"""Arroyo: a flare serif for long essays, with a sans-to-flare axis."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "A quiet serif for long arguments"

AXES = [
    Axis("wght", "Weight", 250, 400, 800, {250: {"weight": 44}, 800: {"weight": 148}}),
    # 0 is a plain sans, 100 is a sharp wedge. The default sits in between.
    Axis("FLAR", "Flare", 0, 40, 100, {0: {"flare": 0.0}, 100: {"flare": 0.78, "flare_len": 150}}),
    Axis("slnt", "Slant", -11, 0, 0, {-11: {"slant": 11, "width": 0.955}}),
]

STYLES = {
    "Light": {"wght": 300},
    "Regular": {},
    "Italic": {"slnt": -11},
    "Medium": {"wght": 520},
    "Bold": {"wght": 700},
    "Bold Italic": {"wght": 700, "slnt": -11},
}

BASE = preset("flare", flare=0.34, flare_len=230, contrast=0.60, xh=492, counter=282, aperture=0.82, apex=0.45,
              spacing=0.98)

FAMILY = Family(
    name="Arroyo",
    description="A calm flare serif. Stems swell gently toward their ends; capitals keep Roman proportions.",
    base=BASE,
    axes=AXES,
    styles=STYLES,
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

# Two more directions to compare on the review board.
GLYPHIC = Family(
    name="Arroyo Glyphic",
    description="Sharper and more incised: short wedge flares, higher contrast, pointed apexes.",
    base=preset("glyphic", flare=0.58, flare_len=150, contrast=0.48, xh=478, counter=286, weight=84),
    axes=[
        Axis("wght", "Weight", 250, 400, 800, {250: {"weight": 46}, 800: {"weight": 150}}),
        Axis("FLAR", "Flare", 0, 60, 100, {0: {"flare": 0.0}, 100: {"flare": 0.95}}),
        Axis("slnt", "Slant", -11, 0, 0, {-11: {"slant": 11, "width": 0.955}}),
    ],
    styles=STYLES,
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

TEXT = Family(
    name="Arroyo Text",
    description="Sturdier for small sizes: lower contrast, larger x-height, looser spacing, a hint of flare.",
    base=preset("flare", flare=0.20, flare_len=200, contrast=0.74, xh=515, counter=292, weight=86, aperture=0.9,
                spacing=1.06, apex=0.6),
    axes=[
        Axis("wght", "Weight", 250, 400, 800, {250: {"weight": 48}, 800: {"weight": 150}}),
        Axis("FLAR", "Flare", 0, 25, 100, {0: {"flare": 0.0}, 100: {"flare": 0.8, "flare_len": 150}}),
        Axis("slnt", "Slant", -11, 0, 0, {-11: {"slant": 11, "width": 0.955}}),
    ],
    styles=STYLES,
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

DIRECTIONS = [FAMILY, GLYPHIC, TEXT]
