"""More Latin letters: the rest of Latin Extended-A, Pinyin, Azerbaijani, Yoruba, Igbo and Hausa.

Ĳ ĳ ĸ Ŀ ŀ Ŋ ŋ Ŧ ŧ ſ ƒ ⁱ, the Pinyin vowels with a caron and ü with a tone mark (ǎ ǘ ǚ), the schwa
ə Ə, the ʻokina and the modifier apostrophe ʻ ʼ, ṣ Ṣ ṅ Ṅ, the hooked letters ɓ ɗ ƙ Ɓ Ɗ Ƙ, and Ω and π.

Most are drawn from the basic recipes: Ŧ is T with a bar, ǘ is u with a dieresis and an acute.
"""

from __future__ import annotations

from ..geom import contour_bounds
from ..glyph import G, H, V, Recipes
from .accents import _center, _compose, mark
from .extended import _then, _width_so_far
from .lower import LOWER, _bowl_width, bowl, n_width, open_angle, round_box
from .punct import PUNCT, dot_d
from .upper import UPPER, h_width
from .upper import o_width as cap_o_width
from .vietnamese import dot_below, stack

LETTERS = Recipes()


def r(name, uni, case="lower"):
    return LETTERS.add(name, uni, case=case)


# --------------------------------------------------------------------------
# Latin Extended-A
# --------------------------------------------------------------------------

@r("IJ", 0x0132, "upper")
def IJ(g):
    g.base("I", UPPER["I"].fn)(g)
    gap = g.sidebearing("s") * 0.95 + g.sidebearing(0.3)
    _then(g, "J", UPPER, _width_so_far(g) + gap)
    g.frame(None, "s", "s")


@r("ij", 0x0133)
def ij(g):
    g.base("i", LOWER["i"].fn)(g)
    gap = g.sidebearing("s") * 1.6
    _then(g, "j", LOWER, _width_so_far(g) + gap)
    g.frame(None, "s", "s")


@r("kgreenlandic", 0x0138)
def kra(g):
    """ĸ: a k as tall as the x-height."""
    w = g.sw + g.cw * 0.96 + g.sw * 0.25
    g.stem(g.L, 0, g.xh)
    pa, pb = g.diagonal(g.sw * 0.75, g.xh * 0.36, w * 0.97, g.xh, "c", "r")
    square = 0.0 if g.serifed else None
    g.line(pa.real, pa.imag, pb.real, pb.imag, b=0, t=1, cut0=V, cut1=H, tag="arm", round1=square)
    j = pa + (pb - pa) * 0.34
    qa, qb = g.diagonal(j.real, j.imag, w, 0, "c", "r")
    g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=pb - pa, cut1=H, tag="leg", round1=square)
    from .lower import diagonal_slab
    diagonal_slab(g, pb.real, g.xh, pb - pa, top=True, left=0.7, right=0.7)
    diagonal_slab(g, qb.real, 0, qb - qa, top=False, left=0.7, right=1.0)
    g.frame(w, "s", "d")


@r("Ldot", 0x013F, "upper")
def Ldot(g):
    """Ŀ: the Catalan L with a middle dot between the stem and the end of the arm."""
    g.base("L", UPPER["L"].fn)(g)
    d = dot_d(g)
    g.dot(g.sw + d * 1.05, g.cap * 0.50, d)


@r("ldot", 0x0140)
def ldot(g):
    """ŀ: l with a middle dot on its right."""
    g.base("l", LOWER["l"].fn)(g)
    d = dot_d(g)
    x = _width_so_far(g) + g.sidebearing(0.5) + d / 2
    g.dot(x, g.xh * 0.52, d)
    g.frame(None, "s", 0.6)


def _eng(g: G, h: float, w: float):
    """An n whose right stem runs down past the baseline and hooks to the left, like j."""
    x1 = w - g.L
    top = g.top(h)
    xm = g.L + (x1 - g.L) * 0.5
    ysh = max(top - (x1 - xm) * 1.02, h * 0.3)
    g.stem(g.L, 0, h)
    rx = min(g.cw * 0.40, (x1 - g.L) * 0.62)
    yh = g.desc * 0.40
    ry = yh - g.dbot
    end = -(90 + open_angle(g, 46, 60))
    (g.path(g.L, h * 0.60, g.p.join)
     .arc(xm, top, "v", k0=0.42, k1=0.62)
     .arc(x1, ysh, "h")
     .to(x1, yh)
     .ellipse(x1 - rx, yh, rx, ry, 0, end, fl=1.0)
     .done(end=g.curved_cut(), tag="arch"))
    g.frame(w, "s", "s")


