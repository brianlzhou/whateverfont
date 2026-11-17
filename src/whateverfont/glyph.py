"""The glyph builder: the vocabulary recipes use to draw letters.

A recipe is a function that receives a :class:`G` and draws on it::

    @recipe("l")
    def l(g):
        g.stem(g.L, 0, g.asc)
        g.frame(g.sw, "s", "s")

``G`` knows the design parameters, so it can answer questions such as "how
thick is a stem" (``g.sw``) or "where does the centerline of a round stroke sit
so that its outside touches the x-height" (``g.top``). It collects skeleton
strokes and filled shapes, and :meth:`G.finish` turns them into outlines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from .geom import (
    apply_affine,
    contour_bounds,
    cross,
    flip_x_about,
    flip_y_about,
    line_hit,
    rotate_about,
    shear_x,
    transform_contour,
    translate,
    unit,
)
from .outline import union
from .params import Params
from .stroke import Cap, Node, Pen, Stroke, clean, expand, fillet

H = 1 + 0j   # a horizontal cut
V = 1j       # a vertical cut


@dataclass
class Glyph:
    """A finished glyph: outlines plus metrics."""
    name: str
    advance: float
    contours: list            # final outlines (overlaps removed unless raw)
    unicode: int | None = None
    #: Named points for accents and components, in glyph space.
    anchors: dict = field(default_factory=dict)
    #: Color layers: list of (palette key, contours). Empty for plain glyphs.
    layers: list = field(default_factory=list)
    #: The skeleton, kept for proofs.
    strokes: list = field(default_factory=list)
    #: The glyph was cut or redrawn after its strokes were expanded (a stencil, an effect),
    #: so it cannot be a master of a variable font.
    static_only: bool = False

    def bounds(self):
        return contour_bounds(self.contours)


class PathBuilder:
    """Builds one stroke, node by node."""

    def __init__(self, g: "G", x: float, y: float, w: float = 1.0, taper=None, fl: float = 0.0):
        self.g = g
        self.nodes: list[Node] = []
        self.handles: list = []
        self._add(x, y, w, taper, fl, None, None)

    # -- internals ---------------------------------------------------------
    def _add(self, x, y, w, taper, fl, corner, apex, turn=0.0):
        wl = wr = None
        self._last = (fl, w)
        if fl:
            w, taper, wl, wr = self._flared(w, taper, fl, turn)
        self.nodes.append(Node(complex(x, y), w, taper, corner, apex, wl, wr))

    def _flared(self, w, taper, fl, turn):
        """Widths for a terminal. ``turn`` is the way the curve bends (0 = straight)."""
        p = self.g.p
        amount = p.eff_flare * fl
        if not turn:
            return w * (1 + amount), (p.flare_taper if taper is None else taper), None, None
        # On a curve the flare goes to the outer side; a flare on the inner
        # side would grow a barb.
        outer, inner = w * (1 + amount * 0.95), w * (1 + amount * 0.10)
        wl, wr = (inner, outer) if turn > 0 else (outer, inner)
        return (wl + wr) / 2, (min(p.flare_taper, 1.3) if taper is None else taper), wl, wr

    def _curve_starts(self, turn):
        """Called before a curve is added: a flared start node becomes a curve terminal."""
        if len(self.nodes) == 1 and self._last[0]:
            fl, w0 = self._last
            n = self.nodes[0]
            n.w, n.taper, n.wl, n.wr = self._flared(w0, None, fl, turn)

    @staticmethod
    def _turn(a, h1, h2, b) -> float:
        t = cross(h1 - a, b - h2)
        if abs(t) < 1e-6:
            t = cross(h1 - a, b - a)
        return 1.0 if t > 0 else -1.0

    @property
    def here(self) -> complex:
        return self.nodes[-1].p

    # -- segments ----------------------------------------------------------
    def to(self, x, y, w=1.0, taper=None, fl=0.0, corner=None, apex=None):
        """A straight line to (x, y)."""
        self.handles.append(None)
        self._add(x, y, w, taper, fl, corner, apex)
        return self

    def _zone(self, a: complex, b: complex) -> float:
        return min(self.g.p.flare_len * self.g.k, abs(b - a) * 0.48)

    def flared_to(self, x, y, fl=1.0, w=1.0):
        """A straight line that ends in a terminal.

        The widening is kept inside the last ``flare_len`` units, so long stems
        stay parallel for most of their length. The extra node is always
        added, so the structure does not depend on the amount of flare.
        """
        a = self.here
        b = complex(x, y)
        m = b - unit(b - a) * self._zone(a, b)
        if self.nodes[-1].taper is None:
            self.nodes[-1].taper = 0.0
        self.to(m.real, m.imag, w, taper=0.0)
        self.to(x, y, w, fl=fl)
        return self

    def flared_from(self, x, y, w=1.0, taper=None, corner=None, apex=None):
        """A straight line that leaves a terminal (the start node) toward (x, y)."""
        a = self.here
        b = complex(x, y)
        m = a + unit(b - a) * self._zone(a, b)
        self.to(m.real, m.imag, w, taper=0.0)
        self.to(x, y, w, taper=0.0 if taper is None else taper, corner=corner, apex=apex)
        return self

    def ellipse(self, cx, cy, rx, ry, a0, a1, w=1.0, fl=0.0, taper=None, w_side=None, w_top=1.0,
                boost=None, boost_all=False):
        """Follow an ellipse from angle ``a0`` to ``a1`` (degrees, 0 = east, 90 = north).

        The current point must be the ellipse point at ``a0``. Nodes are placed
        at the extremes (multiples of 90 degrees) on the way.
        """
        g = self.g
        ws = g.p.round_weight if w_side is None else w_side
        step = 1 if a1 > a0 else -1
        stops = [a0]
        q = math.floor(a0 / 90 + 1e-9) + 1 if step > 0 else math.ceil(a0 / 90 - 1e-9) - 1
        while (q * 90 < a1 - 1e-6) if step > 0 else (q * 90 > a1 + 1e-6):
            stops.append(q * 90.0)
            q += step
        stops.append(a1)
        # Avoid slivers next to the ends.
        if len(stops) > 2 and abs(stops[1] - stops[0]) < 18:
            stops.pop(1)
        if len(stops) > 2 and abs(stops[-1] - stops[-2]) < 18:
            stops.pop(-2)
        boost = g.p.superk / 0.5523 if boost is None else boost
        turn = 1.0 if a1 > a0 else -1.0
        self._curve_starts(turn)

        def pt(a):
            t = math.radians(a)
            return complex(cx + rx * math.cos(t), cy + ry * math.sin(t))

        def dv(a):
            t = math.radians(a)
            return complex(-rx * math.sin(t), ry * math.cos(t))

        for i in range(1, len(stops)):
            s0, s1 = stops[i - 1], stops[i]
            d = math.radians(s1 - s0)
            h = (4.0 / 3.0) * math.tan(d / 4)
            if boost_all or abs(abs(s1 - s0) - 90) < 1e-6:
                h *= boost
            b = pt(s1)
            self.handles.append((pt(s0) + dv(s0) * h, b - dv(s1) * h))
            last = i == len(stops) - 1
            if last:
                self._add(b.real, b.imag, w, taper, fl, None, None, turn)
            else:
                on_side = abs((s1 / 90) % 2) < 1e-6
                self._add(b.real, b.imag, ws if on_side else w_top, None, 0.0, None, None)
        return self

    def arc(self, x, y, via="h", w=1.0, taper=None, fl=0.0, k=None, k0=None, k1=None,
            corner=None, apex=None):
        """A quarter round to (x, y).

        ``via="h"`` leaves the current point horizontally and arrives
        vertically; ``via="v"`` does the opposite. ``via`` may also be a point
        ``(cx, cy)``: the place where the two end tangents meet.
        ``k`` is the handle length as a fraction of the way to that point.
        """
        a = self.here
        b = complex(x, y)
        if via == "h":
            c = complex(b.real, a.imag)
        elif via == "v":
            c = complex(a.real, b.imag)
        else:
            c = complex(*via)
        kk = self.g.p.superk if k is None else k
        ka = kk if k0 is None else k0
        kb = kk if k1 is None else k1
        h1, h2 = a + (c - a) * ka, b + (c - b) * kb
        turn = self._turn(a, h1, h2, b)
        self._curve_starts(turn)
        self.handles.append((h1, h2))
        self._add(x, y, w, taper, fl, corner, apex, turn)
        return self

    def curve(self, h1, h2, x, y, w=1.0, taper=None, fl=0.0, corner=None, apex=None):
        """A cubic with explicit handles (absolute points)."""
        h1, h2 = complex(*h1), complex(*h2)
        turn = self._turn(self.here, h1, h2, complex(x, y))
        self._curve_starts(turn)
        self.handles.append((h1, h2))
        self._add(x, y, w, taper, fl, corner, apex, turn)
        return self

    def smooth(self, x, y, out_len, in_dir, in_len, w=1.0, taper=None, fl=0.0, corner=None, apex=None):
        """A cubic that continues the current direction.

        Leaves along the incoming tangent for ``out_len`` and arrives at
        (x, y) traveling along ``in_dir`` (a direction vector) with a handle
        of ``in_len``.
        """
        a = self.here
        if self.handles and self.handles[-1] is not None:
            d = unit(a - self.handles[-1][1])
        elif len(self.nodes) > 1:
            d = unit(a - self.nodes[-2].p)
        else:
            d = unit(complex(x, y) - a)
        b = complex(x, y)
        ind = in_dir if isinstance(in_dir, complex) else complex(*in_dir)
        h1, h2 = a + d * out_len, b - unit(ind) * in_len
        turn = self._turn(a, h1, h2, b)
        self._curve_starts(turn)
        self.handles.append((h1, h2))
        self._add(x, y, w, taper, fl, corner, apex, turn)
        return self

    # -- finishing -----------------------------------------------------------
    def done(self, start=None, end=None, round_start=None, round_end=None, scale=1.0,
             fixed=None, round_joins=True, miter=2.5, tag="") -> Stroke:
        """End the stroke. ``start``/``end`` are cut directions (``H``, ``V``, a vector, or None)."""
        s = Stroke(self.nodes, self.handles, False,
                   Cap(start, round_start), Cap(end, round_end),
                   scale * self.g.k, fixed, round_joins, miter, tag)
        self.g.strokes.append(s)
        return s

    def close(self, scale=1.0, fixed=None, tag="") -> Stroke:
        """Close the stroke into a ring. The last segment must return to the start."""
        if abs(self.nodes[-1].p - self.nodes[0].p) < 1e-6:
            last = self.nodes.pop()
            self.nodes[0].w = self.nodes[0].w if self.nodes[0].w != 1.0 else last.w
        s = Stroke(self.nodes, self.handles, True, Cap(), Cap(), scale * self.g.k, fixed, True, 2.5, tag)
        self.g.strokes.append(s)
        return s


class G:
    """A glyph under construction."""

    def __init__(self, p: Params, name: str = "", case: str = "lower"):
        self.p = p
        self.name = name
        self.case = case
        #: Stroke scale for this glyph (capitals and figures are a little heavier).
        self.k = {"upper": p.cap_weight, "figure": (1 + p.cap_weight) / 2}.get(case, 1.0)
        self.pen = Pen.for_stems(p.weight, p.eff_contrast, p.stress)
        self.strokes: list[Stroke] = []
        self.shapes: list[list] = []      # filled contours
        self.cutouts: list[list] = []     # contours removed from the result
        self.layers: list = []
        self.anchors: dict = {}
        self._frame = None
        self._advance = None
        self.components: list = []        # (glyph name, dx, dy)
        #: The recipe set this glyph belongs to, so a recipe can draw another letter of the set.
        self.recipes: "Recipes | None" = None
        #: In a monospaced font: the drawing fills the whole cell, so that a row of them joins up (the underscore).
        self.full_cell = False
        #: In a monospaced font: the share of the cell the drawing may fill. None is the usual share
        #: (:meth:`cell_room`). The horn of ơ takes a little more, so that its bowl stays nearly as wide as o.
        self.cell_share = None
        #: Set by an effect that changes the outline after the strokes are expanded.
        self.static_only = False
        #: Set by a color effect whose upper layers lie over the letter (snow): the key of the letter's
        #: layer. ``whateverfont retrace`` then gives a dot that they would cover its own color back.
        self.letter_layer: "str | None" = None
        #: How far slabs reach past the declared frame (left, right), kept when an effect redraws
        #: the glyph and its strokes are gone. None: measure it from the strokes.
        self.slab_reach = None

    def base(self, name: str, default=None):
        """The recipe function of another glyph in this set, or ``default`` if the set has none.

        An accented letter draws its base this way, so a project that redraws
        ``e`` gets its own ``e`` under every accent.
        """
        rec = self.recipes.get(name) if self.recipes is not None else None
        if rec is not None:
            return rec.plain or rec.fn
        if default is None:
            raise KeyError(f"no recipe named {name!r}")
        return default

    # -- thickness -------------------------------------------------------------
    def thick(self, direction: complex = 1j, w: float = 1.0) -> float:
        """Stroke thickness when the pen travels along ``direction``."""
        return 2 * self.pen.half(unit(direction)) * self.k * w

    @property
    def sw(self) -> float:
        """Vertical stem thickness."""
        return self.thick(1j)

    @property
    def hw(self) -> float:
        """Horizontal stroke thickness."""
        return self.thick(1 + 0j)

    @property
    def rw(self) -> float:
        """Thickness of a round stroke at its side."""
        return self.sw * self.p.round_weight

    # -- shortcuts into the parameters -----------------------------------------
    @property
    def xh(self):
        return self.p.xh

    @property
    def cap(self):
        return self.p.cap

    @property
    def asc(self):
        return self.p.asc

    @property
    def desc(self):
        return self.p.desc

    @property
    def o(self):
        return self.p.overshoot

    @property
    def fl(self):
        """Width multiplier at a flared terminal."""
        return 1 + self.p.eff_flare

    @property
    def L(self):
        """x of a stem centerline whose left edge sits at 0."""
        return self.sw / 2

    @property
    def cw(self):
        """Counter of the n for this case."""
        c = self.p.n_counter
        return c * (1.22 * self.p.cap_width if self.case == "upper" else 1.0)

    def top(self, h: float) -> float:
        """Centerline y for a round stroke whose outside overshoots height ``h``."""
        return h + self.o - self.hw / 2

    @property
    def bot(self) -> float:
        """Centerline y for a round stroke whose outside overshoots the baseline."""
        return -self.o + self.hw / 2

    @property
    def dbot(self) -> float:
        """Centerline y for a round stroke whose outside touches the descender line."""
        return self.desc + self.hw / 2

    def flat_top(self, h: float) -> float:
        """Centerline y for a horizontal bar whose top sits exactly at ``h``."""
        return h - self.hw / 2

    def capw(self, modern: float, classical: float) -> float:
        """Blend a width between even and Roman capital proportions."""
        c = self.p.classical
        return (modern + (classical - modern) * c) * self.cw

    def curved_cut(self, default=None):
        """The cut direction for the terminal of a curved stroke."""
        return {"horizontal": H, "vertical": V, "flat": H}.get(self.p.cut, default)

    @property
    def flat(self) -> bool:
        """``cut="flat"``: every curved stroke ends on a level or an upright line, whichever crosses it."""
        return self.p.cut == "flat"

    def hook_cut(self, default=None):
        """The cut for the end of an arm or a hook (r, f, t, j). A flat hook ends level, so its cut is upright:
        a level cut would run along the stroke and leave a sharp wedge."""
        return V if self.flat else self.curved_cut(default)

    def tail_cut(self, default=None):
        """The cut for the end of a long tail (g, J, 3, 5, 6, 9). A flat family cuts it square to the stroke: the
        tail ends on a slope, where a level cut would leave a wedge."""
        return None if self.flat else self.curved_cut(default)

    def hook_reach(self, share: float) -> float:
        """How far the hook of f, t or j reaches sideways from its stem's centerline. A flat hook is a short
        arc, so it also gets a share of the stem: in a heavy or a narrow face it must still clear the stem."""
        return (self.cw * share + (self.sw * 0.25 if self.flat else 0.0)) * self.p.arm

    def hook_end(self, closed: float, opened: float) -> float:
        """How far a hook turns past the stem's direction, in degrees. A flat hook stops soon after it is level."""
        return 14.0 if self.flat else closed + (opened - closed) * self.p.aperture

    # -- drawing ---------------------------------------------------------------
    def path(self, x, y, w=1.0, taper=None, fl=0.0) -> PathBuilder:
        return PathBuilder(self, x, y, w, taper, fl)

    def stem(self, x, y0, y1, b=1.0, t=1.0, x1=None, w=1.0, scale=1.0, cut0=H, cut1=H,
             apex0=None, apex1=None, tag="stem", round0=None, round1=None, serif0=None,
             serif1=None) -> Stroke:
        """A straight stem from (x, y0) to (x1 or x, y1).

        ``b`` and ``t`` are the flare amounts at the start and the end
        (1 = the family's flare, 0 = none, for ends buried in other strokes).
        Ends are cut horizontally unless ``cut0``/``cut1`` say otherwise.

        In a family with slab serifs (``serif`` > 0), a free end of a vertical
        stem gets a slab: a foot on both sides at the baseline or the
        descender, and a head at the x-height, the ascender or the cap height
        (on the left only for a lowercase letter). ``serif0``/``serif1`` say
        otherwise for the start or the end: ``(left, right)`` slab lengths as
        shares of ``serif``, or ``False`` for none.
        """
        p = self.p
        if p.serif > 0 and tag == "stem" and (x1 is None or abs(x1 - x) < 1e-6) and abs(y1 - y0) > 1e-6:
            half = self.sw * scale * w / 2
            for y, amount, which in ((y0, b, serif0), (y1, t, serif1)):
                sides = self._auto_slab(y, amount, which)
                if sides:
                    top = y > (y0 + y1) / 2
                    self.slab(x, y, sides[0], sides[1], top=top, half=half * (1 + p.eff_flare * amount))
                    if top:
                        round1 = 0.0 if round1 is None else round1      # the slab hides the end
                    else:
                        round0 = 0.0 if round0 is None else round0
        a = complex(x, y0)
        c = complex(x if x1 is None else x1, y1)
        length = abs(c - a)
        zone = min(p.flare_len * self.k, length * 0.48)
        d = unit(c - a)
        fb = p.eff_flare * b
        ft = p.eff_flare * t
        nodes = [Node(a, w * (1 + fb), p.flare_taper)]
        handles = []
        m0 = a + d * zone
        m1 = c - d * zone
        nodes.append(Node(m0, w, 0.0))
        handles.append(None)
        nodes.append(Node(m1, w, 0.0))
        handles.append(None)
        nodes.append(Node(c, w * (1 + ft), p.flare_taper))
        handles.append(None)
        s = Stroke(nodes, handles, False, Cap(cut0, round0), Cap(cut1, round1), scale * self.k,
                   None, True, 2.5, tag)
        self.strokes.append(s)
        return s

    # -- slab serifs ---------------------------------------------------------------
    @property
    def serifed(self) -> bool:
        """The family has slab serifs."""
        return self.p.serif > 0

    @property
    def serif_t(self) -> float:
        """Thickness of a slab serif."""
        return self.hw * self.p.serif_weight

    def _auto_slab(self, y: float, amount: float, which):
        """The slab a free stem end at height ``y`` gets: (left, right) lengths, or None."""
        if which is not None:
            return tuple(which) if which else None
        if amount <= 0:
            return None                                  # a buried end
        near = lambda h: abs(y - h) < 1.0
        if near(0.0) or near(self.desc):
            return (1.0, 1.0)
        if near(self.xh) or near(self.asc) or near(self.cap):
            return (1.0, 0.0) if self.case == "lower" else (1.0, 1.0)
        return None

    def slab(self, x: float, y: float, left: float = 1.0, right: float = 1.0, top: bool = False,
             half: float | None = None, length: float | None = None):
        """A slab serif across the end of a stroke. Nothing in a family without serifs.

        ``(x, y)`` is the middle of the end: ``y`` is the baseline for a foot, or the top for a
        head (``top=True``; the slab hangs below it). ``half`` is half the width of the stroke
        there (default: half a stem; for a diagonal, ``g.dx(direction)``). ``left`` and
        ``right`` are the lengths past the stroke on each side, as shares of the family's
        ``serif`` (or of ``length``). A side with 0 gets no slab.
        """
        p = self.p
        if p.serif <= 0:
            return
        t = self.serif_t
        half = self.sw / 2 if half is None else half
        reach = p.serif if length is None else length
        yc = y - t / 2 if top else y + t / 2
        for side, share in ((-1.0, left), (1.0, right)):
            if not share:
                continue
            edge = x + side * half
            s = (self.path(x, yc, w=p.serif_weight)
                 .to(edge + side * reach * share, yc, w=p.serif_weight)
                 .done(start=V, end=V, round_start=0.0, tag="serif"))
            s.anchor = complex(edge, yc)

    def beak(self, x: float, y: float, side: float = 1.0, down: bool = True, length: float = 1.0,
             arm: float | None = None):
        """A short vertical serif at the end of a horizontal arm (E, F, L, T, Z).

        ``x`` is the end of the arm and ``y`` its centerline. ``side`` is 1 for an arm that points
        right (the beak lies left of ``x``), -1 for one that points left. ``down`` hangs the beak
        below the arm; ``length`` is its reach past the arm, as a share of ``serif``. ``arm`` is
        the thickness of the arm (default: a horizontal stroke).
        """
        p = self.p
        if p.serif <= 0:
            return
        t = self.serif_t
        arm = self.hw if arm is None else arm
        xc = x - side * t / 2
        s = -1.0 if down else 1.0
        (self.path(xc, y, w=t / self.sw)
         .to(xc, y + s * (arm / 2 + p.serif * length * 0.95), w=t / self.sw)
         .done(start=H, end=H, round_start=0.0, tag="beak"))

    def _settled(self, strokes: list) -> list:
        """Slab serifs that face each other across a narrow counter, shortened so they do not touch.

        The white between the two ends is kept at about two thirds of a stem, or a third of the
        counter if that is more. A slab never shrinks past the edge of its stem, so the
        structure stays the same.
        """
        slabs = []
        for i, s in enumerate(strokes):
            if s.anchor is None or len(s.nodes) != 2:
                continue
            a, b = s.nodes[0].p, s.nodes[1].p
            if abs(b.imag - a.imag) > 1e-6 or abs(b.real - a.real) < 1e-9:
                continue
            t = 2 * self.pen.half(1 + 0j) * s.scale * s.nodes[0].w
            slabs.append((i, 1.0 if b.real > a.real else -1.0, a.imag, t, s.anchor.real, b.real))
        if len(slabs) < 2:
            return strokes
        ends = {i: e for i, _, _, _, _, e in slabs}
        rights = sorted((sl for sl in slabs if sl[1] > 0), key=lambda sl: sl[4])
        lefts = [sl for sl in slabs if sl[1] < 0]
        least = self.sw * 0.66
        for i, _, y, t, anchor, _ in rights:
            facing = [sl for sl in lefts if sl[4] > anchor - 1e-6 and abs(sl[2] - y) < (sl[3] + t) / 2]
            if not facing:
                continue
            j, _, _, _, anchor_j, _ = min(facing, key=lambda sl: sl[4])
            room = anchor_j - anchor
            want = max(least, room * 0.34)
            gap = ends[j] - ends[i]
            if gap >= want:
                continue
            short = want - gap
            give_i, give_j = ends[i] - anchor, anchor_j - ends[j]       # how far each may shrink
            take_i = min(give_i, max(short / 2, short - give_j))
            take_j = min(give_j, short - take_i)
            ends[i] -= take_i
            ends[j] += take_j
        out = list(strokes)
        for i, e in ends.items():
            s = strokes[i]
            if abs(e - s.nodes[1].p.real) < 1e-9:
                continue
            last = replace(s.nodes[1], p=complex(e, s.nodes[1].p.imag))
            out[i] = replace(s, nodes=[s.nodes[0], last])
        return out

    def bar(self, x0, x1, y, l=0.0, r=0.0, w=1.0, scale=1.0, cut0=V, cut1=V, tag="bar",
            round0=None, round1=None) -> Stroke:
        """A horizontal bar. ``l``/``r`` are flare amounts at the left and right end."""
        return self.stem(x0, y, y, b=l, t=r, x1=x1, w=w, scale=scale, cut0=cut0, cut1=cut1,
                         tag=tag, round0=round0, round1=round1)

    def line(self, x0, y0, x1, y1, b=0.0, t=0.0, w=1.0, scale=1.0, cut0=None, cut1=None,
             tag="line", round0=None, round1=None) -> Stroke:
        """A straight stroke at any angle."""
        s = self.stem(x0, y0, y1, b=b, t=t, x1=x1, w=w, scale=scale, cut0=cut0, cut1=cut1, tag=tag,
                      round0=round0, round1=round1)
        return s

    def ring(self, x0, y0, x1, y1, w_side=None, w_top=1.0, k=None, scale=1.0, tag="ring") -> Stroke:
        """A closed round (the o) whose *centerline* fills the box x0..x1, y0..y1."""
        ws = self.p.round_weight if w_side is None else w_side
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        pb = (self.path(x1, ym, ws)
              .arc(xm, y1, "v", w=w_top, k=k)
              .arc(x0, ym, "h", w=ws, k=k)
              .arc(xm, y0, "v", w=w_top, k=k)
              .arc(x1, ym, "h", w=ws, k=k))
        return pb.close(scale=scale, tag=tag)

    def dot(self, cx, cy, d=None, shape=None):
        """A filled dot (i, j, period...) of diameter ``d``."""
        p = self.p
        d = self.sw * 1.16 if d is None else d
        shape = p.dot if shape is None else shape
        if shape == "auto":
            shape = "round" if p.roundness > 0.55 else ("diamond" if p.flare > 0.22 and p.roundness < 0.2 else "square")
        r = d / 2
        if shape == "diamond":
            r *= 1.22
            pts = [complex(cx, cy + r), complex(cx + r, cy), complex(cx, cy - r), complex(cx - r, cy)]
            rad = r * 0.9 * p.roundness
        else:
            pts = [complex(cx - r, cy + r), complex(cx + r, cy + r), complex(cx + r, cy - r), complex(cx - r, cy - r)]
            rad = r * (1.0 if shape == "round" else p.roundness)
            if shape == "round":
                # a round dot looks smaller than a square one of the same size
                pts = [complex(cx + (q.real - cx) * 1.08, cy + (q.imag - cy) * 1.08) for q in pts]
                rad *= 1.08
        contour = [(pts[i], pts[(i + 1) % 4]) for i in range(4)]
        self.shapes.append(("dot", contour, [rad] * 4))

    def shape(self, contour, radii=None):
        """Add a filled contour (list of segments), drawn clockwise."""
        self.shapes.append(("shape", contour, radii))

    def polygon(self, pts, radius=0.0):
        pts = [complex(*q) if not isinstance(q, complex) else q for q in pts]
        n = len(pts)
        self.shapes.append(("shape", [(pts[i], pts[(i + 1) % n]) for i in range(n)],
                            [radius] * n if radius else None))

    # -- transforms --------------------------------------------------------------
    def transform(self, matrix, start: int = 0, shape_start: int = 0):
        """Transform every stroke and shape added since the given indexes."""
        fn = lambda q: apply_affine(matrix, q)
        flipped = matrix[0] * matrix[3] - matrix[1] * matrix[2] < 0
        for i in range(shape_start, len(self.shapes)):
            kind, contour, radii = self.shapes[i]
            contour = transform_contour(contour, fn)
            if flipped:
                contour = [tuple(reversed(seg)) for seg in reversed(contour)]
                if radii is not None:
                    radii = [radii[0]] + list(reversed(radii[1:]))
            self.shapes[i] = (kind, contour, radii)
        yfn = (lambda y: apply_affine(matrix, complex(0, y)).imag)
        for i in range(start, len(self.strokes)):
            s = self.strokes[i]
            t = s.transformed(fn, yfn, flipped)
            # cut directions follow the linear part of the transform
            lin = (matrix[0], matrix[1], matrix[2], matrix[3], 0.0, 0.0)
            for cap_old, cap_new in ((s.start, "start"), (s.end, "end")):
                if cap_old.cut is not None:
                    setattr(t, cap_new, Cap(apply_affine(lin, cap_old.cut), cap_old.round))
            self.strokes[i] = t

    def mirror_x(self, cx: float, start: int = 0):
        self.transform(flip_x_about(cx), start)

    def mirror_y(self, cy: float, start: int = 0):
        self.transform(flip_y_about(cy), start)

    def rotate(self, deg: float, cx: float, cy: float, start: int = 0):
        self.transform(rotate_about(deg, cx, cy), start)

    def shift(self, dx: float, dy: float = 0.0, start: int = 0):
        self.transform(translate(dx, dy), start)

    # -- diagonals -------------------------------------------------------------
    def dx(self, direction: complex, w: float = 1.0) -> float:
        """Half the width of a stroke along ``direction`` when it is cut horizontally."""
        u = unit(direction)
        return self.pen.half(u) * self.k * w / max(abs(u.imag), 0.05)

    def diagonal(self, xa, ya, xb, yb, a="c", b="c", w=1.0):
        """Centerline end points for a diagonal whose *edges* are given.

        ``a``/``b`` say which part of the horizontally cut end sits at the given
        x: ``"l"`` its left corner, ``"r"`` its right corner, ``"c"`` its center.
        """
        pa, pb = complex(xa, ya), complex(xb, yb)
        off = {"l": 1.0, "r": -1.0, "c": 0.0}
        for _ in range(4):
            d = self.dx(pb - pa, w)
            pa = complex(xa + off[a] * d, ya)
            pb = complex(xb + off[b] * d, yb)
        return pa, pb

    @staticmethod
    def epoint(cx, cy, rx, ry, angle) -> complex:
        t = math.radians(angle)
        return complex(cx + rx * math.cos(t), cy + ry * math.sin(t))

    # -- apex helper -----------------------------------------------------------
    def apex_y(self, x: float, far_a: complex, far_b: complex, y_cut: float, flat: float | None = None,
               w: float = 1.0) -> float:
        """Where to put the corner node of a V shape.

        Two strokes run from ``far_a`` to the corner at ``x`` and on to
        ``far_b``. The result is the node's y such that, once the outside
        point is cut off along ``y_cut``, the flat is ``flat`` units wide
        (default: the family's ``apex`` setting).
        """
        flat = self.p.apex * self.sw if flat is None else flat
        s = 1.0 if far_a.imag > y_cut else -1.0   # +1: the strokes come from above
        order = 1.0 if far_b.real > far_a.real else -1.0
        y = y_cut + s * self.sw
        cut = complex(0, y_cut)
        for _ in range(8):
            node = complex(x, y)
            ua, ub = unit(node - far_a), unit(far_b - node)
            na, nb = 1j * ua, 1j * ub
            if (na.real * (far_b - node).real + na.imag * (far_b - node).imag) > 0:
                na = -na
            if (nb.real * (far_a - node).real + nb.imag * (far_a - node).imag) > 0:
                nb = -nb
            pa = node + na * self.pen.half(ua) * self.k * w
            pb = node + nb * self.pen.half(ub) * self.k * w
            ca, cb = line_hit(pa, ua, cut, 1 + 0j), line_hit(pb, ub, cut, 1 + 0j)
            if ca is None or cb is None or abs(ua.imag) < 1e-6 or abs(ub.imag) < 1e-6:
                break
            got = (cb.real - ca.real) * order
            slope = abs(ua.real / ua.imag) + abs(ub.real / ub.imag)
            if slope < 1e-6:
                break
            y -= s * (flat - got) / slope
            # the node must stay inside the cut line, or there is nothing to cut
            y = max(y, y_cut + 0.2 * self.sw) if s > 0 else min(y, y_cut - 0.2 * self.sw)
        return y

    # -- metrics ---------------------------------------------------------------
    def frame(self, width: float | None, l="s", r="s"):
        """Declare the drawn width and the kind of each side.

        The drawing must sit between x = 0 and x = ``width``; pass None to
        measure the drawing instead. ``l`` and ``r``
        say what the side looks like, which sets the sidebearing:
        ``"s"`` straight stem, ``"r"`` round, ``"d"`` diagonal, ``"o"`` open,
        ``"t"`` a thin tip, or a number (a multiple of the stem sidebearing).

        It replaces an earlier ``fixed_advance``: the last call decides.
        """
        self._frame = (width, l, r)
        self._advance = None

    def fixed_advance(self, advance: float):
        """Center the drawing in a fixed advance (tabular figures, monospace)."""
        self._frame = (None, 0, 0)
        self._advance = advance

    def sidebearing(self, kind) -> float:
        p = self.p
        base = (0.185 * p.n_counter + 12.0 + 0.04 * p.weight) * p.spacing
        if self.case == "upper":
            base *= 1.2
        elif self.case == "figure":
            base *= 1.05
        mult = {"s": 1.0, "r": 0.52, "d": 0.16, "o": 0.42, "t": 0.3, "0": 0.0}
        k = mult[kind] if isinstance(kind, str) else float(kind)
        return base * k

    # -- finishing -------------------------------------------------------------
    def outlines(self, keep_structure: bool = False) -> list:
        """Expand strokes and shapes into contours (overlapping)."""
        p = self.p
        out = []
        for s in (self._settled(self.strokes) if p.serif > 0 else self.strokes):
            out.extend(expand(s, self.pen, p.roundness, keep_structure))
        for kind, contour, radii in self.shapes:
            if radii is not None:
                c = fillet(contour, list(radii), keep_structure)
                contour = c if keep_structure else clean(c)
            out.append(contour)
        return out

    # -- one width for every glyph ------------------------------------------------
    @property
    def is_mark(self) -> bool:
        """A combining mark: no width and no advance. It stays that way in a monospaced font."""
        return self._frame is not None and self._frame[0] == 0 and self._advance is None

    def drawn_width(self) -> float:
        """The width the recipe declared, or the width of the drawing."""
        width = self._frame[0] if self._frame is not None else None
        if width is None:
            b = contour_bounds(self.outlines())
            width = b[2] - b[0] if b else 0.0
        elif self.p.serif > 0:
            left, right = self._past_frame(width, contour_bounds(self.outlines()))
            width += left + right
        return width

    def _past_frame(self, width: float, b) -> tuple:
        """How far slabs reach past the left and the right side of a declared frame.

        Only slabs count: a recipe may let a tail hang past its frame on purpose (j).
        """
        if self.slab_reach is not None:
            return self.slab_reach                   # measured before an effect redrew the glyph
        ends = [s.nodes[-1].p.real for s in self._settled(self.strokes) if s.anchor is not None]
        if not b or not ends:
            return 0.0, 0.0
        left = -b[0] if b[0] < 0 and min(ends) <= b[0] + 0.5 else 0.0
        right = b[2] - width if b[2] > width and max(ends) >= b[2] - 0.5 else 0.0
        return left, right

    @staticmethod
    def cell_room(p: Params) -> float:
        """The widest drawing that fits a monospaced cell."""
        return p.mono * 0.88

    def room(self) -> float:
        """The widest drawing this glyph may have in a monospaced cell."""
        if self.full_cell:
            return self.p.mono
        return self.p.mono * self.cell_share if self.cell_share else self.cell_room(self.p)

    def finish(self, unicode: int | None = None, keep_structure: bool = False) -> Glyph:
        """Turn the drawing into a :class:`Glyph`."""
        p = self.p
        contours = self.outlines(keep_structure)
        width, l, r = self._frame if self._frame is not None else (None, "s", "s")
        x0 = 0.0
        lsb = self.sidebearing(l)
        rsb = self.sidebearing(r)
        if width is None:
            b = contour_bounds(contours)
            x0, width = (b[0], b[2] - b[0]) if b else (0.0, 0.0)
        elif p.serif > 0:
            # Slabs reach past the stems into the sidebearings, as in any serif face: the stems keep
            # their distance, and a slab keeps a little white from the next letter's slab.
            left, right = self._past_frame(width, contour_bounds(contours))
            x0, width = -left, width + left + right
            lsb = max(lsb - left, min(lsb, lsb * 0.3))
            rsb = max(rsb - right, min(rsb, rsb * 0.3))
        squeeze = 1.0
        if p.mono > 0 and not self.is_mark:
            # A fixed cell. A drawing that is still too wide is squeezed; the white that is
            # left is shared the way the sidebearings would have shared it, but nearly evenly.
            room = self.room()
            if width > room:
                squeeze = room / width
            free = p.mono - width * squeeze
            share = lsb / (lsb + rsb) if lsb + rsb > 1e-6 and lsb >= 0 and rsb >= 0 else 0.5
            lsb = free * min(0.58, max(0.42, share))
            rsb = free - lsb
        elif self._advance is not None:
            lsb = (self._advance - width) / 2
            rsb = self._advance - width - lsb
        m = (squeeze, 0.0, 0.0, 1.0, lsb - x0 * squeeze, 0.0)
        if p.slant:
            # shear about the middle of the x-height so the glyph stays centered
            t = math.tan(math.radians(p.slant))
            m = (squeeze, 0.0, t, 1.0, lsb - x0 * squeeze - t * p.xh / 2, 0.0)
        width *= squeeze
        contours = [transform_contour(c, lambda q: apply_affine(m, q)) for c in contours]
        if not keep_structure:
            contours = union(contours)
            if self.cutouts:
                from .outline import difference
                cut = [transform_contour(c, lambda q: apply_affine(m, q)) for c in self.cutouts]
                contours = difference(contours, cut)
        anchors = {k: apply_affine(m, v) for k, v in self.anchors.items()}
        strokes = [s.transformed(lambda q: apply_affine(m, q)) for s in self.strokes]
        layers = [(key, [transform_contour(c, lambda q: apply_affine(m, q)) for c in cs])
                  for key, cs in self.layers]
        return Glyph(self.name, round(lsb + width + rsb), contours, unicode, anchors, layers, strokes,
                     self.static_only or bool(self.cutouts))


