"""Softboil: a soft, rounded sans that stays calm in a page of text."""

from whateverfont import Axis, Family
from whateverfont.presets import preset

SAMPLE = "Good morning. Breakfast is ready."

# Every stroke ends in a half circle (roundness 1). The proportions are those of an interface sans, so the
# round ends are the only soft thing about it: a tall x-height, even widths, loose spacing. cut="flat" ends
# the hooks of f, t, j and the arm of r level, with no curl.
BASE = preset("rounded", xh=536, cap=712, asc=750, weight=88, cap_weight=1.04, contrast=0.95, counter=268,
              round_width=1.14, cap_width=1.12, superness=0.2, aperture=0.4, spacing=1.2, word_space=1.18,
              cut="flat")

FAMILY = Family(
    name="Softboil",
    description="A rounded sans for a friendly app: every stroke ends in a half circle, and the letters keep "
                "the even widths of an interface font.",
    base=BASE,
    axes=[
        Axis("wght", "Weight", 300, 400, 700, {
            300: {"weight": 62, "counter": 272},
            700: {"weight": 128, "counter": 266, "contrast": 1.0, "spacing": 1.1, "arm": 1.2, "aperture": 0.65},
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
