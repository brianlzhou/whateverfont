"""Square pixels on one grid: the effect behind the font in this folder.

Every glyph is a set of whole pixels. A pixel is 125 units square, eight to the em, so at 8, 16, 24, 32
and 48 pixels a font pixel covers whole screen pixels and stays crisp. The rows are fixed: the baseline is
row 0, the x-height is five rows (0 to 4), capitals and ascenders are seven (0 to 6), descenders go down
two rows (-1 and -2), and marks sit above with one empty row between.

Vertical strokes are two pixels wide and horizontal strokes one pixel tall, as on an old television,
where a line one pixel wide blurred sideways and a line one scanline tall stayed sharp.

Where a glyph comes from, in this order:

1. ``DRAWINGS``: the character set as an 8-bit game kept it, each character a small drawing.
2. Lookalikes: a Greek or Cyrillic letter that looks like a Latin one uses its drawing (``SAME``).
3. Accented letters: the drawing of the base letter and the drawing of each mark, placed on the grid by
   rule (``compose``). Fractions, Ĳ and the like are drawings set side by side (``pack``).
4. Forms without a code point (``hyphen.case``, ``two.dnom``): built from another drawing by rule.
5. Anything else is sampled from the outline the engine draws (``sample``): the outline is laid on a
   grid of cells half a stem wide and one stroke tall, and each cell more than half inside becomes a
   pixel.

The pixels of a glyph are merged into rectangles before they become an outline (``rectangles``).
"""

from __future__ import annotations

import unicodedata

from whateverfont import effects
from whateverfont.geom import flatten_contour
from whateverfont.outline import rect, union

#: One pixel, in font units.
PX = 125
#: White after each glyph, in pixels.
GAP = 1
#: The word space, in pixels (with no gap after it).
SPACE = 4


# --------------------------------------------------------------------------------------------- sprites


class Sprite:
    """Pixels on the grid: ``cells`` is a set of (column, row); row 0 sits on the baseline. ``width`` is the
    drawn box in columns (it may hold empty columns). ``rsb`` is the white after it. ``center`` is where a
    mark goes, in half columns (6 is the middle of a box six wide)."""

    __slots__ = ("cells", "width", "rsb", "center")

    def __init__(self, cells, width, rsb=GAP, center=None):
        self.cells = frozenset(cells)
        self.width = width
        self.rsb = rsb
        self.center = width if center is None else center

    def moved(self, dx=0, dy=0) -> "Sprite":
        return Sprite({(c + dx, r + dy) for c, r in self.cells}, self.width + dx, self.rsb, self.center + 2 * dx)

    def plus(self, other: "Sprite", dx=0, dy=0) -> "Sprite":
        """This sprite with ``other`` drawn on top, moved by (dx, dy). The box grows to hold both."""
        cells = set(self.cells) | {(c + dx, r + dy) for c, r in other.cells}
        return Sprite(cells, max(self.width, other.width + dx), self.rsb, self.center)

    def top(self, cols=None) -> int:
        rows = [r for c, r in self.cells if cols is None or c in cols]
        return max(rows) if rows else -99

    def bottom(self, cols=None) -> int:
        rows = [r for c, r in self.cells if cols is None or c in cols]
        return min(rows) if rows else 99

    def right(self) -> int:
        return max(c for c, r in self.cells) + 1 if self.cells else 0

    def trimmed(self) -> "Sprite":
        """The same pixels with the empty columns at both sides cut off."""
        if not self.cells:
            return self
        c0 = min(c for c, r in self.cells)
        sp = self.moved(-c0)
        return Sprite(sp.cells, sp.right(), self.rsb)


def art(text: str) -> Sprite:
    """A sprite from a drawing: rows from the top down, separated by spaces, ``#`` for a pixel.

    The last row sits on the baseline (row 0). A ``|`` marks the baseline when rows hang below it: the
    row before ``|`` is row 0. ``@N`` as the first word puts the last row on row N instead.
    """
    words = text.split()
    bottom = 0
    if words and words[0].startswith("@"):
        bottom = int(words[0][1:])
        words = words[1:]
    if "|" in words:
        i = words.index("|")
        bottom = -(len(words) - i - 1)
        words = words[:i] + words[i + 1:]
    width = len(words[0])
    if any(len(w) != width for w in words):
        raise ValueError(f"rows of unequal length: {text!r}")
    top = bottom + len(words) - 1
    cells = {(c, top - i) for i, w in enumerate(words) for c, ch in enumerate(w) if ch == "#"}
    return Sprite(cells, width)


def touches(a, b) -> bool:
    """True if a pixel of ``b`` is on or next to a pixel of ``a`` (diagonals count)."""
    near = {(c + i, r + j) for c, r in a for i in (-1, 0, 1) for j in (-1, 0, 1)}
    return any(cell in near for cell in b)


def pack(*parts: Sprite) -> Sprite:
    """Sprites side by side, each as close to the last as it can come with one empty column between."""
    out = parts[0]
    for sp in parts[1:]:
        dx = out.right() - sp.width
        while touches(out.cells, {(c + dx, r) for c, r in sp.cells}):
            dx += 1
        out = out.plus(sp, dx)
        out.width = max(out.width, out.right())
    out.center = out.width
    return out


# -------------------------------------------------------------------------------------------- drawings

