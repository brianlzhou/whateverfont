"""The `polished` and `faceted` color effects and their palettes, for the Cabochon families (see font.py).

Each letter is a stone lit by one lamp at the upper left. The effects stack flat color layers, because a
color font of this engine (COLR version 0) has no gradients.

`polished` (the family Cabochon) is a stone with a raised, glossy bevel:

- the stone, in its body color, with paler cloudy patches and a few darker ones;
- a bevel in two steps on each side: a light rim along the edges that face the lamp, a dark rim along
  the edges that face away;
- a thin bright line just inside the lit rim;
- one small specular spot where the lamp is reflected;
- a short shadow cast on the cloth toward the lower right, in translucent black, so it darkens any ground.

`faceted` (the family Cabochon Rose) cuts each stroke into flat facets that meet in a ridge down its
middle. Each facet is a translucent white or black layer over the same cloudy stone, so the facets that
face the lamp are lighter and the others darker, and the stone shows through all of them.

Palette keys, bottom layer first: stone, shadow, deep, cloud, mist, lit, lit2, shade, shade2, line, glint,
spark. `faceted` uses f_left, f_right, f_bottom and f_top in place of the four bevel keys and the line.
"""

import math

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, transform_contour
from whateverfont.outline import circle, difference, intersection, union

AWAY = complex(1, -1) / abs(complex(1, -1))       # from the lamp (upper left) toward the lower right


def moved(contours, d):
    return [transform_contour(c, lambda q: q + d) for c in contours]


def clean(contours, least=24.0):
    """The contours without slivers and specks, which would read as dirt."""
    return [c for c in contours if abs(contour_area(c)) > least]


def facing(ink, start, end, toward=-AWAY):
    """The part of the ink that lies between ``start`` and ``end`` units in from the edges that face ``toward``.

    A point belongs to it when the point ``start`` units toward ``toward`` is still ink and the point
    ``end`` units that way is not. The band is widest on an edge that faces that way squarely and thins
    to nothing on an edge that the light grazes, the way a lit bevel looks.
    """
    far = moved(ink, -toward * end)
    if start <= 0:
        return difference(ink, far)
    return difference(intersection(ink, moved(ink, -toward * start)), far)


