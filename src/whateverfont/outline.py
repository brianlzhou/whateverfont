"""Outline utilities: boolean union, pen output, and a small rasterizer.

Contours use the conventions of :mod:`whateverfont.geom`.
"""

from __future__ import annotations

import pathops
from PIL import Image, ImageDraw

from .geom import (
    apply_affine,
    contour_area,
    contour_bounds,
    flatten_contour,
    reverse_contour,
    transform_contour,
    xy,
)


# --------------------------------------------------------------------------
# Pens
# --------------------------------------------------------------------------

def draw_contours(contours, pen) -> None:
    """Draw contours into any fontTools segment pen."""
    for c in contours:
        if not c:
            continue
        pen.moveTo(xy(c[0][0]))
        for seg in c:
            if len(seg) == 2:
                pen.lineTo(xy(seg[1]))
            else:
                pen.curveTo(xy(seg[1]), xy(seg[2]), xy(seg[3]))
        pen.closePath()


class ContourPen:
    """A minimal segment pen that records contours in whateverfont's format."""

    def __init__(self):
        self.contours: list[list] = []
        self._cur: list | None = None
        self._pt: complex | None = None
        self._start: complex | None = None

    def moveTo(self, p):
        self._close()
        self._cur = []
        self._pt = self._start = complex(*p)

    def lineTo(self, p):
        q = complex(*p)
        if abs(q - self._pt) > 1e-9:
            self._cur.append((self._pt, q))
        self._pt = q

    def curveTo(self, *pts):
        if len(pts) != 3:
            raise ValueError("only single cubic segments are supported")
        a, b, c = (complex(*p) for p in pts)
        self._cur.append((self._pt, a, b, c))
        self._pt = c

    def qCurveTo(self, *pts):
        if pts and pts[-1] is None:
            # A closed contour with no on-curve point (a TrueType circle, or a
            # stroked path from skia). It starts halfway between the last and
            # the first off-curve point.
            offs = [complex(*p) for p in pts[:-1]]
            start = (offs[-1] + offs[0]) / 2
            self.moveTo((start.real, start.imag))
            self.qCurveTo(*[(q.real, q.imag) for q in offs], (start.real, start.imag))
            self._close()
            return
        pts = [complex(*p) for p in pts if p is not None]
        # Expand TrueType implied on-curve points, then raise each quad to a cubic.
        for i, ctrl in enumerate(pts[:-1]):
            end = pts[i + 1] if i == len(pts) - 2 else (ctrl + pts[i + 1]) / 2
            p0 = self._pt
            self._cur.append((p0, p0 + (ctrl - p0) * 2 / 3, end + (ctrl - end) * 2 / 3, end))
            self._pt = end
        if len(pts) == 1:
            self.lineTo((pts[0].real, pts[0].imag))

    def closePath(self):
        self._close()

    def endPath(self):
        self._close()

    def addComponent(self, *args, **kwargs):  # pragma: no cover - not used
        raise NotImplementedError("decompose components before recording")

    def _close(self):
        if self._cur is not None:
            if self._pt is not None and abs(self._pt - self._start) > 1e-9:
                self._cur.append((self._pt, self._start))
            if self._cur:
                self.contours.append(self._cur)
        self._cur = None


# --------------------------------------------------------------------------
# Boolean operations
# --------------------------------------------------------------------------

def to_path(contours) -> pathops.Path:
    path = pathops.Path()
    draw_contours(contours, path.getPen())
    return path


def from_path(path: pathops.Path) -> list[list]:
    if hasattr(path, "convertConicsToQuads"):
        path.convertConicsToQuads()     # stroking makes conics, which pens cannot draw
    pen = ContourPen()
    path.draw(pen)
    return pen.contours


#: What ``union`` could not merge since the list was last cleared: one line of plain words for each case.
#: ``Family.draw`` clears it before a glyph and reports what it holds after, so a build names the glyph.
trouble: list = []


