"""The `klimt` color effect and its palettes, for the Gilt families (see font.py)."""

import math

from whateverfont import effects
from whateverfont.outline import circle, difference, dilate, intersection, rect, union

CIRCLE_KEYS = ("red", "blue", "green", "violet")


def spiral(center, radius, turns=2.0, width=9.0, start=0.0, hand=1):
    """A spiral line as one closed contour: out along one side of the line, back along the other."""
    steps = max(8, int(turns * 18))
    inner = width * 0.75
    out, back = [], []
    for i in range(steps + 1):
        t = i / steps
        angle = start + hand * t * turns * 2 * math.pi
        r = inner + (radius - width / 2 - inner) * t
        d = complex(math.cos(angle), math.sin(angle))
        out.append(center + d * (r + width / 2))
        back.append(center + d * (r - width / 2))
    pts = out + back[::-1]
    return [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]


def grow(ink, amount):
    """The letter made ``amount`` fatter on every side, with its counters kept.

    `outline.dilate` on the whole letter lost the counter of the Gilt Robe zero at amount 7 (it kept
    it at 5 and at 12), so the outside is grown and the counters are shrunk separately.
    """
    outers = [c for c in ink if effects.contour_area(c) < 0]
    holes = [effects.reverse_contour(c) for c in ink if effects.contour_area(c) > 0]
    out = dilate(outers, amount)
    if holes:
        out = difference(out, effects.erode(holes, amount))
    return [c for c in out if not 0 < effects.contour_area(c) < 1500]


def sealed(ink, amount=5.0):
    """The letter with hairline cracks closed (grown, then shrunk by the same amount) and pockets filled.

    At this weight some joins leave a crack a few units wide that opens into a small pocket, in the 6
    and the 9 of Gilt Robe for example. The dark edge layer would show through it as a stray mark.
    If the result loses or gains a real part, keep the ink as it was.
    """
    try:
        out = [c for c in effects.erode(grow(ink, amount), amount) if not 0 < effects.contour_area(c) < 4000]
    except Exception:
        return ink              # Skia could not shrink this outline (the Ə of Gilt): it has no cracks to close

    parts = lambda cs: sorted(effects.contour_area(c) < 0 for c in cs if abs(effects.contour_area(c)) > 4000)
    total = lambda cs: abs(sum(effects.contour_area(c) for c in cs))
    if parts(out) != parts(ink) or abs(total(out) - total(ink)) > 0.03 * total(ink):
        return ink
    return out


