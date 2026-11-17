"""The `chrome` and `chrome_line` color effects and their palettes, for the Tinsheen families (see font.py).

Each letter is polished metal that reflects a world: a sky above a sharp horizon, and dark ground below
it. A color font of this engine (COLR version 0) has no gradients, so the shading is a stack of flat
layers, bottom layer first:

- ``outline``: the letter grown on every side, in a dark color. It holds the letter together on any
  ground, and it is the first layer, so the engine kerns by it and neighbors keep their distance.
- ``ground0`` to ``ground3``: the lower half. ``ground3`` lies just under the horizon and is the darkest;
  the ground gets lighter toward the bottom, and ``ground0`` holds the baseline and the descenders.
- ``sky0`` to ``sky5``: the upper half. ``sky0`` lies just over the horizon and is the palest; the sky gets
  deeper toward the top, and ``sky5`` holds the tops of capitals, ascenders and figures.
- ``rim``: a thin bright band just inside the edge of the letter, even all around.

The band edges are fixed heights in font units, the same in every glyph, so on a line of text the horizon
and every band run straight through capitals, lowercase and figures alike. Accents and other marks that
float above or below a letter get small bands of their own (see `chrome`).

`chrome_line` draws the same bands in a hollow letter: a chrome tube along the edge, held by the outline.
GROUNDS names the ground each palette is drawn for.
"""

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds
from whateverfont.outline import depths, dilate, difference, intersection, rect, union

#: Band edges, in font units above the baseline, bottom to top. The fourth is the horizon. The bands are
#: thin next to the horizon and wider away from it, so the light changes fast near the horizon, as in a
#: curved mirror. The last edge lies above the x-height (540) and its overshoot, so only capitals,
#: ascenders, figures and accents reach the deepest sky.
EDGES = (120, 195, 250, 290, 314, 350, 400, 470, 590)
HORIZON = EDGES[3]
KEYS = ("ground0", "ground1", "ground2", "ground3", "sky0", "sky1", "sky2", "sky3", "sky4", "sky5")


def _outer(contours):
    """Group contours into pieces: each outside contour with the counters inside it."""
    levels = depths(contours)
    outs = [(c, contour_bounds([c])) for c, d in zip(contours, levels) if d % 2 == 0]
    groups = [[c] for c, _ in outs]
    for c, d in zip(contours, levels):
        if d % 2 == 0:
            continue
        b = contour_bounds([c])
        best, area = None, None
        for i, (_, ob) in enumerate(outs):
            if ob[0] <= b[0] + 0.5 and ob[1] <= b[1] + 0.5 and ob[2] >= b[2] - 0.5 and ob[3] >= b[3] - 0.5:
                a = (ob[2] - ob[0]) * (ob[3] - ob[1])
                if area is None or a < area:
                    best, area = i, a
        if best is not None:
            groups[best].append(c)
    return [(g, contour_bounds([g[0]])) for g in groups]


def bands(ink, edges=EDGES, sliver=20.0, lap=6.0):
    """The letter cut into horizontal bands at ``edges``: a list of contour lists, bottom band first.

    A piece of a band thinner than ``sliver`` units (the tip of a round that just crosses an edge) would
    read as a stray line, so it joins the band it touches. Each band also reaches ``lap`` units up into
    the next one, which is painted over it: two layers that only meet along an edge let the layer under
    them show through as a faint line in a browser.
    """
    x0, y0, x1, y1 = contour_bounds(ink)
    lows = [y0 - 10] + list(edges)
    highs = list(edges) + [y1 + 10]
    n = len(lows)
    parts = [[] for _ in range(n)]
    for i in range(n):
        if highs[i] <= y0 or lows[i] >= y1:
            continue
        cut = intersection(ink, [rect(x0 - 10, lows[i], x1 + 10, highs[i])])
        for group, b in _outer(cut):
            target = i
            if b[3] - b[1] < sliver:
                if i < n - 1 and abs(b[3] - highs[i]) < 0.5:
                    target = i + 1
                elif i > 0 and abs(b[1] - lows[i]) < 0.5:
                    target = i - 1
            parts[target].extend(group)
    out = []
    for i in range(n):
        shape = parts[i]
        if shape and i < n - 1 and lap > 0:
            # Only where this band touches the edge above it: a strip of the letter just over that edge.
            b = contour_bounds(shape)
            if b[3] >= highs[i] - 0.5:
                strip = intersection(ink, [rect(b[0] - 1, highs[i] - 1, b[2] + 1, highs[i] + lap)])
                merged = union(shape + strip)
                # A piece of the strip that does not touch this band (the foot of another stroke that
                # starts just over the edge) is hidden under the next band anyway: leave it out.
                shape = [c for group, gb in _outer(merged)
                         if not (gb[1] >= highs[i] - 1.5 and gb[3] <= highs[i] + lap + 0.5) for c in group]
        out.append(union(shape) if shape else [])
    return out


def fill_holes(contours, least):
    """The contours with every counter smaller than ``least`` square units filled."""
    keep = [c for c, d in zip(contours, depths(contours)) if d % 2 == 0 or abs(contour_area(c)) >= least]
    return keep if len(keep) == len(contours) else union(keep)


