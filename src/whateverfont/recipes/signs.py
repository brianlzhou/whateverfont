"""More signs: currency, math, arrows, shapes, superscripts, subscripts, fractions and dashes.

With these a font from the engine is not the one in which a currency sign, a fraction or an arrow
falls back to another font. Most are built from the basic recipes: ₦ is N with two bars, ⅜ is a
small 3 and 8, ∂ is a 6 turned around. A currency sign built from a letter is drawn narrower, so it
is as wide as a figure and lines up in a column of prices.
"""

from __future__ import annotations

import math

from ..geom import contour_bounds, translate
from ..glyph import G, H, V, Recipes
from .figures import _six, fig_advance, fig_w
from .lower import LOWER, arch, s_curve, vee
from .punct import PUNCT, _dash, _quote, math_w, math_y
from .symbols import SUP_K, SUP_WEIGHT, _shrink, _since, _small_figure, _vulgar
from .upper import UPPER

SIGNS = Recipes()

#: How far below the baseline a subscript figure sits, as a share of the cap height.
SUB_DROP = 0.16


def r(name, uni, case="figure"):
    return SIGNS.add(name, uni, case=case)


def _room(g: G, want: float) -> float:
    """``want``, or less in a monospaced font, so that a drawing keeps the cell without being squeezed."""
    if g.p.mono > 0:
        return min(want, G.cell_room(g.p) - g.sw)
    return want


def _drawn(g: G, start: tuple) -> tuple:
    """The ink bounds of what was drawn since ``start``."""
    sub = G(g.p, g.name, g.case)
    sub.strokes = g.strokes[start[0]:]
    sub.shapes = g.shapes[start[1]:]
    return contour_bounds(sub.outlines())


# --------------------------------------------------------------------------
# Dashes and quotes
# --------------------------------------------------------------------------

def _same(name: str, source: Recipes):
    def recipe(g: G):
        g.base(name, source[name].fn)(g)
    return recipe


_Rec = type(LOWER["n"])
SIGNS["uni2010"] = _Rec("uni2010", _same("hyphen", PUNCT), 0x2010, "lower")
SIGNS["uni2011"] = _Rec("uni2011", _same("hyphen", PUNCT), 0x2011, "lower")


@r("figuredash", 0x2012, "lower")
def figuredash(g):
    """‒: a dash as wide as a figure, for telephone numbers."""
    g.bar(0, fig_w(g) * 0.92, g.xh * 0.50)
    g.fixed_advance(fig_advance(g))


@r("horizontalbar", 0x2015, "lower")
def horizontalbar(g):
    """―: the quotation dash, as long as an em dash."""
    _dash(g, g.cw * 2.9, g.xh * 0.50, 0.3)


def _reversed(n: int):
    def recipe(g: G):
        _quote(g, n, False)
        b = contour_bounds(g.outlines())
        g.mirror_x((b[0] + b[2]) / 2)
    return recipe


SIGNS["quotereversed"] = _Rec("quotereversed", _reversed(1), 0x201B, "lower")
SIGNS["quotedblreversed"] = _Rec("quotedblreversed", _reversed(2), 0x201F, "lower")


# --------------------------------------------------------------------------
# Superscripts, subscripts and fractions
# --------------------------------------------------------------------------

FIGURE_NAMES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
#: The superscript of each figure, which the numr, sups and frac features use too.
SUPERIORS = ("zerosuperior", "onesuperior", "twosuperior", "threesuperior", "foursuperior", "fivesuperior",
             "sixsuperior", "sevensuperior", "eightsuperior", "ninesuperior")
#: The subscript of each figure, for the subs and sinf features.
INFERIORS = tuple(n.replace("superior", "inferior") for n in SUPERIORS)


def small_advance(g: G) -> float:
    return fig_advance(g) * SUP_K * 1.05


def superior(fig: str):
    def recipe(g: G):
        _small_figure(g, fig, 0, g.cap * (1 - SUP_K))
        g.fixed_advance(small_advance(g))
    return recipe


def inferior(fig: str, y: float | None = None):
    def recipe(g: G):
        _small_figure(g, fig, 0, -g.cap * SUB_DROP if y is None else y)
        g.fixed_advance(small_advance(g))
    return recipe


for _i, _fig in enumerate(FIGURE_NAMES):
    _uni = 0x2070 if _i == 0 else 0x2070 + _i
    if _i in (1, 2, 3):
        continue                    # ¹ ² ³ are in Latin-1, with the other symbols
    SIGNS[SUPERIORS[_i]] = _Rec(SUPERIORS[_i], superior(_fig), _uni, "figure")
for _i, _fig in enumerate(FIGURE_NAMES):
    SIGNS[INFERIORS[_i]] = _Rec(INFERIORS[_i], inferior(_fig), 0x2080 + _i, "figure")

