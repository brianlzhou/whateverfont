"""Greek: the monotonic alphabet of modern Greek.

The capitals and lowercase U+0391 to U+03C9 with the final sigma, the vowels with the tonos and the
dialytika (Ά Έ Ή Ί Ό Ύ Ώ ά έ ή ί ό ύ ώ Ϊ Ϋ ϊ ϋ ΐ ΰ), the tonos and the dialytika tonos as spacing
marks, the Greek question mark (which is a semicolon) and the ano teleia (a raised dot).

A capital that has the shape of a Latin one draws it: Α is A, Ρ is P. Γ Π Φ are the Г П Ф of the
Cyrillic set, and Ω and π are the ones the Latin set had already. The lowercase letters have shapes
of their own: α has a tail where its bowl meets the stroke, the stroke of β and of φ runs below the
baseline, γ crosses itself in a loop, η and ρ come down to the descender, and ε ζ ξ ς are drawn as
one curve. Only ο takes o, and μ takes the micro sign.

The tonos is steeper than the Latin acute. On a capital it stands in front of the letter, at the
height of its top; on a lowercase letter it stands over it. Polytonic Greek is not drawn.
"""

from __future__ import annotations

from ..geom import contour_bounds, translate
from ..glyph import G, H, V, Recipe, Recipes
from ..outline import intersection, rect
from .accents import ACCENTS, _box, _center, mark
from .cyrillic import _letter, ef, ge, pe, pe_width, small, ze
from .extended import _width_so_far
from .letters import LETTERS
from .lower import (LOWER, _bowl_width, arch, bowl, diagonal_slab, n_width, o_width, open_angle, round_box,
                    vee, x_strokes)
from .punct import PUNCT, dot_d
from .symbols import SYMBOLS
from .upper import UPPER

GREEK = Recipes()


def cap(name, uni):
    return GREEK.add(name, uni, case="upper")


def low(name, uni):
    return GREEK.add(name, uni, case="lower")


def _same(name: str, cp: int, base: str, source: Recipes, case: str):
    GREEK[name] = Recipe(name, _letter(base, source), cp, case)


# --------------------------------------------------------------------------
# The tonos
# --------------------------------------------------------------------------

def tonos(g: G, cx: float, y0: float, h: float, sc: float = 0.80):
    """The tonos: a steep stroke, a little heavier at the top, centered on ``cx`` from ``y0`` up ``h``."""
    lean = h * 0.30
    t = sc
    (g.path(cx - lean * 0.45, y0, w=t * 0.80)
     .to(cx + lean * 0.55, y0 + h, w=t * 1.08)
     .done(start=None, end=None, tag="mark"))


def tonos_lower(g: G, cx: float):
    y0, h, _, sc = _box(g, False)
    tonos(g, cx, y0, h * 1.04, sc)


def _alone_bounds(g: G, draw):
    s = G(g.p, g.name, g.case)
    s.recipes = g.recipes
    draw(s)
    return contour_bounds(s.outlines())


def tonos_capital(g: G):
    """Put the tonos in front of the capital that is drawn: at the height of its top, a little clear of
    its left side there, and move the letter to the right to make room."""
    h = g.cap
    y0, th = h * 0.80, h * 0.22
    contours = g.outlines()
    b = contour_bounds(contours)
    gap = g.sw * 0.55 + g.cap * 0.03
    band = intersection(contours, [rect(b[0] - 10, y0 - gap, b[2] + 10, h + g.o + 10)])
    left = contour_bounds(band)[0] if band else b[0]
    tb = _alone_bounds(g, lambda q: tonos(q, 0.0, y0, th))
    s0, h0 = len(g.strokes), len(g.shapes)
    tonos(g, left - gap - tb[2], y0, th)
    # the whole glyph moves right so that its left edge is at x = 0 again
    lo = min(left - gap - tb[2] + tb[0], b[0])
    width, _, right = g._frame if g._frame is not None else (None, "s", "s")
    g.shift(-lo)
    g.frame(None if width is None else width - lo, 0.45, right)


def _tonos_capital(base: str, source: Recipes):
    def recipe(g: G):
        g.base(base, source[base].fn)(g)
        tonos_capital(g)
    return recipe


