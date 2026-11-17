"""Greenbar: the print of a 9-pin dot-matrix printer on fan-fold paper, about 1985."""

from whateverfont import Axis, Family, effects, mono
from whateverfont.presets import preset
from matrix import matrix, screen

SAMPLE = "INVOICE 004417  12/03/85  QTY 3  RIBBON CART.  $14.85  TOTAL DUE $44.55"

# The letters under the dots: a plain monoline mono. A character without a drawing below is traced
# from their skeletons, so the numbers set what the head traces. The heights are where the dots
# end up (x-height of five pins, capitals of seven, descenders of two), so the font reports them.
BASE = preset("mono", weight=50, contrast=1.0, roundness=0.0, superness=0.30, xh=446, cap=646, asc=746,
              desc=-246, overshoot=0.0, counter=300, aperture=0.45, a_story=2, apex=0.4, join=1.0)

# The character ROM: each character as the head prints it, nine pin rows from the top of the
# capitals (row 6) to the bottom of the descenders (row -2). "#" fires a pin. Capitals are seven
# rows, lowercase five with two above for ascenders and two below for descenders, as on a 9-pin
# printer. A row of six dots starts at the edge of the cell, so that rows of _ and of the em dash
# join up.
BITMAPS = {
    # capitals
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "###.. #..#. #...# #...# #...# #..#. ###..",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .####",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# #...# ##..# #.#.# #..## #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    # lowercase
    "a": "..... ..... .###. ....# .#### #...# .####",
    "b": "#.... #.... #.##. ##..# #...# #...# ####.",
    "c": "..... ..... .###. #.... #.... #...# .###.",
    "d": "....# ....# .##.# #..## #...# #...# .####",
    "e": "..... ..... .###. #...# ##### #.... .###.",
    "f": "..##. .#..# .#... ###.. .#... .#... .#...",
    "g": "..... ..... .#### #...# #...# #...# .#### ....# .###.",
    "h": "#.... #.... #.##. ##..# #...# #...# #...#",
    "i": "..#.. ..... .##.. ..#.. ..#.. ..#.. .###.",
    "j": "...#. ..... ..##. ...#. ...#. ...#. ...#. #..#. .##..",
    "k": "#.... #.... #..#. #.#.. ##... #.#.. #..#.",
    "l": ".##.. ..#.. ..#.. ..#.. ..#.. ..#.. ...##",
    "m": "..... ..... ##.#. #.#.# #.#.# #.#.# #.#.#",
    "n": "..... ..... #.##. ##..# #...# #...# #...#",
    "o": "..... ..... .###. #...# #...# #...# .###.",
    "p": "..... ..... ####. #...# #...# #...# ####. #.... #....",
    "q": "..... ..... .#### #...# #...# #...# .#### ....# ....#",
    "r": "..... ..... #.##. ##..# #.... #.... #....",
    "s": "..... ..... .#### #.... .###. ....# ####.",
    "t": ".#... .#... ####. .#... .#... .#..# ..##.",
    "u": "..... ..... #...# #...# #...# #..## .##.#",
    "v": "..... ..... #...# #...# #...# .#.#. ..#..",
    "w": "..... ..... #...# #...# #.#.# #.#.# .#.#.",
    "x": "..... ..... #...# .#.#. ..#.. .#.#. #...#",
    "y": "..... ..... #...# #...# #...# #...# .#### ....# .###.",
    "z": "..... ..... ##### ...#. ..#.. .#... #####",
    # figures: a slashed zero, so a 0 on an invoice cannot be read as an O
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. #.#.. ..#.. ..#.. ..#.. #####",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "##### ...#. ..#.. ...#. ....# #...# .###.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": "..##. .#... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ...#. .##..",
    # punctuation: the dots are two pins square, so a period survives a worn ribbon
    ".": "..... ..... ..... ..... ..... .##.. .##..",
    ",": "..... ..... ..... ..... ..... .##.. .##.. ..#.. .#...",
    ":": "..... ..... .##.. .##.. ..... .##.. .##..",
    ";": "..... ..... .##.. .##.. ..... .##.. .##.. ..#.. .#...",
    "!": "..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
    "'": "..#.. ..#.. ..#..",
    '"': ".#.#. .#.#. .#.#.",
    "`": ".#... ..#..",
    "‘": "..#.. .#... .##..",
    "’": "..##. ...#. ..#..",
    "“": ".#..# #..#. ##.##",
    "”": "##.## .#..# #..#.",
    # dashes: the hyphen is three pins, the en dash five, the em dash runs into the next cell
    "-": "..... ..... ..... .###.",
    "–": "..... ..... ..... #####",
    "—": "..... ..... ..... ######",
    "_": "..... ..... ..... ..... ..... ..... ..... ######",
    # brackets: as tall as the line, so they hold what is between them
    "(": "...#. ..#.. .#... .#... .#... .#... .#... ..#.. ...#.",
    ")": ".#... ..#.. ...#. ...#. ...#. ...#. ...#. ..#.. .#...",
    "[": ".###. .#... .#... .#... .#... .#... .#... .#... .###.",
    "]": ".###. ...#. ...#. ...#. ...#. ...#. ...#. ...#. .###.",
    "{": "...## ..#.. ..#.. ..#.. ##... ..#.. ..#.. ..#.. ...##",
    "}": "##... ..#.. ..#.. ..#.. ...## ..#.. ..#.. ..#.. ##...",
    "|": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "/": "....# ...#. ...#. ..#.. .#... .#... #....",
    "\\": "#.... .#... .#... ..#.. ...#. ...#. ....#",
    # operators sit on the middle row, so -> and => are level
    "<": "..... ...## .##.. #.... .##.. ...##",
    ">": "..... ##... ..##. ....# ..##. ##...",
    "+": "..... ..#.. ..#.. ##### ..#.. ..#..",
    "=": "..... ..... ##### ..... #####",
    "*": "..... ..#.. #.#.# .###. #.#.# ..#..",
    "~": "..... ..... .#... #.#.# ...#.",
    "^": "..#.. .#.#. #...#",
    # signs
    "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    "@": ".###. #...# #.### #.#.# #.### #.... .###.",
    "#": ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
    "%": "##... ##..# ...#. ..#.. .#... #..## ...##",
    "$": "..#.. .#### #.#.. .###. ..#.# ####. ..#..",
    "£": "..##. .#..# .#... ###.. .#... .#..# #.##.",
    "¢": "..... ..#.. .###. #.#.. #.#.. .###. ..#..",
    "¥": "#...# .#.#. ##### ..#.. ##### ..#.. ..#..",
    "°": ".##.. #..#. .##..",
    "±": "..... ..#.. ..#.. ##### ..#.. ..... #####",
    "×": "..... #...# .#.#. ..#.. .#.#. #...#",
    "÷": "..... ..#.. ..... ##### ..... ..#..",
}