for _name, _uni, _n, _d in (("onethird", 0x2153, "one", "three"), ("twothirds", 0x2154, "two", "three"),
                            ("onefifth", 0x2155, "one", "five"), ("twofifths", 0x2156, "two", "five"),
                            ("threefifths", 0x2157, "three", "five"), ("fourfifths", 0x2158, "four", "five"),
                            ("onesixth", 0x2159, "one", "six"), ("fivesixths", 0x215A, "five", "six"),
                            ("oneeighth", 0x215B, "one", "eight"), ("threeeighths", 0x215C, "three", "eight"),
                            ("fiveeighths", 0x215D, "five", "eight"), ("seveneighths", 0x215E, "seven", "eight")):
    SIGNS[_name] = _Rec(_name, _vulgar(_n, _d), _uni, "figure")


# --------------------------------------------------------------------------
# Currency
# --------------------------------------------------------------------------

def letter_at(g: G, name: str, source: Recipes, target: float, dx: float = 0.0) -> tuple:
    """Draw letter ``name`` with narrower or wider counters, so that it is about ``target`` wide.

    Its stems keep their weight, so a sign built on a capital (₦ ₩ ₱) fits the width of a figure and
    still looks as heavy as the figures. Returns the ink bounds of the letter.
    """
    fn = g.base(name, source[name].fn)

    def width_at(k: float) -> float:
        s = G(g.p.but(width=g.p.width * k), g.name, g.case)
        s.recipes = g.recipes
        fn(s)
        b = contour_bounds(s.outlines())
        return b[2] - b[0]

    k0, w0 = 1.0, width_at(1.0)
    k = k0
    if abs(w0 - target) > 1.0:
        k1 = max(0.25, target / w0)
        for _ in range(4):
            w1 = width_at(k1)
            if abs(w1 - target) < 1.5 or abs(w1 - w0) < 0.25:
                break
            k2 = max(0.25, min(1.6, k1 + (target - w1) * (k1 - k0) / (w1 - w0)))
            k0, w0, k1 = k1, w1, k2
        k = k1
    p = g.p
    start = _since(g)
    g.p = p.but(width=p.width * k)
    fn(g)
    g.p = p
    g._frame = None
    g._advance = None
    b = _drawn(g, start)
    g.transform(translate(dx - b[0], 0.0), start[0], start[1])
    return (dx, b[1], dx + b[2] - b[0], b[3])


def _sign_width(g: G) -> float:
    """The ink width of a currency sign that fits a figure's advance."""
    return fig_w(g) + g.rw * 0.9


def _bars(g: G, x0: float, x1: float, ys, w: float = 0.74):
    for y in ys:
        g.bar(x0, x1, y, w=w)


def _figure_wide(g: G):
    """A figure's advance, or a little more for a sign that cannot be that narrow."""
    b = contour_bounds(g.outlines())
    need = (b[2] - b[0]) + 2 * g.sidebearing(0.5)
    if need <= fig_advance(g):
        g.fixed_advance(fig_advance(g))
    else:
        g.frame(None, 0.5, 0.5)


def _letter_with_bars(letter: str, ys, over: float = 0.42, w: float = 0.74):
    """A capital with horizontal bars across it that reach a little past its sides."""
    def recipe(g: G):
        out = g.sw * over
        x0, _, x1, _ = letter_at(g, letter, UPPER, _sign_width(g) - 2 * out, out)
        _bars(g, x0 - out, x1 + out, [g.cap * y for y in ys], w)
        _figure_wide(g)
    return recipe


def _letter_with_stroke(letter: str, x_at: float = 0.5, reach: float = 0.12, lean: float = 0.0, w: float = 0.62):
    """A capital crossed by a vertical stroke that reaches past its top and bottom (₲ ₵)."""
    def recipe(g: G):
        x0, _, x1, _ = letter_at(g, letter, UPPER, _sign_width(g))
        x = x0 + (x1 - x0) * x_at
        d = g.cap * lean
        g.line(x - d, -g.cap * reach, x + d, g.cap * (1 + reach), w=w, cut0=H, cut1=H, tag="stroke")
        _figure_wide(g)
    return recipe


for _name, _uni, _letter, _ys in (("uni20A6", 0x20A6, "N", (0.38, 0.62)),      # ₦ naira
                                  ("uni20A9", 0x20A9, "W", (0.38, 0.60)),      # ₩ won
                                  ("uni20B3", 0x20B3, "A", (0.30, 0.50))):     # ₳ austral
    SIGNS[_name] = _Rec(_name, _letter_with_bars(_letter, _ys), _uni, "figure")
SIGNS["uni20B2"] = _Rec("uni20B2", _letter_with_stroke("G", 0.54), 0x20B2, "figure")      # ₲ guarani
SIGNS["uni20B5"] = _Rec("uni20B5", _letter_with_stroke("C", 0.54), 0x20B5, "figure")      # ₵ cedi


@r("colonmonetary", 0x20A1)
def colonmonetary(g):
    """₡: a C with two strokes through it."""
    x0, _, x1, _ = letter_at(g, "C", UPPER, _sign_width(g))
    for x in (0.42, 0.66):
        xc = x0 + (x1 - x0) * x
        g.line(xc - g.cap * 0.05, -g.cap * 0.10, xc + g.cap * 0.05, g.cap * 1.10, w=0.56, cut0=H, cut1=H)
    _figure_wide(g)