#: The character set. Capitals are seven pixels tall and mostly seven wide, so a counter is three pixels;
#: the lowercase is five tall and mostly six wide, so a counter is two. Figures are seven wide.
DRAWINGS = {
    # capitals
    "A": "..###.. .##.##. ##...## ##...## ####### ##...## ##...##",
    "B": "######. ##...## ##...## ######. ##...## ##...## ######.",
    "C": ".#####. ##...## ##..... ##..... ##..... ##...## .#####.",
    "D": "#####.. ##..##. ##...## ##...## ##...## ##..##. #####..",
    "E": "####### ##..... ##..... ######. ##..... ##..... #######",
    "F": "####### ##..... ##..... ######. ##..... ##..... ##.....",
    "G": ".#####. ##...## ##..... ##..### ##...## ##...## .#####.",
    "H": "##...## ##...## ##...## ####### ##...## ##...## ##...##",
    "I": "###### ..##.. ..##.. ..##.. ..##.. ..##.. ######",
    "J": "...#### .....## .....## .....## ##...## ##...## .#####.",
    "K": "##...## ##..##. ##.##.. ####... ##.##.. ##..##. ##...##",
    "L": "##..... ##..... ##..... ##..... ##..... ##..... #######",
    "M": "##...## ###.### ####### ##.#.## ##...## ##...## ##...##",
    "N": "##...## ###..## ####.## ##.#### ##..### ##...## ##...##",
    "O": ".#####. ##...## ##...## ##...## ##...## ##...## .#####.",
    "P": "######. ##...## ##...## ######. ##..... ##..... ##.....",
    "Q": ".#####. ##...## ##...## ##...## ##.#.## ##..##. .###.##",
    "R": "######. ##...## ##...## ######. ##.##.. ##..##. ##...##",
    "S": ".#####. ##...## ##..... .#####. .....## ##...## .#####.",
    "T": "###### ..##.. ..##.. ..##.. ..##.. ..##.. ..##..",
    "U": "##...## ##...## ##...## ##...## ##...## ##...## .#####.",
    "V": "##...## ##...## ##...## ##...## .##.##. ..###.. ...#...",
    "W": "##...## ##...## ##...## ##.#.## ####### ###.### ##...##",
    "X": "##...## ##...## .##.##. ..###.. .##.##. ##...## ##...##",
    "Y": "##..## ##..## ##..## .####. ..##.. ..##.. ..##..",
    "Z": "####### .....## ....##. ...##.. ..##... .##.... #######",
    # lowercase
    "a": ".####. ....## .##### ##..## .#####",
    "b": "##.... ##.... #####. ##..## ##..## ##..## #####.",
    "c": ".##### ##.... ##.... ##.... .#####",
    "d": "....## ....## .##### ##..## ##..## ##..## .#####",
    "e": ".####. ##..## ###### ##.... .#####",
    "f": "..### .##.. ####. .##.. .##.. .##.. .##..",
    "g": ".##### ##..## ##..## ##..## .##### | ....## #####.",
    "h": "##.... ##.... #####. ##..## ##..## ##..## ##..##",
    "i": "## .. ## ## ## ## ##",
    "j": "..## .... ..## ..## ..## ..## ..## | ..## ###.",
    "k": "##.... ##.... ##..## ##.##. ####.. ##.##. ##..##",
    "l": "## ## ## ## ## ## ##",
    "m": "#######. ##.##.## ##.##.## ##.##.## ##.##.##",
    "n": "#####. ##..## ##..## ##..## ##..##",
    "o": ".####. ##..## ##..## ##..## .####.",
    "p": "#####. ##..## ##..## ##..## #####. | ##.... ##....",
    "q": ".##### ##..## ##..## ##..## .##### | ....## ....##",
    "r": "#####. ##..## ##.... ##.... ##....",
    "s": ".##### ##.... .####. ....## #####.",
    "t": ".##.. ##### .##.. .##.. .##.. ..###",
    "u": "##..## ##..## ##..## ##..## .#####",
    "v": "##..## ##..## ##..## .####. ..##..",
    "w": "##....## ##....## ##.##.## .######. .##..##.",
    "x": "##..## .####. ..##.. .####. ##..##",
    "y": "##..## ##..## ##..## ##..## .##### | ....## #####.",
    "z": "###### ...##. ..##.. .##... ######",
    # figures: seven wide, so a zero has room for its dot and its slash
    "0": ".#####. ##...## ##...## ##.#.## ##...## ##...## .#####.",
    "1": "..##... .###... ..##... ..##... ..##... ..##... ######.",
    "2": ".#####. ##...## .....## ...###. .###... ##..... #######",
    "3": ".#####. ##...## .....## ...###. .....## ##...## .#####.",
    "4": "...###. ..####. .##.##. ##..##. ####### ....##. ....##.",
    "5": "####### ##..... ######. .....## .....## ##...## .#####.",
    "6": "..####. .##.... ##..... ######. ##...## ##...## .#####.",
    "7": "####### .....## ....##. ...##.. ..##... ..##... ..##...",
    "8": ".#####. ##...## ##...## .#####. ##...## ##...## .#####.",
    "9": ".#####. ##...## ##...## .###### .....## ....##. .####..",
    # ASCII punctuation
    "!": "## ## ## ## ## .. ##",
    '"': "@4 ##.## ##.## ##.##",
    "#": ".##.##. .##.##. ####### .##.##. ####### .##.##. .##.##.",
    "$": "..##.. .##### ##.... .####. ....## #####. ..##..",
    "%": "##...## ##..##. ...##.. ..##... .##.... ##..##. ....##.",
    "&": ".###... ##.##.. ##.##.. .###... ##.##.# ##..##. .###.##",
    "'": "@4 ## ## ##",
    "(": "@-1 ..## .##. ##.. ##.. ##.. ##.. .##. ..##",
    ")": "@-1 ##.. .##. ..## ..## ..## ..## .##. ##..",
    "*": "@1 ##..## .####. ###### .####. ##..##",
    "+": "@1 ..##.. ..##.. ###### ..##.. ..##..",
    ",": "@-1 .## .## ##.",
    "-": "@2 ####",
    ".": "## ##",
    "/": "@-1 ....## ...##. ...##. ..##.. ..##.. .##... .##... ##....",
    ":": "## ## .. ## ##",
    ";": "@-1 .## .## ... .## .## ##.",
    "<": "@1 ....## ..##.. ##.... ..##.. ....##",
    "=": "@2 ###### ...... ######",
    ">": "@1 ##.... ..##.. ....## ..##.. ##....",
    "?": ".####. ##..## ....## ..###. ..##.. ...... ..##..",
    "@": ".######. ##....## ##.##### ##.##.## ##.##### ##...... .######.",
    "[": "@-1 #### ##.. ##.. ##.. ##.. ##.. ##.. ####",
    "\\": "@-1 ##.... .##... .##... ..##.. ..##.. ...##. ...##. ....##",
    "]": "@-1 #### ..## ..## ..## ..## ..## ..## ####",
    "^": "@4 ..##.. .####. ##..##",
    "_": "@-1 ########",
    "`": "@5 ##. .##",
    "{": "@-1 ..### .##.. .##.. ##... .##.. .##.. .##.. ..###",
    "|": "@-2 ## ## ## ## ## ## ## ## ##",
    "}": "@-1 ###.. ..##. ..##. ...## ..##. ..##. ..##. ###..",
    "~": "@3 .###..# #..###.",
    # Latin-1 signs
    "¡": "@-2 ## .. ## ## ## ## ##",
    "¢": "@-1 ...##. .##### ##.##. ##.##. ##.##. .##### ...##.",
    "£": "..####. .##..## .##.... #####.. .##.... .##.... #######",
    "¤": "@1 ##..## .####. .#..#. .####. ##..##",
    "¥": "##..## ##..## .####. ###### ..##.. ###### ..##..",
    "¦": "@-2 ## ## ## ## .. ## ## ## ##",
    "§": ".##### ##.... .####. ##..## .####. ....## #####.",
    "©": ".#######. ##.....## ##.###.## ##.#...## ##.###.## ##.....## .#######.",
    "ª": "@3 .###. ...## ##.## .####",
    "«": "@0 ..##..## .##..##. ##..##.. .##..##. ..##..##",
    "¬": "@1 ###### ....## ....##",
    "®": ".#######. ##.....## ##.##..## ##.###.## ##.#.#.## ##.....## .#######.",
    "°": "@4 .###. ##.## .###.",
    "±": "..##.. ..##.. ###### ..##.. ..##.. ...... ######",
    "µ": "##..## ##..## ##..## ##..## ###### | ##.... ##....",
    "¶": ".###### ####.## ####.## .###.## ..##.## ..##.## ..##.##",
    "·": "@2 ##",
    "º": "@3 .###. ##.## ##.## .###.",
    "»": "@0 ##..##.. .##..##. ..##..## .##..##. ##..##..",
    "¿": "@-2 ..##.. ...... ..##.. .###.. ##.... ##..## .####.",
    "×": "@1 ##..## .####. ..##.. .####. ##..##",
    "÷": "@1 ..##.. ...... ###### ...... ..##..",
    # Latin letters that are not a base letter with a mark
    "Æ": "..####### .##.##... ##..##... ######### ##..##... ##..##... ##..#####",
    "æ": ".###.###. ...##..## .######## ##.##.... .###.####",
    "Ð": ".#####.. .##..##. .##...## ####..## .##...## .##..##. .#####..",
    "ð": "..##.. ###### ....## .##### ##..## ##..## .####.",
    "Å": "..###.. .##.##. ..###.. .##.##. ##...## ##...## ####### ##...## ##...##",
    "ỵ": "##..## ##..## ##..## ##..## .##### | ....## ##.##.",
    "Ø": "@-1 .......# .######. ##...##. ##..###. ##.#.##. ###..##. ##...##. ######.. #.......",
    "ø": "@-1 ......# .#####. ##..##. ##.###. ###.##. .####.. #......",
    "Þ": "##..... ######. ##...## ##...## ######. ##..... ##.....",
    "þ": "##.... ##.... #####. ##..## ##..## ##..## #####. | ##.... ##....",
    "ß": ".####. ##..## ##.##. ##..## ##..## ##..## ##.##.",
    "ẞ": ".#####. ##...## ##..##. ##.##.. ##..##. ##...## ##.###.",
    "Đ": ".#####.. .##..##. .##...## ####..## .##...## .##..##. .#####..",
    "đ": "....##. ...#### .#####. ##..##. ##..##. ##..##. .#####.",
    "Ħ": ".##...##. ######### .##...##. .#######. .##...##. .##...##. .##...##.",
    "ħ": ".##.... ####... .#####. .##..## .##..## .##..## .##..##",
    "ı": "## ## ## ## ##",
    "ȷ": "..## ..## ..## ..## ..## | ..## ###.",
    "ĸ": "##..## ##.##. ####.. ##.##. ##..##",
    "Ŀ": "##..... ##..... ##..... ##.##.. ##..... ##..... #######",
    "ŀ": "##.... ##.... ##.... ##.##. ##.... ##.... ##....",
    "Ł": "..##.... ..##.#.. ..###... .###.... #.##.... ..##.... ..######",
    "ł": "..##.. ..##.# ..###. .###.. #.##.. ..##.. ..##..",
    "Ŋ": "##...## ###..## ####.## ##.#### ##..### ##...## ##...## | .....## ...###.",
    "ŋ": "#####. ##..## ##..## ##..## ##..## | ....## ..###.",
    "Œ": ".########. ##..##.... ##..##.... ##..#####. ##..##.... ##..##.... .########.",
    "œ": ".###.###. ##.##..## ##.###### ##.##.... .###.####",
    "Ŧ": "###### ..##.. ..##.. .####. ..##.. ..##.. ..##..",
    "ŧ": ".##.. ##### .##.. ####. .##.. ..###",
    "ſ": "..### .##.. .##.. .##.. .##.. .##.. .##..",
    "Ɓ": "########. #.##...## ..##...## ..######. ..##...## ..##...## ..######.",
    "Ɗ": "#######.. #.##..##. ..##...## ..##...## ..##...## ..##..##. ..#####..",
    "Ə": ".#####. ##...## .....## ####### ##...## ##...## .#####.",
    "ƒ": "...### ..##.. ..##.. .####. ..##.. ..##.. ..##.. | ..##.. ###...",
    "Ƙ": "##..### ##.##.. ####... ###.... ####... ##.##.. ##..###",
    "ƙ": ".####. ##.... ##..## ##.##. ####.. ##.##. ##..##",
    "ɓ": ".###... ##..... ##..... ######. ##...## ##...## ######.",
    "ɗ": "...###. ....##. ....##. .#####. ##..##. ##..##. .#####.",
    "ə": ".####. ....## ###### ##..## .####.",
    "ʻ": "@4 .## ##. ##.",
    "ʼ": "@4 .## .## ##.",
    # Greek
    "Γ": "####### ##..... ##..... ##..... ##..... ##..... ##.....",
    "Δ": "...#... ..###.. .##.##. .##.##. ##...## ##...## #######",
    "Θ": ".#####. ##...## ##...## ####### ##...## ##...## .#####.",
    "Λ": "...#... ..###.. .##.##. .##.##. ##...## ##...## ##...##",
    "Ξ": "####### ....... ....... .#####. ....... ....... #######",
    "Π": "####### ##...## ##...## ##...## ##...## ##...## ##...##",
    "Σ": "####### ##..... .##.... ..##... .##.... ##..... #######",
    "Φ": "...##... .######. ##.##.## ##.##.## ##.##.## .######. ...##...",
    "Ψ": "##.##.## ##.##.## ##.##.## .######. ...##... ...##... ...##...",
    "Ω": ".#####. ##...## ##...## ##...## .##.##. .##.##. ###.###",
    "α": ".###.## ##..##. ##..##. ##..##. .###.##",
    "β": ".####. ##..## #####. ##..## ##..## ##..## #####. | ##.... ##....",
    "γ": "##..## ##..## .####. ..##.. ..##.. | ..##.. ..##..",
    "δ": ".##### ##.... .####. ##..## ##..## ##..## .####.",
    "ε": ".##### ##.... .###.. ##.... .#####",
    "ζ": "###### ..##.. .##... ##.... ##.... ##.... .####. | ....## ...##.",
    "η": "#####. ##..## ##..## ##..## ##..## | ....## ....##",
    "θ": ".####. ##..## ##..## ###### ##..## ##..## .####.",
    "ι": "##. ##. ##. ##. .##",
    "κ": "##..## ##.##. ####.. ##.##. ##..##",
    "λ": "##.... .##... .##... ..##.. .####. ##..## ##..##",
    "μ": "##..## ##..## ##..## ##..## ###### | ##.... ##....",
    "ν": "##..## ##..## ##..## ##.##. ####..",
    "ξ": "###### .##... ..###. .##... ##.... ##.... .####. | ....## ...##.",
    "π": "####### .##.##. .##.##. .##.##. .##.##.",
    "ρ": ".####. ##..## ##..## ##..## #####. | ##.... ##....",
    "ς": ".##### ##.... ##.... .####. ....## | ...##.",
    "σ": ".###### ##..##. ##..##. ##..##. .####..",
    "τ": "###### ..##.. ..##.. ..##.. ...###",
    "υ": "##..## ##..## ##..## ##..## .####.",
    "φ": "...##... .######. ##.##.## ##.##.## ##.##.## .######. | ...##... ...##...",
    "χ": "##..## ##..## .####. ..##.. .####. | ##..## ##..##",
    "ψ": "##.##.## ##.##.## ##.##.## ##.##.## .######. | ...##... ...##...",
    "ω": ".##..##. ##....## ##.##.## ##.##.## .##..##.",
    "·": "@4 ##",
    "΅": "@6 ...##. ..##.. ##..##",
    # Cyrillic
    "Б": "####### ##..... ##..... ######. ##...## ##...## ######.",
    "Д": "..#####. ..##.##. .##..##. .##..##. .##..##. .##..##. ######## | ##....##",
    "Ж": "##..##..## .##.##.##. ..######.. ..######.. .##.##.##. ##..##..## ##..##..##",
    "З": ".#####. ##...## .....## ..####. .....## ##...## .#####.",
    "И": "##...## ##..### ##.#### ####.## ###..## ##...## ##...##",
    "Л": "..##### .##..## .##..## .##..## .##..## .##..## ##...##",
    "У": "##...## ##...## ##...## .###### .....## ##...## .#####.",
    "Ц": "##...##. ##...##. ##...##. ##...##. ##...##. ##...##. ######## | ......##",
    "Ч": "##...## ##...## ##...## .###### .....## .....## .....##",
    "Ш": "##.##.## ##.##.## ##.##.## ##.##.## ##.##.## ##.##.## ########",
    "Щ": "##.##.##. ##.##.##. ##.##.##. ##.##.##. ##.##.##. ##.##.##. ######### | .......##",
    "Ъ": "###.... .##.... .##.... .#####. .##..## .##..## .#####.",
    "Ы": "##.....## ##.....## ##.....## #####..## ##..##.## ##..##.## #####..##",
    "Ь": "##..... ##..... ##..... ######. ##...## ##...## ######.",
    "Э": ".#####. ##...## .....## ..##### .....## ##...## .#####.",
    "Ю": "##..####. ##.##..## ##.##..## #####..## ##.##..## ##.##..## ##..####.",
    "Я": ".###### ##...## ##...## .###### ..##.## .##..## ##...##",
    "Ђ": "######.. ..##.... ..#####. ..##..## ..##..## ..##..## ..##.##.",
    "Є": ".#####. ##...## ##..... #####.. ##..... ##...## .#####.",
    "Љ": "..####..... .##.##..... .##.##..... .##.######. .##.##...## .##.##...## ##..######.",
    "Њ": "##..##.... ##..##.... ##..##.... #########. ##..##..## ##..##..## ##..#####.",
    "Ћ": "######.. ..##.... ..#####. ..##..## ..##..## ..##..## ..##..##",
    "Џ": "##...## ##...## ##...## ##...## ##...## ##...## ####### | ..###..",
    "Ґ": "......## ######## ##...... ##...... ##...... ##...... ##......",
    "Ғ": ".####### .##..... .##..... #####... .##..... .##..... .##.....",
    "Җ": "##..##..##. .##.##.##.. ..######... ..######... .##.##.##.. ##..##..##. ##..##..### | .........##",
    "Қ": "##...##. ##..##.. ##.##... ####.... ##.##... ##..##.. ##...### | ......##",
    "Ң": "##...##. ##...##. ##...##. #######. ##...##. ##...##. ##...### | ......##",
    "Ү": "##..## ##..## .####. ..##.. ..##.. ..##.. ..##..",
    "Ұ": "##..## ##..## .####. ..##.. ###### ..##.. ..##..",
    "Ҳ": "##...##. ##...##. .##.##.. ..###... .##.##.. ##...##. ##...### | ......##",
    "Ҷ": "##...##. ##...##. ##...##. .######. .....##. .....##. .....### | ......##",
    "Һ": "##..... ##..... ##..... ######. ##...## ##...## ##...##",
    "Ә": ".#####. ##...## .....## ####### ##...## ##...## .#####.",
    "Ө": ".#####. ##...## ##...## ####### ##...## ##...## .#####.",
    "б": ".##### ##.... #####. ##..## ##..## ##..## .####.",
    "в": "#####. ##..## #####. ##..## #####.",
    "г": "##### ##... ##... ##... ##...",
    "д": "..####. .##.##. .##.##. .##.##. ####### | ##...##",
    "ж": "##.##.## .######. ..####.. .######. ##.##.##",
    "з": ".####. ....## ..###. ....## .####.",
    "и": "##..## ##..## ##.### ###.## ##..##",
    "к": "##..## ##.##. ####.. ##.##. ##..##",
    "л": "..#### .##.## .##.## .##.## ##..##",
    "м": "##...## ###.### ##.#.## ##...## ##...##",
    "н": "##..## ##..## ###### ##..## ##..##",
    "п": "###### ##..## ##..## ##..## ##..##",
    "т": "###### ..##.. ..##.. ..##.. ..##..",
    "ф": "...##... .######. ##.##.## ##.##.## ##.##.## .######. | ...##... ...##...",
    "ц": "##..##. ##..##. ##..##. ##..##. ####### | .....##",
    "ч": "##..## ##..## .##### ....## ....##",
    "ш": "##.##.## ##.##.## ##.##.## ##.##.## ########",
    "щ": "##.##.##. ##.##.##. ##.##.##. ##.##.##. ######### | .......##",
    "ъ": "###.... .##.... .#####. .##..## .#####.",
    "ы": "##.....## ##.....## #####..## ##..##.## #####..##",
    "ь": "##.... ##.... #####. ##..## #####.",
    "э": ".####. ....## ..#### ....## .####.",
    "ю": "##..####. ##.##..## #####..## ##.##..## ##..####.",
    "я": ".##### ##..## .##### .##.## ##..##",
    "ђ": ".##.... ####... .#####. .##..## .##..## .##..## .##..## | .....## ...###.",
    "є": ".##### ##.... ####.. ##.... .#####",
    "љ": "..####.... .##.##.... .##.#####. .##.##..## ##..#####.",
    "њ": "##..##.... ##..##.... #########. ##..##..## ##..#####.",
    "ћ": ".##.... ####... .#####. .##..## .##..## .##..## .##..##",
    "џ": "##..## ##..## ##..## ##..## ###### | ..##..",
    "ґ": "....## ###### ##.... ##.... ##.... ##....",
    "ғ": ".##### .##... ####.. .##... .##...",
    "җ": "##.##.##. .######.. ..####... .######.. ##.##.### | .......##",
    "қ": "##..##. ##.##.. ####... ##.##.. ##..### | .....##",
    "ң": "##..##. ##..##. ######. ##..##. ##..### | .....##",
    "ү": "##..## ##..## .####. ..##.. ..##.. | ..##.. ..##..",
    "ұ": "##..## ##..## .####. ..##.. ..##.. | ###### ..##..",
    "ҳ": "##..##. .####.. ..##... .####.. ##..### | .....##",
    "ҷ": "##..##. ##..##. .#####. ....##. ....### | .....##",
    "ә": ".####. ....## ###### ##..## .####.",
    "ө": ".####. ##..## ###### ##..## .####.",
    # general punctuation
    "‒": "@3 #######",
    "–": "@2 ######",
    "—": "@2 #########",
    "―": "@2 ##########",
    "‘": "@4 .## ##. ##.",
    "’": "@4 .## .## ##.",
    "‚": "@-1 .## .## ##.",
    "‛": "@4 ##. ##. .##",
    "“": "@4 .##.## ##.##. ##.##.",
    "”": "@4 .##.## .##.## ##.##.",
    "„": "@-1 .##.## .##.## ##.##.",
    "‟": "@4 ##.##. ##.##. .##.##",
    "†": "@-1 ..##.. ###### ..##.. ..##.. ..##.. ..##.. ..##.. ..##..",
    "‡": "@-1 ..##.. ###### ..##.. ..##.. ..##.. ..##.. ###### ..##..",
    "•": "@1 .##. #### .##.",
    "…": "##.##.## ##.##.##",
    "‰": "##...##.... ##..##..... ...##...... ..##....... .##........ ##..##.##.. #...###.###",
    "′": "@4 ..## .##. ##..",
    "″": "@4 ..##..## .##..##. ##..##..",
    "‹": "@0 ..## .##. ##.. .##. ..##",
    "›": "@0 ##.. .##. ..## .##. ##..",
    "⁄": "@-1 ....## ...##. ...##. ..##.. ..##.. .##... .##... ##....",
    # currency
    "€": "..##### .##.... ######. .##.... ######. .##.... ..#####",
    "₠": ".###.#### ##...##.. ##...##.. ##...###. ##...##.. ##...##.. .###.####",
    "₡": ".###.#. ##.#.## ##.#.#. ##.#.#. ##.#.#. ##.#.## .###.#.",
    "₢": ".#####. ##...## ##..... ##.###. ##.##.. ##.##.. .####..",
    "₣": "####### ##..... ##..... ######. ##..... ####... ##.....",
    "₤": "..####. .##..## ####... .##.... ####... .##.... #######",
    "₥": "@-1 ......## ######## ##.##### ##.##.## ##.##.## ###..### .##.....",
    "₦": ".##...##. .###..##. ######### .##.####. ######### .##...##. .##...##.",
    "₧": "######..... ##...##.##. ##...###### ######..##. ##......##. ##......##. ##.......##",
    "₩": "##.....## ##.....## ######### ##.#.#.## ######### .##.#.##. .##...##.",
    "₪": "######.## ##...#.## ##.#.#.## ##.#.#.## ##.#...## ##.#####. ##.......",
    "₫": "@-2 ....##. ...#### .#####. ##..##. ##..##. ##..##. .#####. ....... #######",
    "₭": ".##...## .##..##. .##.##.. #######. .##.##.. .##..##. .##...##",
    "₮": "###### ..##.. ..#### ####.. ..#### ####.. ..##..",
    "₱": ".######. ######## .##...## ######## .######. .##..... .##.....",
    "₲": "...##... .######. ##.##.## ##.##... ##.##### ##.##.## .######. | ...##...",
    "₳": "...###... ..##.##.. ######### .##...##. ######### .##...##. .##...##.",
    "₴": ".#####. ##...## ####### ..###.. ####### ##...## .#####.",
    "₵": "@-1 ...##.. .#####. ##.##.# ##.##.. ##.##.. ##.##.# .#####. ...##..",
    "₸": "###### ...... ###### ..##.. ..##.. ..##.. ..##..",
    "₹": "####### ....##. ####### ....##. #####.. ..##... ...###.",
    "₺": ".##.... .##..## .####.. ###..## .####.. .##..## .#####.",
    "₼": "...##... .######. ##.##.## ##.##.## ##....## ##....## ##....##",
    "₽": ".######. .##...## .##...## .######. #####... .##..... .##.....",
    "₾": "..#.#.. .#####. ##.#.## ##.#.## ##...## .#####. ###.###",
    "₿": "@-1 .#.#... ######. ##...## ##...## ######. ##...## ##...## ######. .#.#...",
    "⃀": "##..### ##.##.. ####... ###.... ####..# ##.##.# ##..###",
    "№": "##...##...... ###..##...... ####.##..###. ##.####.##.## ##..###.##.## ##...##..###. ##...##.#####",
    "™": "@4 ######.##...## ..##...###.### ..##...##.#.##",
    "℮": "..####.. .##..##. ##....## ######## ##...... .##..##. ..####..",
    # math
    "∂": ".####. ....## .##### ##..## ##..## ##..## .####.",
    "∆": "...#... ..###.. .##.##. .##.##. ##...## ##...## #######",
    "∏": "@-1 ######## .##..##. .##..##. .##..##. .##..##. .##..##. .##..##. .##..##.",
    "∑": "@-1 ####### ##..... .##.... ..##... ...##.. ..##... .##.... ##..... #######",
    "−": "@3 ######",
    "√": ".....### .....##. ....##.. ##..##.. .####... ..##.... ..##....",
    "∞": "@1 .##..##. #..##..# .##..##.",
    "∫": "@-2 ..### ..##. ..##. ..##. ..##. ..##. ..##. ..##. ###..",
    "≈": "@1 .###..# #..###. ....... .###..# #..###.",
    "≠": "@1 ....## ###### ..##.. ###### ##....",
    "≤": "....## ..##.. ##.... ..##.. ....## ...... ######",
    "≥": "##.... ..##.. ....## ..##.. ##.... ...... ######",
    # arrows and shapes
    "←": "@1 ..##.... .###.... ######## .###.... ..##....",
    "→": "@1 ....##.. ....###. ######## ....###. ....##..",
    "↑": "..##.. .####. ###### ..##.. ..##.. ..##.. ..##..",
    "↓": "..##.. ..##.. ..##.. ..##.. ###### .####. ..##..",
    "↔": "@1 ..##..##.. .###..###. ########## .###..###. ..##..##..",
    "↕": "@-1 ..##.. .####. ###### ..##.. ..##.. ..##.. ###### .####. ..##..",
    "↖": "@1 #####.. ###.... ####... ##.##.. ....##. .....##",
    "↗": "@1 ..##### ....### ...#### ..##.## .##.... ##.....",
    "↘": "@1 ##..... .##.... ..##.## ...#### ....### ..#####",
    "↙": "@1 .....## ....##. ##.##.. ####... ###.... #####..",
    "■": "@0 ###### ###### ###### ###### ###### ######",
    "□": "@0 ###### ##..## ##..## ##..## ##..## ######",
    "▲": "@0 ...##... ..####.. .######. ########",
    "▼": "@1 ######## .######. ..####.. ...##...",
    "◆": "...##... ..####.. .######. ######## .######. ..####.. ...##...",
    "◊": "...##... ..####.. .##..##. ##....## .##..##. ..####.. ...##...",
    "○": "..####.. .##..##. ##....## ##....## ##....## .##..##. ..####..",
    "●": "..####.. .######. ######## ######## ######## .######. ..####..",
    "★": "....#.... ...###... ######### .#######. ..#####.. .###.###. .##...##.",
    "☆": "....#.... ...#.#... ####.#### .#.....#. ..#...#.. .#..#..#. .##...##.",
    "♥": "@0 .##.##. ####### ####### .#####. ..###.. ...#...",
    "✓": "@0 ......## .....##. ##..##.. .####... ..##....",
    "✗": "##...## .##.##. ..###.. ..###.. .##.##. ##...##",
}

