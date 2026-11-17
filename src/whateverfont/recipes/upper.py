"""Latin capital recipes."""

from __future__ import annotations

import math

from ..glyph import G, H, V, Recipes
from .lower import apex_cut, crowded, diagonal_slab, open_angle, round_box, s_curve, vee, x_strokes

UPPER = Recipes()


def r(name, uni=None):
    return UPPER.add(name, uni if uni is not None else name, case="upper")


def h_width(g: G) -> float:
    return 2 * g.sw + g.capw(1.02, 1.04)


def o_width(g: G) -> float:
    return 2 * g.rw + g.capw(1.16, 1.42)


def bar_y(g: G, at: float = 0.525) -> float:
    return g.cap * at


# --------------------------------------------------------------------------
# Stems and bars: I H E F L T
# --------------------------------------------------------------------------

@r("I")
def I(g):
    g.stem(g.L, 0, g.cap)
    g.frame(g.sw)


@r("H")
def H_(g):
    w = h_width(g)
    g.stem(g.L, 0, g.cap)
    g.stem(w - g.L, 0, g.cap)
    g.bar(g.L, w - g.L, bar_y(g))
    g.frame(w)


def _arms(g: G, w: float, top=True, mid=True, bottom=True, mid_len=0.88, top_len=0.96):
    """The arms of E, F and L. In a family with serifs each arm ends in a beak."""
    if top:
        g.bar(g.L, w * top_len, g.flat_top(g.cap), r=0.7)
        g.beak(w * top_len, g.flat_top(g.cap), down=True)
    if mid:
        g.bar(g.L, w * mid_len, bar_y(g), r=0.5)
        g.beak(w * mid_len, bar_y(g), down=True, length=0.45)
        g.beak(w * mid_len, bar_y(g), down=False, length=0.45)
    if bottom:
        g.bar(g.L, w, g.hw / 2, r=0.7)
        g.beak(w, g.hw / 2, down=False)


@r("E")
def E(g):
    w = g.sw + g.capw(0.92, 0.70)
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0), serif1=(1.0, 0))
    _arms(g, w)
    g.frame(w, "s", 0.45)


@r("F")
def F(g):
    w = g.sw + g.capw(0.86, 0.66)
    g.stem(g.L, 0, g.cap, serif1=(1.0, 0))
    _arms(g, w, bottom=False, top_len=1.0, mid_len=0.86)
    g.frame(w, "s", 0.3)


@r("L")
def L(g):
    w = g.sw + g.capw(0.84, 0.66)
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0))
    _arms(g, w, top=False, mid=False)
    g.frame(w, "s", 0.2)


@r("T")
def T(g):
    w = g.capw(1.22, 1.30) + g.sw
    g.bar(0, w, g.flat_top(g.cap), l=0.7, r=0.7)
    g.stem(w / 2, 0, g.cap, t=0)
    g.beak(0, g.flat_top(g.cap), side=-1, down=True)
    g.beak(w, g.flat_top(g.cap), side=1, down=True)
    g.frame(w, 0.25, 0.25)


# --------------------------------------------------------------------------
# Diagonals: A V W M N K X Y Z
# --------------------------------------------------------------------------

@r("A")
def A(g):
    w = g.capw(1.28, 1.36) + g.sw * 1.6
    pa, pc, ya = vee(g, 0, w, 0, g.cap, down=False)
    # crossbar between the two legs
    yb = g.cap * 0.29
    t = (yb - 0) / (ya - 0)
    xl = pa.real + (w / 2 - pa.real) * t
    xr = pc.real + (w / 2 - pc.real) * t
    g.bar(xl, xr, yb)
    g.frame(w, "d", "d")


@r("V")
def V_(g):
    w = g.capw(1.24, 1.32) + g.sw * 1.6
    vee(g, 0, w, g.cap, 0)
    g.frame(w, "d", "d")


@r("W")
def W(g):
    # in a cell crowded by slabs the middle stops lower and the inner strokes are lighter
    tight = crowded(g)
    double_vee(g, 0.70 if tight else None, 0.76 if tight else 1.0)


