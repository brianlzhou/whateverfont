"""Doorstep: a friendly slab serif for long reading, with a bold for headlines."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "News from the corner bakery"

# The humanist preset gives open c, e, s and a, a slight pen angle and capitals with Roman widths. Slabs
# 48 units long and as thick as the hairlines make it a slab serif; a little roundness softens the corners
# without making round ends. Low contrast, a tall x-height and wide round letters keep long text even.
BASE = preset("humanist", serif=48, serif_weight=1.0, weight=86, contrast=0.85, stress=6, aperture=0.7,
              roundness=0.18, classical=0.5, xh=515, counter=284, round_width=1.12, cap_width=1.04,
              spacing=1.08, word_space=1.1)

FAMILY = Family(
    name="Doorstep",
    description="A slab serif for newsletters and long reading: square slabs with softened corners, open "
                "letters, and a bold for headlines.",
    base=BASE,
    axes=[
        # The light gets more room between letters, so its slabs do not crowd. The bold gets shorter,
        # heavier slabs, wider counters, more open c, e and s and longer arms on f, t and r.
        Axis("wght", "Weight", 300, 400, 700, {
            300: {"weight": 58, "spacing": 1.14},
            700: {"weight": 130, "serif": 44, "serif_weight": 1.15, "counter": 292, "arm": 1.2, "aperture": 0.85,
                  "spacing": 1.02},
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
