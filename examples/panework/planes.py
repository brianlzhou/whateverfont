"""The `composition` color effect and its palettes, for the Panework families (see font.py).

Each letter is a window cut out of one painting. The painting is a white plane divided by thick
horizontal and vertical lines into unequal rectangles, a few of them filled with red, yellow or blue.
The letter's own edge is a line of the same kind, so the letter keeps its shape on any page.

How a letter is divided:

1. Before anything else, narrow notches and slits are closed (`sealed`). Thin marks (accents, the
   tail of a comma) are too small to hold a rectangle: they are solid, in the color of the lines.
   Small square parts (the dot of an i, a period) are one colored square in a frame.
2. The rest is split again and again, like a plan of rooms: each split is one line across the part
   of the letter that it divides, so lines end where they meet another line. A split is never in
   the middle, and never so near an edge of the letter or another line that it leaves a thin strip.
3. One or two of the rectangles get a color. Only a rectangle that the letter shows almost whole
   can get one, so a color always reads as a plane and never as a scrap.
4. Some lines stop short of the edge of the letter, and the white runs past their end.

Curves and diagonals cut the grid, as the edge of a diamond-shaped canvas cuts it. The lines stay
horizontal and vertical everywhere.

`composition(..., squares=...)` adds the second kind of painting: lines broken by small squares of
red, blue and gray, and blocks of color with a smaller square inside.
"""

from whateverfont import effects
from whateverfont.geom import flatten_contour
from whateverfont.outline import difference, dilate, intersection, rect, union

# ------------------------------------------------------------------------------------------- measuring


def _polys(contours, tol=1.0):
    return [p for p in (flatten_contour(c, tol) for c in contours) if len(p) > 2]


