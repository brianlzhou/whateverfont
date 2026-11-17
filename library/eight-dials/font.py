"""Eight Dials: one family with a slider for every decision.

The "How it works" part of the project site sets a line in this font with a slider for each axis.
"""

from whateverfont import Axis, Family
from whateverfont.presets import preset

BASE = preset("humanist", weight=84, contrast=0.78, xh=500, counter=285, aperture=0.8, classical=0.7, stress=0,
              flare=0.0, roundness=0.0, apex=0.55, spacing=1.0)

AXES = [
    Axis("wght", "Weight", 200, 400, 800, {200: {"weight": 40}, 800: {"weight": 158}}),
    Axis("wdth", "Width", 60, 100, 130, {60: {"width": 0.60}, 130: {"width": 1.30}}),
    Axis("slnt", "Slant", -14, 0, 0, {-14: {"slant": 14}}),
    Axis("CNTR", "Contrast", 0, 60, 100, {0: {"contrast": 1.0}, 100: {"contrast": 0.24}}),
    Axis("FLAR", "Flare", 0, 0, 100, {100: {"flare": 0.75, "flare_len": 170}}),
    Axis("ROND", "Roundness", 0, 0, 100, {100: {"roundness": 1.0}}),
    Axis("SPAC", "Spacing", 0, 40, 100, {0: {"spacing": 0.62}, 100: {"spacing": 1.9}}),
    Axis("XHGT", "x-height", 0, 50, 100, {0: {"xh": 420}, 100: {"xh": 590}}),
]

FAMILY = Family(
    name="Eight Dials",
    description="One family with a slider for every decision: weight, width, slant, contrast, flare, "
                "roundness, spacing and x-height.",
    base=BASE,
    axes=AXES,
    styles={"Regular": {}},
    sample="Every letter is a decision",
    designer="Brian Zhou",
    copyright="Copyright 2026 Brian Zhou",
)