def _small_letter(g: G, name: str, source: Recipes, k: float, x: float, y: float, weight: float = 1.0):
    """Letter ``name`` scaled by ``k``, its left edge at ``x`` and its baseline at ``y``."""
    start = _since(g)
    g.base(name, source[name].fn)(g)
    g._frame = None
    g._advance = None
    b = _drawn(g, start)
    _shrink(g, start, k, x - b[0] * k, y, k * weight)
    return x + (b[2] - b[0]) * k


@r("uni20A0", 0x20A0)
def euroarchaic(g):
    """₠: a C that holds a small E."""
    x0, b0, x1, _ = letter_at(g, "C", UPPER, _sign_width(g))
    k = 0.56
    _small_letter(g, "E", UPPER, k, x0 + (x1 - x0) * 0.40, g.cap * (1 - k) / 2, 1.25)
    _figure_wide(g)


@r("cruzeiro", 0x20A2)
def cruzeiro(g):
    """₢: a C that holds a small r."""
    x0, _, x1, _ = letter_at(g, "C", UPPER, _sign_width(g))
    k = 0.62
    _small_letter(g, "r", LOWER, k, x0 + (x1 - x0) * 0.40, g.cap * 0.14, 1.2)
    _figure_wide(g)


@r("franc", 0x20A3)
def franc(g):
    """₣: an F with a bar through its stem."""
    out = g.sw * 0.9
    x0, _, x1, _ = letter_at(g, "F", UPPER, _sign_width(g) - out, out)
    g.bar(0, x0 + g.sw * 2.2, g.cap * 0.22, w=0.74)
    _figure_wide(g)


@r("lira", 0x20A4)
def lira(g):
    """₤: the pound sign with two bars."""
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
    g.bar(w * 0.08, w * 0.68, g.cap * 0.54, w=0.74)
    g.bar(w * 0.08, w * 0.68, g.cap * 0.36, w=0.74)
    g.fixed_advance(fig_advance(g))


@r("mill", 0x20A5, "lower")
def mill(g):
    """₥: an m with a stroke through it."""
    g.base("m", LOWER["m"].fn)(g)
    b = contour_bounds(g.outlines())
    w = b[2] - b[0]
    a, c = g.diagonal(b[0] + w * 0.30, -g.xh * 0.18, b[0] + w * 0.70, g.xh * 1.18, "c", "c", w=0.62)
    g.line(a.real, a.imag, c.real, c.imag, w=0.62, cut0=H, cut1=H)
    g.frame(None, "s", "s")


def _letters(g: G, parts: list, gap: float = 0.6):
    """Letters set side by side, ``gap`` straight sidebearings apart: ₧ is P t s, ₨ is R s.

    Each part is (name, recipe set), or a function that draws it."""
    x = 0.0
    for part in parts:
        start = _since(g)
        if callable(part):
            part(g)
        else:
            name, source = part
            g.base(name, source[name].fn)(g)
        g._frame = None
        g._advance = None
        b = _drawn(g, start)
        g.transform(translate(x - b[0], 0.0), start[0], start[1])
        x += (b[2] - b[0]) + g.sidebearing("s") * gap


@r("peseta", 0x20A7)
def peseta(g):
    """₧: P t s."""
    _letters(g, [("P", UPPER), ("t", LOWER), ("s", LOWER)])
    g.frame(None, 0.5, 0.5)


@r("rupee", 0x20A8)
def rupee(g):
    """₨: R s."""
    _letters(g, [("R", UPPER), ("s", LOWER)])
    g.frame(None, 0.5, 0.5)


@r("sheqel", 0x20AA)
def sheqel(g):
    """₪: an arch whose right leg stops halfway, and the same turned over, set inside each other.

    Four stems stand at even steps: the outer two reach the baseline and the top, and each inner one
    stops short of the arch it faces."""
    k = 0.84
    w = _room(g, max(_sign_width(g) * 1.30, g.cap * 0.95))
    h = g.cap * 0.74
    xa = g.sw * k / 2
    step = (w - g.sw * k) / 3
    for turn in (False, True):
        start = _since(g)
        g.stem(xa, 0, h * 0.6, b=1, t=0)
        arch(g, xa, xa + 2 * step, foot=h * 0.34, height=h, fl=0, branch=0.6)
        if turn:
            g.rotate(180, xa + 1.5 * step, h / 2, start[0])
    for s in g.strokes:
        s.scale *= k
    _figure_wide(g)


@r("kip", 0x20AD)
def kip(g):
    """₭: a K with a bar through it."""
    out = g.sw * 0.5
    x0, _, x1, _ = letter_at(g, "K", UPPER, _sign_width(g) - out * 2, out)
    g.bar(0, x1 + out * 0.4, g.cap * 0.50, w=0.74)
    _figure_wide(g)


@r("tugrik", 0x20AE)
def tugrik(g):
    """₮: a T with two slanted bars through its stem."""
    x0, _, x1, _ = letter_at(g, "T", UPPER, _sign_width(g))
    xm = (x0 + x1) / 2
    half = (x1 - x0) * 0.30
    for y in (0.30, 0.52):
        g.line(xm - half, g.cap * (y - 0.05), xm + half, g.cap * (y + 0.05), w=0.62 * g.hw / g.sw * 1.2)
    _figure_wide(g)


