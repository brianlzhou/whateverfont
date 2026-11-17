"""Fallen leaves: the color effect of the Leafpile families (see font.py).

Each letter is a small heap of fallen leaves. The leaves are of four kinds, drawn here from a plain
description of each: a maple (five pointed lobes), an oak (round lobes), a ginkgo (a fan with a notch)
and a birch (an oval with a point). They lie along the strokes of the letter, overlap like leaves on a
lawn, and are cut to the letter, so the letter keeps its outline. A dark layer under them shows in the
thin gaps between the leaves, as wet leaves show under dry ones, and a vein layer draws the ribs.

Palette keys, bottom layer first: under, leaf0 to leaf4 (darkest to lightest), vein.
"""

from __future__ import annotations

import cmath
import math

from whateverfont import effects, outline
from whateverfont.geom import flatten_contour, seg_length, seg_point, seg_tangent
from whateverfont.outline import dilate, difference, intersection, union

LEAF_KEYS = ("leaf0", "leaf1", "leaf2", "leaf3", "leaf4")

# ------------------------------------------------------------------------------------------- the leaves
#
# Every leaf is drawn pointing up, with the foot of its blade at (0, 0) and its tip near (0, 1). It has a
# short stalk below the foot. Each function returns (outline, ribs, center): the ribs are (from, to)
# pairs, and the center is the point that the placement puts on the letter.


def _clockwise(contour: list) -> list:
    """The same contour, running clockwise (ink)."""
    return contour if effects.contour_area(contour) < 0 else effects.reverse_contour(contour)


def _poly(points: list) -> list:
    return _clockwise([(points[i], points[(i + 1) % len(points)]) for i in range(len(points))])


def _mirror(right: list) -> list:
    """A closed run of points: the right half from the top down, then the left half back up."""
    left = [complex(-p.real, p.imag) for p in reversed(right)]
    return right + left


def _bump(a: complex, tip: complex, b: complex, round_: float = 0.55) -> tuple:
    """Two cubic segments from ``a`` over ``tip`` to ``b``: one round lobe."""
    along = (b - a) / abs(b - a)
    ha = abs(tip - a) * round_
    hb = abs(b - tip) * round_
    out = (tip - (a + b) / 2) / (abs(tip - (a + b) / 2) or 1)
    return ((a, a + out * ha * 0.9, tip - along * ha, tip),
            (tip, tip + along * hb, b + out * hb * 0.9, b))


def maple() -> tuple:
    """A sugar maple: three big pointed lobes and two small ones at the foot, with a few teeth."""
    right = [complex(x, y) for x, y in (
        (0.00, 1.00), (0.08, 0.84), (0.18, 0.88), (0.15, 0.62),   # the top lobe, a tooth, the cleft
        (0.33, 0.73), (0.38, 0.66), (0.58, 0.70),                 # the side lobe: a tooth and its tip
        (0.46, 0.52), (0.52, 0.46), (0.29, 0.36),                 # under the side lobe, the lower cleft
        (0.37, 0.20), (0.16, 0.17), (0.035, 0.10),                # the small lobe at the foot
        (0.025, -0.12),                                           # the stalk
    )]
    blade = _poly(_mirror(right))
    hub = complex(0, 0.14)
    veins = [(hub, complex(0, 0.93)), (hub, complex(0.50, 0.66)), (hub, complex(-0.50, 0.66)),
             (hub, complex(0.30, 0.22)), (hub, complex(-0.30, 0.22))]
    return blade, veins, complex(0, 0.5)


