"""Latin lowercase recipes.

Each recipe draws one letter with skeleton strokes. All measurements come from
the builder ``g`` so the same recipe works at any weight, width or contrast.
"""

from __future__ import annotations

import math

from ..glyph import G, H, V, Recipes

LOWER = Recipes()
r = LOWER.add


# --------------------------------------------------------------------------
# Shared parts
# --------------------------------------------------------------------------

def n_width(g: G) -> float:
    return 2 * g.sw + g.cw


def o_width(g: G) -> float:
    return g.cw * 1.06 * g.p.round_width + 2 * g.rw


def arch(g: G, x0: float, x1: float, foot: float = 0.0, fl: float = 1.0, peak: float = 0.5,
         branch: float = 0.60, height: float | None = None, serif=(1.0, 1.0)):
    """The arch of n, h and m: leaves the stem at ``x0``, comes down as a stem at ``x1``.

    In a family with slab serifs the foot gets a slab: ``serif`` gives its (left, right)
    lengths, or None for no slab.
    """
    h = g.xh if height is None else height
    top = g.top(h)
    xm = x0 + (x1 - x0) * peak
    ysh = max(top - (x1 - xm) * 1.02, foot + h * 0.3)
    slab = bool(g.serifed and serif and fl)
    s = (g.path(x0, h * branch, g.p.join)
         .arc(xm, top, "v", k0=0.42, k1=0.62)
         .arc(x1, ysh, "h")
         .flared_to(x1, foot, fl)
         .done(end=H, round_end=0.0 if slab else None, tag="arch"))
    if slab:
        g.slab(x1, foot, serif[0], serif[1], half=g.sw / 2 * (1 + g.p.eff_flare * fl))
    return s


def bowl(g: G, x_stem: float, x_far: float, branch: float = 0.37, height: float | None = None):
    """An open bowl on a stem (b, d, p, q). ``x_far`` is the centerline of its far side."""
    h = g.xh if height is None else height
    top, bot = g.top(h), g.bot
    xm = (x_stem + x_far) / 2
    ym = (top + bot) / 2
    return (g.path(x_stem, h * (1 - branch), g.p.join)
            .arc(xm, top, "v", k0=0.42, k1=0.62)
            .arc(x_far, ym, "h", w=g.p.round_weight)
            .arc(xm, bot, "v")
            .arc(x_stem, h * branch, "h", w=g.p.join, k0=0.62, k1=0.42)
            .done(tag="bowl"))


def round_box(g: G, width: float, height: float | None = None):
    """Center and radii of the centerline ellipse for a round letter ``width`` wide."""
    h = g.xh if height is None else height
    top, bot = g.top(h), g.bot
    rx = (width - g.rw) / 2
    return g.rw / 2 + rx, (top + bot) / 2, rx, (top - bot) / 2


def crowded(g: G) -> bool:
    """A monospaced family with slab serifs: the slabs take room in the cell, so m, w, M and W
    are drawn lighter and more open."""
    return g.serifed and g.p.mono > 0


def open_angle(g: G, closed: float, opened: float) -> float:
    """An angle that depends on the aperture setting."""
    return closed + (opened - closed) * g.p.aperture


def i_dot_y(g: G) -> float:
    return g.xh + (g.asc - g.xh) * 0.60


# --------------------------------------------------------------------------
# Stems and arches: i l n m h u r
# --------------------------------------------------------------------------

@r("i", "i")
def i(g):
    g.stem(g.L, 0, g.xh)
    g.dot(g.L, i_dot_y(g))
    g.frame(g.sw)


@r("dotlessi", 0x0131)
def dotlessi(g):
    g.stem(g.L, 0, g.xh)
    g.frame(g.sw)


@r("l", "l")
def l(g):
    g.stem(g.L, 0, g.asc)
    g.frame(g.sw)


@r("n", "n")
def n(g):
    w = n_width(g)
    g.stem(g.L, 0, g.xh)
    arch(g, g.L, w - g.L)
    g.frame(w, "s", 0.94)


