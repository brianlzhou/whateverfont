"""Starry: letters painted in short, loaded brush marks, and capitals set in a turning night sky."""

from whateverfont import Family, latin
from whateverfont.presets import preset

import starry

SAMPLE = "The Night Is Full Of Stars"

# A heavy, soft sans: the paint needs wide strokes to lie in, and round ends suit a brush.
BASE = preset("humanist", weight=148, contrast=0.90, roundness=0.75, xh=520, counter=300, aperture=0.75,
              classical=0.45, apex=0.5, join=0.92, spacing=1.0, stress=0)

NIGHT = starry.night("#101A38", ["#16264F", "#1F3B7A", "#2E5CA8", "#4F8BCB", "#A3C8E8", "#F3E7A6"],
                     ["#D98E2B", "#EFB43E", "#F7D568", "#FFF5C6"])
DAWN = starry.night("#3A2A4A", ["#4B3565", "#7A4B86", "#C06C8E", "#EE9A7B", "#F9C99A", "#FFF0CF"],
                    ["#3B2A5A", "#5A3F86", "#8A6BB8", "#D9C6F2"], star="#FFF6DD", glow="#F7B99A")
INK = starry.night("#F4EFE4", ["#E6DFD0", "#CFC6B4", "#A99F8C", "#7C7363", "#4A443A", "#1F1C18"],
                   ["#1F1C18", "#35302A", "#5A5248", "#8A8073"], star="#1F1C18", glow="#7C7363")
PALETTES = {"Night": NIGHT, "Dawn": DAWN, "Ink": INK}
COMMON = dict(base=BASE, styles={"Regular": {}}, palettes=PALETTES, sample=SAMPLE,
              designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou")

FAMILY = Family(
    name="Starry Initials",
    description="Every capital is a gold letter in a square of turning sky, with rings of light around it "
                "and stars in the corners. The rest of the text is painted in the blues of the sky.",
    recipes=starry.initials(latin().only()),
    **COMMON,
)

TEXT = Family(
    name="Starry",
    description="The same letters without the sky: currents of blue paint that follow each stroke, with "
                "sparks of yellow down the middle.",
    recipes=starry.painted(latin().only()),
    **COMMON,
)

DIRECTIONS = [FAMILY, TEXT]
