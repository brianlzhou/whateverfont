"""Aviary: a picture font of birds. Type a letter, get a bird.

A to Z are 26 birds facing right. Lowercase letters are the same birds facing left.
"""

from whateverfont import Family, Params

import aviary
from birds import BIRDS, EXTRAS, PALETTES

SAMPLE = "FLOCK"
BASE = Params(kerning=0)
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE,
              ascent=960, descent=-80)

COLOR = Family(
    name="Aviary Color",
    description="26 birds cut from colored paper, in four palettes: Field Guide, Letterpress, Risograph, Chalk.",
    base=BASE, recipes=aviary.bird_recipes(BIRDS, EXTRAS, "color"), styles={"Regular": {}}, palettes=PALETTES,
    **COMMON)

AVIARY = Family(
    name="Aviary",
    description="The same birds in one color, with the eyes, the white marks and the feather lines cut out.",
    base=BASE, recipes=aviary.bird_recipes(BIRDS, EXTRAS, "solid"), styles={"Regular": {}}, **COMMON)

LINE = Family(
    name="Aviary Line",
    description="The same birds as outlines, a coloring book.",
    base=BASE, recipes=aviary.bird_recipes(BIRDS, EXTRAS, "line"), styles={"Regular": {}}, **COMMON)

FAMILY = COLOR
DIRECTIONS = [COLOR, AVIARY, LINE]
