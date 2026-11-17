"""Retrace: redraw an existing font with a family's pen, by tracing the centerline of every glyph.

This is how whateverfont draws scripts it has no recipes for (Arabic, Devanagari). The source
font gives the skeleton of each letter. The family gives the pen, and an effect may add color
layers. Everything that makes the script work stays as the source has it: the shaping tables
(GSUB, GPOS, GDEF), the character map, the advances, the anchors and the composite glyphs.

The letter shapes are the source's. The result is a modified version of the source font: it
keeps the source's license and copyright notice, and it must have a new name.

Tracing needs numpy, an optional extra: ``pip install 'whateverfont[trace]'``.

    from whateverfont import trace
    traced = trace.trace_font("NotoSansArabic-Regular.ttf")
    result = trace.redraw(traced, "out/LastBellArabic", "Last Bell Arabic", family)
"""

from __future__ import annotations

import copy
import io
import math
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from .compile import _stamp, _tt_glyph, quadratic_points, save_woff2, slug
from .geom import contour_area, contour_bounds, flatten_contour, transform_contour
from .glyph import G, V, Recipe, Recipes
from .outline import ContourPen, depths, union
from .remix import HINT_TABLES, _reserved_names, declared_license
from .stroke import Cap, Node, Stroke

INSTALL = "uv tool install 'whateverfont[trace]' (or: pipx inject whateverfont numpy; in a virtual environment: pip install 'whateverfont[trace]')"
SCALE = 0.5            # raster pixels per font unit, for 1000 units to the em
BLOB = 1.65            # a place on the skeleton this many times wider than the usual stroke is a ball terminal
DIR_SKIP = 1.5         # where the direction of an edge leaving a junction is measured, in junction radii
DIR_SPAN = 3.5         # over how long a run, in junction radii
THROUGH = 2.0          # how much of a through stroke is dropped on each side of a junction, in junction radii
PAIR_DEG = 45.0        # two edges at a junction are one stroke if they bend less than this
PAIR_DEG_DENSE = 22.0  # the same in Chinese characters and Hangul, whose strokes run straight through a crossing
FREE_TRIM = 1.6        # how much of a free end is dropped before it is extended, in end radii
SIGMA = 4.0            # smoothing of the centerline, in pixels
MARK_GROW = 0.4        # a mark gets this share of the extra weight a heavier pen gives the letters
DOT_GROW = 0.6         # a dot gets this share
KEEP_COUNTER = 0.45    # the share of a counter's white that must stay white
KEEP_GAP = 0.4         # the share of the white between two parts that must stay white
CONTRAST_WARN = 1.55   # a source whose wide strokes are this many times its narrow ones gets a warning
UPM = 1000             # the lengths in this module are in units of an em of this many: a source is brought to it
#: The scripts whose letters hang from a headline, as (first, last) code points: Devanagari, Bengali, Gurmukhi.
HEADLINE_SCRIPTS = ((0x0900, 0x097F), (0x0980, 0x09FF), (0x0A00, 0x0A7F))
DENSE_KEEP = 0.25      # in a dense character (Chinese, Japanese, Korean), the share of the white between strokes kept
DENSE_SAMPLE = 6       # the narrow white of a character is what this percentage of its stroke sides face
DENSE_FLOOR = 0.4      # a dense character's pen is never thinner than this share of the pen's stem
DENSE_FILL = 0.1       # a dense character whose narrow white keeps less than this share at the floor is flagged
FIT = 6.0              # no drawn curve strays farther than this from the traced centerline, in font units
NEAR = 0.3             # in the self-check of a dense font, parts closer than twice this share of the stroke touch


class MissingDependency(ImportError):
    """The ``trace`` extra is not installed."""


def _sk():
    try:
        from . import skeleton
    except ImportError as exc:
        raise MissingDependency(f"retracing needs numpy, which is not installed. Install it with: {INSTALL}") from exc
    return skeleton


# --------------------------------------------------------------------------
# Source outlines
# --------------------------------------------------------------------------

def glyph_contours(glyphset, name: str) -> list:
    """The outline of one glyph, components resolved."""
    rec = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(rec)
    pen = ContourPen()
    rec.replay(pen)
    pen._close()
    return pen.contours


def _resample(pts: list, step: float) -> list:
    """Points along a closed polyline, no farther apart than ``step``."""
    out = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(abs(b - a) / step))
        out.extend(a + (b - a) * (i / n) for i in range(n))
    return out


def _resample_open(pts: list, step: float) -> list:
    """Points along an open polyline, no farther apart than ``step``."""
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(abs(b - a) / step))
        out.extend(a + (b - a) * (i / n) for i in range(n))
    return out + pts[-1:]


# --------------------------------------------------------------------------
# One glyph: raster, skeleton, strokes in pixels
# --------------------------------------------------------------------------

def _headline_runs(sk, body, R, line, half):
    """Column runs where a band around ``line`` (font y) is solid ink: a Devanagari headline."""
    np = sk.np
    rc = R.row_of(line)
    h = half * R.s
    r0, r1 = max(0, int(math.floor(rc - h))), min(body.shape[0], int(math.ceil(rc + h)) + 1)
    if r1 - r0 < 2:
        return [], (r0, r1)
    core = body[max(r0, int(rc - h * 0.6)):min(r1, int(rc + h * 0.6) + 1), :]
    solid = core.mean(axis=0) > 0.95 if core.size else np.zeros(body.shape[1], bool)
    runs, c, w = [], 0, body.shape[1]
    while c < w:
        if solid[c]:
            c0 = c
            while c < w and solid[c]:
                c += 1
            if c - c0 >= 3.0 * h:
                runs.append((c0, c - 1))
        else:
            c += 1
    return runs, (r0, r1)


def _pair_and_walk(sk, g, pair_deg: float = PAIR_DEG):
    """Chain the edges of a skeleton graph through its junctions by good continuation.

    Returns dicts: px (pixel path), closed, and for each end: kind ("free" or "junction"),
    center, radius and the direction of the stroke that runs through that junction."""
    ends = {}
    for k, (a, b, path) in g.edges.items():
        ra, rb = g.nodes[a]["r"], g.nodes[b]["r"]
        ends[(k, 0)] = (a, sk.direction(path, True, ra * DIR_SKIP, ra * DIR_SPAN + 6))
        ends[(k, 1)] = (b, sk.direction(path, False, rb * DIR_SKIP, rb * DIR_SPAN + 6))
    pair = {}
    for n in g.nodes:
        inc = [e for e, (node, _) in ends.items() if node == n]
        if len(inc) < 3:
            if len(inc) == 2 and inc[0][0] != inc[1][0]:
                pair[inc[0]], pair[inc[1]] = inc[1], inc[0]
            continue
        cands = []
        for i in range(len(inc)):
            for j in range(i + 1, len(inc)):
                if inc[i][0] == inc[j][0]:
                    continue
                d1, d2 = ends[inc[i]][1], ends[inc[j]][1]
                bend = math.degrees(math.acos(max(-1, min(1, -(d1[0] * d2[0] + d1[1] * d2[1])))))
                cands.append((bend, inc[i], inc[j]))
        cands.sort()
        for bend, x, y in cands:
            if bend > pair_deg:
                break
            if x in pair or y in pair:
                continue
            pair[x], pair[y] = y, x
    done = set()

    def info(e):
        k, side = e
        a, b, _ = g.edges[k]
        n = a if side == 0 else b
        through = None
        for x, (node, d) in ends.items():
            if node == n and x != e and x in pair:
                through = complex(d[1], -d[0])
                break
        return dict(kind="free" if g.degree(n) == 1 else "junction", center=g.nodes[n]["center"],
                    r=g.nodes[n]["r"], through=through)

    def walk(start):
        pts, cur = [], start
        while True:
            k, side = cur
            a, b, path = g.edges[k]
            p = path if side == 0 else path[::-1]
            n0 = g.nodes[a if side == 0 else b]
            n1 = g.nodes[b if side == 0 else a]
            done.add(k)
            seg = sk.trim(p, n0["center"], n0["r"] * THROUGH, 0.35) if pts else p
            other = (k, 1 - side)
            nxt = pair.get(other)
            if nxt is not None and nxt[0] not in done:
                pts += sk.trim(seg[::-1], n1["center"], n1["r"] * THROUGH, 0.35)[::-1]
                cur = nxt
                continue
            return pts + seg, other

    out = []
    for k, (a, b, path) in g.edges.items():
        if a == b and g.degree(a) == 2:
            # a ring with nothing attached (an o): one closed stroke, with no seam
            done.add(k)
            out.append(dict(px=path[:-1] if path[0] == path[-1] else path, closed=True, start=info((k, 0)),
                            end=info((k, 1))))
    for e in ends:
        if e in pair or e[0] in done:
            continue
        pts, last = walk(e)
        out.append(dict(px=pts, closed=False, start=info(e), end=info(last)))
    for k in list(g.edges):
        if k in done:
            continue
        a, b, _ = g.edges[k]
        start = (k, 0)
        pts, last = walk(start)
        closed = (a == b and g.degree(a) == 2) or pair.get(last) == start
        if closed:
            n = g.nodes[a]
            pts = sk.trim(pts, n["center"], n["r"] * 1.1)
            pts = sk.trim(pts[::-1], n["center"], n["r"] * 1.1)[::-1]
        out.append(dict(px=pts, closed=closed, start=info(start), end=info(last)))
    return [s for s in out if len(s["px"]) >= 2]