def cleaned(ink, pinhole=1500.0, speck=400.0, smooth=0.0):
    """The ink without pinholes and specks, and with its small steps smoothed.

    In heavy weights the hook of a 6 or a 9 can touch its bowl, and a cedilla or a ring can close up,
    which leaves a tiny counter. With a bright rim round it, such a hole reads as a stray white dot, so
    a counter smaller than ``pinhole`` square units is filled. A piece of ink smaller than ``speck`` is
    dropped.

    ``smooth`` (in units) grows the letter and shrinks it back by that much, then shrinks and grows it:
    a small step in the inside of a bowl, where the engine's heavy stroke turns too fast, is smoothed
    away, and every corner gets that radius. The rim follows the outline exactly, so it would trace
    every such step. If smoothing would open or close a counter (the narrow slot under the hook of a 6),
    or change the area by more than 5%, the glyph keeps its outline.
    """
    ink = tidy(ink)
    keep = []
    for c, d in zip(ink, depths(ink)):
        a = abs(contour_area(c))
        if (d % 2 == 1 and a < pinhole) or (d % 2 == 0 and a < speck):
            continue
        keep.append(c)
    ink = union(keep) if keep else []
    if ink and smooth > 0:
        area = abs(sum(contour_area(c) for c in ink))
        closed = effects.erode(dilate(ink, smooth), smooth)
        shape = dilate(effects.erode(closed, smooth), smooth) if closed else []
        if (shape and len(shape) == len(ink)
                and abs(abs(sum(contour_area(c) for c in shape)) - area) < 0.05 * area):
            ink = tidy(shape)
    return ink


def tidy(ink, least=0.05):
    """The contours without segments shorter than ``least`` units.

    A few outlines (the Greek xi) come out of the merge with a segment a hundredth of a unit long. Skia
    cannot stroke such a contour, so the rim would cover the whole letter.
    """
    out = []
    for c in ink:
        segs = [s for s in c if max(abs(p - s[0]) for p in s) >= least]
        if len(segs) < 2:
            continue
        fixed = []
        for i, s in enumerate(segs):
            start = segs[i - 1][-1]               # join each segment to the end of the one before it
            fixed.append((start,) + tuple(s[1:]))
        out.append(fixed)
    return out


def rim_band(ink, depth):
    """A band ``depth`` units wide just inside the edge of the letter, and 2 units past it, so the bands
    under it cannot peek out along the edge."""
    area = abs(sum(contour_area(c) for c in ink))
    inner = effects.erode(ink, depth)
    left = abs(sum(contour_area(c) for c in inner)) if inner else 0.0
    if left < 0.3 * area:
        # Skia sometimes fails on an outline; grow it by half a unit first, which rebuilds its curves.
        inner = effects.erode(dilate(ink, 0.5), depth + 0.5)
    return difference(dilate(ink, 2.0), inner) if inner else dilate(ink, 2.0)


#: A piece of a glyph that starts above this height is a mark (an accent, the dot of i): it lies wholly
#: in the deepest sky, so it gets bands of its own. A piece that ends below MARK_BELOW (a dot below, a
#: comma below) gets bands of ground of its own.
MARK_ABOVE = 575
MARK_BELOW = -25


def marks(ink):
    """Split the ink into the body of the letter and its marks above and below: three contour lists."""
    body, above, below = [], [], []
    for group, b in _outer(ink):
        if b[1] > MARK_ABOVE:
            above.append(group)
        elif b[3] < MARK_BELOW:
            below.append(group)
        else:
            body.extend(group)
    return body, above, below


def mark_bands(group, keys, lap=6.0):
    """One mark cut into ``len(keys)`` bands of equal height, bottom band first: ``[(key, contours)]``."""
    x0, y0, x1, y1 = contour_bounds(group)
    n = len(keys)
    step = (y1 - y0) / n
    out = []
    for i, key in enumerate(keys):
        lo = y0 - 2 if i == 0 else y0 + step * i
        hi = y1 + 2 if i == n - 1 else y0 + step * (i + 1) + lap
        part = intersection(group, [rect(x0 - 2, lo, x1 + 2, hi)])
        if part:
            out.append((key, part))
    return out