def _delta(g: G):
    """Δ: a triangle on the baseline, the height of a capital."""
    w = g.capw(1.10, 1.16) + g.sw * 1.2
    fb = g.hw / 2
    pa, pc, _ = vee(g, 0, w, 0, g.cap, down=False)
    g.bar(pa.real, pc.real, fb, tag="base")


def _rho(g: G):
    """ρ: a round with a stem down from its left side."""
    from .lower import o_width
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.xh))
    g.stem(g.rw / 2, g.desc, g.xh * 0.5, b=1, t=0, w=g.p.round_weight)


@r("drachma", 0x20AF)
def drachma(g):
    """₯: Δρ, a delta and a rho side by side."""
    _letters(g, [_delta, _rho], gap=0.3)
    g.frame(None, 0.5, 0.5)


@r("peso", 0x20B1)
def peso(g):
    """₱: a P with two bars through its bowl."""
    out = g.sw * 0.9
    x0, _, x1, _ = letter_at(g, "P", UPPER, _sign_width(g) - out * 1.3, out)
    _bars(g, 0, x1 + out * 0.3, (g.cap * 0.80, g.cap * 0.63), 0.66)
    _figure_wide(g)


@r("hryvnia", 0x20B4)
def hryvnia(g):
    """₴: an S turned around, with two bars."""
    w = _sign_width(g) * 0.86
    x0 = g.rw / 2 + g.sw * 0.4
    s_curve(g, x0, x0 + w - g.rw, g.bot, g.top(g.cap))
    b = contour_bounds(g.outlines())
    g.mirror_x((b[0] + b[2]) / 2)
    _bars(g, b[0] - g.sw * 0.4, b[2] + g.sw * 0.4, (g.cap * 0.40, g.cap * 0.60), 0.66)
    _figure_wide(g)


@r("tenge", 0x20B8)
def tenge(g):
    """₸: a T with a second bar above it."""
    w = _sign_width(g)
    g.bar(0, w, g.flat_top(g.cap), w=0.9)
    yt = g.cap * 0.74
    g.bar(0, w, yt - g.hw / 2, l=0.5, r=0.5)
    g.stem(w / 2, 0, yt - g.hw * 0.5, t=0, serif1=False)
    _figure_wide(g)


@r("uni20B9", 0x20B9)
def rupeeindian(g):
    """₹: two bars on top, a bowl that turns back, and a leg."""
    w = _sign_width(g)
    ft = g.flat_top(g.cap)
    y2 = g.cap * 0.70
    yb = g.cap * 0.42
    xr = w * 0.62
    ry = (ft - yb) / 2
    g.bar(0, w, ft, r=0.5)
    g.bar(0, w, y2, w=0.86, r=0.5)
    (g.path(g.sw * 0.2, ft)
     .to(xr - ry * 0.6, ft)
     .arc(xr + ry * 0.5, (ft + yb) / 2, "h", w=g.p.round_weight)
     .arc(xr - ry * 0.6, yb, "v")
     .to(g.sw * 0.2, yb, corner=True)
     .to(w * 0.80, 0, fl=0.6)
     .done(start=V, end=H, miter=4, tag="bowl"))
    _figure_wide(g)


@r("uni20BA", 0x20BA)
def liraturkish(g):
    """₺: a stem whose foot sweeps up to the right, crossed by two slanted bars."""
    w = _sign_width(g)
    xs = w * 0.30
    fb = g.hw / 2
    (g.path(xs, g.cap, fl=1.0)
     .to(xs, fb, corner=True)
     .to(w * 0.55, fb)
     .arc(w, g.cap * 0.42, "h", w=g.p.round_weight)
     .done(start=H, end=H, tag="stem"))
    t = 0.62 * g.hw / g.sw * 1.2
    for y in (0.44, 0.64):
        g.line(xs - w * 0.24, g.cap * (y - 0.06), xs + w * 0.34, g.cap * (y + 0.06), w=t)
    _figure_wide(g)


@r("manat", 0x20BC)
def manat(g):
    """₼: an arch on two legs, with a stem from its middle."""
    w = _sign_width(g)
    rx = (w - g.sw) / 2
    cy = g.cap * 0.40
    ry = g.cap * 0.40
    cx = w / 2
    (g.path(cx - rx, 0, fl=1.0)
     .flared_from(cx - rx, cy)
     .ellipse(cx, cy, rx, ry, 180, 0)
     .flared_to(cx + rx, 0)
     .done(start=H, end=H, tag="arch"))
    g.stem(cx, g.cap * 0.28, g.cap, b=0, t=1, w=0.9, serif0=False, serif1=False)
    _figure_wide(g)


@r("ruble", 0x20BD)
def ruble(g):
    """₽: a P with a bar under its bowl."""
    out = g.sw * 1.1
    x0, _, x1, _ = letter_at(g, "P", UPPER, _sign_width(g) - out * 0.8, out)
    g.bar(0, x0 + (x1 - x0) * 0.66, g.cap * 0.24, w=0.74)
    _figure_wide(g)


