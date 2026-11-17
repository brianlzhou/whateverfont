"""Punctuation and symbols."""

from __future__ import annotations

import math

from ..glyph import G, H, V, Recipes
from .figures import fig_advance
from .lower import open_angle, s_curve

PUNCT = Recipes()


def r(name, uni, case="lower"):
    return PUNCT.add(name, uni, case=case)


def dot_d(g: G) -> float:
    return g.sw * 1.22


def tail(g: G, cx: float, cy: float, d: float, up: bool = False, reach: float = 1.42, tip: float = 0.42):
    """A dot with a tapering tail: comma and quotes.

    ``reach`` is how far the tail goes past the middle of the dot, in dot widths, and ``tip`` how
    wide it still is at its end. A comma must not pass for a period at small sizes.
    """
    g.dot(cx, cy, d)
    s = -1 if not up else 1
    (g.path(cx + d * 0.22, cy + s * d * 0.05, w=1.0)
     .to(cx - d * 0.32, cy + s * d * reach, w=tip)
     .done(fixed=d * 0.28, round_start=0.0, tag="tail"))


@r("space", " ")
def space(g):
    g._advance = round((g.cw * 0.52 + g.sw * 0.9) * g.p.word_space)
    g._frame = (0, 0, 0)


@r("nbspace", 0x00A0)
def nbspace(g):
    space(g)


@r("period", ".")
def period(g):
    d = dot_d(g)
    g.dot(d / 2, d / 2, d)
    g.frame(d, 0.75, 0.75)


@r("comma", ",")
def comma(g):
    d = dot_d(g)
    tail(g, d / 2, d / 2, d)
    g.frame(d, 0.75, 0.75)


@r("colon", ":")
def colon(g):
    d = dot_d(g)
    g.dot(d / 2, d / 2, d)
    g.dot(d / 2, g.xh - d / 2 - g.o, d)
    g.frame(d, 0.8, 0.8)


@r("semicolon", ";")
def semicolon(g):
    d = dot_d(g)
    tail(g, d / 2, d / 2, d)
    g.dot(d / 2, g.xh - d / 2 - g.o, d)
    g.frame(d, 0.8, 0.8)


@r("ellipsis", 0x2026)
def ellipsis(g):
    d = dot_d(g)
    step = d * 2.6
    for i in range(3):
        g.dot(d / 2 + i * step, d / 2, d)
    g.frame(d + 2 * step, 0.9, 0.9)


@r("periodcentered", 0x00B7)
def periodcentered(g):
    d = dot_d(g)
    g.dot(d / 2, g.xh * 0.52, d)
    g.frame(d, 0.9, 0.9)


@r("bullet", 0x2022)
def bullet(g):
    d = g.xh * 0.44
    g.dot(d / 2, g.xh * 0.52, d, shape="round")
    g.frame(d, 0.8, 0.8)


@r("exclam", "!", "upper")
def exclam(g):
    d = dot_d(g)
    g.dot(d / 2, d / 2, d)
    (g.path(d / 2, g.cap, w=1.12, fl=0.5)
     .to(d / 2, d * 1.75, w=0.72)
     .done(start=H, end=H, tag="stem"))
    g.frame(d, 0.9, 0.9)


@r("question", "?", "upper")
def question(g):
    d = dot_d(g)
    rx = g.cw * 0.34 + g.sw * 0.42
    ry = g.cap * 0.235
    cx, cy = g.rw / 2 + rx, g.top(g.cap) - ry
    a0 = 180 - open_angle(g, 24, 40)
    p0 = g.epoint(cx, cy, rx, ry, a0)
    pe = g.epoint(cx, cy, rx, ry, -52)
    ys = min(d * 1.85, pe.imag - g.cap * 0.16)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, rx, ry, a0, -52)
     .smooth(cx, ys + (pe.imag - ys) * 0.38, (pe.imag - ys) * 0.22, (0, -1), (pe.imag - ys) * 0.3)
     .to(cx, ys)
     .done(start=g.curved_cut(), end=H, tag="hook"))
    g.dot(cx, d / 2, d)
    g.frame(None, 0.6, 0.6)


# --------------------------------------------------------------------------
# Dashes
# --------------------------------------------------------------------------

def _dash(g: G, length: float, y: float, sb: float = 0.7):
    g.bar(0, length, y)
    g.frame(length, sb, sb)


@r("hyphen", "-")
def hyphen(g):
    _dash(g, g.cw * 0.74, g.xh * 0.50)


@r("endash", 0x2013)
def endash(g):
    _dash(g, g.cw * 1.55, g.xh * 0.50, 0.3)