RECIPES = mono().only("".join(BITMAPS))

FAMILY = Family(
    name="Greenbar",
    description="Dot-matrix print on a strict grid of nine pins: invoices, boarding passes, fan-fold listings.",
    base=BASE,
    recipes=matrix(RECIPES, BITMAPS),
    # Bold is the printer's emphasized mode: each dot struck twice, half a step apart (matrix.py).
    # The dots are cut after drawing, so there is no variable font, only these two styles.
    axes=[Axis("wght", "Weight", 400, 400, 700, {700: {"weight": 100}})],
    styles={"Regular": {}, "Bold": {"wght": 700}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

# The same character ROM on the terminal that sent the job to the printer: a phosphor screen.
# On a screen the lit pixels of one scanline fuse into a bar, dark lines run between the
# scanlines, and the phosphor glows. The palettes are the three phosphors terminals shipped with:
# P1 green, P3 amber and P4 white, each a bright core inside rings of its own color, for a dark ground.
def phosphor(glow: str, core: str) -> dict:
    """Rings of ``glow`` that get more solid toward the beam, and a beam of ``core``."""
    colors = effects.glow_palette(glow, core)
    colors["beam"] = colors.pop("tube")
    return colors


HALATION = Family(
    name="Halation",
    description="The Greenbar character set on a phosphor screen: scanlines of light with a glow, in green, amber or white.",
    base=BASE,
    recipes=screen(RECIPES, BITMAPS, glow=70.0),
    styles={"Regular": {}},
    # Paper is for a light page, where a pale beam would vanish: the beam itself is dark green.
    palettes={"Green": phosphor("#33FF66", "#C9FFD6"), "Amber": phosphor("#FFAA00", "#FFE2A8"),
              "White": phosphor("#9DB8FF", "#F4F7FF"), "Paper": phosphor("#2FBF5A", "#0B5E26")},
    # the glow reaches 70 units past the lowest pin; give the line room for it
    descent=-336,
    sample="READY.  RUN LEDGER.BAS  BALANCE FWD $1,204.55  OK",
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

DIRECTIONS = [FAMILY, HALATION]
