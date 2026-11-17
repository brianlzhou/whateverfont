"""Kanagawa: a poster title face after Hokusai's Great Wave off Kanagawa."""

from whateverfont import Family, latin
from whateverfont.presets import preset

from breaker import BARE, NIGHT, PRINT, breaker

SAMPLE = "THE GREAT WAVE"

PALETTES = {"Print": PRINT, "Night": NIGHT, "Bare": BARE}

# 1. Carved: a heavy flare serif with Roman capitals, like letters cut in a woodblock.
FAMILY = Family(
    name="Kanagawa",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Heavy flared capitals, cut like a woodblock. Every letter is a wave with a foam crest.",
    base=preset("flare", weight=165, counter=300, spacing=1.1, dot="round"),
    recipes=breaker(latin()),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=1010, descent=-270,    # room for the marks of heavy capitals (Ż Ǘ)
    sample=SAMPLE,
)

# 2. Brushed: written with a broad brush held at an angle, thick and thin.
BRUSH = Family(
    name="Kanagawa Brush",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Written with a broad brush: thick and thin strokes, a livelier and more bookish wave.",
    base=preset("broadnib", weight=158, contrast=0.42, stress=26, slant=8, width=0.92, counter=280, spacing=1.14,
                dot="round"),
    recipes=breaker(latin(), streaks=2, every=132),
    styles={"Regular": {}},
    ascent=1005, descent=-300,    # the slanted j and parentheses, and the marks of the capitals, pass the default line
    palettes=PALETTES,
    sample=SAMPLE,
)

# 3. Swell: fat, round, even strokes, like the swell before the wave breaks.
SWELL = Family(
    name="Kanagawa Swell",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Fat round letters with even strokes: the calm swell, with the most room for water.",
    base=preset("rounded", weight=190, counter=300, width=1.08, spacing=1.12, cap_weight=1.05),
    recipes=breaker(latin(), streaks=3, foam=0.22),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=1025, descent=-285,    # room for the marks of heavy capitals (Ż Ǘ)
    sample=SAMPLE,
)

DIRECTIONS = [FAMILY, BRUSH, SWELL]