@r("emdash", 0x2014)
def emdash(g):
    _dash(g, g.cw * 2.9, g.xh * 0.50, 0.0)


@r("underscore", "_")
def underscore(g):
    _dash(g, g.cw * 1.7, g.desc * 0.45, 0.0)


# --------------------------------------------------------------------------
# Quotes
# --------------------------------------------------------------------------

def _tick(g: G, x: float):
    (g.path(x, g.asc, w=1.05)
     .to(x, g.asc - (g.asc - g.xh) * 1.05, w=0.62)
     .done(start=H, end=H, tag="tick"))


@r("quotesingle", "'")
def quotesingle(g):
    _tick(g, g.L * 1.05)
    g.frame(g.sw * 1.05, 0.6, 0.6)


@r("quotedbl", '"')
def quotedbl(g):
    step = g.sw * 2.2
    _tick(g, g.L * 1.05)
    _tick(g, g.L * 1.05 + step)
    g.frame(g.sw * 1.05 + step, 0.6, 0.6)


def _quote(g: G, n: int, left: bool):
    d = dot_d(g)
    step = d * 1.75
    cy = g.asc - d / 2
    for i in range(n):
        tail(g, d / 2 + i * step, cy, d)
    if left:
        # a left quote is a right quote turned upside down
        g.rotate(180, d / 2 + (n - 1) * step / 2, cy - d * 0.45)
    g.frame(None, 0.6, 0.6)


@r("quoteright", 0x2019)
def quoteright(g):
    _quote(g, 1, False)


@r("quoteleft", 0x2018)
def quoteleft(g):
    _quote(g, 1, True)


@r("quotedblright", 0x201D)
def quotedblright(g):
    _quote(g, 2, False)


@r("quotedblleft", 0x201C)
def quotedblleft(g):
    _quote(g, 2, True)


@r("grave", "`")
def grave(g):
    g.line(0, g.asc, g.sw * 1.5, g.asc - (g.asc - g.xh) * 0.62, w=0.78, tag="accent")
    g.frame(None, 0.9, 0.9)


# --------------------------------------------------------------------------
# Brackets and slashes
# --------------------------------------------------------------------------

def _paren(g: G, x_in: float, x_out: float):
    top, bot = g.asc + 16, g.desc * 0.82
    ym = (top + bot) / 2
    (g.path(x_in, top, w=0.72)
     .arc(x_out, ym, via=(x_out, top), k0=0.46, k1=0.62, w=0.788)
     .arc(x_in, bot, via=(x_out, bot), k0=0.62, k1=0.46, w=0.72)
     .done(tag="paren"))


@r("parenleft", "(")
def parenleft(g):
    d = g.cw * 0.30 + g.sw * 0.75
    _paren(g, d, g.L)
    g.frame(None, 0.7, 0.35)


@r("parenright", ")")
def parenright(g):
    d = g.cw * 0.30 + g.sw * 0.75
    _paren(g, g.L, d)
    g.frame(None, 0.35, 0.7)


def _bracket(g: G, x_stem: float, x_arm: float):
    top, bot = g.asc + 16, g.desc * 0.82
    (g.path(x_arm, top - g.hw / 2)
     .to(x_stem, top - g.hw / 2, corner=True)
     .to(x_stem, bot + g.hw / 2, corner=True)
     .to(x_arm, bot + g.hw / 2)
     .done(start=V, end=V, tag="bracket"))


@r("bracketleft", "[")
def bracketleft(g):
    _bracket(g, g.L, g.L + g.cw * 0.28 + g.sw * 0.7)
    g.frame(None, 0.9, 0.35)


@r("bracketright", "]")
def bracketright(g):
    _bracket(g, g.L + g.cw * 0.28 + g.sw * 0.7, g.L)
    g.frame(None, 0.35, 0.9)


def _brace(g: G, x_stem: float, x_tip: float, x_arm: float):
    top, bot = g.asc + 16, g.desc * 0.82
    ym = (top + bot) / 2
    q = (top - ym) * 0.5
    (g.path(x_arm, top - g.hw / 2, w=0.78)
     .arc(x_stem, top - q * 0.9, "h", k0=0.7, k1=0.5, w=0.78)
     .to(x_stem, ym + q * 0.55, w=0.78)
     .arc(x_tip, ym, "v", k0=0.6, k1=0.5, w=0.78, corner=True)
     .arc(x_stem, ym - q * 0.55, "h", k0=0.5, k1=0.6, w=0.78)
     .to(x_stem, bot + q * 0.9, w=0.78)
     .arc(x_arm, bot + g.hw / 2, "v", k0=0.5, k1=0.7, w=0.78)
     .done(start=V, end=V, tag="brace"))