@r("lari", 0x20BE)
def lari(g):
    """₾: a round open at the upper right, standing on a bar, with two stems that drop into it."""
    w = _sign_width(g)
    rx = (w - g.rw) / 2 * 0.94
    ry = (g.top(g.cap * 0.86) - g.bot) / 2
    cx, cy = g.rw / 2 + rx, g.bot + ry
    a0 = 30
    p0 = g.epoint(cx, cy, rx, ry, a0)
    (g.path(p0.real, p0.imag, fl=0.6)
     .ellipse(cx, cy, rx, ry, a0, 270)
     .to(w + g.sw * 0.3, g.bot, w=1.0)
     .done(start=g.curved_cut(), end=V, tag="round"))
    for x in (cx - rx * 0.28, cx + rx * 0.28):
        g.stem(x, cy - ry * 0.05, g.cap, b=0, t=0.4, w=0.72, serif0=False, serif1=False)
    _figure_wide(g)


@r("bitcoin", 0x20BF)
def bitcoin(g):
    """₿: a B with two short strokes above and below."""
    x0, _, x1, _ = letter_at(g, "B", UPPER, _sign_width(g) * 0.96, g.sw * 0.1)
    reach = g.cap * 0.12
    for x in (x0 + g.sw * 0.75, x0 + (x1 - x0) * 0.56):
        g.stem(x, g.cap - g.hw, g.cap + reach, b=0, t=0, w=0.6, serif0=False, serif1=False)
        g.stem(x, -reach, g.hw, b=0, t=0, w=0.6, serif0=False, serif1=False)
    _figure_wide(g)


@r("som", 0x20C0)
def som(g):
    """⃀: a C standing on a bar."""
    w = _sign_width(g)
    h = g.cap * 0.80
    lift = g.cap - h
    s = _since(g)
    x0, _, x1, _ = letter_at(g, "C", UPPER, w * 0.92)
    g.transform((1.0, 0.0, 0.0, h / g.cap, 0.0, lift), s[0], s[1])
    g.bar(x0 - g.sw * 0.1, x1 + g.sw * 0.1, g.hw / 2, w=0.86)
    _figure_wide(g)


# --------------------------------------------------------------------------
# Signs
# --------------------------------------------------------------------------

@r("numero", 0x2116, "upper")
def numero(g):
    """№: an N with a small underlined o."""
    g.base("N", UPPER["N"].fn)(g)
    w = contour_bounds(g.outlines())[2]
    k = 0.58
    start = _since(g)
    g.base("o", LOWER["o"].fn)(g)
    g._frame = None
    x = w + g.sidebearing("s") * 0.5
    _shrink(g, start, k, x, g.cap - g.xh * k, k * SUP_WEIGHT)
    b = _drawn(g, start)
    g.bar(b[0], b[2], g.cap - g.xh * k - g.cap * 0.12, w=0.62)
    g.frame(None, "s", 0.5)


@r("estimated", 0x212E)
def estimated(g):
    """℮: a round e as tall as a capital, its bar running edge to edge."""
    w = math_w(g) * 1.02
    h = g.cap * 0.76
    from .letters import _e_shape
    _e_shape(g, w, h)
    g.fixed_advance(fig_advance(g))


@r("lozenge", 0x25CA)
def lozenge(g):
    """◊: a tall diamond, drawn with the pen."""
    w = _room(g, fig_w(g) * 0.86)
    t = g.hw / g.sw * 0.95
    y0, y1 = g.cap * -0.04, g.cap * 1.04
    ym = (y0 + y1) / 2
    (g.path(w / 4, (y0 + ym) / 2, w=t)
     .to(w / 2, y0, corner=True, w=t)
     .to(w, ym, corner=True, w=t)
     .to(w / 2, y1, corner=True, w=t)
     .to(0, ym, corner=True, w=t)
     .to(w / 4, (y0 + ym) / 2, w=t)
     .close(tag="lozenge"))
    g.fixed_advance(fig_advance(g))


# --------------------------------------------------------------------------
# Math
# --------------------------------------------------------------------------

@r("partialdiff", 0x2202)
def partialdiff(g):
    """∂: a 6 turned around, with a smaller bowl."""
    x0, x1 = _six(g)
    g.mirror_x((x0 + x1) / 2)
    g.fixed_advance(fig_advance(g))


@r("uni2206", 0x2206)
def increment(g):
    """∆: a triangle, drawn with the pen."""
    w = math_w(g) * 0.98
    t = g.hw / g.sw
    fb = g.hw / 2
    top = g.cap
    pa, _ = g.diagonal(0, fb, w / 2, top, "l", "c", w=t)
    pc, _ = g.diagonal(w, fb, w / 2, top, "r", "c", w=t)
    (g.path(w / 2, fb, w=t)
     .to(pc.real, fb, corner=True, w=t)
     .to(w / 2, top - g.sw * 0.3, corner=True, apex=top, w=t)
     .to(pa.real, fb, corner=True, w=t)
     .to(w / 2, fb, w=t)
     .close(tag="delta"))
    g.fixed_advance(fig_advance(g))


