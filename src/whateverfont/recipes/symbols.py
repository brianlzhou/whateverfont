"""Currency, legal and typographic signs, more math, superscripts and fractions.

With these the basic set covers every symbol of Latin-1 (U+00A0 to U+00BF)
and the common signs around it: € £ ¥ ¢ © ® ™ § ¶ † ‡ ± ÷ ‰ ′ ″ ‚ „ and the
vulgar fractions.
"""

from __future__ import annotations

import math

from ..glyph import G, H, V, Recipes
from .accents import mark
from .figures import FIGURES, fig_advance, fig_w
from .lower import LOWER, round_box, vee
from .punct import dot_d, math_w, math_y, tail

SYMBOLS = Recipes()


def r(name, uni, case="figure"):
    return SYMBOLS.add(name, uni, case=case)


def _since(g: G):
    """Indexes to pass to :meth:`G.transform` for everything drawn after this call."""
    return len(g.strokes), len(g.shapes)


def _shrink(g: G, start: tuple, k: float, dx: float, dy: float, weight: float = 1.0):
    """Scale what was drawn since ``start`` by ``k`` about the origin, move it, and set its stroke weight."""
    g.transform((k, 0.0, 0.0, k, dx, dy), start[0], start[1])
    for s in g.strokes[start[0]:]:
        s.scale *= weight


# --------------------------------------------------------------------------
# Currency
# --------------------------------------------------------------------------

@r("Euro", 0x20AC)
def euro(g):
    w = fig_w(g)
    bar_out = g.sw * 0.55
    x0 = bar_out + g.rw / 2
    cx, cy = x0 + w * 0.5, g.cap / 2
    rx, ry = w * 0.5, (g.top(g.cap) - g.bot) / 2
    a0, a1 = 44, 316
    p0 = g.epoint(cx, cy, rx, ry, a0)
    (g.path(p0.real, p0.imag, fl=0.6)
     .ellipse(cx, cy, rx, ry, a0, a1, fl=0.6)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="c"))
    for fy in (0.40, 0.60):
        g.bar(0, cx + rx * 0.18, g.cap * fy, w=0.74)
    g.fixed_advance(fig_advance(g))


@r("sterling", 0x00A3)
def sterling(g):
    w = fig_w(g) + g.rw
    xs = w * 0.36
    top = g.top(g.cap)
    rh = w * 0.30
    hook_end = g.epoint(xs + rh, top - rh, rh, rh, 18)
    (g.path(hook_end.real, hook_end.imag, fl=0.8)
     .ellipse(xs + rh, top - rh, rh, rh, 18, 180)
     .to(xs, g.cap * 0.30)
     .curve((xs, g.cap * 0.12), (xs * 0.55, g.hw), g.sw * 0.25, g.hw / 2)
     .done(start=g.curved_cut(), end=V, tag="stem"))
    g.bar(0, w, g.hw / 2, l=0, r=0.6)
    g.bar(w * 0.10, w * 0.70, g.cap * 0.47, w=0.8)
    g.fixed_advance(fig_advance(g))


@r("yen", 0x00A5)
def yen(g):
    w = fig_w(g) + g.sw * 0.9
    yj = g.cap * 0.47
    vee(g, 0, w, g.cap, yj)
    g.stem(w / 2, 0, yj + g.sw * 0.3, t=0)
    for fy in (0.37, 0.21):
        g.bar(w * 0.14, w * 0.86, g.cap * fy, w=0.74)
    g.fixed_advance(fig_advance(g))


@r("cent", 0x00A2)
def cent(g):
    cx, cy, rx, ry = round_box(g, fig_w(g) * 0.9 + g.rw)
    p0 = g.epoint(cx, cy, rx, ry, 40)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, rx, ry, 40, 320, fl=1.0)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="c"))
    g.stem(cx, -g.xh * 0.16, g.xh * 1.16, b=0, t=0, w=0.6)
    g.fixed_advance(fig_advance(g))


@r("currency", 0x00A4)
def currency(g):
    w = math_w(g) * 0.92
    y = math_y(g)
    rad = w * 0.27 + g.sw * 0.25
    t = g.hw / g.sw
    g.ring(w / 2 - rad, y - rad, w / 2 + rad, y + rad, w_side=1.0, scale=0.7)
    for a in (45, 135, 225, 315):
        d = complex(math.cos(math.radians(a)), math.sin(math.radians(a)))
        p, q = complex(w / 2, y) + d * rad * 1.0, complex(w / 2, y) + d * (rad + w * 0.20)
        g.line(p.real, p.imag, q.real, q.imag, w=t * 0.9)
    g.fixed_advance(fig_advance(g))


# --------------------------------------------------------------------------
# Legal and typographic signs
# --------------------------------------------------------------------------

