"""Dayshift: a plain sans for the interface of an app."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "Your changes are saved"

# The proportions of an interface sans: a tall x-height, a narrow n next to a wide o, wide capitals, and
# loose spacing so that 13-pixel text stays even. cut="flat": the round letters end in level cuts, and the
# arm of r and the hooks of f, t and j end upright.
BASE = preset("grotesk", xh=540, cap=720, asc=752, desc=-205, weight=86, cap_weight=1.05, contrast=0.9,
              counter=264, round_width=1.17, cap_width=1.14, superness=0.14, aperture=0.2, cut="flat", spacing=1.22,
              word_space=1.22, apex=0.9, join=0.82, round_weight=1.02, overshoot=10)

FAMILY = Family(
    name="Dayshift",
    description="A plain sans for the interface of an app: a tall x-height, wide round letters, loose spacing "
                "and five weights.",
    base=BASE,
    axes=[
        # The bold opens c, e and s and lengthens the arms of f, t and r, so they stay clear when heavy.
        Axis("wght", "Weight", 300, 400, 700, {
            300: {"weight": 60, "counter": 270},
            700: {"weight": 128, "counter": 264, "contrast": 0.99, "spacing": 1.12, "arm": 1.2, "aperture": 0.5},
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