def _tonos_lower(draw, center=None):
    def recipe(g: G):
        draw(g)
        tonos_lower(g, _center(g) if center is None else center(g))
    return recipe


def dialytika_tonos(g: G, cx: float):
    """The dialytika with the tonos between its dots (ΐ ΰ)."""
    y0, h, half, sc = _box(g, False)
    d = g.sw * 0.98
    gap = max(half * 0.78, d * 1.25)
    for sx in (-1, 1):
        g.dot(cx + sx * gap, y0 + d * 0.62, d)
    tonos(g, cx, y0, h * 1.12, sc)


# --------------------------------------------------------------------------
# Capitals
# --------------------------------------------------------------------------

for _cp, _name, _base in ((0x0391, "Alpha", "A"), (0x0392, "Beta", "B"), (0x0395, "Epsilon", "E"),
                          (0x0396, "Zeta", "Z"), (0x0397, "Eta", "H"), (0x0399, "Iota", "I"), (0x039A, "Kappa", "K"),
                          (0x039C, "Mu", "M"), (0x039D, "Nu", "N"), (0x039F, "Omicron", "O"), (0x03A1, "Rho", "P"),
                          (0x03A4, "Tau", "T"), (0x03A5, "Upsilon", "Y"), (0x03A7, "Chi", "X")):
    _same(_name, _cp, _base, UPPER, "upper")


@cap("Gamma", 0x0393)
def Gamma(g):
    g.frame(ge(g), "s", 0.25)


@cap("Delta", 0x0394)
def Delta(g):
    """Δ: a triangle that stands on its base."""
    w = g.capw(1.16, 1.24) + g.sw * 1.5
    pa, pc, _ = vee(g, 0, w, 0, g.cap, fl=0.0, down=False)
    g.bar(pa.real, pc.real, g.hw / 2, tag="base")
    g.frame(w, "d", "d")


@cap("Theta", 0x0398)
def Theta(g):
    """Θ: an O with a short bar that floats in its middle."""
    g.base("O", UPPER["O"].fn)(g)
    w = _width_so_far(g)
    inner = w - 2 * g.rw
    gap = max(inner * 0.20, g.sw * 0.55)
    g.bar(g.rw + gap, w - g.rw - gap, g.cap * 0.5, w=0.94)


@cap("Lambda", 0x039B)
def Lambda(g):
    """Λ: two strokes that meet in a point at the top."""
    w = g.capw(1.20, 1.28) + g.sw * 1.6
    vee(g, 0, w, 0, g.cap, down=False)
    g.frame(w, "d", "d")


@cap("Xi", 0x039E)
def Xi(g):
    """Ξ: three bars, the middle one shorter."""
    w = g.capw(1.0, 0.96) + g.sw
    ft, fb = g.flat_top(g.cap), g.hw / 2
    g.bar(0, w, ft, l=0.7, r=0.7)
    g.bar(w * 0.13, w * 0.87, g.cap * 0.5, l=0.5, r=0.5)
    g.bar(0, w, fb, l=0.7, r=0.7)
    g.beak(0, ft, side=-1, down=True)
    g.beak(w, ft, side=1, down=True)
    g.beak(0, fb, side=-1, down=False)
    g.beak(w, fb, side=1, down=False)
    for side, x in ((-1, w * 0.13), (1, w * 0.87)):
        g.beak(x, g.cap * 0.5, side=side, down=True, length=0.45)
        g.beak(x, g.cap * 0.5, side=side, down=False, length=0.45)
    g.frame(w, 0.4, 0.4)


@cap("Pi", 0x03A0)
def Pi(g):
    pe(g, pe_width(g))


@cap("Sigma", 0x03A3)
def Sigma(g):
    """Σ: an arm along the top, two strokes that meet in a point in the middle, and an arm along the foot."""
    w = g.capw(1.0, 0.98) + g.sw
    ft, fb = g.flat_top(g.cap), g.hw / 2
    xm = w * 0.50
    x0 = g.sw * 0.30
    (g.path(w, ft, fl=0.7)
     .to(x0, ft, corner=True)
     .to(xm, g.cap * 0.5, corner=True)
     .to(x0, fb, corner=True)
     .to(w, fb, fl=0.7)
     .done(start=V, end=V, miter=4, tag="sigma"))
    g.beak(w, ft, side=1, down=True)
    g.beak(w, fb, side=1, down=False)
    g.frame(w, 0.4, 0.4)