@r("product", 0x220F)
def product(g):
    """∏: a tall Π, from below the baseline to the cap height."""
    w = _room(g, g.capw(1.08, 1.12) * 1.05 + 2 * g.sw)
    low = -g.cap * 0.16
    g.bar(0, w, g.flat_top(g.cap), w=1.0)
    g.stem(g.L, low, g.cap, t=0, serif1=False)
    g.stem(w - g.L, low, g.cap, t=0, serif1=False)
    g.frame(w, 0.5, 0.5)


@r("summation", 0x2211)
def summation(g):
    """∑: a tall Σ."""
    w = _room(g, g.capw(1.0, 1.04) * 1.05 + g.sw)
    low = -g.cap * 0.16
    ft, fb = g.flat_top(g.cap), low + g.hw / 2
    ym = (g.cap + low) / 2
    xm = w * 0.52
    (g.path(w, ft, fl=0.6)
     .to(g.sw * 0.3, ft, corner=True)
     .to(xm, ym, corner=True, w=1.0)
     .to(g.sw * 0.3, fb, corner=True)
     .to(w, fb, fl=0.6)
     .done(start=V, end=V, miter=4, tag="sigma"))
    g.frame(w, 0.5, 0.5)


@r("radical", 0x221A)
def radical(g):
    """√: a short stroke down, and a long one up to the top."""
    w = math_w(g)
    # One width along the stroke: the pen makes the long stroke thinner than the short one. A width
    # that changed from node to node would make a curve of a side in some masters and not in others.
    (g.path(0, g.cap * 0.42, w=0.82)
     .to(w * 0.16, g.cap * 0.46, corner=True, w=0.82)
     .to(w * 0.40, 0, corner=True, apex=-g.o, w=0.82)      # the point is cut at the overshoot
     .to(w, g.cap * 1.04, w=0.82)
     .done(start=V, end=H, miter=4, tag="radical"))
    g.fixed_advance(fig_advance(g))


@r("infinity", 0x221E)
def infinity(g):
    """∞: two loops that cross in the middle."""
    k = 0.86                                 # a little lighter than a letter, so the crossing stays open
    w = _room(g, max(math_w(g) * 1.30, g.cap * 0.80))
    y = math_y(g)
    h = g.cap * 0.46
    ry = (h - g.hw * k) / 2
    rx = (w - g.rw * k) / 4
    t = g.hw / g.sw
    m = w / 2
    for s in (-1, 1):
        c = m + s * rx                       # the middle of the loop
        xo = m + s * 2 * rx                  # its outer side
        # from the outer side round the bottom into the crossing, and out of it round the top
        (g.path(xo, y, w=g.p.round_weight)
         .arc(c, y - ry, "v", w=t)
         .curve((c - s * rx * 0.50, y - ry), (m + s * rx * 0.40, y - ry * 0.62), m, y, w=t * 0.95, corner=True)
         .curve((m + s * rx * 0.40, y + ry * 0.62), (c - s * rx * 0.50, y + ry), c, y + ry, w=t)
         .arc(xo, y, "h", w=g.p.round_weight)
         .close(scale=k, tag="loop"))
    g.fixed_advance(fig_advance(g))


@r("integral", 0x222B)
def integral(g):
    """∫: a long stroke with a hook at each end."""
    rx = g.cw * 0.26
    top = g.top(g.asc + 30)
    low = g.desc + g.hw / 2
    ry = g.cap * 0.10
    x = rx + g.L + g.cw * 0.1
    end_t = 90 - 40
    end_b = -(90 + 40)
    pb = g.epoint(x - rx, low + ry, rx, ry, end_b)
    (g.path(pb.real, pb.imag, fl=0.8)
     .ellipse(x - rx, low + ry, rx, ry, end_b, 0)
     .to(x, top - ry)
     .ellipse(x + rx, top - ry, rx, ry, 180, end_t, fl=0.8)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="integral"))
    g.frame(None, 0.5, 0.5)


def _tilde(g: G, w: float, y: float):
    a = g.cap * 0.075
    t = g.hw / g.sw
    (g.path(0, y - a * 0.6, w=t * 0.9)
     .curve((w * 0.12, y + a * 1.9), (w * 0.34, y + a * 1.5), w * 0.5, y, w=t * 1.2)
     .curve((w * 0.66, y - a * 1.5), (w * 0.88, y - a * 1.9), w, y + a * 0.6, w=t * 0.9)
     .done(tag="tilde"))


@r("approxequal", 0x2248)
def approxequal(g):
    w, y = math_w(g), math_y(g)
    gap = g.cap * 0.115
    _tilde(g, w, y + gap)
    _tilde(g, w, y - gap)
    g.fixed_advance(fig_advance(g))


