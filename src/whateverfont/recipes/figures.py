"""Figures (lining, tabular)."""

from __future__ import annotations

import math

from ..glyph import G, H, V, Recipes
from .lower import open_angle, s_curve

FIGURES = Recipes()


def r(name, uni):
    return FIGURES.add(name, uni, case="figure")


def fig_advance(g: G) -> float:
    """Every figure has the same advance, so columns of numbers line up."""
    return round(fig_w(g) + g.rw + 2 * g.sidebearing("r") * 1.2)


def fig_w(g: G) -> float:
    """Centerline width of a round figure."""
    return g.cw * 0.98 * g.p.round_width + g.sw * 0.85


def _box(g: G):
    w = fig_w(g)
    x0 = g.rw / 2
    return x0, x0 + w, g.bot, g.top(g.cap)


@r("zero", "0")
def zero(g):
    x0, x1, bot, top = _box(g)
    g.ring(x0, bot, x1, top)
    g.fixed_advance(fig_advance(g))


@r("one", "1")
def one(g):
    xs = fig_w(g) * 0.56
    yf = g.cap * 0.72
    pa, _ = g.diagonal(0, yf, xs, g.cap, "l", "c", w=0.9)
    yt = g.apex_y(xs, pa, complex(xs, 0), g.cap, flat=g.sw * 1.02)
    # With a very heavy pen the flag is a stub, and the search for the corner ends far down the
    # stem: the 1 lost its stem at weight 200. The corner stays near the top.
    yt = max(yt, g.cap - 0.5 * g.sw)
    (g.path(pa.real, yf)
     .to(xs, yt, corner=True, apex=g.cap)
     .flared_to(xs, 0)
     .done(start=V, end=H, round_end=0.0 if g.serifed else None, miter=6, tag="one"))
    g.slab(xs, 0, 1.15, 1.15, half=g.sw / 2 * g.fl)
    g.fixed_advance(fig_advance(g))


@r("two", "2")
def two(g):
    x0, x1, bot, top = _box(g)
    fb = g.hw / 2
    rx = (x1 - x0) / 2 * 0.96
    ry = g.cap * 0.27
    cx, cy = (x0 + x1) / 2, top - ry
    a0 = 180 - open_angle(g, 26, 40)
    p0 = g.epoint(cx, cy, rx, ry, a0)
    pe = g.epoint(cx, cy, rx, ry, -38)
    xl = x0 + g.dx(complex(pe.real - x0, pe.imag - fb)) * 0.9
    d = complex(xl - pe.real, fb - pe.imag)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, rx, ry, a0, -38)
     .smooth(xl, fb, abs(d) * 0.30, d + complex(-abs(d) * 0.1, 0), abs(d) * 0.34, corner=True)
     .to(x1 + g.sw * 0.3, fb, fl=0.6)
     .done(start=g.curved_cut(), end=V, miter=5, tag="two"))
    g.beak(x1 + g.sw * 0.3, fb, down=False, length=0.8)
    g.fixed_advance(fig_advance(g))


@r("three", "3")
def three(g):
    x0, x1, bot, top = _box(g)
    ym = g.cap * 0.53
    urx, ury = (x1 - x0) / 2 * 0.90, (top - ym) / 2
    lrx, lry = (x1 - x0) / 2, (ym - bot) / 2
    ucx = x1 - (x1 - x0) * 0.06 - urx
    lcx = x1 - lrx
    a0 = 180 - open_angle(g, 26, 42)
    a1 = -(180 - open_angle(g, 24, 40))
    ps = g.epoint(ucx, top - ury, urx, ury, -104)
    pt = g.epoint(ucx, top - ury, urx, ury, a0)
    (g.path(ps.real, ps.imag, 0.85)
     .ellipse(ucx, top - ury, urx, ury, -104, a0, fl=1.0)
     .done(end=g.tail_cut(), tag="upper"))
    qs = g.epoint(lcx, bot + lry, lrx, lry, 104)
    (g.path(qs.real, qs.imag, 0.85)
     .ellipse(lcx, bot + lry, lrx, lry, 104, a1, fl=1.0)
     .done(end=g.tail_cut(), tag="lower"))
    g.fixed_advance(fig_advance(g))


