"""Letters for a monospaced font.

In a font where every glyph has one width, a bare stem (i, l, I, 1) leaves a
hole in the line. These recipes give those letters bars and feet, so they fill
the cell, put a dot in the zero so it cannot be read as a capital O, and draw
the signs of code large, level and as heavy as the letters. Everything else is
the basic Latin set: the engine fits each glyph to the cell.
"""

from __future__ import annotations

import math

from ..glyph import G, H, V, Recipes
from .figures import FIGURES, _box
from .lower import LOWER, i_dot_y, open_angle

MONO = Recipes()
r = MONO.add


def _body(g: G) -> float:
    """The width these letters are drawn at: wide enough to read as a letter, not a line."""
    return g.cw * 0.92 + g.sw * 1.6


def _bar_t(g: G) -> tuple:
    """Thickness of the flags and feet, and the width multiplier that draws it.

    In a family with slab serifs they are the slabs, so they take the slab's thickness.
    """
    if g.serifed:
        return g.serif_t, g.p.serif_weight
    return g.hw, 1.0


def _flagged(g: G, h: float, dot: bool):
    """A stem with a flag on the left at height ``h`` and a foot: i, and l in a family with serifs."""
    w = _body(g)
    x = w * 0.54
    t, k = _bar_t(g)
    g.stem(x, 0, h, serif0=False, serif1=False)       # the flag and the foot are its serifs
    g.bar(w * 0.14, x, h - t / 2, l=0.5, w=k)          # the flag
    g.bar(0, w, t / 2, l=0.5, r=0.5, w=k)              # the foot
    if dot:
        g.dot(x - g.sw * 0.05, i_dot_y(g))
    g.frame(w, 0.5, 0.5)


@r("i", "i")
def i(g):
    _flagged(g, g.xh, True)


@r("dotlessi", 0x0131)
def dotlessi(g):
    n = len(g.shapes)
    i(g)
    del g.shapes[n:]


@r("l", "l")
def l(g):
    """A bar on the left at the top and a tail to the right at the foot, so it is not a 1 or an I.

    A family with slab serifs gets the typewriter l instead: a flag and a foot, like the i.
    """
    if g.serifed:
        _flagged(g, g.asc, False)
        return
    w = 0.70 * (g.p.mono or 600.0)
    xs = 0.44 * w                              # the stem, left of the middle
    r_ = 0.30 * w
    yb = g.hw / 2
    g.bar(0, xs, g.flat_top(g.asc), l=0.5)
    (g.path(xs, g.asc)
     .to(xs, yb + r_)
     .arc(xs + r_, yb, "v")
     .to(w, yb)
     .done(start=H, end=V))
    g.frame(w, 0.5, 0.5)


@r("j", "j")
def j(g):
    w = _body(g)
    x = w * 0.66
    rx = min(g.cw * 0.42, x - g.sw * 0.2)
    yh = g.desc * 0.40
    ry = yh - g.dbot
    end = -(90 + open_angle(g, 46, 60))
    (g.path(x, g.xh, fl=1.0)
     .flared_from(x, yh)
     .ellipse(x - rx, yh, rx, ry, 0, end, fl=1.0)
     .done(start=H, end=g.curved_cut(), round_start=0.0 if g.serifed else None, tag="tail"))
    t, k = _bar_t(g)
    g.bar(w * 0.20, x, g.xh - t / 2, l=0.5, w=k)
    g.dot(x - g.sw * 0.05, i_dot_y(g))
    g.frame(w, 0.5, 0.5)


@r("dotlessj", 0x0237)
def dotlessj(g):
    n = len(g.shapes)
    j(g)
    del g.shapes[n:]


@r("I", "I", case="upper")
def I(g):
    w = g.cw * 0.80 + g.sw * 1.4
    t, k = _bar_t(g)
    g.stem(w / 2, 0, g.cap, serif0=False, serif1=False)
    g.bar(0, w, g.cap - t / 2, l=0.5, r=0.5, w=k)
    g.bar(0, w, t / 2, l=0.5, r=0.5, w=k)
    g.frame(w, 0.5, 0.5)