@r("m", "m")
def m(g):
    c = g.cw * 0.9
    w = 3 * g.sw + 2 * c
    x1 = g.L + g.sw + c
    # in a crowded cell the feet are short, so the two counters keep their white
    out, inner = (0.75, 0.5) if crowded(g) else (1.0, 1.0)
    g.stem(g.L, 0, g.xh, serif0=(out, inner) if g.serifed else None)
    arch(g, g.L, x1, serif=(inner, inner))
    arch(g, x1, w - g.L, serif=(inner, out))
    g.frame(w, "s", 0.94)


@r("h", "h")
def h(g):
    w = n_width(g)
    g.stem(g.L, 0, g.asc)
    arch(g, g.L, w - g.L)
    g.frame(w, "s", 0.94)


@r("u", "u")
def u(g):
    w = n_width(g)
    # an n turned over; its slabs would land in the wrong places, so u places its own
    square = 0.0 if g.serifed else None
    g.stem(g.L, 0, g.xh, serif0=False, serif1=False, round0=square, round1=square)
    arch(g, g.L, w - g.L, serif=None)
    g.rotate(180, w / 2, g.xh / 2)
    g.slab(g.L, g.xh, 1, 0, top=True)              # heads on the left of both stems
    g.slab(w - g.L, g.xh, 1, 0, top=True)
    g.slab(w - g.L, 0, 0, 1)                       # and a foot to the right
    g.frame(w, 0.94, "s")


@r("r", "r")
def r_(g):
    arm = (g.cw * 0.50 + g.sw * 0.42) * g.p.arm
    w = g.sw + arm
    top = g.top(g.xh)
    # a typewriter r stands on a wide foot, which fills its cell
    g.stem(g.L, 0, g.xh, serif0=(1.0, 1.45) if g.p.mono else None)
    d = complex(1, -0.1) if g.flat else complex(1, -0.38)      # a flat arm ends almost level
    xt = w - g.thick(d) * g.fl * 0.2
    yt = top - arm * 0.085
    y0 = g.xh * 0.56
    (g.path(g.L, y0, g.p.join)
     .curve((g.L, y0 + (top - y0) * 0.78), (xt - arm * 0.62 * d.real, yt - arm * 0.62 * d.imag * 0.6), xt, yt, fl=1.0)
     .done(end=g.hook_cut(), tag="arm"))
    g.frame(None, "s", 0.22)


# --------------------------------------------------------------------------
# Rounds: o c e
# --------------------------------------------------------------------------

@r("o", "o")
def o(g):
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.xh))
    g.frame(w, "r", "r")


@r("c", "c")
def c(g):
    cx, cy, rx, ry = round_box(g, o_width(g) * 0.97)
    a0 = open_angle(g, 30, 50)
    a1 = open_angle(g, 30, 46)
    p0 = g.epoint(cx, cy, rx, ry, a0)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, rx, ry, a0, 360 - a1, fl=1.0)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="c"))
    g.frame(None, "r", 0.3)


@r("e", "e")
def e(g):
    cx, cy, rx, ry = round_box(g, o_width(g) * 0.97)
    ym = g.xh * 0.53
    ab = math.degrees(math.asin(max(-0.9, min(0.9, (ym - cy) / ry))))
    a1 = open_angle(g, 28, 48)
    pb = g.epoint(cx, cy, rx, ry, ab)
    (g.path(cx - rx, ym)
     .to(pb.real, pb.imag, corner=True)
     .ellipse(cx, cy, rx, ry, ab, 360 - a1, fl=1.0)
     .done(end=g.curved_cut(), tag="e"))
    g.frame(None, "r", 0.36)


# --------------------------------------------------------------------------
# Bowls on stems: a b d p q g
# --------------------------------------------------------------------------

def _bowl_width(g: G) -> float:
    return g.sw + g.cw * g.p.round_width + g.rw


@r("b", "b")
def b(g):
    w = _bowl_width(g)
    g.stem(g.L, 0, g.asc, serif0=(1.0, 0))          # the bowl takes the right side of the foot
    bowl(g, g.L, w - g.rw / 2)
    g.frame(w, "s", "r")