#: Glyphs that sit flush with the next one: no white after them.
FLUSH = set("_")

#: Small figures, five rows tall: superscripts sit on row 2, denominators on the baseline, subscripts on
#: row -2, and the fractions are built from them.
SMALL = {
    "0": ".###. ##.## ##.## ##.## .###.",
    "1": ".##. ###. .##. .##. ####",
    "2": "####. ...## .###. ##... #####",
    "3": "####. ...## .###. ...## ####.",
    "4": "##.## ##.## ##### ...## ...##",
    "5": "##### ##... ####. ...## ####.",
    "6": ".###. ##... ####. ##.## .###.",
    "7": "##### ...## ..##. .##.. .##..",
    "8": ".###. ##.## .###. ##.## .###.",
    "9": ".###. ##.## .#### ...## .###.",
    "i": "## .. ## ## ##",
}
SUPERSCRIPTS = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹ⁱ", "0123456789i"))
SUBSCRIPTS = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
FRACTIONS = {"¼": "14", "½": "12", "¾": "34", "⅓": "13", "⅔": "23", "⅕": "15", "⅖": "25", "⅗": "35", "⅘": "45",
             "⅙": "16", "⅚": "56", "⅛": "18", "⅜": "38", "⅝": "58", "⅞": "78"}

#: Characters drawn like another one: Greek and Cyrillic letters that look like Latin ones, and signs
#: that Unicode holds twice.
SAME = dict(zip(
    "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧοАВЕКМНОРСТХЅІЈаеорсухѕіјһГПФΩ‐‑;",
    "ABEZHIKMNOPTYXoABEKMHOPCTXSIJaeopcyxsijhΓΠΦΩ--;"))