@r("notequal", 0x2260)
def notequal(g):
    w, y = math_w(g), math_y(g)
    gap = g.cap * 0.105
    g.bar(0, w, y + gap, w=0.785)
    g.bar(0, w, y - gap, w=0.785)
    a, b = g.diagonal(w * 0.28, y - w * 0.40, w * 0.72, y + w * 0.40, "c", "c", w=0.72)
    g.line(a.real, a.imag, b.real, b.imag, w=0.72, cut0=H, cut1=H)
    g.fixed_advance(fig_advance(g))


def _less_equal(g: G, s: int):
    w, y = math_w(g), math_y(g) + g.cap * 0.07
    h = w * 0.34
    t = g.hw / g.sw
    x_open, x_tip = (w, g.hw * 0.6) if s < 0 else (0, w - g.hw * 0.6)
    (g.path(x_open, y + h, w=t)
     .to(x_tip, y, corner=True, w=t)
     .to(x_open, y - h, w=t)
     .done(miter=4, tag="angle"))
    g.bar(0, w, y - h - g.cap * 0.14, w=0.785)
    g.fixed_advance(fig_advance(g))


@r("lessequal", 0x2264)
def lessequal(g):
    _less_equal(g, -1)


@r("greaterequal", 0x2265)
def greaterequal(g):
    _less_equal(g, 1)


# --------------------------------------------------------------------------
# Arrows
# --------------------------------------------------------------------------

def _arrow(g: G, both: bool = False):
    """A horizontal arrow that points left, on the axis of the math signs. Returns its middle."""
    w = _room(g, max(math_w(g) * 1.30, g.cap * 0.66))
    y = math_y(g)
    h = min(w * 0.34, g.cap * 0.28)
    t = g.hw / g.sw
    for side in ((0, 1), (w, -1)) if both else ((0, 1),):
        x, s = side
        (g.path(x + s * h, y + h, w=t)
         .to(x + s * g.hw * 0.25, y, corner=True, w=t)
         .to(x + s * h, y - h, w=t)
         .done(miter=4, tag="head"))
    g.bar(g.hw * 0.6, w - (g.hw * 0.6 if both else 0.0), y, w=0.86)
    return complex(w / 2, y)


def _arrow_recipe(angle: float, both: bool = False):
    """An arrow turned ``angle`` degrees from pointing left (90 turns it to point down)."""
    def recipe(g: G):
        c = _arrow(g, both)
        if angle:
            g.rotate(angle, c.real, c.imag)
        g.frame(None, 0.6, 0.6)
    return recipe


for _name, _uni, _angle, _both in (("arrowleft", 0x2190, 0, False), ("arrowup", 0x2191, -90, False),
                                   ("arrowright", 0x2192, 180, False), ("arrowdown", 0x2193, 90, False),
                                   ("arrowboth", 0x2194, 0, True), ("arrowupdn", 0x2195, 90, True),
                                   ("arrowupleft", 0x2196, -45, False), ("arrowupright", 0x2197, -135, False),
                                   ("arrowdownright", 0x2198, 135, False), ("arrowdownleft", 0x2199, 45, False)):
    SIGNS[_name] = _Rec(_name, _arrow_recipe(_angle, _both), _uni, "figure")


# --------------------------------------------------------------------------
# Marks and shapes
# --------------------------------------------------------------------------

def _shape_size(g: G) -> float:
    """The side of a square or the width of a round: about two thirds of the cap height, a little
    less in a condensed family."""
    return _room(g, g.cap * 0.70 * (0.8 + 0.2 * min(1.0, g.p.width)))


def _corner(g: G, size: float) -> float:
    """How round the corners of a filled shape are: the family's roundness, at a small scale."""
    return size * 0.10 * g.p.roundness


def _filled(g: G, pts: list, radius: float):
    """A filled polygon (clockwise) with round corners. Every corner gets a radius, even 0, so the
    outline has the same points in every master of a variable font whose roundness changes."""
    n = len(pts)
    g.shape([(pts[i], pts[(i + 1) % n]) for i in range(n)], [radius] * n)


@r("checkmark", 0x2713)
def checkmark(g):
    w = _room(g, g.cap * 0.86)
    (g.path(0, g.cap * 0.42, w=0.95)
     .to(w * 0.36, g.cap * 0.04, corner=True, apex=-g.o, w=0.95)
     .to(w, g.cap * 0.86, w=0.95)
     .done(start=H, end=H, miter=4, tag="check"))
    g.frame(None, 0.5, 0.5)


@r("ballotx", 0x2717)
def ballotx(g):
    w = _room(g, g.cap * 0.72)
    h = g.cap * 0.78
    y0 = g.cap * 0.04
    for a, b in ((complex(0, y0), complex(w, y0 + h)), (complex(0, y0 + h), complex(w, y0))):
        g.line(a.real, a.imag, b.real, b.imag, w=0.86, cut0=H, cut1=H, tag="x")
    g.frame(None, 0.5, 0.5)