SPUR = 0.55     #: a spur is a short slab: on the foot of a and d, at the top of q and g


@r("d", "d")
def d(g):
    w = _bowl_width(g)
    g.stem(w - g.L, 0, g.asc, serif0=(0, SPUR))
    bowl(g, w - g.L, g.rw / 2)
    g.frame(w, "r", "s")


@r("p", "p")
def p(g):
    w = _bowl_width(g)
    g.stem(g.L, g.desc, g.xh)
    bowl(g, g.L, w - g.rw / 2)
    g.frame(w, "s", "r")


@r("q", "q")
def q(g):
    w = _bowl_width(g)
    g.stem(w - g.L, g.desc, g.xh, serif1=(0, SPUR))
    bowl(g, w - g.L, g.rw / 2)
    g.frame(w, "r", "s")


@r("a", "a")
def a(g):
    if g.p.a_story == 1:
        w = _bowl_width(g) * 0.97
        g.stem(w - g.L, 0, g.xh, serif0=(0, SPUR), serif1=False)
        bowl(g, w - g.L, g.rw / 2)
        g.frame(w, "r", "s")
        return
    # the two-story a follows the wide rounds part of the way: it has a stem on one side
    w = g.sw + g.cw * 0.86 * (1 + (g.p.round_width - 1) * 0.6) + g.rw * 0.9
    R = w - g.L
    top, bot = g.top(g.xh), g.bot
    # stem and the roof
    ry = g.xh * 0.33
    ysh = top - ry
    rx = (R - g.rw * 0.5) * 0.5
    at = 180 - open_angle(g, 22, 44)
    (g.path(R, 0, fl=1.0)
     .flared_from(R, ysh)
     .ellipse(R - rx, ysh, rx, ry, 0, at, fl=1.0)
     .done(start=H, end=g.curved_cut(), round_start=0.0 if g.serifed else None, tag="roof"))
    g.slab(R, 0, 0, SPUR, half=g.sw / 2 * g.fl)
    # bowl
    xl = g.rw / 2
    ytj = g.xh * 0.585
    ybj = g.xh * 0.16
    yc = (ytj + bot) / 2 - g.xh * 0.02
    xm = xl + (R - xl) * 0.5
    (g.path(R, ytj, g.p.join)
     .arc(xl, yc, "h", w=g.p.round_weight, k0=0.72, k1=0.6)
     .arc(xm, bot, "v")
     .arc(R, ybj, "h", w=g.p.join, k0=0.62, k1=0.42)
     .done(tag="bowl"))
    g.frame(w, 0.6, "s")


@r("g", "g")
def g_(g):
    w = _bowl_width(g)
    R = w - g.L
    bowl(g, R, g.rw / 2)
    rx = (R - g.rw / 2) * 0.5
    yh = g.desc * 0.42
    ry = yh - g.dbot
    end = -(90 + open_angle(g, 48, 64))
    (g.path(R, g.xh, fl=1.0)
     .flared_from(R, yh)
     .ellipse(R - rx, yh, rx, ry, 0, end, fl=1.0)
     .done(start=H, end=g.tail_cut(), round_start=0.0 if g.serifed else None, tag="tail"))
    g.slab(R, g.xh, 0, SPUR * 1.2, top=True, half=g.sw / 2 * g.fl)       # the ear of a typewriter g
    g.frame(w, "r", "s")


# --------------------------------------------------------------------------
# Hooks: f t j
# --------------------------------------------------------------------------

@r("f", "f")
def f(g):
    rx = g.hook_reach(0.40)
    top = g.top(g.asc)
    ry = (g.asc - g.xh) * 0.66
    yh = top - ry
    x = g.cw * 0.30 + g.L
    end = 90 - g.hook_end(52, 38)
    (g.path(x, 0, fl=1.0)
     .flared_from(x, yh)
     .ellipse(x + rx, yh, rx, ry, 180, end, fl=1.0)
     .done(start=H, end=g.hook_cut(), round_start=0.0 if g.serifed else None, tag="hook"))
    g.bar(0, x + g.cw * 0.42 * g.p.arm, g.flat_top(g.xh), l=0.5, r=0.5)
    g.slab(x, 0, 1, 1, half=g.sw / 2 * g.fl)
    g.frame(None, 0.3, 0.1)