#: The zero with a slash, for the ``zero`` feature (and Ø is drawn the same way).
ZERO_SLASHED = ".#####. ##...## ##..### ##.#.## ###..## ##...## .#####."

#: Two letters as one character.
PAIRS = {"Ĳ": "IJ", "ĳ": "ij", "₨": "Rs", "₯": "Δρ"}


# ------------------------------------------------------------------------------------------------ marks

#: Marks above a letter, drawn with their lowest row on row 0: (for an even width, for an odd width).
#: A base an even number of pixels wide takes the first, so the mark sits exactly in its middle.
ABOVE = {
    "grave": ("##. .##", None),
    "acute": (".## ##.", None),
    "circumflex": ("..##.. ##..##", "..#.. ##.##"),
    "tilde": (".##..# #..##.", ".###..# #..###."),
    "macron": ("####", "#####"),
    "breve": ("##..## .####.", "##.## .###."),
    "dot": ("##", None),
    "dieresis": ("##..##", "##.##"),
    "hook": ("### ..#", None),
    "ring": (".##. #..# .##.", ".#. #.# .#."),
    "hungarumlaut": (".##.## ##.##.", None),
    "caron": ("##..## ..##..", "##.## ..#.."),
    "commaturned": ("..## .##.", None),
}
#: Marks below, drawn with their top row on row 0, and how they sit: under the letter with a row of
#: white between ("apart"), touching it ("touch"), or at its right foot ("foot").
BELOW = {
    "dotbelow": ("##", "apart"),
    "commabelow": (".## ##.", "apart"),
    "cedilla": (".## ##.", "touch"),
    "ogonek": ("##. .##", "foot"),
}
#: Combining characters and the marks they are drawn with.
COMBINING = {0x300: "grave", 0x301: "acute", 0x302: "circumflex", 0x303: "tilde", 0x304: "macron",
             0x306: "breve", 0x307: "dot", 0x308: "dieresis", 0x309: "hook", 0x30A: "ring",
             0x30B: "hungarumlaut", 0x30C: "caron", 0x340: "grave", 0x341: "acute",
             0x323: "dotbelow", 0x326: "commabelow", 0x327: "cedilla", 0x328: "ogonek", 0x31B: "horn"}