def oak() -> tuple:
    """A white oak: a long leaf with four round lobes on each side and one at the top."""
    tips = [(0.20, 0.82), (0.27, 0.60), (0.26, 0.38), (0.16, 0.17)]
    clefts = [(0.07, 0.88), (0.09, 0.70), (0.10, 0.48), (0.08, 0.27), (0.03, 0.05)]
    right = []
    for i, tip in enumerate(tips):
        right += _bump(complex(*clefts[i]), complex(*tip), complex(*clefts[i + 1]))
    right.append((complex(*clefts[-1]), complex(0.02, -0.14)))          # down the stalk
    left = [tuple(complex(-p.real, p.imag) for p in reversed(seg)) for seg in reversed(right)]
    top = list(_bump(complex(-0.07, 0.88), complex(0, 1.0), complex(0.07, 0.88), 0.6))
    contour = _join(top + right + [(complex(0.02, -0.14), complex(-0.02, -0.14))] + left)
    veins = [(complex(0, -0.02), complex(0, 0.92))]
    for x, y in tips:
        foot = complex(0, y - 0.10)
        veins += [(foot, complex(x * 0.8, y)), (foot, complex(-x * 0.8, y))]
    return _clockwise(contour), veins, complex(0, 0.5)


def _join(segs: list) -> list:
    """Make a run of segments closed: each one starts where the last one ended."""
    out = []
    for i, s in enumerate(segs):
        nxt = segs[(i + 1) % len(segs)]
        if abs(s[-1] - nxt[0]) > 1e-9:
            out.append(s)
            out.append((s[-1], nxt[0]))
        else:
            out.append(s)
    return out


def ginkgo() -> tuple:
    """A ginkgo: a fan on a long stalk, with a notch in the middle of its wavy top edge."""
    base = complex(0.03, 0)
    corner = complex(0.62, 0.50)
    lobe = complex(0.26, 0.86)
    notch = complex(0.0, 0.76)
    right = [
        (complex(0.025, -0.30), complex(0.025, -0.12), complex(0.03, -0.04), base),
        (base, complex(0.20, 0.14), complex(0.44, 0.34), corner),
        (corner, complex(0.60, 0.64), complex(0.44, 0.80), lobe),
        (lobe, complex(0.12, 0.88), complex(0.03, 0.86), notch),
    ]
    left = [tuple(complex(-p.real, p.imag) for p in reversed(seg)) for seg in reversed(right)]
    contour = _join(right + left + [(complex(-0.025, -0.30), complex(0.025, -0.30))])
    veins = [(complex(0, 0.04), complex(math.sin(a) * 0.74, 0.04 + math.cos(a) * 0.70))
             for a in (-0.80, -0.40, 0.40, 0.80)]
    return _clockwise(contour), veins, complex(0, 0.45)


def birch() -> tuple:
    """A birch: an oval leaf with a long point and a toothed edge, ribbed like a feather."""
    pts = []
    for i in range(13):                                   # the right edge, from the tip down, with teeth
        t = i / 12
        y = 1.0 - t
        half = 0.35 * math.sin(math.pi * t ** 1.55) ** 0.8
        pts.append(complex(half + (0.022 if i % 2 and 0 < i < 12 else 0.0), y))
    pts[-1] = complex(0.03, 0.0)
    right = pts + [complex(0.022, -0.16)]
    contour = _poly(_mirror(right))
    veins = [(complex(0, -0.02), complex(0, 0.94))]
    for y in (0.16, 0.32, 0.48, 0.64):
        x = 0.27 - 0.22 * y
        veins += [(complex(0, y), complex(x, y + 0.15)), (complex(0, y), complex(-x, y + 0.15))]
    return contour, veins, complex(0, 0.48)


# kind: (drawing, how long it is against the others, how often it falls)
KINDS = {"maple": (maple(), 1.00, 0.40), "oak": (oak(), 1.22, 0.22),
         "birch": (birch(), 1.10, 0.20), "ginkgo": (ginkgo(), 0.95, 0.18)}


def _vein(a: complex, b: complex, width: float) -> list:
    """A rib: a long thin wedge from ``a`` (its full width) to ``b`` (a point)."""
    n = (b - a) / abs(b - a) * 1j * width / 2
    return _poly([a + n, b, a - n])


# ------------------------------------------------------------------------------------------- the effect


