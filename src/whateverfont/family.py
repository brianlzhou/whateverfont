"""A family: one set of recipes, a base style, axes, and named styles.

A font project is a Python file that defines ``FAMILY``::

    from whateverfont import Axis, Family, Params

    FAMILY = Family(
        name="Example",
        base=Params(flare=0.3, contrast=0.6),
        axes=[Axis("wght", "Weight", 300, 400, 800,
                   {300: {"weight": 50}, 800: {"weight": 150}})],
        styles={"Regular": {}, "Bold": {"wght": 700}},
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .glyph import Glyph, Recipes
from .params import NUMERIC_FIELDS, Params


@dataclass
class Axis:
    """One axis of variation.

    ``poles`` maps an axis value to the parameters that hold there. The
    default value needs no entry: it is the family's base style.
    Registered tags are lowercase (``wght``, ``wdth``, ``slnt``, ``opsz``);
    custom tags must be four uppercase letters (``FLAR``, ``ROND``).
    """
    tag: str
    name: str
    minimum: float
    default: float
    maximum: float
    poles: dict = field(default_factory=dict)

    def __post_init__(self):
        if len(self.tag) != 4:
            raise ValueError(f"axis tag {self.tag!r} must have four characters, like 'wght' or 'FLAR'")
        if not (self.minimum <= self.default <= self.maximum):
            raise ValueError(f"axis {self.tag}: the default {self.default} is outside {self.minimum}..{self.maximum}")
        if self.default in self.poles:
            raise ValueError(f"axis {self.tag}: remove the pole at {self.default}. The default style is the "
                             f"family's base; set those values there (for example base=preset(...).but(weight=112))")
        for v in self.poles:
            if not (self.minimum <= v <= self.maximum):
                raise ValueError(f"axis {self.tag}: the pole at {v} is outside {self.minimum}..{self.maximum}")

    def delta(self, base: Params, value: float) -> dict:
        """Parameter changes, relative to ``base``, at ``value``."""
        value = max(self.minimum, min(self.maximum, value))
        stops = sorted(set(self.poles) | {self.default})
        if value == self.default or len(stops) < 2:
            return {}
        lo = max((s for s in stops if s <= value), default=stops[0])
        hi = min((s for s in stops if s >= value), default=stops[-1])
        fields_ = set()
        for s in (lo, hi):
            fields_ |= set(self.poles.get(s, {}))
        out = {}
        for f in fields_:
            if f not in NUMERIC_FIELDS:
                raise ValueError(f"axis {self.tag}: {f!r} cannot vary along an axis")
            b = getattr(base, f)
            a_lo = self.poles.get(lo, {}).get(f, b)
            a_hi = self.poles.get(hi, {}).get(f, b)
            t = 0.0 if hi == lo else (value - lo) / (hi - lo)
            out[f] = a_lo + (a_hi - a_lo) * t - b
        return out


@dataclass
class Family:
    name: str
    base: Params = field(default_factory=Params)
    recipes: Recipes | None = None
    axes: list = field(default_factory=list)
    #: Named styles: style name -> axis location, e.g. {"Bold": {"wght": 700}}.
    styles: dict = field(default_factory=lambda: {"Regular": {}})
    designer: str = ""
    description: str = ""
    #: SPDX id or free text. Original fonts made with whateverfont are yours to license.
    license: str = "OFL-1.1"
    license_url: str = "https://openfontlicense.org"
    copyright: str = ""
    version: str = "0.1"
    vendor: str = "FREE"
    #: Text the family was designed around, shown first on proofs.
    sample: str = ""
    #: Color palettes for color fonts: name -> {key: "#rrggbb"}.
    palettes: dict = field(default_factory=dict)
    #: The top and the bottom of a line of text, in font units (the bottom is negative).
    #: None works them out from the ascender and the descender. Set them when the
    #: drawings are taller than letters: a picture font, a framed capital, stacked marks.
    ascent: float | None = None
    descent: float | None = None
    #: The default figures: "tabular" (every figure as wide as the others, so columns of numbers line
    #: up; ``pnum`` gives proportional ones) or "proportional" (each figure as wide as its shape, for
    #: text; ``tnum`` gives tabular ones).
    figures: str = "tabular"

    def __post_init__(self):
        if self.recipes is None:
            from .recipes import latin, mono
            self.recipes = mono() if self.base.mono > 0 else latin()
        if self.figures not in ("tabular", "proportional"):
            raise ValueError(f"figures must be 'tabular' or 'proportional', not {self.figures!r}")
        if self.figures == "proportional":
            from .recipes.forms import proportional_default
            self.recipes = proportional_default(self.recipes)
        if self.base.dot == "auto":
            # decide once for the family, so the dot does not change shape along an axis
            b = self.base
            shape = "round" if b.roundness > 0.55 else ("diamond" if b.flare > 0.22 and b.roundness < 0.2 else "square")
            self.base = b.but(dot=shape)

    # -- the design space -----------------------------------------------------
    def axis(self, tag: str) -> Axis:
        for a in self.axes:
            if a.tag == tag:
                return a
        raise KeyError(tag)

    def default_location(self) -> dict:
        return {a.tag: a.default for a in self.axes}

    def params_at(self, location: dict | None = None) -> Params:
        """The parameters at an axis location. Axis effects add up."""
        location = location or {}
        unknown = set(location) - {a.tag for a in self.axes}
        if unknown:
            raise KeyError(f"{self.name} has no axis {sorted(unknown)}")
        changes: dict = {}
        for a in self.axes:
            for f, d in a.delta(self.base, location.get(a.tag, a.default)).items():
                changes[f] = changes.get(f, 0.0) + d
        return self.base.but(**{f: getattr(self.base, f) + d for f, d in changes.items()})

    def masters(self) -> list:
        """Axis locations of the masters of a variable font.

        The default, plus the minimum and the maximum of every axis that has
        a pole there.
        """
        default = self.default_location()
        out = [dict(default)]
        for a in self.axes:
            for v in (a.minimum, a.maximum):
                if v != a.default:
                    loc = dict(default)
                    loc[a.tag] = v
                    out.append(loc)
        return out

    # -- drawing --------------------------------------------------------------
    def glyph_names(self) -> list:
        return list(self.recipes)

    def draw(self, location: dict | None = None, names=None, keep_structure: bool = False,
             on_error=None, on_trouble=None) -> dict:
        """Draw glyphs at a location. Returns name -> :class:`Glyph`.

        ``on_error(name, exc)`` receives a recipe that failed. ``on_trouble(name, text)`` receives a
        glyph that was drawn, but with a defect that the engine could not repair.
        """
        from . import outline
        p = self.params_at(location)
        out = {}
        for name in (names or self.recipes):
            del outline.trouble[:]
            try:
                out[name] = self.recipes.draw(name, p, keep_structure)
            except Exception as exc:  # a broken recipe should not hide the others
                if on_error is None:
                    raise RuntimeError(f"recipe {name!r} failed: {exc}") from exc
                on_error(name, exc)
            if on_trouble is not None:
                for text in dict.fromkeys(outline.trouble):
                    on_trouble(name, text)
        del outline.trouble[:]
        return out


def style_location(family: Family, style: str) -> dict:
    loc = family.default_location()
    loc.update(family.styles.get(style, {}))
    return loc