#: Spacing marks: the mark on its own, at the height it has over a lowercase letter.
SPACING = {"´": "acute", "¨": "dieresis", "¯": "macron", "¸": "cedilla", "ˆ": "circumflex", "ˇ": "caron",
           "˘": "breve", "˙": "dot", "˚": "ring", "˛": "ogonek", "˜": "tilde", "˝": "hungarumlaut",
           "΄": "acute"}
#: Letters whose cedilla is drawn as a comma below them (Latvian), and the g whose comma is turned above.
COMMA_CEDILLA = set("KkLlNnRrGg")
#: The apostrophe that stands for a caron beside a tall letter (ď ľ ť Ľ).
TICK = "## ## #."
#: Letters that drop their dot under a mark above.
DOTLESS = {"i": "ı", "j": "ȷ", "і": "ı", "ј": "ȷ"}
#: Letters whose caron is an apostrophe beside the ascender (ď ľ ť Ľ).
CARON_BESIDE = set("dltL")
GREEK_CAPITALS = set("ΑΕΗΙΟΥΩ")

_PARSED: dict = {}


def _art(key, text) -> Sprite:
    if key not in _PARSED:
        _PARSED[key] = art(text)
    return _PARSED[key]


def mark(name: str, odd: bool) -> Sprite:
    even_art, odd_art = ABOVE[name]
    return _art(("mark", name, odd and odd_art is not None), odd_art if odd and odd_art else even_art)


