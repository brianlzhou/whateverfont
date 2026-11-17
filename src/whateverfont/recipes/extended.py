"""Latin letters beyond the accented ones: Æ æ Œ œ ß ẞ Ð ð Þ þ Đ đ Ł ł Ħ ħ ȷ.

Most are built from the basic recipes: æ is a and e, Đ is D with a bar.
"""

from __future__ import annotations

from ..geom import contour_bounds, translate
from ..glyph import G, H, V, Recipes
from .lower import LOWER, _bowl_width, bowl, diagonal_slab, n_width, o_width
from .upper import UPPER, _lobe, bar_y
from .upper import o_width as cap_o_width

EXTENDED = Recipes()


def r(name, uni, case="lower"):
    return EXTENDED.add(name, uni, case=case)


def _mark(g: G):
    return len(g.strokes), len(g.shapes)


def _width_so_far(g: G) -> float:
    if g._frame is not None and g._frame[0] is not None:
        return g._frame[0]
    b = contour_bounds(g.outlines())
    return b[2] if b else 0.0


def _then(g: G, name: str, source, dx: float):
    """Draw recipe ``name`` from ``source`` moved ``dx`` to the right."""
    start = _mark(g)
    g.base(name, source[name].fn)(g)
    g.transform(translate(dx, 0.0), start[0], start[1])


# --------------------------------------------------------------------------
# Ligature letters
# --------------------------------------------------------------------------

def _beaks(g: G, w: float, top: float, mid: float):
    """The beaks on the arms of the E in Æ and Œ, in a family with serifs."""
    g.beak(w * top, g.flat_top(g.cap), down=True)
    g.beak(w * mid, bar_y(g), down=True, length=0.45)
    g.beak(w * mid, bar_y(g), down=False, length=0.45)
    g.beak(w, g.hw / 2, down=False)


@r("AE", 0x00C6, "upper")
def AE(g):
    xs = g.L + g.capw(1.04, 1.12)            # the stem the A and the E share
    # A heavy, narrow Æ needs room for the white between the diagonal and the stem.
    xs = max(xs, 2 * g.dx(complex(xs, g.cap)) + g.sw * 1.0)
    arm = g.capw(0.86, 0.66)
    w = xs + g.sw / 2 + arm
    pa, pb = g.diagonal(0, 0, xs, g.cap, "l", "c")
    g.line(pa.real, 0, pb.real, g.cap, b=1, t=0, cut0=H, cut1=H, tag="diag",
           round0=0.0 if g.serifed else None)
    g.stem(xs, 0, g.cap, b=1, t=0, serif0=False)
    g.bar(pb.real - g.sw * 0.5, w * 0.97, g.flat_top(g.cap), l=0, r=0.7)
    g.bar(xs, w * 0.90, bar_y(g), r=0.5)
    g.bar(xs, w, g.hw / 2, r=0.7)
    _beaks(g, w, 0.97, 0.90)
    yb = g.cap * 0.29
    xl = pa.real + (pb.real - pa.real) * yb / g.cap
    g.bar(xl, xs, yb)
    diagonal_slab(g, pa.real, 0, pb - pa, top=False)
    g.frame(w, "d", 0.45)


@r("OE", 0x0152, "upper")
def OE(g):
    wo = cap_o_width(g) * 0.86
    g.ring(g.rw / 2, g.bot, wo - g.rw / 2, g.top(g.cap))
    xs = wo - g.L
    arm = g.capw(0.80, 0.62)
    w = xs + g.sw / 2 + arm
    g.stem(xs, 0, g.cap, b=0, t=0)
    g.bar(xs, w * 0.97, g.flat_top(g.cap), r=0.7)
    g.bar(xs, w * 0.90, bar_y(g), r=0.5)
    g.bar(xs, w, g.hw / 2, r=0.7)
    _beaks(g, w, 0.97, 0.90)
    g.frame(w, "r", 0.45)


@r("ae", 0x00E6)
def ae(g):
    # Always the two-story a: a round a joined to an e reads as œ.
    p = g.p
    g.p = p.but(a_story=2)
    g.base("a", LOWER["a"].fn)(g)
    g.p = p
    wa = _width_so_far(g)
    _then(g, "e", LOWER, wa - g.sw * 1.25)
    g.frame(None, 0.8, 0.36)


@r("oe", 0x0153)
def oe(g):
    g.base("o", LOWER["o"].fn)(g)
    wo = _width_so_far(g)
    _then(g, "e", LOWER, wo - g.rw * 1.1)
    g.frame(None, "r", 0.36)


# --------------------------------------------------------------------------
# Sharp s, eth, thorn
# --------------------------------------------------------------------------

@r("germandbls", 0x00DF)
def germandbls(g):
    w = n_width(g) * 0.98
    x0 = g.L
    top = g.top(g.asc)
    xr = w - g.rw / 2
    r_top = (xr - x0) * 0.46
    xw = x0 + (xr - x0) * 0.42
    yw = g.xh * 0.70
    (g.path(x0, 0, fl=1.0)
     .flared_from(x0, g.asc * 0.62)
     .to(x0, top - r_top)
     .arc(x0 + r_top, top, "v")
     .arc(x0 + r_top * 2, top - r_top * 1.05, "h", w=g.p.round_weight)
     .curve((x0 + r_top * 2, top - r_top * 1.9), (xw + (xr - xw) * 0.2, yw + g.xh * 0.12), xw, yw, w=0.8)
     .curve((xr, yw), (xr, g.xh * 0.55), xr, g.xh * 0.32, w=g.p.round_weight)
     .curve((xr, g.xh * 0.08), (xw + (xr - xw) * 0.5, g.bot), xw, g.bot)
     .done(start=H, end=V, round_start=0.0 if g.serifed else None, tag="sharp"))
    g.slab(x0, 0, 1.0, 0.5, half=g.sw / 2 * g.fl)
    g.frame(w + g.rw * 0.1, "s", "r")