@r("one", "1", case="figure")
def one(g):
    start = len(g.strokes)
    FIGURES["one"].fn(g)
    g._advance = None
    # the foot bar below is the serif, so the figure's own slab goes
    g.strokes[start:] = [s for s in g.strokes[start:] if s.anchor is None]
    xs = [n.p.real for s in g.strokes[start:] for n in s.nodes]
    x0, x1 = min(xs), max(xs)
    stem = max(xs)                                   # the stem is the right-hand stroke
    half = max(stem - x0, g.sw * 1.6)
    t, k = _bar_t(g)
    g.bar(stem - half, stem + half * 0.9, t / 2, l=0.5, r=0.5, w=k)
    g.frame(None, 0.5, 0.5)


@r("zero", "0", case="figure")
def zero(g):
    w = 0.755 * (g.p.mono or 600.0)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.cap))
    # a dot in the counter that takes a third of the white, so it is still there at 13 pixels
    k = max(0.3, 0.34 * (w - 2 * g.rw) / g.sw)
    g.stem(w / 2, g.cap * 0.34, g.cap * 0.66, b=0, t=0, w=k, tag="dot")
    g.frame(w, 0.5, 0.5)


# --------------------------------------------------------------------------
# Signs for code
# --------------------------------------------------------------------------
# In code the signs are words. They sit on one line (the middle of the figures), so that -> and
# => are level; they are as heavy as the letters; brackets are deep enough to tell ( from |;
# and a comma cannot pass for a period at 12 pixels.

def _cell(g: G) -> float:
    return g.p.mono or 600.0


def _axis(g: G) -> float:
    """The height every operator is centered on."""
    return g.cap / 2


def _lighten(g: G) -> float:
    """A width multiplier that keeps brackets and stars open in bold: 1 at a regular weight, less above."""
    return max(0.55, min(1.0, 1 - 3 * (g.sw / _cell(g) - 0.15)))


def sign(name, char):
    return MONO.add(name, char, case="figure")


@sign("plus", "+")
def plus(g):
    w = 0.74 * _cell(g)
    cy = _axis(g)
    g.bar(0, w, cy)
    g.stem(w / 2, cy - w / 2, cy + w / 2, b=0, t=0)
    g.frame(w, 0.5, 0.5)


@sign("hyphen", "-")
def hyphen(g):
    w = 0.74 * _cell(g)
    g.bar(0, w, _axis(g))
    g.frame(w, 0.5, 0.5)


@sign("equal", "=")
def equal(g):
    w = 0.74 * _cell(g)
    d = 0.086 * g.cap + 0.37 * g.hw
    g.bar(0, w, _axis(g) + d)
    g.bar(0, w, _axis(g) - d)
    g.frame(w, 0.5, 0.5)


def _chevron(g: G, s: int):
    w = 0.61 * _cell(g)
    h = 0.27 * g.cap
    cy = _axis(g)
    x0, x1 = (w, 0) if s < 0 else (0, w)
    g.path(x0, cy + h).to(x1, cy, corner=True).to(x0, cy - h).done()
    g.frame(None, 0.5, 0.5)                    # center what was drawn: the point sticks out


@sign("less", "<")
def less(g):
    _chevron(g, -1)


@sign("greater", ">")
def greater(g):
    _chevron(g, 1)


@sign("asterisk", "*")
def asterisk(g):
    r_ = 0.28 * g.cap
    cy = _axis(g)
    dx, dy = r_ * math.cos(math.radians(30)), r_ * math.sin(math.radians(30))
    k = 0.9 * _lighten(g)
    g.stem(r_, cy - r_, cy + r_, b=0, t=0, w=k)
    g.line(r_ - dx, cy - dy, r_ + dx, cy + dy, w=k)
    g.line(r_ - dx, cy + dy, r_ + dx, cy - dy, w=k)
    g.frame(2 * r_, 0.5, 0.5)


@sign("asciicircum", "^")
def asciicircum(g):
    w = 0.60 * _cell(g)
    top = g.cap * 1.04
    g.path(0, top - 0.42 * g.cap).to(w / 2, top, corner=True).to(w, top - 0.42 * g.cap).done()
    g.frame(None, 0.5, 0.5)


@sign("asciitilde", "~")
def asciitilde(g):
    w = 0.74 * _cell(g) - g.hw
    cy, h = _axis(g), 0.09 * g.cap
    (g.path(0, cy - 0.35 * h)
     .curve((0.12 * w, cy + 1.3 * h), (0.30 * w, cy + 1.3 * h), w / 2, cy)
     .curve((0.70 * w, cy - 1.3 * h), (0.88 * w, cy - 1.3 * h), w, cy + 0.35 * h)
     .done())
    g.frame(w, 0.5, 0.5)