def _skeleton(contours, scale: float, headline=None, dot_ratio: float = 3.3, spur: float = 1.7,
              adv: float = 0.0, pair_deg: float = PAIR_DEG) -> dict:
    """Raster, distance, dots, the headline, the skeleton graph and its strokes, for one glyph."""
    sk = _sk()
    np = sk.np
    R = sk.Raster(contours, scale)
    dist = sk.edt(R.ink)
    lab, n = sk.label(R.ink)
    dots, body = [], np.zeros_like(R.ink)
    for i in range(1, n + 1):
        m = lab == i
        rmax = float(dist[m].max())
        rows, cols = np.nonzero(m)
        side = max(rows.max() - rows.min(), cols.max() - cols.min()) + 1
        if side <= dot_ratio * rmax and side < 240 * scale:
            d = 2 * math.sqrt(m.sum() / math.pi) / scale
            dots.append((R.to_font(rows.mean(), cols.mean()), d))
        else:
            body |= m
    heads, band = [], None
    if headline is not None:
        line, half = headline
        runs, band = _headline_runs(sk, body, R, line, half)
        rc = R.row_of(line)
        for c0, c1 in runs:
            # the headline is its own stroke, from the first to the last column of ink on the line
            row = R.ink[int(round(rc)), :]
            a, b = c0, c1
            while a > 0 and row[a - 1]:
                a -= 1
            while b < len(row) - 1 and row[b + 1]:
                b += 1
            heads.append([R.to_font(rc, a), R.to_font(rc, b)])
            body[max(0, band[0] - 1):band[1] + 1, a:b + 1] = False
        if runs:
            lab2, n2 = sk.label(body)
            for i in range(1, n2 + 1):
                m = lab2 == i
                if m.sum() < (half * scale) ** 2 * 1.5:
                    body[m] = False          # crumbs left by the cut
    skel = sk.thin(body)
    # ball terminals: far wider than the usual stroke. Pruning would remove their skeleton,
    # so they are found first and drawn as round dots.
    blobs = []
    if skel.any():
        med = float(np.median(dist[skel]))
        fat = skel & (dist > BLOB * med)
        if fat.any():
            lab3, n3 = sk.label(sk.grow(fat, 3))
            for i in range(1, n3 + 1):
                m = (lab3 == i) & fat
                rr, cc = np.nonzero(m)
                k = int(np.argmax(dist[rr, cc]))
                blobs.append((R.to_font(rr[k], cc[k]), 2 * float(dist[rr[k], cc[k]]) / scale))
    g = sk.Graph(skel, dist)
    cols = [int(round((x - R.x0) * scale + sk.PAD)) for x in (0.0, float(adv))]
    w = R.ink.shape[1]
    hung = band if heads else None

    def keep(px):
        r, c = px
        # a short stub whose row of ink reaches the left or the right edge joins the next letter
        for edge, inward in zip(cols if adv > 0 else [], (1, -1)):
            e = min(w - 1, max(0, edge + inward))
            if abs(c - edge) < 60 * scale and R.ink[r, e] and R.ink[r, min(w - 1, max(0, e + inward * 2))]:
                return True
        # a short stub just under the headline holds the letter to it
        return bool(hung is not None and 0 <= r - hung[1] <= 60 * scale and R.ink[hung[1], c]
                    and R.ink[hung[1]:r + 1, c].all())
    g.prune(spur=spur, keep=keep)
    widths = 2 * dist[skel] / scale
    return dict(raster=R, dist=dist, strokes=_pair_and_walk(sk, g, pair_deg), dots=dots, heads=heads, band=band,
                blobs=blobs, width=float(np.median(widths)) if widths.size else 0.0, skeleton=skel)


def _extend_to_edge(sk, R, pts, from_start, maxlen, span=14):
    """Walk from an end of ``pts`` along its tangent until the ray leaves the ink."""
    p = pts if from_start else pts[::-1]
    d = sk.direction(p, True, 0, span)
    d = (-d[0], -d[1])
    r0, c0 = p[0]
    last = (r0, c0)
    h, w = R.ink.shape
    t = 0.0
    while t < maxlen:
        t += 0.5
        r, c = r0 + d[0] * t, c0 + d[1] * t
        ri, ci = int(round(r)), int(round(c))
        if not (0 <= ri < h and 0 <= ci < w) or not R.ink[ri, ci]:
            break
        last = (r, c)
    return last


def _solid(ink, end, rc) -> bool:
    """The column from ``end`` (row, column) to row ``rc`` is ink all the way."""
    r0, r1 = sorted((int(round(end[0])), int(round(rc))))
    c = int(round(end[1]))
    return bool(ink[r0:r1 + 1, max(0, c - 2):c + 3].all())


def _ray_hit(o, d, a, b):
    """t >= 0 where the ray o + t d crosses the segment a-b, or None."""
    e = b - a
    den = (d.conjugate() * e).imag
    if abs(den) < 1e-9:
        return None
    w = a - o
    t = (w.conjugate() * e).imag / den
    u = (w.conjugate() * d).imag / den
    return t if t >= 0 and -0.02 <= u <= 1.02 else None