# --------------------------------------------------------------------------
# Recipe registry
# --------------------------------------------------------------------------

#: The characters of :meth:`Recipes.only`: what a title or a poster needs.
BASIC = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
         " .,:;!?'\"-()[]/&@#%$*+=<>\u2018\u2019\u201c\u201d\u2013\u2014\u2026\u00b7")

#: In a monospaced font these signs are drawn at least this wide, as a share of the cell:
#: the operators of code read as words, and a small one looks like a mistake.
MONO_SIGNS = {"+": 0.60, "-": 0.56, "=": 0.60, "<": 0.56, ">": 0.56, "~": 0.60, "^": 0.52, "\u2212": 0.60,
              "\u00d7": 0.52, "\u00f7": 0.60, "\u00b1": 0.60, "\u2013": 0.70, "\u00ac": 0.56}
#: These fill the cell from edge to edge, so that a row of them is one line.
MONO_FULL = "_\u2014"

@dataclass
class Recipe:
    name: str
    fn: object
    unicode: int | None
    case: str
    #: For a recipe that wraps a whole glyph with an effect (a tile, a glow, paint):
    #: the plain drawing it wraps. An accented letter builds on this, so the base
    #: letter under an accent is drawn plain and the effect is applied once.
    plain: object = None

    def __call__(self, g: "G"):
        """Draw this recipe on ``g``, so a new recipe can start from a stock one: ``latin()["r"](g)``."""
        return self.fn(g)