@r("Eng", 0x014A, "upper")
def Eng(g):
    _eng(g, g.cap, h_width(g))


@r("eng", 0x014B)
def eng(g):
    _eng(g, g.xh, n_width(g))


@r("Tbar", 0x0166, "upper")
def Tbar(g):
    g.base("T", UPPER["T"].fn)(g)
    w = _width_so_far(g)
    g.bar(w * 0.22, w * 0.78, g.cap * 0.47, w=0.9)


@r("tbar", 0x0167)
def tbar(g):
    g.base("t", LOWER["t"].fn)(g)
    x = g.cw * 0.28 + g.L
    g.bar(x - g.cw * 0.25, x + g.cw * 0.32, g.xh * 0.46, w=0.9)


@r("longs", 0x017F)
def longs(g):
    """ſ: the f without its crossbar."""
    g.base("f", LOWER["f"].fn)(g)
    g.strokes = [s for s in g.strokes if s.tag != "bar"]
    g.frame(None, 0.6, 0.1)


@r("florin", 0x0192)
def florin(g):
    """ƒ: a slanted f that hooks right at the top and left under the baseline."""
    rx = g.cw * 0.34
    top = g.top(g.asc)
    ry = (g.asc - g.xh) * 0.62
    yh = top - ry
    x = g.cw * 0.40 + g.L
    yb = g.desc * 0.42
    rby = yb - g.dbot
    end_t = 90 - open_angle(g, 52, 38)
    end_b = -(90 + open_angle(g, 46, 60))
    pb = g.epoint(x - rx, yb, rx, rby, end_b)
    (g.path(pb.real, pb.imag, fl=1.0)
     .ellipse(x - rx, yb, rx, rby, end_b, 0)
     .to(x, yh)
     .ellipse(x + rx, yh, rx, ry, 180, end_t, fl=1.0)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="hook"))
    g.bar(x - g.cw * 0.36, x + g.cw * 0.36, g.flat_top(g.xh), l=0.5, r=0.5)
    t = 0.18                                        # about ten degrees
    g.transform((1.0, 0.0, t, 1.0, -t * g.xh / 2, 0.0))
    g.frame(None, 0.3, 0.3)


@r("isuperior", 0x2071)
def isuperior(g):
    """ⁱ: a small i whose x-height reaches the cap height."""
    from .symbols import SUP_WEIGHT, _shrink, _since
    start = _since(g)
    g.base("i", LOWER["i"].fn)(g)
    g._frame = None
    k = 0.58
    _shrink(g, start, k, 0, g.cap - g.xh * k, k * SUP_WEIGHT)
    g.frame(None, 0.5, 0.5)


def _omega(g: G):
    """Ω: an open round on two short feet."""
    w = cap_o_width(g)
    rx = (w - g.rw) / 2
    top = g.top(g.cap)
    cy = g.cap * 0.56
    ry = top - cy
    cx = g.rw / 2 + rx
    a = 58
    pr = g.epoint(cx, cy, rx, ry, -a)
    pl = g.epoint(cx, cy, rx, ry, 180 + a)
    fb = g.hw / 2
    foot = g.sw * 1.15
    xl, xr = pl.real + rx * 0.08, pr.real - rx * 0.08
    (g.path(xl - foot, fb)
     .to(xl, fb, corner=True)
     .to(pl.real, pl.imag)
     .ellipse(cx, cy, rx, ry, 180 + a, -a)
     .to(xr, fb, corner=True)
     .to(xr + foot, fb)
     .done(start=V, end=V, miter=4, tag="omega"))
    g.frame(None, 0.5, 0.5)


@r("Omega", 0x03A9, "upper")
def Omega(g):
    _omega(g)


@r("Ohm", 0x2126, "upper")
def Ohm(g):
    _omega(g)


@r("pi", 0x03C0)
def pi(g):
    w = n_width(g) * 1.04
    g.bar(0, w, g.flat_top(g.xh), l=0.4, r=0.4)
    g.stem(w * 0.27, 0, g.xh, t=0, serif1=False)
    g.stem(w * 0.73, 0, g.xh, t=0, serif1=False)
    g.frame(w, 0.4, 0.4)