def _attach(strokes: list, ink_ahead=None):
    """Run each junction end on along its own direction until it meets the centerline of another stroke.

    Thinning puts a junction where the largest circle fits, which can be far from the stroke the
    end belongs to. Stopping there leaves the end hanging. If no stroke lies ahead but ink does
    (a short stub that pruning removed), the end runs on to the edge of the ink."""
    for si, s in enumerate(strokes):
        for i in (0, 1):
            junction = s.get("junction", (None, None))[i]
            if junction is None:
                continue
            center, r = junction
            pts = s["pts"]
            end = pts[0] if i == 0 else pts[-1]
            inner = pts[min(6, len(pts) - 1)] if i == 0 else pts[max(-7, -len(pts))]
            d = end - inner
            if abs(d) < 1e-6:
                continue
            d /= abs(d)
            best = along = None
            for oi, o in enumerate(strokes):
                q = o["pts"]
                if oi == si:
                    q = q[len(q) // 3: 2 * len(q) // 3] if len(q) > 12 else []
                segs = list(zip(q, q[1:])) + ([(q[-1], q[0])] if o["closed"] and len(q) > 2 else [])
                for a, b in segs:
                    t = _ray_hit(end, d, a, b)
                    if t is not None and t < 4 * r and (best is None or t < best):
                        best, along = t, b - a
            reach = ink_ahead(end, d) if ink_ahead is not None and best is None else 0.0
            if best is not None:
                new = [end + d * (best * 0.5), end + d * best]
                cut = list(s.get("cut", (None, None)))
                cut[i] = along / abs(along) if abs(along) > 1e-9 else cut[i]
                s["cut"] = tuple(cut)
            elif reach > 1.5 * r:
                new = [end + d * (reach * 0.5), end + d * max(0.0, reach - 0.5 * r)]
            else:
                near, nd = center, abs(center - end)
                for oi, o in enumerate(strokes):
                    if oi == si:
                        continue
                    for q in o["pts"]:
                        if abs(q - end) < nd:
                            near, nd = q, abs(q - end)
                new = [near]
            s["pts"] = new[::-1] + pts if i == 0 else pts + new


def trace_glyph(contours: list, advance: float = 0.0, upm: int = 1000, headline=None) -> dict:
    """Trace one shape (contours in font units) into pen-free parts.

    Returns a dict: ``strokes`` (each with ``pts``, a list of points, and ``closed``), ``dots``
    ((center, diameter) pairs), ``blobs`` (ball terminals, the same) and ``width`` (the median stroke
    width). With ``advance``, an end at the left or the right edge counts as a join to the next letter.
    ``headline`` is (height, half thickness) of a line the letters hang from.
    """
    return _prepare(union(contours), advance, SCALE * 1000.0 / upm, headline)


def _prepare(contours, adv: float, scale: float, headline=None, corners: str = "sharp", dense: bool = False) -> dict:
    """Trace one glyph into pen-free strokes in font units."""
    sk = _sk()
    np = sk.np
    tr = _skeleton(contours, scale, headline=headline, adv=adv, pair_deg=PAIR_DEG_DENSE if dense else PAIR_DEG)
    R, dist = tr["raster"], tr["dist"]
    band = tr["band"] if tr["heads"] else None
    rc = R.row_of(headline[0]) if band is not None else None
    skel = tr["skeleton"]
    med_r = float(np.median(dist[skel])) if skel.any() else 1.0
    sharp = corners == "sharp"
    out = []
    for st in tr["strokes"]:
        px = [tuple(map(float, q)) for q in st["px"]]
        if st["closed"]:
            px, marks = sk.sharpen(px, med_r, True, ink=R.ink) if sharp else (px, [])
            pts = sk.smooth_pieces(px, marks, SIGMA, True)
            if sharp and dense:
                pts = sk.straighten(pts, marks, med_r, True)
            out.append(dict(pts=[R.to_font(r, c) for r, c in pts], closed=True, edge=(False, False),
                            corners=[R.to_font(r, c) for r, c in marks]))
            continue
        ends = [dict(st["start"]), dict(st["end"])]
        for i, e in enumerate(ends):
            if e["kind"] == "free":
                # the radius at the very tip is tiny: use the stroke's half width near it
                near = px[:30] if i == 0 else px[-30:]
                e["r"] = max(float(np.median([dist[int(r), int(c)] for r, c in near])), med_r, 2.0)
        # a free end just under the headline, with ink all the way up to it: a stub that holds the letter
        # to the line. It is not trimmed, and it runs straight up to the line.
        hangs = [e["kind"] == "free" and band is not None and 0 <= (px[0] if i == 0 else px[-1])[0] - band[1] < 3 * e["r"]
                 and _solid(R.ink, px[0] if i == 0 else px[-1], rc) for i, e in enumerate(ends)]
        for i, e in enumerate(ends):
            # junction ends: drop the part that bends toward the junction. Free ends: drop the
            # last bit, which veers toward a corner of a slanted cut.
            k = 1.0 if e["kind"] == "junction" else FREE_TRIM
            center = e["center"] if e["kind"] == "junction" else (px[0] if i == 0 else px[-1])
            if sk.path_length(px) < 3 * e["r"] or hangs[i]:
                continue
            px = (sk.trim(px, center, e["r"] * k, 0.3) if i == 0
                  else sk.trim(px[::-1], center, e["r"] * k, 0.3)[::-1])
        if sk.path_length(px) < 3:
            continue
        px, marks = sk.sharpen(px, med_r, False, ink=R.ink) if sharp else (px, [])
        pts = sk.smooth_pieces(px, marks, SIGMA, False)
        if sharp and dense:
            pts = sk.straighten(pts, marks, med_r, False)
        new_ends, at_head = [], [False, False]
        for i, e in enumerate(ends):
            first = i == 0
            end = pts[0] if first else pts[-1]
            if hangs[i]:
                new_ends.append([(rc, end[1])])
                at_head[i] = True
            elif e["kind"] == "free" and band is not None and band[0] - 6 <= end[0] <= band[1] + 6:
                # a stem cut off by the headline: run it on to the headline's centerline
                d = sk.direction(pts if first else pts[::-1], True, 0, max(14, 2 * e["r"]))
                if abs(d[0]) > 0.3:
                    t = (end[0] - rc) / d[0]
                    q = (end[0] - d[0] * t, end[1] - d[1] * t)
                else:
                    q = (rc, end[1])
                new_ends.append([q])
                at_head[i] = True
            elif (e["kind"] == "free" and band is not None
                  and (0 < end[0] - band[1] < 4 * e["r"] or 0 < band[0] - end[0] < 4 * e["r"])
                  and _solid(R.ink, end, rc)):
                # a stub of ink joins this end to the headline: follow it
                new_ends.append([(rc, end[1])])
                at_head[i] = True
            elif e["kind"] == "free":
                new_ends.append([_extend_to_edge(sk, R, pts, first, 4 * max(e["r"], 4), max(14, 2 * e["r"]))])
            else:
                new_ends.append([])          # joined to its stroke below, once every stroke is known
        pts = new_ends[0] + pts + new_ends[1]
        f = [R.to_font(r, c) for r, c in pts]
        edge = []
        for q, e, h in ((f[0], ends[0], at_head[0]), (f[-1], ends[1], at_head[1])):
            edge.append(bool(adv > 0 and e["kind"] == "free" and not h and (q.real <= 8 or q.real >= adv - 8)))
        junction = tuple((R.to_font(*e["center"]), e["r"] / R.s) if e["kind"] == "junction" else None for e in ends)
        cut = tuple(1 + 0j if at_head[i] else (e.get("through") if e["kind"] == "junction" else None)
                    for i, e in enumerate(ends))
        out.append(dict(pts=f, closed=False, edge=tuple(edge), junction=junction, cut=cut,
                        corners=[R.to_font(r, c) for r, c in marks]))
    for a, b in tr["heads"]:
        out.append(dict(pts=[a + (b - a) * t / 8 for t in range(9)], closed=False,
                        edge=(adv > 0 and a.real <= 8, adv > 0 and b.real >= adv - 8),
                        junction=(None, None), cut=(None, None), head=True, corners=[]))

    def ink_ahead(q: complex, d: complex) -> float:
        """How far the ink goes from ``q`` along ``d``, in font units."""
        h, w = R.ink.shape
        t = 0.0
        while t < 400:
            x, y = R.to_px(q + d * (t + 1))
            ri, ci = int(round(y)), int(round(x))
            if not (0 <= ri < h and 0 <= ci < w) or not R.ink[ri, ci]:
                break
            t += 1
        return t

    _attach(out, ink_ahead)
    for s in out:
        s.pop("junction", None)
    # how much the stroke width varies: a brush or a high-contrast face varies a lot
    widths = 2 * dist[skel] / scale
    spread = float(np.percentile(widths, 90) / max(1e-6, np.percentile(widths, 25))) if widths.size > 20 else None
    res = dict(strokes=out, dots=tr["dots"], blobs=tr["blobs"], width=tr["width"], spread=spread, soft=not sharp)
    if dense:
        res["gaps"] = _gaps(sk, R, out, tr["width"])
    return res


def _gaps(sk, R, strokes: list, width: float, step: float = 8.0, reach: float = 260.0) -> list:
    """The white between each stroke and its neighbors, in font units: from points along every centerline,
    across the stroke on both sides, the run of white up to the next ink. A run that starts deep in ink (a
    junction, or along a crossing stroke) or meets no ink (the open side) does not count. Only white between
    strokes that run side by side counts: where the run grows or shrinks fast along the stroke, it is the
    wedge where two strokes meet at an angle, which no pen can keep open. A run narrower than half the stroke
    ``width`` does not count either.

    Returns the number of places measured (two sides of each point), then the widths that count, sorted."""
    np = sk.np
    pts, normals, run = [], [], []
    for si, s in enumerate(strokes):
        q = s["pts"]
        if len(q) < 3:
            continue
        flat = _resample(q, step) if s["closed"] else _resample_open(q, step)
        n = len(flat)
        for i in range(2, n - 2) if not s["closed"] else range(n):
            d = flat[(i + 2) % n] - flat[(i - 2) % n]
            if abs(d) < 1e-6:
                continue
            pts.append(flat[i])
            normals.append(d / abs(d) * 1j)
            run.append(si)
    if not pts:
        return [0]
    P = np.array([R.to_px(q) for q in pts])                          # (x, y) pixels
    N = np.array([(z.real, -z.imag) for z in normals])                # y runs down in the image
    t = np.arange(0.0, reach * R.s, 0.5)
    h, w = R.ink.shape
    dist = sk.edt(R.ink)
    out = []
    for sign in (1.0, -1.0):
        xs = P[:, None, 0] + sign * N[:, None, 0] * t[None, :]
        ys = P[:, None, 1] + sign * N[:, None, 1] * t[None, :]
        ci, ri = np.round(xs).astype(int), np.round(ys).astype(int)
        inside = (ri >= 0) & (ri < h) & (ci >= 0) & (ci < w)
        ink = np.zeros(xs.shape, bool)
        ink[inside] = R.ink[ri[inside], ci[inside]]
        leave = np.argmax(~ink, axis=1)                                # the first white step
        r0 = np.clip(np.round(P[:, 1]).astype(int), 0, h - 1)
        c0 = np.clip(np.round(P[:, 0]).astype(int), 0, w - 1)
        half = dist[r0, c0]
        gap = np.full(len(P), np.nan)
        for k in range(len(P)):
            a = leave[k]
            if not ink[k, 0] or a == 0 or t[a] > 1.6 * half[k] + 2:
                continue
            back = np.nonzero(ink[k, a:])[0]
            if back.size:
                gap[k] = float(t[a + back[0]] - t[a]) / R.s
        for k in range(1, len(P) - 1):
            g, a, b = gap[k], gap[k - 1], gap[k + 1]
            if np.isnan(g) or g < 0.5 * width or run[k - 1] != run[k] or run[k + 1] != run[k]:
                continue
            if not (np.isnan(a) or np.isnan(b)) and abs(b - a) < 0.5 * step:
                out.append(float(g))
    return [len(P) * 2] + sorted(out)


def _headline_half(sk, items: list, line: float, scale: float) -> float:
    """Half the thickness of a headline: the shortest vertical ink runs through the line."""
    np = sk.np
    runs = []
    for contours in items:
        R = sk.Raster(contours, scale)
        rc = int(round(R.row_of(line)))
        if not 0 <= rc < R.ink.shape[0]:
            continue
        for c in np.nonzero(R.ink[rc])[0][::3]:
            col = R.ink[:, c]
            a = b = rc
            while a > 0 and col[a - 1]:
                a -= 1
            while b < len(col) - 1 and col[b + 1]:
                b += 1
            runs.append((b - a + 1) / R.s)
    runs.sort()
    return float(np.median(runs[: max(1, len(runs) // 2)])) / 2 + 3 if runs else 0.0


def _join_line(prepared: dict) -> float | None:
    """The height of the ends that reach a glyph's left or right edge: the baseline of joined Arabic,
    the headline of Devanagari."""
    ys = []
    for g in prepared.values():
        for s in g["strokes"]:
            for i in (0, 1):
                if not s["edge"][i] or len(s["pts"]) < 2:
                    continue
                a = s["pts"][0] if i == 0 else s["pts"][-1]
                b = s["pts"][min(5, len(s["pts"]) - 1)] if i == 0 else s["pts"][max(-6, -len(s["pts"]))]
                t = a - b
                if abs(t) > 1e-6 and abs(t.real) / abs(t) > 0.9:
                    ys.append(a.imag)
    if not ys:
        return None
    ys.sort()
    return float(ys[len(ys) // 2])


def _snap(prepared: dict, adv: dict, line: float):
    """Put every joining end at one height, reaching the glyph's edge, and ease the stroke onto it."""
    for name, g in prepared.items():
        for s in g["strokes"]:
            for i in (0, 1):
                if not s["edge"][i]:
                    continue
                j = 0 if i == 0 else -1
                q = s["pts"][j]
                if abs(q.imag - line) > 40:
                    s["edge"] = tuple(False if k == i else s["edge"][k] for k in (0, 1))
                    continue
                x = min(q.real, 0.0) if q.real < adv[name] / 2 else max(q.real, float(adv[name]))
                s["pts"][j] = complex(x, line)
                reach = 70.0
                idx = range(len(s["pts"])) if i == 0 else range(len(s["pts"]) - 1, -1, -1)
                for m in idx:
                    pt = s["pts"][m]
                    dx = abs(pt.real - x)
                    if dx >= reach:
                        break
                    t = dx / reach
                    w = t * t * (3 - 2 * t)
                    s["pts"][m] = complex(pt.real, line + (pt.imag - line) * w)


# --------------------------------------------------------------------------
# Room: the white that must stay white when the pen is heavier than the source
# --------------------------------------------------------------------------

def _parts(contours: list) -> tuple:
    """(outer contours, holes) of a merged outline."""
    level = depths(contours) if contours else []
    outers = [c for c, d in zip(contours, level) if d % 2 == 0 and abs(contour_area(c)) > 4]
    holes = [c for c, d in zip(contours, level) if d % 2 == 1 and abs(contour_area(c)) > 4]
    return outers, holes


def _gap(sk, a: list, b: list):
    """The shortest distance between two point sets, and the two points."""
    np = sk.np
    A, B = np.array(a), np.array(b)
    d = np.abs(A[:, None] - B[None, :])
    k = int(np.argmin(d))
    i, j = divmod(k, len(B))
    return float(d[i, j]), complex(A[i]), complex(B[j])


def _gap_room(gap: float, p: complex, q: complex, area_p: float, area_q: float) -> tuple:
    """Room entries for the white between two parts.

    Parts of a size share the white. A small part (a dot, a mark) next to a large one takes it
    alone, after the large part has grown as the pen says: the letter keeps its weight."""
    share = (1 - KEEP_GAP) * gap
    if area_p < 0.5 * area_q:
        return [([p], 2 * share, 1.0)], []
    if area_q < 0.5 * area_p:
        return [], [([q], 2 * share, 1.0)]
    return [([p, (p + q) / 2], share, 0.0)], [([q, (p + q) / 2], share, 0.0)]


def _room(sk, contours: list, scale: float, gaps: list | None = None) -> list:
    """Counters and the gaps between parts, as (points, extra width the strokes near them may take,
    and how much of the pen's extra weight the other side takes from that). The white between each
    two parts is also added to ``gaps``, if given."""
    room = []
    outers, holes = _parts(contours)
    for h in holes:
        R = sk.Raster([h], scale)
        rho = float(sk.edt(R.ink).max()) / scale
        room.append((_resample(flatten_contour(h, 2.0), 10.0), 2 * (1 - KEEP_COUNTER) * rho, 0.0))
    pts = [_resample(flatten_contour(c, 2.0), 8.0) for c in outers]
    areas = [abs(contour_area(c)) for c in outers]
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            gap, p, q = _gap(sk, pts[i], pts[j])
            if gaps is not None:
                gaps.append(gap)
            if gap < 400:
                a, b = _gap_room(gap, p, q, areas[i], areas[j])
                room += a + b
    return room


# --------------------------------------------------------------------------
# The whole font, traced
# --------------------------------------------------------------------------

@dataclass
class TracedFont:
    """A source font with the centerlines of its glyphs. Nothing in here depends on a pen."""
    path: Path
    font: TTFont
    glyphs: dict                  # glyph name -> traced glyph
    sources: dict                 # glyph name -> source outline (merged), for every simple glyph
    composites: list              # names of composite glyphs, kept as they are
    marks: set                    # glyph names of the mark class
    width: float                  # median stroke width of the source, in its units
    line: float | None            # the height of joins
    headline: bool
    upm: int
    seconds: float = 0.0
    failed: dict = field(default_factory=dict)
    contrast: float = 1.0         # how much the source's stroke width varies (see CONTRAST_WARN)
    warnings: list = field(default_factory=list)
    cjk: bool = False             # Chinese characters, kana or Hangul: dense, and nothing joins
    corners: str = "sharp"        # "sharp" (rebuilt as points) or "soft" (round)


_SHARED: dict = {}


def _pool_map(fn, items: list, jobs: int | None, chunk: int = 8) -> list:
    """``[fn(x) for x in items]``, in forked worker processes where the platform has them."""
    import multiprocessing
    if jobs is None:
        from .compile import default_jobs
        jobs = default_jobs()
    jobs = min(jobs, max(1, len(items) // chunk))
    if jobs > 1 and "fork" in multiprocessing.get_all_start_methods() and not multiprocessing.current_process().daemon:
        from concurrent.futures import ProcessPoolExecutor
        from concurrent.futures.process import BrokenProcessPool
        try:
            with ProcessPoolExecutor(jobs, mp_context=multiprocessing.get_context("fork")) as pool:
                return list(pool.map(fn, items, chunksize=chunk))
        except (BrokenProcessPool, OSError):
            pass
    return [fn(x) for x in items]


def _trace_job(name):
    s = _SHARED
    try:
        traced = _prepare(s["sources"][name], s["adv"][name], s["scale"], s["headline"], s["corners"], s["dense"])
        if s["room"]:
            apart = [] if s["dense"] else None
            traced["room"] = _room(_sk(), s["sources"][name], s["scale"], apart)
            if apart is not None:
                # the white between separate parts, wider than strokes that almost touch
                traced["apart"] = sorted(g for g in apart if g >= 2 * NEAR * (traced["width"] or 0.0))
        return name, traced, None
    except Exception as exc:          # a glyph that cannot be traced is reported, not fatal
        return name, None, f"{type(exc).__name__}: {exc}"


def _trace_all(names, sources, adv, scale, headline, jobs, room=False, corners="sharp", dense=False) -> tuple:
    _SHARED.update(sources=sources, adv=adv, scale=scale, headline=headline, room=room, corners=corners,
                   dense=dense)
    try:
        done = _pool_map(_trace_job, list(names), jobs)
    finally:
        _SHARED.clear()
    prepared = {n: p for n, p, e in done if p is not None}
    failed = {n: e for n, p, e in done if e is not None}
    return prepared, failed


def subset(font: TTFont, codepoints) -> int:
    """Keep only the glyphs of ``codepoints`` that the font has, and the glyphs its shaping tables reach from
    them, in place. The features that shaping uses stay (``vert``, ``locl``, ``ccmp``, ``palt`` ...); the
    lists of alternates (``aalt`` and the like) go, as they would pull in thousands of glyphs. Returns how many
    of the code points the font has."""
    from fontTools import subset as ftsubset
    cmap = font.getBestCmap() or {}
    keep = sorted(set(codepoints) & set(cmap))
    if not keep:
        raise ValueError("the font has none of the characters that --only asks for")
    opts = ftsubset.Options()
    opts.name_IDs = ["*"]
    opts.name_languages = ["*"]
    opts.name_legacy = True
    opts.notdef_outline = True
    opts.glyph_names = True
    opts.legacy_kern = True
    opts.hinting = False                 # the new glyphs have no hinting anyway
    opts.desubroutinize = True
    opts.ignore_missing_unicodes = True
    sub = ftsubset.Subsetter(opts)
    sub.populate(unicodes=keep)
    import logging
    log = logging.getLogger("fontTools.subset")
    level = log.level
    log.setLevel(logging.ERROR)              # not "meta NOT subset; dropped" for every source
    try:
        sub.subset(font)
    finally:
        log.setLevel(level)
    return len(keep)


def open_font(src, at: dict | None = None, only=None) -> TTFont:
    """Load a font (.ttf or .otf, static or variable). A variable font is cut to one instance (its
    default, or ``at``). With ``only`` (code points), the font keeps just those characters (see
    :func:`subset`). A font with PostScript outlines gets TrueType outlines, which the new glyphs
    replace anyway."""
    font = TTFont(str(src))
    if "fvar" in font:
        from fontTools.varLib import instancer
        loc = {a.axisTag: a.defaultValue for a in font["fvar"].axes}
        loc.update(at or {})
        font = instancer.instantiateVariableFont(font, loc, inplace=False)
    if only is not None:
        subset(font, only)
        buf = io.BytesIO()
        font.save(buf)
        buf.seek(0)
        font = TTFont(buf)
    if "glyf" not in font:
        if "CFF " not in font and "CFF2" not in font:
            raise ValueError("the font has no outlines that whateverfont can read (no glyf or CFF table)")
        _to_truetype(font)
    if font["head"].unitsPerEm != UPM:
        # Inter, Roboto and many others have 2048 units to the em. The tracer's lengths (how large a dot may
        # be, how far a join reaches) are in units of a 1000-unit em, so the source is scaled to that first:
        # its outlines, advances, kerning and anchors together.
        from fontTools.ttLib.scaleUpem import scale_upem
        scale_upem(font, UPM)
    for tag in font.keys():
        font[tag]                    # read every table now: the glyph order changes later
    return font


def _to_truetype(font: TTFont):
    """Replace PostScript (CFF) outlines with TrueType ones, in place."""
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable
    order = font.getGlyphOrder()
    gs = font.getGlyphSet()
    glyphs = {}
    for n in order:
        pen = TTGlyphPen(None)
        gs[n].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyphs[n] = pen.glyph()
    glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = glyphs
    for tag in ("CFF ", "CFF2", "VORG"):
        if tag in font:
            del font[tag]
    font["glyf"] = glyf
    font["loca"] = newTable("loca")
    maxp = font["maxp"]
    maxp.tableVersion = 0x00010000
    for attr in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
                 "maxStackElements", "maxSizeOfInstructions", "maxComponentElements", "maxComponentDepth",
                 "maxPoints", "maxContours", "maxCompositePoints", "maxCompositeContours"):
        setattr(maxp, attr, 1 if attr == "maxZones" else 0)
    font["head"].indexToLocFormat = 0
    font["head"].glyphDataFormat = 0
    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = order
    font.sfntVersion = "\x00\x01\x00\x00"


#: Unicode blocks of East Asian scripts: Hangul jamo, kana, Hangul compatibility jamo, the CJK ideographs and
#: their extensions, Hangul syllables, compatibility ideographs and the supplementary ideographs
EAST_ASIAN_BLOCKS = ((0x1100, 0x11FF), (0x3040, 0x30FF), (0x3130, 0x318F), (0x31F0, 0x31FF), (0x3400, 0x4DBF),
                     (0x4E00, 0x9FFF), (0xA960, 0xA97F), (0xAC00, 0xD7FF), (0xF900, 0xFAFF), (0x20000, 0x3FFFF))
CORNER_SHARE = 0.4      # a source with more of its outline nodes at sharp corners than this is type, not a hand


def east_asian(cmap: dict) -> bool:
    """Most of the characters are Chinese characters, kana or Hangul: each sits alone in a square, and nothing
    joins."""
    cps = list(cmap)
    hits = sum(1 for cp in cps if any(a <= cp <= b for a, b in EAST_ASIAN_BLOCKS))
    return bool(cps) and hits > 0.5 * len(cps)


def corner_share(gs, names: list) -> float:
    """The share of the outline nodes of ``names`` where the outline turns sharply (more than 45 degrees).
    Type has corners at most of its nodes; a handwritten or brush face has round ends and curves."""
    corners = nodes = 0
    for n in names:
        rec = DecomposingRecordingPen(gs)
        gs[n].draw(rec)
        prev = prev_dir = None
        for op, args in rec.value:
            if op == "moveTo":
                prev, prev_dir = complex(*args[0]), None
                continue
            pts = [complex(*a) for a in args if a is not None]
            if op in ("closePath", "endPath") or not pts or prev is None:
                continue
            out_dir = pts[0] - prev
            in_dir = pts[-1] - (pts[-2] if len(pts) > 1 else prev)
            if prev_dir is not None and abs(prev_dir) > 1e-6 and abs(out_dir) > 1e-6:
                turn = prev_dir.conjugate() * out_dir
                nodes += 1
                corners += abs(math.degrees(math.atan2(turn.imag, turn.real))) > 45
            prev_dir, prev = in_dir, pts[-1]
    return corners / nodes if nodes else 1.0


def trace_font(src, headline: bool | None = None, at: dict | None = None, jobs: int | None = None,
               only=None, corners: str = "auto") -> TracedFont:
    """Trace every glyph of ``src`` that has an outline of its own.

    Composite glyphs are not traced: they keep pointing at their parts, which are. ``headline``
    says whether the script hangs from a line (Devanagari); None decides from the font. ``only``
    (code points, see :mod:`whateverfont.charsets`) keeps just those characters and what the shaping
    tables reach from them. ``corners`` is "sharp" (corners rebuilt as points, for type), "soft" (round,
    for a handwritten source) or "auto": for Japanese, Chinese and Korean decided from the source's
    outlines, sharp for other scripts.
    """
    sk = _sk()
    np = sk.np
    t0 = time.time()
    if corners not in ("auto", "sharp", "soft"):
        raise ValueError(f"corners must be auto, sharp or soft, not {corners!r}")
    font = open_font(src, at, only)
    upm = font["head"].unitsPerEm
    scale = SCALE * 1000.0 / upm
    glyf, hmtx = font["glyf"], font["hmtx"]
    gs = font.getGlyphSet()
    order = font.getGlyphOrder()
    composites = [n for n in order if glyf[n].isComposite()]
    simple = [n for n in order if n != ".notdef" and not glyf[n].isComposite() and glyf[n].numberOfContours > 0]
    sources = {}
    for n in simple:
        merged = union(glyph_contours(gs, n))
        if merged:
            sources[n] = merged
    adv = {n: hmtx[n][0] for n in order}
    marks = set()
    gdef = font["GDEF"].table if "GDEF" in font else None
    if gdef is not None and gdef.GlyphClassDef is not None:
        marks = {n for n, c in gdef.GlyphClassDef.classDefs.items() if c == 3}

    cmap = font.getBestCmap() or {}
    letters = sorted({n for cp, n in cmap.items() if n in sources and adv[n] > 0 and chr(cp).isalpha()})
    sample = letters[:: max(1, len(letters) // 80)]
    cjk = east_asian(cmap)
    if corners == "auto":
        corners = "sharp" if not cjk or corner_share(gs, sample) > CORNER_SHARE else "soft"
    if cjk:
        # Each character sits alone in its square: no joins to the next one, and no headline.
        line, head, headline = None, None, False
        prepared, failed = _trace_all(list(sources), sources, {n: 0.0 for n in adv}, scale, None, jobs,
                                      room=True, corners=corners, dense=True)
    else:
        # A first look at the letters finds the height of the joins. A line high above the
        # baseline is a headline, and the headline is traced on its own.
        first, _ = _trace_all(sample, sources, adv, scale, None, jobs, corners=corners)
        line = _join_line(first)
        if headline is None:
            # Only a script that has a headline can have one. In a Latin font the ends that reach a glyph's
            # edge at the x-height (a dash, an arrow, a ligature) are not a line that the letters hang from.
            hangs = any(lo <= cp <= hi for cp in cmap for lo, hi in HEADLINE_SCRIPTS)
            headline = hangs and line is not None and line > 0.4 * upm
        head = None
        if headline and line is not None:
            head = (line, _headline_half(sk, [sources[n] for n in sample], line, scale))
        prepared, failed = _trace_all(list(sources), sources, adv, scale, head, jobs, room=True, corners=corners)
        line = _join_line(prepared) if line is None or not headline else line
    if line is not None:
        _snap(prepared, adv, line)
    for n, g in prepared.items():
        g["mark"] = n in marks
    _composite_room(sk, font, gs, prepared, sources, composites)
    widths = [g["width"] for n, g in prepared.items() if g["width"] and n not in marks]
    width = float(np.median(widths)) if widths else 0.0
    spreads = [g["spread"] for n, g in prepared.items() if g.get("spread") and n not in marks]
    contrast = float(np.median(spreads)) if spreads else 1.0
    warnings = []
    if contrast > CONTRAST_WARN:
        warnings.append(f"the source's strokes vary a lot in width (the wide parts are {contrast:.1f} times the "
                        "narrow ones). The tracer follows strokes of even width: a brush or high-contrast source "
                        "comes out lumpy, with broken joins. A source with thin, even strokes works best")
    return TracedFont(Path(src), font, prepared, sources, composites, marks, width, line, bool(headline), upm,
                      time.time() - t0, failed, contrast, warnings, cjk, corners)


def _composite_room(sk, font, gs, prepared, sources, composites):
    """The white between the parts of a composite (a letter and its dots) belongs to the parts."""
    glyf = font["glyf"]
    for n in composites:
        parts = []
        for comp in glyf[n].components:
            if comp.glyphName not in prepared or getattr(comp, "transform", None) is not None:
                continue
            off = complex(comp.x, comp.y)
            outline = [transform_contour(c, lambda q, off=off: q + off) for c in sources[comp.glyphName]]
            outers = _parts(outline)[0]
            parts.append((comp.glyphName, off, [_resample(flatten_contour(c, 2.0), 8.0) for c in outers],
                          sum(abs(contour_area(c)) for c in outers)))
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                (na, oa, pa, area_a), (nb, ob, pb, area_b) = parts[i], parts[j]
                a = [q for c in pa for q in c]
                b = [q for c in pb for q in c]
                if not a or not b or na == nb:
                    continue
                gap, p, q = _gap(sk, a, b)
                if gap < 400:
                    ra, rb = _gap_room(gap, p, q, area_a, area_b)
                    prepared[na]["room"] += [([x - oa for x in pts], extra, other) for pts, extra, other in ra]
                    prepared[nb]["room"] += [([x - ob for x in pts], extra, other) for pts, extra, other in rb]


# --------------------------------------------------------------------------
# Drawing with a pen
# --------------------------------------------------------------------------

def _bezier(sk, fpts, closed, eps, corner_deg=55.0, force=(), fit=None):
    """Dense points in font units -> (nodes, handles, corners). With ``fit``, no curve strays farther than
    that from the points."""
    keep = sorted({i for i, q in enumerate(fpts) for c in force if abs(q - c) < 1e-6})
    # A ring is simplified with its first point repeated at the end, so that the closing piece runs back to
    # the first point itself. Without it the last point (one step before the first, often a corner) would
    # be a node with a tangent from the far side of that corner, and the closing curve would bulge.
    seq = fpts + fpts[:1] if closed else fpts
    if keep:
        cuts = sorted(set([0] + keep + [len(seq) - 1]))
        idx = []
        for a, b in zip(cuts, cuts[1:]):
            part = sk.rdp([(q.real, q.imag) for q in seq[a:b + 1]], eps)
            idx.extend(a + j for j in part if not idx or a + j > idx[-1])
    else:
        idx = sk.rdp([(q.real, q.imag) for q in seq], eps)
    if closed:
        idx = [i for i in idx if i < len(fpts)]
    n = len(fpts)

    def tangent(i):
        if closed:
            d = fpts[(i + 4) % n] - fpts[(i - 4) % n]
        else:
            d = fpts[min(n - 1, i + 4)] - fpts[max(0, i - 4)]
        return d / abs(d) if abs(d) > 1e-9 else 1 + 0j

    def build(idx):
        nodes = [fpts[i] for i in idx]
        tans = [tangent(i) for i in idx]
        corners = [i in keep for i in idx]
        m = len(nodes)
        for j in range(m):
            if not closed and (j == 0 or j == m - 1):
                continue
            a, b = nodes[j] - nodes[j - 1], nodes[(j + 1) % m] - nodes[j]
            if abs(a) < 1e-9 or abs(b) < 1e-9:
                continue
            ang = abs(math.degrees(math.atan2((a.conjugate() * b).imag, (a.conjugate() * b).real)))
            if ang > corner_deg and min(abs(a), abs(b)) > 6:
                corners[j] = True
        handles = []
        for j in range(m if closed else m - 1):
            p, q = nodes[j], nodes[(j + 1) % m]
            third = abs(q - p) / 3
            chord = (q - p) / (abs(q - p) or 1)
            t0 = chord if corners[j] or (not closed and j == 0 and m == 2) else tans[j]
            t1 = chord if corners[(j + 1) % m] else tans[(j + 1) % m]
            handles.append((p + t0 * third, q - t1 * third))
        return nodes, handles, corners

    # A long curve that leaves a round turn takes the turn's tangent and can bow far from the points it
    # stands for (the side of a handwritten 月 after its corner). Such a curve is split at its middle point.
    for _ in range(4):
        nodes, handles, corners = build(idx)
        if fit is None:
            break
        split = []
        for j, (h0, h1) in enumerate(handles):
            a, b = idx[j], (idx[j + 1] if j + 1 < len(idx) else n)
            if b - a < 4:
                continue
            p, q = nodes[j], nodes[(j + 1) % len(nodes)]
            dense = [fpts[i % n] for i in range(a, b + 1)]
            worst = 0.0
            for t in (0.25, 0.5, 0.75):
                u = 1 - t
                c = u ** 3 * p + 3 * u * u * t * h0 + 3 * u * t * t * h1 + t ** 3 * q
                worst = max(worst, min(abs(c - d) for d in dense))
            if worst > fit:
                split.append((a + b) // 2)
        if not split:
            break
        idx = sorted(set(idx) | {i % n for i in split})
    return nodes, handles, corners


def _crosses(a: complex, b: complex, c: complex, d: complex) -> bool:
    """The segments a-b and c-d cross."""
    def side(p, q, r):
        return ((q - p).conjugate() * (r - p)).imag
    return side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0


def _uncrossed(pts: list, closed: bool, step: int = 3, overlap: int = 4) -> list:
    """Split a stroke that crosses itself (a loop like ∞, a handwritten loop) into pieces that do not.

    The pen draws a stroke as one outline, and the two halves of a self-crossing outline cancel where
    they wind opposite ways. The pieces overlap by a few points, so they join with no seam.
    Returns [(points, closed)]."""
    n = len(pts)
    if n < 4 * step:
        return [(pts, closed)]
    seq = pts + [pts[0]] if closed else pts
    idx = list(range(0, len(seq), step))
    if idx[-1] != len(seq) - 1:
        idx.append(len(seq) - 1)
    cuts, start = [], 0
    for j in range(2, len(idx) - 1):
        a, b = seq[idx[j]], seq[idx[j + 1]]
        for i in range(start, j - 1):
            if _crosses(seq[idx[i]], seq[idx[i + 1]], a, b):
                cuts.append(idx[j])
                start = j
                break
    if not cuts:
        return [(pts, closed)]
    bounds = [0] + cuts + [len(seq) - 1]
    return [(seq[max(0, lo - overlap):min(len(seq), hi + overlap + 1)], False) for lo, hi in zip(bounds, bounds[1:])]


def _allowed(room: list, p: complex, base: float, half: float) -> float:
    """The widest stroke (or dot) at ``p`` that leaves the white around it open."""
    best = math.inf
    for pts, extra in room:
        t = min(abs(p - q) for q in pts)
        if t > half * 1.6 + 2 * max(extra, 0.0) + 40:
            continue
        best = min(best, base + extra + max(0.0, t - half * 1.2) * 1.5)
    return best


@dataclass
class Pen:
    """How heavy a family's pen draws a traced font."""
    p: object                     # Params
    k: float                      # pen units per source unit
    width: float                  # source stroke width, in pen units
    stem: float                   # the pen's stem, in pen units
    cap: float = 1.0              # the share of the stem a dense font is drawn at, at most (see dense_cap)

    def grow(self, share: float) -> float:
        """How much wider than the source a part gets, if it takes ``share`` of the pen's extra weight."""
        return (self.stem - self.width) * (share if self.stem > self.width else 1.0)


def _split_stroke(s: Stroke) -> tuple | None:
    """Two strokes that together draw ``s``, cut in the middle of its longest segment. They overlap a
    little, so that no edge of one lies exactly on an edge of the other."""
    import dataclasses
    n = len(s.nodes)
    segs = n if s.closed else n - 1
    if segs < 2 or s.closed:
        return None
    j = max(range(segs), key=lambda i: abs(s.nodes[i + 1].p - s.nodes[i].p))
    a, b, h = s.nodes[j], s.nodes[j + 1], s.handles[j]
    c1, c2 = (h if h is not None else (a.p + (b.p - a.p) / 3, a.p + 2 * (b.p - a.p) / 3))

    def cut(t0, t1):
        """The piece of segment j from t0 to t1: (start, handle, handle, end)."""
        def at(t):
            u = 1 - t
            return u ** 3 * a.p + 3 * u * u * t * c1 + 3 * u * t * t * c2 + t ** 3 * b.p

        def d(t):
            u = 1 - t
            return 3 * (u * u * (c1 - a.p) + 2 * u * t * (c2 - c1) + t * t * (b.p - c2))
        k = (t1 - t0) / 3
        return at(t0), at(t0) + d(t0) * k, at(t1) - d(t1) * k, at(t1)

    mid = lambda p, t: dataclasses.replace(a, p=p, w=a.w + (b.w - a.w) * t, corner=False, apex=None)
    p0, h1, h2, p1 = cut(0.0, 0.53)
    first = dataclasses.replace(s, nodes=s.nodes[:j + 1] + [mid(p1, 0.53)],
                                handles=list(s.handles[:j]) + [(h1, h2)], end=Cap())
    q0, g1, g2, q1 = cut(0.47, 1.0)
    second = dataclasses.replace(s, nodes=[mid(q0, 0.47)] + s.nodes[j + 1:],
                                 handles=[(g1, g2)] + list(s.handles[j + 1:]), start=Cap())
    return first, second


def _stroke_outline(s: Stroke, g: G, depth: int = 0) -> list:
    """The merged outline of one stroke. A stroke whose outline touches itself (a box drawn as one
    stroke, its end on its start) can fail to merge; it is cut in two and each half is merged."""
    from . import outline
    from .stroke import expand
    cs = expand(s, g.pen, g.p.roundness, False)
    before = len(outline.trouble)
    merged = union(cs)
    if len(outline.trouble) == before:
        return merged
    del outline.trouble[before:]
    halves = _split_stroke(s) if depth < 3 else None
    if halves is None:
        return _union_flat(cs)
    return [c for h in halves for c in _stroke_outline(h, g, depth + 1)]


def _union_flat(contours: list) -> list:
    """Merge contours that skia cannot merge as curves: as polygons of short lines, which it can. The last
    resort, for a few glyphs: the result has many more points."""
    from . import outline
    flat = []
    for c in contours:
        pts = flatten_contour(c, 0.5)
        if len(pts) >= 3:
            flat.append([(a, b) for a, b in zip(pts, pts[1:] + pts[:1]) if abs(b - a) > 1e-9])
    before = len(outline.trouble)
    merged = union(flat)
    if len(outline.trouble) == before:
        return merged
    return contours                  # unmerged; union has said so in outline.trouble


def _outlines_by_stroke(g: G, keep_structure: bool = False) -> list:
    """Like ``G.outlines``, but each stroke is merged on its own first.

    A heavy pen on a tight curve of a traced line folds the inner edge back. Merged alone, the fold
    vanishes; merged with every other stroke, its reversed winding would cut a hole in the stroke it
    overlaps (the stem through a handwritten loop)."""
    from .stroke import clean, expand, fillet
    out, groups, probes = [], [], []
    for s in g.strokes:
        if keep_structure:
            out.extend(expand(s, g.pen, g.p.roundness, True))
        else:
            groups.append(_stroke_outline(s, g))
            probes.append(_midpoints(s))
            out.extend(groups[-1])
    for kind, contour, radii in g.shapes:
        if radii is not None:
            c = fillet(contour, list(radii), keep_structure)
            contour = c if keep_structure else clean(c)
        out.append(contour)
        box = contour_bounds([contour])
        groups.append([contour])
        probes.append([complex((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)] if box else [])
    if getattr(g, "nudge", 0.0) and not keep_structure:
        from .outline import dilate
        out = dilate(union(out), g.nudge)      # a second try for an effect that failed: edges that coincided move apart
    elif getattr(g, "many", False) and not keep_structure:
        out = _merge_one_by_one(groups, probes)
    return out


def _midpoints(s: Stroke) -> list:
    """Points on the centerline of a stroke, well inside its outline: the middle of each segment."""
    out = []
    n = len(s.nodes)
    for j, h in enumerate(s.handles):
        p, q = s.nodes[j].p, s.nodes[(j + 1) % n].p
        out.append((p + q) / 2 if h is None else (p + 3 * h[0] + 3 * h[1] + q) / 8)
    return out


def _merge_one_by_one(groups: list, probes: list) -> list:
    """Merge a glyph of many strokes (each a list of contours, with points on its centerline in ``probes``).
    If skia cannot merge them all at once, they are merged one stroke at a time, and a stroke that still fails
    is merged again as polygons of short lines. (Growing a stroke by half a unit, as an effect's second try
    does, can send skia into an endless loop on these outlines.) Unmerged overlaps would fill as
    they should, but the self-check and the effects need one clean outline.

    Skia can also drop a stroke and say nothing (the long stroke of a handwritten 水): a merge is good only if
    every centerline point of its strokes is inside it."""
    from . import outline
    from .effects import inside

    def merge(parts: list, points: list, flat: bool = False):
        """The union of ``parts`` (lists of contours), or None if it failed or lost one of them."""
        mark = len(outline.trouble)
        both = [c for cs in parts for c in cs]
        new = _union_flat(both) if flat else union(both)
        failed = len(outline.trouble) > mark or (flat and new is both)
        del outline.trouble[mark:]
        if failed or not new:
            return None
        test = inside(new)
        return new if all(test(q) for q in points) else None

    points = [q for ps in probes for q in ps]
    merged = merge(groups, points)
    if merged is not None:
        return merged
    acc, seen, aside = [], [], []
    for cs, ps in zip(groups, probes):
        if not acc:
            acc, seen = cs, list(ps)
            continue
        new = merge([acc, cs], seen + ps)
        if new is None:
            new = merge([acc, cs], seen + ps, flat=True)       # the glyph so far and this stroke as polygons
        if new is not None:
            acc, seen = new, seen + ps
        else:
            aside += cs
    return acc + aside


def density(traced: dict, pen: Pen) -> tuple:
    """How thick the pen may draw a dense character (a share of its stem), and whether the white between its
    strokes still fills in at the thinnest pen allowed.

    A heavy pen on a character with many strokes (想, 意, 議) closes the white between them. The pen is thinned
    for the whole character, so that ``DENSE_KEEP`` of the narrow white stays. The narrow white is the
    width that ``DENSE_SAMPLE`` percent of the stroke sides face or less (see :func:`_gaps`): a kana with
    one narrow turn is not thinned for it. The white between two separate parts counts too, however
    short: the dakuten of ザ must not run into the kana. The pen is never thinner than ``DENSE_FLOOR`` of
    the stem."""
    share = _room_share(traced, pen)
    if share is None:
        return 1.0, False
    want = share
    share = min(share, pen.cap)
    if share >= 1.0:
        return 1.0, False
    base = (traced.get("width") or pen.width / pen.k) * pen.k
    floor = max(DENSE_FLOOR, min(1.0, base / pen.stem))
    if share >= floor:
        return share, False
    # at the floor, the narrow white keeps (narrow - (floor * stem - base)); it fills in below DENSE_FILL of it
    narrow = (want * pen.stem - base) / (1 - DENSE_KEEP)
    left = narrow - (floor * pen.stem - base)
    return floor, left < DENSE_FILL * narrow


def _room_share(traced: dict, pen: Pen):
    """The share of the pen's stem that leaves ``DENSE_KEEP`` of a dense character's narrow white open (more
    than 1 if the full pen does), or None for a glyph that was not measured."""
    gaps = traced.get("gaps")
    if not gaps or pen.stem <= pen.width:
        return None
    k = pen.k
    places, gaps = gaps[0], gaps[1:]
    rank = int(places * DENSE_SAMPLE / 100)
    narrow = min(gaps[rank] if rank < len(gaps) else math.inf, (traced.get("apart") or [math.inf])[0]) * k
    base = (traced.get("width") or pen.width / k) * k
    return (base + (1 - DENSE_KEEP) * narrow) / pen.stem       # the white left is narrow - (pen - base)


def dense_cap(traced: TracedFont, pen: Pen) -> float:
    """How thick a heavy pen draws a whole dense font, as a share of its stem: the share its median character
    allows (see :func:`density`). Simple characters are drawn this thick too, so that a kana does not stand
    out twice as dark as the kanji next to it."""
    shares = sorted(min(1.0, s) for s in (_room_share(g, pen) for g in traced.glyphs.values()) if s is not None)
    if not shares:
        return 1.0
    return max(DENSE_FLOOR, shares[len(shares) // 2])


def paint(g: G, traced: dict, pen: Pen):
    """Add the strokes and dots of one traced glyph to a builder, in the pen's units."""
    import types
    g.outlines = types.MethodType(_outlines_by_stroke, g)
    k = pen.k
    sk = _sk()
    mark = traced.get("mark", False)
    thin, _ = density(traced, pen)
    g.many = "gaps" in traced                  # a dense character: merged carefully (see _merge_one_by_one)
    if thin < 1.0:
        pen = Pen(pen.p, pen.k, pen.width, pen.stem * thin)
    # the other side of a gap may be a letter that grows as the pen says
    body = max(0.0, pen.stem - pen.width)
    room = [([q * k for q in pts], extra * k - other * body) for pts, extra, other in traced.get("room", [])]
    base = (traced.get("width") or pen.width / k) * k
    stem = pen.stem
    scale = thin
    if mark and stem > pen.width:
        scale = thin * (pen.width + pen.grow(MARK_GROW)) / stem
    eff = pen.stem * scale / thin
    floor = min(1.0, base / eff) if eff > 0 else 1.0
    # Curves are fitted closely in dense characters only: the Arabic and Devanagari fonts were reviewed as
    # they are drawn without it.
    fit = FIT * k if g.many else None
    for s in traced["strokes"]:
        corners_at = [q * k for q in s.get("corners", ())]
        pieces = _uncrossed([q * k for q in s["pts"]], s["closed"])
        for n_piece, (pts, closed) in enumerate(pieces):
            nodes, handles, corners = _bezier(sk, pts, closed, eps=2.5 * k, force=corners_at, fit=fit)
            if len(nodes) < 2:
                continue
            ns = []
            for q, c in zip(nodes, corners):
                w = 1.0
                if room and eff > base:
                    w = max(floor, min(1.0, _allowed(room, q, base, base / 2) / eff))
                ns.append(Node(q, w, None, True if c else None))
            if closed:
                st = Stroke(ns, handles, True, Cap(), Cap(), scale, None, True, 2.0, "trace")
            else:
                # the stroke's own ends keep their cuts; where it was split, the pieces overlap
                first, last = n_piece == 0 and not s["closed"], n_piece == len(pieces) - 1 and not s["closed"]
                cut = s.get("cut", (None, None))
                c0 = (Cap(V, 0.0) if s["edge"][0] else (Cap(cut[0], 0.0) if cut[0] is not None else Cap())) \
                    if first else Cap()
                c1 = (Cap(V, 0.0) if s["edge"][1] else (Cap(cut[1], 0.0) if cut[1] is not None else Cap())) \
                    if last else Cap()
                st = Stroke(ns, handles, False, c0, c1, scale, None, True, 2.0, "trace")
            g.strokes.append(st)
    share = MARK_GROW if mark else DOT_GROW
    # The source's dots are measured as circles. g.dot draws a round dot 8% larger, and a square dot of
    # the same width reaches farther at its corners: both are sized to the circle's area instead, so
    # that dots in a row or a triangle keep the white between them.
    shape = g.p.dot if g.p.dot in ("round", "square", "diamond") else "round"
    swell = {"round": 1.08, "square": 1.12}.get(shape, 1.0)
    for c, d in traced["dots"]:
        c, d = c * k, d * k
        grown = d + pen.grow(share)
        if room:
            grown = min(grown, _allowed(room, c, d, d / 2))
        g.dot(c.real, c.imag, max(grown, min(d, eff) * 0.9, 1.0) / swell)
    for c, d in traced.get("blobs", []):
        c, d = c * k, d * k
        grown = d + pen.grow(share)
        if room:
            grown = min(grown, _allowed(room, c, d, d / 2))
        g.dot(c.real, c.imag, max(grown, eff * 1.1) / 1.08, shape="round")


def make_pen(traced: TracedFont, params) -> Pen:
    k = params.upm / traced.upm
    g = G(params, "n", "lower")
    return Pen(params, k, traced.width * k, g.sw)


# --------------------------------------------------------------------------
# The self-check
# --------------------------------------------------------------------------

def check(source: list, drawn: list, scale: float = SCALE, width: float | None = None, near: float = 0.0) -> list:
    """What a redrawn glyph lost, compared with its source. Both are merged outlines in the same units.

    Flags: a part of the source's centerline that the new ink does not cover, a counter that
    closed, two parts that merged, and a stroke that broke in two. With ``near``, two parts of the
    source closer than twice that already count as one: strokes that almost touch (common in Chinese
    characters, and in handwriting) may touch.
    """
    sk = _sk()
    np = sk.np
    problems = []
    src_out, src_holes = _parts(source)
    new_out, new_holes = _parts(drawn)
    joined = len(src_out)
    if near > 0 and len(src_out) > len(new_out):
        from .outline import dilate
        joined = len(_parts(dilate(source, near))[0])
    least = ((width or 40.0) * 0.25) ** 2
    src_holes = [h for h in src_holes if abs(contour_area(h)) > least]
    new_holes = [h for h in new_holes if abs(contour_area(h)) > least * 0.25]
    if len(new_holes) < len(src_holes):
        problems.append(f"{len(src_holes) - len(new_holes)} counter(s) closed")
    if len(new_out) < joined:
        problems.append(f"{joined - len(new_out)} part(s) merged into others")
    elif len(new_out) > len(src_out):
        problems.append(f"broke into {len(new_out) - len(src_out)} more part(s)")
    if source and drawn:
        pts = [q for c in source + drawn for q in flatten_contour(c, 2.0)]
        box = (min(q.real for q in pts), min(q.imag for q in pts), max(q.real for q in pts), max(q.imag for q in pts))
        a = sk.Raster(source, scale, box).ink
        b = sk.Raster(drawn, scale, box).ink
        h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
        a, b = a[:h, :w], b[:h, :w]
        line = sk.thin(a)
        total = int(line.sum())
        if total > 10:
            covered = int((line & sk.grow(b, 2)).sum())
            share = covered / total
            if share < 0.92:
                problems.append(f"the new ink misses {100 * (1 - share):.0f}% of the source's centerline")
    return problems


# --------------------------------------------------------------------------
# Drawing every glyph, with an effect
# --------------------------------------------------------------------------

def uncover_small_parts(shape: list, layers: list, stem: float, letter: str, most: float = 0.6) -> list:
    """Give a small part of a letter (a dot, a short mark) its own color back where the layers drawn
    over the letter would cover more than ``most`` of it. Snow on a dot would make the dot all snow.

    ``letter`` is the key of the layer that holds the letter: the layers after it are the ones that cover
    it. Only an effect that names its letter layer asks for this (``g.letter_layer``, as snow does). For
    paint, tiles, dots or bands, a dot keeps the effect like every other stroke."""
    from .outline import difference, dilate, intersection
    area = lambda cs: sum(-contour_area(c) for c in cs)
    keys = [key for key, _ in layers]
    if area(shape) <= 0 or letter not in keys:
        return layers
    above = [i for i in range(keys.index(letter) + 1, len(layers)) if layers[i][1]]
    if not above:
        return layers
    outers, _ = _parts(shape)
    small = []
    for c in outers:
        b = contour_bounds([c])
        if b and max(b[2] - b[0], b[3] - b[1]) < 2.4 * stem:
            small.append(c)
    if not small:
        return layers
    cover = union([c for i in above for c in layers[i][1]])
    clear = []
    for part in small:
        piece = union([part] + [h for h in shape if _inside_part(h, part)])
        own = area(piece)
        if own > 0 and area(intersection(piece, cover)) > most * own:
            clear += piece
    if not clear:
        return layers
    cut = dilate(clear, max(2.0, stem * 0.04))
    out = list(layers)
    for i in above:
        key, cs = out[i]
        out[i] = (key, difference(cs, cut))
    return out


def _inside_part(hole: list, part: list) -> bool:
    """A counter that lies in ``part``."""
    if contour_area(hole) <= 0:
        return False
    b, h = contour_bounds([part]), contour_bounds([hole])
    return bool(b and h and b[0] <= h[0] and b[1] <= h[1] and h[2] <= b[2] and h[3] <= b[3])


def _draw_job(name):
    s = _SHARED
    traced, pen, recipes, plain = s["traced"], s["pen"], s["recipes"], s["plain"]
    k = pen.k
    back = (lambda q: q / k) if k != 1 else None
    from .effects import ink
    err = None
    layers = []
    try:
        try:
            g = recipes._run(recipes[name], pen.p)
        except Exception:
            if recipes is plain:
                raise
            # skia-pathops fails on edges that lie exactly on each other: try once more with the
            # outline grown by a fraction of a unit
            nudged = Recipes()
            nudged[name] = Recipe(name, lambda g, fn=recipes[name].fn: (setattr(g, "nudge", 0.6), fn(g)), None,
                                  "lower")
            g = nudged._run(nudged[name], pen.p)
        shape = ink(g)
        layers = g.layers
    except Exception as exc:          # an effect that fails leaves this glyph plain
        err = f"{type(exc).__name__}: {exc}"
        try:
            g = plain._run(plain[name], pen.p)
            shape = ink(g)
        except Exception as exc2:
            return name, [], [], [], f"{type(exc2).__name__}: {exc2}", None
    letter = getattr(g, "letter_layer", None) if layers else None
    if letter and shape:
        try:
            layers = uncover_small_parts(shape, layers, pen.stem, letter)
        except Exception:
            pass                       # a boolean operation that fails leaves the layers as the effect made them
    if back:
        shape = [transform_contour(c, back) for c in shape]
        layers = [(key, [transform_contour(c, back) for c in cs]) for key, cs in layers]
    problems = []
    if s["check"]:
        try:
            problems = check(traced.sources[name], shape, SCALE * 1000.0 / traced.upm, traced.width,
                             near=NEAR * traced.width if traced.cjk else 0.0)
        except Exception as exc:
            problems = [f"could not be checked ({type(exc).__name__})"]
        thin, fills = density(traced.glyphs[name], pen)
        if fills:
            problems.append(f"too dense for this pen: drawn at {100 * thin:.0f}% of the stem, the white between "
                            "its strokes still fills in")
    return name, shape, layers, problems, None, err


@dataclass
class Result:
    """What :func:`redraw` wrote and found."""
    name: str
    ttf: Path
    woff2: Path
    css: Path
    traced: int
    composites: int
    flagged: dict                  # glyph name -> problems
    failed: dict                   # glyph name -> error: drawn empty
    plain: dict                    # glyph name -> error: the effect failed, so the glyph has no color
    notes: list
    seconds: float
    color_glyphs: int = 0


def load_family(spec: str):
    """``PROJECT[:FAMILY]``: a family of a project folder (default: its first family)."""
    from . import project
    path, sep, name = str(spec).partition(":")
    if sep and len(path) == 1:                 # a Windows drive letter, C:\...
        drive, _, rest = name.partition(":")
        path, name = f"{path}:{drive}", rest
    proj = project.load(path)
    if not name:
        return proj.family
    for fam in proj.families:
        if fam.name.lower() == name.lower():
            return fam
    raise ValueError(f"no family named {name!r} in {path}; it has: {', '.join(f.name for f in proj.families)}")


def _options(text: str) -> dict:
    out = {}
    for part in (text or "").split(","):
        if part.strip():
            key, _, value = part.partition("=")
            try:
                out[key.strip()] = float(value)
            except ValueError:
                out[key.strip()] = value.strip()
    return out


def load_effect(spec: str) -> tuple:
    """``NAME[:k=v,...]`` from whateverfont.effects, or ``FILE.py:FUNCTION[:k=v,...]``.

    Returns (a function from a recipe set to a recipe set, a label for the font's description)."""
    import importlib.util
    import sys
    from . import effects
    if ".py:" in spec:
        file, _, rest = spec.partition(".py:")
        path = Path(file + ".py")
        fn_name, _, opts = rest.partition(":")
        if not path.is_file():
            raise FileNotFoundError(f"no effect file {path}")
        sys.path.insert(0, str(path.resolve().parent))
        mod_spec = importlib.util.spec_from_file_location(f"whateverfont_effect_{path.stem}", path)
        module = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(module)
        label = f"{fn_name} from {path.name}"
    else:
        fn_name, _, opts = spec.partition(":")
        module, label = effects, fn_name
    fn = getattr(module, fn_name, None)
    if not callable(fn):
        raise ValueError(f"no effect named {fn_name!r}; use a name from whateverfont.effects (glow, painted, ...) "
                         "or FILE.py:FUNCTION")
    kwargs = _options(opts)
    return (lambda recipes: fn(recipes, **kwargs)), label


def protected_names(font: TTFont) -> list:
    """Names a modified version must not use: the source's family name, its Reserved Font Names and its trademarks."""
    names = list(_reserved_names(font))
    tm = font["name"].getDebugName(7) or ""
    for m in re.finditer(r"([A-Z][\w\-]*(?: [A-Z][\w\-]*)*)\s+(?:is|are)\s+(?:a\s+)?(?:registered\s+)?trademarks?", tm):
        names.append(m.group(1))
    fam = font["name"].getBestFamilyName()
    if fam:
        names.append(fam)
    out = []
    for n in names:
        n = n.strip()
        if n and n.lower() not in [o.lower() for o in out]:
            out.append(n)
    return out


def check_name(font: TTFont, name: str):
    """Raise ValueError if ``name`` uses a protected name of ``font``."""
    low = name.lower()
    for word in protected_names(font):
        if re.search(rf"(?<![a-z0-9]){re.escape(word.lower())}(?![a-z0-9])", low):
            raise ValueError(f"the new name must not contain {word!r}: it is a name the source font reserves "
                             "(its family name, a Reserved Font Name or a trademark). Choose another name")


def redraw(traced: TracedFont, out, name: str, family, effect=None, palettes: dict | None = None,
           copyright: str | None = None, description: str | None = None, check_glyphs: bool = True,
           jobs: int | None = None, effect_label: str = "") -> Result:
    """Draw ``traced`` with the pen of ``family`` and write ``out/ttf``, ``out/woff2`` and a CSS file.

    ``effect`` is a function that takes a recipe set and returns one, like ``effects.glow`` or a
    project's own; if it sets color layers, ``palettes`` (default: the family's) give their colors.
    """
    t0 = time.time()
    check_name(traced.font, name)
    params = family.params_at(family.default_location())
    pen = make_pen(traced, params)
    notes = []
    if traced.cjk:
        pen.cap = dense_cap(traced, pen)
        if pen.cap < 1.0:
            notes.append(f"the pen is heavier than the white between the strokes allows: it draws at "
                         f"{100 * pen.cap:.0f}% of its stem, and the densest characters at down to "
                         f"{100 * DENSE_FLOOR:.0f}%")
    plain = Recipes()
    plain.parts = True               # the source's composites stay, so a combining mark is a glyph that is seen
    for n, t in traced.glyphs.items():
        def fn(g, t=t, adv=traced.font["hmtx"][n][0]):
            paint(g, t, pen)
            g._frame = (adv * pen.k, 0, 0)
        plain[n] = Recipe(n, fn, None, "lower")
    recipes = plain
    if effect is not None:
        recipes = effect(plain)
        missing = [n for n in plain if n not in recipes]
        for n in missing:
            recipes[n] = plain[n]
    _SHARED.update(traced=traced, pen=pen, recipes=recipes, plain=plain, check=check_glyphs)
    try:
        done = _pool_map(_draw_job, list(traced.glyphs), jobs)
    finally:
        _SHARED.clear()
    shapes, layers, flagged, failed, plain_only = {}, {}, {}, {}, {}
    for n, shape, lay, problems, err, effect_err in done:
        if err:
            failed[n] = err
        shapes[n] = shape
        if lay:
            layers[n] = lay
        if problems:
            flagged[n] = problems
        if effect_err:
            plain_only[n] = effect_err
    for n, e in traced.failed.items():
        failed[n] = f"could not be traced ({e})"
    palettes = palettes if palettes is not None else getattr(family, "palettes", {}) or {}
    if layers and not palettes:
        raise ValueError("the effect makes color layers, but there are no palettes: use a family that has "
                         "palettes, or give them")
    if layers:
        letter = _letter_key(shapes, layers)
        for n in plain_only:
            if shapes.get(n):
                layers[n] = [(letter, shapes[n])]
    font = _build_font(traced, shapes, layers, palettes, name, family, params, copyright, description, effect_label)
    out = Path(out)
    ttf_dir = out / "ttf"
    ttf_dir.mkdir(parents=True, exist_ok=True)
    ps = f"{slug(name)}-Regular"
    path = ttf_dir / f"{ps}.ttf"
    _stamp(font).save(path)
    woff2 = save_woff2(path, out / "woff2")
    from types import SimpleNamespace
    from .compile import BuildResult
    from .project import write_css
    res = BuildResult(name, [path, woff2], [], {"Regular": path})
    css = write_css(SimpleNamespace(name=name, axes=[], styles={"Regular": {}}), res, out)
    is_open, _ = declared_license(traced.font)
    if not is_open:
        notes.append("the source declares no open license. Check its terms before you share this font")
    return Result(name, path, woff2, css, len(traced.glyphs), len(traced.composites), flagged, failed, plain_only,
                  notes, time.time() - t0, sum(1 for n in layers))


def _letter_key(shapes: dict, layers: dict) -> str:
    """The layer key that holds the letter itself: its area is closest to the plain ink's."""
    from collections import Counter
    votes = Counter()
    for n, lay in list(layers.items())[:60]:
        a = sum(-contour_area(c) for c in shapes.get(n, []))
        if a <= 0:
            continue
        best = min(lay, key=lambda kv: abs(sum(-contour_area(c) for c in kv[1]) - a))
        votes[best[0]] += 1
    return votes.most_common(1)[0][0] if votes else next(iter(next(iter(layers.values()))))[0]


def _build_font(traced, shapes, layers, palettes, name, family, params, copyright, description, effect_label):
    buf = io.BytesIO()
    traced.font.save(buf)
    buf.seek(0)
    font = TTFont(buf)
    for tag in font.keys():
        font[tag]
    glyf, hmtx = font["glyf"], font["hmtx"]
    for n, contours in shapes.items():
        g = _tt_glyph(quadratic_points([contours])[0]) if contours else _tt_glyph([])
        glyf[n] = g
    from fontTools.ttLib.tables import ttProgram
    for n in font.getGlyphOrder():
        g = glyf[n]
        if g.isComposite():
            if hasattr(g, "program"):
                g.program = ttProgram.Program()
                g.program.fromBytecode(b"")
        elif n not in shapes and g.numberOfContours > 0:
            g.program = ttProgram.Program()
            g.program.fromBytecode(b"")
    for n in font.getGlyphOrder():
        g = glyf[n]
        g.recalcBounds(glyf)
        hmtx[n] = (hmtx[n][0], int(getattr(g, "xMin", 0) or 0))
    for tag in HINT_TABLES + ("gasp",):
        if tag in font:
            del font[tag]
    if layers:
        _add_layers(font, layers, palettes)
    _names(font, traced, name, family, params, copyright, description, effect_label)
    return font


def _add_layers(font, layers: dict, palettes: dict):
    """COLR version 0 layers. A composite gets layers made of its parts' layers, so it stays a composite."""
    from types import SimpleNamespace
    from .color import add_color
    glyf, hmtx = font["glyf"], font["hmtx"]
    order = list(font.getGlyphOrder())
    table = {}
    for n, lay in layers.items():
        table[n] = []
        for i, (key, contours) in enumerate(lay):
            ln = f"{n}.c{i}"
            order.append(ln)
            g = _tt_glyph(quadratic_points([contours])[0]) if contours else _tt_glyph([])
            glyf[ln] = g
            table[n].append((ln, key))
    memo = {}

    def comp_layers(n):
        """[(key, [(component, layer glyph)])] for a composite, or the layers of a simple glyph."""
        if n in memo:
            return memo[n]
        g = glyf[n]
        if not g.isComposite():
            memo[n] = table.get(n, [])
            return memo[n]
        keys, parts = [], {}
        for comp in g.components:
            for ln, key in comp_layers(comp.glyphName):
                if key not in keys:
                    keys.append(key)
                parts.setdefault(key, []).append((comp, ln))
        result = []
        for i, key in enumerate(keys):
            ln = f"{n}.c{i}"
            new = copy.deepcopy(g)
            new.components = []
            for comp, layer in parts[key]:
                c = copy.copy(comp)
                c.glyphName = layer
                c.flags &= ~0x0200            # USE_MY_METRICS belongs to the base glyph
                new.components.append(c)
            if hasattr(new, "program"):
                del new.program
            order.append(ln)
            glyf[ln] = new
            result.append((ln, key))
        memo[n] = result
        return result

    for n in font.getGlyphOrder():
        if glyf[n].isComposite():
            lay = comp_layers(n)
            if lay:
                table[n] = lay
    font.setGlyphOrder(order)
    glyf.glyphOrder = order
    vmtx = font["vmtx"] if "vmtx" in font else None
    for ln in order:
        if ln not in hmtx.metrics:
            base = ln.rsplit(".c", 1)[0]
            g = glyf[ln]
            g.recalcBounds(glyf)
            hmtx[ln] = (hmtx[base][0], int(getattr(g, "xMin", 0) or 0))
            if vmtx is not None and base in vmtx.metrics:
                vmtx[ln] = vmtx[base]
    add_color(font, SimpleNamespace(palettes=palettes), table)


OFL_TEXT = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
            "This license is available with a FAQ at https://openfontlicense.org")


def _names(font, traced, name, family, params, copyright, description, effect_label):
    from .compile import _weight_class
    table = font["name"]
    src = {i: table.getDebugName(i) for i in (0, 1, 9, 13, 14)}
    original = src[1] or "the source font"
    is_open, notice = declared_license(font)
    ofl = is_open and re.search(r"open font licen[cs]e|\bOFL\b|scripts\.sil\.org/OFL|openfontlicense", notice or "", re.I)
    for rec in list(table.names):
        if rec.platformID == 1 or rec.nameID in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 16, 17, 18, 21, 22, 25):
            table.removeNames(nameID=rec.nameID, platformID=rec.platformID)
    ps = f"{slug(name)}-Regular"
    new_copyright = copyright if copyright is not None else (getattr(family, "copyright", "") or "")
    line = (src[0] or "").strip().rstrip(".")
    if new_copyright:
        line = f"{line}. {new_copyright.strip().rstrip('.')} (the redrawing)." if line else new_copyright
    vendor = (getattr(family, "vendor", "") or "NONE")[:4]
    version = getattr(family, "version", "1.0")
    pen = getattr(family, "name", "a whateverfont family")
    how = f"the pen of {pen}" + (f" and the effect {effect_label}" if effect_label else "")
    about = description or (f"The letters of {original}, traced along their centerlines and redrawn with {how}. "
                            f"The letter shapes and the shaping are the work of the authors of {original}; "
                            "this modified version is distributed under the same license.")
    records = {0: line, 1: name, 2: "Regular", 3: f"{version};{vendor};{ps}", 4: f"{name} Regular",
               5: f"Version {version}; retraced with whateverfont", 6: ps, 10: about}
    if src[9]:
        records[9] = f"{src[9]} (letters); redrawn with whateverfont"
    if ofl:
        records[13] = OFL_TEXT
        records[14] = "https://openfontlicense.org"
    for nid, value in records.items():
        if value:
            table.setName(value, nid, 3, 1, 0x409)
    os2 = font["OS/2"]
    os2.achVendID = (vendor + "    ")[:4]
    os2.usWeightClass = _weight_class(family, family.default_location(), params) if hasattr(family, "axes") else 400
    try:
        font["head"].fontRevision = float(version)
    except ValueError:
        pass
