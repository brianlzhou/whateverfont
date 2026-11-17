"""Cutout: letters cut with scissors out of painted paper, for a children's museum sign and a festival poster."""

from whateverfont import Family, latin
from whateverfont.presets import preset

from cutpaper import add_leaves, close_one, painted_paper, paper_palette, roomy_dots, scissors

SAMPLE = "Children's Museum"

# Heavy, with little contrast: a cut shape has no pen. The stems swell toward their ends, as a leaf does, and
# that is also what the hand does when it turns the paper at the end of a cut. The single-story `a`, the round
# dots and the tall x-height are for children who are learning to read.
BASE = preset("flare", weight=180, counter=300, contrast=0.85, flare=0.42, a_story=1, xh=515, aperture=0.6,
              dot="round", spacing=0.9)

FAMILY = Family(
    name="Cutout",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="One color to color yourself: heavy letters cut with scissors, and leaves on * ^ ~ { }.",
    base=BASE,
    recipes=scissors(add_leaves(close_one(roomy_dots(latin())))),
    styles={"Regular": {}},
    ascent=1000, descent=-260,          # room for the accents on capitals, which the cut lifts and leans
    sample=SAMPLE,
)

COLOR = Family(
    name="Cutout Color",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Each letter cut from its own sheet of painted paper, in three palettes: Paper, Night, Lagoon.",
    base=BASE,
    recipes=painted_paper(add_leaves(close_one(latin()))),
    styles={"Regular": {}},
    ascent=1000, descent=-260,          # the same line as Cutout, so the two can be set one over the other
    palettes={
        #                       sheet0     sheet1     sheet2     sheet3     sheet4
        "Paper": paper_palette("#1F56B0", "#F0604A", "#1F9A5B", "#F4B312", "#1B1A1F"),
        "Night": paper_palette("#5B9BFF", "#FF7C66", "#4FCB82", "#FFD23F", "#FBF2DF"),
        "Lagoon": paper_palette("#1F56B0", "#12A39A", "#F0604A", "#2F8FE0", "#0E2A5C"),
    },
    sample=SAMPLE,
)

DIRECTIONS = [FAMILY, COLOR]
