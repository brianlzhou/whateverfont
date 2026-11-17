"""The `contour_map` effect and its palettes, for the Knollrise families (see font.py).

Each letter is a hill on a topographic map. The stroke is the hill, its edge is the foot of the hill, and
the middle of the stroke is the ridge. Contour lines are the outline of the letter shrunk by growing
distances, so they run parallel to the edge, ring inside ring. They lie close together near the edge,
where the slope is steep, and wider apart toward the ridge. Where strokes meet, the letter is wider, so
the hill is higher there and a few more small rings close around the top.

Layers, bottom layer first: land (the letter, a flat tint), line (the thin contour lines), index (the
thicker index contours, the first of which is the edge of the letter), summit (one small triangle at the
highest point of the letter).
"""

import math

import pathops

from whateverfont import effects, outline
from whateverfont.geom import contour_area, contour_bounds, flatten_contour
from whateverfont.outline import circle, depths, difference, dilate, from_path, to_path, union

#: The contour lines, from the edge in: (distance from the edge to the outer side of the line, line width).
#: The line at the edge is the first, and every fifth line from it is an index contour.
RINGS = ((0, 9), (15, 5), (27, 5), (41, 5), (57, 5), (84, 9), (104, 5), (124, 5), (144, 5), (164, 5), (184, 9))
EVERY = 5


def solid(contours):
    """The area of ink of some contours (holes subtract)."""
    return -sum(contour_area(c) for c in contours)


def pieces(contours):
    """The contours grouped into pieces: each outside with the holes directly inside it."""
    if not contours:
        return []
    level = depths(contours)
    outs = [i for i, d in enumerate(level) if d % 2 == 0]
    groups = {i: [contours[i]] for i in outs}
    for i, d in enumerate(level):
        if d % 2 == 0:
            continue
        p = contours[i][0][0]
        for j in outs:
            if level[j] == d - 1 and effects.inside([contours[j]])(p):
                groups[j].append(contours[i])
                break
    return list(groups.values())