@r("eth", 0x00F0)
def eth(g):
    w = o_width(g)
    h = g.xh * 1.04
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(h))
    cx = w / 2
    x_top = cx - w * 0.18
    (g.path(cx - w * 0.30, g.top(h) - g.hw * 0.2)
     .curve((cx + w * 0.42, h * 1.05), (cx + w * 0.30, g.asc * 0.95), x_top, g.asc, w=0.9)
     .done(start=H, end=None, tag="eth"))
    g.line(cx - w * 0.22, g.asc * 0.70, cx + w * 0.36, g.asc * 0.90, w=0.62 * g.hw / g.sw * 1.3, tag="bar")
    g.frame(w, "r", "r")


@r("thorn", 0x00FE)
def thorn(g):
    w = _bowl_width(g)
    g.stem(g.L, g.desc, g.asc)
    bowl(g, g.L, w - g.rw / 2)
    g.frame(w, "s", "r")


@r("Thorn", 0x00DE, "upper")
def Thorn(g):
    w = g.sw + g.rw + g.capw(0.80, 0.62)
    g.stem(g.L, 0, g.cap)
    _lobe(g, g.L, w - g.rw / 2, g.cap * 0.78, g.cap * 0.20)
    g.frame(w, "s", 0.45)


# --------------------------------------------------------------------------
# Barred letters
# --------------------------------------------------------------------------

def _barred_D(g: G):
    over = g.sw * 0.75
    _then(g, "D", UPPER, over)
    g.bar(0, g.L + over + g.sw * 1.6, g.cap * 0.5, w=0.9)
    g.frame(None, 0.5, "r")


@r("Eth", 0x00D0, "upper")
def Eth(g):
    _barred_D(g)


@r("Dcroat", 0x0110, "upper")
def Dcroat(g):
    _barred_D(g)


@r("dcroat", 0x0111)
def dcroat(g):
    g.base("d", LOWER["d"].fn)(g)
    w = _width_so_far(g)
    xs = w - g.L
    g.bar(xs - g.sw * 1.6, xs + g.sw * 1.1, g.asc * 0.80, w=0.9)
    g.frame(None, "r", 0.5)


def _slash(g: G, x: float, y: float, span: float):
    t = g.hw / g.sw
    g.line(x - span * 0.55, y - span * 0.32, x + span * 0.75, y + span * 0.42, w=t * 1.15, tag="slash")


@r("Lslash", 0x0141, "upper")
def Lslash(g):
    over = g.sw * 0.7
    _then(g, "L", UPPER, over)
    _slash(g, g.L + over, g.cap * 0.46, g.sw * 2.2)
    g.frame(None, 0.4, 0.2)


@r("lslash", 0x0142)
def lslash(g):
    over = g.sw * 0.7
    _then(g, "l", LOWER, over)
    _slash(g, g.L + over, g.asc * 0.55, g.sw * 2.2)
    g.frame(None, 0.4, 0.4)


@r("Hbar", 0x0126, "upper")
def Hbar(g):
    over = g.sw * 0.55
    _then(g, "H", UPPER, over)
    w = _width_so_far(g)
    g.bar(0, w + over, g.cap * 0.76, w=0.85)
    g.frame(None, 0.4, 0.4)


@r("hbar", 0x0127)
def hbar(g):
    over = g.sw * 0.7
    _then(g, "h", LOWER, over)
    g.bar(0, g.L + over + g.sw * 1.5, g.asc * 0.80, w=0.85)
    g.frame(None, 0.4, 0.94)


@r("dotlessj", 0x0237)
def dotlessj(g):
    n = len(g.shapes)
    g.base("j", LOWER["j"].fn)(g)
    del g.shapes[n:]          # the j without its dot


@r("uni1E9E", 0x1E9E, "upper")
def germandbls_cap(g):
    w = g.sw + g.rw + g.capw(0.98, 0.86)
    x0 = g.L
    ft = g.flat_top(g.cap)
    r_ = (w - x0) * 0.20
    xd = w * 0.84
    xm = x0 + (w - x0) * 0.44
    ym = g.cap * 0.56
    xr = w - g.rw / 2
    (g.path(x0, 0, fl=1.0)
     .flared_from(x0, g.cap * 0.5)
     .to(x0, ft - r_)
     .arc(x0 + r_, ft, "v")
     .to(xd, ft, corner=True)
     .to(xm, ym, corner=True)
     .curve((xm + (xr - xm) * 0.95, ym), (xr, ym - g.cap * 0.06), xr, g.cap * 0.28, w=g.p.round_weight)
     .arc(xm, g.bot, "v")
     .to(x0 + g.sw * 1.2, g.bot)
     .done(start=H, end=V, round_start=0.0 if g.serifed else None, miter=4, tag="sharp"))
    g.slab(x0, 0, 1.0, 0.5, half=g.sw / 2 * g.fl)
    g.frame(w, "s", "r")