@cap("Phi", 0x03A6)
def Phi(g):
    h = g.cap
    ef(g, 0, h, h * 0.125 + g.hw / 2, h * 0.875 - g.hw / 2, g.capw(0.50, 0.56))


@cap("Psi", 0x03A8)
def Psi(g):
    """Ψ: a stem through a cup whose arms rise to the top."""
    h = g.cap
    w = 3 * g.sw + g.capw(0.80, 0.86)                # three strokes side by side, and white between them
    L, R = g.L, w - g.L
    yr = h * 0.62
    ybot = h * 0.27 + g.hw / 2
    square = 0.0 if g.serifed else None
    (g.path(L, h, fl=1.0)
     .flared_from(L, yr)
     .arc(w / 2, ybot, "v")
     .arc(R, yr, "h")
     .flared_to(R, h)
     .done(start=H, end=H, round_start=square, round_end=square, tag="cup"))
    g.slab(L, h, 1, 1, top=True, half=g.sw / 2 * g.fl)
    g.slab(R, h, 1, 1, top=True, half=g.sw / 2 * g.fl)
    g.stem(w / 2, 0, h)
    g.frame(w)


# Ά Έ Ή Ί Ό Ύ Ώ: the tonos in front of the capital
for _cp, _name, _base, _src in ((0x0386, "Alphatonos", "A", UPPER), (0x0388, "Epsilontonos", "E", UPPER),
                                (0x0389, "Etatonos", "H", UPPER), (0x038A, "Iotatonos", "I", UPPER),
                                (0x038C, "Omicrontonos", "O", UPPER), (0x038E, "Upsilontonos", "Y", UPPER),
                                (0x038F, "Omegatonos", "Omega", LETTERS)):
    GREEK[_name] = Recipe(_name, _tonos_capital(_base, _src), _cp, "upper")

GREEK["Iotadieresis"] = Recipe("Iotadieresis", _letter("Idieresis", ACCENTS), 0x03AA, "upper")
GREEK["Upsilondieresis"] = Recipe("Upsilondieresis", _letter("Ydieresis", ACCENTS), 0x03AB, "upper")


# --------------------------------------------------------------------------
# Lowercase
# --------------------------------------------------------------------------

def _under(pb, g: G, x_from: float):
    """Go on from the foot of a curve, moving right along the baseline at ``x_from``: turn down below the
    baseline and back to the left, in two quarter rounds (ζ ξ ς). The rounds are about as wide as they
    are tall, half the depth of the descender each: a wider one is tighter where it turns down, and a
    heavy stroke folds there."""
    y_end = g.dbot * 0.9
    r = (g.bot - y_end) / 2
    x_turn = x_from + r * 1.06
    return (pb.arc(x_turn, g.bot - r, "h", w=g.p.round_weight)
            .arc(x_turn - r * 0.96, y_end, "v", fl=1.0))


def _hook(g: G, x: float, y_top: float, rx: float, ry: float, fl0: float = 1.0):
    """A stroke down from ``y_top`` that turns right at the baseline (ι, τ, the tail of α)."""
    yh = g.bot + ry
    end = 270 + open_angle(g, 56, 40)
    return (g.path(x, y_top, fl=fl0)
            .flared_from(x, yh)
            .ellipse(x + rx, yh, rx, ry, 180, end, fl=1.0)
            .done(start=H, end=g.curved_cut(), round_start=0.0 if g.serifed and fl0 else None, tag="hook"))


@low("alpha", 0x03B1)
def alpha(g):
    """α: a round bowl on a stroke that comes down from the x-height and turns out to the right."""
    w0 = _bowl_width(g) * 0.97
    R = w0 - g.L
    bowl(g, R, g.rw / 2, branch=0.34)
    rx, ry = g.cw * 0.22, g.xh * 0.22
    _hook(g, R, g.xh, rx, ry)
    g.frame(None, "r", 0.3)


