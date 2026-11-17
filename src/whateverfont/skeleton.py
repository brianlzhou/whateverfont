"""Centerlines of filled shapes: raster, distance, thinning, and a graph of the skeleton.

This is the image part of :mod:`whateverfont.trace`. It needs numpy (the ``trace`` extra:
``pip install 'whateverfont[trace]'``) and nothing else. Coordinates in here are pixels,
(row, column), unless a name says font units.
"""

from __future__ import annotations

import math

try:
    import numpy as np
except ImportError as exc:          # pragma: no cover - depends on the environment
    raise ImportError("tracing needs numpy. Install it with: pip install 'whateverfont[trace]'") from exc

from PIL import Image, ImageDraw

from .geom import flatten_contour

PAD = 24          # pixels of white around a glyph


# --------------------------------------------------------------------------
# Raster
# --------------------------------------------------------------------------

class Raster:
    """A filled shape on a pixel grid. ``scale`` is pixels per font unit.

    The contours must not overlap (the output of :func:`whateverfont.outline.union`):
    they are filled by parity, so a counter is white whatever its direction.
    """

    def __init__(self, contours: list, scale: float, box=None):
        pts = [flatten_contour(c, 0.25) for c in contours]
        pts = [p for p in pts if len(p) >= 3]
        self.s = scale
        if box is None:
            xs = [q.real for p in pts for q in p] or [0.0]
            ys = [q.imag for p in pts for q in p] or [0.0]
            box = (min(xs), min(ys), max(xs), max(ys))
        self.x0, self.y1 = box[0], box[3]
        w = int((box[2] - box[0]) * scale) + 2 * PAD
        h = int((box[3] - box[1]) * scale) + 2 * PAD
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        acc = np.zeros((h, w), dtype=np.uint8)
        for p in pts:
            mask.paste(0, (0, 0, w, h))
            draw.polygon([self.to_px(q) for q in p], fill=1)
            acc ^= np.asarray(mask, dtype=np.uint8)
        self.ink = acc.astype(bool)

    def to_px(self, q: complex) -> tuple:
        """Font units to (x, y) image coordinates, for drawing."""
        return ((q.real - self.x0) * self.s + PAD, (self.y1 - q.imag) * self.s + PAD)

    def to_font(self, r: float, c: float) -> complex:
        """(row, column) to font units."""
        return complex((c - PAD) / self.s + self.x0, self.y1 - (r - PAD) / self.s)

    def row_of(self, y: float) -> float:
        return PAD + (self.y1 - y) * self.s


# --------------------------------------------------------------------------
# Image operations, in numpy
# --------------------------------------------------------------------------

def edt(mask) -> "np.ndarray":
    """Exact Euclidean distance from each pixel of ``mask`` to the nearest pixel outside it."""
    h, w = mask.shape
    big = h + w + 1
    rows = np.arange(h)[:, None]
    out = ~mask
    last = np.maximum.accumulate(np.where(out, rows, -big), axis=0)
    nxt = np.minimum.accumulate(np.where(out, rows, 2 * big)[::-1], axis=0)[::-1]
    g = np.minimum(rows - last, nxt - rows).astype(np.float64)
    if not mask.any():
        return np.zeros((h, w))
    best = g * g
    top = float(g[mask].max())
    for dc in range(1, int(top) + 2):
        if dc * dc > best.max():
            break
        d2 = g * g + dc * dc
        best[:, dc:] = np.minimum(best[:, dc:], d2[:, :-dc])
        best[:, :-dc] = np.minimum(best[:, :-dc], d2[:, dc:])
    return np.sqrt(best)


def _thin_tables(least: int = 2):
    """Zhang and Suen's two removal tests, for each of the 256 neighborhoods. A pixel goes only if it has
    at least ``least`` neighbors: 3 is Lü and Wang's change, which keeps a line at 45 degrees."""
    tables = []
    for step in (0, 1):
        t = np.zeros(256, dtype=bool)
        for code in range(256):
            p = [(code >> i) & 1 for i in range(8)]     # p2 (north), p3, p4 (east), ..., p9 (north-west)
            b = sum(p)
            a = sum(1 for i in range(8) if p[i] == 0 and p[(i + 1) % 8] == 1)
            p2, p4, p6, p8 = p[0], p[2], p[4], p[6]
            if step == 0:
                c = p2 * p4 * p6 == 0 and p4 * p6 * p8 == 0
            else:
                c = p2 * p4 * p8 == 0 and p2 * p6 * p8 == 0
            t[code] = least <= b <= 6 and a == 1 and c
        tables.append(t)
    return tables