@r("four", "4")
def four(g):
    w = fig_w(g) + g.sw * 0.9
    xs = w * 0.74
    yb = g.cap * 0.27
    g.stem(xs, 0, g.cap, t=0.4, serif1=False)
    pa, pb = g.diagonal(xs + g.sw / 2, g.cap, 0, yb, "r", "c")
    xl = g.dx(pb - pa) * 0.8
    (g.path(pa.real, g.cap)
     .to(xl, yb, corner=True)
     .to(w, yb, fl=0.5)
     .done(start=H, end=V, miter=4, tag="four"))
    g.fixed_advance(fig_advance(g))


@r("five", "5")
def five(g):
    x0, x1, bot, top = _box(g)
    ft = g.flat_top(g.cap)
    xl = x0 + (x1 - x0) * 0.10
    yj = g.cap * 0.50
    (g.path(x1 - (x1 - x0) * 0.04, ft, fl=0.6)
     .to(xl, ft, corner=True)
     .to(xl - (x1 - x0) * 0.04, yj)
     .done(start=V, end=H, tag="flag"))
    g.beak(x1 - (x1 - x0) * 0.04, ft, down=True, length=0.7)
    ry = g.cap * 0.325
    rx = (x1 - x0) / 2
    cx, cy = x1 - rx, bot + ry
    a1 = -(180 - open_angle(g, 24, 40))
    ps = g.epoint(cx, cy, rx, ry, 146)
    (g.path(ps.real, ps.imag, g.p.join)
     .ellipse(cx, cy, rx, ry, 146, a1, fl=1.0)
     .done(end=g.tail_cut(), tag="bowl"))
    g.fixed_advance(fig_advance(g))


def _six(g: G):
    x0, x1, bot, top = _box(g)
    ry = g.cap * 0.315
    g.ring(x0, bot, x1, bot + 2 * ry)
    # the stroke that rises from the bowl's left side to the top right
    brx, bry = (x1 - x0) / 2 * 1.04, (top - bot) / 2
    cx, cy = x0 + brx, (top + bot) / 2
    a0 = open_angle(g, 52, 64)
    p0 = g.epoint(cx, cy, brx, bry, a0)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, brx, bry, a0, 180)
     .to(x0, bot + ry, w=g.p.round_weight)
     .done(start=g.tail_cut(), tag="stroke"))
    return x0, x1


@r("six", "6")
def six(g):
    _six(g)
    g.fixed_advance(fig_advance(g))


@r("nine", "9")
def nine(g):
    x0, x1 = _six(g)
    g.rotate(180, (x0 + x1) / 2, g.cap / 2)
    g.fixed_advance(fig_advance(g))


@r("seven", "7")
def seven(g):
    w = fig_w(g) + g.sw * 0.5
    ft = g.flat_top(g.cap)
    pa, pb = g.diagonal(w, g.cap, w * 0.30, 0, "r", "c")
    (g.path(0, ft, fl=0.6)
     .to(pa.real - g.dx(pb - pa) * 0.2, ft, corner=True, apex=g.cap)
     .flared_to(pb.real, 0)
     .done(start=V, end=H, miter=6, tag="seven"))
    g.beak(0, ft, side=-1, down=True, length=0.8)
    g.fixed_advance(fig_advance(g))


@r("eight", "8")
def eight(g):
    x0, x1, bot, top = _box(g)
    ym = g.cap * 0.535
    inset = (x1 - x0) * 0.055
    g.ring(x0 + inset, ym, x1 - inset, top, w_side=g.p.round_weight * 0.97)
    g.ring(x0, bot, x1, ym)
    g.fixed_advance(fig_advance(g))