@low("beta", 0x03B2)
def beta(g):
    """β: a stem from the descender that rounds over at the top into two bowls, the lower one larger."""
    w = g.sw + g.cw * 0.80 + g.rw
    x0 = g.L
    top = g.top(g.asc)
    bot = g.bot
    ym = g.asc * 0.55
    xu = w * 0.90 - g.rw / 2
    xl = w - g.rw / 2
    r = (xu - x0) * 0.5
    xa = x0 + (xl - x0) * 0.40
    (g.path(x0, g.desc, fl=1.0)
     .flared_from(x0, top - r)
     .arc(x0 + r, top, "v")
     .arc(xu, top - (top - ym) * 0.5, "h", w=g.p.round_weight)
     .arc(xa, ym, "v")
     .to(x0 + g.sw * 0.2, ym)
     .done(start=H, end=V, round_start=0.0 if g.serifed else None, tag="upper"))
    (g.path(x0 + g.sw * 0.2, ym)
     .to(xa, ym)
     .arc(xl, (ym + bot) / 2, "h", w=g.p.round_weight)
     .arc(xa, bot, "v")
     .arc(x0, bot + (ym - bot) * 0.30, "h", w=g.p.join)
     .done(start=V, tag="lower"))
    g.slab(x0, g.desc, 1, 1, half=g.sw / 2 * g.fl)
    g.frame(w, "s", "r")


@low("gamma", 0x03B3)
def gamma(g):
    """γ: two arms that come down, bend toward each other, cross on the baseline and close in a loop.

    The arms bend so that they cross at a wide angle: two steep strokes would overlap over a long
    height and fill the loop. In the heaviest weights the loop still closes up.
    """
    w = n_width(g) * 0.98
    xm = w / 2
    yb = g.dbot                                     # the bottom of the loop
    # where the arms cross: just over the baseline, higher when a short descender and a heavy stroke
    # leave the loop no room
    yc = max(g.xh * 0.08, yb + g.sw * 1.5)
    d1 = complex(0.62, -1) / abs(complex(0.62, -1))  # the left arm at the crossing, down and to the right
    d2 = complex(d1.real, -d1.imag)                  # the left side of the loop, up and to the right
    top_dir = complex(0.20, -1)
    pa = complex(g.dx(top_dir), g.xh)                # the outer corner of each top end sits at the edge
    pc = complex(w - pa.real, g.xh)
    c = complex(xm, yc)
    reach = (yc - yb) * 0.28                         # how far the arms run on past the crossing
    p1, p2 = c + d1 * reach, c - d2 * reach
    a = max(w * 0.20, g.sw * 1.05)                   # how far the loop swings out to each side
    k = (p1.imag - yb) * 0.66
    ka = (g.xh - yc) * 0.42
    kb = (g.xh - yc) * 0.30
    square = 0.0 if g.serifed else None
    # Two strokes, so that neither crosses itself: the left arm runs on round the loop and up its left
    # side, and the right arm comes down across it to meet it there.
    thin = 0.80                                      # the loop is lighter than the arms, so it stays open
    (g.path(pa.real, g.xh, fl=1.0)
     .curve((pa.real + top_dir.real * ka, g.xh + top_dir.imag * ka), (c.real - d1.real * kb, c.imag - d1.imag * kb),
            c.real, c.imag, w=0.92)
     .to(p1.real, p1.imag, w=thin)
     .curve((p1.real + d1.real * k, p1.imag + d1.imag * k), (xm + a, yb), xm, yb, w=thin)
     .curve((xm - a, yb), (p2.real - d2.real * k, p2.imag - d2.imag * k), p2.real, p2.imag, w=thin)
     .done(start=H, round_start=square, tag="gamma"))
    e = complex(-d1.real, d1.imag)                   # the right arm at the crossing, down and to the left
    q = c + e * (reach + g.sw * 0.45)
    (g.path(pc.real, g.xh, fl=1.0)
     .curve((pc.real - top_dir.real * ka, g.xh + top_dir.imag * ka), (c.real - e.real * kb, c.imag - e.imag * kb),
            c.real, c.imag, w=0.92)
     .to(q.real, q.imag, w=thin)
     .done(start=H, round_start=square, tag="arm"))
    diagonal_slab(g, pa.real, g.xh, top_dir, top=True)
    diagonal_slab(g, pc.real, g.xh, complex(-top_dir.real, top_dir.imag), top=True)
    g.frame(w, "d", "d")


