"""Caliper: a light condensed flare for titles, and Gantry, a technical sans for labels."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "Measure twice, cut once, ship on Friday"

FAMILY = Family(
    name="Caliper",
    description="Tall, narrow and light, with flared ends. Made for large titles on white pages.",
    base=preset("flare", width=0.70, weight=62, flare=0.42, flare_len=210, contrast=0.66, xh=505, cap=715, asc=752,
                counter=292, classical=0.55, aperture=0.7, apex=0.4, spacing=0.92),
    axes=[
        Axis("wght", "Weight", 200, 300, 700, {200: {"weight": 38}, 700: {"weight": 132}}),
        Axis("wdth", "Width", 60, 75, 100, {60: {"width": 0.56}, 100: {"width": 0.98}}),
        Axis("FLAR", "Flare", 0, 45, 100, {0: {"flare": 0.0}, 100: {"flare": 0.85, "flare_len": 150}}),
        Axis("slnt", "Slant", -10, 0, 0, {-10: {"slant": 10}}),
    ],
    styles={
        "Thin": {"wght": 200},
        "Light": {},
        "Light Italic": {"slnt": -10},
        "Regular": {"wght": 400},
        "Medium": {"wght": 520},
        "Bold": {"wght": 700},
        "Light Compressed": {"wdth": 60},
        "Light Wide": {"wdth": 100},
    },
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

GANTRY = Family(
    name="Gantry",
    description="Squared rounds and flat cuts, like the labels on a machine. Corners soften along the ROND axis.",
    base=preset("technical", weight=80, xh=520, counter=268, superness=0.8, roundness=0.25, spacing=1.0),
    axes=[
        Axis("wght", "Weight", 250, 400, 800, {250: {"weight": 46}, 800: {"weight": 150}}),
        Axis("ROND", "Roundness", 0, 25, 100, {0: {"roundness": 0.0}, 100: {"roundness": 1.0}}),
        Axis("wdth", "Width", 75, 100, 100, {75: {"width": 0.74}}),
    ],
    styles={"Light": {"wght": 300}, "Regular": {}, "Medium": {"wght": 520}, "Bold": {"wght": 700},
            "Round": {"ROND": 100}, "Condensed": {"wdth": 75}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

DIRECTIONS = [FAMILY, GANTRY]