@r("braceleft", "{")
def braceleft(g):
    c = g.cw * 0.20 + g.sw * 0.55
    _brace(g, g.L + c, g.L, g.L + c * 2)
    g.frame(None, 0.5, 0.35)


@r("braceright", "}")
def braceright(g):
    c = g.cw * 0.20 + g.sw * 0.55
    _brace(g, g.L + c, g.L + c * 2, g.L)
    g.frame(None, 0.35, 0.5)


@r("slash", "/")
def slash(g):
    w = g.cw * 1.05
    top, bot = g.asc + 16, g.desc * 0.6
    a, b = g.diagonal(0, bot, w, top, "l", "r", w=0.782)
    g.line(a.real, bot, b.real, top, w=0.782, cut0=H, cut1=H)
    g.frame(w, 0.15, 0.15)


@r("backslash", "\\")
def backslash(g):
    w = g.cw * 1.05
    top, bot = g.asc + 16, g.desc * 0.6
    a, b = g.diagonal(0, top, w, bot, "l", "r", w=0.782)
    g.line(a.real, top, b.real, bot, w=0.782, cut0=H, cut1=H)
    g.frame(w, 0.15, 0.15)


@r("bar", "|")
def bar(g):
    g.stem(g.L, g.desc, g.asc + 16, b=0, t=0, w=0.782)
    g.frame(g.sw, 1.3, 1.3)


# --------------------------------------------------------------------------
# Math
# --------------------------------------------------------------------------

def math_w(g: G) -> float:
    return g.cw * 1.34


def math_y(g: G) -> float:
    return g.cap * 0.50


@r("plus", "+", "figure")
def plus(g):
    w, y = math_w(g), math_y(g)
    g.bar(0, w, y, w=0.785)
    g.stem(w / 2, y - w / 2, y + w / 2, b=0, t=0, w=0.785 * g.hw / g.sw)
    g.fixed_advance(fig_advance(g))


@r("minus", 0x2212, "figure")
def minus(g):
    g.bar(0, math_w(g), math_y(g), w=0.785)
    g.fixed_advance(fig_advance(g))


@r("equal", "=", "figure")
def equal(g):
    w, y = math_w(g), math_y(g)
    gap = g.cap * 0.105
    g.bar(0, w, y + gap, w=0.785)
    g.bar(0, w, y - gap, w=0.785)
    g.fixed_advance(fig_advance(g))


@r("multiply", 0x00D7, "figure")
def multiply(g):
    w, y = math_w(g) * 0.84, math_y(g)
    g.line(0, y - w / 2, w, y + w / 2, w=0.78 * g.hw / g.sw)
    g.line(0, y + w / 2, w, y - w / 2, w=0.78 * g.hw / g.sw)
    g.fixed_advance(fig_advance(g))


def _angle(g: G, x_open: float, x_tip: float):
    w, y = math_w(g), math_y(g)
    h = w * 0.44
    t = g.hw / g.sw
    (g.path(x_open, y + h, w=t)
     .to(x_tip, y, corner=True, w=t)
     .to(x_open, y - h, w=t)
     .done(miter=4, tag="angle"))


@r("less", "<", "figure")
def less(g):
    _angle(g, math_w(g), g.hw * 0.6)
    g.fixed_advance(fig_advance(g))


@r("greater", ">", "figure")
def greater(g):
    _angle(g, 0, math_w(g) - g.hw * 0.6)
    g.fixed_advance(fig_advance(g))


@r("asciicircum", "^", "figure")
def asciicircum(g):
    w = g.cw * 1.1
    t = g.hw / g.sw
    (g.path(0, g.cap * 0.56, w=t)
     .to(w / 2, g.cap, corner=True, w=t)
     .to(w, g.cap * 0.56, w=t)
     .done(start=H, end=H, miter=4, tag="caret"))
    g.fixed_advance(fig_advance(g))


@r("asciitilde", "~", "figure")
def asciitilde(g):
    w, y = math_w(g), math_y(g)
    a = g.cap * 0.075
    t = g.hw / g.sw
    (g.path(0, y - a * 0.6, w=t * 0.9)
     .curve((w * 0.12, y + a * 1.9), (w * 0.34, y + a * 1.5), w * 0.5, y, w=t * 1.2)
     .curve((w * 0.66, y - a * 1.5), (w * 0.88, y - a * 1.9), w, y + a * 0.6, w=t * 0.9)
     .done(tag="tilde"))
    g.fixed_advance(fig_advance(g))


