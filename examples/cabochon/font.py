"""Cabochon: a color display family in which every letter is cut from a polished stone.

The person asked for a font that looks cut from polished gemstones, and showed a jade letter on a dark
red cloth. The effects in gem.py, next to this file, build each letter from flat color layers: the stone
with its cloudy patches, a lit and a shaded bevel, a bright line and a lamp's reflection (Cabochon), or
facets that meet in a ridge (Cabochon Rose). Each of the six palettes is one stone; gem.GROUNDS names the
cloth each one is shown on.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from gem import PALETTES, faceted, polished

SAMPLE = "Jade & Ruby"
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE,
              styles={"Regular": {}}, palettes=PALETTES)

# 1. Polished: a bracketed book serif with a raised, glossy bevel, like the jade letter in the picture.
FAMILY = Family(
    name="Cabochon",
    description="A bracketed book serif cut from polished stone, with a lit bevel and a lamp's reflection.",
    base=preset("flare", weight=120, contrast=0.45, serif=30, serif_weight=0.95, classical=1, xh=480, stress=8,
                spacing=1.06),
    recipes=polished(latin()),
    **COMMON)

# 2. Faceted: incised letters whose strokes are cut into facets that meet in a ridge down the middle.
ROSE = Family(
    name="Cabochon Rose",
    description="Incised capitals and a flared lowercase, each stroke cut into facets that meet in a ridge.",
    base=preset("glyphic", weight=138, contrast=0.72, classical=1, xh=490, spacing=1.06),
    recipes=faceted(latin()),
    **COMMON)

DIRECTIONS = [FAMILY, ROSE]