@r("t", "t")
def t(g):
    rx = g.hook_reach(0.36)
    ry = g.xh * 0.26
    yh = g.bot + ry
    x = g.cw * 0.28 + g.L
    end = 270 + g.hook_end(56, 40)
    ytop = g.xh + (g.cap - g.xh) * 0.62
    (g.path(x, ytop, fl=0.6)
     .flared_from(x, yh)
     .ellipse(x + rx, yh, rx, ry, 180, end, fl=1.0)
     .done(start=H, end=g.hook_cut(), tag="hook"))
    g.bar(0, x + g.cw * 0.44 * g.p.arm, g.flat_top(g.xh), l=0.5, r=0.5)
    g.frame(None, 0.3, 0.25)


@r("j", "j")
def j(g):
    rx = g.hook_reach(0.40)
    yh = g.desc * 0.40
    ry = yh - g.dbot
    x = rx * 0.92 + g.L
    end = -(90 + g.hook_end(46, 60))
    (g.path(x, g.xh, fl=1.0)
     .flared_from(x, yh)
     .ellipse(x - rx, yh, rx, ry, 0, end, fl=1.0)
     .done(start=H, end=g.hook_cut(), round_start=0.0 if g.serifed else None, tag="tail"))
    g.slab(x, g.xh, 1, 0, top=True, half=g.sw / 2 * g.fl)
    g.dot(x, i_dot_y(g))
    g.frame(x + g.L, -0.55, "s")


# --------------------------------------------------------------------------
# The s
# --------------------------------------------------------------------------

def s_curve(g: G, x0: float, x1: float, y0: float, y1: float, ym: float | None = None,
            tilt: float = 0.0):
    """The s spine between centerline box x0..x1, y0..y1 (shared with S, 5, 3...)."""
    wbox = x1 - x0
    ym = (y0 + y1) / 2 + (y1 - y0) * 0.012 if ym is None else ym
    # upper bowl is a little smaller than the lower one
    ux0, ux1 = x0 + wbox * 0.035, x1 - wbox * 0.035
    ucx, ury = (ux0 + ux1) / 2, (y1 - ym) / 2
    urx = (ux1 - ux0) / 2
    ucy = y1 - ury
    lcx, lry = (x0 + x1) / 2, (ym - y0) / 2
    lrx = wbox / 2
    lcy = y0 + lry
    a0 = open_angle(g, 28, 48)
    a1 = open_angle(g, 26, 44)
    slope = math.atan2(lry + ury, wbox) * 0.62 + tilt
    d = complex(math.cos(slope), -math.sin(slope))
    # the spine carries the weight of the s, a little less so in bold, where it would clog
    spine = g.sw * (0.96 - 0.0022 * max(0.0, g.p.weight - 82.0))
    ws = min(1.5, spine / g.thick(d))
    boost = 1 + (g.p.superk / 0.5523 - 1) * 0.45
    k = 0.5523 * boost
    p0 = g.epoint(ucx, ucy, urx, ury, a0)
    return (g.path(p0.real, p0.imag, fl=1.0)
            .ellipse(ucx, ucy, urx, ury, a0, 180, boost=boost, boost_all=True)
            .curve((ux0, ucy - ury * k), (lcx - d.real * wbox * 0.30, ym - d.imag * wbox * 0.30),
                   (ux0 + ux1 + x0 + x1) / 4, ym, w=ws)
            .curve(((ux0 + ux1 + x0 + x1) / 4 + d.real * wbox * 0.30, ym + d.imag * wbox * 0.30),
                   (x1, lcy + lry * k), x1, lcy, w=g.p.round_weight)
            .ellipse(lcx, lcy, lrx, lry, 0, -(180 - a1), fl=1.0, boost=boost, boost_all=True)
            .done(start=g.curved_cut(), end=g.curved_cut(), tag="s"))