def ellipse(cx, cy, rx, ry, angle):
    """A clockwise ellipse, turned by ``angle`` degrees."""
    turn = complex(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    return transform_contour(circle(0, 0, 1), lambda q: complex(cx, cy) + complex(q.real * rx, q.imag * ry) * turn)


def sparkle(cx, cy, r):
    """A four-pointed glint: the flash of a facet that catches the lamp."""
    pts = []
    for i in range(8):
        t = -math.pi * i / 4 + math.pi / 2              # clockwise, starting at the top
        pts.append(complex(cx, cy) + complex(math.cos(t), math.sin(t)) * (r if i % 2 == 0 else r * 0.24))
    return [(pts[i], pts[(i + 1) % 8]) for i in range(8)]


def blob(rng, center, radius, grain, stretch, points=9):
    """One soft, irregular patch: a closed curve whose radius wanders, leaning along the grain."""
    waves = [(f, a * rng.uniform(0.6, 1.0), rng.uniform(0, 2 * math.pi)) for f, a in ((2, 0.20), (3, 0.14), (5, 0.07))]
    turn = complex(math.cos(math.radians(grain)), math.sin(math.radians(grain)))
    pts = []
    for i in range(points):
        t = -2 * math.pi * i / points                  # clockwise, like ink
        r = radius * (1 + sum(a * math.sin(f * t + ph) for f, a, ph in waves))
        pts.append(center + complex(math.cos(t) * stretch, math.sin(t)) * r * turn)
    n = len(pts)
    segs = []
    for i in range(n):                                  # Catmull-Rom through the points, as cubics
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        segs.append((p1, p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6, p2))
    return segs


def patches(rng, box, count, size, grain, stretch=1.7):
    """Cloudy patches: one to three soft blobs each, leaning along the grain of the stone."""
    x0, y0, x1, y1 = box
    along = complex(math.cos(math.radians(grain)), math.sin(math.radians(grain)))
    shapes = []
    for _ in range(count):
        c = complex(rng.uniform(x0, x1), rng.uniform(y0, y1))
        for _ in range(rng.choice((1, 2, 2, 3))):
            r = rng.uniform(*size)
            p = c + along * rng.gauss(0, size[1] * 0.8) + along * 1j * rng.gauss(0, size[1] * 0.25)
            shapes.append(blob(rng, p, r, grain + rng.uniform(-10, 10), stretch))
    return union(shapes) if shapes else []


def stone(ink, rng, shadow, clouds, deeps, cloud_size, grain):
    """The body of the stone, its cast shadow, and its darker and paler patches, bottom layer first.

    The letter itself is the bottom layer: the engine spaces and kerns a color glyph by that layer.
    """
    box = contour_bounds(ink)
    area = abs(sum(contour_area(c) for c in ink))
    layers = [("stone", ink)]
    if shadow:
        cast = clean(difference(moved(ink, complex(*shadow)), ink))
        if cast:
            layers.append(("shadow", cast))

    # A few darker patches, then paler clouds, and inside some clouds a paler core, like light caught
    # inside jade.
    unit = 2600.0 * (cloud_size[1] / 44.0) ** 2
    lean = grain + rng.uniform(-8, 8)
    for key, share, size in (("deep", 0.22 * deeps, (cloud_size[0] * 1.1, cloud_size[1] * 1.2)),
                             ("cloud", 0.34 * clouds, cloud_size)):
        count = round(area / unit * share + rng.random() * 0.8)
        if count <= 0:
            continue
        shapes = patches(rng, box, count, size, lean)
        part = clean(intersection(shapes, ink), 60) if shapes else []
        if part:
            layers.append((key, part))
            if key == "cloud":
                cores = patches(rng, contour_bounds(part), count * 2, (size[0] * 0.5, size[1] * 0.6), lean)
                inner = effects.erode(part, 7.0)
                core = clean(intersection(inner, cores), 50) if cores and inner else []
                if core:
                    layers.append(("mist", core))
    return layers


def lamp_spot(ink, margin, r):
    """Where the lamp is reflected: the point with room for a spot of radius ``r`` that lies nearest to a
    point near the upper left of the letter. None if no part of the letter is wide enough."""
    core = effects.erode(ink, margin + r) if r > 0 else []
    if not core:
        return None
    x0, y0, x1, y1 = contour_bounds(ink)
    room = effects.inside(core)
    lamp = complex(x0 + 0.30 * (x1 - x0), y1 - 0.22 * (y1 - y0))
    step = r * 0.8
    grid = [complex(x0 + i * step, y0 + j * step)
            for i in range(int((x1 - x0) / step) + 1) for j in range(int((y1 - y0) / step) + 1)]
    grid.sort(key=lambda p: abs(p - lamp))
    return next((p for p in grid if room(p)), None)


def polished(recipes, bevel=0.25, line=(0.12, 0.34), shadow=(13.0, -13.0), clouds=1.0, deeps=1.0,
             cloud_size=(22.0, 44.0), grain=24.0, spot=0.15, seed=0, names=None):
    """Letters cut from polished stone, with a raised, glossy bevel.

    ``bevel`` is the depth of the lit and the dark rim, as a share of the stem. It is held to a little
    less than half of the hairline, so a thin stroke keeps a light half and a dark half. ``line`` is
    where the bright line runs, as shares of the bevel, measured in from the edge. ``shadow`` is where
    the cast shadow falls, in units (None for no shadow). ``clouds`` and ``deeps`` scale how many pale and
    dark patches a letter gets. ``grain`` is the angle, in degrees, along which the patches lean. ``spot``
    is the radius of the specular spot as a share of the stem (0 for none).
    """

    def effect(g, ink):
        if contour_bounds(ink) is None:
            return
        rng = effects.seed_for(g, seed)
        depth = min(bevel * g.sw, 0.46 * math.sqrt(2) * g.hw)
        layers = stone(ink, rng, shadow, clouds, deeps, cloud_size, grain)

        # The bevel, in two steps on each side, so the edge rounds over like a polished dome.
        for key, end in (("lit", depth), ("lit2", depth * 0.5)):
            band = clean(facing(ink, 0, end))
            if band:
                layers.append((key, band))
        for key, end in (("shade", depth * 0.8), ("shade2", depth * 0.36)):
            band = clean(facing(ink, 0, end, toward=AWAY))
            if band:
                layers.append((key, band))
        bright = clean(facing(ink, depth * line[0], depth * line[1]), 30)
        if bright:
            layers.append(("line", bright))

        # The lamp: one small spot on the face of the stone, near the upper left of the letter.
        r = spot * g.sw
        best = lamp_spot(ink, depth * 0.9, r)
        if best is not None:
            layers.append(("glint", [ellipse(best.real, best.imag, r * 1.25, r * 0.8, 50)]))
            layers.append(("spark", [ellipse(best.real - r * 0.12, best.imag + r * 0.12, r * 0.55, r * 0.36, 50)]))
        g.layers = layers

    return effects.wrapped(recipes, effect, names=names)


def faceted(recipes, cut=0.56, shadow=(13.0, -13.0), clouds=0.45, deeps=0.35, cloud_size=(22.0, 44.0), grain=24.0,
            glint=0.24, glints=0.4, seed=0, names=None):
    """Letters cut with facets: each stroke has four sloping faces that meet in a ridge down its middle.

    ``cut`` is how far each face reaches in from the edge, as a share of the stroke: a little more than
    half, so the two faces of a stroke meet. ``glint`` is the size of the four-pointed flash where the
    lamp catches a facet, as a share of the stem (0 for none), and ``glints`` the share of letters that
    get one. The other options are those of `polished`.
    """

    def effect(g, ink):
        if contour_bounds(ink) is None:
            return
        rng = effects.seed_for(g, seed)
        layers = stone(ink, rng, shadow, clouds, deeps, cloud_size, grain)
        across, down = cut * g.sw, cut * g.hw           # stems are measured across, bars from top to bottom

        # Faces turned to the left, the right, down and up. Each is a translucent layer, so where two
        # overlap (a diagonal faces both up and left) their light adds up.
        for key, toward, reach in (("f_left", -1, across), ("f_right", 1, across),
                                   ("f_bottom", -1j, down), ("f_top", 1j, down)):
            face = clean(facing(ink, 0, reach, toward=toward), 30)
            if face:
                layers.append((key, face))

        r = glint * g.sw
        best = lamp_spot(ink, 0, r * 0.3) if rng.random() < glints else None
        if best is not None and r > 0:
            layers.append(("glint", [circle(best.real, best.imag, r * 0.30)]))
            layers.append(("spark", [sparkle(best.real, best.imag, r)]))
        g.layers = layers

    return effects.wrapped(recipes, effect, names=names)


def palette(stone, deep, cloud, mist, lit, lit2, shade, shade2, line, glint, spark="#FFFFFF", shadow="#00000052",
            faces=("#FFFFFF75", "#FFFFFF38", "#00000040", "#00000075")):
    """The colors of one stone. ``faces`` are the four facets of Cabochon Rose: top, left, right, bottom."""
    top, left, right, bottom = faces
    return {"stone": stone, "shadow": shadow, "deep": deep, "cloud": cloud, "mist": mist, "lit": lit, "lit2": lit2,
            "shade": shade, "shade2": shade2, "line": line, "glint": glint, "spark": spark,
            "f_top": top, "f_left": left, "f_right": right, "f_bottom": bottom}


# Each stone with the cloth it is shown on (the ground), named in the comment.
PALETTES = {
    # stone, deep, cloud, mist, lit, lit2, shade, shade2, line, glint
    "Jade": palette("#3B9163", "#2F7D53", "#4FA273", "#67B587", "#62AF82", "#8ACDA3", "#226342", "#123D27",
                    "#E4FBEC", "#CDEFD9"),   # on dark red cloth, #7A1418
    "Ruby": palette("#A8132F", "#8C0E26", "#BE223D", "#D23B55", "#D2445C", "#F08597", "#66071A", "#3D0410",
                    "#FFE5EA", "#FFD0D8"),   # on ivory satin, #F2EADB
    "Sapphire": palette("#1F4AA0", "#193C86", "#2C5DB6", "#4271C8", "#4A7BD0", "#86A9E6", "#102A63", "#08173D",
                        "#E6EEFF", "#CFDDFA"),   # on old gold cloth, #B08636
    "Amethyst": palette("#7A3FA6", "#66338E", "#8C51B9", "#A06ACA", "#A570CC", "#CBA2E6", "#4A2368", "#2D1342",
                        "#F6EBFF", "#E8D6F6"),   # on pale sage silk, #D2D8C6
    "Amber": palette("#D07E14", "#B86A0E", "#E0942A", "#ECAC45", "#EBA742", "#F8CF7A", "#8A4A06", "#5A2E03",
                     "#FFF4D6", "#FFE7B0"),   # on midnight velvet, #15233A
    "Onyx": palette("#202024", "#151518", "#2E2E34", "#3D3D44", "#4A4A52", "#7C7C86", "#0B0B0D", "#000000",
                    "#EDEDF2", "#BDBDC6", faces=("#FFFFFF4A", "#FFFFFF24", "#0000004D", "#0000008C")),   # on camel suede, #C6A77B
}

#: The ground each palette is shown on: the cloth the stones lie on.
GROUNDS = {"Jade": "#7A1418", "Ruby": "#F2EADB", "Sapphire": "#B08636", "Amethyst": "#D2D8C6",
           "Amber": "#15233A", "Onyx": "#C6A77B"}