def _nudged(contours, k: int) -> list:
    """Each contour moved by a different few hundredths of a unit, so that no two curves coincide exactly."""
    out = []
    for i, c in enumerate(contours):
        off = complex(((i * 7 + k * 3) % 11 - 5) * 0.03, ((i * 5 + k * 2) % 13 - 6) * 0.03)
        out.append(transform_contour(c, lambda q, off=off: q + off))
    return out


def union(contours) -> list[list]:
    """Merge overlapping contours (non-zero winding). Outer contours come back clockwise.

    Skia can fail, or lose a piece, where two curves lie exactly on each other. Every contour of the
    input must lie in the box of the result (a merge may trim a small loop, so the test is the middle
    of each contour). If one does not, the contours are moved apart by a hair and merged again. If
    that fails too, the contours come back unmerged (they still fill the same area) and ``trouble``
    says so.
    """
    contours = [c for c in contours if c]
    if not contours:
        return []
    # Non-zero fill: clockwise contours add ink, counter-clockwise ones cut holes.
    middles = []
    for c in contours:
        if abs(contour_area(c)) > 0.5:
            x0, y0, x1, y1 = contour_bounds([c])
            middles.append(((x0 + x1) / 2, (y0 + y1) / 2))
    for k in range(6):
        path = to_path(contours if k == 0 else _nudged(contours, k))
        try:
            path.simplify(fix_winding=True, keep_starting_points=False, clockwise=True)
        except Exception:
            continue
        out = [c for c in from_path(path) if len(c) >= 2 and abs(contour_area(c)) > 0.5]
        if not middles:
            return out
        if out:
            x0, y0, x1, y1 = contour_bounds(out)
            if all(x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1 for x, y in middles):
                return out
    trouble.append("overlapping shapes could not be merged, so the outline keeps its overlaps. "
                   "Move the shapes that lie exactly on each other apart by a unit")
    return contours


def difference(contours, cutters) -> list[list]:
    a, b = to_path(contours), to_path(cutters)
    out = pathops.op(a, b, pathops.PathOp.DIFFERENCE, fix_winding=True, clockwise=True)
    return from_path(out)


def intersection(contours, clip) -> list[list]:
    a, b = to_path(contours), to_path(clip)
    out = pathops.op(a, b, pathops.PathOp.INTERSECTION, fix_winding=True, clockwise=True)
    return from_path(out)


def depths(contours) -> list:
    """How many of the other contours contain each contour: 0 for an outside, 1 for a counter,
    2 for an island in a counter. The contours must not cross (the output of :func:`union`)."""
    flat = [flatten_contour(c, 2.0) for c in contours]
    boxes = [(min(q.real for q in f), max(q.real for q in f), min(q.imag for q in f), max(q.imag for q in f))
             if f else (0, 0, 0, 0) for f in flat]
    out = []
    for i, pts in enumerate(flat):
        d = 0
        if pts:
            x, y = pts[0].real, pts[0].imag
            for j, other in enumerate(flat):
                if i == j or not (boxes[j][0] <= x <= boxes[j][1] and boxes[j][2] <= y <= boxes[j][3]):
                    continue
                hit = False
                n = len(other)
                for k in range(n):
                    a, b = other[k], other[(k + 1) % n]
                    if (a.imag > y) != (b.imag > y) and x < a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag):
                        hit = not hit
                d += hit
        out.append(d)
    return out


