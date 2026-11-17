"""Neon: a bar-menu face drawn as one bent glass tube, with a color glow companion."""

from whateverfont import Axis, Family, effects, latin
from whateverfont.presets import preset

SAMPLE = "Happy Hour 5-7 · Negroni 12 · Gin Fizz 11"

# A glass tube has the same thickness everywhere: no contrast, no thinning at joins,
# capitals the same tube as lowercase, and fully round ends where the tube stops.
TUBE = dict(contrast=1.0, round_weight=1.0, join=1.0, cap_weight=1.0, flare=0.0, roundness=1.0,
            dot="round")

# 1. Geometric tube: circles and straight runs, single-story a, airy spacing.
BASE = preset("geometric", **TUBE, weight=62, xh=500, width=1.04, counter=300, classical=0.5,
              apex=0.6, aperture=0.6, spacing=1.18)

# 2. Diner: tall, narrow, with squarer bends, like a 1950s roadside sign.
DINER = preset("condensed", **TUBE, weight=62, xh=560, superness=0.5, aperture=0.45, apex=0.6,
               spacing=1.22)

# 3. Bent rod: wide, squared bends like tube bent around a jig, low x-height.
ROD = preset("technical", **TUBE, weight=62, xh=450, width=1.28, superness=0.92, apex=0.9,
             aperture=0.4, spacing=1.2, desc=-222)


def axes(base):
    w = base.weight
    return [
        Axis("wght", "Weight", 200, 400, 700, {200: {"weight": w * 0.55}, 700: {"weight": w * 1.9}}),
        Axis("slnt", "Slant", -10, 0, 0, {-10: {"slant": 10}}),
    ]


STYLES = {
    "Light": {"wght": 200},
    "Regular": {},
    "Bold": {"wght": 700},
    "Italic": {"slnt": -10},
}

FAMILY = Family(
    name="Neon",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Round geometric letters drawn as one even tube with round ends. The all-round menu face.",
    base=BASE,
    axes=axes(BASE),
    styles=STYLES,
    sample=SAMPLE,
)

DINER_FAMILY = Family(
    name="Neon Diner",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Tall, narrow tube letters with squarer bends, like a roadside diner sign.",
    base=DINER,
    axes=axes(DINER),
    styles=STYLES,
    sample=SAMPLE,
)

ROD_FAMILY = Family(
    name="Neon Rod",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Wide, low letters whose tube turns tight squared corners, like glass bent on a jig.",
    base=ROD,
    axes=axes(ROD),
    styles=STYLES,
    sample=SAMPLE,
)


# The glow: effects.glow draws each letter as stacked color layers. A pale tube sits inside a
# saturated halo, inside three translucent rings that overlap like real light.
def palette(rgb, tube):
    """Glow rings in one color, more opaque toward the tube."""
    return effects.glow_palette(rgb, tube)


# Night palettes have a white-hot tube for dark walls. Day palettes color the tube itself,
# because a pale tube on a light wall reads as an outline letter.
PINK = palette("#FF2E9A", "#FFE6F3")
BLUE = palette("#22A6FF", "#E3F6FF")
PINK_DAY = palette("#FF2E9A", "#F0157F")
BLUE_DAY = palette("#22A6FF", "#0A86E0")

GLOW = Family(
    name="Neon Glow",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="The Neon tube lit: a color font with a soft glow, in pink or blue palettes.",
    base=BASE,
    recipes=effects.glow(latin(), size=80),
    # No axes: the color format (COLR version 0) cannot vary, so a color family is static.
    styles={"Regular": {}},
    palettes={"Pink": PINK, "Blue": BLUE, "Pink Day": PINK_DAY, "Blue Day": BLUE_DAY},
    sample=SAMPLE,
)

DIRECTIONS = [FAMILY, DINER_FAMILY, ROD_FAMILY, GLOW]