_TABLES = None
_TABLES_45 = None


def thin(mask) -> "np.ndarray":
    """The skeleton of ``mask``, one pixel wide (Zhang and Suen's thinning).

    Zhang and Suen's thinning can wear a straight stroke at 45 degrees away to a single pixel (the slash
    ／ of Noto Sans CJK). A part of the shape whose skeleton is far shorter than the part is thinned
    again with Lü and Wang's test, which keeps such a stroke."""
    global _TABLES_45
    out = _thin(mask)
    lab, n = label(mask)
    for i in range(1, n + 1):
        m = lab == i
        rows, cols = np.nonzero(m)
        side = max(rows.max() - rows.min(), cols.max() - cols.min()) + 1
        if side > 12 and out[m].sum() < 0.25 * side:
            if _TABLES_45 is None:
                _TABLES_45 = _thin_tables(3)
            out[m] = _thin(m, _TABLES_45)[m]
    return out


def _thin(mask, tables=None) -> "np.ndarray":
    global _TABLES
    if tables is None:
        if _TABLES is None:
            _TABLES = _thin_tables()
        tables = _TABLES
    img = mask.astype(np.uint8)
    rows, cols = np.nonzero(img)
    if rows.size == 0:
        return img.astype(bool)
    r0, r1 = max(0, rows.min() - 1), min(img.shape[0], rows.max() + 2)
    c0, c1 = max(0, cols.min() - 1), min(img.shape[1], cols.max() + 2)
    sub = img[r0:r1, c0:c1].copy()
    while True:
        changed = False
        for table in tables:
            p = np.pad(sub, 1)
            code = (p[:-2, 1:-1] | (p[:-2, 2:] << 1) | (p[1:-1, 2:] << 2) | (p[2:, 2:] << 3)
                    | (p[2:, 1:-1] << 4) | (p[2:, :-2] << 5) | (p[1:-1, :-2] << 6) | (p[:-2, :-2] << 7))
            gone = table[code] & (sub == 1)
            if gone.any():
                sub[gone] = 0
                changed = True
        if not changed:
            break
    out = np.zeros_like(img, dtype=bool)
    out[r0:r1, c0:c1] = sub.astype(bool)
    return out


