"""Last Bell: chunky marker letters made in four rounds of feedback, and a color font with snow on them.

See BRIEF.md for the rounds.
"""

from whateverfont import Axis, Family, latin
from whateverfont.presets import preset

import snow

SAMPLE = "No school till January"
COMMON = dict(designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou", sample=SAMPLE)

# Round 1: a polite rounded sans.
FIRST = preset("rounded", weight=90, a_story=1, xh=505, counter=292, cut="horizontal")

# Round 2: "Chunkier. Like marker letters on a classroom door."
# Round 3: "The tails on g and y hang too low."
CHUNKY = dict(weight=132, cap_weight=1.05, contrast=0.95, superness=0.3, xh=540, counter=300, width=1.04,
              join=0.84, spacing=1.04, apex=0.9)
BASE = FIRST.but(**CHUNKY, desc=-150)

FAMILY = Family(
    name="Last Bell",
    description="Chunky marker letters with short tails, like a poster on a classroom door in December.",
    base=BASE,
    axes=[Axis("wght", "Weight", 400, 700, 700, {400: {"weight": 92, "counter": 292, "spacing": 1.0}})],
    styles={"Regular": {"wght": 400}, "Bold": {}},
    **COMMON)

# Round 4: "Now put snow on it."
SNOW = Family(
    name="Last Bell Snow",
    description="The same letters after a night of snow: a color font with the snow as its own layer.",
    base=BASE, recipes=snow.capped(latin()), styles={"Regular": {}},
    palettes={
        "Mitten": {"letter": "#D5402B", "snow": "#FFFFFF"},
        "Pine": {"letter": "#1F6B4A", "snow": "#FFFFFF"},
        "Cocoa": {"letter": "#6B3F2A", "snow": "#FFF8EC"},
        "Midnight": {"letter": "#F2C14E", "snow": "#FFFFFF"},
    },
    **COMMON)

# Rounds one to three as one variable font: Chunk runs from the first take to the marker letters, and
# Tail shortens the descenders. The demo of the four rounds on the project site moves along these axes.
ROUNDS = Family(
    name="Last Bell Rounds",
    description="The first three rounds as one font: drag Chunk from the first take to the marker letters, "
                "and Tail to pull up the descenders.",
    base=FIRST,
    axes=[Axis("CHNK", "Chunk", 0, 0, 100, {100: CHUNKY}),
          Axis("TAIL", "Tail", 0, 0, 100, {100: {"desc": -150}})],
    styles={"Regular": {}},
    **COMMON)

DIRECTIONS = [FAMILY, SNOW, ROUNDS]