@low("delta", 0x03B4)
def delta(g):
    """δ: a round bowl, and a neck that rises from its top, leans left and turns right under the ascender."""
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.xh))
    top = g.flat_top(g.asc)
    x0 = w * 0.50
    xl = w * 0.30
    x_end = w * 0.88
    y0 = g.top(g.xh) - g.hw * 0.3                  # inside the top of the bowl, so the join is buried
    ym = g.xh + (g.asc - g.xh) * 0.45
    (g.path(x0, y0)
     .curve((x0 - (x0 - xl) * 0.9, y0 + (ym - y0) * 0.35), (xl, ym - (ym - y0) * 0.45), xl, ym)
     .curve((xl, ym + (top - ym) * 0.55), (xl + (x_end - xl) * 0.25, top), xl + (x_end - xl) * 0.55, top)
     .to(x_end, top, fl=1.0)
     .done(end=V, tag="neck"))
    g.frame(w, "r", "r")


@low("epsilon", 0x03B5)
def epsilon(g):
    """ε: the з turned over: two bowls open to the right."""
    small(g, ze)
    b = contour_bounds(g.outlines())
    g.mirror_x((b[0] + b[2]) / 2)
    g.frame(None, "r", 0.45)


@low("zeta", 0x03B6)
def zeta(g):
    """ζ: an arm under the ascender, a curve down to the left and along the baseline, and a hook below it."""
    w = o_width(g) * 0.88
    ft = g.flat_top(g.asc * 0.97)
    x0 = g.rw / 2
    xb = w * 0.86
    yl = g.xh * 0.42
    xr = w * 0.78
    g.bar(w * 0.12, xb, ft, l=0.5)
    d = complex(-0.62, -1) * (ft - yl) * 0.26
    xm = (x0 + xr) / 2
    pb = (g.path(xb - g.sw * 0.2, ft)
          .curve((xb - g.sw * 0.2 + d.real, ft + d.imag), (x0, yl + (ft - yl) * 0.45), x0, yl)
          .arc(xm, g.bot, "v"))
    _under(pb, g, xm).done(start=None, end=V, tag="zeta")
    g.frame(w, "r", 0.4)


@low("eta", 0x03B7)
def eta(g):
    """η: an n whose right stem runs on down to the descender."""
    w = n_width(g)
    g.stem(g.L, 0, g.xh)
    arch(g, g.L, w - g.L, foot=g.desc)
    g.frame(w, "s", 0.94)


@low("theta", 0x03B8)
def theta(g):
    """θ: a tall narrow oval, as high as the ascender, with a bar across its middle."""
    w = o_width(g) * 0.92
    top = g.top(g.asc)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, top)
    g.bar(g.rw / 2, w - g.rw / 2, (top + g.bot) / 2, w=0.94)
    g.frame(w, "r", "r")


def _iota(g: G):
    rx, ry = g.cw * 0.24, g.xh * 0.22
    _hook(g, g.L, g.xh, rx, ry)
    g.slab(g.L, g.xh, 1, 0, top=True)
    g.frame(None, "s", 0.3)


@low("iota", 0x03B9)
def iota(g):
    """ι: a short stem that turns right at the foot."""
    _iota(g)


GREEK["kappa"] = Recipe("kappa", _letter("kgreenlandic", LETTERS), 0x03BA, "lower")