def label(mask) -> tuple:
    """Connected parts of ``mask`` (8-connected). Returns (labels, count); labels run from 1."""
    h, w = mask.shape
    m = np.zeros((h, w + 2), dtype=np.int8)
    m[:, 1:-1] = mask
    d = np.diff(m, axis=1)
    sr, sc = np.nonzero(d == 1)
    er, ec = np.nonzero(d == -1)
    runs = list(zip(sr.tolist(), sc.tolist(), (ec - 1).tolist()))     # (row, first, last)
    parent = list(range(len(runs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    by_row = {}
    for i, (r, a, b) in enumerate(runs):
        by_row.setdefault(r, []).append(i)
    for i, (r, a, b) in enumerate(runs):
        for j in by_row.get(r - 1, []):
            _, a2, b2 = runs[j]
            if a2 <= b + 1 and b2 >= a - 1:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    lab = np.zeros((h, w), dtype=np.int32)
    ids = {}
    for i, (r, a, b) in enumerate(runs):
        root = find(i)
        if root not in ids:
            ids[root] = len(ids) + 1
        lab[r, a:b + 1] = ids[root]
    return lab, len(ids)


def grow(mask, steps: int = 1) -> "np.ndarray":
    """``mask`` grown by ``steps`` pixels (4-connected)."""
    out = mask.copy()
    for _ in range(steps):
        new = out.copy()
        new[1:, :] |= out[:-1, :]
        new[:-1, :] |= out[1:, :]
        new[:, 1:] |= out[:, :-1]
        new[:, :-1] |= out[:, 1:]
        out = new
    return out


def gauss1d(a, sigma: float, wrap: bool = False) -> "np.ndarray":
    """Gaussian smoothing of each column of ``a``. The ends repeat, or the rows wrap around."""
    radius = int(4.0 * sigma + 0.5)
    if radius < 1:
        return a
    x = np.arange(-radius, radius + 1)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()
    n = len(a)
    idx = np.arange(-radius, n + radius)
    padded = a[idx % n] if wrap else a[np.clip(idx, 0, n - 1)]
    out = np.empty_like(a, dtype=np.float64)
    for j in range(a.shape[1]):
        out[:, j] = np.convolve(padded[:, j], k, mode="valid")
    return out


# --------------------------------------------------------------------------
# The skeleton as a graph
# --------------------------------------------------------------------------

N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
ND = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def neighbors(p, pix) -> list:
    """The skeleton pixels next to ``p``. A diagonal counts only where no straight step joins them."""
    r, c = p
    out = [(r + dr, c + dc) for dr, dc in N4 if (r + dr, c + dc) in pix]
    for dr, dc in ND:
        q = (r + dr, c + dc)
        if q in pix and (r + dr, c) not in pix and (r, c + dc) not in pix:
            out.append(q)
    return out


def path_length(path) -> float:
    return sum(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(path, path[1:]))


class Graph:
    """Nodes are ends and junctions of the skeleton; edges are the pixel paths between them."""

    def __init__(self, sk, dist):
        pix = set(zip(*(v.tolist() for v in np.nonzero(sk))))
        self.dist = dist
        nb = {p: neighbors(p, pix) for p in pix}
        node_of = {}
        self.nodes = {}
        nid = 0
        junction = {p for p in pix if len(nb[p]) >= 3}
        seen = set()
        for p in junction:
            if p in seen:
                continue
            stack, cluster = [p], []
            seen.add(p)
            while stack:
                q = stack.pop()
                cluster.append(q)
                for n in nb[q]:
                    if n in junction and n not in seen:
                        seen.add(n)
                        stack.append(n)
            for q in cluster:
                node_of[q] = nid
            self.nodes[nid] = self._node(cluster)
            nid += 1
        for p in pix:
            if len(nb[p]) <= 1:
                node_of[p] = nid
                self.nodes[nid] = self._node([p])
                nid += 1
        self.edges = {}
        eid = 0
        used = set()
        for p, a in list(node_of.items()):
            for n in nb[p]:
                if node_of.get(n) == a or (p, n) in used:
                    continue
                path, prev, cur = [p, n], p, n
                used.add((p, n))
                ok = True
                while cur not in node_of:
                    nxt = [q for q in nb[cur] if q != prev]
                    if not nxt:
                        ok = False
                        break
                    prev, cur = cur, nxt[0]
                    path.append(cur)
                    if len(path) > 20000:
                        ok = False
                        break
                if not ok:
                    continue
                used.add((cur, prev))
                b = node_of[cur]
                if a == b and len(path) < 6:
                    continue
                self.edges[eid] = [a, b, path]
                eid += 1
        # rings: pixels that belong to no edge
        covered = {q for e in self.edges.values() for q in e[2]} | set(node_of)
        rest = pix - covered
        while rest:
            p = rest.pop()
            path, prev, cur = [p], None, p
            while True:
                nxt = [q for q in nb[cur] if q != prev and q in rest]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
                rest.discard(cur)
                path.append(cur)
            if len(path) > 8:
                self.nodes[nid] = self._node([p])
                self.edges[eid] = [nid, nid, path + [p]]
                nid += 1
                eid += 1

    def _node(self, cluster):
        rs = [q[0] for q in cluster]
        cs = [q[1] for q in cluster]
        return dict(pix=cluster, center=(sum(rs) / len(rs), sum(cs) / len(cs)),
                    r=max(float(self.dist[q]) for q in cluster))

    def degree(self, n) -> int:
        return sum((e[0] == n) + (e[1] == n) for e in self.edges.values())

    def _merge_through(self, n) -> bool:
        """Join the two edges at a node of degree 2 that is not a ring."""
        inc = [(k, e) for k, e in self.edges.items() if n in (e[0], e[1])]
        if len(inc) != 2 or inc[0][0] == inc[1][0]:
            return False
        (k1, e1), (k2, e2) = inc
        p1 = e1[2] if e1[1] == n else e1[2][::-1]
        o1 = e1[0] if e1[1] == n else e1[1]
        p2 = e2[2] if e2[0] == n else e2[2][::-1]
        o2 = e2[1] if e2[0] == n else e2[0]
        if o1 == n or o2 == n:
            return False
        del self.edges[k1], self.edges[k2]
        self.edges[k1] = [o1, o2, p1 + p2[1:]]
        del self.nodes[n]
        return True

    def prune(self, spur: float = 1.7, merge: float = 0.9, keep=None):
        """Remove short spurs (from corners and ends) and merge junctions that sit close together.

        ``keep(pixel)`` is true for the end of a spur that must stay (a stub that joins the next letter)."""
        changed = True
        while changed:
            changed = False
            for k, (a, b, path) in list(self.edges.items()):
                if k not in self.edges:
                    continue
                da, db = self.degree(a), self.degree(b)
                for end, other, dend, doth in ((a, b, da, db), (b, a, db, da)):
                    if keep is not None and dend == 1 and keep(self.nodes[end]["pix"][0]):
                        continue
                    if dend == 1 and doth >= 3 and path_length(path) < spur * self.nodes[other]["r"]:
                        del self.edges[k]
                        del self.nodes[end]
                        if self.degree(other) == 2:
                            self._merge_through(other)
                        changed = True
                        break
                if changed:
                    break
            if changed:
                continue
            # two junctions joined by a short edge: an X that the thinning split into two Ys
            for k, (a, b, path) in list(self.edges.items()):
                if a == b or self.degree(a) < 3 or self.degree(b) < 3:
                    continue
                if path_length(path) < merge * (self.nodes[a]["r"] + self.nodes[b]["r"]):
                    na, nb_ = self.nodes[a], self.nodes[b]
                    na["pix"] = na["pix"] + nb_["pix"] + path
                    na["center"] = ((na["center"][0] + nb_["center"][0]) / 2, (na["center"][1] + nb_["center"][1]) / 2)
                    na["r"] = max(na["r"], nb_["r"])
                    del self.edges[k]
                    for e in self.edges.values():
                        if e[0] == b:
                            e[0] = a
                        if e[1] == b:
                            e[1] = a
                    del self.nodes[b]
                    changed = True
                    break
        for n in list(self.nodes):
            if n in self.nodes and self.degree(n) == 2:
                self._merge_through(n)
        for n in list(self.nodes):
            if self.degree(n) == 0:
                del self.nodes[n]


# --------------------------------------------------------------------------
# Paths: directions, smoothing, corners, simplification
# --------------------------------------------------------------------------

def direction(path, from_start: bool, skip: float, span: float) -> tuple:
    """The unit direction (row, column) of a path leaving its start (or its end), past the first ``skip`` pixels."""
    p = path if from_start else path[::-1]
    acc, i0 = 0.0, 0
    for i in range(1, len(p)):
        acc += math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1])
        if acc >= skip:
            i0 = i
            break
    acc, i1 = 0.0, len(p) - 1
    for i in range(i0 + 1, len(p)):
        acc += math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1])
        if acc >= span:
            i1 = i
            break
    if i1 <= i0:
        i0, i1 = 0, len(p) - 1
    d = (p[i1][0] - p[i0][0], p[i1][1] - p[i0][1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def trim(path, center, r, limit: float = 1.0) -> list:
    """Drop the points within ``r`` of ``center`` at the start of ``path``, but no more than
    the share ``limit`` of its points: a short arm keeps most of itself."""
    i = 0
    most = max(0, min(len(path) - 2, int(len(path) * limit)))
    while i < most and math.hypot(path[i][0] - center[0], path[i][1] - center[1]) < r:
        if math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) > 3:
            break                    # a gap that an earlier trim left: the rest belongs to another arm
        i += 1
    return path[i:]


def smooth(pts, sigma: float) -> list:
    """Smooth an open path. The ends stay put: the path is mirrored about them first."""
    if len(pts) < 5 or sigma <= 0:
        return pts
    a = np.array(pts, float)
    pad = min(int(3 * sigma) + 1, len(a) - 1)
    head = 2 * a[0] - a[1:pad + 1][::-1]
    tail = 2 * a[-1] - a[-pad - 1:-1][::-1]
    b = gauss1d(np.vstack([head, a, tail]), sigma)
    return [tuple(q) for q in b[pad:pad + len(a)].tolist()]


def smooth_ring(pts, sigma: float) -> list:
    return [tuple(q) for q in gauss1d(np.array(pts, float), sigma, wrap=True).tolist()]


def _turns(a, w: int, closed: bool):
    n = len(a)
    prev = np.roll(a, w, axis=0)
    nxt = np.roll(a, -w, axis=0)
    d0, d1 = a - prev, nxt - a
    l0, l1 = np.hypot(d0[:, 0], d0[:, 1]), np.hypot(d1[:, 0], d1[:, 1])
    ok = (l0 > 1e-9) & (l1 > 1e-9)
    c = np.ones(n)
    c[ok] = (d0[ok] * d1[ok]).sum(axis=1) / (l0[ok] * l1[ok])
    turn = np.degrees(np.arccos(np.clip(c, -1, 1)))
    if not closed:
        turn[:w] = 0
        turn[n - w:] = 0
    return turn


def _line_fit(pts):
    c = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - c)
    return c, vt[0]