def _circled(g: G):
    """A thin ring the height of a capital. Returns (center, inner radius)."""
    d = g.cap + g.o * 2
    rad = d / 2 - g.hw * 0.4
    cx, cy = rad + g.hw * 0.4, g.cap / 2
    g.ring(cx - rad, cy - rad, cx + rad, cy + rad, w_side=1.0, scale=0.62)
    return complex(cx, cy), rad


@r("copyright", 0x00A9, "upper")
def copyright(g):
    c, rad = _circled(g)
    rx, ry = rad * 0.40, rad * 0.46
    p0 = g.epoint(c.real, c.imag, rx, ry, 42)
    (g.path(p0.real, p0.imag)
     .ellipse(c.real, c.imag, rx, ry, 42, 318)
     .done(start=g.curved_cut(), end=g.curved_cut(), scale=0.68, tag="c"))
    g.frame(None, "r", "r")


@r("registered", 0x00AE, "upper")
def registered(g):
    c, rad = _circled(g)
    h = rad * 0.98
    x0, y0 = c.real - rad * 0.30, c.imag - h / 2
    xf = c.real + rad * 0.30
    ym = y0 + h * 0.48
    g.stem(x0, y0, y0 + h, b=0, t=0, scale=0.68)
    xa = x0 + (xf - x0) * 0.42
    (g.path(x0, y0 + h - g.hw * 0.3).to(xa, y0 + h - g.hw * 0.3)
     .arc(xf, (y0 + h + ym) / 2, "h").arc(xa, ym, "v").to(x0, ym)
     .done(scale=0.68, tag="lobe"))
    g.line(xa, ym, xf + rad * 0.06, y0, b=0, t=0, cut0=H, cut1=H, scale=0.68, tag="leg")
    g.frame(None, "r", "r")


@r("trademark", 0x2122, "upper")
def trademark(g):
    h = g.cap * 0.40
    y0 = g.cap - h
    k = 0.62
    tw = h * 0.95
    g.bar(0, tw, g.cap - g.hw * k / 2, scale=k)
    g.stem(tw / 2, y0, g.cap, b=0, t=0, scale=k)
    mx = tw + h * 0.30
    mw = h * 1.12
    g.stem(mx, y0, g.cap, b=0, t=0, scale=k)
    g.stem(mx + mw, y0, g.cap, b=0, t=0, scale=k)
    t = g.hw / g.sw
    (g.path(mx, g.cap, w=t).to(mx + mw / 2, y0 + h * 0.25, corner=True, w=t).to(mx + mw, g.cap, w=t)
     .done(scale=k, miter=3, tag="m"))
    g.frame(None, 0.5, 0.5)


@r("section", 0x00A7, "upper")
def section(g):
    from .lower import s_curve
    w = g.cw * 0.86 + g.sw * 0.3
    x0 = g.rw / 2
    total = g.cap * 1.10
    y_low = -g.cap * 0.12
    hs = total * 0.60
    s_curve(g, x0, x0 + w, y_low + total - hs, y_low + total)
    s_curve(g, x0, x0 + w, y_low, y_low + hs)
    for s in g.strokes:
        s.scale *= 0.86
    g.frame(None, 0.5, 0.5)


@r("paragraph", 0x00B6, "upper")
def paragraph(g):
    w = g.cw * 1.1 + g.sw * 2
    x1 = w - g.L
    x2 = x1 - g.sw * 1.6
    yb = g.cap * 0.42
    top = g.cap
    g.stem(x1, -g.cap * 0.12, top, b=0, t=0, w=0.8)
    g.stem(x2, -g.cap * 0.12, top, b=0, t=0, w=0.8)
    # the bowl is solid
    xl = 0.0
    ym = (top + yb) / 2
    rx, ry = (x2 - xl), (top - yb) / 2
    k = 0.5523
    a, b_, c = complex(x2, top), complex(xl, ym), complex(x2, yb)
    contour = [(a, c), (c, c - rx * k, b_ - 1j * ry * k, b_), (b_, b_ + 1j * ry * k, a - rx * k, a)]
    g.shape(contour)
    g.bar(x2, x1 + g.sw / 2, top - g.hw / 2, w=1.0)
    g.frame(w, 0.4, "s")


@r("dagger", 0x2020, "upper")
def dagger(g):
    w = g.cw * 1.05
    g.stem(w / 2, -g.cap * 0.14, g.cap, b=0, t=0, w=0.8)
    g.bar(0, w, g.cap * 0.68, w=0.85)
    g.frame(w, 0.5, 0.5)


@r("daggerdbl", 0x2021, "upper")
def daggerdbl(g):
    w = g.cw * 1.05
    g.stem(w / 2, -g.cap * 0.14, g.cap, b=0, t=0, w=0.8)
    g.bar(0, w, g.cap * 0.70, w=0.85)
    g.bar(0, w, g.cap * 0.16, w=0.85)
    g.frame(w, 0.5, 0.5)