def double_vee(g: G, middle: float | None = None, thin: float = 1.0):
    """The W. ``middle`` is where the middle point stops, as a share of the cap height (None: at the
    top), and ``thin`` the weight of the two inner strokes there. A monospaced cell needs both."""
    w = g.capw(2.02, 2.18) + g.sw * 2.6
    xb1, xb2, xt = w * 0.27, w * 0.73, w * 0.5
    cut_b = apex_cut(g, 0, True)
    cut_t = apex_cut(g, g.cap, False) if middle is None else g.cap * middle
    pa, _ = g.diagonal(0, g.cap, xb1, 0, "l", "c")
    pe, _ = g.diagonal(w, g.cap, xb2, 0, "r", "c")
    yt = g.cap - g.sw
    for _ in range(3):
        yb1 = g.apex_y(xb1, pa, complex(xt, yt), cut_b)
        yb2 = g.apex_y(xb2, complex(xt, yt), pe, cut_b)
        yt = g.apex_y(xt, complex(xb1, yb1), complex(xb2, yb2), cut_t, w=thin)
    (g.path(pa.real, g.cap, fl=1.0)
     .flared_from(xb1, yb1, corner=True, apex=cut_b)
     .to(xt, yt, corner=True, apex=cut_t, w=thin)
     .to(xb2, yb2, corner=True, apex=cut_b)
     .flared_to(pe.real, g.cap)
     .done(start=H, end=H, round_start=0.0 if g.serifed else None, round_end=0.0 if g.serifed else None,
           tag="w"))
    diagonal_slab(g, pa.real, g.cap, complex(xb1, yb1) - pa, top=True)
    diagonal_slab(g, pe.real, g.cap, complex(xb2, yb2) - pe, top=True)
    g.frame(w, "d", "d")


@r("M")
def M(g):
    # in a cell crowded by slabs the V stops above the baseline, and its strokes are lighter
    tight = crowded(g)
    em(g, 0.26 if tight else None, 0.72 if tight else 1.0, 0.8 if tight else 1.0)


def em(g: G, vertex: float | None = None, thin: float = 1.0, out: float = 1.0):
    """The M. ``vertex`` is where its V stops, as a share of the cap height (None: on the baseline),
    ``thin`` the weight of the V at its point, and ``out`` the length of the outer slabs."""
    w = 2 * g.sw + g.capw(1.52, 1.62)
    R = w - g.L
    xm = w / 2
    cut_b = apex_cut(g, 0, True) if vertex is None else g.cap * vertex
    ym = g.cap * 0.10
    for _ in range(3):
        yl = g.apex_y(g.L, complex(g.L, 0), complex(xm, ym), g.cap, flat=g.sw * 1.04)
        ym = g.apex_y(xm, complex(g.L, yl), complex(R, yl), cut_b, w=thin)
    square = 0.0 if g.serifed else None
    (g.path(g.L, 0, fl=1.0)
     .flared_from(g.L, yl, corner=True, apex=g.cap)
     .to(xm, ym, corner=True, apex=cut_b, w=thin)
     .to(R, yl, corner=True, apex=g.cap)
     .flared_to(R, 0)
     .done(start=H, end=H, round_start=square, round_end=square, miter=6, tag="m"))
    half = g.sw / 2 * g.fl
    g.slab(g.L, 0, out, 1, half=half)
    g.slab(R, 0, 1, out, half=half)
    g.slab(g.L, g.cap, out, 0, top=True)           # the outer corners of the top
    g.slab(R, g.cap, 0, out, top=True)
    g.frame(w)


@r("N")
def N(g):
    w = 2 * g.sw + g.capw(1.08, 1.12)
    R = w - g.L
    yl, yr = g.cap - g.sw, g.sw
    for _ in range(3):
        yl = g.apex_y(g.L, complex(g.L, 0), complex(R, yr), g.cap, flat=g.sw * 1.04)
        yr = g.apex_y(R, complex(g.L, yl), complex(R, g.cap), 0, flat=g.sw * 1.04)
    square = 0.0 if g.serifed else None
    (g.path(g.L, 0, fl=1.0)
     .flared_from(g.L, yl, corner=True, apex=g.cap)
     .to(R, yr, corner=True, apex=0)
     .flared_to(R, g.cap)
     .done(start=H, end=H, round_start=square, round_end=square, miter=6, tag="n"))
    half = g.sw / 2 * g.fl
    g.slab(g.L, 0, 1, 1, half=half)
    g.slab(g.L, g.cap, 1, 0, top=True)
    g.slab(R, g.cap, 1, 1, top=True, half=half)
    g.frame(w)


