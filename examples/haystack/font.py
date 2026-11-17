"""Haystack: letters in short, broken touches of paint, and capitals that stand in a field in changing light."""

from whateverfont import Family, latin
from whateverfont.presets import preset

import haystack

SAMPLE = "Late Afternoon In The Field"

# Broad, low and soft, like something stacked by hand.
BASE = preset("humanist", weight=156, contrast=0.92, roundness=0.6, xh=530, counter=310, aperture=0.7,
              classical=0.3, apex=0.6, join=0.95, stress=0, width=1.04)

# One drawing, four hours. Each palette is: ground, sky (high to horizon), land (near to far),
# hay (shadow side to lit side), the cast shadow, and the color under the hay.
PALETTES = {
    "Noon": haystack.light("#D9C56A", ["#8FB6D9", "#B4CFE3", "#D6E2E6", "#EEEBD8"],
                           ["#B9A63F", "#CDBB52", "#DCCB6B", "#C8CF8A"],
                           ["#7A4A2E", "#A8672F", "#CF8C36", "#E8B452", "#F6DC8C"], "#5E5A8C", "#8A5528"),
    "Sunset": haystack.light("#C97B4A", ["#5B5A9A", "#9A6BA6", "#E08A7A", "#F7C27A"],
                             ["#8C4F4A", "#B5654A", "#D9824A", "#E9A765"],
                             ["#3D2A5E", "#6B3566", "#B4483F", "#E8743A", "#FBB05A"], "#3A2E6E", "#5A2F56"),
    "Snow": haystack.light("#DDE3EE", ["#9FB4D6", "#BFCBE2", "#E3DDE8", "#F6E6DD"],
                           ["#B9C6E0", "#CDD6EA", "#E2E6F2", "#F4F2F4"],
                           ["#3F3C6E", "#6A4E7A", "#A8626A", "#D98A62", "#F2C08A"], "#6F7FB8", "#54406E"),
    "Dusk": haystack.light("#2E3558", ["#1C2244", "#2E3A6A", "#56558C", "#A0709A"],
                           ["#252B4C", "#333A60", "#454B78", "#5E5E8E"],
                           ["#141831", "#22284A", "#3A3A6A", "#6A5890", "#B08AB0"], "#11142A", "#1B2040"),
}
COMMON = dict(base=BASE, styles={"Regular": {}}, palettes=PALETTES, sample=SAMPLE,
              designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou")

FAMILY = Family(
    name="Haystack Initials",
    description="Every capital stands in a field like a stack of hay, with a band of sky behind it and its "
                "shadow on the ground. Four palettes paint the same drawing at noon, at sunset, in snow and at dusk.",
    recipes=haystack.initials(latin().only()),
    **COMMON,
)

TEXT = Family(
    name="Haystack",
    description="The same letters without the field: short, broken touches of paint, lit from the upper left.",
    recipes=haystack.painted(latin().only()),
    **COMMON,
)

DIRECTIONS = [FAMILY, TEXT]
