"""Skeleton strokes and the expander that turns them into outlines.

A glyph is drawn as a handful of *strokes*. Each stroke is a centerline (lines
and cubic Beziers through a list of nodes) and the expander gives it thickness
with a *pen*:

* ``Pen`` is an elliptical pen. The half-width of the stroke depends on the
  direction of travel, so one pen gives thick verticals and thin horizontals
  (``contrast``) and can be rotated (``angle``, the stress of the letterform).
* Each node carries a width multiplier ``w`` and an optional ``taper``. That is
  how stems flare toward their terminals and how joins thin out.
* Caps are flat. A cap can be cut along a fixed direction (for example the
  baseline), and its corners can be rounded by ``roundness`` from 0 (sharp) to
  1 (a full semicircle).

With ``keep_structure=True`` the expander emits the same segments for the same
skeleton, whatever the pen. That makes every weight, width and contrast
setting point-compatible, which is what a variable font needs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .geom import (
    contour_area,
    cross,
    dot,
    left,
    line_hit,
    polar,
    reverse_contour,
    seg_length,
    seg_point,
    seg_tangent,
    split_cubic,
    unit,
)


# --------------------------------------------------------------------------
# Pen
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Pen:
    """An elliptical pen.

    ``a`` is the half-thickness of a stroke drawn across the nib (the thick
    direction), ``b`` the half-thickness of a stroke drawn along it (the thin
    direction). ``angle`` rotates the nib counter-clockwise from horizontal:
    0 gives vertical stress (thin horizontals), 20-30 gives the diagonal
    stress of humanist letters.
    """

    a: float
    b: float
    angle: float = 0.0

    def __post_init__(self):
        # the nib axis, worked out once: half() runs a million times in a build
        ax = polar(self.angle)
        object.__setattr__(self, "_ax", (ax.real, ax.imag))

    def half(self, tangent: complex) -> float:
        cx, cy = self._ax
        tx, ty = tangent.real, tangent.imag
        # the normal is the tangent turned left: (-ty, tx)
        return math.hypot(self.a * (tx * cy - ty * cx), self.b * (cx * tx + cy * ty))

    def scaled(self, k: float) -> "Pen":
        return Pen(self.a * k, self.b * k, self.angle)

    @staticmethod
    def for_stems(vertical: float, contrast: float = 1.0, angle: float = 0.0) -> "Pen":
        """A pen whose *vertical* strokes are exactly ``vertical`` units thick.

        ``contrast`` is thin/thick (1 = monoline).
        """
        t = math.radians(angle)
        k = math.hypot(math.cos(t), contrast * math.sin(t))
        a = vertical / 2 / k
        return Pen(a, a * contrast, angle)


class FixedPen:
    """A pen with the same half-width in every direction."""

    def __init__(self, half: float):
        self._h = half

    def half(self, tangent: complex) -> float:
        return self._h


# --------------------------------------------------------------------------
# Skeleton
# --------------------------------------------------------------------------

@dataclass
class Node:
    p: complex
    w: float = 1.0
    #: How the width changes near this node when its neighbor has another
    #: width. None or 1 is a straight taper, 0 keeps the sides parallel to the
    #: skeleton here (a waist), larger values make the change more abrupt
    #: (a sharp flare).
    taper: float | None = None
    #: Force a corner (True) or a smooth join (False); None decides by angle.
    corner: bool | None = None
    #: At a corner: cut the outer point off along the horizontal line y = apex.
    apex: float | None = None
    #: Width multipliers for the left and the right side alone (None: ``w``).
    #: A terminal on a curve flares on its outer side only.
    wl: float | None = None
    wr: float | None = None

    def side_w(self, sign: float) -> float:
        v = self.wl if sign > 0 else self.wr
        return self.w if v is None else v


@dataclass
class Cap:
    #: Direction of the cut line. None cuts square to the stroke.
    cut: complex | None = None
    #: Corner rounding 0..1 for this cap. None uses the stroke's roundness.
    round: float | None = None


@dataclass
class Stroke:
    nodes: list[Node]
    #: One entry per segment: None for a line, (h1, h2) absolute handles for a cubic.
    handles: list[tuple[complex, complex] | None]
    closed: bool = False
    start: Cap = field(default_factory=Cap)
    end: Cap = field(default_factory=Cap)
    #: Multiplies the pen for this stroke.
    scale: float = 1.0
    #: None uses the pen. A number fixes the half-width in every direction.
    fixed: float | None = None
    #: Round the outside of corners inside the stroke as well as the caps.
    round_joins: bool = True
    miter_limit: float = 2.5
    #: Free-form tag, used by recipes and proofs.
    tag: str = ""
    #: For a slab serif: the point on the edge of the stem it grows from. The engine may shorten
    #: a slab that meets another one across a narrow counter, but never past this point.
    anchor: complex | None = None

    def segment(self, i: int):
        a = self.nodes[i].p
        b = self.nodes[(i + 1) % len(self.nodes)].p
        h = self.handles[i]
        return (a, b) if h is None else (a, h[0], h[1], b)

    def segments(self):
        n = len(self.nodes) if self.closed else len(self.nodes) - 1
        return [self.segment(i) for i in range(n)]

    def transformed(self, fn, yfn=None, flip: bool = False) -> "Stroke":
        """Map every point through ``fn``. ``yfn`` maps apex cut heights.

        ``flip`` says the map mirrors the stroke, so left and right swap."""
        nodes = [Node(fn(n.p), n.w, n.taper, n.corner,
                      n.apex if (n.apex is None or yfn is None) else yfn(n.apex),
                      n.wr if flip else n.wl, n.wl if flip else n.wr)
                 for n in self.nodes]
        handles = [None if h is None else (fn(h[0]), fn(h[1])) for h in self.handles]
        return Stroke(nodes, handles, self.closed, self.start, self.end, self.scale,
                      self.fixed, self.round_joins, self.miter_limit, self.tag,
                      None if self.anchor is None else fn(self.anchor))


# --------------------------------------------------------------------------
# Expansion
# --------------------------------------------------------------------------

CORNER_DEG = 3.0
_DU = 1e-3


def _hermite(u: float, wa: float, wb: float, sa: float, sb: float) -> float:
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * wa + (u3 - 2 * u2 + u) * sa
            + (-2 * u3 + 3 * u2) * wb + (u3 - u2) * sb)


class _Seg:
    """One skeleton segment with its width function."""

    def __init__(self, seg, na: Node, nb: Node, pen, scale: float):
        self.seg = seg
        self.cubic = len(seg) == 4
        self.pen = pen
        self.scale = scale
        ta = 1.0 if na.taper is None else na.taper
        tb = 1.0 if nb.taper is None else nb.taper
        #: per side: (width at a, width at b, slope at a, slope at b)
        self.sides = {}
        differs = False
        for sign in (1.0, -1.0):
            wa, wb = na.side_w(sign), nb.side_w(sign)
            self.sides[sign] = (wa, wb, ta * (wb - wa), tb * (wb - wa))
            differs = differs or abs(wb - wa) > 1e-9
        # Decided by how the nodes were declared, not by the widths alone, so a
        # flare of zero keeps the same structure as any other flare.
        self.tapered = differs or na.taper not in (None, 0.0) or nb.taper not in (None, 0.0)
        self.t0 = seg_tangent(seg, 0)
        self.t1 = seg_tangent(seg, 1)
        #: a straight segment of constant width: its sides run parallel to it
        self.plain = not self.cubic and not self.tapered
        self._deriv: dict = {}

    def tangent(self, u: float, raw: bool = False) -> complex:
        if not raw:
            if u <= 0:
                return self.t0
            if u >= 1:
                return self.t1
        return seg_tangent(self.seg, min(1.0, max(0.0, u)))

    def half(self, u: float, raw: bool = False, sign: float = 1.0) -> float:
        w = _hermite(u, *self.sides[sign])
        return self.pen.half(self.tangent(u, raw)) * self.scale * max(w, 0.0)

    def offset(self, u: float, sign: float, raw: bool = False) -> complex:
        t = self.tangent(u, raw)
        return seg_point(self.seg, u) + left(t) * sign * self.half(u, raw, sign)

    def deriv(self, u: float, sign: float) -> complex:
        """d(offset)/du, by finite differences on the raw curve."""
        key = (u, sign)
        d = self._deriv.get(key)
        if d is None:
            u0, u1 = max(0.0, u - _DU), min(1.0, u + _DU)
            d = self._deriv[key] = (self.offset(u1, sign, True) - self.offset(u0, sign, True)) / (u1 - u0)
        return d

    def direction(self, u: float, sign: float) -> complex:
        t = self.tangent(u, True)
        if self.plain:
            return t
        d = unit(self.deriv(u, sign))
        if d == 0 or dot(d, t) < 0.1:
            return t
        return d


@dataclass
class _Piece:
    s: _Seg
    u0: float
    u1: float
    plain_line: bool
    corner_after: bool = False
    node_after: Node | None = None

    @property
    def ta(self):
        return self.s.tangent(self.u0)

    @property
    def tb(self):
        return self.s.tangent(self.u1)


def _fit_side(pc: _Piece, sign: float, d0: complex, d1: complex):
    """One side of one piece, as a line or a cubic."""
    s = pc.s
    q0 = s.offset(pc.u0, sign)
    q1 = s.offset(pc.u1, sign)
    if pc.plain_line:
        return (q0, q1)
    du = pc.u1 - pc.u0
    chord = abs(q1 - q0)
    if chord < 1e-9:
        return (q0, q0, q1, q1)
    # Handles that match the end derivatives. Exact for a tapered line.
    a = abs(s.deriv(pc.u0, sign)) * du / 3
    b = abs(s.deriv(pc.u1, sign)) * du / 3
    if s.cubic:
        # Better for curves: make the cubic pass through the true midpoint.
        qm = s.offset((pc.u0 + pc.u1) / 2, sign)
        rhs = (qm - (q0 + q1) / 2) * (8.0 / 3.0)
        den = cross(d0, -d1)
        if abs(den) > 1e-3:
            fa = cross(rhs, -d1) / den
            fb = cross(d0, rhs) / den
            if 0.02 * chord < fa < 1.6 * chord and 0.02 * chord < fb < 1.6 * chord:
                a, b = fa, fb
    a = min(a, 1.6 * chord)
    b = min(b, 1.6 * chord)
    return (q0, q0 + d0 * a, q1 - d1 * b, q1)


def _set_start(seg, p):
    if len(seg) == 2:
        return (p, seg[1])
    return (p, seg[1] + (p - seg[0]), seg[2], seg[3])


def _set_end(seg, p):
    if len(seg) == 2:
        return (seg[0], p)
    return (seg[0], seg[1], seg[2] + (p - seg[3]), p)


# --------------------------------------------------------------------------
# Fillets
# --------------------------------------------------------------------------

def _point_from_start(seg, dist: float, length: float) -> complex:
    if len(seg) == 2:
        return seg[0] + unit(seg[1] - seg[0]) * dist
    return seg_point(seg, min(1.0, dist / max(length, 1e-9)))


def _point_from_end(seg, dist: float, length: float) -> complex:
    if len(seg) == 2:
        return seg[1] - unit(seg[1] - seg[0]) * dist
    return seg_point(seg, max(0.0, 1 - dist / max(length, 1e-9)))


def _trim(seg, start_cut: float, end_cut: float, length: float):
    if start_cut <= 1e-9 and end_cut <= 1e-9:
        return seg
    if len(seg) == 2:
        d = unit(seg[1] - seg[0])
        return (seg[0] + d * start_cut, seg[1] - d * end_cut)
    length = max(length, 1e-9)
    t0 = min(1.0, start_cut / length)
    t1 = max(t0, 1 - end_cut / length)
    out = seg
    if t1 < 1:
        out, _ = split_cubic(out, t1)
    if t0 > 0:
        _, out = split_cubic(out, t0 / t1 if t1 > 1e-9 else 0.0)
    return out


def fillet(contour: list, radii: list, keep: bool = False) -> list:
    """Round corners of a closed contour.

    ``radii[i]`` applies to the vertex where segment ``i`` starts; None leaves
    the vertex alone. With ``keep`` every vertex that has a radius gets an arc
    segment, even if the arc has no size, so the structure never changes.
    Vertices joined by zero-length segments are rounded as one corner.
    """
    n = len(contour)
    flagged = [r is not None and (keep or r > 1e-6) for r in radii]
    if not any(flagged):
        return contour
    lens = [seg_length(s) for s in contour]
    real = [ln > 1e-6 for ln in lens]
    if sum(real) < 2:
        return contour

    # Group vertices into clusters: a cluster is a run of vertices joined by
    # zero-length segments. It starts at the vertex after a real segment.
    start = next(i for i in range(n) if real[(i - 1) % n])
    out: list = []
    i = start
    visited = 0
    # First pass: the trim wanted at each real segment's start and end.
    clusters = []
    while visited < n:
        members = [i]
        while not real[members[-1]]:
            members.append((members[-1] + 1) % n)
            if len(members) > n:
                break
        clusters.append(members)
        visited += len(members)
        i = (members[-1] + 1) % n
    info = {}
    for members in clusters:
        first, last = members[0], members[-1]
        prev = (first - 1) % n
        rs = [radii[v] for v in members if flagged[v]]
        ell = 0.0
        alpha = 0.0
        d_in = seg_tangent(contour[prev], 1)
        d_out = seg_tangent(contour[last], 0)
        if rs:
            alpha = abs(math.atan2(cross(d_in, d_out), dot(d_in, d_out)))
            if 1e-3 < alpha < math.pi - 1e-3:
                ell = max(rs) * math.tan(alpha / 2)
                ell = max(0.0, min(ell, lens[prev] * 0.5, lens[last] * 0.5))
        info[first] = (members, prev, last, ell, alpha, d_in, d_out)
    cut_start = {m[2]: m[3] for m in info.values()}   # real segment index -> trim at its start
    cut_end = {m[1]: m[3] for m in info.values()}     # real segment index -> trim at its end

    for members in clusters:
        mem, prev, last, ell, alpha, d_in, d_out = info[members[0]]
        corner = contour[last][0]
        if ell > 1e-9:
            pa = _point_from_end(contour[prev], ell, lens[prev])
            pb = _point_from_start(contour[last], ell, lens[last])
            kappa = (4.0 / 3.0) * math.tan(alpha / 4) / math.tan(alpha / 2)
            arc = (pa, pa + d_in * ell * kappa, pb - d_out * ell * kappa, pb)
        else:
            pa = pb = corner
            arc = (corner, corner, corner, corner)
        done_arc = False
        for v in mem:
            if flagged[v]:
                if not done_arc:
                    out.append(arc)
                    done_arc = True
                else:
                    out.append((pb, pb, pb, pb))
            if v == last:
                out.append(_trim(contour[v], cut_start.get(v, 0.0), cut_end.get(v, 0.0), lens[v]))
            else:
                at = pb if done_arc else pa
                seg = contour[v]
                out.append((at, at) if len(seg) == 2 else (at, at, at, at))
    return out


def clean(contour: list) -> list:
    """Drop zero-length segments and turn straight cubics into lines."""
    out = []
    for seg in contour:
        if all(abs(p - seg[0]) < 1e-3 for p in seg):
            continue
        if len(seg) == 4:
            d = seg[3] - seg[0]
            n = abs(d)
            if n > 1e-6 and abs(cross(seg[1] - seg[0], d)) / n < 0.02 and abs(cross(seg[2] - seg[0], d)) / n < 0.02:
                t1 = dot(seg[1] - seg[0], d) / (n * n)
                t2 = dot(seg[2] - seg[0], d) / (n * n)
                if -0.01 <= t1 <= 1.01 and -0.01 <= t2 <= 1.01:
                    seg = (seg[0], seg[3])
        out.append(seg)
    for i in range(len(out)):
        nxt = out[(i + 1) % len(out)]
        if abs(out[i][-1] - nxt[0]) > 1e-9:
            out[i] = out[i][:-1] + (nxt[0],)
    # merge neighboring lines that continue each other
    merged: list = []
    for seg in out:
        if merged and len(seg) == 2 and len(merged[-1]) == 2:
            a, b, c = merged[-1][0], merged[-1][1], seg[1]
            n = abs(c - a)
            if n > 1e-6 and abs(cross(b - a, c - a)) / n < 0.05 and dot(b - a, c - b) > 0:
                merged[-1] = (a, c)
                continue
        merged.append(seg)
    return merged


#: The least angle between a cut and the stroke it cuts: 38 degrees.
_LEAST_CUT_SIN, _LEAST_CUT_COS = math.sin(math.radians(38)), math.cos(math.radians(38))


def _cut_segment(seg, origin: complex, c: complex, at_end: bool, reach: float):
    """Make a side segment end (or start) on the line through ``origin`` along ``c``.

    If the segment crosses the line it is trimmed there. If it stops short it
    is extended along its end tangent, by ``reach`` at most. The result is
    always one segment of the same kind.
    """
    def side(p):
        return cross(c, p - origin)

    if not at_end:
        out = _cut_segment(tuple(reversed(seg)), origin, c, True, reach)
        return tuple(reversed(out))
    steps = 24
    prev_t, prev_f = 1.0, side(seg_point(seg, 1.0))
    if abs(prev_f) < 1e-6:
        return seg
    for i in range(1, steps + 1):
        t = 1.0 - i / steps * 0.75          # never cut away more than three quarters
        f = side(seg_point(seg, t))
        if (f > 0) != (prev_f > 0):
            lo, hi = t, prev_t               # the crossing is between lo and hi
            f_lo = f
            for _ in range(30):
                mid = (lo + hi) / 2
                fm = side(seg_point(seg, mid))
                if (fm > 0) == (f_lo > 0):
                    lo = mid
                else:
                    hi = mid
            t_cut = (lo + hi) / 2
            if len(seg) == 2:
                return (seg[0], seg_point(seg, t_cut))
            return split_cubic(seg, t_cut)[0]
        prev_t, prev_f = t, f
    # no crossing: extend along the end tangent
    q = seg[-1]
    d = seg_tangent(seg, 1)
    hit = line_hit(q, d, origin, c)
    if hit is None or dot(hit - q, d) <= 0:
        return seg
    if abs(hit - q) > reach:
        hit = q + d * reach
    return _set_end(seg, hit)


# --------------------------------------------------------------------------
# The expander
# --------------------------------------------------------------------------

def _pieces(stroke: Stroke, pen) -> list[_Piece]:
    n = len(stroke.nodes)
    count = n if stroke.closed else n - 1
    segs: list[_Seg] = []
    for i in range(count):
        segs.append(_Seg(stroke.segment(i), stroke.nodes[i], stroke.nodes[(i + 1) % n], pen, stroke.scale))

    # Decide corners at nodes, and share one tangent across smooth joins.
    corner_at: dict[int, bool] = {}
    joins = range(count) if stroke.closed else range(count - 1)
    for i in joins:
        a, b = segs[i], segs[(i + 1) % count]
        node = stroke.nodes[(i + 1) % n]
        ang = abs(math.degrees(math.atan2(cross(a.t1, b.t0), dot(a.t1, b.t0))))
        if node.corner is not None:
            is_corner = node.corner
        elif a.cubic or b.cubic:
            # A curve joins smoothly unless the recipe says otherwise. Deciding
            # by angle would let the structure change from one master to the next.
            is_corner = False
        else:
            is_corner = ang > CORNER_DEG
        corner_at[i] = is_corner
        if not is_corner:
            t = unit(a.t1 + b.t0) or a.t1
            a.t1 = t
            b.t0 = t

    out: list[_Piece] = []
    for i, s in enumerate(segs):
        node = stroke.nodes[(i + 1) % n]
        if s.cubic:
            out.append(_Piece(s, 0.0, 0.5, False))
            out.append(_Piece(s, 0.5, 1.0, False, corner_at.get(i, False), node))
        else:
            out.append(_Piece(s, 0.0, 1.0, not s.tapered, corner_at.get(i, False), node))
    return out


def _outer_join(a, da, b, db, node: Node, hmax: float, limit: float):
    """Three segments that join two side ends around the outside of a corner."""
    mpt = line_hit(a, da, b, db)
    if mpt is None or dot(mpt - a, da) < -1e-6 or dot(b - mpt, db) < -1e-6:
        mid = (a + b) / 2
        return [(a, mid), (mid, mid), (mid, b)]
    m1 = m2 = mpt
    done = False
    if node.apex is not None:
        y = node.apex
        if (mpt.imag - y) * (y - node.p.imag) > 0:
            # The point passes the line: cut it off. A side end that is itself
            # past the line gets a short fold back, which the union removes.
            c1 = line_hit(a, da, complex(0, y), 1 + 0j)
            c2 = line_hit(b, db, complex(0, y), 1 + 0j)
            # A side that runs almost level with the line (the top bar of a 7 drawn small and heavy)
            # meets it far away: that is no point to cut, so the corner keeps its miter.
            far = 20 * hmax
            if c1 is not None and c2 is not None and abs(c1 - node.p) < far and abs(c2 - node.p) < far:
                m1, m2 = c1, c2
                done = True
    if not done and abs(mpt - node.p) > limit * hmax:
        axis = unit(mpt - node.p)
        p = node.p + axis * limit * hmax
        c1 = line_hit(a, da, p, left(axis))
        c2 = line_hit(b, db, p, left(axis))
        if c1 is not None and c2 is not None:
            m1, m2 = c1, c2
    return [(a, m1), (m1, m2), (m2, b)]


def expand(stroke: Stroke, pen, roundness: float = 0.0, keep_structure: bool = False) -> list[list]:
    """Turn a skeleton stroke into closed contours.

    Returns one contour for an open stroke and two (outer, inner) for a closed
    one. Outer contours run clockwise, inner ones counter-clockwise (TrueType
    direction, y up).
    """
    if stroke.fixed is not None:
        pen = FixedPen(stroke.fixed)
    pieces = _pieces(stroke, pen)
    if not pieces:
        return []
    m = len(pieces)
    joins = range(m) if stroke.closed else range(m - 1)

    def build_side(sign: float):
        d0 = [pc.s.direction(pc.u0, sign) for pc in pieces]
        d1 = [pc.s.direction(pc.u1, sign) for pc in pieces]
        for i in joins:
            j = (i + 1) % m
            if not pieces[i].corner_after:
                d = unit(d1[i] + d0[j]) or d1[i]
                d1[i] = d0[j] = d
        segs = [_fit_side(pc, sign, d0[i], d1[i]) for i, pc in enumerate(pieces)]
        links: dict[int, tuple[list, list]] = {}
        for i in joins:
            j = (i + 1) % m
            pi, pj = pieces[i], pieces[j]
            if not pi.corner_after:
                # Smooth join: both sides computed the same point; make it exact.
                segs[j] = _set_start(segs[j], segs[i][-1])
                continue
            node = pi.node_after
            ta, tb = pi.tb, pj.ta
            turn = cross(ta, tb)
            a, b = segs[i][-1], segs[j][0]
            ha = abs(a - node.p)
            hb = abs(b - node.p)
            outer = (turn > 0) == (sign < 0)
            if outer:
                conn = _outer_join(a, d1[i], b, d0[j], node, max(ha, hb), stroke.miter_limit)
                r = max(ha, hb) if stroke.round_joins else None
                links[i] = (conn, [None, r, r])
            else:
                if pi.plain_line and pj.plain_line:
                    hit = line_hit(a, ta, b, tb)
                    if hit is not None and dot(hit - segs[i][0], ta) > 0 and dot(segs[j][-1] - hit, tb) > 0:
                        segs[i] = _set_end(segs[i], hit)
                        segs[j] = _set_start(segs[j], hit)
                        a = b = hit
                links[i] = ([(a, b)], [None])
        out: list = []
        radii: list = []
        for i in range(m):
            out.append(segs[i])
            radii.append(None)
            if i in links:
                conn, rr = links[i]
                out.extend(conn)
                radii.extend(rr)
        return out, radii

    lsegs, lrad = build_side(1.0)
    rsegs, rrad = build_side(-1.0)

    def finish(contour, radii):
        contour = fillet(contour, radii, keep_structure)
        return contour if keep_structure else clean(contour)

    if stroke.closed:
        result = []
        for segs, rad in ((lsegs, lrad), (rsegs, rrad)):
            rr = [None if r is None else r * roundness for r in rad]
            result.append(finish(list(segs), rr))
        areas = [abs(contour_area(c)) for c in result]
        outer, inner = (result[0], result[1]) if areas[0] >= areas[1] else (result[1], result[0])
        if contour_area(outer) > 0:
            outer = reverse_contour(outer)
        if contour_area(inner) < 0:
            inner = reverse_contour(inner)
        return [outer, inner]

    # Caps: cut along a fixed direction if asked.
    def cut(cap: Cap, piece: _Piece, at_end: bool):
        if cap.cut is None:
            return
        c = unit(cap.cut)
        u = piece.u1 if at_end else piece.u0
        # A cut that runs nearly along the stroke leaves a spike as long as the stroke is thick
        # (a horizontal cut on the arm of a heavy r). The cut keeps a least angle to the stroke.
        t = unit(piece.s.tangent(u, True))
        if dot(c, t) < 0:
            c = -c
        turn = cross(t, c)
        if abs(turn) < _LEAST_CUT_SIN:
            c = t * complex(_LEAST_CUT_COS, _LEAST_CUT_SIN if turn >= 0 else -_LEAST_CUT_SIN)
        origin = seg_point(piece.s.seg, u)
        reach = 2.6 * max(piece.s.half(u), 1.0)
        for segs in (lsegs, rsegs):
            idx = len(segs) - 1 if at_end else 0
            segs[idx] = _cut_segment(segs[idx], origin, c, at_end, reach)

    cut(stroke.end, pieces[-1], True)
    cut(stroke.start, pieces[0], False)

    r_end = roundness if stroke.end.round is None else stroke.end.round
    r_start = roundness if stroke.start.round is None else stroke.start.round
    l_start, l_end = lsegs[0][0], lsegs[-1][-1]
    r_start_pt, r_end_pt = rsegs[0][0], rsegs[-1][-1]
    end_radius = abs(l_end - r_end_pt) / 2 * r_end
    start_radius = abs(l_start - r_start_pt) / 2 * r_start

    # The contour runs: left side forward, end cap, right side backward, start cap.
    contour: list = []
    radii: list = []
    for k, (seg, r) in enumerate(zip(lsegs, lrad)):
        contour.append(seg)
        radii.append(start_radius if k == 0 else (None if r is None else r * roundness))
    contour.append((l_end, r_end_pt))
    radii.append(end_radius)
    nr = len(rsegs)
    for k in range(nr):
        contour.append(tuple(reversed(rsegs[nr - 1 - k])))
        if k == 0:
            radii.append(end_radius)
        else:
            # The vertex before reversed segment k is the one after forward segment nr-1-k.
            r = rrad[nr - k]
            radii.append(None if r is None else r * roundness)
    contour.append((r_start_pt, l_start))
    radii.append(start_radius)

    contour = finish(contour, radii)
    if contour_area(contour) > 0:
        contour = reverse_contour(contour)
    return [contour]
