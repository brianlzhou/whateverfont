"""Copper traces on a circuit board: the `traces` and `plain` effects and the palettes of Etchant.

Every letter of the engine is drawn from centerline strokes before it gets a thickness. A trace is a
centerline too, so the effect works on the strokes (``g.strokes``), not on the finished outline:

1. Each stroke is cut into chains at its corners. A straight chain at an odd angle becomes two or
   three runs at 0, 45 and 90 degrees: an upright or level run and a diagonal one, the way a board
   is routed. A curved chain is sampled, the direction of each sample is rounded to one of the eight,
   and each stretch of samples with one direction becomes one straight run. The runs meet where
   their lines cross, so a round letter becomes an octagon whose flat sides touch the old curve.
2. An end that was buried in another stroke slides along its run until it meets that trace, so
   traces join at T and L joints without stubs. Two traces that meet end to end become one.
3. Every square corner gets a 45 degree chamfer with legs of at least ``CHAMFER`` units.
4. Every end that is left free gets a round pad with a drilled hole, moved in along the trace so the
   pad stays inside the letter's height. The dots of i, j, !, ?, : and ; are pads. A T joint near
   the middle of a glyph gets a via.
5. The color layers, bottom first: mask (a lighter halo of solder mask around all copper), gap (the
   ring of bare board around each pad), trace, shine (a light line down the middle of each trace),
   via, pad, hole.
"""

from __future__ import annotations

import math

import pathops

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, cross, dot, reverse_contour, seg_length, seg_point, \
    seg_tangent, unit
from whateverfont.outline import circle, difference, dilate, from_path, union
from whateverfont.stroke import FixedPen, expand

# --------------------------------------------------------------------------
# Sizes, in font units (1000 to the em)
# --------------------------------------------------------------------------

W = 44.0            #: trace width: one width for every stroke of every glyph
PAD = 46.0          #: pad radius
HOLE = 16.0         #: drill hole radius in a pad
VIA = 36.0          #: via ring radius
VIA_HOLE = 14.0     #: drill hole radius in a via
HALO = 18.0         #: how far the lighter solder mask reaches past the copper
GAP = 7.0           #: the ring of bare board around a pad, where the mask stops short of it
SHINE = 12.0        #: a lighter line down the middle of a trace, where it catches the light
CHAMFER = 64.0      #: least leg of the 45 degree chamfer on a square corner
LIP = 8.0           #: how far a pad may pass the line that the stroke ended on (an overshoot)
DIAG = 15.0         #: a tangent this close to a diagonal (in degrees) makes a diagonal run
MAX_VIAS = 1        #: vias in one glyph, at most
CROSSBAR = 300.0    #: a bar shorter than this that crosses a stem (t, f) keeps plain ends

DIRS = [complex(math.cos(math.radians(45 * k)), math.sin(math.radians(45 * k))) for k in range(8)]
SQ = math.sqrt(0.5)


# --------------------------------------------------------------------------
# Small geometry
# --------------------------------------------------------------------------

def _ang(v: complex) -> float:
    return math.degrees(math.atan2(v.imag, v.real))


def _octi(v: complex, tol: float = 2.0) -> bool:
    """True if ``v`` runs within ``tol`` degrees of a multiple of 45."""
    a = _ang(v) / 45.0
    return abs(a - round(a)) * 45.0 < tol


def _kdir(v: complex) -> int:
    return round(_ang(v) / 45.0) % 8


def _quant(a: float) -> int:
    """The run direction for a tangent at ``a`` degrees, as a multiple of 45 (unwrapped).

    A tangent within ``DIAG`` degrees of a diagonal runs diagonally; any other runs level or upright.
    The window is narrower than an even split (22.5), so curves become level and upright runs with
    shorter chamfers, and the spine of an s lies flat.
    """
    ax = 90.0 * round(a / 90.0)
    off = a - ax
    if abs(off) <= 45.0 - DIAG:
        return round(ax / 45.0)
    return round(ax / 45.0) + (1 if off > 0 else -1)


def _hit(p: complex, d: complex, q: complex, e: complex):
    """Where the line p + s d crosses the line q + t e: (point, s, t), or None if parallel."""
    den = cross(d, e)
    if abs(den) < 1e-9:
        return None
    s = cross(q - p, e) / den
    t = cross(q - p, d) / den
    return p + d * s, s, t


def _seg_dist(p: complex, a: complex, b: complex) -> float:
    ab = b - a
    L2 = dot(ab, ab)
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, dot(p - a, ab) / L2))
    return abs(p - (a + ab * t))


def _poly_dist(p: complex, pts: list, closed: bool) -> float:
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n if closed else n - 1)]
    return min((_seg_dist(p, a, b) for a, b in segs), default=1e9)


def _clean(pts: list, closed: bool) -> list:
    """Drop repeated points and points in the middle of a straight run."""
    out = []
    for q in pts:
        if out and abs(q - out[-1]) < 0.5:
            continue
        out.append(q)
    if closed and len(out) > 2 and abs(out[0] - out[-1]) < 0.5:
        out.pop()
    changed = True
    while changed and len(out) > 2:
        changed = False
        n = len(out)
        rng = range(n) if closed else range(1, n - 1)
        for i in rng:
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            if abs(cross(unit(b - a), unit(c - b))) < 1e-3 and dot(b - a, c - b) > 0:
                del out[i]
                changed = True
                break
    return out


def _net(contours) -> float:
    """The inked area: outsides run clockwise (negative area), counters the other way."""
    return -sum(contour_area(c) for c in contours)


def _jiggled(shape: list, k: int) -> list:
    """A shape moved by a few hundredths of a unit, so that no two curves of a union coincide."""
    off = complex(((k * 7) % 11 - 5) * 0.013, ((k * 5) % 13 - 6) * 0.013)
    return [[tuple(q + off for q in seg) for seg in c] for c in shape]