class Edge:
    """The outline of a letter, flattened, to measure how far a point lies from it."""

    def __init__(self, ink):
        self.segs = []
        for c in ink:
            pts = flatten_contour(c, 1.5)
            self.segs += [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        self.inside = effects.inside(ink)

    def distance(self, q):
        best = float("inf")
        for a, b in self.segs:
            ab = b - a
            den = ab.real * ab.real + ab.imag * ab.imag
            t = 0.0 if den < 1e-9 else max(0.0, min(1.0, ((q - a).real * ab.real + (q - a).imag * ab.imag) / den))
            d = abs(q - a - ab * t)
            if d < best:
                best = d
        return best

    def depth_ok(self, contour, d):
        """Whether ``contour`` lies about ``d`` inside the letter, as an outline shrunk by ``d`` must."""
        pts = flatten_contour(contour, 2.0)
        for q in pts[:: max(1, len(pts) // 6)]:
            if not self.inside(q) or self.distance(q) < d - max(2.0, 0.08 * d):
                return False
        return True


def shrink(ink, d, edge=None, retry=True):
    """The letter shrunk by ``d`` on every side, or [] if nothing is left.

    Skia's stroker does not always give an empty result when ``d`` is wider than the stroke: it can
    leave scraps far from the middle (a shrunk dot left a piece the size of a stem at 300 units). So
    every piece is checked: it must lie ``d`` inside the letter.
    """
    if d <= 0:
        return ink
    edge = edge or Edge(ink)
    best, best_area = [], -1.0
    for nudge in (0.0, 0.31, 0.73, 1.17):
        # Skia now and then cannot merge the band it shrinks with (it says so in outline.trouble, and
        # the build would name the glyph), or leaves a spur that runs out to the edge (the top corner
        # of the Cyrillic El). The band is only a tool here, so try a hair deeper instead.
        seen = len(outline.trouble)
        try:
            raw = effects.erode(ink, d + nudge)
        except Exception:
            raw = []
        clean = len(outline.trouble) == seen
        del outline.trouble[seen:]
        # empty holes and spurs with no area: merging the result again removes them
        raw = [c for c in raw if len(c) >= 2 and (contour_area(c) < -0.5 or contour_area(c) > 20)]
        if raw:
            seen = len(outline.trouble)
            merged = union(raw)
            if len(outline.trouble) == seen:
                raw = [c for c in merged if contour_area(c) < -0.5 or contour_area(c) > 20]
            del outline.trouble[seen:]
        if not raw:
            if clean:
                return []
            continue
        out, whole = [], True
        for piece in pieces(raw):
            if all(edge.depth_ok(c, d) for c in piece if contour_area(c) < 0 or contour_area(c) > 200):
                out += piece
            elif solid(piece) > 400:
                whole = False            # a real piece with a scrap on it: try again
        if (clean and whole) or not retry:
            return out
        if solid(out) > best_area:
            best, best_area = out, solid(out)
    return best


def shallow(contours, thin):
    """The pieces of ``contours`` that are thin: more than a hair, but no disc of radius ``thin`` fits."""
    return [p for p in pieces(contours) if solid(p) > 6 and shrink(p, 0.6) and not shrink(p, thin)]


def counters(contours):
    return sum(1 for c in contours if contour_area(c) > 50)


def soften(ink, fill=200.0, dent=10.0, trim=14.0, point=4.5):
    """The letter with its shallow dents filled and its sharp points rounded off.

    At this weight the round end of a stem rises past the bar that joins it, which leaves a nub and a
    shallow dent at the top and bottom corners of B D E F P R, and the cut end of a diagonal leaves a
    sharp point at the top of N. Every ring would repeat them.

    Growing and shrinking by ``fill`` fills the concave places, and only the thin fills are kept: no
    disc of radius ``dent`` fits in them, and they must not close a counter or an aperture. A square
    inside corner keeps its shape; an acute one (the crotch of v, k, x) is rounded a little.
    Shrinking and growing by ``trim`` cuts the convex points, and only cuts in which no disc of
    radius ``point`` fits are kept.
    """
    # Each fill and each cut shares an edge with the letter. Merging along a shared edge with
    # `outline.union` leaves Skia hairline scraps that later spoil the rings (the Cyrillic El lost all
    # its rings), so a fill is merged with one boolean operation and kept only if the areas add up.
    seen = len(outline.trouble)
    try:
        holes = counters(ink)
        out = ink
        closed = shrink(dilate(ink, fill), fill)
        for piece in (shallow(difference(closed, ink), dent) if closed else []):
            merged = [c for c in from_path(pathops.op(to_path(out), to_path(piece), pathops.PathOp.UNION,
                                                      fix_winding=True, clockwise=True))
                      if abs(contour_area(c)) > 0.5]
            if counters(merged) == holes and abs(solid(merged) - solid(out) - solid(piece)) < 0.2 * solid(piece):
                out = merged
        core = shrink(out, trim)
        opened = [c for c in dilate(core, trim) if abs(contour_area(c)) > 0.5] if core else []
        cut = [c for p in shallow(difference(out, opened), point) for c in p] if opened else []
        out = difference(out, cut) if cut else out
    except Exception:
        out = None
    if len(outline.trouble) > seen:
        del outline.trouble[seen:]
        return ink
    if not out or counters(out) != holes or abs(solid(out) - solid(ink)) > 0.03 * solid(ink):
        return ink
    return out


def split_marks(g, ink, gap=30.0):
    """The ink with a gap between the two strokes of a double acute (ő ű Ő Ű).

    At this weight the engine draws the two strokes so close that they touch, and the rings would
    run round both as one blob. A cut parallel to the strokes, halfway between them, keeps them two.
    """
    if "doubleacute" not in g.name and "hungarumlaut" not in g.name:
        return ink
    marks = [s for s in g.strokes if s.tag == "mark" and len(s.nodes) >= 2]
    if len(marks) != 2:
        return ink
    a, b = ((s.nodes[0].p + s.nodes[-1].p) / 2 for s in marks)
    run = marks[0].nodes[-1].p - marks[0].nodes[0].p
    if abs(run) < 1:
        return ink
    d = run / abs(run)
    side = d * 1j
    mid, reach = (a + b) / 2, abs(run) * 1.1
    pts = [mid - d * reach - side * gap / 2, mid + d * reach - side * gap / 2,
           mid + d * reach + side * gap / 2, mid - d * reach + side * gap / 2]
    cut = [(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    # Cut the mark only, never the letter under it: the mark is the piece that starts near the
    # foot of its strokes.
    low = min(node.p.imag for s in marks for node in s.nodes) - 80
    mark, rest = [], []
    for p in pieces(ink):
        (mark if contour_bounds(p)[1] > low else rest).extend(p)
    if not mark:
        return ink
    mark = difference(mark, [cut])
    core = shrink(mark, 10.0)                # round the corners that the cut leaves
    if core:
        mark = [c for c in dilate(core, 10.0) if abs(contour_area(c)) > 0.5]
    return rest + mark


def triangle(p, r):
    """A clockwise triangle pointing up, its center at ``p``, its corners ``r`` from the center."""
    pts = [p + r * complex(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (90, -30, -150)]
    return [(pts[i], pts[(i + 1) % 3]) for i in range(3)]


def summit_point(ink, start, edge, tolerance=2.0, reach=400.0):
    """The highest point of the hill: the deepest point inside the letter, and its depth.

    None if the letter is not ``start`` deep anywhere.
    """
    lo, hi = start, reach
    best = shrink(ink, lo, edge)
    if not best:
        return None
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        s = shrink(ink, mid, edge, retry=False)
        if s:
            lo, best = mid, s
        else:
            hi = mid
    top = max(pieces(best), key=solid)
    pts = [q for c in top for q in flatten_contour(c, 1.0)]
    mid = sum(pts) / len(pts)
    if not effects.inside(top)(mid):
        mid = min(pts, key=lambda q: abs(q - mid))      # a thin curved ridge: the nearest point on it
    return mid, lo


def level(ink, d, edge, smooth):
    """The letter shrunk by ``d``, with its sharp points rounded off.

    Where a ring pinches off between two strokes, or closes around the top of a junction, the shrunk
    outline has sharp points. Shrinking ``smooth`` more and growing back by ``smooth`` rounds every
    point to that radius and drops every part narrower than twice that.
    """
    if smooth <= 0:
        return shrink(ink, d, edge)
    core = shrink(ink, d + smooth, edge)
    if not core:
        return []
    return [c for c in dilate(core, smooth) if abs(contour_area(c)) > 0.5]


def rings(ink, edge, scale=1.0, least=2500.0, smooth=12.0):
    """The contour lines of one letter: a list of (key, piece), one piece for each closed line."""
    out = []
    for k, (d, w) in enumerate(RINGS):
        d, w = d * scale, w * scale
        key = "index" if k % EVERY == 0 else "line"
        if k == 0:
            band = difference(ink, shrink(ink, w, edge))
        else:
            middle = [c for p in pieces(level(ink, d + w / 2, edge, smooth)) if solid(p) >= least * scale * scale
                      for c in p]
            if not middle:
                break
            band = effects.band(middle, w)
        out += [(key, p) for p in pieces(band)]
    return out


def contour_map(recipes, scale=1.0, summit=18.0, clear=6.0, least=2500.0, smooth=12.0, soft=True, color=True,
                names=None):
    """Letters drawn as hills on a contour map. Keys: land, line, index, summit.

    ``scale`` multiplies every distance of `RINGS`. ``summit`` is the distance from the center of the
    summit triangle to its corners (0 for none), and ``clear`` the white kept between it and any line.
    ``least`` is the smallest piece, in square units, that still gets a ring, and ``smooth`` the
    radius to which the sharp points of a ring are rounded. ``soft`` smooths the small dents and
    points of the letter itself first (see `soften`). With ``color=False`` the letter is the lines
    and the summit alone, in one color, with no layers.
    """

    def effect(g, ink):
        if contour_bounds(ink) is None:
            return
        if soft:
            ink = soften(ink)
        ink = split_marks(g, ink)
        edge = Edge(ink)
        lines = rings(ink, edge, scale, least, smooth)
        top = []
        if summit > 0:
            # Only where the mark clears the last line of a plain stem (line 5 ends 62 units in).
            found = summit_point(ink, (RINGS[4][0] + RINGS[4][1]) * scale + summit + clear, edge)
            if found is not None:
                p, _ = found
                top = [triangle(p, summit)]
                reach = summit + clear
                keep_out = [circle(p.real, p.imag, reach)]
                kept = []
                for key, piece in lines:
                    x0, y0, x1, y1 = contour_bounds(piece)
                    near = x0 - reach < p.real < x1 + reach and y0 - reach < p.imag < y1 + reach
                    left = difference(piece, keep_out) if near else piece
                    if not near or abs(solid(left) - solid(piece)) < 1.0:
                        kept.append((key, piece))
                    elif max(x1 - x0, y1 - y0) < 5 * reach:
                        continue                    # a small top ring: the summit mark takes its place
                    else:
                        rest = [c for p2 in pieces(left) if solid(p2) > 40 for c in p2]
                        if rest:
                            kept.append((key, rest))
                lines = kept
        if not color:
            # One color: the lines and the summit are the letter, and the paper shows between them.
            effects.redraw(g, union([c for _, piece in lines for c in piece] + top))
            return
        layers = [("land", ink)]
        for key in ("line", "index"):
            part = [c for k, piece in lines if k == key for c in piece]
            if part:
                layers.append((key, part))
        if top:
            layers.append(("summit", top))
        g.layers = layers

    return effects.wrapped(recipes, effect, names=names)


def palette(land, line, index, summit):
    return {"land": land, "line": line, "index": index, "summit": summit}


#: Each palette is a kind of map. GROUNDS holds the paper each one is printed on.
PALETTES = {
    "Trail": palette("#C6DA9E", "#9A6436", "#6B3E1C", "#C2392A"),
    "Sea Chart": palette("#B5D5E6", "#3C78A8", "#1F4F7C", "#1B3F63"),
    "Night": palette("#34475A", "#AFC0B0", "#E6DEC2", "#F0B860"),
    "Desert": palette("#E8BE8E", "#A4532E", "#7A351A", "#4A3324"),
}

GROUNDS = {"Trail": "#F4EEDC", "Sea Chart": "#E6F0F2", "Night": "#1A222B", "Desert": "#F7EBDA"}