def drawing(ch: str) -> Sprite | None:
    """The sprite of a character that has a drawing, or None."""
    if ch in DRAWINGS:
        sp = _art(ch, DRAWINGS[ch])
        if ch in FLUSH:
            sp.rsb = 0
        if ch in "jȷ":
            sp.center = 6          # over the stem, not the tail
        return sp
    if ch in SAME:
        return drawing(SAME[ch])
    return None


def _above(sp: Sprite, name: str) -> Sprite:
    """``sp`` with a mark above it, in the middle, one empty row over the pixels below it. Every mark
    over a lowercase letter starts on row 6, over a capital or an ascender on row 8. The ring, three
    rows tall, comes down as far as it can without touching the letter (Ů)."""
    m = mark(name, sp.center % 2 == 1)
    lean = 1 if name in ("acute", "hook", "hungarumlaut", "commaturned") else 0
    c0 = (sp.center - m.width + lean) // 2
    y = sp.top(range(c0, c0 + m.width)) + 2
    while touches(sp.cells, {(c + c0, r + y) for c, r in m.cells}):
        y += 1
    if name == "ring":
        while not touches(sp.cells, {(c + c0, r + y - 1) for c, r in m.cells}) and y > sp.top(range(c0, c0 + m.width)) + 1:
            y -= 1
    return sp.plus(m, c0, y)


def _below(sp: Sprite, name: str) -> Sprite:
    """``sp`` with a mark below it: in the middle, or at the right foot for the ogonek."""
    text, how = BELOW[name]
    m = _art(("below", name), text)
    m_top = m.top()
    if how == "foot":
        row0 = [c for c, r in sp.cells if r == sp.bottom()]
        c0 = max(row0) - 1
        return sp.plus(m, c0, sp.bottom() - 1 - m_top)
    c0 = (sp.center - m.width) // 2
    low = sp.bottom(range(c0 - 1, c0 + m.width + 1))
    y = low - (2 if how == "apart" else 1)
    return sp.plus(m, c0, y - m_top)