@r("asterisk", "*", "figure")
def asterisk(g):
    rad = g.cap * 0.19
    cy = g.cap - rad
    t = 0.85 * g.hw / g.sw
    for k in range(3):
        a = math.radians(90 + 60 * k)
        dx, dy = math.cos(a) * rad, math.sin(a) * rad
        g.line(rad - dx, cy - dy, rad + dx, cy + dy, w=t / max(0.6, g.thick(complex(dx, dy)) / g.sw))
    g.frame(None, 0.6, 0.6)


@r("numbersign", "#", "figure")
def numbersign(g):
    w = g.cw * 1.5
    h = g.cap
    lean = w * 0.10
    t = 0.9 * g.hw / g.sw
    for fx in (0.30, 0.70):
        g.line(w * fx - lean, 0, w * fx + lean, h, w=t, cut0=H, cut1=H)
    for fy in (0.34, 0.66):
        g.bar(0, w, h * fy, w=0.78)
    g.fixed_advance(fig_advance(g))


@r("percent", "%", "figure")
def percent(g):
    t = 0.72
    rw = g.cw * 0.46 + g.sw * 0.95
    rh = g.cap * 0.45
    w = rw * 2 + g.cw * 0.5 + g.sw * 0.9
    g.ring(g.rw * t / 2, g.cap - rh, g.rw * t / 2 + rw, g.top(g.cap), scale=t)
    g.ring(w - rw - g.rw * t / 2, g.bot, w - g.rw * t / 2, rh, scale=t)
    a, b = g.diagonal(w * 0.24, 0, w * 0.76, g.cap, "c", "c", w=0.72)
    g.line(a.real, 0, b.real, g.cap, w=0.72, cut0=H, cut1=H)
    g.frame(None, 0.5, 0.5)


@r("dollar", "$", "figure")
def dollar(g):
    x0 = g.rw / 2
    x1 = x0 + g.cw * 0.92 + g.sw * 0.3
    s_curve(g, x0, x1, g.bot, g.top(g.cap))
    g.stem((x0 + x1) / 2, -g.cap * 0.11, g.cap * 1.11, b=0, t=0, w=0.62)
    g.fixed_advance(fig_advance(g))


@r("ampersand", "&", "upper")
def ampersand(g):
    w = g.capw(1.22, 1.22) + g.sw
    top, bot = g.top(g.cap), g.bot
    # upper loop
    ux0, ux1 = w * 0.20, w * 0.62
    uy0 = g.cap * 0.56
    ucx, ucy = (ux0 + ux1) / 2, (top + uy0) / 2
    urx, ury = (ux1 - ux0) / 2, (top - uy0) / 2
    # lower bowl
    lx0 = g.rw / 2
    lcy = bot + g.cap * 0.25
    lrx, lry = w * 0.40, g.cap * 0.25
    lcx = lx0 + lrx
    pe = g.epoint(ucx, ucy, urx, ury, -40)
    ps = complex(w * 0.98, g.cap * 0.02)
    (g.path(ps.real, ps.imag, fl=0.8)
     .curve((w * 0.74, g.cap * 0.28), (ux0 - urx * 0.25, ucy - ury * 0.75), ux0, ucy, w=0.785)
     .ellipse(ucx, ucy, urx, ury, 180, -40, w=0.8, w_side=0.9, w_top=0.85)
     .curve((pe.real - urx * 0.5, pe.imag - ury * 0.6), (lx0, lcy + lry * 0.9), lx0, lcy, w=g.p.round_weight)
     .ellipse(lcx, lcy, lrx, lry, 180, 360 + 40, fl=0.8)
     .done(start=H, end=g.curved_cut(), tag="amp"))
    g.frame(None, 0.5, 0.3)


@r("at", "@", "upper")
def at(g):
    w = g.capw(2.0, 2.0) + g.rw
    top, bot = g.top(g.cap), g.desc * 0.5
    t = 0.72
    cx, cy = w / 2, (top + bot) / 2
    rx, ry = (w - g.rw * t) / 2, (top - bot) / 2
    # inner bowl
    irx, iry = rx * 0.42, ry * 0.40
    g.ring(cx - irx, cy - iry, cx + irx * 0.9, cy + iry, scale=t)
    # stem that hooks into the outer ring
    xs = cx + irx * 0.9
    hook = g.epoint(cx, cy, rx, ry, -8)
    (g.path(xs, cy + iry * 1.05, w=1.0)
     .to(xs, cy - iry * 0.35)
     .curve((xs, cy - iry * 1.25), (hook.real - rx * 0.05, cy - iry * 1.5), hook.real, hook.imag)
     .ellipse(cx, cy, rx, ry, -8, 360 - 62)
     .done(scale=t, tag="outer"))
    g.frame(None, 0.6, 0.6)
