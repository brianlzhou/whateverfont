"""Etchant: letters drawn as copper traces on a printed circuit board.

The `traces` effect (traces.py, next to this file) redraws the centerline of every stroke as a trace
that runs at 0, 45 and 90 degrees, with a round pad at each free end. The recipes below redraw the
few glyphs whose stock shape did not survive that: parens that were nearly straight, brackets and
braces whose arms were shorter than a pad, a double quote too tight for two pads, an I that matched
l, a ! that read as an i turned over, a y that became a fork, and an N and an M whose diagonals
needed a step to reach 45 degrees.
"""

from whateverfont import Family, latin
from whateverfont.glyph import H, V
from whateverfont.presets import preset
from whateverfont.recipes.lower import arch, n_width

from traces import PAD, PALETTES, W, plain, traces

SAMPLE = "Signal Path"

# A monoline skeleton: the stem is as wide as a trace, so the centerlines sit where a trace of
# that width needs them. Every stroke has the same thickness (contrast 1, no join thinning, capitals
# as heavy as the lowercase).
BASE = preset("technical", weight=W, contrast=1.0, cap_weight=1.0, round_weight=1.0, join=1.0, roundness=0.0,
              flare=0.0, superness=0.4, spacing=1.2, word_space=1.2)

RECIPES = latin()
r = RECIPES.add


def _ends(g):
    """The top and the bottom of brackets and parens: centerlines, so the trace reaches the stock ends."""
    return g.asc + 16 - W / 2, g.desc * 0.82 + W / 2


def _paren(g, x_in, x_out):
    """A paren as a trace: a 45 degree run out, an upright run, a 45 degree run back."""
    top, bot = _ends(g)
    d = x_in - x_out
    (g.path(x_in, top)
     .to(x_out, top - abs(d), corner=True)
     .to(x_out, bot + abs(d), corner=True)
     .to(x_in, bot)
     .done(tag="paren"))


PAREN = 118.0      # how far a paren bows out


@r("parenleft", "(")
def parenleft(g):
    _paren(g, g.L + PAREN, g.L)
    g.frame(None, 0.7, 0.35)


@r("parenright", ")")
def parenright(g):
    _paren(g, g.L, g.L + PAREN)
    g.frame(None, 0.35, 0.7)


ARM = 170.0        # bracket arms reach past the chamfer and the pad


def _bracket(g, x_stem, x_arm):
    top, bot = _ends(g)
    (g.path(x_arm, top)
     .to(x_stem, top, corner=True)
     .to(x_stem, bot, corner=True)
     .to(x_arm, bot)
     .done(start=V, end=V, tag="bracket"))


@r("bracketleft", "[")
def bracketleft(g):
    _bracket(g, g.L, g.L + ARM)
    g.frame(None, 0.9, 0.35)


@r("bracketright", "]")
def bracketright(g):
    _bracket(g, g.L + ARM, g.L)
    g.frame(None, 0.35, 0.9)


def _brace(g, x_stem, x_tip, x_arm):
    """A brace: a bracket whose stem steps out to a point at the middle in two 45 degree runs."""
    top, bot = _ends(g)
    ym = (top + bot) / 2
    t = abs(x_stem - x_tip)
    (g.path(x_arm, top)
     .to(x_stem, top, corner=True)
     .to(x_stem, ym + t, corner=True)
     .to(x_tip, ym, corner=True)
     .to(x_stem, ym - t, corner=True)
     .to(x_stem, bot, corner=True)
     .to(x_arm, bot)
     .done(start=V, end=V, tag="brace"))


@r("braceleft", "{")
def braceleft(g):
    _brace(g, g.L + 76, g.L, g.L + 76 + ARM - 30)
    g.frame(None, 0.5, 0.35)


@r("braceright", "}")
def braceright(g):
    _brace(g, g.L + ARM - 30, g.L + ARM + 46, g.L)
    g.frame(None, 0.35, 0.5)


@r("quotedbl", '"')
def quotedbl(g):
    """Two ticks set far enough apart for a pad on each."""
    x0 = g.L * 1.05
    step = 2 * PAD + 22
    for x in (x0, x0 + step):
        g.path(x, g.asc).to(x, g.asc - (g.asc - g.xh) * 1.05).done(start=H, end=H, tag="tick")
    g.frame(g.sw * 1.05 + step, 0.6, 0.6)


@r("I", "I", case="upper")
def I(g):
    """A stem between two bars, so that I is not l. The bars are long enough for a pad at each end
    to clear the stem."""
    w = 236.0
    g.bar(0, w, g.cap - W / 2)
    g.bar(0, w, W / 2)
    g.stem(w / 2, 0, g.cap)
    g.frame(w, 0.45, 0.45)


@r("exclam", "!", case="upper")
def exclam(g):
    """A plain stem over a pad: with a pad on top as well it read as an i turned over."""
    d = g.sw * 1.22
    g.dot(d / 2, d / 2, d)
    g.path(d / 2, g.cap).to(d / 2, d * 1.75).done(start=H, end=H, tag="bare")
    g.frame(d, 0.9, 0.9)


@r("y", "y")
def y(g):
    """A u whose right stem runs on into the descender and turns left, like the tail of g and j.

    The stock y is two diagonals; as traces they bent into a fork that read as a small Y."""
    w = n_width(g)
    start = len(g.strokes)
    arch(g, g.L, w - g.L)
    g.rotate(180, w / 2, g.xh / 2, start=start)
    R = w - g.L
    (g.path(R, g.xh)
     .to(R, g.desc + W / 2, corner=True)
     .to(g.L + 20, g.desc + W / 2)
     .done(start=H, end=V, tag="tail"))
    g.frame(w, "s", "s")


@r("N", "N", case="upper")
def N(g):
    """A left stem that turns down into one 45 degree run, which ends on a full right stem.

    The stock diagonal is steeper than 45 degrees; drawn as a trace it needed a step in the middle."""
    w = 2 * g.sw + g.capw(1.08, 1.12)
    R = w - g.L
    top = g.cap - W / 2
    (g.path(g.L, 0)
     .to(g.L, top, corner=True)
     .to(R, top - (R - g.L))
     .done(start=H, tag="n"))
    g.stem(R, 0, g.cap)
    g.frame(w)


@r("M", "M", case="upper")
def M(g):
    """Upright legs and a V of two 45 degree runs that meets a little above the middle."""
    w = 2 * g.sw + g.capw(1.52, 1.62)
    R = w - g.L
    xm = w / 2
    top = g.cap - W / 2
    (g.path(g.L, 0)
     .to(g.L, top, corner=True)
     .to(xm, top - (xm - g.L), corner=True)
     .to(R, top, corner=True)
     .to(R, 0)
     .done(tag="m"))
    g.frame(w)


FAMILY = Family(
    name="Etchant",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Letters drawn as copper traces with 45 degree bends, pads and vias, on a solder mask board.",
    base=BASE,
    recipes=traces(RECIPES),
    styles={"Regular": {}},
    palettes=PALETTES,
    ascent=960,          # room for the stacked marks of Vietnamese capitals (Ẫ) with their solder mask
    sample=SAMPLE,
)

PLAIN = Family(
    name="Etchant Plain",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="The same trace letters in one color, with the pad holes drilled through.",
    base=BASE,
    recipes=plain(RECIPES),
    styles={"Regular": {}},
    ascent=960,
    sample=SAMPLE,
)

DIRECTIONS = [FAMILY, PLAIN]