# --------------------------------------------------------------------------
# Math
# --------------------------------------------------------------------------

@r("plusminus", 0x00B1)
def plusminus(g):
    w, y = math_w(g), math_y(g) + g.cap * 0.08
    g.bar(0, w, y, w=0.785)
    g.stem(w / 2, y - w * 0.42, y + w * 0.42, b=0, t=0, w=0.785 * g.hw / g.sw)
    g.bar(0, w, y - w * 0.42 - g.cap * 0.13, w=0.785)
    g.fixed_advance(fig_advance(g))


@r("divide", 0x00F7)
def divide(g):
    w, y = math_w(g), math_y(g)
    g.bar(0, w, y, w=0.785)
    d = dot_d(g) * 0.92
    off = max(g.cap * 0.20, g.hw / 2 + d / 2 + g.sw * 0.5)
    for s in (1, -1):
        g.dot(w / 2, y + s * off, d)
    g.fixed_advance(fig_advance(g))


@r("logicalnot", 0x00AC)
def logicalnot(g):
    w, y = math_w(g), math_y(g) + g.cap * 0.06
    t = g.hw / g.sw
    (g.path(0, y, w=t).to(w - g.hw * 0.5, y, corner=True, w=t).to(w - g.hw * 0.5, y - g.cap * 0.22, w=t)
     .done(start=V, end=H, miter=4, tag="not"))
    g.fixed_advance(fig_advance(g))


@r("brokenbar", 0x00A6)
def brokenbar(g):
    x = g.L
    gap = g.cap * 0.10
    mid = g.cap * 0.45
    g.stem(x, -g.cap * 0.12, mid - gap, b=0, t=0, w=0.8)
    g.stem(x, mid + gap, g.cap * 1.02, b=0, t=0, w=0.8)
    g.frame(None, 1.2, 1.2)


@r("perthousand", 0x2030)
def perthousand(g):
    t = 0.72
    rw = g.cw * 0.46 + g.sw * 0.95
    rh = g.cap * 0.45
    gap = g.cw * 0.18 + g.sw * 0.3
    w = rw * 2 + g.cw * 0.5 + g.sw * 0.9
    g.ring(g.rw * t / 2, g.cap - rh, g.rw * t / 2 + rw, g.top(g.cap), scale=t)
    x2 = w - rw - g.rw * t / 2
    g.ring(x2, g.bot, x2 + rw, rh, scale=t)
    g.ring(x2 + rw + gap, g.bot, x2 + 2 * rw + gap, rh, scale=t)
    a, b = g.diagonal(w * 0.24, 0, w * 0.76, g.cap, "c", "c", w=0.72)
    g.line(a.real, 0, b.real, g.cap, w=0.72, cut0=H, cut1=H)
    g.frame(None, 0.5, 0.5)


@r("micro", 0x00B5, "lower")
def micro(g):
    g.base("u", LOWER["u"].fn)(g)
    g.stem(g.L, g.desc, g.xh * 0.4, b=1, t=0)


# --------------------------------------------------------------------------
# Quotes, primes, spacing accents
# --------------------------------------------------------------------------

@r("quotesinglbase", 0x201A, "lower")
def quotesinglbase(g):
    d = dot_d(g)
    tail(g, d / 2, d / 2, d)
    g.frame(None, 0.6, 0.6)


@r("quotedblbase", 0x201E, "lower")
def quotedblbase(g):
    d = dot_d(g)
    for i in range(2):
        tail(g, d / 2 + i * d * 1.75, d / 2, d)
    g.frame(None, 0.6, 0.6)


def _prime(g: G, n: int):
    step = g.sw * 1.7
    h = (g.asc - g.xh) * 1.15
    for i in range(n):
        x = i * step
        (g.path(x + g.sw * 0.55, g.asc, w=1.0).to(x, g.asc - h, w=0.55)
         .done(start=H, end=None, round_end=1.0, tag="prime"))


@r("minute", 0x2032, "lower")
def minute(g):
    _prime(g, 1)
    g.frame(None, 0.6, 0.6)


@r("second", 0x2033, "lower")
def second(g):
    _prime(g, 2)
    g.frame(None, 0.6, 0.6)


def _spacing_mark(kind: str):
    def recipe(g):
        half = g.p.n_counter * 0.27 + g.sw * 0.25
        mark(g, kind, half + g.sw * 0.2, False)
        g.frame(None, 0.5, 0.5)
    return recipe


