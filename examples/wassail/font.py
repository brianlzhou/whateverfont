"""Wassail: a Christmas book face with illuminated capitals."""

from whateverfont import Family, latin
from whateverfont.ornament import CHRISTMAS, FROST, ULTRAMARINE, illuminate
from whateverfont.presets import preset

SAMPLE = "Hark the Herald Angels Sing"

# Written with a broad pen held at about 32 degrees, like a round book hand.
BASE = preset("broadnib", stress=32, contrast=0.34, weight=102, xh=455, asc=760, desc=-225, flare=0.20,
              a_story=1, aperture=1.0, counter=258, apex=0.1, spacing=0.96)

FAMILY = Family(
    name="Wassail",
    description="A round book hand written with a broad pen. Use it for the running text.",
    base=BASE,
    styles={"Regular": {}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

INITIALS = Family(
    name="Wassail Initials",
    description="The same hand, with every capital set on a framed field with holly, berries and gold. "
                "A color font with three palettes.",
    base=BASE,
    recipes=illuminate(latin()),
    styles={"Regular": {}},
    palettes={"Christmas": CHRISTMAS, "Ultramarine": ULTRAMARINE, "Frost": FROST},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

DIRECTIONS = [INITIALS, FAMILY]