@low("lambda", 0x03BB)
def lambda_(g):
    """λ: a long stroke from the top left down to the right foot, and a short leg out to the left."""
    w = n_width(g) * 1.02
    pa, pb = g.diagonal(w * 0.10, g.asc, w, 0, "l", "r")
    square = 0.0 if g.serifed else None
    g.line(pa.real, g.asc, pb.real, 0, b=0.6, t=1, cut0=H, cut1=H, round0=square, round1=square, tag="long")
    t = 0.40                                       # where the leg meets the long stroke, from the foot
    j = pb + (pa - pb) * t
    qa, _ = g.diagonal(0, 0, j.real, j.imag, "l", "c")
    g.line(qa.real, 0, j.real, j.imag, b=1, t=0, cut0=H, cut1=pa - pb, round0=square, tag="leg")
    diagonal_slab(g, pb.real, 0, pb - pa, top=False, left=0.6, right=1.0)
    diagonal_slab(g, qa.real, 0, qa - j, top=False, left=1.0, right=0.6)
    g.slab(pa.real, g.asc, 1.0, 0.0, top=True, half=g.dx(pb - pa))
    g.frame(w, "d", "d")


GREEK["mu"] = Recipe("mu", _letter("micro", SYMBOLS), 0x03BC, "lower")


@low("nu", 0x03BD)
def nu(g):
    """ν: a straight left arm down to the point, and a right arm that bows out as it rises."""
    w = n_width(g) * 0.98
    xm = w * 0.46
    cut = 0.0 - g.o * 1.2 * max(0.0, 1 - g.p.apex * 1.5)
    pa, _ = g.diagonal(0, g.xh, xm, 0, "l", "c")
    pc = complex(w - g.L * 1.05, g.xh)
    ya = g.apex_y(xm, pa, complex(xm + (pc.real - xm) * 0.55, g.xh * 0.5), cut)
    square = 0.0 if g.serifed else None
    (g.path(pa.real, g.xh, fl=1.0)
     .flared_from(xm, ya, corner=True, apex=cut)
     .curve((xm + (pc.real - xm) * 0.42, ya + g.xh * 0.18), (pc.real, g.xh * 0.42), pc.real, g.xh * 0.80)
     .to(pc.real, g.xh, fl=1.0)
     .done(start=H, end=H, round_start=square, tag="nu"))
    diagonal_slab(g, pa.real, g.xh, complex(xm, ya) - pa, top=True)
    g.frame(w, "d", "s")


@low("xi", 0x03BE)
def xi(g):
    """ξ: an arm under the ascender, a small bowl and a larger one open to the right, and a hook below."""
    w = o_width(g) * 0.88
    ft = g.flat_top(g.asc * 0.97)
    x0 = g.rw / 2
    xb = w * 0.86
    ym = g.xh * 0.98                               # the waist between the bowls
    xr = w * 0.78
    xw = w * 0.62
    g.bar(w * 0.12, xb, ft, l=0.5)
    # the small bowl: from under the arm, out to the left and back in to the waist
    (g.path(x0 + w * 0.30, ft)
     .curve((x0 + w * 0.06, ft - (ft - ym) * 0.25), (x0 + w * 0.06, ym + (ft - ym) * 0.18), x0 + w * 0.30, ym)
     .to(xw, ym)
     .done(start=None, end=V, tag="upper"))
    # the large bowl: from the waist round the left, along the baseline and down into the hook
    xm = (x0 + xr) / 2
    pb = (g.path(x0 + w * 0.36, ym)
          .curve((x0 + w * 0.02, ym), (x0, ym - (ym - g.bot) * 0.25), x0, (ym + g.bot) * 0.45)
          .arc(xm, g.bot, "v"))
    _under(pb, g, xm).done(start=None, end=V, tag="lower")
    g.frame(w, "r", 0.4)


GREEK["omicron"] = Recipe("omicron", _letter("o", LOWER), 0x03BF, "lower")


@low("rho", 0x03C1)
def rho(g):
    """ρ: a round bowl with a stem from its left side down to the descender."""
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.xh))
    g.stem(g.rw / 2, g.desc, g.xh * 0.5, b=1, t=0, w=g.p.round_weight)
    g.frame(w, "r", "r")