class Recipes(dict):
    """A named set of recipes. Later definitions replace earlier ones."""

    #: True where an accented letter is a composite of separate glyphs, as in a retraced font: an effect
    #: then decorates the combining marks too. In the engine's own sets an accented letter is drawn as a
    #: whole and decorated once, so its marks stay plain.
    parts = False

    def add(self, name: str, unicode: int | str | None = None, case: str = "lower"):
        if isinstance(unicode, str):
            unicode = ord(unicode)

        def deco(fn):
            self[name] = Recipe(name, fn, unicode, case)
            return fn
        return deco

    def copy(self) -> "Recipes":
        r = Recipes()
        r.update(self)
        r.parts = self.parts
        return r

    def only(self, chars: str = "", vietnamese: bool = False, greek: bool = False,
             cyrillic: bool = False) -> "Recipes":
        """A copy with just the glyphs for ``chars`` (default: letters, figures and common signs).

        Use it for a color font whose glyphs are heavy, such as brush marks (about 10 KB a glyph):
        fewer glyphs build faster and make a smaller file. The space is always kept. Glyphs without
        a code point (the forms of the OpenType features) are left out, so the font gets none of
        those features.
        ``vietnamese=True`` keeps the Vietnamese alphabet too, with its tone marks and the dong sign.
        ``greek=True`` keeps the Greek letters, with the tonos and the dialytika, and ``cyrillic=True``
        the Cyrillic ones (if the set has them).
        """
        chars = chars or BASIC
        if vietnamese:
            from .recipes.vietnamese import ALPHABET
            chars += ALPHABET
        if greek:
            from .recipes.greek import ALPHABET as GREEK_ALPHABET
            chars += GREEK_ALPHABET
        if cyrillic:
            from .recipes.cyrillic import ALPHABET as CYRILLIC_ALPHABET
            chars += CYRILLIC_ALPHABET
        want = {ord(c) for c in chars} | {0x20, 0xA0}
        r = Recipes()
        r.update({n: rec for n, rec in self.items() if rec.unicode in want})
        return r

    def draw(self, name: str, p: Params, keep_structure: bool = False) -> Glyph:
        rec = self[name]
        g = self._run(rec, p)
        if p.mono > 0 and not g.is_mark:
            g = self._fit(rec, p, g)
        return g.finish(rec.unicode, keep_structure)

    def _run(self, rec: Recipe, p: Params) -> G:
        g = G(p, rec.name, rec.case)
        g.recipes = self
        rec.fn(g)
        return g

    def _fit(self, rec: Recipe, p: Params, g: G) -> G:
        """Fit a glyph to a monospaced cell by drawing it again, narrower or wider.

        A letter that is too wide (m, w, @) is drawn with narrower counters, which keeps
        its stems at full weight. A letter or figure that is much narrower than the cell
        (r, f, t) is drawn wider. Signs and punctuation keep their size.
        """
        w0 = g.drawn_width()
        if w0 <= 0 or g.full_cell:
            return g                        # nothing drawn, or a recipe that fills the cell itself
        room = g.room()
        ch = chr(rec.unicode) if rec.unicode is not None else ""
        if not ch and "." in rec.name:
            # a form without a code point (emdash.case, two.dnom) is fitted like the glyph it stands for
            stands = self.get(rec.name.split(".")[0])
            ch = chr(stands.unicode) if stands is not None and stands.unicode is not None else ""
        full = bool(ch) and ch in MONO_FULL
        least = p.mono * (0.60 if ch.isalnum() else MONO_SIGNS.get(ch, 0.0))
        if full:
            target = p.mono
        elif w0 > room:
            target = room
        elif w0 < least:
            target = least
        else:
            return g
        # A glyph wrapped by an effect is fitted with its plain drawing, and the effect runs once
        # at the width that fits: an effect can be slow, and it does not change the width.
        trial = Recipe(rec.name, rec.plain, rec.unicode, rec.case) if rec.plain is not None else rec
        k0, best, best_w, best_k = 1.0, g, w0, 1.0
        k1 = target / w0
        for _ in range(5):
            k1 = max(0.3, min(1.9, k1))
            g1 = self._run(trial, p.but(width=p.width * k1))
            w1 = g1.drawn_width()
            if abs(w1 - target) < abs(best_w - target) and (target != room or w1 <= room + 0.5 or best_w > room):
                best, best_w, best_k = g1, w1, k1
            if abs(w1 - target) < 1.5 or abs(w1 - w0) < 0.25 or abs(k1 - k0) < 1e-6:
                break                       # close enough, or the width does not answer (a bare stem)
            k2 = k1 + (target - w1) * (k1 - k0) / (w1 - w0)
            k0, w0, k1 = k1, w1, k2
        if trial is not rec and best is not g:
            best = self._run(rec, p.but(width=p.width * best_k))
        # the glyph was drawn with other counters; it is still a glyph of this style
        best.p = best.p.but(width=p.width)
        best.full_cell = full
        return best
