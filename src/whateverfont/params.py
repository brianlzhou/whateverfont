"""Design parameters: the numbers that define one style of a typeface.

A :class:`Params` object is a point in the design space. Recipes read it to
decide where skeleton points go and how the pen behaves, so one set of recipes
can produce a hairline grotesque, a bold flare serif or a rounded display face.

Every numeric field can be driven by a variable-font axis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace


@dataclass(frozen=True)
class Params:
    # --- vertical metrics (font units, 1000 per em) --------------------------
    upm: int = 1000
    cap: float = 700.0        #: capital height
    xh: float = 500.0         #: x-height
    asc: float = 740.0        #: ascender height (b d h k l)
    desc: float = -215.0      #: descender depth (g j p q y)
    overshoot: float = 11.0   #: how far rounds pass the baseline and x-height

    # --- stroke ------------------------------------------------------------
    weight: float = 82.0      #: thickness of a lowercase vertical stem
    cap_weight: float = 1.10  #: capital stems, relative to lowercase stems
    contrast: float = 0.86    #: thin stroke / thick stroke (1 = monoline)
    stress: float = 0.0       #: pen angle in degrees (0 = vertical stress)
    round_weight: float = 1.04  #: round strokes, relative to straight stems
    join: float = 0.74        #: thinning where an arch leaves a stem

    # --- proportions -------------------------------------------------------
    width: float = 1.0        #: scales every counter (0.75 condensed, 1.2 wide)
    counter: float = 285.0    #: white inside the lowercase n at width 1
    round_width: float = 1.0  #: round lowercase letters and figures (o c e b d p q s, 0), relative to the n
    cap_width: float = 1.0    #: capitals, relative to the lowercase
    arm: float = 1.0          #: reach of the arm of r, the hooks of f, t and j and the bars of f and t
    classical: float = 0.0    #: 0 = even capital widths, 1 = Roman proportions
    superness: float = 0.0    #: 0 = elliptical rounds, 1 = squarish rounds
    aperture: float = 0.5     #: 0 = closed c/e/s/a terminals, 1 = wide open

    # --- terminals ---------------------------------------------------------
    flare: float = 0.0        #: terminal widening (0.3 = 30% wider than the stem)
    flare_len: float = 190.0  #: length of the widening zone
    flare_taper: float = 1.9  #: 1 = straight wedge, higher = sudden flare
    roundness: float = 0.0    #: 0 = sharp corners, 1 = fully round terminals
    cut: str = "square"       #: curved terminals: "square", "horizontal", "vertical" or "flat"
    apex: float = 0.75        #: flat width of V/A/W points, relative to the stem

    # --- serifs --------------------------------------------------------------
    #: Slab serifs: how far a slab reaches past the edge of a stem, on each side. 0 = no serifs.
    #: Turning serifs on adds strokes, so it is a structure choice: every master of a variable
    #: font must have serif > 0, or every master serif = 0. The length may vary along an axis.
    serif: float = 0.0
    serif_weight: float = 1.0  #: thickness of a slab, relative to the horizontal stroke

    # --- slope and rhythm ---------------------------------------------------
    slant: float = 0.0        #: degrees, positive leans right
    spacing: float = 1.0      #: scales sidebearings
    word_space: float = 1.0   #: scales the space between words
    kerning: float = 1.0      #: scales automatic kerning (0 = none)
    mono: float = 0.0         #: 0 = proportional; otherwise every glyph is this wide (600 is usual)

    # --- structure (not interpolable) ----------------------------------------
    a_story: int = 2          #: 2 = double-story a, 1 = single-story
    dot: str = "auto"         #: "auto", "round", "square" or "diamond"

    def but(self, **changes) -> "Params":
        """A copy with some fields changed."""
        return replace(self, **changes)

    def to_dict(self) -> dict:
        return asdict(self)

    # --- derived -------------------------------------------------------------
    @property
    def eff_contrast(self) -> float:
        """Contrast after weight compensation: bold needs thinner horizontals."""
        k = 1.0 - 0.0022 * (self.weight - 82.0)
        return max(0.08, min(1.0, self.contrast * max(0.62, min(1.12, k))))

    @property
    def eff_flare(self) -> float:
        """Flare after weight compensation: heavy strokes need less of it."""
        return self.flare * max(0.5, min(1.2, 1.0 - 0.0045 * (self.weight - 82.0)))

    @property
    def n_counter(self) -> float:
        """White inside the n. Counters close up a little as weight grows."""
        c = self.counter * self.width - 0.42 * (self.weight - 82.0)
        return max(c, 0.9 * self.weight, 60.0)

    @property
    def line_top(self) -> float:
        """Top of a line of text: the default ascent of the font."""
        return max(self.asc + 70, 0.94 * self.upm)

    @property
    def line_bottom(self) -> float:
        """Bottom of a line of text (negative): the default descent of the font."""
        return min(self.desc - 40, -0.26 * self.upm)

    @property
    def superk(self) -> float:
        """Bezier handle length for a quarter round."""
        return 0.5523 + 0.24 * max(0.0, min(1.0, self.superness))


NUMERIC_FIELDS = tuple(
    f.name for f in fields(Params) if f.type in ("float", "int") and f.name != "upm"
)
STRUCTURE_FIELDS = ("a_story", "dot", "cut", "upm")


def lerp_params(a: Params, b: Params, t: float) -> Params:
    """Blend two parameter sets. Structure fields come from ``a``."""
    changes = {}
    for name in NUMERIC_FIELDS:
        if name in STRUCTURE_FIELDS:
            continue
        va, vb = getattr(a, name), getattr(b, name)
        if va != vb:
            changes[name] = va + (vb - va) * t
    return a.but(**changes)
