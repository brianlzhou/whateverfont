"""Leafpile: letters made of fallen leaves, for a harvest fair poster. See BRIEF.md.

The `fallen` effect (leaves.py, next to this file) covers each heavy, round letter with overlapping
maple, oak, birch and ginkgo leaves cut to its outline; a few leaves on top stick out past the edge.
`Leafpile Plain` is the same letters in one color.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from leaves import fallen, palette

SAMPLE = "Harvest Fair"
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE,
              figures="proportional",      # a poster sets "2026" and "4 pm" in a line, not in a column
              ascent=960)                  # room for the dots of heavy capitals (Ä Ż), which reach 946

BASE = preset("rounded", weight=155, counter=310, width=1.06, xh=530, spacing=1.08)

PALETTES = {
    "Maple": palette("#5A1A10", ["#9E2318", "#C8361E", "#DE5A22", "#EC8A2B", "#F2B23A"], "#3A0E0866"),
    "Ginkgo": palette("#6B4A0E", ["#C99A1C", "#DDB22A", "#EAC83A", "#F3DA5A", "#F8E98E"], "#6B4A0E70"),
    "Oak": palette("#2E1A0E", ["#5E3219", "#86431F", "#AE5A26", "#C77B3A", "#DDA65E"], "#1E100866"),
    "Late October": palette("#4A2A1A", ["#B3361F", "#D9562A", "#EE8A2E", "#F5B23E", "#F9D46A"], "#1A141066"),
}

FAMILY = Family(
    name="Leafpile",
    description="Round, heavy letters heaped with fallen maple, oak, birch and ginkgo leaves.",
    base=BASE,
    recipes=fallen(latin(), poke=0.38, whole=0.3),
    styles={"Regular": {}},
    palettes=PALETTES,
    **COMMON)

PLAIN = Family(
    name="Leafpile Plain",
    description="The same round, heavy letters in one color, for the words under a Leafpile heading.",
    base=BASE,
    styles={"Regular": {}},
    **COMMON)

DIRECTIONS = [FAMILY, PLAIN]