@r("K")
def K(g):
    w = g.sw + g.capw(1.06, 1.08) + g.sw * 0.3
    g.stem(g.L, 0, g.cap)
    pa, pb = g.diagonal(g.sw * 0.75, g.cap * 0.40, w * 0.96, g.cap, "c", "r")
    square = 0.0 if g.serifed else None
    g.line(pa.real, pa.imag, pb.real, pb.imag, b=0, t=1, cut0=V, cut1=H, tag="arm", round1=square)
    j = pa + (pb - pa) * 0.30
    qa, qb = g.diagonal(j.real, j.imag, w, 0, "c", "r")
    g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=pb - pa, cut1=H, tag="leg", round1=square)
    diagonal_slab(g, pb.real, g.cap, pb - pa, top=True, left=0.8, right=0.8)
    diagonal_slab(g, qb.real, 0, qb - qa, top=False, left=0.8, right=1.0)
    g.frame(w, "s", "d")


@r("X")
def X(g):
    w = g.capw(1.14, 1.20) + g.sw * 1.5
    x_strokes(g, w, g.cap, w * 0.035)
    g.frame(w, "d", "d")


@r("Y")
def Y(g):
    w = g.capw(1.16, 1.24) + g.sw * 1.5
    yj = g.cap * 0.40
    pa, pc, ya = vee(g, 0, w, g.cap, yj)
    g.stem(w / 2, 0, max(ya, yj) + g.sw * 0.4, t=0)
    g.frame(w, "d", "d")


@r("Z")
def Z(g):
    w = g.capw(1.12, 1.16) + g.sw
    inset = w * 0.03
    g.bar(inset, w - inset, g.flat_top(g.cap), l=0.6, r=0)
    g.bar(0, w, g.hw / 2, l=0, r=0.6)
    pa, pb = g.diagonal(w - inset, g.cap, 0, 0, "r", "l")
    g.line(pa.real, g.cap, pb.real, 0, b=0, t=0, cut0=H, cut1=H, tag="diag")
    g.beak(inset, g.flat_top(g.cap), side=-1, down=True)
    g.beak(w, g.hw / 2, side=1, down=False)
    g.frame(w, 0.4, 0.4)


# --------------------------------------------------------------------------
# Rounds: O Q C G D
# --------------------------------------------------------------------------

@r("O")
def O(g):
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.cap))
    g.frame(w, "r", "r")


@r("Q")
def Q(g):
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.cap))
    x0, y0 = w * 0.52, g.cap * 0.20
    x1, y1 = w * 0.93, -g.cap * 0.115
    g.line(x0, y0, x1, y1, b=0, t=0.8, cut1=H, tag="tail")
    g.frame(w, "r", "r")


@r("C")
def C(g):
    cx, cy, rx, ry = round_box(g, o_width(g) * 0.95, g.cap)
    a0 = open_angle(g, 30, 46)
    a1 = open_angle(g, 30, 44)
    p0 = g.epoint(cx, cy, rx, ry, a0)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, rx, ry, a0, 360 - a1, fl=1.0)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="c"))
    g.frame(None, "r", 0.36)


@r("G")
def G_(g):
    cx, cy, rx, ry = round_box(g, o_width(g) * 0.97, g.cap)
    a0 = open_angle(g, 32, 46)
    a1 = 30.0
    p0 = g.epoint(cx, cy, rx, ry, a0)
    pe = g.epoint(cx, cy, rx, ry, -a1)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, rx, ry, a0, 360 - a1)
     .done(start=g.curved_cut(), end=V, tag="c"))
    # the spur: its right edge is flush with the arc's cut face, and its lower
    # end is cut along the arc, at the arc's centerline, so it stays buried
    xs = pe.real - g.sw / 2
    u = max(-0.98, min(0.98, (xs - cx) / rx))
    v = math.sqrt(1 - u * u)
    ye = cy - ry * v
    tan = complex(rx * v, ry * u)
    yb = g.cap * 0.455
    (g.path(cx + rx * 0.08, yb)
     .to(xs, yb, corner=True)
     .to(xs, ye)
     .done(start=V, end=tan, tag="spur"))
    g.frame(None, "r", 0.7)