#: The horn of ơ and ư, from the right edge of the letter (x = 0) and its top row (y = 0): it fills the
#: round corner and rises one row up and to the right.
HORN = {(-1, 0), (0, 1), (1, 1)}


def _horn(sp: Sprite) -> Sprite:
    """The horn of ơ and ư: it grows from the upper right of the bowl."""
    top = sp.top()
    right = max(c for c, r in sp.cells if r == top - 1) + 1
    return sp.plus(Sprite(HORN, 0), right, top)


def compose(ch: str) -> Sprite | None:
    """An accented letter from its base and its marks, or None if it has no such parts."""
    parts = unicodedata.normalize("NFD", ch)
    if len(parts) < 2:
        return None
    base_ch, marks = parts[0], [COMBINING.get(ord(m)) for m in parts[1:]]
    if None in marks:
        return None
    if base_ch in DOTLESS and any(m in ABOVE for m in marks):
        base_ch = DOTLESS[base_ch]
    base = drawing(base_ch)
    if base is None:
        return None
    sp = Sprite(base.cells, base.width, base.rsb, base.center)
    if base_ch in GREEK_CAPITALS and marks == ["acute"]:
        # the tonos of a Greek capital stands at its upper left
        tonos = _art(("mark", "tonos"), ".## ##.")
        sp = sp.moved(4).plus(tonos, 0, 5)
        sp.center = sp.width
        return sp
    if base_ch in CARON_BESIDE and marks == ["caron"]:
        # beside the ascender, one column of white from the highest three rows of the letter
        top = sp.top()
        right = max(c for c, r in sp.cells if r >= top - 2) + 1
        return sp.plus(_art(("mark", "tick"), TICK), right + 1, top - 2)
    for i, name in enumerate(marks):
        if name == "horn":
            sp = _horn(sp)
        elif name in ABOVE:
            if i and marks[i - 1] == "circumflex" and name in ("acute", "grave", "hook"):
                sp = _beside(sp, name)
            else:
                sp = _above(sp, name)
        elif name == "cedilla" and base_ch in COMMA_CEDILLA:
            sp = _above(sp, "commaturned") if base_ch == "g" else _below(sp, "commabelow")
        else:
            sp = _below(sp, name)
    return flush_left(sp)


def flush_left(sp: Sprite) -> Sprite:
    """The sprite moved right until no pixel is left of column 0 (a mark wider than its letter)."""
    c0 = min(c for c, r in sp.cells) if sp.cells else 0
    if c0 < 0:
        sp = sp.moved(-c0)
    sp.width = max(sp.width, sp.right())
    return sp


def _beside(sp: Sprite, name: str) -> Sprite:
    """A Vietnamese tone mark over a circumflex: up and to the right of it (the grave to the left)."""
    m = mark(name, False)
    top = sp.top()
    marks_cols = [c for c, r in sp.cells if r == top]
    if name == "grave":
        c0 = min(marks_cols) - m.width
    else:
        c0 = max(marks_cols) + 2
    sp = sp.plus(m, c0, top + 1)
    if c0 < 0:
        sp = sp.moved(-c0)
        sp.center = sp.width
    return sp


def small(ch: str) -> Sprite:
    return _art(("small", ch), SMALL[ch])


def fraction(digits: str) -> Sprite:
    """A fraction: the numerator on rows 2 to 6, the fraction slash cut to the height of a capital, and the
    denominator on the baseline, each as close to the last as one column of white allows."""
    slash = _art("⁄", DRAWINGS["⁄"])
    slash = Sprite({(c, r) for c, r in slash.cells if 0 <= r <= 6}, slash.width)
    return pack(small(digits[0]).moved(0, 2), slash, small(digits[1]))


def sprite_for(name: str, ch: str | None) -> Sprite | None:
    """The sprite of a glyph from the drawings and the rules, or None if it must be sampled."""
    if ch is not None:
        sp = drawing(ch)
        if sp is not None:
            return sp
        if ch in SUPERSCRIPTS:
            return small(SUPERSCRIPTS[ch]).moved(0, 2)
        if ch in SUBSCRIPTS:
            return small(SUBSCRIPTS[ch]).moved(0, -2)
        if ch in FRACTIONS:
            return fraction(FRACTIONS[ch])
        if ch in PAIRS:
            return pack(*(drawing(c) for c in PAIRS[ch]))
        if ch in SPACING:
            m = SPACING[ch]
            if m in ABOVE:
                return mark(m, False).moved(0, 6)
            sp = _art(("below", m), BELOW[m][0])
            return sp.moved(0, -1 - sp.top())
        sp = compose(ch)
        if sp is not None:
            return sp
        return None
    # forms without a code point
    base, _, suffix = name.partition(".")
    figures = dict(zip(("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"),
                       "0123456789"))
    if base in figures:
        if suffix == "pnum":
            return drawing(figures[base]).trimmed()
        if suffix == "dnom":
            return small(figures[base])
        if suffix == "zero":
            return _art("zero.zero", ZERO_SLASHED)
    up = {"hyphen": ("-", 1), "endash": ("–", 1), "emdash": ("—", 1), "figuredash": ("‒", 0),
          "horizontalbar": ("―", 1), "periodcentered": ("·", 1), "bullet": ("•", 1),
          "guillemotleft": ("«", 1), "guillemotright": ("»", 1), "guilsinglleft": ("‹", 1),
          "guilsinglright": ("›", 1), "exclamdown": ("¡", 2), "questiondown": ("¿", 2),
          "parenleft": ("(", 0), "parenright": (")", 0), "bracketleft": ("[", 0), "bracketright": ("]", 0),
          "braceleft": ("{", 0), "braceright": ("}", 0), "slash": ("/", 0), "backslash": ("\\", 0),
          "bar": ("|", 0), "at": ("@", 0)}
    if name == "periodcentered.loclCAT":
        return drawing("·")
    if name == "periodcentered.loclCAT.case":
        return drawing("·").moved(0, 1)
    if suffix == "case" and base in up:
        c, dy = up[base]
        return drawing(c).moved(0, dy)
    return None


