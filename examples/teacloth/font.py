"""Teacloth: letters in cross stitch on one grid, like the alphabet on a sampler that hangs in a kitchen."""

from whateverfont import Family, latin
from whateverfont.presets import preset
from whateverfont.recipes import upper

import stitch

CELL = 70.0          # one square of the cloth, in font units

# A heavy grotesk whose heights are whole rows: x-height 7, capitals 10, ascenders 11, descenders 3.
# A stem is 140 units, two squares; a horizontal stroke is about 55 units and is settled to one row.
BASE = preset("grotesk", weight=140, cap_weight=1.0, contrast=0.45, apex=0.25, xh=7 * CELL, cap=10 * CELL,
              asc=11 * CELL, desc=-3 * CELL, overshoot=0, counter=300, superness=0.5, aperture=0.2,
              word_space=0.8, kerning=0)


def letters():
    """The engine's letters, with an M whose V stops at a third of the height, so its four strokes do
    not run together into a block of stitches."""
    r = latin()

    @r.add("M", "M", case="upper")
    def M(g):
        upper.em(g, vertex=0.34, thin=0.80)

    return r


# Charts by hand, for the glyphs that the rules cannot chart well: (top row, rows from the top).
# Row 0 sits on the baseline; the x-height is 7 rows, the capitals 10, the descenders 3.
PAREN = ["..##", ".##.", ".##."] + ["##.."] * 7 + [".##.", ".##.", "..##"]
BRACKET = ["####"] + ["##.."] * 11 + ["####"]
BRACE = ["..###"] + [".##.."] * 5 + ["###.."] + [".##.."] * 5 + ["..###"]


def mirror(rows):
    return [r[::-1] for r in rows]