def _skeleton(g, step: float = 24.0) -> list:
    """Points along the strokes of ``g``, each with the direction of the stroke there."""
    out = []
    for s in g.strokes:
        for seg in s.segments():
            n = max(1, int(seg_length(seg) / step))
            for k in range(n + 1):
                t = k / n
                d = seg_tangent(seg, t)
                if d:
                    out.append((seg_point(seg, t), d))
    return out


def _inside_poly(poly: list, q: complex) -> bool:
    hit = False
    a = poly[-1]
    for b in poly:
        if (a.imag > q.imag) != (b.imag > q.imag) and q.real < a.real + (b.real - a.real) * (q.imag - a.imag) / (b.imag - a.imag):
            hit = not hit
        a = b
    return hit


TONES = (0, 1, 1, 2, 2, 2, 3, 3, 4)           # how often each leaf color falls, darkest first


def _no_pockets(grown: list, ink: list) -> list:
    """The grown letter without the holes that are not counters.

    Some strokes meet with a hairline crack (the `~` has one under its wave). Growing the letter closes
    the mouth of the crack and leaves a small hole, which showed as a notch of paper. A hole is kept
    only if it lies in a counter of the letter.
    """
    counters = [c for c in ink if effects.contour_area(c) > 0]
    in_counter = effects.inside(counters) if counters else (lambda q: False)
    return [c for c in grown if effects.contour_area(c) < 0 or in_counter(c[0][0])]


def _parts(contours: list) -> tuple:
    """(outsides, counters) of merged contours."""
    return ([c for c in contours if effects.contour_area(c) < 0],
            [c for c in contours if effects.contour_area(c) > 0])


def _grown(ink: list, reach: float) -> tuple:
    """(reach, the letter grown by it). The reach shrinks where the full one would join two parts.

    The dot of the i sits less than 40 units above the stem: grown by 19 units on each side, the two
    met. So the letter grows by less until it keeps as many parts and counters as the ink has.
    """
    outs, holes = _parts(ink)
    for share in (1.0, 0.6, 0.35, 0.0):
        r = reach * share
        if r <= 0:
            return 0.0, ink
        grown = _no_pockets(dilate(ink, r), ink)
        o, h = _parts(grown)
        if len(o) == len(outs) and len(h) == len(holes):
            return r, grown
    return 0.0, ink


def _room(ink: list, sw: float, reach: float, far: float, gap: float) -> list | None:
    """Where a leaf may stick out: up to ``far`` from the big parts of the letter, and nowhere else.

    Not into a counter. Not into an opening or an inside corner narrower than twice ``far`` (the mouth
    of the e, the crotch of the V), where a leaf would close the letter. Not toward another part of
    the letter, and not near a dot, an accent or a thin sign, which would lose its shape.
    """
    outs, holes = _parts(ink)
    big = [c for c in outs if -effects.contour_area(c) > 3.0 * sw * sw]
    if not big:
        return None
    try:
        shut = effects.erode(dilate(ink, far), far)            # the letter with its openings closed
        mouths = difference(shut, ink) if shut else []
    except Exception:
        mouths = []
    # rounding leaves slivers along the whole outline, and Skia cannot merge those
    mouths = [c for c in mouths if abs(effects.contour_area(c)) > 0.02 * sw * sw]
    room = []
    for part in big:
        zone = dilate([part], far)
        others = [c for c in outs if c is not part]
        if others:
            zone = difference(zone, dilate(others, far + gap))
        room.extend(zone)
    room = union(room)
    if mouths:
        room = difference(room, dilate(mouths, gap))
    if holes:
        room = difference(room, effects.erode([effects.reverse_contour(c) for c in holes], reach) if reach > 0
                          else [effects.reverse_contour(c) for c in holes])
    return room