def _merged(shapes: list) -> list:
    """The union of shapes (each a list of contours), checked.

    The boolean union sometimes returns a wrong outline without an error (the mask of the Cyrillic Ze
    lost a quarter of its area). The merged ink can be no smaller than its largest shape and no larger
    than all of them; if it is, the shapes are moved apart by a hair and merged again.
    """
    shapes = [s for s in shapes if s]
    if not shapes:
        return []
    nets = [_net(s) for s in shapes]
    lo, hi = max(nets) - 2.0, sum(nets) + 2.0
    out = []
    for k in range(8):
        flat = [c for i, s in enumerate(shapes) for c in (s if k == 0 else _jiggled(s, k * 3 + i))]
        out = union(flat)
        if lo <= _net(out) <= hi:
            return out
    return out


def _stroked(pts: list, closed: bool, width: float) -> list:
    """One polyline stroked with a round pen ``width`` wide: what a plotter draws with a round aperture.

    Bands built from separate capsules met on identical arcs at every bend, which the boolean union
    could not merge. The result is checked against the capsules it must cover, and redone a hair off if wrong.
    """
    h = width / 2
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n if closed else n - 1)]
    caps = [abs(b - a) * width + math.pi * h * h for a, b in segs]
    lo, hi = max(caps) * 0.97, sum(caps) + 2.0
    out = []
    for k in range(8):
        off = 0j if k == 0 else complex(((k * 7) % 11 - 5) * 0.013, ((k * 5) % 13 - 6) * 0.013)
        path = pathops.Path()
        pen = path.getPen()
        pen.moveTo(((pts[0] + off).real, (pts[0] + off).imag))
        for i, q in enumerate(pts[1:]):
            q = q + off * (1 + (i % 3) * 0.5)
            pen.lineTo((q.real, q.imag))
        if closed:
            pen.closePath()
        else:
            pen.endPath()
        path.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4.0)
        path.convertConicsToQuads()
        try:
            path.simplify(fix_winding=True, keep_starting_points=False, clockwise=True)
        except Exception:
            continue
        out = from_path(path)
        if lo <= _net(out) <= hi:
            return out
    return out


def _band(pieces, width: float) -> list:
    """Every polyline stroked ``width`` wide, merged."""
    return _merged([_stroked(pc.pts, pc.closed, width) for pc in pieces if len(pc.pts) >= 2])


def _disc(p: complex, r: float) -> list:
    c = circle(p.real, p.imag, r)
    return c if contour_area(c) < 0 else reverse_contour(c)


# --------------------------------------------------------------------------
# 1. Strokes into octilinear polylines
# --------------------------------------------------------------------------

def _segments(stroke) -> list:
    """The stroke's segments, with zero-length ones dropped and collinear lines merged."""
    out = []
    for seg in stroke.segments():
        if seg_length(seg) < 0.5:
            continue
        if out and len(seg) == 2 and len(out[-1]) == 2:
            a, b = out[-1]
            c = seg[1]
            if abs(cross(unit(b - a), unit(c - b))) < 0.004 and dot(b - a, c - b) > 0:
                out[-1] = (a, c)
                continue
        out.append(seg)
    return out


def _dogleg(a: complex, b: complex, pa: str, pb: str, avoid=None) -> list:
    """A straight run from a to b at an odd angle, as runs at 0, 45 and 90 degrees.

    ``pa`` and ``pb`` say what each end wants: "axis" (a level or upright run there) or "diag".
    """
    v = b - a
    if abs(v) < 1e-6 or _octi(v, 0.3):
        return [a, b]
    k = _ang(v) / 45.0
    lo, hi = math.floor(k), math.ceil(k)
    ax, dg = (lo, hi) if lo % 2 == 0 else (hi, lo)
    da, dd = DIRS[ax % 8], DIRS[dg % 8]
    det = cross(da, dd)
    alpha = cross(v, dd) / det          # along the axis
    beta = cross(da, v) / det           # along the diagonal
    near = "axis" if abs(k - ax) < abs(k - dg) else "diag"
    free_a, free_b = pa == "free", pb == "free"
    pa = near if pa == "near" else ("axis" if free_a else pa)
    pb = near if pb == "near" else ("axis" if free_b else pb)
    # a jog shorter than a quarter of a trace is not worth a bend: the run goes straight, at the
    # nearer direction, and its free end moves the few units that takes
    if alpha < W * 0.25 or beta < W * 0.25:
        dmain = da if alpha >= beta else dd
        if free_b:
            return [a, a + dmain * dot(v, dmain)]
        if free_a:
            return [b - dmain * dot(v, dmain), b]
        return [a, b]
    if pa == "axis" and pb == "diag":
        return [a, a + da * alpha, b]
    if pa == "diag" and pb == "axis":
        return [a, a + dd * beta, b]
    m = a + da * alpha / 2
    upright_ends = [a, m, m + dd * beta, b]
    m = a + dd * beta / 2
    upright_middle = [a, m, m + da * alpha, b]
    if pa == "axis" and free_a and free_b and avoid:
        # a stroke free at both ends (a slash): bend it where it keeps farther from the other strokes
        # (the slash of a fraction ran up beside the figures)
        def clearance(poly):
            return min((_seg_dist(q, poly[i], poly[i + 1]) for q in avoid for i in range(len(poly) - 1)),
                       default=1e9)
        if clearance(upright_middle) > clearance(upright_ends) + 10:
            return upright_middle
    return upright_ends if pa == "axis" else upright_middle