@r("D")
def D(g):
    w = g.sw + g.rw + g.capw(1.02, 1.20)
    ft, fb = g.flat_top(g.cap), g.hw / 2
    xa = g.L + (w - g.L) * 0.30
    xr = w - g.rw / 2
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0), serif1=(1.0, 0))
    (g.path(g.L, ft)
     .to(xa, ft)
     .arc(xr, g.cap / 2, "h", w=g.p.round_weight)
     .arc(xa, fb, "v")
     .to(g.L, fb)
     .done(tag="bowl"))
    g.frame(w, "s", "r")


# --------------------------------------------------------------------------
# Bowls: B P R S U J
# --------------------------------------------------------------------------

def _lobe(g: G, x_stem: float, x_far: float, y_top: float, y_bot: float, straight: float = 0.42):
    xa = x_stem + (x_far - x_stem) * straight
    return (g.path(x_stem, y_top)
            .to(xa, y_top)
            .arc(x_far, (y_top + y_bot) / 2, "h", w=g.p.round_weight)
            .arc(xa, y_bot, "v")
            .to(x_stem, y_bot)
            .done(tag="lobe"))


@r("B")
def B(g):
    w = g.sw + g.rw + g.capw(0.86, 0.66)
    ym = bar_y(g, 0.535)
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0), serif1=(1.0, 0))
    _lobe(g, g.L, w * 0.94 - g.rw / 2, g.flat_top(g.cap), ym)
    _lobe(g, g.L, w - g.rw / 2, ym, g.hw / 2)
    g.frame(w, "s", 0.6)


@r("P")
def P(g):
    w = g.sw + g.rw + g.capw(0.82, 0.64)
    ym = bar_y(g, 0.45)
    g.stem(g.L, 0, g.cap, serif1=(1.0, 0))
    _lobe(g, g.L, w - g.rw / 2, g.flat_top(g.cap), ym)
    g.frame(w, "s", 0.45)


@r("R")
def R_(g):
    w = g.sw + g.rw + g.capw(0.88, 0.72)
    ym = bar_y(g, 0.47)
    g.stem(g.L, 0, g.cap, serif1=(1.0, 0))
    xf = w * 0.93 - g.rw / 2
    _lobe(g, g.L, xf, g.flat_top(g.cap), ym)
    xj = g.L + (xf - g.L) * 0.46
    qa, qb = g.diagonal(xj, ym, w, 0, "c", "r")
    g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=H, cut1=H, tag="leg",
           round1=0.0 if g.serifed else None)
    diagonal_slab(g, qb.real, 0, qb - qa, top=False, left=0.6, right=1.0)
    g.frame(w, "s", "d")


@r("S")
def S(g):
    x0 = g.rw / 2
    x1 = x0 + g.capw(0.92, 0.80) + g.sw * 0.3
    s_curve(g, x0, x1, g.bot, g.top(g.cap))
    g.frame(None, 0.45, 0.45)


@r("U")
def U(g):
    w = 2 * g.sw + g.capw(1.0, 1.04)
    R = w - g.L
    yr = g.bot + (R - g.L) * 0.52
    square = 0.0 if g.serifed else None
    (g.path(g.L, g.cap, fl=1.0)
     .flared_from(g.L, yr)
     .arc(w / 2, g.bot, "v")
     .arc(R, yr, "h")
     .flared_to(R, g.cap)
     .done(start=H, end=H, round_start=square, round_end=square, tag="u"))
    g.slab(g.L, g.cap, 1, 1, top=True, half=g.sw / 2 * g.fl)
    g.slab(R, g.cap, 1, 1, top=True, half=g.sw / 2 * g.fl)
    g.frame(w, "s", "s")


@r("J")
def J(g):
    rx = g.capw(0.50, 0.46)
    ry = g.cap * 0.26
    yh = g.bot + ry
    x = rx * 0.94 + g.L
    end = -(90 + open_angle(g, 46, 60))
    (g.path(x, g.cap, fl=1.0)
     .flared_from(x, yh)
     .ellipse(x - rx, yh, rx, ry, 0, end, fl=1.0)
     .done(start=H, end=g.tail_cut(), round_start=0.0 if g.serifed else None, tag="tail"))
    g.slab(x, g.cap, 1.0, 0.6, top=True, half=g.sw / 2 * g.fl)
    g.frame(None, 0.3, "s")