@r("s", "s")
def s(g):
    x0 = g.rw / 2
    x1 = x0 + g.cw * 0.86 * g.p.round_width + g.sw * 0.32
    s_curve(g, x0, x1, g.bot, g.top(g.xh))
    g.frame(None, 0.42, 0.42)


# --------------------------------------------------------------------------
# Diagonals: k v w x y z
# --------------------------------------------------------------------------

def apex_cut(g: G, y: float, down: bool = True) -> float:
    """Where the point of a V is cut: flat points sit on the line, sharp ones overshoot."""
    over = g.o * 1.2 * max(0.0, 1 - g.p.apex * 1.5)
    return y - over if down else y + over


def vee(g: G, x0: float, x1: float, y_far: float, y_tip: float, xm: float | None = None,
        fl: float = 1.0, down: bool = True):
    """A V (or an inverted one) between outer edges x0 and x1."""
    xm = (x0 + x1) / 2 if xm is None else xm
    cut = apex_cut(g, y_tip, down)
    pa, _ = g.diagonal(x0, y_far, xm, y_tip, "l", "c")
    pc, _ = g.diagonal(x1, y_far, xm, y_tip, "r", "c")
    ya = g.apex_y(xm, pa, pc, cut)
    square = 0.0 if g.serifed else None
    (g.path(pa.real, y_far, fl=fl)
     .flared_from(xm, ya, corner=True, apex=cut)
     .flared_to(pc.real, y_far, fl)
     .done(start=H, end=H, round_start=square, round_end=square, tag="vee"))
    diagonal_slab(g, pa.real, y_far, complex(xm, ya) - pa, top=down, fl=fl)
    diagonal_slab(g, pc.real, y_far, complex(xm, ya) - pc, top=down, fl=fl)
    return pa, pc, ya


def diagonal_slab(g: G, x: float, y: float, direction: complex, top: bool, left: float = 1.0,
                  right: float = 1.0, fl: float = 1.0):
    """A slab across the horizontally cut end of a diagonal whose centerline ends at (x, y)."""
    if g.serifed:
        g.slab(x, y, left, right, top=top, half=g.dx(direction) * (1 + g.p.eff_flare * fl))


@r("v", "v")
def v(g):
    w = n_width(g) * 1.0
    vee(g, 0, w, g.xh, 0)
    g.frame(w, "d", "d")


@r("w", "w")
def w_(g):
    tight = crowded(g)
    double_vee(g, 0.74 if tight else None, 0.78 if tight else 1.0)


def double_vee(g: G, middle: float | None = None, thin: float = 1.0):
    """The w. ``middle`` is where the middle point stops, as a share of the x-height (None: at the
    top), and ``thin`` the weight of the two inner strokes there."""
    w = n_width(g) * 1.56
    xb1, xb2, xt = w * 0.275, w * 0.725, w * 0.5
    cut_b = apex_cut(g, 0, True)
    cut_t = apex_cut(g, g.xh, False) if middle is None else g.xh * middle
    pa, _ = g.diagonal(0, g.xh, xb1, 0, "l", "c")
    pe, _ = g.diagonal(w, g.xh, xb2, 0, "r", "c")
    yt = g.xh - g.sw
    for _ in range(3):
        yb1 = g.apex_y(xb1, pa, complex(xt, yt), cut_b)
        yb2 = g.apex_y(xb2, complex(xt, yt), pe, cut_b)
        yt = g.apex_y(xt, complex(xb1, yb1), complex(xb2, yb2), cut_t, w=thin)
    square = 0.0 if g.serifed else None
    (g.path(pa.real, g.xh, fl=1.0)
     .flared_from(xb1, yb1, corner=True, apex=cut_b)
     .to(xt, yt, corner=True, apex=cut_t, w=thin)
     .to(xb2, yb2, corner=True, apex=cut_b)
     .flared_to(pe.real, g.xh)
     .done(start=H, end=H, round_start=square, round_end=square, tag="w"))
    diagonal_slab(g, pa.real, g.xh, complex(xb1, yb1) - pa, top=True)
    diagonal_slab(g, pe.real, g.xh, complex(xb2, yb2) - pe, top=True)
    g.frame(w, "d", "d")


