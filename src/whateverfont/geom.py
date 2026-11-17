"""2D geometry helpers.

Points and vectors are Python ``complex`` numbers (``x + yj``). That keeps the
vector math short: addition and scaling are native, and multiplying by ``1j``
rotates a vector 90 degrees counter-clockwise.

A *segment* is a tuple of points: two points make a line, four make a cubic
Bezier. A *contour* is a list of segments in which each segment starts where
the previous one ended, and the last one ends where the first one started.
"""

from __future__ import annotations

import math

EPS = 1e-9


def pt(x: float, y: float) -> complex:
    return complex(x, y)


def xy(p: complex) -> tuple[float, float]:
    return (p.real, p.imag)


def unit(v: complex) -> complex:
    n = abs(v)
    return v / n if n > EPS else 0j


def left(v: complex) -> complex:
    """Rotate 90 degrees counter-clockwise (the left-hand normal of a direction)."""
    return v * 1j


def dot(a: complex, b: complex) -> float:
    return a.real * b.real + a.imag * b.imag


def cross(a: complex, b: complex) -> float:
    return a.real * b.imag - a.imag * b.real


def lerp(a, b, t: float):
    return a + (b - a) * t


def polar(angle_deg: float, r: float = 1.0) -> complex:
    a = math.radians(angle_deg)
    return complex(math.cos(a) * r, math.sin(a) * r)


def angle_deg(v: complex) -> float:
    return math.degrees(math.atan2(v.imag, v.real))


def line_hit(p: complex, d: complex, q: complex, e: complex) -> complex | None:
    """Intersection of the line through ``p`` along ``d`` with the line through ``q`` along ``e``."""
    den = cross(d, e)
    if abs(den) < 1e-7:
        return None
    s = cross(q - p, e) / den
    return p + d * s


# --------------------------------------------------------------------------
# Segments
# --------------------------------------------------------------------------

def is_line(seg) -> bool:
    return len(seg) == 2


def seg_point(seg, t: float) -> complex:
    if len(seg) == 2:
        return lerp(seg[0], seg[1], t)
    p0, p1, p2, p3 = seg
    u = 1 - t
    return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3


def seg_deriv(seg, t: float) -> complex:
    if len(seg) == 2:
        return seg[1] - seg[0]
    p0, p1, p2, p3 = seg
    u = 1 - t
    return 3 * u * u * (p1 - p0) + 6 * u * t * (p2 - p1) + 3 * t * t * (p3 - p2)


def seg_tangent(seg, t: float) -> complex:
    """Unit tangent at ``t``; survives zero-length handles at either end."""
    if len(seg) == 2:
        return unit(seg[1] - seg[0])
    p0, p1, p2, p3 = seg
    if t <= 0:
        for q in (p1, p2, p3):
            if abs(q - p0) > 1e-6:
                return unit(q - p0)
        return 0j
    if t >= 1:
        for q in (p2, p1, p0):
            if abs(p3 - q) > 1e-6:
                return unit(p3 - q)
        return 0j
    d = seg_deriv(seg, t)
    if abs(d) < 1e-9:
        return unit(seg_point(seg, min(1, t + 1e-3)) - seg_point(seg, max(0, t - 1e-3)))
    return unit(d)


def split_cubic(seg, t: float):
    p0, p1, p2, p3 = seg
    a = lerp(p0, p1, t)
    b = lerp(p1, p2, t)
    c = lerp(p2, p3, t)
    d = lerp(a, b, t)
    e = lerp(b, c, t)
    f = lerp(d, e, t)
    return (p0, a, d, f), (f, e, c, p3)


def split_seg(seg, t: float):
    if len(seg) == 2:
        m = lerp(seg[0], seg[1], t)
        return (seg[0], m), (m, seg[1])
    return split_cubic(seg, t)


def seg_length(seg, n: int = 8) -> float:
    if len(seg) == 2:
        return abs(seg[1] - seg[0])
    total = 0.0
    prev = seg[0]
    for i in range(1, n + 1):
        q = seg_point(seg, i / n)
        total += abs(q - prev)
        prev = q
    return total


def reverse_seg(seg):
    return tuple(reversed(seg))


def flatten_seg(seg, tol: float = 0.5) -> list[complex]:
    """Points along a segment, excluding its first point."""
    if len(seg) == 2:
        return [seg[1]]
    p0, p1, p2, p3 = seg
    # Flatness estimate decides the number of steps.
    d = max(abs(p0 - 2 * p1 + p2), abs(p1 - 2 * p2 + p3))
    n = max(2, min(64, int(math.ceil(math.sqrt(3 * d / (4 * tol))))))
    return [seg_point(seg, i / n) for i in range(1, n + 1)]


def flatten_contour(contour, tol: float = 0.5) -> list[complex]:
    out: list[complex] = []
    if not contour:
        return out
    out.append(contour[0][0])
    for seg in contour:
        out.extend(flatten_seg(seg, tol))
    if len(out) > 1 and abs(out[0] - out[-1]) < 1e-6:
        out.pop()
    return out


def polygon_area(points: list[complex]) -> float:
    """Signed area; positive when the polygon runs counter-clockwise (y up)."""
    a = 0.0
    n = len(points)
    for i in range(n):
        p, q = points[i], points[(i + 1) % n]
        a += p.real * q.imag - q.real * p.imag
    return a / 2


def contour_area(contour) -> float:
    return polygon_area(flatten_contour(contour, 1.0))


def reverse_contour(contour):
    return [reverse_seg(s) for s in reversed(contour)]


def transform_contour(contour, fn):
    return [tuple(fn(p) for p in seg) for seg in contour]


def contour_bounds(contours) -> tuple[float, float, float, float] | None:
    xs: list[float] = []
    ys: list[float] = []
    for c in contours:
        for p in flatten_contour(c, 1.0):
            xs.append(p.real)
            ys.append(p.imag)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------
# Affine transforms: (a, b, c, d, e, f) maps (x, y) -> (ax + cy + e, bx + dy + f)
# --------------------------------------------------------------------------

IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def apply_affine(m, p: complex) -> complex:
    a, b, c, d, e, f = m
    return complex(a * p.real + c * p.imag + e, b * p.real + d * p.imag + f)


def affine_mul(m1, m2):
    """Compose so that the result applies ``m2`` first, then ``m1``."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def translate(dx: float, dy: float):
    return (1.0, 0.0, 0.0, 1.0, dx, dy)


def scale(sx: float, sy: float | None = None):
    return (sx, 0.0, 0.0, sx if sy is None else sy, 0.0, 0.0)


def shear_x(tan_angle: float):
    return (1.0, 0.0, tan_angle, 1.0, 0.0, 0.0)


def rotate_about(deg: float, cx: float = 0.0, cy: float = 0.0):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy)


def flip_x_about(cx: float):
    return (-1.0, 0.0, 0.0, 1.0, 2 * cx, 0.0)


def flip_y_about(cy: float):
    return (1.0, 0.0, 0.0, -1.0, 0.0, 2 * cy)