def klimt(recipes, tile=(34.0, 60.0), courses=(50.0, 64.0, 64.0, 84.0, 104.0), gap=6.0, rim=7.0,
          big=52.0, small=30.0, share=(0.11, 0.035), circles=1.0, spirals=1.0, blocks=1.0, seed=0, names=None):
    """Gold tiles in courses, with black and white rectangles, spirals and ringed circles mixed in.

    Keys: edge, grout, gold0 to gold3, black, white, red, blue, green, violet.
    ``circles``, ``spirals`` and ``blocks`` scale how many of each motif a letter gets.
    """

    def effect(g, ink):
        box = effects.contour_bounds(ink)
        if box is None:
            return
        rng = effects.seed_for(g, seed)
        ink = sealed(ink)
        x0, y0, x1, y1 = box
        in_ink = effects.inside(ink)
        area = abs(sum(effects.contour_area(c) for c in ink))

        # Round motifs first: they need the widest parts of the letter.
        motifs = []                                            # (center, radius, kind)
        round_share = (circles + spirals) / 2
        for radius, part in ((big, share[0]), (small, share[1])):
            room = effects.inside(effects.erode(ink, radius + 11))
            step = radius * 0.45
            spots = []
            y = y0
            while y < y1:
                x = x0
                while x < x1:
                    p = complex(x + rng.uniform(0, step), y + rng.uniform(0, step))
                    if room(p):
                        spots.append(p)
                    x += step
                y += step
            quota = round(area * part * round_share / (math.pi * radius * radius))
            while spots and quota > 0:
                # Of a few candidates, take the one farthest from the motifs already placed.
                best, best_d = None, -1.0
                for p in rng.sample(spots, min(10, len(spots))):
                    d = min((abs(p - q) - r for q, r, _ in motifs), default=1e9)
                    if d > best_d:
                        best, best_d = p, d
                if best_d < radius + 16:
                    spots = [p for p in spots if all(abs(p - q) >= r + radius + 16 for q, r, _ in motifs)]
                    if not spots:
                        break
                    continue
                kind = "spiral" if rng.random() < spirals / (circles + spirals) else "circle"
                motifs.append((best, radius, kind))
                quota -= 1

        def clear_of_motifs(xa, ya, xb, yb):
            for q, r, _ in motifs:
                dx = max(xa - q.real, 0.0, q.real - xb)
                dy = max(ya - q.imag, 0.0, q.imag - yb)
                if math.hypot(dx, dy) < r + 8:
                    return False
            return True

        # Tiles: courses of upright rectangles over the whole box, cut to the letter afterward.
        golds = [[] for _ in range(4)]
        blacks, whites = [], []
        ph1, ph2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
        y = y0 - rng.uniform(0, 30)
        while y < y1:
            h = rng.choice(courses)
            x = x0 - rng.uniform(0, tile[1])
            run, dark = 0, True
            while x < x1:
                # Inside a run the rectangles are narrow, like piano keys, so that two or three
                # fit across a stem.
                w = rng.uniform(26.0, 40.0) if run > 0 else rng.uniform(*tile) * (0.85 if h > 80 else 1.0)
                xa, ya, xb, yb = x + gap / 2, y + gap / 2, x + w - gap / 2, y + h - gap / 2
                x += w
                # A rectangle must be whole and keep gold around it. A white one at the edge
                # reads as a notch on white paper, and a black one does on a black label.
                whole = (h >= 60
                         and all(in_ink(complex(px, py))
                                 for px in (xa - 8, (xa + xb) / 2, xb + 8)
                                 for py in (ya - 8, (ya + yb) / 2, yb + 8))
                         and clear_of_motifs(xa, ya, xb, yb))
                if run == 0 and whole and rng.random() < 0.2 * blocks:
                    run, dark = rng.choice((2, 3, 3, 4)), True
                if run > 0:
                    run = run - 1 if whole else 0              # a run ends at the edge of the stroke
                    if whole:
                        (blacks if dark else whites).append(rect(xa, ya, xb, yb))
                        dark = not dark
                        continue
                cx, cy = (xa + xb) / 2, (ya + yb) / 2
                if any(abs(complex(cx, cy) - q) < r - max(w, h) / 2 for q, r, _ in motifs):
                    continue                                   # hidden under a round motif
                tone = 0.5 + 0.26 * math.sin(cx / 150 + ph1) * math.cos(cy / 180 + ph2) + rng.uniform(-0.34, 0.34)
                golds[min(3, max(0, int(tone * 4)))].append(rect(xa, ya, xb, yb))
            y += h

        layers = [("edge", grow(ink, rim)), ("grout", ink)]
        for k, tiles in enumerate(golds):
            cut = [c for c in intersection(tiles, ink) if abs(effects.contour_area(c)) > 140] if tiles else []
            if cut:
                layers.append((f"gold{k}", cut))
        if blacks:
            layers.append(("black", blacks))
        if whites:
            layers.append(("white", whites))

        # Round motifs: a dark rim, a disc, a ring, a center.
        rims, discs, rings, centers = [], {}, {}, {}
        for q, r, kind in motifs:
            rims.append(circle(q.real, q.imag, r + 5))
            if kind == "spiral":
                discs.setdefault("gold3", []).append(circle(q.real, q.imag, r))
                line = spiral(q, r - 5, turns=2.0 if r > 40 else 1.4, width=9.0 if r > 40 else 7.0,
                              start=rng.uniform(0, 6.28), hand=rng.choice((1, -1)))
                centers.setdefault("black", []).extend(union([line]))
            else:
                a, b = rng.sample(CIRCLE_KEYS, 2)
                discs.setdefault(a, []).append(circle(q.real, q.imag, r))
                if r > 40:
                    rings.setdefault(rng.choice(("gold3", "white")), []).append(circle(q.real, q.imag, r * 0.66))
                    centers.setdefault(b, []).append(circle(q.real, q.imag, r * 0.36))
                else:
                    centers.setdefault(rng.choice(("gold3", "white")), []).append(circle(q.real, q.imag, r * 0.45))
        if rims:
            layers.append(("edge", rims))
        for level in (discs, rings, centers):
            for key in sorted(level):
                layers.append((key, level[key]))
        g.layers = layers

    return effects.wrapped(recipes, effect, names=names)


def palette(edge, grout, golds, black="#15120E", white="#F7F0DF", red="#B5332B", blue="#2B5BA6",
            green="#3A7F5E", violet="#6F4E99"):
    out = {"edge": edge, "grout": grout, "black": black, "white": white,
           "red": red, "blue": blue, "green": green, "violet": violet}
    out.update({f"gold{k}": c for k, c in enumerate(golds)})
    return out


# "Gold" has a dark edge for light paper. "Gold on Dark" has a bright edge, for a black label.
PALETTES = {
    "Gold": palette("#3A2607", "#7A5512", ["#B0821E", "#D0A22C", "#E7C24C", "#F7E18E"]),
    "Gold on Dark": palette("#E9C552", "#4A3209", ["#A87A1A", "#CC9C28", "#E7C24C", "#F9E7A0"],
                            black="#0D0B09", white="#FBF5E6"),
    "Silver": palette("#1E2228", "#5A616B", ["#8B939D", "#AEB5BD", "#CDD2D8", "#EEF1F4"],
                      red="#8E2F4A", blue="#27508F", green="#2F7C7A", violet="#5B4A94"),
    "Rose": palette("#3B1D18", "#8A4B3C", ["#B87462", "#D39480", "#E8B5A2", "#F8DCCF"],
                    red="#A32C3F", blue="#3F5C97", green="#5E8466", violet="#7A4C86"),
}