for _name, _uni, _kind in (("dieresis", 0x00A8, "dieresis"), ("acute", 0x00B4, "acute"),
                           ("cedilla", 0x00B8, "cedilla"), ("circumflex", 0x02C6, "circumflex"),
                           ("caron", 0x02C7, "caron"), ("breve", 0x02D8, "breve"), ("dotaccent", 0x02D9, "dotaccent"),
                           ("ring", 0x02DA, "ring"), ("ogonek", 0x02DB, "ogonek"), ("tilde", 0x02DC, "tilde"),
                           ("hungarumlaut", 0x02DD, "doubleacute")):
    SYMBOLS[_name] = type(LOWER["n"])(_name, _spacing_mark(_kind), _uni, "lower")


@r("macron", 0x00AF, "lower")
def macron(g):
    half = g.p.n_counter * 0.27 + g.sw * 0.25
    g.bar(0, half * 2, g.xh * 1.16 + g.xh * 0.12, w=0.8)
    g.frame(None, 0.5, 0.5)




# --------------------------------------------------------------------------
# Ordinals, superscripts, fractions
# --------------------------------------------------------------------------

SUP_K = 0.60          # superscript size, relative to a full figure
SUP_WEIGHT = 1.12     # strokes are a little heavier than a plain scale-down


def _small_figure(g: G, name: str, x: float, y: float) -> float:
    """Draw figure ``name`` at superscript size with its left edge at ``x``, baseline ``y``.

    Returns the advance it takes.
    """
    start = _since(g)
    g.base(name, FIGURES[name].fn)(g)
    adv = g._advance or fig_advance(g)
    g._advance = None
    g._frame = None
    _shrink(g, start, SUP_K, x, y, SUP_K * SUP_WEIGHT)
    return adv * SUP_K


for _name, _uni, _fig in (("onesuperior", 0x00B9, "one"), ("twosuperior", 0x00B2, "two"),
                          ("threesuperior", 0x00B3, "three")):
    def _sup(g, fig=_fig):
        _small_figure(g, fig, 0, g.cap * (1 - SUP_K))
        g.fixed_advance(fig_advance(g) * SUP_K * 1.05)
    SYMBOLS[_name] = type(LOWER["n"])(_name, _sup, _uni, "figure")


@r("fraction", 0x2044)
def fraction(g):
    w = fig_w(g) * 0.9
    a, b = g.diagonal(0, 0, w, g.cap, "l", "r", w=0.62)
    g.line(a.real, 0, b.real, g.cap, w=0.62, cut0=H, cut1=H)
    g.frame(None, 0, 0)


def _vulgar(num: str, den: str):
    def recipe(g):
        adv = _small_figure(g, num, 0, g.cap * (1 - SUP_K))
        w = fig_w(g) * 0.9
        x_sl = adv * 0.78
        a, b = g.diagonal(x_sl, 0, x_sl + w, g.cap, "l", "r", w=0.62)
        g.line(a.real, 0, b.real, g.cap, w=0.62, cut0=H, cut1=H)
        _small_figure(g, den, x_sl + w * 0.62, 0)
        g.frame(None, 0.5, 0.5)
    return recipe


for _name, _uni, _n, _d in (("onehalf", 0x00BD, "one", "two"), ("onequarter", 0x00BC, "one", "four"),
                            ("threequarters", 0x00BE, "three", "four")):
    SYMBOLS[_name] = type(LOWER["n"])(_name, _vulgar(_n, _d), _uni, "figure")


def _ordinal(letter: str):
    def recipe(g):
        start = _since(g)
        g.base(letter, LOWER[letter].fn)(g)
        g._frame = None
        k = 0.58
        _shrink(g, start, k, 0, g.cap - g.xh * k, k * SUP_WEIGHT)
        from ..geom import contour_bounds
        b = contour_bounds(g.outlines())
        g.bar(b[0], b[2], g.cap - g.xh * k - g.cap * 0.10, w=0.62)
        g.frame(None, 0.5, 0.5)
    return recipe


for _name, _uni, _l in (("ordfeminine", 0x00AA, "a"), ("ordmasculine", 0x00BA, "o")):
    SYMBOLS[_name] = type(LOWER["n"])(_name, _ordinal(_l), _uni, "lower")


# --------------------------------------------------------------------------
# Glyphs without a code point, used by the locl feature
# --------------------------------------------------------------------------

@r("periodcentered.loclCAT", None, "lower")
def periodcentered_cat(g):
    """Catalan l·l: a middle dot with tight sides, so the two l stay one letter."""
    d = dot_d(g)
    g.dot(d / 2, g.xh * 0.52, d)
    g.frame(d, 0.15, 0.15)


@r("periodcentered.loclCAT.case", None, "upper")
def periodcentered_cat_case(g):
    """Catalan L·L: the same dot at the middle of a capital."""
    d = dot_d(g)
    g.dot(d / 2, g.cap * 0.50, d)
    g.frame(d, 0.15, 0.15)