def _cross(polys, y):
    """Where a horizontal line at ``y`` is inside the shape: a sorted list of (x0, x1)."""
    xs = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if (a.imag > y) != (b.imag > y):
                xs.append(a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def _flip(polys):
    """The same polygons with x and y swapped, so that a vertical line can be measured as a horizontal one."""
    return [[complex(p.imag, p.real) for p in poly] for poly in polys]


def _edges(polys, least=6.0):
    """The straight horizontal runs of the outline: (y, x0, x1)."""
    out = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if abs(a.imag - b.imag) < 0.8 and abs(a.real - b.real) > least:
                out.append(((a.imag + b.imag) / 2, min(a.real, b.real), max(a.real, b.real)))
    return out


def _clip(spans, lo, hi):
    return [(max(a, lo), min(b, hi)) for a, b in spans if min(b, hi) > max(a, lo)]


class _Measure:
    """Areas and crossings of one shape, in both directions."""

    def __init__(self, contours, step=10.0):
        self.polys = _polys(contours)
        self.flip = _flip(self.polys)
        self.hedges = _edges(self.polys)
        self.vedges = _edges(self.flip)
        box = effects.contour_bounds(contours)
        self.box = box
        self.step = step
        self.rows = []
        y = box[1] + step / 2
        while y < box[3]:
            self.rows.append((y, _cross(self.polys, y)))
            y += step

    def area(self, x0, y0, x1, y1):
        """The area of the shape inside a rectangle (sampled in rows)."""
        total = 0.0
        for y, spans in self.rows:
            if y0 <= y <= y1:
                total += sum(b - a for a, b in _clip(spans, x0, x1))
        return total * self.step

    def extent(self, x0, y0, x1, y1):
        """The bounding box of the shape inside a rectangle, or None."""
        xs, ys = [], []
        for y, spans in self.rows:
            if y0 <= y <= y1:
                for a, b in _clip(spans, x0, x1):
                    xs += [a, b]
                    ys.append(y)
        if not xs:
            return None
        return min(xs), min(ys) - self.step / 2, max(xs), max(ys) + self.step / 2

    def spans(self, horizontal, pos, lo, hi):
        """Where a line at ``pos`` (y for a horizontal line, x for a vertical one) crosses the shape."""
        return _clip(_cross(self.polys if horizontal else self.flip, pos), lo, hi)

    def edges(self, horizontal):
        return self.hedges if horizontal else self.vedges


# ------------------------------------------------------------------------------------------ the parts


def _components(ink):
    """Each outside contour with the counters inside it."""
    outers = [c for c in ink if effects.contour_area(c) < 0]
    holes = [c for c in ink if effects.contour_area(c) > 0]
    tests = [effects.inside([c]) for c in outers]
    groups = [[c] for c in outers]
    for h in holes:
        p = h[0][0]
        best, best_area = None, None
        for i, test in enumerate(tests):
            if test(p):
                a = abs(effects.contour_area(outers[i]))
                if best is None or a < best_area:
                    best, best_area = i, a
        if best is not None:
            groups[best].append(h)
    return groups


def _compact(part):
    """True for a part about as wide as it is tall that fills most of its box: a dot, a period. Thin
    strokes (a bracket, the # and the %) are not compact: they stay white, so that they do not become
    a heavy plane of color."""
    x0, y0, x1, y1 = effects.contour_bounds(part)
    w, h = x1 - x0, y1 - y0
    filled = abs(sum(effects.contour_area(c) for c in part)) / max(1.0, w * h)
    return max(w, h) <= 1.8 * max(1.0, min(w, h)) and filled >= 0.75


def _small(part, amount):
    """True if nothing is left of ``part`` when it is shrunk by ``amount``: a mark too small to divide."""
    try:
        left = effects.erode(part, amount)
    except Exception:
        return False
    return abs(sum(effects.contour_area(c) for c in left)) < amount * amount * 1.5


def sealed(ink, amount=14.0, pocket=5000.0):
    """The letter with narrow notches and slits closed, and very small counters filled.

    At this weight the engine leaves a notch or a slit where a hook meets a bowl (9, 6, 5, s). The
    frame would outline each one and draw a black knot. Grow the letter by ``amount``, shrink it back,
    and drop counters smaller than ``pocket`` square units. If that joins two parts or changes the
    ink by more than 4%, keep the letter as it is.
    """
    try:
        out = effects.erode(dilate(ink, amount, miter=True), amount)
    except Exception:
        return ink
    out = [c for c in out if not 0 < effects.contour_area(c) < pocket]
    outers = lambda cs: sum(1 for c in cs if effects.contour_area(c) < -2000)
    total = lambda cs: abs(sum(effects.contour_area(c) for c in cs))
    if not out or outers(out) != outers(ink) or abs(total(out) - total(ink)) > 0.04 * total(ink):
        return ink
    return out


# ---------------------------------------------------------------------------------------- the effect


def composition(recipes, line=32.0, frame=34.0, room=56.0, per_split=68000.0, most=6, fields=(1, 2, 2),
                short=0.3, tint=0.25, hues=("red", "red", "red", "blue", "blue", "yellow", "yellow"),
                squares=None, frame_squares=False, inner=0.0, seed=0, names=None):
    """Divide each letter into rectangles with horizontal and vertical lines.

    ``line`` is the width of a line and ``frame`` the width of the line along the letter's edge, in
    units. ``room`` is the least white between two lines, or between a line and the edge. A letter
    gets about one split for each ``per_split`` square units of ink, and at most ``most``. ``fields``
    lists how many colored rectangles a letter may get (one is drawn at random). ``short`` is the share
    of lines that stop short of the edge, and ``tint`` the share of rectangles in the second white.
    ``hues`` is the bag that the colors of the rectangles are drawn from.

    ``squares`` = (least, most) turns on small squares along the lines, one every ``least`` to
    ``most`` line widths. ``frame_squares`` puts them on the straight parts of the edge too. ``inner``
    is the share of colored blocks that get a smaller square of another color inside.

    Keys: white, tint, red, yellow, blue, gray, frame, line, and for squares sq_red, sq_blue, sq_gray.
    """
    margin = line / 2 + frame + room          # from a line's middle to the letter's edge, at least
    apart = line + room                       # from a line's middle to the middle of the next one

    def effect(g, ink):
        rng = effects.seed_for(g, seed)
        ink = sealed(ink)
        # 1. Thin marks (accents, a comma) are solid. Small compact parts (a dot, a period) are one
        #    colored square in a frame. The rest is divided.
        solid, dots, body = [], [], []
        for part in _components(ink):
            if _small(part, frame + 10):
                solid.extend(part)
            elif _small(part, frame + room * 0.5) and _compact(part):
                dots.extend(part)
            else:
                body.extend(part)
        framed = body + dots
        if not framed:
            g.layers = [("frame", ink)]
            return
        lines, leaves, picked, keys, bars, runs, fills, tints = [], [], [], [], [], [], {}, []
        if dots:
            fills.setdefault(rng.choice(("red", "red", "blue", "yellow")), []).extend(dots)
        if body:
            m = _Measure(body)
            compose(rng, m, lines, leaves, picked, keys, bars, runs, fills, tints)
        g.layers = paint(rng, body, framed, solid, runs, bars, fills, tints, picked, keys, m if body else None)

    def compose(rng, m, lines, leaves, picked, keys, bars, runs, fills, tints):
        """2 to 4: split the letter, draw the lines, choose the colored rectangles."""
        x0, y0, x1, y1 = m.box
        canvas = (x0 - 1, y0 - 1, x1 + 1, y1 + 1)

        # -- 2. split the letter into rectangles ---------------------------------------------------
        def try_split(region, horizontal):
            rx0, ry0, rx1, ry1 = region
            lo, hi = (ry0, ry1) if horizontal else (rx0, rx1)              # where the line may go
            olo, ohi = (rx0, rx1) if horizontal else (ry0, ry1)            # how far it runs
            inner_lo = lo + (apart if lo > (canvas[1] if horizontal else canvas[0]) else 0)
            inner_hi = hi - (apart if hi < (canvas[3] if horizontal else canvas[2]) else 0)
            if inner_hi - inner_lo < 2:
                return None
            for _ in range(16):
                t = rng.uniform(0.2, 0.8)
                if abs(t - 0.5) < 0.07:
                    continue                                                 # never in the middle
                pos = lo + (hi - lo) * t
                if not inner_lo <= pos <= inner_hi:
                    continue
                spans = [s for s in m.spans(horizontal, pos, olo, ohi) if s[1] - s[0] > 2 * frame + 8]
                if not spans:
                    continue                                                 # the line would be all in a counter
                near = False
                for e, a, b in m.edges(horizontal):
                    if abs(e - pos) < margin and any(min(v - frame, b) - max(u + frame, a) > 2 for u, v in spans):
                        near = True
                        break
                if near:
                    continue
                # both sides must hold some ink, or the line divides nothing
                if horizontal:
                    sides = (m.area(rx0, ry0, rx1, pos), m.area(rx0, pos, rx1, ry1))
                else:
                    sides = (m.area(rx0, ry0, pos, ry1), m.area(pos, ry0, rx1, ry1))
                if min(sides) < (line + room) * room * 2:
                    continue
                return pos, spans
            return None

        area = m.area(*canvas)
        target = min(most, max(1, round(area / per_split * rng.uniform(0.75, 1.3))))
        leaves.append(canvas)                      # lines: (horizontal, pos, olo, ohi, spans)
        for _ in range(target):
            order = sorted(leaves, key=lambda r: -m.area(*r))
            done = False
            for region in order:
                ext = m.extent(*region)
                if ext is None:
                    continue
                tall = (ext[3] - ext[1]) > (ext[2] - ext[0])
                first = tall if rng.random() < 0.8 else not tall
                for horizontal in (first, not first):
                    hit = try_split(region, horizontal)
                    if hit is None:
                        continue
                    pos, spans = hit
                    rx0, ry0, rx1, ry1 = region
                    leaves.remove(region)
                    if horizontal:
                        leaves += [(rx0, ry0, rx1, pos), (rx0, pos, rx1, ry1)]
                        lines.append((True, pos, rx0, rx1, spans))
                    else:
                        leaves += [(rx0, ry0, pos, ry1), (pos, ry0, rx1, ry1)]
                        lines.append((False, pos, ry0, ry1, spans))
                    done = True
                    break
                if done:
                    break
            if not done:
                break

        # -- the lines, some of them stopping short of the edge --------------------------------------
        def met(horizontal, pos, lo, hi):
            """True if another line ends on this one between ``lo`` and ``hi`` (a T-junction)."""
            for h2, p2, olo2, ohi2, _ in lines:
                if h2 != horizontal and lo - line <= p2 <= hi + line and (abs(olo2 - pos) < 1 or abs(ohi2 - pos) < 1):
                    return True
            return False

        # bars: the line shapes; runs: (horizontal, pos, a, b), the visible middle of each line
        for horizontal, pos, olo, ohi, spans in lines:
            for u, v in spans:
                a, b = max(olo, u - frame), min(ohi, v + frame)
                # An end at the letter's edge may stop short, if the line is long, so that it does not
                # turn into a stub, and if no other line ends on the part that goes.
                free_a, free_b = u > olo + 1, v < ohi - 1
                gap = rng.uniform(0.9, 1.6) * room
                if rng.random() < short and (v - u) - 2 * frame - gap >= max(170.0, 3 * gap):
                    ends = [e for e in ("a", "b") if (free_a if e == "a" else free_b)]
                    rng.shuffle(ends)
                    for e in ends:
                        lo_, hi_ = (u, u + frame + gap) if e == "a" else (v - frame - gap, v)
                        if not met(horizontal, pos, lo_, hi_):
                            if e == "a":
                                a = u + frame + gap
                            else:
                                b = v - frame - gap
                            break
                if b - a < line:
                    continue
                if horizontal:
                    bars.append(rect(a, pos - line / 2, b, pos + line / 2))
                else:
                    bars.append(rect(pos - line / 2, a, pos + line / 2, b))
                runs.append((horizontal, pos, max(a, u + frame), min(b, v - frame)))

        # -- 3. color: one or two rectangles that the letter shows almost whole ----------------------
        choices = []
        for r in leaves:
            got = m.area(*r)
            ext = m.extent(*r)
            if ext is None or got < 2.2 * room * room * 4:
                continue
            fill = got / max(1.0, (ext[2] - ext[0]) * (ext[3] - ext[1]))
            if fill > 0.8:
                choices.append((got, r))
        choices.sort(key=lambda c: -c[0])
        count = rng.choice(fields)
        order = list(hues)
        rng.shuffle(order)
        for got, r in choices[: max(3, len(choices) // 2 + 1)]:
            if len(picked) >= count:
                break
            if rng.random() < 0.55 or len(choices) <= count:
                picked.append(r)
        if not picked and choices:
            picked.append(choices[0][1])
        for r in picked:
            hue = next((h for h in order if h not in keys), order[0])
            keys.append(hue)

        for r, hue in zip(picked, keys):
            fills.setdefault(hue, []).append(rect(*r))
        tints.extend(rect(*r) for r in leaves if r not in picked and rng.random() < tint)

    def paint(rng, body, framed, solid, runs, bars, fills, tints, picked, keys, m):
        """The layers, bottom first: the white letter, tint, colors, lines, the edge, squares, solid marks."""
        layers = [("white", framed)]
        if tints:
            cut = intersection(tints, body)
            if cut:
                layers.append(("tint", cut))
        for hue in ("red", "yellow", "blue", "gray"):
            if hue in fills:
                cut = intersection(fills[hue], framed)
                if cut:
                    layers.append((hue, cut))
        # a smaller square of another color inside some colored blocks
        blocks_inner = {}
        if inner and m is not None:
            pad = max(frame, line / 2) + 10
            for r, hue in zip(picked, keys):
                ext = m.extent(*r)
                if ext is None or rng.random() >= inner:
                    continue
                ex0, ey0, ex1, ey1 = ext
                side = (min(ex1 - ex0, ey1 - ey0) - 2 * pad) * rng.uniform(0.5, 0.7)
                if side < line:
                    continue
                cx = rng.uniform(ex0 + pad + side / 2, ex1 - pad - side / 2)
                cy = rng.uniform(ey0 + pad + side / 2, ey1 - pad - side / 2)
                other = rng.choice([h for h in ("red", "yellow", "blue", "gray", "gray", "white") if h != hue])
                blocks_inner.setdefault(other, []).append(
                    rect(cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2))
        for key in ("red", "yellow", "blue", "gray", "white"):
            if key in blocks_inner:
                cut = intersection(blocks_inner[key], body)
                if cut:
                    layers.append((key, cut))
        if bars:
            cut = intersection(union(bars), body)
            if cut:
                layers.append(("line", cut))
        try:
            edge = difference(framed, effects.erode(framed, frame))
        except Exception:
            edge = intersection(effects.band(framed, 2 * frame), framed)
        layers.append(("frame", edge))

        # -- small squares along the lines and the straight parts of the edge ---------------------------
        if squares and m is not None:
            dots = {"sq_red": [], "sq_blue": [], "sq_gray": []}
            pick = ["sq_red", "sq_red", "sq_blue", "sq_gray", "sq_gray"]

            def walk(a, b, at, width):
                """Squares along a run from ``a`` to ``b``; ``at(t, width)`` gives the square at ``t``."""
                t = a + rng.uniform(0.5, 2.5) * width
                while t + width <= b:
                    dots[rng.choice(pick)].append(at(t, width))
                    t += width * rng.uniform(*squares)

            for horizontal, pos, a, b in runs:
                if horizontal:
                    walk(a, b, lambda t, w, pos=pos: rect(t, pos - line / 2, t + w, pos + line / 2), line)
                else:
                    walk(a, b, lambda t, w, pos=pos: rect(pos - line / 2, t, pos + line / 2, t + w), line)
            if frame_squares:
                test = effects.inside(body)
                for horizontal in (True, False):
                    for e, a, b in m.edges(horizontal):
                        if b - a < 4 * frame:
                            continue
                        mid = (a + b) / 2
                        probe = complex(mid, e - frame / 2) if horizontal else complex(e - frame / 2, mid)
                        sign = -1 if test(probe) else 1                     # which side the ink is on
                        lo_, hi_ = a + frame, b - frame
                        if horizontal:
                            walk(lo_, hi_, lambda t, w, e=e, s=sign: rect(t, min(e, e + s * frame), t + w,
                                                                           max(e, e + s * frame)), frame)
                        else:
                            walk(lo_, hi_, lambda t, w, e=e, s=sign: rect(min(e, e + s * frame), t,
                                                                           max(e, e + s * frame), t + w), frame)
            for key in ("sq_red", "sq_blue", "sq_gray"):
                if dots[key]:
                    cut = intersection(dots[key], body)
                    if cut:
                        layers.append((key, cut))

        if solid:
            layers.append(("frame", solid))
        return layers

    return effects.wrapped(recipes, effect, names=names)


# ------------------------------------------------------------------------------------------ palettes


def palette(line, white, tint, red, yellow, blue, gray="#9A9893", frame=None, squares=None):
    """A palette. ``frame`` is the edge of the letter (the lines' color by default). ``squares`` gives the
    small squares on the lines as (red, blue, gray); by default they take the color of the lines, so they
    do not show."""
    sq = squares or (line, line, line)
    return {"white": white, "tint": tint, "red": red, "yellow": yellow, "blue": blue, "gray": gray,
            "line": line, "frame": frame or line, "sq_red": sq[0], "sq_blue": sq[1], "sq_gray": sq[2]}
