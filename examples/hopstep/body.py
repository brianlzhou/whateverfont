"""Hopstep: the body kit, the line, the dashes and the recipes.

The system
----------
- One body. A round head that floats a little above the torso, a torso, two arms and two legs. Every
  limb is a tube ``LIMB`` wide with round ends that bends once (elbow, knee), with a mitten hand or a
  mitten foot at its end. Bone lengths are constants: a pose only says where the hands and feet go (or
  at which angles the bones point), and ``limb`` works out the elbow or the knee. So every figure has the
  same proportions.
- One line. A black line ``LINE`` wide around the whole body (the body shapes grown by ``LINE``). Where
  a part lies in front of another, the line of the front part is cut into the part behind it, except at
  the joint where they grow out of each other (a shoulder, a hip).
- Dashes. Short round-ended dashes ``LINE`` wide that radiate from a hand, a foot or the head.
- Color. A glyph has two layers: ``ink`` (the line and the dashes) under the color of its letter
  (``c0`` to ``c5``). The ink layer is the whole grown body, so no light seam shows between line and color.
- Ground. Every drawing is moved so that its lowest ink sits on the baseline, unless the pose is in the
  air (``air``), when the body floats at a set height over its dashes.

A bone is a band with flat ends buried in a joint ball, a hand, a foot or the torso. Round ends that lie
exactly on top of each other make Skia's boolean operations fail or drop a piece; ``merge`` and ``_op``
also retry with a hair of jitter when that happens anyway.

Coordinates are font units, ground at y = 0. Angles are degrees, 0 is east, 90 is north.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from functools import lru_cache

import pathops

from whateverfont.geom import contour_area, contour_bounds, reverse_contour, transform_contour
from whateverfont.glyph import Recipe, Recipes
from whateverfont.outline import circle, from_path, to_path

# ------------------------------------------------------------------------------------------ the body

LIMB = 64.0                 # arms and legs: the width of the color
LINE = 22.0                 # the black line, inside lines and dashes
TORSO = 100.0               # the width of the torso
TORSO_LEN = 180.0           # between the centers of its two round ends
HEAD = 62.0                 # the radius of the head
NECK = 2 * LINE + 16.0      # color to color between torso and head: two lines and a little white
SHOULDER = 24.0             # the shoulders sit this far below the top of the torso
UPPER_ARM, FOREARM = 140.0, 125.0
THIGH, SHIN = 170.0, 170.0
HAND = LIMB / 2 * 1.22      # the radius of a mitten hand
FOOT = LIMB / 2 * 1.06      # the radius of a mitten foot
FOOT_LEN = 42.0             # from the ankle to the center of the toe end

GROUND = LINE + FOOT        # the y of an ankle whose foot is flat on the floor
SEAT = LINE + TORSO / 2     # the y of a hip (the bottom of the torso) that sits on the floor
KNEEL = LINE + LIMB / 2     # the y of a knee on the floor

JOINT_CLEAR = TORSO / 2 + LINE + 10.0   # no inside line this close to the joint two parts share

DASH = LINE                 # the width of a dash
DASH_LEN = 62.0
DASH_GAP = 30.0             # white between a dash and the line of the body

SIDE = 36.0                 # white on each side of a glyph
SPACE = 300.0


def P(x, y=None) -> complex:
    if y is None:
        return x if isinstance(x, complex) else complex(*x)
    return complex(x, y)


def pol(deg: float, r: float = 1.0) -> complex:
    return cmath.rect(r, math.radians(deg))


def ang(v: complex) -> float:
    return math.degrees(cmath.phase(v))


# ------------------------------------------------------------------------------------- primitives


def _arc(c: complex, r: float, a0: float, sweep: float):
    """Cubic segments of an arc of radius ``r`` around ``c`` from angle ``a0``, turning ``sweep`` degrees."""
    n = max(1, math.ceil(abs(sweep) / 90 - 1e-9))
    t = sweep / n
    k = 4 / 3 * math.tan(math.radians(t) / 4)
    out = []
    for i in range(n):
        a, b = a0 + t * i, a0 + t * (i + 1)
        p0, p3 = c + pol(a, r), c + pol(b, r)
        out.append((p0, p0 + pol(a + 90, r * k), p3 - pol(b + 90, r * k), p3))
    return out


def _cw(contour):
    return reverse_contour(contour) if contour_area(contour) > 0 else contour


@dataclass(frozen=True)
class Disc:
    c: complex
    r: float

    def contour(self, grow: float = 0.0):
        return circle(self.c.real, self.c.imag, self.r + grow)


@dataclass(frozen=True)
class Rod:
    """A tube with round ends from ``p`` to ``q``, of radius ``r``."""
    p: complex
    q: complex
    r: float

    def contour(self, grow: float = 0.0):
        r = self.r + grow
        p, q = self.p, self.q
        if abs(q - p) < 1e-6:
            return circle(p.real, p.imag, r)
        d = (q - p) / abs(q - p)
        n = d * 1j * r
        a = ang(n)
        segs = [(p + n, q + n)] + _arc(q, r, a, -180) + [(q - n, p - n)] + _arc(p, r, a + 180, -180)
        return _cw(segs)


@dataclass(frozen=True)
class Bar:
    """A bone: a band with flat ends from ``p`` to ``q``, of half-width ``r``. Its ends are always buried
    in a joint ball, a hand, a foot or the torso, so that no two round ends lie on top of each other
    (the boolean operations stumble on curves that coincide)."""
    p: complex
    q: complex
    r: float

    def contour(self, grow: float = 0.0):
        r = self.r + grow
        n = (self.q - self.p) / abs(self.q - self.p) * 1j * r
        pts = [self.p + n, self.q + n, self.q - n, self.p - n]
        return _cw([(pts[i], pts[(i + 1) % 4]) for i in range(4)])


def _sized(pr, k: float):
    """A part of a larger or smaller person: its place and its width grow together."""
    if isinstance(pr, Disc):
        return Disc(pr.c * k, pr.r * k)
    return type(pr)(pr.p * k, pr.q * k, pr.r * k)


def _turned(pr, fn):
    if isinstance(pr, Disc):
        return Disc(fn(pr.c), pr.r)
    return type(pr)(fn(pr.p), fn(pr.q), pr.r)


# ---------------------------------------------------------------------------- robust boolean operations


def _jitter(contours, k: int):
    """Each contour moved by a different hundredth of a unit: it breaks curves that coincide exactly."""
    out = []
    for i, c in enumerate(contours):
        off = complex(((i * 7 + k * 3) % 11 - 5) * 0.03, ((i * 5 + k * 2) % 13 - 6) * 0.03)
        out.append(transform_contour(c, lambda q, off=off: q + off))
    return out


def merge(contours):
    """The union of contours. Skia sometimes fails, or loses a piece, where two curves coincide; then
    the contours are nudged apart by a hair and merged again. The result must cover the same box."""
    contours = [c for c in contours if c]
    if not contours:
        return []
    want = contour_bounds(contours)
    for k in range(8):
        cs = contours if k == 0 else _jitter(contours, k)
        path = to_path(cs)
        try:
            path.simplify(fix_winding=True, keep_starting_points=False, clockwise=True)
        except Exception:
            continue
        out = [c for c in from_path(path) if len(c) >= 2 and abs(contour_area(c)) > 0.5]
        got = contour_bounds(out) if out else None
        if got and all(abs(a - b) < 1.0 for a, b in zip(got, want)):
            return out
    raise ValueError("the union failed")


def _op(a, b, kind):
    if not a:
        return []
    if not b:
        return list(a) if kind == pathops.PathOp.DIFFERENCE else []
    for k in range(8):
        aa, bb = (a, b) if k == 0 else (_jitter(a, k), _jitter(b, k + 3))
        try:
            out = pathops.op(to_path(aa), to_path(bb), kind, fix_winding=True, clockwise=True)
        except Exception:
            continue
        return [c for c in from_path(out) if len(c) >= 2 and abs(contour_area(c)) > 0.5]
    raise ValueError("a boolean operation failed")


def cut(a, b):
    return _op(a, b, pathops.PathOp.DIFFERENCE)


def clip(a, b):
    return _op(a, b, pathops.PathOp.INTERSECTION)


def shape(prims, grow: float = 0.0):
    return merge([pr.contour(grow) for pr in prims])


# --------------------------------------------------------------------------------------- the limbs


@dataclass(frozen=True)
class To:
    """A limb that reaches for a point. ``bend`` +1 puts the elbow (knee) on the left of the line from the
    root to the point, -1 on its right. ``foot`` is the direction of a foot or a hand, in degrees."""
    x: float
    y: float
    bend: int = 1
    foot: float | None = None


@dataclass(frozen=True)
class Bones:
    """A limb given by the directions of its two bones, in degrees."""
    upper: float
    lower: float
    foot: float | None = None


def limb(root: complex, spec, a: float, b: float):
    """(elbow or knee, end) for a limb with bones ``a`` and ``b``."""
    if isinstance(spec, Bones):
        mid = root + pol(spec.upper, a)
        return mid, mid + pol(spec.lower, b)
    target = complex(spec.x, spec.y)
    v = target - root
    d = abs(v)
    lo, hi = abs(a - b) + 1e-3, a + b - 1e-3
    if d > hi + 0.5:
        raise ValueError(f"cannot reach {target} from {root}: {d:.0f} > {a + b:.0f}")
    d = min(max(d, lo), hi)
    u = v / abs(v)
    cos_a = (a * a + d * d - b * b) / (2 * a * d)
    turn = math.acos(max(-1.0, min(1.0, cos_a)))
    mid = root + a * u * cmath.rect(1.0, spec.bend * turn)
    return mid, root + u * d


# ------------------------------------------------------------------------------------- one figure


@dataclass
class Part:
    name: str
    prims: list
    joints: frozenset       # names of the joints this part grows from


@dataclass
class Burst:
    """Dashes that radiate from ``at`` (a joint name or a point), centered on direction ``deg``."""
    at: object
    deg: float
    n: int = 3
    spread: float = 26.0
    length: float = DASH_LEN
    gap: float = DASH_GAP
    shift: float = 0.0          # move the dashes along their own direction


def burst(at, deg, n=3, spread=26.0, length=DASH_LEN, gap=DASH_GAP, shift=0.0):
    return Burst(at, deg, n, spread, length, gap, shift)


@dataclass
class Fig:
    """One figure. ``hip`` is the center of the bottom end of the torso and ``torso`` the direction from
    there to the top. ``la``, ``ra`` (arms) and ``ll``, ``rl`` (legs) are ``To`` or ``Bones``: l is the
    limb drawn on the left of the picture when the figure faces us. ``face`` is +1 (facing right), -1
    (left) or 0 (facing us): it points the feet. ``order`` lists the parts from back to front."""
    hip: complex
    torso: float = 90.0
    head: float | None = None
    la: object = None
    ra: object = None
    ll: object = None
    rl: object = None
    face: int = 0
    order: tuple = ("ll", "rl", "torso", "head", "la", "ra")
    dashes: tuple = ()
    spin: float = 0.0           # turn the whole figure (and its dashes) about ``pivot``, in degrees
    pivot: complex = 0j
    tag: str = ""

    def solve(self):
        parts, J = self._solve()
        if not self.spin:
            return parts, J
        turn = lambda q: self.pivot + (q - self.pivot) * pol(self.spin)
        for p in parts:
            p.prims = [_turned(pr, turn) for pr in p.prims]
        return parts, {k: turn(v) for k, v in J.items()}

    def _solve(self):
        """Parts (in drawing order, back first), joints and the dash shapes."""
        hip = P(self.hip)
        up = pol(self.torso)
        neck = hip + up * TORSO_LEN
        shoulder = neck - up * SHOULDER
        head_dir = pol(self.head if self.head is not None else self.torso)
        head = neck + head_dir * (TORSO / 2 + NECK + HEAD)
        t = self.tag
        J = {"hip": hip, "neck": neck, "shoulder": shoulder, "head": head}
        parts = {"torso": Part("torso", [Rod(hip, neck, TORSO / 2)], frozenset({t + "shoulder", t + "hip"})),
                 "head": Part("head", [Disc(head, HEAD)], frozenset())}
        down = -up
        arms = {"la": self.la or Bones(ang(down) - 12, ang(down) - 4), "ra": self.ra or Bones(ang(down) + 12, ang(down) + 4)}
        for name, spec in arms.items():
            elbow, hand = limb(shoulder, spec, UPPER_ARM, FOREARM)
            d = (hand - elbow) / abs(hand - elbow)
            if getattr(spec, "foot", None) is not None:
                d = pol(spec.foot)
            mitt = hand + d * 6
            s = name[0]
            J[s + "e"], J[s + "h"] = elbow, mitt
            parts[name] = Part(name, [Bar(shoulder, elbow, LIMB / 2), Disc(elbow, LIMB / 2 + 0.5),
                                      Bar(elbow, hand, LIMB / 2), Disc(mitt, HAND)], frozenset({t + "shoulder"}))
        legs = {"ll": self.ll or To(hip.real - 34, GROUND, -1), "rl": self.rl or To(hip.real + 34, GROUND, 1)}
        for name, spec in legs.items():
            knee, ankle = limb(hip, spec, THIGH, SHIN)
            s = name[0]
            facing = self.face or (-1 if s == "l" else 1)
            foot = spec.foot if spec.foot is not None else ang(ankle - knee) + 90 * facing
            toe = ankle + pol(foot, FOOT_LEN)
            J[s + "k"], J[s + "a"], J[s + "f"] = knee, ankle, (ankle + toe) / 2
            parts[name] = Part(name, [Bar(hip, knee, LIMB / 2), Disc(knee, LIMB / 2 + 0.5),
                                      Bar(knee, ankle, LIMB / 2), Rod(ankle, toe, FOOT)], frozenset({t + "hip"}))
        ordered = [parts[n] for n in self.order]
        return ordered, J

    def dash_shapes(self, J, size: float = 1.0):
        out = []
        reach = {"h": HAND, "f": FOOT, "head": HEAD, "hip": TORSO / 2, "neck": TORSO / 2}
        for b in self.dashes:
            if isinstance(b.at, str):
                c = J[b.at]
                r = reach.get(b.at, reach.get(b.at[-1], LIMB / 2)) * size
            else:
                c, r = P(b.at), 0.0
            r0 = r + LINE + b.gap + b.shift
            for i in range(b.n):
                a = b.deg + self.spin * (isinstance(b.at, str)) + (i - (b.n - 1) / 2) * b.spread
                u = pol(a)
                out.append(Rod(c + u * (r0 + DASH / 2), c + u * (r0 + b.length - DASH / 2), DASH / 2))
        return out


@dataclass(frozen=True)
class Hull:
    """Two discs joined by their outer tangents: a tube that tapers from ``r1`` at ``p`` to ``r2`` at ``q``."""
    p: complex
    q: complex
    r1: float
    r2: float

    def contour(self, grow: float = 0.0):
        p, q, r1, r2 = self.p, self.q, self.r1 + grow, self.r2 + grow
        d = q - p
        phi = ang(d)
        beta = math.degrees(math.acos((r1 - r2) / abs(d)))
        start = p + pol(phi + beta, r1)
        segs = [(start, q + pol(phi + beta, r2))]
        segs += _arc(q, r2, phi + beta, -2 * beta)
        segs.append((q + pol(phi - beta, r2), p + pol(phi - beta, r1)))
        segs += _arc(p, r1, phi - beta, -(360 - 2 * beta))
        last = segs[-1]
        segs[-1] = last[:-1] + (start,)
        return _cw(segs)


@dataclass
class Thing:
    """A sign that is not a figure: a ball, a tube. It has the same line and the same dashes."""
    prims: list
    dashes: tuple = ()
    spin: float = 0.0
    tag: str = ""

    def solve(self):
        return [Part("thing", list(self.prims), frozenset())], {}

    def dash_shapes(self, J, size: float = 1.0):
        return Fig.dash_shapes(self, J)


def tube(*pts, r: float = LIMB / 2):
    """A bent tube through points, like a limb: bars, with a ball at every bend and at both ends."""
    pts = [P(p) for p in pts]
    out = [Disc(pts[0], r + 0.5), Disc(pts[-1], r + 0.7)]
    for a, b in zip(pts, pts[1:]):
        out.append(Bar(a, b, r))
    out += [Disc(p, r + 0.5) for p in pts[1:-1]]
    return out


# ------------------------------------------------------------------------------------ the drawing


@dataclass
class Drawing:
    ink: list           # the line under the color, with the dashes
    color: list         # the color: the body less its inside lines
    solid: list         # one color: the body, slightly fuller, with its inside lines cut
    line: list          # one color: the line only, as chalk on a board
    dashes: list
    bounds: tuple


def paint(parts, grow: float = 0.0, line: float = LINE, joints: dict | None = None, size: float = 1.0):
    """The body less its inside lines. Parts are back to front; each cuts its line into the parts
    behind it, except near a joint that the two share."""
    fill: list = []
    shapes = [shape(p.prims, grow) for p in parts]
    for k, part in enumerate(parts):
        mine = shapes[k]
        ring = cut(shape(part.prims, grow + line), mine)
        cuts = []
        for j, other in enumerate(parts[:k]):
            c = clip(ring, shapes[j])
            if not c:
                continue
            shared = part.joints & other.joints
            if shared:
                c = cut(c, [circle(joints[s].real, joints[s].imag, JOINT_CLEAR * size + grow) for s in shared])
            cuts += c
        if cuts:
            fill = cut(fill, merge(cuts))
        fill = merge(fill + mine)
    return fill


def _moved(contours, dy):
    return [transform_contour(c, lambda q: q + 1j * dy) for c in contours]


def draw(figs, lift: float | None = None, size: float = 1.0) -> Drawing:
    """The drawing of a glyph. It is moved so that its lowest ink is on the baseline, or, with ``lift``, so
    that the body is ``lift`` units in the air (the dashes under it may go lower, not under 0).

    ``size`` draws larger people: a figure that sits is only 500 units tall, so a letter of seated figures
    is drawn with larger people to stand as tall as the others. The line keeps its width: it is the same
    marker, drawing a bigger person."""
    parts, joints, dashes = [], {}, []
    for i, f in enumerate(figs):
        f.tag = f"f{i}."
        ps, J = f.solve()
        if size != 1.0:
            for part in ps:
                part.prims = [_sized(pr, size) for pr in part.prims]
            J = {k: v * size for k, v in J.items()}
        parts += ps
        joints.update({f.tag + k: v for k, v in J.items()})
        dashes += f.dash_shapes(J, size)
    prims = [pr for p in parts for pr in p.prims]
    outline = shape(prims, LINE)
    color = paint(parts, joints=joints, size=size)
    dash = shape(dashes) if dashes else []
    ink = merge(outline + dash)
    # one color: grow the body by half a line, so it is as heavy as the color figure, and cut thinner lines
    solid_body = paint(parts, grow=LINE * 0.5, line=LINE * 0.8, joints=joints, size=size)
    solid = merge(solid_body + dash)
    chalk = merge(cut(outline, color) + dash)
    if lift is None:
        dy = -contour_bounds(ink)[1]
    else:
        dy = lift - contour_bounds(outline)[1]
    ink, color, solid, chalk, dash = (_moved(x, dy) for x in (ink, color, solid, chalk, dash))
    return Drawing(ink, color, solid, chalk, dash, contour_bounds(ink))


def check(name: str, d: Drawing):
    """Problems a pose can have: ink under the baseline, dashes touching the body."""
    problems = []
    x0, y0, x1, y1 = d.bounds
    if y0 < -1:
        problems.append(f"{name}: ink {-y0:.0f} units under the baseline")
    if d.dashes:
        body = cut(d.ink, d.dashes)
        if clip(d.dashes, body):
            problems.append(f"{name}: a dash touches the body")
    return problems


# --------------------------------------------------------------------------------------- recipes

@lru_cache(maxsize=None)
def drawing(name: str, build) -> Drawing:
    figs = build()
    if isinstance(figs, (Fig, Thing)):
        figs = [figs]
    return draw(list(figs), getattr(build, "lift", None), getattr(build, "size", 1.0))


def size(k: float):
    """A pose of larger people: every figure of the letter is ``k`` times as large."""
    def deco(fn):
        fn.size = k
        return fn
    return deco


def air(lift: float):
    """A pose in the air: its body is ``lift`` units above the baseline."""
    def deco(fn):
        fn.lift = lift
        return fn
    return deco


def _recipe(name: str, build, key: str, mirror: bool, style: str):
    def recipe(g):
        d = drawing(name, build)
        x0, _, x1, _ = d.bounds
        width = x1 - x0 + 2 * SIDE
        if mirror:
            f = lambda c: reverse_contour(transform_contour(c, lambda q: complex(x1 + SIDE - q.real, q.imag)))
        else:
            f = lambda c: transform_contour(c, lambda q: complex(q.real - x0 + SIDE, q.imag))
        base = {"color": d.solid, "solid": d.solid, "line": d.line}[style]
        for c in base:
            g.shape(f(c))
        if style == "color":
            g.layers = [("ink", [f(c) for c in d.ink]), (key, [f(c) for c in d.color])]
        g.frame(width, 0, 0)
    return recipe


def recipes(letters: dict, keys: dict, mirrored: str, extras: dict | None = None, style: str = "color") -> Recipes:
    """A to Z, a to z (the next color, and mirrored when the letter in ``mirrored`` still reads), extras.

    ``letters`` is {letter: (name, build)}; ``keys`` is {letter: palette key}; ``extras`` is
    {glyph name: (character, name, build, key)}.
    """
    r = Recipes()

    def space(g):
        g.frame(0, 0, 0)
        g.fixed_advance(SPACE)
    r["space"] = Recipe("space", space, 0x20, "lower")
    order = sorted(set(keys.values()))
    for letter, (name, build) in letters.items():
        key = keys[letter]
        r[letter] = Recipe(letter, _recipe(name, build, key, False, style), ord(letter), "upper")
        lo = letter.lower()
        nxt = order[(order.index(key) + 1) % len(order)]
        r[lo] = Recipe(lo, _recipe(name, build, nxt, letter in mirrored, style), ord(lo), "lower")
    for glyph, (ch, name, build, key) in (extras or {}).items():
        r[glyph] = Recipe(glyph, _recipe(name, build, key, False, style), ord(ch), "figure")
    return r