@low("sigma1", 0x03C2)
def sigma1(g):
    """ς: a c whose foot runs on below the baseline and hooks back to the left."""
    cx, cy, rx, ry = round_box(g, o_width(g) * 0.92)
    a0 = open_angle(g, 30, 50)
    p0 = g.epoint(cx, cy, rx, ry, a0)
    pb = (g.path(p0.real, p0.imag, fl=1.0)
          .ellipse(cx, cy, rx, ry, a0, 270))
    _under(pb, g, cx).done(start=g.curved_cut(), end=V, tag="sigma")
    g.frame(None, "r", 0.3)


@low("sigma", 0x03C3)
def sigma(g):
    """σ: a round bowl with an arm along the x-height out to the right."""
    wo = o_width(g) * 0.98
    g.ring(g.rw / 2, g.bot, wo - g.rw / 2, g.top(g.xh))
    w = wo + g.cw * 0.26
    g.bar(wo * 0.5, w, g.flat_top(g.xh), r=0.6)
    g.beak(w, g.flat_top(g.xh), down=True, length=0.6)
    g.frame(w, "r", 0.3)


@low("tau", 0x03C4)
def tau(g):
    """τ: a bar along the x-height, and a stem that turns right at the foot."""
    w = n_width(g) * 0.90
    ft = g.flat_top(g.xh)
    g.bar(0, w, ft, l=0.5, r=0.6)
    _hook(g, w * 0.44, ft, g.cw * 0.22, g.xh * 0.22, fl0=0.0)
    g.beak(0, ft, side=-1, down=True, length=0.6)
    g.beak(w, ft, side=1, down=True, length=0.6)
    g.frame(w, 0.3, 0.3)


def _upsilon(g: G, w: float):
    L, R = g.L, w - g.L
    yr = g.bot + (R - L) * 0.52
    square = 0.0 if g.serifed else None
    (g.path(L, g.xh, fl=1.0)
     .flared_from(L, yr)
     .arc(w / 2, g.bot, "v")
     .arc(R, yr, "h")
     .to(R, g.xh * 0.90)
     .to(R, g.xh, fl=1.0)
     .done(start=H, end=H, round_start=square, tag="upsilon"))
    g.slab(L, g.xh, 1, 0, top=True, half=g.sw / 2 * g.fl)


@low("upsilon", 0x03C5)
def upsilon(g):
    """υ: a round-bottomed cup, with no stem."""
    w = n_width(g) * 0.98
    _upsilon(g, w)
    g.frame(w, "s", "s")


@low("phi", 0x03C6)
def phi(g):
    """φ: a stem from the descender to the ascender through a wide round bowl."""
    ef(g, g.desc, g.asc, g.bot, g.top(g.xh), g.cw * 0.50)


@low("chi", 0x03C7)
def chi(g):
    """χ: two strokes that cross, from the x-height to the descender."""
    w = n_width(g) * 0.98
    s0, h0 = len(g.strokes), len(g.shapes)
    x_strokes(g, w, g.xh - g.desc, w * 0.03)
    g.transform(translate(0.0, g.desc), s0, h0)
    g.frame(w, "d", "d")


@low("psi", 0x03C8)
def psi(g):
    """ψ: a stem from the descender to the ascender through a cup that rises to the x-height."""
    w = 3 * g.sw + g.cw * 0.95
    _upsilon_cup(g, w)
    g.stem(w / 2, g.desc, g.asc)
    g.frame(w, "s", "s")


def _upsilon_cup(g: G, w: float):
    L, R = g.L, w - g.L
    yr = g.bot + (R - L) * 0.46
    square = 0.0 if g.serifed else None
    (g.path(L, g.xh, fl=1.0)
     .flared_from(L, yr)
     .arc(w / 2, g.bot, "v")
     .arc(R, yr, "h")
     .flared_to(R, g.xh)
     .done(start=H, end=H, round_start=square, round_end=square, tag="cup"))
    g.slab(L, g.xh, 1, 0, top=True, half=g.sw / 2 * g.fl)
    g.slab(R, g.xh, 1, 0, top=True, half=g.sw / 2 * g.fl)