HAND = {
    # a two-story a with a flat bowl: the rules gave its bowl a diagonal top that read as ø
    "a": (6, [".#####.",
              ".....##",
              ".....##",
              ".######",
              "##...##",
              "##...##",
              ".######"]),
    # I with bars and l with a foot, so that I, l, 1 and | differ (the Greek and Cyrillic I follow I)
    "I": (9, ["####"] + [".##."] * 8 + ["####"]),
    "l": (10, ["##.."] * 10 + [".###"]),
    "lslash": (10, [".##..", ".##..", ".##.#", ".###.", ".##..", "###..", ".##..", ".##..", ".##..", ".##..",
                    "..###"]),
    "ldot": (10, ["##...."] * 5 + ["##.##.", "##.##."] + ["##...."] * 3 + [".###.."]),
    # diagonal letters as even, mirrored staircases two stitches wide; the rules left uneven steps
    "A": (9, ["....##....",
              "...####...",
              "...####...",
              "..##..##..",
              "..##..##..",
              ".##....##.",
              ".########.",
              ".##....##.",
              "##......##",
              "##......##"]),
    "V": (9, ["##......##",
              "##......##",
              ".##....##.",
              ".##....##.",
              "..##..##..",
              "..##..##..",
              "...####...",
              "...####...",
              "....##....",
              "....##...."]),
    "X": (9, ["##......##",
              ".##....##.",
              ".##....##.",
              "..##..##..",
              "...####...",
              "...####...",
              "..##..##..",
              ".##....##.",
              ".##....##.",
              "##......##"]),
    "K": (9, ["##....##",
              "##...##.",
              "##..##..",
              "##.##...",
              "####....",
              "####....",
              "##.##...",
              "##..##..",
              "##...##.",
              "##....##"]),
    "k": (10, ["##....."] * 4 + ["##...##",
                                 "##..##.",
                                 "##.##..",
                                 "####...",
                                 "##.##..",
                                 "##..##.",
                                 "##...##"]),
    "v": (6, ["##....##",
              "##....##",
              ".##..##.",
              ".##..##.",
              "..####..",
              "..####..",
              "...##..."]),
    "x": (6, ["##...##",
              ".##.##.",
              "..###..",
              "..###..",
              "..###..",
              ".##.##.",
              "##...##"]),
    # the w and the W: wide letters whose four strokes crowd each other on the grid
    "w": (6, ["##.......##",
              "##.......##",
              ".##..#..##.",
              ".##.###.##.",
              ".####.####.",
              "..##...##..",
              "..##...##.."]),
    "W": (9, ["##..........##",
              "##..........##",
              "##..........##",
              ".##...##...##.",
              ".##..####..##.",
              ".##..#..#..##.",
              "..####..####..",
              "..###....###..",
              "..##......##..",
              "..##......##.."]),
    # brackets: the engine's curves are too shallow to show on the grid
    "parenleft": (10, PAREN), "parenright": (10, mirror(PAREN)),
    "bracketleft": (10, BRACKET), "bracketright": (10, mirror(BRACKET)),
    "braceleft": (10, BRACE), "braceright": (10, mirror(BRACE)),
    # quotes and commas: a square dot with a one-stitch tail
    "quoteright": (10, ["##", "##", ".#", "#."]),
    "quoteleft": (10, [".#", "#.", "##", "##"]),
    "quotedblright": (10, ["##.##", "##.##", ".#..#", "#..#."]),
    "quotedblleft": (10, [".#..#", "#..#.", "##.##", "##.##"]),
    "quotesinglbase": (1, ["##", "##", ".#", "#."]),
    "quotedblbase": (1, ["##.##", "##.##", ".#..#", "#..#."]),
    "comma": (1, ["##", "##", ".#", "#."]),
    "semicolon": (6, ["##", "##", "..", "..", "..", "##", "##", ".#", "#."]),
    "guilsinglleft": (5, ["..#", ".#.", "#..", ".#.", "..#"]),
    "guilsinglright": (5, ["#..", ".#.", "..#", ".#.", "#.."]),
    "guillemotleft": (5, ["..#..#", ".#..#.", "#..#..", ".#..#.", "..#..#"]),
    "guillemotright": (5, ["#..#..", ".#..#.", "..#..#", ".#..#.", "#..#.."]),
    # signs on the axis of the minus (row 5)
    "plus": (7, ["..#..", "..#..", "#####", "..#..", "..#.."]),
    "equal": (6, ["#####", ".....", "#####"]),
    "less": (7, ["....##", "..##..", "##....", "..##..", "....##"]),
    "greater": (7, ["##....", "..##..", "....##", "..##..", "##...."]),
    "multiply": (7, ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"]),
    "divide": (7, ["..#..", ".....", "#####", ".....", "..#.."]),
    "plusminus": (8, ["..#..", "..#..", "#####", "..#..", "..#..", ".....", "#####"]),
    "notequal": (8, ["....#", "...#.", "#####", "..#..", "#####", ".#...", "#...."]),
    "approxequal": (7, [".##..#", "#..##.", "......", ".##..#", "#..##."]),
    "lessequal": (8, ["....##", "..##..", "##....", "..##..", "....##", "......", "######"]),
    "greaterequal": (8, ["##....", "..##..", "....##", "..##..", "##....", "......", "######"]),
    "infinity": (7, [".##...##.", "#..#.#..#", "#...#...#", "#..#.#..#", ".##...##."]),
    "asterisk": (10, ["..#..", "#.#.#", ".###.", "#.#.#", "..#.."]),
    "asciicircum": (9, ["..#..", ".#.#.", "#...#"]),
    "asciitilde": (6, [".##..#", "#..##."]),
    "degree": (10, [".##.", "#..#", "#..#", ".##."]),
    # the dollar: the S of the figures, narrower, with a one-stitch bar through it
    "dollar": (9, ["...#...",
                   ".#####.",
                   "##.#...",
                   "##.#...",
                   ".####..",
                   "..####.",
                   "...#.##",
                   "...#.##",
                   ".#####.",
                   "...#..."]),
    "numbersign": (8, ["...#..#.", "...#..#.", "########", "..#..#..", "..#..#..", "########", ".#..#...",
                       ".#..#..."]),
}

# Each palette is one thread on one cloth. The top thread is a little lighter than the under thread,
# as the thread that lies on top catches more light. The cloth is the page: GROUNDS. The frames of
# Teacloth Initials take a border, petals, a heart and leaves from the same palette.
GREEN = ("#3F6B2E", "#5A8A3F")
GOLD = ("#A87515", "#D29E32")
ROSE = ("#A8394E", "#CB5A6E")
PALETTES = {
    # turkey red on natural linen: the showpiece
    "Linen": stitch.palette("#9A1D28", "#C7363C", border=GREEN, petal=("#9A1D28", "#C7363C"), heart=GOLD,
                            leaf=GREEN),
    # dark blue on white cotton, all in blue
    "Blue": stitch.palette("#1D3A82", "#3159AA", border=("#1D3A82", "#3159AA"), petal=("#4A6FB8", "#6D8FCC"),
                           heart=("#1D3A82", "#3159AA"), leaf=("#4A6FB8", "#6D8FCC")),
    # three bands, from the baseline up: moss green for the lower half of the x-height, rose for its
    # upper half, gold for the capitals and ascenders above it (and for the descenders)
    "Garden": stitch.banded([GREEN, ROSE, GOLD], [3, 4, 3], border=("#2C4E86", "#4670AE"), petal=ROSE,
                            heart=GOLD, leaf=GREEN),
    # white on dark cloth, with pale flowers
    "Night": stitch.palette("#D9D2C2", "#FBF8F1", border=("#D9D2C2", "#FBF8F1"), petal=("#D98A9A", "#F0AFBC"),
                            heart=("#E0B550", "#F2CF74"), leaf=("#86B07A", "#A6CC98")),
}
GROUNDS = {"Linen": "#E6DCC6", "Blue": "#F8F7F2", "Garden": "#EDE5D2", "Night": "#232B38"}

COMMON = dict(base=BASE, styles={"Regular": {}}, palettes=PALETTES, figures="proportional",
              designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou")

FAMILY = Family(
    name="Teacloth",
    description="Letters in cross stitch on one grid of cloth, like the alphabet on a kitchen sampler.",
    recipes=stitch.stitched(letters(), cell=CELL, hand=HAND),
    ascent=1050,         # two marks on a capital reach row 14 (stitch.TOP_ROW)
    sample="Home Sweet Home",
    **COMMON,
)

CAPITALS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

INITIALS = Family(
    name="Teacloth Initials",
    description="Every capital in a stitched frame with a flower at each corner. The rest is Teacloth.",
    recipes=stitch.stitched(letters(), cell=CELL, hand=HAND, framed=CAPITALS),
    ascent=1050,
    descent=-290,        # the flowers under a frame reach row -4
    sample="Home Sweet Home",
    **COMMON,
)

DIRECTIONS = [FAMILY, INITIALS]
