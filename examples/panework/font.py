"""Panework: a color display family in which every letter is a grid painting of the De Stijl kind.

Thick lines divide each letter into unequal rectangles, most of them white and one or two red, yellow
or blue. The effect is `composition` in planes.py, next to this file. Panework Boogie divides the
letters more finely and breaks its lines with small squares of color.
"""

from whateverfont import Family, latin
from whateverfont.presets import preset

from planes import composition, palette

SAMPLE = "Composition in Red"

# Heavy, with squared rounds and flat cuts, so that a stroke is wide enough to hold a rectangle and a
# round letter is mostly straight lines. The grotesk stays clean at this weight; the technical and
# geometric presets put kinks in S, s, e, 5 and 9.
BASE = preset("grotesk", weight=170, superness=0.85, counter=330, width=1.12, cut="horizontal", spacing=1.05)

#                        lines      white      tint       red        yellow     blue
PALETTES = {
    # black lines, white planes, pure red, yellow and blue
    "Primary": palette("#141414", "#FBFAF5", "#F0EEE7", "#D7261E", "#F5C40E", "#1D4E9E"),
    # softer lines, light grays among the whites, earthier colors: the quieter grids of the early years
    "Stone": palette("#2A2A2A", "#F4F3EF", "#D6D4CE", "#B4372B", "#E0B83A", "#3A5A8C"),
    # turned around for a dark page: light lines, dark planes, bright colors
    "Night": palette("#F2EEE3", "#252A33", "#323844", "#E8432F", "#F7CB2D", "#4A7BE0"),
}

BOOGIE_PALETTES = {
    # yellow lines broken by red, blue and gray squares, on an off-white plane
    "Broadway": palette("#F2C511", "#F2EFE6", "#E6E3DA", "#CC2A1F", "#F2C511", "#2148A6", gray="#BDBAB3",
                        squares=("#CC2A1F", "#2148A6", "#BDBAB3")),
    # black lines broken by red, blue and yellow squares: the same picture for a white page
    "Midtown": palette("#151515", "#FBFAF5", "#F0EEE7", "#D7261E", "#F5C40E", "#1D4E9E", gray="#A9A7A1",
                       squares=("#D7261E", "#1D4E9E", "#F5C40E")),
}

# The ground that each palette is drawn for, and the color of plain text beside it: (ground, ink).
# The engine picks a dark ground by itself only for Night, so a page that shows these fonts should use
# this table. Every palette also reads on the other kind of page: see BRIEF.md.
GROUNDS = {
    "Panework": {"Primary": ("#F3F1EC", "#141414"), "Stone": ("#FFFFFF", "#2A2A2A"),
                 "Night": ("#101217", "#F2EEE3")},
    "Panework Boogie": {"Broadway": ("#1B1C21", "#F2C511"), "Midtown": ("#F3F1EC", "#151515")},
}

FAMILY = Family(
    name="Panework",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Heavy squared letters divided by thick lines into white rectangles and a few of red, yellow and blue.",
    base=BASE,
    recipes=composition(latin()),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=975,          # room for the marks of heavy capitals (Ö Ǘ)
    sample=SAMPLE,
)

BOOGIE = Family(
    name="Panework Boogie",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="The same letters on a finer grid, with lines broken by small squares and blocks of color.",
    base=BASE,
    recipes=composition(latin(), line=28.0, frame=30.0, room=46.0, per_split=34000.0, most=10, fields=(2, 2, 3),
                        short=0.12, tint=0.0, hues=("red", "red", "red", "blue", "blue", "gray", "gray"),
                        squares=(2.0, 4.2), frame_squares=True, inner=0.75, seed=4),
    styles={"Regular": {}},
    palettes=BOOGIE_PALETTES,
    ascent=975,          # room for the marks of heavy capitals (Ö Ǘ)
    sample="Broadway at Night",
)

DIRECTIONS = [FAMILY, BOOGIE]