# --------------------------------------------------------------------------
# Azerbaijani, Yoruba, Igbo, the okina
# --------------------------------------------------------------------------

def _e_shape(g: G, width: float, h: float, inset: float = 0.08):
    """The e, ``width`` wide and ``h`` high (the cap height for Ə)."""
    import math
    cx, cy, rx, ry = round_box(g, width, h)
    ym = h * 0.53
    ab = math.degrees(math.asin(max(-0.9, min(0.9, (ym - cy) / ry))))
    a1 = open_angle(g, 28, 48)
    pb = g.epoint(cx, cy, rx, ry, ab)
    # the bar starts a little inside the bowl: an end that lies exactly on its edge can stop an
    # effect from merging the two
    (g.path(cx - rx + g.sw * inset, ym)
     .to(pb.real, pb.imag, corner=True)
     .ellipse(cx, cy, rx, ry, ab, 360 - a1, fl=1.0)
     .done(end=g.curved_cut(), tag="e"))
    return cx


@r("schwa", 0x0259)
def schwa(g):
    """ə: the e turned over."""
    g.base("e", LOWER["e"].fn)(g)
    b = contour_bounds(g.outlines())
    g.rotate(180, (b[0] + b[2]) / 2, g.xh / 2)
    g.frame(None, 0.36, "r")


@r("Schwa", 0x018F, "upper")
def Schwa(g):
    """Ə: a capital e turned over."""
    cx = _e_shape(g, cap_o_width(g) * 0.92, g.cap)
    g.rotate(180, cx, g.cap / 2)
    g.frame(None, 0.36, "r")


@r("uni02BB", 0x02BB)
def okina(g):
    """ʻ: the okina, a turned comma. It is a letter, so it has the shape of the left quote."""
    g.base("quoteleft", PUNCT["quoteleft"].fn)(g)


@r("uni02BC", 0x02BC)
def apostrophemod(g):
    """ʼ: the modifier apostrophe, a letter with the shape of the right quote."""
    g.base("quoteright", PUNCT["quoteright"].fn)(g)


def _dot_below(base: str, source: Recipes, upper: bool):
    def recipe(g: G):
        g.base(base, source[base].fn)(g)
        dot_below(g, _center(g), upper)
    return recipe


def _dot_above(base: str, source: Recipes, upper: bool):
    def recipe(g: G):
        g.base(base, source[base].fn)(g)
        mark(g, "dotaccent", _center(g), upper)
    return recipe


_Rec = type(LOWER["n"])
for _name, _uni, _base, _src, _up, _fn in (("sdotbelow", 0x1E63, "s", LOWER, False, _dot_below),
                                          ("Sdotbelow", 0x1E62, "S", UPPER, True, _dot_below),
                                          ("ndotaccent", 0x1E45, "n", LOWER, False, _dot_above),
                                          ("Ndotaccent", 0x1E44, "N", UPPER, True, _dot_above)):
    LETTERS[_name] = _Rec(_name, _fn(_base, _src, _up), _uni, "upper" if _up else "lower")


# --------------------------------------------------------------------------
# Hausa: letters with a hook
# --------------------------------------------------------------------------

def _hooked_stem(g: G, x: float, foot_slab=(1.0, 0.0)):
    """A stem from the baseline whose top turns to the right like the top of an f."""
    rx = g.cw * 0.34
    top = g.top(g.asc)
    ry = (g.asc - g.xh) * 0.60
    yh = top - ry
    end = 90 - open_angle(g, 52, 38)
    (g.path(x, 0, fl=1.0)
     .flared_from(x, yh)
     .ellipse(x + rx, yh, rx, ry, 180, end, fl=1.0)
     .done(start=H, end=g.curved_cut(), round_start=0.0 if g.serifed else None, tag="hook"))
    if foot_slab:
        g.slab(x, 0, foot_slab[0], foot_slab[1], half=g.sw / 2 * g.fl)


@r("bhook", 0x0253)
def bhook(g):
    w = _bowl_width(g)
    _hooked_stem(g, g.L)
    bowl(g, g.L, w - g.rw / 2)
    g.frame(None, "s", "r")