@low("omega", 0x03C9)
def omega(g):
    """ω: two round bowls side by side, joined by a short stem in the middle."""
    w = 2.6 * g.sw + g.cw * 1.40
    L, R = g.L, w - g.L
    xm = w / 2
    ry = (xm - L) * 0.56
    yr = g.bot + ry
    yj = g.xh * 0.30
    ym = g.xh * 0.62
    square = 0.0 if g.serifed else None
    for x_out in (L, R):
        x1 = (x_out + xm) / 2
        (g.path(x_out, g.xh, fl=1.0)
         .flared_from(x_out, yr)
         .arc(x1, g.bot, "v")
         .arc(xm, yj, "h", w=g.p.join)
         .done(start=H, round_start=square, tag="bowl"))
    g.stem(xm, yj - g.sw * 0.5, ym, b=0, serif0=False, serif1=False)
    g.slab(L, g.xh, 1, 0, top=True, half=g.sw / 2 * g.fl)
    g.frame(w, "s", "s")


# Lowercase with the tonos and the dialytika

def _drawn(name: str, source: Recipes):
    def draw(g: G):
        g.base(name, source[name].fn)(g)
    return draw


def _stem_x(g: G) -> float:
    return g.L


for _cp, _name, _base, _src, _center_fn in ((0x03AC, "alphatonos", "alpha", GREEK, None),
                                            (0x03AD, "epsilontonos", "epsilon", GREEK, None),
                                            (0x03AE, "etatonos", "eta", GREEK, None),
                                            (0x03AF, "iotatonos", "iota", GREEK, _stem_x),
                                            (0x03CC, "omicrontonos", "o", LOWER, None),
                                            (0x03CD, "upsilontonos", "upsilon", GREEK, None),
                                            (0x03CE, "omegatonos", "omega", GREEK, None)):
    GREEK[_name] = Recipe(_name, _tonos_lower(_drawn(_base, _src), _center_fn), _cp, "lower")


def _dieresis(base: str, center=None):
    def recipe(g: G):
        g.base(base, GREEK[base].fn)(g)
        mark(g, "dieresis", _center(g) if center is None else center(g), False)
    return recipe


def _dialytika_tonos(base: str, center=None):
    def recipe(g: G):
        g.base(base, GREEK[base].fn)(g)
        dialytika_tonos(g, _center(g) if center is None else center(g))
    return recipe


GREEK["iotadieresis"] = Recipe("iotadieresis", _dieresis("iota", _stem_x), 0x03CA, "lower")
GREEK["upsilondieresis"] = Recipe("upsilondieresis", _dieresis("upsilon"), 0x03CB, "lower")
GREEK["iotadieresistonos"] = Recipe("iotadieresistonos", _dialytika_tonos("iota", _stem_x), 0x0390, "lower")
GREEK["upsilondieresistonos"] = Recipe("upsilondieresistonos", _dialytika_tonos("upsilon"), 0x03B0, "lower")


# --------------------------------------------------------------------------
# Marks and punctuation
# --------------------------------------------------------------------------

@low("tonos", 0x0384)
def tonos_spacing(g):
    half = g.p.n_counter * 0.27 + g.sw * 0.25
    tonos_lower(g, half * 0.5 + g.sw * 0.2)
    g.frame(None, 0.5, 0.5)


@low("dieresistonos", 0x0385)
def dieresistonos(g):
    half = g.p.n_counter * 0.27 + g.sw * 0.25
    dialytika_tonos(g, half + g.sw * 0.2)
    g.frame(None, 0.5, 0.5)


GREEK["uni037E"] = Recipe("uni037E", _letter("semicolon", PUNCT), 0x037E, "lower")


@low("anoteleia", 0x0387)
def anoteleia(g):
    """·: the Greek upper stop, a dot at the top of the x-height."""
    d = dot_d(g)
    g.dot(d / 2, g.xh - d / 2 - g.o, d)
    g.frame(d, 0.9, 0.9)


# in the order of the code points, so the font lists them as Unicode does
_by_code = sorted(GREEK.values(), key=lambda rec: rec.unicode)
GREEK.clear()
GREEK.update((rec.name, rec) for rec in _by_code)

#: Every character of the set, for ``Recipes.only(greek=True)``; with Ω and π, which the Latin set has.
ALPHABET = "".join(chr(rec.unicode) for rec in GREEK.values()) + "Ωπ"