def _star_points(cx: float, cy: float, ro: float, ri: float) -> list:
    pts = []
    for i in range(10):
        a = math.radians(90 + 36 * i)
        rad = ro if i % 2 == 0 else ri
        pts.append(complex(cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts[::-1]                        # clockwise


def _star_size(g: G) -> tuple:
    ro = _room(g, g.cap * 0.82) / 2 / math.cos(math.radians(18))
    return ro, ro * 0.42


@r("blackstar", 0x2605)
def blackstar(g):
    ro, ri = _star_size(g)
    cy = math_y(g) + ro * 0.06
    _filled(g, _star_points(ro, cy, ro, ri), _corner(g, ro))
    g.frame(None, 0.5, 0.5)


@r("whitestar", 0x2606)
def whitestar(g):
    ro, ri = _star_size(g)
    cy = math_y(g) + ro * 0.06
    t = g.hw / g.sw * 0.9
    pts = _star_points(ro, cy, ro - g.hw * 0.4, ri)[::-1]
    start = (pts[0] + pts[1]) / 2
    pb = g.path(start.real, start.imag, w=t)
    for q in pts[1:] + pts[:1]:
        pb.to(q.real, q.imag, corner=True, w=t)
    pb.to(start.real, start.imag, w=t).close(tag="star")
    g.frame(None, 0.5, 0.5)


@r("heart", 0x2665)
def heart(g):
    s = _shape_size(g) * 1.04
    cx, y0 = s / 2, math_y(g) - s * 0.48
    top = y0 + s * 0.92
    a = complex(cx, y0)                     # the point
    b = complex(0, y0 + s * 0.62)           # the left side
    c = complex(cx * 0.5, top)              # the top of the left lobe
    d = complex(cx, y0 + s * 0.74)          # the notch
    e = complex(s - cx * 0.5, top)
    f = complex(s, y0 + s * 0.62)
    k = 0.55
    contour = [
        (a, a + complex(-s * 0.18, s * 0.16), b + complex(0, -s * 0.22), b),
        (b, b + complex(0, s * 0.20), c + complex(-cx * 0.5 * k, 0), c),
        (c, c + complex(cx * 0.5 * k, 0), d + complex(-s * 0.02, s * 0.12), d),
        (d, d + complex(s * 0.02, s * 0.12), e + complex(-cx * 0.5 * k, 0), e),
        (e, e + complex(cx * 0.5 * k, 0), f + complex(0, s * 0.20), f),
        (f, f + complex(0, -s * 0.22), a + complex(s * 0.18, s * 0.16), a),
    ]
    g.shape(contour, [_corner(g, s) * 0.6, 0, 0, s * 0.03, 0, 0])
    g.frame(None, 0.5, 0.5)


def _circle_contour(cx: float, cy: float, rad: float) -> list:
    from ..outline import circle
    return circle(cx, cy, rad)


@r("blackcircle", 0x25CF)
def blackcircle(g):
    rad = _shape_size(g) / 2
    g.shape(_circle_contour(rad, math_y(g), rad))
    g.frame(None, 0.5, 0.5)


@r("whitecircle", 0x25CB)
def whitecircle(g):
    s = _shape_size(g)
    t = g.sw * 0.8
    y = math_y(g)
    g.ring(t / 2, y - s / 2 + t / 2, s - t / 2, y + s / 2 - t / 2, w_side=1.0, scale=0.8, tag="ring")
    g.frame(None, 0.5, 0.5)


@r("blacksquare", 0x25A0)
def blacksquare(g):
    s = _shape_size(g)
    y = math_y(g)
    _filled(g, [complex(0, y - s / 2), complex(0, y + s / 2), complex(s, y + s / 2), complex(s, y - s / 2)],
            _corner(g, s))
    g.frame(None, 0.5, 0.5)


@r("whitesquare", 0x25A1)
def whitesquare(g):
    s = _shape_size(g)
    y = math_y(g)
    h = g.sw * 0.4
    x0, x1, y0, y1 = h, s - h, y - s / 2 + h, y + s / 2 - h
    (g.path((x0 + x1) / 2, y0, w=0.8)
     .to(x0, y0, corner=True, w=0.8)
     .to(x0, y1, corner=True, w=0.8)
     .to(x1, y1, corner=True, w=0.8)
     .to(x1, y0, corner=True, w=0.8)
     .to((x0 + x1) / 2, y0, w=0.8)
     .close(tag="square"))
    g.frame(None, 0.5, 0.5)


def _triangle(g: G, up: bool):
    s = _shape_size(g) * 1.06
    h = s * 0.90
    y = math_y(g)
    lo, hi = y - h / 2, y + h / 2
    if up:
        pts = [complex(0, lo), complex(s / 2, hi), complex(s, lo)]
    else:
        pts = [complex(0, hi), complex(s, hi), complex(s / 2, lo)]
    _filled(g, pts, _corner(g, s) * 0.8)
    g.frame(None, 0.5, 0.5)


@r("triagup", 0x25B2)
def triagup(g):
    _triangle(g, True)


@r("triagdn", 0x25BC)
def triagdn(g):
    _triangle(g, False)


@r("blackdiamond", 0x25C6)
def blackdiamond(g):
    s = _shape_size(g) * 1.12
    y = math_y(g)
    _filled(g, [complex(0, y), complex(s / 2, y + s / 2), complex(s, y), complex(s / 2, y - s / 2)],
            _corner(g, s))
    g.frame(None, 0.5, 0.5)