def _clearance(points: list, edge: list) -> float:
    """The smallest distance from any of ``points`` to the closed polyline ``edge``."""
    best = float("inf")
    n = len(edge)
    for q in points[::max(1, len(points) // 24)]:
        for k in range(n):
            a, b = edge[k], edge[(k + 1) % n]
            ab = b - a
            den = ab.real * ab.real + ab.imag * ab.imag
            t = 0.0 if den < 1e-12 else max(0.0, min(1.0, ((q - a).real * ab.real + (q - a).imag * ab.imag) / den))
            d = abs(q - (a + ab * t))
            if d < best:
                best = d
    return best


def _band(contour, amount: float, miter: bool) -> list:
    """A band ``2 * amount`` wide along one contour."""
    path = to_path([contour])
    join = pathops.LineJoin.MITER_JOIN if miter else pathops.LineJoin.ROUND_JOIN
    path.stroke(amount * 2, pathops.LineCap.ROUND_CAP, join, 4.0)
    if hasattr(path, "convertConicsToQuads"):
        path.convertConicsToQuads()
    return union(from_path(path))


def dilate(contours, amount: float, miter: bool = False) -> list[list]:
    """Grow a shape outward by ``amount`` on every side (round or mitered corners).

    Each contour is handled on its own: an outside grows, a counter shrinks, an island in a
    counter grows again. Growing the whole outline at once can lose a counter.
    """
    shape = union(contours)
    if amount <= 0 or not shape:
        return shape
    level = depths(shape)
    result = pathops.Path()
    for d in range(max(level) + 1):
        ink, holes = [], []
        for c, lv in zip(shape, level):
            if lv != d:
                continue
            band = _band(c, amount, miter)
            solid = c if contour_area(c) < 0 else reverse_contour(c)
            if d % 2 == 0:
                ink += union([solid] + band)
            else:
                # a counter: what is left of it after the ink grows into it
                left = from_path(pathops.op(to_path([solid]), to_path(band), pathops.PathOp.DIFFERENCE,
                                            fix_winding=True, clockwise=True))
                # In a counter narrower than the band, the stroker leaves a scrap in the middle.
                # What is really left lies a full ``amount`` from the old edge.
                edge = flatten_contour(c, 0.25)
                least = amount - max(1.0, 0.15 * amount)
                holes += [piece for piece in left if _clearance(flatten_contour(piece, 0.25), edge) >= least]
        if ink:
            result = pathops.op(result, to_path(union(ink)), pathops.PathOp.UNION, fix_winding=True, clockwise=True)
        if holes:
            result = pathops.op(result, to_path(holes), pathops.PathOp.DIFFERENCE, fix_winding=True, clockwise=True)
    return [c for c in from_path(result) if len(c) >= 2 and abs(contour_area(c)) > 0.5]


def rect(x0: float, y0: float, x1: float, y1: float, radius: float = 0.0) -> list:
    """A clockwise rectangle contour, optionally with rounded corners."""
    from .stroke import clean, fillet
    pts = [complex(x0, y0), complex(x0, y1), complex(x1, y1), complex(x1, y0)]
    c = [(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    return clean(fillet(c, [radius] * 4)) if radius > 0 else c


def circle(cx: float, cy: float, r: float) -> list:
    """A clockwise circle contour."""
    k = 0.5523 * r
    e, n, w, s = complex(cx + r, cy), complex(cx, cy + r), complex(cx - r, cy), complex(cx, cy - r)
    return [(n, n + k, e + 1j * k, e), (e, e - 1j * k, s + k, s), (s, s - k, w - 1j * k, w), (w, w + 1j * k, n - k, n)]


# --------------------------------------------------------------------------
# Raster (for looking at work in progress, before a font file exists)
# --------------------------------------------------------------------------

def raster(contours, matrix, size, ink=(20, 20, 20), paper=(255, 255, 255), image=None,
           ss: int = 3) -> Image.Image:
    """Fill non-overlapping contours (the output of :func:`union`).

    ``matrix`` maps font units to pixels (y down). Contours are painted from
    the largest to the smallest, so counters punch holes.
    """
    w, h = size
    mask = Image.new("L", (w * ss, h * ss), 0)
    draw = ImageDraw.Draw(mask)
    polys = []
    for c in contours:
        pts = [apply_affine(matrix, p) for p in flatten_contour(c, 0.3)]
        if len(pts) < 3:
            continue
        polys.append((abs(contour_area(c)), contour_area(c) < 0, pts))
    for _, solid, pts in sorted(polys, key=lambda t: -t[0]):
        draw.polygon([(p.real * ss, p.imag * ss) for p in pts], fill=255 if solid else 0)
    mask = mask.resize((w, h), Image.LANCZOS)
    if image is None:
        image = Image.new("RGB", (w, h), paper)
    image.paste(Image.new("RGB", (w, h), ink), (0, 0), mask)
    return image