def chrome(recipes, edges=EDGES, outline=24.0, rim=13.0, smooth=9.0, sliver=20.0, lap=6.0, names=None):
    """Letters of polished chrome: a dark outline, flat bands of sky and ground, and a bright rim.

    ``edges`` are the heights of the band edges, bottom to top; the fourth is the horizon. ``outline`` is
    how far the dark outline reaches past the letter and ``rim`` how far the bright rim reaches into it,
    in font units. ``sliver`` and ``lap`` are explained in :func:`bands`.

    A mark above the letter would be one flat color, the deepest sky, so each mark gets three bands of
    its own, pale at its foot and deep at its top, as the sky runs. A mark below the letter gets three
    bands of ground, dark at its top and light at its foot.
    """

    def effect(g, ink):
        if contour_bounds(ink) is None:
            return
        ink = cleaned(ink, smooth=smooth)
        if not ink:
            return
        body, above, below = marks(ink)
        parts = {key: [] for key in KEYS}
        if body:
            for key, part in zip(KEYS, bands(body, edges, sliver, lap)):
                parts[key].extend(part)
        for group in above:
            height = contour_bounds(group)[3] - contour_bounds(group)[1]
            keys = ("sky1", "sky3", "sky5") if height > 90 else ("sky2", "sky5")
            for key, part in mark_bands(group, keys, lap):
                parts[key].extend(part)
        for group in below:
            for key, part in mark_bands(group, ("ground0", "ground1", "ground2"), lap):
                parts[key].extend(part)
        # A counter that the outline nearly closes (the 4, the loop of a γ) would leave a speck of the
        # ground inside it, and a pinhole in the rim a speck of a band: fill both.
        layers = [("outline", fill_holes(dilate(ink, outline), 900.0))]
        layers += [(key, parts[key]) for key in KEYS if parts[key]]
        edge = fill_holes(rim_band(ink, rim), 400.0)
        if edge:
            layers.append(("rim", edge))
        g.layers = layers
        # The plain outline of the glyph (what a program without color fonts shows, and what the engine
        # measures) becomes the cleaned letter. redraw() moves the layers with it, so it comes last.
        effects.redraw(g, ink)

    return effects.wrapped(recipes, effect, names=names)


def chrome_line(recipes, edges=EDGES, tube=46.0, outline=24.0, inner=10.0, rim=9.0, smooth=9.0, sliver=20.0,
                lap=6.0, names=None):
    """Hollow letters: a chrome tube along the edge of each letter, and the ground showing through it.

    ``tube`` is the width of the chrome band inside the edge, in units. A dark band holds it: ``outline``
    units outside the edge and ``inner`` units inside the tube. The tube has the bands of `chrome`, at the
    same heights, and a thin bright ``rim`` along its outer edge. Same keys and palettes as `chrome`.
    """

    def effect(g, ink):
        if contour_bounds(ink) is None:
            return
        ink = cleaned(ink, smooth=smooth)
        if not ink:
            return
        # The hollow: the letter shrunk by the tube. A piece of it too small to read (in a small figure of
        # a fraction, a thin accent) would be a dark speck, so the tube fills it.
        core = effects.erode(ink, tube)
        core = [c for group, b in _outer(core) if abs(contour_area(group[0])) >= 3000 for c in group] if core else []
        band_ = difference(ink, core) if core else ink
        hole = effects.erode(core, inner) if core else []
        dark = dilate(ink, outline)
        dark = difference(dark, hole) if hole else dark
        layers = [("outline", fill_holes(dark, 900.0))]
        body, above, below = marks(band_)
        parts = {key: [] for key in KEYS}
        if body:
            for key, part in zip(KEYS, bands(body, edges, sliver, lap)):
                parts[key].extend(part)
        for group in above:
            for key, part in mark_bands(group, ("sky1", "sky3", "sky5"), lap):
                parts[key].extend(part)
        for group in below:
            for key, part in mark_bands(group, ("ground0", "ground1", "ground2"), lap):
                parts[key].extend(part)
        layers += [(key, parts[key]) for key in KEYS if parts[key]]
        edge = fill_holes(rim_band(ink, rim), 400.0)
        if edge:
            layers.append(("rim", edge))
        g.layers = layers
        effects.redraw(g, ink)

    return effects.wrapped(recipes, effect, names=names)


def palette(outline, ground, sky, rim):
    """One palette. ``ground``: four colors from the bottom up to the horizon (light to dark). ``sky``: six
    colors from the horizon up (pale to deep)."""
    colors = {"outline": outline, "rim": rim}
    colors.update({f"ground{i}": c for i, c in enumerate(ground)})
    colors.update({f"sky{i}": c for i, c in enumerate(sky)})
    return colors


PALETTES = {
    "Chrome": palette("#02040C", ["#A3AACB", "#686F93", "#383D5E", "#14142A"],
                      ["#F8FCFF", "#DCEEFE", "#B6D8FB", "#8CBDF6", "#62A0EE", "#3E7EDF"], "#FFFFFF"),
    "Gold": palette("#160800", ["#E2A04E", "#A8661C", "#6C380A", "#341703"],
                    ["#FFFADF", "#FFE9A2", "#FACF5E", "#EDAD2E", "#CE8616", "#9E5A08"], "#FFF4C6"),
    "Magenta": palette("#0C0012", ["#E54FB6", "#951F94", "#561066", "#25062F"],
                       ["#FFEAF8", "#FFC0E7", "#FF8AD4", "#EF56C8", "#C03CD8", "#7F27C2"], "#FFF0FA"),
    "Lime": palette("#001012", ["#2BB5AA", "#127479", "#0A464E", "#04252A"],
                    ["#F7FFDA", "#DEFB9C", "#B4EE62", "#72D66E", "#2FB48E", "#0F7F88"], "#F8FFE8"),
}

#: The ground each palette is drawn for.
GROUNDS = {"Chrome": "#0A1A4F", "Gold": "#2A0710", "Magenta": "#000000", "Lime": "#03181C"}