def sharpen(px, r: float, closed: bool, min_turn: float = 50.0, ink=None) -> tuple:
    """Rebuild sharp corners of a dense pixel path.

    Thinning cuts a corner short and grows a spur into it. A corner is a place where the direction
    turns more than ``min_turn`` degrees over about a stroke width; it is replaced by the meeting
    point of straight lines fitted to the runs on either side. With ``ink`` (the source raster), a
    meeting point in the white is a tight curl, not a corner, and stays round.
    Returns (points, corner points).
    """
    a = np.array(px, float)
    n = len(a)
    w = max(3, int(round(1.4 * r)))
    if n < 4 * w + 2:
        return px, []
    if closed:
        turn0 = _turns(a, w, True)
        if turn0.max() < min_turn:
            return px, []
        # Open the ring in the middle of the longest run between its corners: a corner near the seam
        # would be lost (a box has four, so starting opposite the sharpest one puts another at the seam).
        peaks = []
        for i in np.argsort(-turn0):
            if turn0[i] < min_turn:
                break
            if all(min(abs(i - j), n - abs(i - j)) > 2 * w for j in peaks):
                peaks.append(int(i))
        peaks.sort()
        gaps = [((peaks[(k + 1) % len(peaks)] - peaks[k]) % n or n, peaks[k]) for k in range(len(peaks))]
        span, at = max(gaps)
        start = (at + span // 2) % n
        a = np.vstack([a[start:], a[:start]])
    turn = _turns(a, w, False)
    corners = []
    taken = np.zeros(n, bool)
    for i in np.argsort(-turn):
        if turn[i] < min_turn:
            break
        if taken[i] or i < 2 * w or i > n - 1 - 2 * w:
            continue
        taken[max(0, i - 2 * w):i + 2 * w + 1] = True
        corners.append(int(i))
    if not corners:
        return ([tuple(q) for q in a.tolist()] if closed else px), []
    corners.sort()
    out, marks, last = [], [], 0
    for i in corners:
        b0, b1 = max(last, i - 3 * w), i - w
        c0, c1 = i + w, min(n - 1, i + 3 * w)
        if b1 - b0 < 3 or c1 - c0 < 3:
            continue
        (pa, ua), (pb, ub) = _line_fit(a[b0:b1 + 1]), _line_fit(a[c0:c1 + 1])
        den = ua[0] * ub[1] - ua[1] * ub[0]
        if abs(den) < 1e-6:
            continue
        t = ((pb[0] - pa[0]) * ub[1] - (pb[1] - pa[1]) * ub[0]) / den
        x = pa + ua * t
        if np.hypot(*(x - a[i])) > 2.5 * r:
            continue
        if ink is not None:
            ri, ci = int(round(x[0])), int(round(x[1]))
            if not (0 <= ri < ink.shape[0] and 0 <= ci < ink.shape[1]) or not ink[ri, ci]:
                continue
        out.extend(tuple(q) for q in a[last:i - w].tolist())
        out.append(tuple(x.tolist()))
        marks.append(tuple(x.tolist()))
        last = i + w + 1
    out.extend(tuple(q) for q in a[last:].tolist())
    return out, marks


def smooth_pieces(pts, marks, sigma: float, closed: bool) -> list:
    """Smooth a path piece by piece between its corners, which stay where they are."""
    if not marks:
        if closed:
            return smooth_ring(pts, sigma) if len(pts) > 8 else pts
        return smooth(pts, sigma)
    keep = set(marks)
    idx = [i for i, q in enumerate(pts) if q in keep]
    if closed:
        k = idx[0]
        pts = pts[k:] + pts[:k] + [pts[k]]
        idx = [i for i, q in enumerate(pts) if q in keep]
    cuts = sorted(set([0] + idx + [len(pts) - 1]))
    out = []
    for a, b in zip(cuts, cuts[1:]):
        piece = smooth(pts[a:b + 1], sigma)
        piece[0], piece[-1] = pts[a], pts[b]
        out.extend(piece if not out else piece[1:])
    if closed:
        out = out[:-1]
    return out


def straighten(pts, marks, r: float, closed: bool, share: float = 0.06) -> list:
    """Make the nearly straight pieces of a path straight. A piece runs between two corners (or a corner and
    an end). It becomes the line between its ends if no point lies farther from that line than half the
    stroke's half width ``r`` or ``share`` of the piece's length.

    The strokes of type in Chinese characters and Hangul are straight. Thinning bends them where they meet
    other strokes, and a heavy pen makes the bend a wobble."""
    keep = set(marks)
    n = len(pts)
    if n < 3:
        return pts
    idx = [i for i, q in enumerate(pts) if q in keep]
    if closed:
        if len(idx) < 2:
            return pts
        k = idx[0]
        seq = pts[k:] + pts[:k] + [pts[k]]
    else:
        seq = list(pts)
    idx = [i for i, q in enumerate(seq) if q in keep]
    cuts = sorted(set([0] + idx + [len(seq) - 1]))
    out = []
    for a, b in zip(cuts, cuts[1:]):
        piece = seq[a:b + 1]
        if len(piece) > 2:
            p, q = np.array(piece[0]), np.array(piece[-1])
            d = q - p
            length = math.hypot(*d)
            if length > 1e-6:
                arr = np.array(piece)
                off = np.abs(d[0] * (arr[:, 1] - p[1]) - d[1] * (arr[:, 0] - p[0])) / length
                along = ((arr - p) @ d) / (length * length)
                if off.max() <= min(0.5 * r, share * length) and along.min() > -0.05 and along.max() < 1.05:
                    t = np.linspace(0.0, 1.0, len(piece))
                    piece = [tuple(x) for x in (p[None, :] + t[:, None] * d[None, :]).tolist()]
                    piece[0], piece[-1] = seq[a], seq[b]
        out.extend(piece if not out else piece[1:])
    if closed:
        out = out[:-1]
    return out


def rdp(pts, eps: float) -> list:
    """Indexes of the points that Ramer, Douglas and Peucker keep."""
    if len(pts) < 3:
        return list(range(len(pts)))
    a = np.array(pts, float)
    keep = [0, len(pts) - 1]
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        p, q = a[i], a[j]
        d = q - p
        n = math.hypot(*d)
        seg = a[i + 1:j]
        if n < 1e-9:
            dist = np.hypot(*(seg - p).T)
        else:
            dist = np.abs(d[0] * (seg[:, 1] - p[1]) - d[1] * (seg[:, 0] - p[0])) / n
        k = int(np.argmax(dist))
        if dist[k] > eps:
            m = i + 1 + k
            keep.append(m)
            stack += [(i, m), (m, j)]
    return sorted(set(keep))