def _tail(g: G, cx: float, d: float):
    """The tail of a comma: it leaves the dot on the right and ends well under the baseline."""
    g.path(cx + 0.14 * d, 0.45 * d, w=0.8).to(cx - 0.42 * d, -0.2 * g.cap, w=0.5).done()


@sign("period", ".")
def period(g):
    d = 1.3 * g.sw
    g.dot(d / 2, d / 2, d)
    g.frame(d, 0.5, 0.5)


@sign("colon", ":")
def colon(g):
    d = 1.3 * g.sw
    g.dot(d / 2, d / 2, d)
    g.dot(d / 2, g.xh - d / 2, d)
    g.frame(d, 0.5, 0.5)


@sign("comma", ",")
def comma(g):
    d = 1.3 * g.sw
    g.dot(d / 2, d / 2, d)
    _tail(g, d / 2, d)
    g.frame(d, 0.5, 0.5)


@sign("semicolon", ";")
def semicolon(g):
    d = 1.3 * g.sw
    g.dot(d / 2, d / 2, d)
    g.dot(d / 2, g.xh - d / 2, d)
    _tail(g, d / 2, d)
    g.frame(d, 0.5, 0.5)


def _paren(g: G, s: int):
    """A deep arc from below the baseline to above the capitals. s = 1 opens to the right."""
    k = _lighten(g)
    t = k * g.sw
    w = 0.21 * _cell(g) + t
    top, bot = g.asc + 0.03 * g.cap, 0.72 * g.desc
    cy = (top + bot) / 2
    a = 58                                     # half of the arc, in degrees
    rx = (w - t) / (1 - math.cos(math.radians(a)))
    ry = (top - bot) / 2 / math.sin(math.radians(a))
    cx = t / 2 + rx if s > 0 else w - t / 2 - rx
    a0, a1 = (180 - a, 180 + a) if s > 0 else (a, -a)
    (g.path(cx + rx * math.cos(math.radians(a0)), cy + ry * math.sin(math.radians(a0)), w=k)
     .ellipse(cx, cy, rx, ry, a0, a1, w=k)
     .done())
    lean = 0.08 * _cell(g)                     # sit closer to what the bracket holds
    if s > 0:
        g.shift(lean)
    g.frame(w + lean, 0.5, 0.5)


@sign("parenleft", "(")
def parenleft(g):
    _paren(g, 1)


@sign("parenright", ")")
def parenright(g):
    _paren(g, -1)


def _brace(g: G, s: int):
    """Two hooks that meet in a nib on the axis of the brackets. s = 1 opens to the right."""
    k = _lighten(g)
    t = k * g.sw
    w = 0.50 * _cell(g)
    top, bot = g.asc + 0.02 * g.cap, 0.72 * g.desc
    cy = (top + bot) / 2
    r_ = 0.36 * w                              # height of the four bends
    xs, x_end, x_nib = 0.5 * w, w - t / 2, t / 2
    if s < 0:
        x_end, x_nib = w - x_end, w - x_nib
    for y, d in ((top - t / 2, -1), (bot + t / 2, 1)):
        (g.path(x_end, y, w=k)
         .arc(xs, y + d * r_, "h", w=k)
         .to(xs, cy - d * r_, w=k)
         .arc(x_nib, cy, "v", w=k)
         .done())
    lean = 0.05 * _cell(g)
    if s > 0:
        g.shift(lean)
    g.frame(w + lean, 0.5, 0.5)


@sign("braceleft", "{")
def braceleft(g):
    _brace(g, 1)


@sign("braceright", "}")
def braceright(g):
    _brace(g, -1)


def _slash(g: G, s: int):
    """A slash that leans enough to stay a slash in the italic. s = 1 is /, s = -1 is the backslash."""
    w = 0.58 * _cell(g)
    top, bot = g.asc + 0.02 * g.cap, 0.62 * g.desc
    x0, x1 = (0, w) if s > 0 else (w, 0)
    g.line(x0, bot, x1, top, cut0=H, cut1=H)
    g.frame(None, 0.5, 0.5)


@sign("slash", "/")
def slash(g):
    _slash(g, 1)


@sign("backslash", "\\")
def backslash(g):
    _slash(g, -1)