@r("dhook", 0x0257)
def dhook(g):
    w = _bowl_width(g)
    _hooked_stem(g, w - g.L, (0.0, 0.55))
    bowl(g, w - g.L, g.rw / 2)
    g.frame(None, "r", 0.3)


@r("khook", 0x0199)
def khook(g):
    w = g.sw + g.cw * 0.96 + g.sw * 0.25
    _hooked_stem(g, g.L)
    pa, pb = g.diagonal(g.sw * 0.75, g.xh * 0.36, w * 0.97, g.xh, "c", "r")
    square = 0.0 if g.serifed else None
    g.line(pa.real, pa.imag, pb.real, pb.imag, b=0, t=1, cut0=V, cut1=H, tag="arm", round1=square)
    j = pa + (pb - pa) * 0.34
    qa, qb = g.diagonal(j.real, j.imag, w, 0, "c", "r")
    g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=pb - pa, cut1=H, tag="leg", round1=square)
    g.frame(None, "s", "d")


def _cap_hook(g: G, letter: str):
    """Ɓ Ɗ: the letter with its stem turned over to the left at the top, in a hook."""
    rx = g.cw * 0.24
    top = g.top(g.cap)
    ry = g.cap * 0.17
    end = 180 - (90 - open_angle(g, 52, 38))
    reach = rx * 1.75
    _then(g, letter, UPPER, reach)
    x = reach + g.L
    yh = top - ry
    (g.path(x, g.cap * 0.62, w=1.0)
     .to(x, yh)
     .ellipse(x - rx, yh, rx, ry, 0, end, fl=1.0)
     .done(end=g.curved_cut(), tag="hook"))
    g.frame(None, 0.4, "r" if letter == "D" else 0.6)


@r("Bhook", 0x0181, "upper")
def Bhook(g):
    _cap_hook(g, "B")


@r("Dhook", 0x018A, "upper")
def Dhook(g):
    _cap_hook(g, "D")


@r("Khook", 0x0198, "upper")
def Khook(g):
    """Ƙ: the upper arm of the K ends in a hook that turns over to the right."""
    w = g.sw + g.capw(1.06, 1.08) + g.sw * 0.3
    g.stem(g.L, 0, g.cap)
    rx = g.cw * 0.20
    ry = g.cap * 0.15
    top = g.top(g.cap)
    xe = w * 0.80                                   # where the arm meets the hook
    pa, pb = g.diagonal(g.sw * 0.75, g.cap * 0.40, xe, top - ry, "c", "c")
    d = pb - pa
    end = 90 - open_angle(g, 60, 40)
    (g.path(pa.real, pa.imag)
     .to(pb.real, pb.imag)
     .curve((pb.real + d.real * 0.35, pb.imag + d.imag * 0.35), (pb.real + rx * 0.2, top), pb.real + rx * 0.9, top)
     .ellipse(pb.real + rx * 0.9, top - ry, rx * 1.1, ry, 90, end, fl=1.0)
     .done(start=V, end=g.curved_cut(), tag="arm"))
    j = pa + (pb - pa) * 0.32
    qa, qb = g.diagonal(j.real, j.imag, w, 0, "c", "r")
    square = 0.0 if g.serifed else None
    g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=pb - pa, cut1=H, tag="leg", round1=square)
    g.frame(None, "s", "d")


# --------------------------------------------------------------------------
# Pinyin: the third tone (a caron) on a e i o u, and ü with each tone
# --------------------------------------------------------------------------

for _ch in "ǍǎǏǐǑǒǓǔ":
    _compose(_ch, LETTERS)


def _u_tone(base: str, tone: str):
    upper = base.isupper()
    source = UPPER if upper else LOWER

    def recipe(g: G):
        g.base(base, source[base].fn)(g)
        stack(g, ["dieresis", tone], _center(g), upper)
    return recipe


for _uni, _base, _tone in ((0x01D5, "U", "macron"), (0x01D6, "u", "macron"), (0x01D7, "U", "acute"),
                           (0x01D8, "u", "acute"), (0x01D9, "U", "caron"), (0x01DA, "u", "caron"),
                           (0x01DB, "U", "grave"), (0x01DC, "u", "grave")):
    _name = f"{_base}dieresis{_tone}"
    LETTERS[_name] = _Rec(_name, _u_tone(_base, _tone), _uni, "upper" if _base.isupper() else "lower")