def mark_sprite(name: str, ch: str | None) -> Sprite | None:
    """A combining mark on its own, around x = 0, where the ``mark`` feature puts it: a mark above
    starts on row 6 (the engine moves it two rows up over a capital), a mark below hangs under row 0,
    and the horn starts at the right edge of the letter."""
    if name == "caroncomb.alt":
        return _art(("mark", "tick"), TICK).moved(0, 4)
    m = COMBINING.get(ord(ch)) if ch else None
    if m in ABOVE:
        sp = mark(m, False)
        return sp.moved(-(sp.width // 2), 6)
    if m == "horn":
        return Sprite(HORN, 0).moved(0, 4)
    if m in BELOW:
        text, how = BELOW[m]
        sp = _art(("below", m), text)
        dx = -1 if how == "foot" else -(sp.width // 2)
        return sp.moved(dx, (-1 if how in ("touch", "foot") else -2) - sp.top())
    return None


# -------------------------------------------------------------------------------------------- the grid


def rectangles(cells) -> list:
    """The pixels as few rectangles: runs along each row, and runs that repeat on the rows above merged."""
    rows: dict = {}
    for c, r in cells:
        rows.setdefault(r, set()).add(c)
    runs = {}
    for r, cs in rows.items():
        cs = sorted(cs)
        start = prev = cs[0]
        out = []
        for c in cs[1:] + [None]:
            if c is not None and c == prev + 1:
                prev = c
                continue
            out.append((start, prev + 1))
            if c is not None:
                start = prev = c
        runs[r] = out
    boxes = []
    done = set()
    for r in sorted(runs):
        for run in runs[r]:
            if (r, run) in done:
                continue
            top = r
            while run in runs.get(top + 1, []):
                top += 1
                done.add((top, run))
            boxes.append((run[0], r, run[1], top + 1))
    return boxes


def outline(cells, dx=0) -> list:
    """Contours for the pixels, shifted ``dx`` columns."""
    if not cells:
        return []
    return union([rect((a + dx) * PX, r0 * PX, (b + dx) * PX, r1 * PX) for a, r0, b, r1 in rectangles(cells)])


# ------------------------------------------------------------------------------------------- sampling

#: The cell that one pixel samples, in the units of the outline: half a stem wide and one stroke tall.
#: The outline is drawn with stems of 125 units, so a stem covers two cells and becomes two pixels.
CELL_W, CELL_H = 62.5, 125.0
#: Sub-rows per cell row when the coverage is measured.
SUB = 8


def _spans(polys, y):
    """Where a horizontal line at ``y`` is inside the outline (non-zero winding)."""
    xs = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if (a.imag > y) != (b.imag > y):
                x = a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag)
                xs.append((x, 1 if b.imag > a.imag else -1))
    xs.sort()
    out, w, start = [], 0, 0.0
    for x, d in xs:
        nw = w + d
        if w == 0 and nw != 0:
            start = x
        elif w != 0 and nw == 0:
            out.append((start, x))
        w = nw
    return out


def coverage(contours, phase=0.0):
    """How much of each cell the outline covers: {(column, row): share}. ``phase`` moves the grid
    sideways by that share of a cell."""
    polys = [p for p in (flatten_contour(c, 1.0) for c in contours) if len(p) > 2]
    if not polys:
        return {}
    xs = [q.real for p in polys for q in p]
    ys = [q.imag for p in polys for q in p]
    x0 = min(xs) - phase * CELL_W
    r0, r1 = int(min(ys) // CELL_H) - 1, int(max(ys) // CELL_H) + 1
    out = {}
    for r in range(r0, r1 + 1):
        for s in range(SUB):
            y = (r + (s + 0.5) / SUB) * CELL_H
            for a, b in _spans(polys, y):
                ca, cb = (a - x0) / CELL_W, (b - x0) / CELL_W
                i = int(ca)
                while i < cb:
                    part = min(cb, i + 1) - max(ca, i)
                    if part > 0:
                        out[(i, r)] = out.get((i, r), 0.0) + part / SUB
                    i += 1
    return out


def sample(contours, keep=0.5) -> Sprite | None:
    """Pixels for an outline: the grid is tried at eight sideways phases, and the phase that leaves the
    fewest half-covered cells wins. A cell more than ``keep`` covered becomes a pixel."""
    best = None
    for k in range(8):
        cov = coverage(contours, k / 8)
        doubt = sum(min(v, 1 - v) for v in cov.values())
        if best is None or doubt < best[0] - 1e-6:
            best = (doubt, cov)
    if best is None or not best[1]:
        return None
    cells = {cell for cell, v in best[1].items() if v > keep}
    if not cells:
        # a mark thinner than half a cell: keep the cells it covers most
        top = max(best[1].values())
        cells = {cell for cell, v in best[1].items() if v >= top * 0.8}
    c0 = min(c for c, r in cells)
    cells = {(c - c0, r) for c, r in cells}
    return Sprite(cells, max(c for c, r in cells) + 1)


# ------------------------------------------------------------------------------------------ the effect

#: Names of the glyphs that were sampled in the last build, for a report.
SAMPLED: list = []


def pixelate(recipes, layers=False, gap=GAP, split=2, names=None):
    """Every glyph as square pixels on the grid. A character with a drawing (or a rule) uses it; any
    other glyph is sampled from its outline.

    ``gap`` is the white after each glyph, in pixels. With ``layers`` the glyph is a color glyph with
    three flat layers: ``face`` (every pixel), ``lower`` (the pixels on row ``split`` and below, the
    darker part of the letter) and ``shadow`` (the pixels one row down and one column right that the
    letter does not cover: a hard drop shadow)."""
    chars = {n: chr(r.unicode) for n, r in recipes.items() if r.unicode is not None}

    def effect(g, ink):
        ch = chars.get(g.name)
        is_mark = (g._frame is not None and g._frame[0] == 0 and g._advance is None) or g.name == "caroncomb.alt"
        sp = mark_sprite(g.name, ch) if is_mark else sprite_for(g.name, ch)
        if sp is None:
            sp = sample(ink)
            if sp is not None and g.name not in SAMPLED:
                SAMPLED.append(g.name)
        if sp is None:
            return
        if not is_mark:
            sp = flush_left(sp)
            sp = Sprite(sp.cells, sp.width, sp.rsb + gap - GAP, sp.center)
        place(g, sp, is_mark)
        if layers:
            cells = sp.cells
            shadow = {(c + 1, r - 1) for c, r in cells} - cells
            lower = {(c, r) for c, r in cells if r <= split}
            g.layers = [("face", outline(cells))]
            if lower:
                g.layers.append(("lower", outline(lower)))
            if shadow:
                g.layers.append(("shadow", outline(shadow)))

    return effects.wrapped(recipes, effect, names=names or [n for n in recipes if n not in ("space", "nbspace")])


def with_space(recipes, width=SPACE):
    """The word space and the no-break space: ``width`` pixels wide."""
    from whateverfont.glyph import Recipe

    def space(g):
        g._advance = width * PX
        g._frame = (0, 0, 0)

    out = recipes.copy()
    for name in ("space", "nbspace"):
        if name in out:
            r = out[name]
            out[name] = Recipe(name, space, r.unicode, r.case)
    return out


def place(g, sp: Sprite, is_mark=False):
    """Put a sprite into the glyph: pixels from x = 0, the advance a whole number of pixels."""
    if is_mark:
        # a combining mark: no advance, drawn around x = 0
        g.frame(0, 0, 0)
        effects.redraw(g, outline(sp.cells))
        return
    g.frame((sp.width + sp.rsb) * PX, 0, 0)
    g.anchors["top"] = complex(sp.center // 2 * PX, g.xh)
    effects.redraw(g, outline(sp.cells))
