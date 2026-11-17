"""Vietnamese: the horn of ơ and ư, the hook above, the dot below, and letters with two marks.

Each of the twelve vowels a ă â e ê i o ô ơ u ư y takes one of five tone marks: the grave, the
hook above, the tilde, the acute or the dot below. On ă â ê ô the tone mark joins a breve or a
circumflex, so many letters carry two marks. Vietnamese type sets them by these rules:

- The horn is part of the letter. It grows from the upper right of o and u and turns up, clear of
  any mark above.
- With a circumflex, the acute, the grave and the hook above sit to the upper right of it, not
  straight on top. The tilde sits on top.
- With a breve, the tone mark is smaller and sits on it: an acute, a grave or a hook down in its
  cup, a tilde on top. So the stack stays compact.
- The dot below hangs under the letter, clear of the baseline.
- Capitals use flatter marks, so that a line of capitals stays as low as it can.

Marks that share a letter are placed by measuring their outlines, so they keep a gap at every
weight and width.
"""

from __future__ import annotations

import unicodedata

from ..geom import contour_area, contour_bounds, transform_contour, unit
from ..glyph import G, H, Recipes
from ..outline import dilate, intersection, rect
from .accents import MARKS, _box, _center, mark
from .extended import EXTENDED
from .lower import LOWER
from .upper import UPPER

VIETNAMESE = Recipes()

#: The letters of the Vietnamese alphabet that the rest of the Latin set does not have
#: (Ỳ ỳ, à, ă, đ and the others are there already).
LETTERS = "".join(chr(c) for c in range(0x1EA0, 0x1EFA) if c not in (0x1EF2, 0x1EF3)) + "ƠơƯư"

#: Every letter Vietnamese text uses, for ``Recipes.only``: the alphabet with all its tone marks.
ALPHABET = ("aàảãáạăằẳẵắặâầẩẫấậbcdđeèẻẽéẹêềểễếệghiìỉĩíịklmnoòỏõóọôồổỗốộơờởỡớợpqrstuùủũúụưừửữứựvxyỳỷỹýỵ"
            "AÀẢÃÁẠĂẰẲẴẮẶÂẦẨẪẤẬBCDĐEÈẺẼÉẸÊỀỂỄẾỆGHIÌỈĨÍỊKLMNOÒỎÕÓỌÔỒỔỖỐỘƠỜỞỠỚỢPQRSTUÙỦŨÚỤƯỪỬỮỨỰVXYỲỶỸÝỴ₫")


# --------------------------------------------------------------------------
# Measuring
# --------------------------------------------------------------------------

def _alone(g: G, draw) -> list:
    """The outline of what ``draw`` puts on an empty builder of the same style: one mark on its own."""
    s = G(g.p, g.name, g.case)
    s.recipes = g.recipes
    draw(s)
    return s.outlines()


def _moved(contours: list, d: complex) -> list:
    return [transform_contour(c, lambda q: q + d) for c in contours]


def _free(fixed: list, moving: list) -> bool:
    """The two shapes do not overlap."""
    return not any(abs(contour_area(c)) > 0.5 for c in intersection(fixed, moving))


def _clear(fixed: list, moving: list, d: complex, lo: float, hi: float, gap: float) -> float:
    """How far to move ``moving`` along ``d`` so that it keeps ``gap`` from ``fixed``: the least
    distance between ``lo`` and ``hi`` that does it (``hi`` must be far enough)."""
    grown = dilate(moving, gap)
    if _free(fixed, _moved(grown, d * lo)):
        return lo
    for _ in range(14):
        mid = (lo + hi) / 2
        if _free(fixed, _moved(grown, d * mid)):
            hi = mid
        else:
            lo = mid
    return hi


def _gap(g: G, upper: bool) -> float:
    """The white between two marks of one letter."""
    return (g.cap * 0.05 if upper else g.xh * 0.06) + g.hw * 0.12


# --------------------------------------------------------------------------
# Two marks above
# --------------------------------------------------------------------------

def _tone_half(g: G, tone: str, h: float, half: float, sc: float) -> float:
    """The half width for a tone mark ``h`` high. A short acute or grave leans over further, so it
    stays at least twice as long as it is thick: squeezed upright, it would turn into a lozenge
    that cannot be told from the other one. A heavy tilde gets wider, so its wave does not knot."""
    if tone == "tilde":
        return max(half, min(half * 1.5, g.sw * sc * 1.4))
    if tone not in ("acute", "grave"):
        return half
    length = g.sw * sc * 2.4
    lean = max(0.0, length * length - h * h) ** 0.5 / 1.2      # the acute runs 1.2 leans across
    return max(half, min(half * 1.7, lean / 0.62))