def _samples(segs: list):
    """Points and unwrapped tangent angles along a chain, about every 2.5 units."""
    pts, angs = [], []
    for j, seg in enumerate(segs):
        n = max(2, int(seg_length(seg) / 2.5))
        for i in range(0 if j == 0 else 1, n + 1):
            t = i / n
            pts.append(seg_point(seg, t))
            angs.append(_ang(seg_tangent(seg, t)))
    for i in range(1, len(angs)):
        while angs[i] - angs[i - 1] > 180:
            angs[i] -= 360
        while angs[i] - angs[i - 1] < -180:
            angs[i] += 360
    return pts, angs


def _runs(segs: list, closed: bool, pa: str, pb: str) -> list:
    """A curved chain as straight runs at multiples of 45 degrees."""
    pts, angs = _samples(segs)
    if closed:
        pts.pop()
        angs.pop()
    ks = [_quant(a) for a in angs]
    if closed:
        # start at a change of direction, so that no run is split across the start
        for i in range(len(ks)):
            if ks[i] != ks[i - 1]:
                break
        else:
            i = 0
        pts = pts[i:] + pts[:i]
        angs = angs[i:] + angs[:i]
        # unwrap again after the rotation
        for j in range(1, len(angs)):
            while angs[j] - angs[j - 1] > 180:
                angs[j] -= 360
            while angs[j] - angs[j - 1] < -180:
                angs[j] += 360
        ks = [_quant(a) for a in angs]
    runs = []                                     # [k, i0, i1]
    for i, k in enumerate(ks):
        if runs and runs[-1][0] == k:
            runs[-1][2] = i
        else:
            runs.append([k, i, i])
    if closed and len(runs) > 1 and (runs[0][0] - runs[-1][0]) % 8 == 0:
        # the last run continues the first
        k0, a0, b0 = runs[0]
        kl, al, bl = runs.pop()
        runs[0] = [k0, al - len(pts), b0]

    def support(r: int):
        k, i0, i1 = runs[r]
        if not closed and r == 0:
            return pts[0]
        if not closed and r == len(runs) - 1:
            return pts[-1]
        target = 45.0 * k
        idx = [i % len(pts) for i in range(i0, i1 + 1)]
        crossings = [j for j in range(len(idx) - 1)
                     if (angs[idx[j]] - target) * (angs[idx[j + 1]] - target) <= 0]
        if len(crossings) == 1:
            return pts[idx[crossings[0]]]
        return pts[idx[len(idx) // 2]]

    while True:
        if not closed and len(runs) < 2:
            return _dogleg(pts[0], pts[-1], pa, pb)
        if closed and len(runs) < 3:
            return None
        lines = [(DIRS[r[0] % 8], support(i)) for i, r in enumerate(runs)]
        n = len(runs)
        verts = []
        bad = None
        if closed:
            for i in range(n):
                (d0, q0), (d1, q1) = lines[i - 1], lines[i]
                h = _hit(q0, d0, q1, d1)
                if h is None:
                    bad = i
                    break
                verts.append(h[0])
            if bad is None:
                for i in range(n):
                    a, b = verts[i], verts[(i + 1) % n]
                    if dot(b - a, lines[i][0]) < 3.0:
                        bad = i
                        break
        else:
            verts.append(pts[0])
            for i in range(1, n):
                (d0, q0), (d1, q1) = lines[i - 1], lines[i]
                h = _hit(q0, d0, q1, d1)
                if h is None:
                    bad = i
                    break
                verts.append(h[0])
            if bad is None:
                verts.append(pts[-1])
                for i in range(n):
                    if dot(verts[i + 1] - verts[i], lines[i][0]) < (0.5 if i in (0, n - 1) else 3.0):
                        bad = i
                        break
        if bad is None:
            return verts
        # drop the run that does not fit and let its neighbors meet; neighbors that now run the
        # same way become one run
        del runs[bad]
        merged = True
        while merged and len(runs) > 1:
            merged = False
            for i in (range(len(runs)) if closed else range(1, len(runs))):
                if runs[i][0] % 8 == runs[i - 1][0] % 8:
                    if i == 0:
                        runs[-1][2] = runs[0][2] + len(pts)
                        del runs[0]
                    else:
                        runs[i - 1][2] = runs[i][2]
                        del runs[i]
                    merged = True
                    break


def _chains(segs: list, closed: bool):
    """Split a stroke's segments where the direction jumps or a straight line at an odd angle starts.

    Returns ([chain, ...], [kind of each split]), with kinds "corner" or "smooth".
    """
    if not segs:
        return [], []
    cuts = []
    n = len(segs)
    for i in range(n if closed else n - 1):
        a, b = segs[i], segs[(i + 1) % n]
        turn = abs(((_ang(seg_tangent(b, 0)) - _ang(seg_tangent(a, 1))) + 180) % 360 - 180)
        odd_a = len(a) == 2 and not _octi(a[1] - a[0])
        odd_b = len(b) == 2 and not _octi(b[1] - b[0])
        if turn > 10 or (len(a) == 2 and len(b) == 2):
            cuts.append((i, "corner"))
        elif odd_a or odd_b:
            cuts.append((i, "smooth"))
    if not cuts:
        return [segs], []
    if closed:
        start = cuts[0][0] + 1
        segs = segs[start:] + segs[:start]
        cuts = [((i - start) % n, kind) for i, kind in cuts]
        cuts.sort()
    chains, kinds, cur = [], [], []
    cutmap = dict(cuts)
    for i, seg in enumerate(segs):
        cur.append(seg)
        if i in cutmap and i != len(segs) - 1:
            chains.append(cur)
            kinds.append(cutmap[i])
            cur = []
    chains.append(cur)
    if closed:
        kinds.append(cutmap.get(len(segs) - 1, "corner"))
    return chains, kinds


def _pref(kind: str, host_axis: bool | None = None) -> str:
    if kind == "free":
        return "free"
    if kind == "joint":
        return "axis" if host_axis else "diag"
    if kind == "smooth":
        return "near"
    return "diag"


# --------------------------------------------------------------------------
# The effect
# --------------------------------------------------------------------------

class Piece:
    def __init__(self, pts, closed, src, ends=(None, None), hosts=((), ())):
        self.pts = pts
        self.closed = closed
        self.src = src
        self.srcs = [src, src]          # the stroke at each end (they differ after a merge)
        self.ends = list(ends)
        self.hosts = [set(hosts[0]), set(hosts[1])]


def _end_info(g, strokes, outlines, shapes_in, i, at_end):
    """Whether one end of stroke i is free or buried in another stroke: (kind, hosts, host_axis)."""
    s = strokes[i]
    segs = s.segments()
    seg = segs[-1] if at_end else segs[0]
    e = seg[-1] if at_end else seg[0]
    t = seg_tangent(seg, 1.0) if at_end else -seg_tangent(seg, 0.0)
    probe = e - t * 3.0
    hosts = []
    for j, inside in enumerate(outlines):
        if j != i and inside(probe):
            hosts.append(j)
    if not hosts and any(inside(probe) for inside in shapes_in):
        return "joint", [], None
    if not hosts:
        return "free", [], None
    # the direction of the host near the end
    best, best_d = None, 1e9
    for j in hosts:
        for hs in strokes[j].segments():
            for k in range(9):
                q = seg_point(hs, k / 8)
                dd = abs(q - e)
                if dd < best_d:
                    best, best_d = seg_tangent(hs, k / 8), dd
    host_axis = best is not None and _octi(best, 12) and _kdir(best) % 2 == 0
    return "joint", hosts, host_axis


def _stroke_poly(g, strokes, i, info, avoid=None):
    """One stroke as an octilinear polyline. ``avoid``: points on the other strokes."""
    s = strokes[i]
    segs = _segments(s)
    if not segs:
        return None
    chains, kinds = _chains(segs, s.closed)
    if s.closed and not kinds:
        pts = _runs(chains[0], True, "near", "near")
        if pts is None:
            pts = [q for seg in chains[0] for q in (seg[0],)]
        return pts, True
    out = []
    m = len(chains)
    for c, chain in enumerate(chains):
        if s.closed:
            ka = kinds[c - 1] if c > 0 else kinds[-1]
            kb = kinds[c]
            pa, pb = _pref(ka), _pref(kb)
        else:
            ka = info[0] if c == 0 else kinds[c - 1]
            kb = info[1] if c == m - 1 else kinds[c]
            pa = _pref(ka[0], ka[2]) if isinstance(ka, tuple) else _pref(ka)
            pb = _pref(kb[0], kb[2]) if isinstance(kb, tuple) else _pref(kb)
        if len(chain) == 1 and len(chain[0]) == 2:
            pts = _dogleg(chain[0][0], chain[0][1], pa, pb, avoid)
        else:
            pts = _runs(chain, False, pa, pb)
        if out and abs(out[-1] - pts[0]) < 0.5:
            pts = pts[1:]
        out.extend(pts)
    if s.closed:
        return _clean(out, True), True
    return _clean(out, False), False


def _snap(pieces, strokes_src_pieces):
    """Move every buried end along its last run until it meets the trace it was buried in."""
    for pc in pieces:
        if pc.closed:
            continue
        for end in (0, 1):
            if pc.ends[end] != "joint" or not pc.hosts[end]:
                continue
            pts = pc.pts
            e = pts[-1] if end else pts[0]
            prev = pts[-2] if end else pts[1]
            d = unit(e - prev)
            seglen = abs(e - prev)
            best = None
            for h in pc.hosts[end]:
                for hp in strokes_src_pieces.get(h, []):
                    hn = len(hp.pts)
                    for k in range(hn if hp.closed else hn - 1):
                        a, b = hp.pts[k], hp.pts[(k + 1) % hn]
                        r = _hit(e, d, a, b - a)
                        if r is None:
                            continue
                        q, s, t = r
                        if -1e-6 <= t <= 1 + 1e-6 and -seglen + 2.0 < s < W * 2.6:
                            if best is None or abs(s) < abs(best[1]):
                                best = (q, s)
            if best is not None and abs(best[1]) > 0.3:
                if end:
                    pts[-1] = best[0]
                else:
                    pts[0] = best[0]
            if best is not None:
                continue
            # no crossing: the last run lies alongside a run of the host, a few units off (the bowl
            # of 5 leaves a stem that leaned a little). Slide the run onto the host's line.
            slide = None
            for h in pc.hosts[end]:
                for hp in strokes_src_pieces.get(h, []):
                    hn = len(hp.pts)
                    for k in range(hn if hp.closed else hn - 1):
                        a, b = hp.pts[k], hp.pts[(k + 1) % hn]
                        u = unit(b - a)
                        if abs(cross(u, d)) > 1e-3:
                            continue
                        off = cross(u, e - a)
                        along = dot(e - a, u)
                        if 0.3 < abs(off) < W * 0.75 and -W < along < abs(b - a) + W:
                            if slide is None or abs(off) < abs(slide[1]):
                                slide = (a, off, u)
            if slide is None or len(pts) < 2:
                continue
            a, off, u = slide
            shift = -u * 1j * off
            if len(pts) >= 3:
                before = pts[-3] if end else pts[2]
                h2 = _hit(before, prev - before, a, u)
                new_prev = h2[0] if h2 is not None else prev + shift
            else:
                new_prev = prev + shift
            if end:
                pts[-1], pts[-2] = e + shift, new_prev
            else:
                pts[0], pts[1] = e + shift, new_prev


def _shift_run(pc, k: int, delta: complex) -> bool:
    """Move run k of a piece sideways by ``delta``; its neighbors keep their directions. False if
    that would turn a neighbor around."""
    pts = list(pc.pts)
    n = len(pts)
    a, b = pts[k], pts[(k + 1) % n]
    d = b - a
    na, nb = a + delta, b + delta
    if pc.closed or k > 0:
        p0 = pts[k - 1]
        h = _hit(p0, a - p0, na, d)
        if h is None or dot(h[0] - p0, a - p0) <= 1.0:
            return False
        na = h[0]
    if pc.closed or k + 2 < n:
        p3 = pts[(k + 2) % n]
        h = _hit(p3, b - p3, na, d)
        if h is None or dot(h[0] - p3, b - p3) <= 1.0:
            return False
        nb = h[0]
    if dot(nb - na, d) <= 1.0:
        return False
    pts[k], pts[(k + 1) % n] = na, nb
    pc.pts = pts
    return True


def _align(pieces):
    """Two parallel runs of different traces a few units apart print as one thick trace (the stems
    of a and e in æ). Move the shorter one onto the line of the longer."""
    for _ in range(3):
        moved = False
        runs = []
        for pc in pieces:
            n = len(pc.pts)
            for k in range(n if pc.closed else n - 1):
                runs.append((pc, k))
        for i, (p1, k1) in enumerate(runs):
            for p2, k2 in runs[i + 1:]:
                if p1 is p2:
                    continue
                n1, n2 = len(p1.pts), len(p2.pts)
                a, b = p1.pts[k1], p1.pts[(k1 + 1) % n1]
                c, d = p2.pts[k2], p2.pts[(k2 + 1) % n2]
                u = unit(b - a)
                if abs(cross(u, unit(d - c))) > 1e-3:
                    continue
                off = cross(u, c - a)
                if not 0.5 < abs(off) < W * 0.6:
                    continue
                t0, t1 = sorted((dot(c - a, u), dot(d - a, u)))
                if min(abs(b - a), t1) - max(0.0, t0) < W:
                    continue
                if abs(d - c) <= abs(b - a):
                    ok = _shift_run(p2, k2, -u * 1j * off)
                else:
                    ok = _shift_run(p1, k1, u * 1j * off)
                moved = moved or ok
        if not moved:
            break


def _merge(pieces):
    """Join two open pieces that meet end to end (an L joint) into one."""
    changed = True
    while changed:
        changed = False
        for a in pieces:
            if a.closed:
                continue
            for b in pieces:
                if b is a or b.closed:
                    continue
                for ea in (0, 1):
                    for eb in (0, 1):
                        if a.ends[ea] != "joint" or b.ends[eb] != "joint":
                            continue
                        pa = a.pts[-1] if ea else a.pts[0]
                        pb = b.pts[-1] if eb else b.pts[0]
                        if abs(pa - pb) > 1.5:
                            continue
                        # the two runs must turn, not overlap
                        da = unit(pa - (a.pts[-2] if ea else a.pts[1]))
                        db = unit(pb - (b.pts[-2] if eb else b.pts[1]))
                        if dot(da, db) > 0.2:
                            continue
                        apts = a.pts if ea else a.pts[::-1]
                        bpts = b.pts if not eb else b.pts[::-1]
                        a.pts = _clean(apts + bpts[1:], False)
                        a_end0 = a.ends[1 - ea]
                        a_host0 = a.hosts[1 - ea]
                        b_end1 = b.ends[1 - eb]
                        b_host1 = b.hosts[1 - eb]
                        a.ends = [a_end0, b_end1]
                        a.hosts = [a_host0, b_host1]
                        a.srcs = [a.srcs[1 - ea], b.srcs[1 - eb]]
                        pieces.remove(b)
                        changed = True
                        break
                    if changed:
                        break
                if changed:
                    break
            if changed:
                break


def _chamfer(pts: list, closed: bool) -> list:
    """Cut every square corner between level and upright runs at 45 degrees, and widen short chamfers."""
    n = len(pts)
    if n < 3:
        return pts
    out = list(pts)

    def axis(v):
        return _octi(v, 1.0) and _kdir(v) % 2 == 0

    i = 0 if closed else 1
    while True:
        n = len(out)
        if n < 3 or i >= (n if closed else n - 1):
            break
        a, b, c = out[i - 1], out[i], out[(i + 1) % n]
        d1, d2 = b - a, c - b
        if axis(d1) and axis(d2) and abs(dot(unit(d1), unit(d2))) < 0.01:
            cut = min(CHAMFER, abs(d1) * 0.5, abs(d2) * 0.5)
            p, q = b - unit(d1) * cut, b + unit(d2) * cut
            out[i:i + 1] = [p, q]
            i += 2
            continue
        # a short 45 degree run between a level and an upright one: make it as long as a chamfer
        if (i + 2 <= (n if closed else n - 1)) and axis(d1) and not axis(d2) and _octi(d2):
            c2 = out[(i + 2) % n]
            d3 = c2 - c
            if axis(d3) and abs(dot(unit(d1), unit(d3))) < 0.01 and abs(d2) * SQ < CHAMFER - 1:
                h = _hit(a, unit(d1), c2, unit(d3))
                if h is not None:
                    x = h[0]
                    cut = min(CHAMFER, abs(x - a) * 0.5, abs(c2 - x) * 0.5)
                    if cut > abs(d2) * SQ:
                        out[i] = x - unit(d1) * cut
                        out[(i + 1) % n] = x + unit(d3) * cut
        i += 1
    return _clean(out, closed)


def _walk_back(pts: list, dist: float) -> complex:
    """The point ``dist`` back from the end of a polyline (its last point)."""
    for k in range(len(pts) - 1, 0, -1):
        a, b = pts[k - 1], pts[k]
        L = abs(b - a)
        if dist <= L:
            return b + (a - b) * (dist / L if L else 0)
        dist -= L
    return pts[0]


def _trim(pts: list, p: complex) -> list:
    """The polyline cut at point p (which lies on it), keeping the start."""
    best, best_k = 1e9, len(pts) - 1
    for k in range(len(pts) - 1, 0, -1):
        dd = _seg_dist(p, pts[k - 1], pts[k])
        if dd < best - 1e-6:
            best, best_k = dd, k
        if dd < 0.5:
            break
    return pts[:best_k] + [p]


def _length(pts):
    return sum(abs(pts[k + 1] - pts[k]) for k in range(len(pts) - 1))


def build(g, ink):
    """The copper of one glyph: (traces, pads, vias, pours), as polylines and centers."""
    strokes = list(g.strokes)
    outlines = []
    for s in strokes:
        pen = FixedPen(s.fixed) if s.fixed is not None else g.pen
        outlines.append(effects.inside(expand(s, pen, g.p.roundness)))
    dots, pours = [], []
    shapes_in = []
    for kind, contour, radii in g.shapes:
        b = contour_bounds([contour])
        if b is None:
            continue
        shapes_in.append(effects.inside([contour]))
        if kind == "dot":
            c = complex((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            if -5 < b[1] < 30:
                # a dot on the baseline (a period): the pad is larger, so it rises to stand there too
                c = complex(c.real, max(c.imag, b[1] + PAD - LIP))
            dots.append(c)
        else:
            pours.append(_pour(contour))

    # points along every stroke, so that a slash can keep clear of the others
    along = []
    for s in strokes:
        qs = []
        for seg in s.segments():
            n = max(1, int(seg_length(seg) / 12))
            qs += [seg_point(seg, k / n) for k in range(n + 1)]
        along.append(qs)

    pieces = []
    by_src = {}
    for i, s in enumerate(strokes):
        if s.closed:
            info = (None, None)
        else:
            info = (_end_info(g, strokes, outlines, shapes_in, i, False),
                    _end_info(g, strokes, outlines, shapes_in, i, True))
        avoid = [q for j, qs in enumerate(along) if j != i for q in qs] + [d for d in dots]
        res = _stroke_poly(g, strokes, i, info, avoid)
        if res is None:
            continue
        pts, closed = res
        if len(pts) < 2:
            continue
        if closed:
            pc = Piece(pts, True, i)
        else:
            pc = Piece(pts, False, i, (info[0][0], info[1][0]), (info[0][1], info[1][1]))
        pieces.append(pc)
        by_src.setdefault(i, []).append(pc)

    _snap(pieces, by_src)
    _merge(pieces)
    _align(pieces)
    for pc in pieces:
        pc.pts = _chamfer(pc.pts, pc.closed)

    # A pad is wider than the dot it replaces. Two that would touch (the dieresis) move apart, and one
    # that would lie on a trace it does not belong to (the caron of ď ľ Ľ beside the stem) moves away
    # from it, with its tail.
    for i in range(len(dots)):
        for j in range(i + 1, len(dots)):
            v = dots[j] - dots[i]
            short = 2 * PAD + 14 - abs(v)
            if short > 0 and abs(v) > 1e-6:
                dots[i] -= unit(v) * short / 2
                dots[j] += unit(v) * short / 2
    for i, c in enumerate(dots):
        own = [pc for pc in pieces if not pc.closed and min(abs(pc.pts[0] - c), abs(pc.pts[-1] - c)) < PAD]
        for _ in range(3):
            worst, push = 0.0, 0j
            for pc in pieces:
                if pc in own:
                    continue
                n = len(pc.pts)
                for k in range(n if pc.closed else n - 1):
                    a, b = pc.pts[k], pc.pts[(k + 1) % n]
                    ab = b - a
                    t = max(0.0, min(1.0, dot(c - a, ab) / max(dot(ab, ab), 1e-9)))
                    q = a + ab * t
                    need = PAD + W / 2 + 10 - abs(c - q)
                    if need > worst and abs(c - q) > 1e-6:
                        worst, push = need, unit(c - q) * need
            if worst <= 0.5:
                break
            c = c + push
            for pc in own:
                pc.pts = [q + push for q in pc.pts]
        dots[i] = c

    # pads at the free ends: first where each would go
    cands = []                                   # [piece, end, center, outward direction, keep]
    bounds = {}
    for pc in pieces:
        if pc.closed:
            continue
        for end in (0, 1):
            if pc.ends[end] != "free":
                continue
            pts = pc.pts if end else pc.pts[::-1]
            e = pts[-1]
            near = [o for o in pieces if o is not pc and _poly_dist(e, o.pts, o.closed) < W * 0.5]
            if near:
                # the end lies on another trace: no pad. If that trace starts or bends on this
                # one's line just short of the end, stop there, so no stub shows past the joint.
                a = pts[-2]
                u = unit(e - a)
                cut = None
                for o in near:
                    for v in o.pts:
                        along = dot(v - a, u)
                        if abs(cross(u, v - a)) < 1.5 and 1.0 < along < abs(e - a) - 0.5:
                            if cut is None or along < dot(cut - a, u):
                                cut = a + u * along
                if cut is not None:
                    pts = pts[:-1] + [cut]
                    pc.pts = pts if end else pts[::-1]
                continue
            src = pc.srcs[end]
            if src not in bounds:
                s = strokes[src]
                bounds[src] = contour_bounds(expand(s, FixedPen(s.fixed) if s.fixed is not None else g.pen,
                                                    g.p.roundness))
            x0, y0, x1, y1 = bounds[src]
            # move the pad back along the trace until it stays within the stroke's own extent
            u = unit(pts[-1] - pts[-2])
            k = _kdir(u)
            far = max(dot(complex(x, y), DIRS[k]) for x in (x0, x1) for y in (y0, y1))
            inset = max(0.0, dot(e, DIRS[k]) - (far + LIP - PAD))
            inset = min(inset, max(0.0, _length(pts) - 1.0))
            cands.append([pc, end, _walk_back(pts, inset), u, True])

    # then which of them to drop
    ahead = list(dots)
    for i in range(len(dots)):
        for j in range(i + 1, len(dots)):
            if abs(dots[i].imag - dots[j].imag) < 5 and abs(dots[i] - dots[j]) < 4 * PAD:
                ahead.append((dots[i] + dots[j]) / 2)       # the middle of a dieresis (ï)
    for c in cands:
        pc, end, q, u, _ = c
        # a dot straight ahead (i, j, !, ?, ï) is the pad of this stroke
        for d in ahead:
            v = d - q
            if dot(v, u) > 0 and abs(cross(v, u)) < PAD * 0.5 and abs(v) < PAD * 6:
                c[4] = False
        # a short spur that leaves another trace: its pad would sit on the joint
        if pc.ends[1 - end] == "joint" and _length(pc.pts) < PAD * 1.6:
            c[4] = False
        # the straight quotes: a pad on top and a short tail, like the curly ones
        other = pc.pts[0] if end else pc.pts[-1]
        tag = strokes[pc.srcs[end]].tag
        if tag == "tick" and q.imag < other.imag:
            c[4] = False
        if tag == "bare":
            c[4] = False
        # an accent that bends (circumflex, caron, breve, tilde, cedilla): pads at its ends made it
        # wider than an i and ran into the next letter, so it stays a plain trace. A straight one
        # (acute, grave) keeps a pad at its upper end.
        if tag == "mark":
            segs = _segments(strokes[pc.srcs[end]])
            if len(segs) > 1 or len(segs[0]) == 4:
                c[4] = False
        # a short bar across another trace (t, f, the stroke of ł): pads at its ends would crowd the
        # stem, so its ends stay plain
        if pc.ends[1 - end] == "free" and _length(pc.pts) < CROSSBAR and _crosses(pc, pieces):
            c[4] = False
    for i, a in enumerate(cands):
        for b in cands[i + 1:]:
            if a[0] is b[0] and a[4] and b[4] and abs(a[2] - b[2]) < 2 * PAD + W * 0.5:
                # a short stroke free at both ends (an accent, a quote): one pad, at the upper end
                lower = a if (a[2].imag, a[2].real) < (b[2].imag, b[2].real) else b
                lower[4] = False
    # pads that would touch (the arms of an asterisk) all go: the ends stay plain
    crowded = [a for a in cands if a[4] and (
        any(b is not a and b[4] and abs(a[2] - b[2]) < 2 * PAD + 6 for b in cands)
        or any(abs(a[2] - d) < 2 * PAD + 20 for d in dots))]
    for a in crowded:
        a[4] = False

    pads = []
    for pc, end, q, u, keep in cands:
        pts = pc.pts if end else pc.pts[::-1]
        if keep:
            pads.append(q)
            cut = _trim(pts, q)
        else:
            # a bare end: pull it in so that its round end stops where the stroke ended
            back = min(W * 0.5, max(0.0, _length(pts) - 1.0))
            cut = _trim(pts, _walk_back(pts, back)) if back > 0.5 else pts
        pc.pts = cut if end else cut[::-1]
    pads += dots
    return pieces, pads, _vias(pieces, pads), pours


def _pour(contour: list) -> list:
    """A filled shape (a copper pour: the bowl of the pilcrow, a black circle or heart) with its curves
    redrawn as runs at 0, 45 and 90 degrees. Its straight edges stay as they are."""
    segs = [seg for seg in contour if seg_length(seg) > 0.5]
    if not any(len(seg) == 4 for seg in segs):
        return contour
    chains, kinds = _chains(segs, True)
    if not kinds:
        pts = _runs(chains[0], True, "near", "near")
    else:
        pts = []
        for chain in chains:
            run = [chain[0][0], chain[0][1]] if len(chain) == 1 and len(chain[0]) == 2 else \
                _runs(chain, False, "near", "near")
            if pts and abs(pts[-1] - run[0]) < 0.5:
                run = run[1:]
            pts.extend(run)
    if not pts or len(pts) < 3:
        return contour
    pts = _clean(pts, True)
    out = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    return out if contour_area(out) < 0 else reverse_contour(out)


def _crosses(pc, pieces) -> bool:
    """True if piece ``pc`` crosses another trace away from its own ends."""
    n = len(pc.pts)
    for o in pieces:
        if o is pc:
            continue
        m = len(o.pts)
        for i in range(n - 1):
            a, b = pc.pts[i], pc.pts[i + 1]
            for k in range(m if o.closed else m - 1):
                c, d = o.pts[k], o.pts[(k + 1) % m]
                h = _hit(a, b - a, c, d - c)
                if h is None:
                    continue
                q, s, t = h
                if not (0 <= s <= 1 and 0 <= t <= 1) or min(abs(q - pc.pts[0]), abs(q - pc.pts[-1])) <= W:
                    continue
                if o.closed or min(abs(q - o.pts[0]), abs(q - o.pts[-1])) > W:
                    return True               # a crossing, not the other trace ending on this one
    return False


def _vias(pieces, pads) -> list:
    """At most ``MAX_VIAS`` vias, at T joints: where a trace ends on the middle of another, away from pads.

    Of those, the one nearest the middle of the glyph, so a word gets a few and not one on every bar.
    """
    cands = []
    for pc in pieces:
        if pc.closed:
            continue
        for end in (0, 1):
            if pc.ends[end] != "joint" or len(pc.pts) < 2:
                continue
            e = pc.pts[-1] if end else pc.pts[0]
            d = unit(e - (pc.pts[-2] if end else pc.pts[1]))
            for o in pieces:
                if o is pc:
                    continue
                n = len(o.pts)
                for k in range(n if o.closed else n - 1):
                    a, b = o.pts[k], o.pts[(k + 1) % n]
                    if _seg_dist(e, a, b) > 1.5 or abs(cross(unit(b - a), d)) < 0.5:
                        continue
                    if min(abs(e - a), abs(e - b)) < W and not (o.closed or 0 < k < n - 2):
                        continue
                    if not o.closed and min(abs(e - o.pts[0]), abs(e - o.pts[-1])) < W * 1.5:
                        continue
                    cands.append(e)
    cands = [c for c in cands if all(abs(c - p) > PAD + VIA + 18 for p in pads)]
    if not cands or not MAX_VIAS:
        return []
    xs = [q.real for pc in pieces for q in pc.pts]
    ys = [q.imag for pc in pieces for q in pc.pts]
    mid = complex((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    cands.sort(key=lambda c: abs(c - mid))
    out = []
    for c in cands:
        if all(abs(c - v) > 4 * VIA for v in out):
            out.append(c)
        if len(out) >= MAX_VIAS:
            break
    return out


def _layers(pieces, pads, vias, pours):
    """The color layers, bottom first, and the one-color copper with its holes."""
    trace = _band(pieces, W)
    halo = _band(pieces, W + 2 * HALO)
    pad_c = [[_disc(p, PAD)] for p in pads]
    via_c = [[_disc(p, VIA)] for p in vias]
    pour_c = [[c] for c in pours]
    holes = [_disc(p, HOLE) for p in pads] + [_disc(p, VIA_HOLE) for p in vias]
    halo_parts = [halo] + [[_disc(p, PAD + HALO)] for p in pads] + [[_disc(p, VIA + HALO)] for p in vias]
    if pours:
        halo_parts.append(dilate(pours, HALO))
    layers = [("mask", _merged(halo_parts))]
    if pads:
        layers.append(("gap", _merged([[_disc(p, PAD + GAP)] for p in pads])))
    if trace:
        layers.append(("trace", trace))
    if SHINE and pieces:
        layers.append(("shine", _band(pieces, SHINE)))
    if via_c:
        layers.append(("via", _merged(via_c)))
    if pad_c or pours:
        layers.append(("pad", _merged(pad_c + pour_c)))
    if holes:
        layers.append(("hole", union(holes)))
    copper = _merged([trace] + via_c + pad_c + pour_c)
    return layers, (difference(copper, holes) if holes else copper)


#: Sidebearings for the sides a recipe declares diagonal ("d", 0.16 of a stem's) or thin ("t", 0.3).
#: As traces those sides end in upright runs with pads (V, A, X, K, R, k, v, x), so they get most of a
#: straight side, and kerning closes what the shapes allow. With the stock values the pads of
#: neighbors (the leg of R and the foot of x) touched, and kerning may only push apart a little.
SIDES = {"d": 0.62, "t": 0.62}


def _respace(g):
    if g._frame is not None:
        width, left, right = g._frame
        g._frame = (width, SIDES.get(left, left) if isinstance(left, str) else left,
                    SIDES.get(right, right) if isinstance(right, str) else right)


def traces(recipes, names=None):
    """Letters as copper traces on a board. Keys, bottom first: mask, gap, trace, shine, via, pad, hole."""

    def effect(g, ink):
        layers, copper = _layers(*build(g, ink))
        g.layers = layers
        effects.redraw(g, copper)
        _respace(g)

    return effects.wrapped(recipes, effect, names=names)


def plain(recipes, names=None):
    """The same traces in one color: copper with the holes drilled through."""

    def effect(g, ink):
        layers, copper = _layers(*build(g, ink))
        effects.redraw(g, copper)
        _respace(g)

    return effects.wrapped(recipes, effect, names=names)


# --------------------------------------------------------------------------
# Palettes: each is drawn for one ground, listed in GROUNDS
# --------------------------------------------------------------------------

# Green: gold traces on the classic green board. Black: tin-silver traces on a black board. Blue: gold
# on a blue board. Paper: copper on a white page, with a pale green mask and the holes left white.
PALETTES = {
    "Green": {"mask": "#247442", "gap": "#0C2E1B", "trace": "#D19A3A", "shine": "#E9BE62", "via": "#E3B556",
              "pad": "#F3D47C", "hole": "#0B2416"},
    "Black": {"mask": "#2E3236", "gap": "#0B0C0D", "trace": "#A9AFB6", "shine": "#CDD2D7", "via": "#C3C8CE",
              "pad": "#E8EBEE", "hole": "#08090A"},
    "Blue": {"mask": "#2259A6", "gap": "#081D45", "trace": "#DCA845", "shine": "#F0C96E", "via": "#E8BE5E",
             "pad": "#F7DC8F", "hole": "#07183A"},
    "Paper": {"mask": "#DCEADF", "gap": "#FFFFFF", "trace": "#B5651D", "shine": "#C07429", "via": "#A65A18",
              "pad": "#8E4A12", "hole": "#FFFFFF"},
}

GROUNDS = {"Green": "#0F3D24", "Black": "#141517", "Blue": "#0C2D63", "Paper": "#FFFFFF"}