def _ribs_on(ribs: list, width: float, seen: list) -> list:
    """The ribs of one leaf, cut to the part of it that shows.

    Two workarounds for Skia. (1) It fails on some of these cuts ("operation did not succeed", for the
    thin bar of U+2015). Then each rib is cut on its own, and a rib that still fails is left out.
    (2) It sometimes returns a piece that lies outside both shapes: for the Ż, a bit of rib 20 units
    to the left of the letter, where it showed as a gray dash. A piece that leaves the box of the leaf
    is dropped.
    """
    wedges = [_vein(a, b, width) for a, b in ribs]
    try:
        out = intersection(wedges, seen)
    except Exception:
        out = []
        for wedge in wedges:
            try:
                out.extend(intersection([wedge], seen))
            except Exception:
                pass
    box = effects.contour_bounds(seen)
    if box is None:
        return []

    def within(c):
        b = effects.contour_bounds([c])
        return b is not None and b[0] >= box[0] - 1 and b[1] >= box[1] - 1 and b[2] <= box[2] + 1 and b[3] <= box[3] + 1

    return [c for c in out if within(c)]


def fallen(recipes, size: float = 1.45, margin: float = 0.12, poke: float = 0.0, whole: float = 0.3,
           lying: float = 0.55, gap: float = 7.0, vein: float = 9.0, veins: bool = True, turn: float = 40.0,
           cover: float = 0.97, least: float = 420.0, seed: int = 0, names=None):
    """Letters made of fallen leaves. Keys: under, leaf0 to leaf4, vein.

    ``size`` is the length of a maple leaf as a share of the stem. ``margin`` is how far the heap
    reaches past the letter, as a share of the stem: the dark ``under`` layer is the letter grown by
    that much. ``poke`` (a share of the stem, 0 for none) lets the top ``whole`` share of the leaves
    stick out farther, if at least ``lying`` of the leaf lies on the letter. ``gap`` is the dark line between two
    leaves, ``vein`` the width of a rib at its foot, in units. ``turn`` is how far, in degrees, a leaf
    may turn away from the direction of the stroke. ``cover`` is the share of the letter the leaves must
    cover before the heap is done. A piece of leaf smaller than ``least`` square units is left out.
    """

    def effect(g, ink):
        box = effects.contour_bounds(ink)
        if box is None:
            return
        rng = effects.seed_for(g, seed)
        x0, y0, x1, y1 = box
        sw = g.sw
        reach, clip = _grown(ink, sw * margin)
        under = clip
        in_ink = effects.inside(ink)

        # points of the letter that the leaves must cover
        step = max(12.0, sw * 0.13)
        targets = []
        y = y0 + step / 2
        while y < y1:
            x = x0 + step / 2
            while x < x1:
                q = complex(x, y)
                if in_ink(q):
                    targets.append(q)
                x += step
            y += step
        if not targets:
            g.layers = [("under", under)]
            return
        bones = _skeleton(g)

        def direction(q):
            if not bones:
                return cmath.rect(1.0, rng.uniform(0, math.tau))
            p, d = min(bones, key=lambda b: abs(b[0] - q))
            return d / abs(d)

        kinds = list(KINDS)
        weights = [KINDS[k][2] for k in kinds]
        open_ = set(range(len(targets)))
        need = len(targets) * (1.0 - cover)
        leaves = []                                           # (contour in place, veins in place, tone)
        tries = 0
        # Colors come out of a shuffled bag, so every letter gets the same mix and no letter of a word
        # is darker than its neighbors.
        bag = []
        while len(open_) > need and tries < 400:
            tries += 1
            q = targets[rng.choice(tuple(open_))]
            kind = rng.choices(kinds, weights)[0]
            (blade, ribs, center), length, _ = KINDS[kind]
            scale = sw * size * length * rng.uniform(0.82, 1.12)
            d = direction(q)
            if rng.random() < 0.5:
                d = -d                                        # a leaf points either way along the stroke
            angle = cmath.phase(d) - math.pi / 2 + math.radians(rng.uniform(-turn, turn))
            rot = cmath.rect(scale, angle)
            if rng.random() < 0.5:                            # some leaves land face down
                flip = lambda p: complex(-p.real, p.imag)
            else:
                flip = lambda p: p
            place = lambda p, rot=rot, q=q, center=center, flip=flip: q + (flip(p) - center) * rot
            contour = [tuple(place(p) for p in seg) for seg in blade]
            poly = flatten_contour(contour, 4.0)
            hit = {i for i in open_ if _inside_poly(poly, targets[i])}
            if not hit and tries > 40:
                continue
            open_ -= hit
            if not bag:
                bag = list(TONES)
                rng.shuffle(bag)
            ribs_here = [(place(a), place(b)) for a, b in ribs]
            leaves.append((contour, ribs_here, bag.pop()))

        def stack(loose):
            """The heap, from its top leaf down: (under, leaves by color, ribs)."""
            layers = {k: [] for k in range(5)}
            vein_parts = []
            rims = []                                         # the leaves that stick out
            above = []                                        # the leaves above, grown by the gap
            for n, (contour, ribs, tone) in enumerate(reversed(leaves)):
                seen = intersection([contour], clip)
                sticks_out = False
                if loose and n < len(leaves) * whole and seen:
                    inside_share = sum(-effects.contour_area(c) for c in seen) / -effects.contour_area(contour)
                    if inside_share > lying:
                        seen = intersection([contour], loose)
                        sticks_out = True
                if above and seen:
                    seen = difference(seen, above)
                seen = [c for c in seen if abs(effects.contour_area(c)) > least]
                grown = dilate([contour], gap) if gap > 0 else [contour]
                above = union(above + grown) if above else grown
                if not seen:
                    continue
                layers[tone].extend(seen)
                if sticks_out:
                    rims.extend(seen)
                if veins and vein > 0:
                    width = vein * min(1.0, sw / 150)
                    vein_parts.extend(c for c in _ribs_on(ribs, width, seen) if abs(effects.contour_area(c)) > 60)
            base = under
            if rims and gap > 0:
                # Past the edge of the letter, the gap between two leaves would show the paper, as a
                # crack. The dark layer reaches under every leaf that sticks out, so it shows there too.
                # Where a rim meets the letter it can close a small pocket of paper: fill it.
                counters = {round(effects.contour_area(c)) for c in under if effects.contour_area(c) > 0}
                base = [c for c in union(under + dilate(rims, gap))
                        if effects.contour_area(c) < 0 or effects.contour_area(c) > 0.12 * sw * sw
                        or round(effects.contour_area(c)) in counters]
            return base, layers, vein_parts

        # A few leaves near the top of the heap lie whole, and their tips stick out past the edge of the
        # letter, by up to ``poke`` (a share of the stem). See `_room` for where they may not go.
        loose = None
        if sw * poke > reach:
            # The engine warns about every merge that gives up while a glyph is drawn. This zone is a
            # rough limit and never goes into the font, so its troubles (slivers along the outline)
            # are dropped, as the engine's own trace.py does.
            before = len(outline.trouble)
            room = _room(ink, sw, reach, sw * poke, gap)
            del outline.trouble[before:]
            if room:
                loose = union(room + clip)
        base, layers, vein_parts = stack(loose)
        if loose:
            # If two leaves that stick out still meet across an opening (the mouth of an e) and close it,
            # or join two parts, the letter would change: then no leaf of this glyph sticks out.
            o, h = _parts(base)
            o0, h0 = _parts(under)
            if len(o) != len(o0) or len(h) != len(h0):
                base, layers, vein_parts = stack(None)
        under = base
        out = [("under", under)]
        for k in range(5):
            if layers[k]:
                out.append((LEAF_KEYS[k], layers[k]))
        if vein_parts:
            out.append(("vein", vein_parts))
        g.layers = out

    return effects.wrapped(recipes, effect, names=names)


def palette(under: str, leaves: list, vein: str) -> dict:
    """A palette: the color under the leaves, five leaf colors from dark to light, and the ribs."""
    out = {"under": under, "vein": vein}
    out.update({k: c for k, c in zip(LEAF_KEYS, leaves)})
    return out
