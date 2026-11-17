"""Five display faces, each made with one effect from whateverfont.effects. See docs/effects.md."""

from whateverfont import Family, effects, latin
from whateverfont.presets import preset

SET = latin()

MARQUEE = Family(
    name="Marquee",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Tall geometric capitals with an engraved line, for a cinema sign.",
    base=preset("geometric", weight=168, contrast=0.72, width=0.86, xh=470, cap=720, counter=300, classical=0.2, apex=0.3),
    recipes=effects.inline(SET, width=0.17, rim=0.24), sample="Now Showing",
    ascent=990, descent=-275)          # room for the marks of heavy capitals (Ż Ǘ)

TURBO = Family(
    name="Turbo",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Wide, leaning and striped, like the side of a 1970s racing car.",
    base=preset("technical", weight=182, width=1.18, slant=12, superness=0.6, roundness=0.35, xh=540, counter=300),
    recipes=effects.stripes(SET, count=5, gap=0.36, low=0.02, high=0.56), sample="Turbo 77",
    ascent=985)                        # room for the marks of heavy capitals (Ż Ǘ)

BILLBOARD = Family(
    name="Billboard",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Sign-painter capitals with a block shadow in a second color.",
    base=preset("grotesk", weight=150, width=0.92, contrast=0.8, xh=520, counter=290, roundness=0.2),
    recipes=effects.layered_shadow(SET, dx=34, dy=-34), sample="Fresh Peaches",
    palettes={"Peach": {"side": "#1F3B4D", "face": "#F28F5B"}, "Lime": {"side": "#16302B", "face": "#C6E377"},
              "Paper": {"side": "#C8423B", "face": "#F6EFDF"}})

POINTILLE = Family(
    name="Pointille",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Letters built from whole dots of pure color that mix in the eye.",
    base=preset("rounded", weight=170, xh=530, counter=300),
    recipes=effects.dotted(SET, size=27, colors=5, tone=lambda along, across, x, y, rng: 0.25 + 0.5 * y + rng.uniform(-0.3, 0.3)),
    sample="Sunday Afternoon",
    ascent=980,                        # room for the marks of heavy capitals (Ż Ǘ)
    palettes={"Park": effects.paint_palette("#F3EAD3", ["#2C3E8C", "#3F8F6B", "#E0892B", "#F2C53D", "#F7E9A8"]),
              "Dusk": effects.paint_palette("#2B2140", ["#3B2F7A", "#7A3F8C", "#D4567A", "#F28F5B", "#F9D58A"])})

SUNSET = Family(
    name="Meridian",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Heavy letters filled with the bands of a sky at sunset.",
    base=preset("geometric", weight=176, xh=520, counter=300, apex=0.6),
    recipes=effects.banded(SET, bands=6), sample="Golden Hour",
    ascent=985,                        # room for the marks of heavy capitals (Ż Ǘ)
    palettes={"Sunset": {f"band{i}": c for i, c in enumerate(["#2B1E5A", "#5B2A7A", "#A8327A", "#E0506A", "#F58A4B", "#F9D45C"])},
              "Sea": {f"band{i}": c for i, c in enumerate(["#0B2545", "#13466B", "#1F7A8C", "#4DB6AC", "#A7E0C8", "#F1F7D6"])}})

FAMILY = MARQUEE
DIRECTIONS = [MARQUEE, TURBO, BILLBOARD, POINTILLE, SUNSET]