def x_strokes(g: G, w: float, h: float, inset: float):
    """The two strokes of x and X, with a slab on every end in a family with serifs."""
    a0, a1 = g.diagonal(inset, h, w, 0, "l", "r")
    b0, b1 = g.diagonal(0, 0, w - inset, h, "l", "r")
    square = 0.0 if g.serifed else None
    g.line(a0.real, h, a1.real, 0, b=1, t=1, cut0=H, cut1=H, round0=square, round1=square)
    g.line(b0.real, 0, b1.real, h, b=1, t=1, cut0=H, cut1=H, round0=square, round1=square)
    for (p, q), top in (((a0, a1), True), ((a1, a0), False), ((b0, b1), False), ((b1, b0), True)):
        diagonal_slab(g, p.real, h if top else 0, q - p, top=top)


@r("x", "x")
def x(g):
    w = n_width(g) * 0.98
    x_strokes(g, w, g.xh, w * 0.03)
    g.frame(w, "d", "d")


@r("y", "y")
def y(g):
    w = n_width(g) * 1.0
    xm = w * 0.5
    pa, _ = g.diagonal(0, g.xh, xm, 0, "l", "c")
    pc, _ = g.diagonal(w, g.xh, xm, 0, "r", "c")
    # the right stroke runs through the meeting point and on to the descender
    xj = xm + g.sw * 0.12
    yj = g.sw * 0.25
    slope = (pc.real - xj) / (g.xh - yj)
    xtail = xj + slope * (g.desc - yj)
    square = 0.0 if g.serifed else None
    g.line(pc.real, g.xh, xtail, g.desc, b=1, t=1, cut0=H, cut1=H, tag="tail", round0=square, round1=square)
    g.line(pa.real, g.xh, xj, yj, b=1, t=0, cut0=H, cut1=complex(slope, 1), tag="arm", round0=square)
    diagonal_slab(g, pa.real, g.xh, complex(xj, yj) - pa, top=True)
    diagonal_slab(g, pc.real, g.xh, complex(xtail, g.desc) - pc, top=True)
    diagonal_slab(g, xtail, g.desc, complex(xtail, g.desc) - pc, top=False, left=1.0, right=0.5)
    g.frame(None, "d", "d")


@r("k", "k")
def k(g):
    w = g.sw + g.cw * 0.96 + g.sw * 0.25
    g.stem(g.L, 0, g.asc)
    pa, pb = g.diagonal(g.sw * 0.75, g.xh * 0.36, w * 0.97, g.xh, "c", "r")
    square = 0.0 if g.serifed else None
    g.line(pa.real, pa.imag, pb.real, pb.imag, b=0, t=1, cut0=V, cut1=H, tag="arm", round1=square)
    j = pa + (pb - pa) * 0.34
    qa, qb = g.diagonal(j.real, j.imag, w, 0, "c", "r")
    g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=pb - pa, cut1=H, tag="leg", round1=square)
    diagonal_slab(g, pb.real, g.xh, pb - pa, top=True, left=0.7, right=0.7)
    diagonal_slab(g, qb.real, 0, qb - qa, top=False, left=0.7, right=1.0)
    g.frame(w, "s", "d")


@r("z", "z")
def z(g):
    w = g.cw * 0.98 + g.sw * 0.9
    inset = w * 0.035
    g.bar(inset, w - inset, g.flat_top(g.xh), l=0.6, r=0)
    g.bar(0, w, g.hw / 2, l=0, r=0.6)
    pa, pb = g.diagonal(w - inset, g.xh, 0, 0, "r", "l")
    g.line(pa.real, g.xh, pb.real, 0, b=0, t=0, cut0=H, cut1=H, tag="diag")
    g.beak(inset, g.flat_top(g.xh), side=-1, down=True, length=0.8)
    g.beak(w, g.hw / 2, side=1, down=False, length=0.8)
    g.frame(w, 0.4, 0.4)