def _layout(g: G, first: str, tone: str, cx: float, upper: bool, size: float = 1.0, nest: bool = False):
    """Where the two marks of a stack go: [(kind, x, box), (kind, x, box)], and the top of the pair.

    ``size`` 1 is the full stack, 0 the smallest. From 1 down to 0.5 the circumflex or the breve
    gets flatter and the gaps smaller. Below 0.5 the tone mark gets smaller and lighter too. So a
    stack fits under the top of the line, and its tone mark stays big enough to read. ``nest`` lets a
    tone mark over a dieresis (Pinyin ǘ) come down between the dots, for a stack that does not fit
    otherwise.
    """
    y0, h, half, sc = _box(g, upper)
    ref = g.cap if upper else g.xh
    first_k = max(0.0, min(1.0, size * 2 - 1))
    tone_k = max(0.0, min(1.0, size * 2))
    first_size = lambda small, full: small + (full - small) * first_k
    tone_size = lambda small, full: small + (full - small) * tone_k
    # the hook has a bowl that must stay open, so it may get lighter than the others
    light = tone_size(0.50 if tone == "hookabove" else 0.66, 1.0)
    gap = _gap(g, upper) * first_size(0.62, 1.0)
    narrow = tone != "tilde"                       # these need more height than a tilde to be read
    # A breve must stay a cup, or it reads as a macron: it keeps most of its depth, and an acute, a
    # grave or a hook sits down in it. A tilde is too wide for that, so under a tilde the breve
    # gets flatter. A circumflex may get quite flat.
    flat = (0.58 if tone == "tilde" else 0.80) if first == "breve" else 0.30
    if upper:
        # capitals: flatter marks, a little closer to the letter, so that the line stays low
        h1, rest = h * first_size(flat, 0.74), first_size(0.40, 0.62)
        h_side = h * tone_size(0.64, 0.82)
        h_top = h * (tone_size(0.62, 0.80) if narrow else tone_size(0.48, 0.62))
    else:
        h1, rest = h * first_size(flat + 0.12, 0.90), first_size(0.70, 1.0)
        h_side = h * tone_size(0.70, 0.86)
        h_top = h * (tone_size(0.66, 0.84) if narrow else tone_size(0.54, 0.70))
    # The first mark rests where the same mark alone would (on â as on ấ), lower on a capital.
    alone = contour_bounds(_alone(g, lambda q: mark(q, first, cx, upper)))
    # nested, the dots of a dieresis also get smaller and come closer to the letter
    dots = 0.72 if nest else 1.0
    bottom = ref + (alone[1] - ref) * rest * (0.5 if nest else 1.0)
    one = _alone(g, lambda q: mark(q, first, cx, upper, (0.0, h1, half, sc * light * dots)))
    y1 = bottom - contour_bounds(one)[1]
    under = _moved(one, 1j * y1)
    parts = [(first, cx, (y1, h1, half, sc * light * dots))]
    if first == "circumflex" and tone != "tilde":
        # the acute, the grave or the hook above goes to the upper right of the circumflex
        apex = complex(cx, y1 + h1 * 0.92)
        arm = unit(complex(cx + half, y1) - apex)      # down the right arm of the circumflex
        away = arm * 1j                                # square to the arm, up and to the right
        box = (0.0, h_side, _tone_half(g, tone, h_side, half * 0.92, sc * light), sc * light)
        moving = _alone(g, lambda q: mark(q, tone, 0.0, upper, box))
        b = contour_bounds(moving)
        middle = complex((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        # the middle of the tone mark over the middle of the arm, then moved out until it is clear
        start = apex + arm * abs(complex(half, h1 * 0.92)) * 0.50 - middle
        t = _clear(under, _moved(moving, start), away, 0.0, h * 3 + g.sw * 2, gap)
        shift = start + away * t
        placed = contour_bounds(_moved(moving, shift))
        # the pair moves a little to the left, so that it does not hang off the right of the letter
        left = ((placed[2] + contour_bounds(under)[0]) / 2 - cx) * 0.35
        parts = [(first, cx - left, parts[0][2]), (tone, shift.real - left, (shift.imag, h_side, box[2], box[3]))]
        return parts, max(placed[3], contour_bounds(under)[3])
    # a tone mark on a breve, or a tilde on a circumflex: on top, and smaller than alone
    ub = contour_bounds(under)
    box = (0.0, h_top, _tone_half(g, tone, h_top, half * (0.86 if tone == "tilde" else 0.80), sc * light),
           sc * light)
    moving = _alone(g, lambda q: mark(q, tone, cx, upper, box))
    tb = contour_bounds(moving)
    # from down in the cup of the breve (an acute or a hook fits in it) up to clear of its top
    lo = ub[1] + (ub[3] - ub[1]) * 0.25 - tb[1]
    if first == "dieresis" and not nest:
        lo = ub[3] - tb[1]                         # Pinyin ǘ: the tone mark goes over the dots, not between them
    hi = ub[3] + g.sw - tb[1]
    dy = _clear(under, moving, 1j, lo, hi, gap)
    parts.append((tone, cx, (dy, h_top, box[2], box[3])))
    return parts, max(tb[3] + dy, ub[3])


def stack(g: G, kinds: list, cx: float, upper: bool):
    """The marks above a Vietnamese letter: one mark, or a circumflex or breve and a tone mark.

    A stack that would rise above the top of the line (the font's ascent, where programs clip) is
    drawn smaller: flatter, closer and lighter (see :func:`_layout`).
    """
    if len(kinds) == 1:
        mark(g, kinds[0], cx, upper)
        return
    first, tone = kinds
    room = g.p.line_top - g.p.upm * 0.004

    def fitted(nest: bool):
        parts, top = _layout(g, first, tone, cx, upper, nest=nest)
        if top > room:
            lo, hi = 0.0, 1.0
            parts, top = _layout(g, first, tone, cx, upper, lo, nest)
            if top <= room:
                for _ in range(5):
                    mid = (lo + hi) / 2
                    trial, t = _layout(g, first, tone, cx, upper, mid, nest)
                    if t <= room:
                        lo, parts, top = mid, trial, t
                    else:
                        hi = mid
        return parts, top

    parts, top = fitted(False)
    if top > room and first == "dieresis":
        parts, top = fitted(True)              # a heavy Ǘ: the tone mark comes down between the dots
    for kind, x, box in parts:
        mark(g, kind, x, upper, box)


# --------------------------------------------------------------------------
# The dot below and the horn
# --------------------------------------------------------------------------

def dot_below(g: G, cx: float, upper: bool):
    """The dot below. If the letter has a tail there (ỵ), the dot moves aside, the shorter way."""
    base = g.outlines()
    dot = _alone(g, lambda s: mark(s, "dotbelow", cx, upper))
    b = contour_bounds(base)
    span, gap = (b[2] - b[0]) + g.sw * 2, _gap(g, upper) * 0.75
    dx = _clear(base, dot, 1 + 0j, 0.0, span, gap)
    if dx > 0:
        dx = min(dx, -_clear(base, dot, -1 + 0j, 0.0, span, gap), key=abs)
    mark(g, "dotbelow", cx + dx, upper)
    width, left, right = g._frame if g._frame is not None else (None, "s", "s")
    d = contour_bounds(_moved(dot, dx))
    if width is not None and (d[0] < 0 or d[2] > width):
        # the dot is wider than the letter: the letter takes its width, so the dot keeps off its neighbors
        g._frame = (max(width, d[2]) - min(0.0, d[0]), left, right)
        if d[0] < 0:
            g.shift(-d[0])


def _edge(contours: list, y: float) -> float | None:
    """The right edge of the ink on the line at height ``y``."""
    b = contour_bounds(contours)
    part = contour_bounds(intersection(contours, [rect(b[0] - 10, y - 1, b[2] + 10, y + 1)]))
    return part[2] if part else None


def horn(g: G, x: float, y: float, upper: bool, w: float = 0.86):
    """The horn: it leaves the letter at (x, y), a point on its right edge, and turns up.

    The stroke starts inside the letter, so the join is buried, and it ends in a flat top above the
    x-height (or the cap height), well to the right of any mark above.
    """
    size = g.cap if upper else g.xh
    x0, y0 = x - g.sw * 0.45, y - g.hw * 0.15
    x1 = x + size * (0.15 if upper else 0.17)
    y1 = size * (1.08 if upper else 1.13)
    (g.path(x0, y0, w=w)
     .curve((x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.06), (x1, y0 + (y1 - y0) * 0.42), x1, y1, w=w * 0.94,
            fl=0.5)
     .done(end=H, tag="horn"))


def add_horn(g: G, base: str, upper: bool):
    """Put the horn on a drawn o or u (or a redrawn one), and widen the letter to hold it."""
    contours = g.outlines()
    b = contour_bounds(contours)
    ref = g.cap if upper else g.xh
    if base in "oO":
        y = ref * 0.78
    elif g.serifed and upper:
        y = ref - g.serif_t * 0.5            # out of the end of the slab on top of the U
    else:
        y = ref * 0.86
    x = _edge(contours, y)
    horn(g, b[2] if x is None else x, y, upper)
    # In a monospaced cell the thin tip of the horn may come closer to the edge than a letter does, so
    # the letter is drawn only a little narrower than o or u (at the usual share its marks get cramped).
    # The rest of the white is kept for an effect that spreads the ink.
    g.cell_share = 0.94
    width, left, _ = g._frame if g._frame is not None else (None, "s", "s")
    if width is not None:
        right = contour_bounds(g.outlines())[2]
        g._frame = (max(width, right), left, 0.4)


# --------------------------------------------------------------------------
# The letters
# --------------------------------------------------------------------------

#: The marks of a letter, in the order of its name: horn first, then the marks above, then below.
ORDER = ("horn", "circumflex", "breve", "grave", "acute", "hookabove", "tilde", "dotbelow")


def _letter(char: str):
    base, *combining = unicodedata.normalize("NFD", char)
    kinds = sorted((MARKS[c] for c in combining), key=ORDER.index)
    above = [k for k in kinds if k not in ("horn", "dotbelow")]
    name = base + "".join(kinds)
    upper = base.isupper()
    source = UPPER if upper else LOWER
    # ỉ: a mark above an i takes the place of its dot. ị keeps the dot.
    base_name = "dotlessi" if base == "i" and above else base
    fn = source[base_name].fn

    def recipe(g: G):
        g.base(base_name, fn)(g)          # the project's own letter, if it redrew it
        cx = _center(g)                   # before the horn: the marks center on the letter, not on the horn
        if "horn" in kinds:
            add_horn(g, base, upper)
            # a combining mark goes over the letter, not over the middle of the letter and its horn
            g.anchors["top"] = complex(cx, g.cap if upper else g.xh)
        if above:
            stack(g, above, cx, upper)
        if "dotbelow" in kinds:
            dot_below(g, cx, upper)

    VIETNAMESE[name] = type(source[base])(name, recipe, ord(char), "upper" if upper else "lower")


for _ch in LETTERS:
    _letter(_ch)


# --------------------------------------------------------------------------
# Combining marks, and the dong sign
# --------------------------------------------------------------------------

def _combining(kind: str):
    def recipe(g: G):
        mark(g, kind, 0.0, False)
        g.frame(0, 0, 0)          # no advance, and no shift: x = 0 is the attachment point
    return recipe


def _horncomb(g: G):
    """The horn as a mark: x = 0 is the point on the right edge of the letter where it grows out."""
    horn(g, 0.0, g.xh * 0.80, False)
    g.frame(0, 0, 0)


_Rec = type(LOWER["n"])
for _uni, (_name, _kind) in {0x0309: ("hookabovecomb", "hookabove"), 0x0323: ("dotbelowcomb", "dotbelow"),
                             0x0340: ("gravetonecomb", "grave"), 0x0341: ("acutetonecomb", "acute")}.items():
    VIETNAMESE[_name] = _Rec(_name, _combining(_kind), _uni, "lower")
VIETNAMESE["horncomb"] = _Rec("horncomb", _horncomb, 0x031B, "lower")


@VIETNAMESE.add("dong", 0x20AB, case="figure")
def dong(g: G):
    """₫: a small đ standing on a bar, as wide as a figure."""
    from .figures import fig_advance
    s0, h0 = len(g.strokes), len(g.shapes)
    g.base("dcroat", EXTENDED["dcroat"].fn)(g)
    g._frame = None
    k = 0.80
    b = contour_bounds(g.outlines())
    bar = g.hw * 0.9
    lift = bar + g.cap * 0.08 + g.o * k
    g.transform((k, 0.0, 0.0, k, -b[0] * k, lift), s0, h0)
    for s in g.strokes[s0:]:
        s.scale *= 0.92
    b = contour_bounds(g.outlines())
    g.bar(b[0], b[2], bar / 2, w=0.9, tag="bar")
    g.fixed_advance(fig_advance(g))
