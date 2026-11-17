# Effects, color and picture fonts

Parameters and recipes draw letters with a pen. An effect works on the letters after they are drawn: it cuts
bridges for a stencil, engraves a line, stacks color layers for a glow, or paints the letter with brush
marks. `whateverfont.effects` holds the ones that ship, and `wrapped` lets you write your own.

```python
from whateverfont import Family, effects, latin
from whateverfont.presets import preset

FAMILY = Family(
    name="Marquee",
    base=preset("geometric", weight=150),
    recipes=effects.inline(latin()),          # every letter, then the effect
)
```

An effect takes a recipe set and returns a new one, so effects can be chained:
`effects.rough(effects.stencil(latin()))`. An effect also works on a font of another script that
`whateverfont retrace --effect` redraws from an open font: see [scripts](scripts.md).

## Shape effects (one color)

| Effect | What it does | Options, with their defaults |
|---|---|---|
| `stencil(recipes)` | A vertical bridge through every closed counter. | `gap=0.30`: the bridge width, as a share of the stem. `least=20`: its minimum, in units. |
| `inline(recipes)` | A white line down the middle of every stroke. Needs a heavy weight. | `width=0.20`: the line. `rim=0.22`: the least ink left on each side. Both are shares of the stem. |
| `outlined(recipes)` | Hollow letters. | `width=0.24`: the line that is left, as a share of the stem. `least=12`: its minimum, in units. |
| `shadow(recipes)` | A block shadow, set apart by a thin white line. | `dx=34`, `dy=-34`: where the shadow falls, in units. `gap=12`: the white line, in units. |
| `stripes(recipes)` | Horizontal white lines through the lower part of the letters. | `count=5`. `gap=0.34`: the white, as a share of each step. `low=0.0`, `high=0.52`: where the lines are, as shares of the cap height. |
| `rough(recipes)` | A wobbling outline, as if cut by hand. | `amount=5`: how far a point may move, in units. `scale=130`: the length of one wave, in units. `seed=0`. |

Units are font units, 1000 to the em. Every effect also takes `names=[...]` to limit it to some glyphs.

A shape effect changes the outline after the strokes are expanded, so the family gets static fonts only.
`whateverfont build` says so in a warning if the family has axes. Each named style is still built exactly.

## Color effects

A color effect sets layers. Each layer has a key, and the family's `palettes` give every key a color.
Colors are `"#rrggbb"`, or `"#rrggbbaa"` for a transparent one.

| Effect | Keys | What it does |
|---|---|---|
| `glow(recipes, size=80)` | `glow1` `glow2` `glow3` `halo` `tube` | A lit tube. `glow_palette("#FF2E9A")` makes the palette. |
| `layered_shadow(recipes)` | `side` `face` | A block shadow in its own color. |
| `banded(recipes, bands=5)` | `band0` (lowest) to `band4` | Horizontal bands: a sunset, a flag. |
| `mosaic(recipes, colors=4)` | `grout`, `c0` to `c3` | Small uneven tiles. |
| `dotted(recipes, colors=4)` | `base`, `c0` to `c3` | Whole dots, like a pointillist painting. |
| `painted(recipes, colors=5)` | `base`, `c0` to `c4` | Short brush marks that follow the pen. |

`paint_palette(base, [c0, c1, ...])` makes a palette for the last three.

```python
PAINT = Family(
    name="Impasto",
    base=preset("humanist", weight=140),
    recipes=effects.painted(latin().only(), colors=5, tone="along"),
    palettes={
        "Night": effects.paint_palette("#16233F", ["#1F3A6E", "#2F62A6", "#6FA3D8", "#E9D36B", "#F6EDB2"]),
        "Wheat": effects.paint_palette("#7A4A1E", ["#A8641F", "#D08A2A", "#E9B44C", "#F3D27A", "#FBEFC2"]),
    },
)
```

`tone` decides which color a mark gets, from the first color (0) to the last (1): `"along"` makes streaks
that follow the stroke, `"across"` is bright in the middle of the stroke, `"light"` is lit from the top left,
`"rise"` runs from dark feet to bright heads, and `"random"` mixes. It can also be a function of
`(along, across, x, y, rng)`.

Five things to know about color fonts:

- **A proof needs a ground that shows every color.** White snow does not show on white paper. `whateverfont look`
  gives such a palette a dark ground and says so. `--bg "#12372A"` sets the ground you want, and
  `look --directions` gives the row its own band.

- **The bottom layer sets the spacing.** Kerning measures the first layer, so make it the shape that should
  keep its distance from the neighbors: the letter, or a tile. A glow or a halo as the first layer pushes
  the letters apart by its own width.

- **Keep the whole set unless a glyph is heavy.** `latin()` has 847 glyphs for 800 code points, so no accent,
  currency sign or arrow falls back to another font. An effect that adds a few layers (Gilt, Kanagawa,
  Pointille) makes a file of 500 to 800 KB; a shape effect (inline, stripes) one of about 60 KB. A painted
  glyph is hundreds of marks and about 10 KB, so a painted family keeps a small set: `latin().only()` keeps letters, figures and common
  signs (about 95 glyphs); `latin().only("ABC...")` keeps what you name. `latin().only(vietnamese=True)` adds
  the Vietnamese alphabet (about 230 glyphs in all). A small set gets the features its glyphs allow, which is
  usually none. In a heavy family the marks of some capitals (`Ż Ố Ǘ`) rise above the default top of the
  line: `whateverfont probe --problems` names them and the `ascent` to give the family.
- **A color family has no variable font** (the color format, COLR version 0, has no axes). Every named style
  is a static color font.
- **Look at it in a browser.** `whateverfont look` shows the first palette. The review board shows all of them,
  with a button for each. In CSS, choose a palette with `font-palette`.

## Your own effect

`wrapped(recipes, effect)` runs `effect(g, ink)` after each glyph is drawn. `g` is the builder (see
[recipes](recipes.md)) and `ink` is the merged outline of the letter.

```python
from whateverfont import effects
from whateverfont.outline import dilate

def halo(recipes, size=30):
    def effect(g, ink):
        g.layers = [("halo", dilate(ink, size)), ("letter", ink)]      # bottom layer first
    return effects.wrapped(recipes, effect)
```

An effect can:

- set `g.layers` to `[(key, contours), ...]` for a color font;
- add contours to `g.cutouts`, which are removed from the letter (the stencil does this);
- call `effects.redraw(g, contours)` to replace the outline.

Inside an effect, `g.name` is the glyph name (`"A"`, `"eacute"`, `"zero"`), `g.case` is `"upper"`,
`"lower"` or `"figure"`, `g.sw` is the stem thickness, `g.cap` and `g.xh` are the heights, and `g.strokes`
is the skeleton.

### Contours

A point is a Python `complex` number: `complex(x, y)`, in font units, y up. A segment is a tuple of points:
two for a line, four for a cubic curve (start, two handles, end). A contour is a list of segments in which
each one starts where the last one ended, and the last ends where the first started.

```python
square = [(0j, 100j), (100j, 100 + 100j), (100 + 100j, 100 + 0j), (100 + 0j, 0j)]
```

Ink runs clockwise and a counter (a hole) runs counter-clockwise. `whateverfont.geom.contour_area(c)` is
negative for ink and positive for a counter, and `contour_bounds([c])` returns `(x0, y0, x1, y1)`.
`transform_contour(c, fn)` maps every point through `fn`.

### Tools

| In `whateverfont.outline` | Returns |
|---|---|
| `union(contours)` | The contours merged, with no overlaps. |
| `difference(contours, cutters)` | The first shape with the second removed. |
| `intersection(contours, clip)` | The part the two shapes share. |
| `dilate(contours, amount)` | The shape grown by `amount` on every side. Counters shrink. |
| `rect(x0, y0, x1, y1, radius=0)` | One contour: a rectangle, with round corners if asked. |
| `circle(cx, cy, r)` | One contour. |
| `depths(contours)` | For each contour: 0 for an outside, 1 for a counter, 2 for an island in a counter. |

| In `whateverfont.effects` | Returns |
|---|---|
| `ink(g)` | The merged outline of what `g` has drawn. |
| `erode(contours, amount)` | The shape shrunk by `amount`. |
| `band(contours, width)` | A band along the outline. |
| `extrusion(contours, dx, dy)` | The area the shape sweeps when it slides: a block shadow. |
| `inside(contours)` | A function: `inside(shape)(complex(x, y))` is true for a point in the ink. |
| `brush_mark(center, direction, length, width, bend=0)` | One contour: a brush mark. |
| `stroke_marks(g, dab=(84, 30), ...)` | `[(contour, tone), ...]`: marks along the skeleton of `g`. |
| `field_marks(box, flow, ...)` | `[(contour, tone), ...]`: marks that fill a box and follow `flow(point)`. |
| `paint_layers(marks, colors, rng, clip=...)` | `[(key, contours), ...]` with keys `c0`, `c1`, ... ready for `g.layers`. |
| `seed_for(g, seed=0)` | A `random.Random` that gives this glyph the same numbers in every build. |
| `redraw(g, contours)` | Nothing. Replaces the drawing of `g`. |

`examples/starry/starry.py` uses most of them to set a letter in a painted sky.

An accented letter is drawn plain and gets the effect once. A project that redraws `e` gets its own `e`
under every accent, in `æ` and in `œ`.

## Decorated capitals

`whateverfont.ornament.illuminate(latin())` sets each capital on a framed field with holly and vines. See
[recipes](recipes.md#color-layers) and `examples/wassail`.

## Picture fonts

A font does not have to hold letters. A recipe may draw anything, and `g.shape(contour)` or
`g.polygon(points)` adds a filled shape, so a typed `A` can give a bird. `examples/aviary` builds 26 birds
from circles and straight lines, as a color font with four palettes, a one-color cut and a line drawing.

For a picture font:

- Set `kerning=0` in the base, and end each recipe with `g.frame(width, 0.3, 0.3)` or a fixed advance.
- If the pictures are taller than letters, set `ascent` and `descent` on the family
  (`Family(..., ascent=1100, descent=-300)`), or programs will clip them. `whateverfont probe` tells you when.
- Draw every character you promise. `whateverfont probe` lists empty glyphs.

## Monospaced fonts

Set `mono` in the base to the width of the cell, or start from `preset("mono")`:

```python
FAMILY = Family(name="Tally Mono", base=preset("mono"),
                axes=[Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 50}, 700: {"weight": 124}})],
                styles={"Regular": {}, "Bold": {"wght": 700}})
```

Every glyph then has that advance. The engine fits each one to the cell: a letter that is too wide (`m`,
`w`, `@`) is drawn with narrower counters, so its stems keep their weight, and a letter that is too narrow
(`r`, `f`, `t`) is drawn wider. A monospaced family uses the `mono()` recipe set, which gives `i`, `j`, `l`,
`I` and `1` bars and feet and puts a dot in the zero. Kerning is off, and the font files are flagged as
fixed-pitch, so terminals and editors list them.

- Any preset can be monospaced: `preset("technical", mono=580)` or `preset("humanist", mono=620)`. A family
  whose base has `mono` set gets the `mono()` recipes unless you pass `recipes`.
- `preset("typewriter")` is a monospaced slab serif. With serifs on, `i j l I 1` take the typewriter forms (a
  flag and a foot of slab weight), `r` stands on a wide foot, and `m w M W` are drawn lighter and more open.
  The slabs count when a letter is fitted to the cell.
- An effect in a monospaced family runs once per glyph: the engine fits the plain letter to the cell, then
  applies the effect. An effect that places its marks in the cell itself (a dot-matrix grid) can set
  `g.full_cell = True` and `g._frame = (g.p.mono, 0.5, 0.5)` before it redraws; see `examples/greenbar`.
- The `mono()` set draws the signs of code on one axis and as heavy as the letters (`+ - = < > * ~ ^`),
  deep brackets, a comma with a long tail, an `l` with a tail and a dotted zero. It also holds the 160
  box-drawing characters and block elements (U+2500 to U+259F), which fill the cell so that lines join.
  They join vertically when the family uses the default line height (no `ascent` or `descent`).
- In an italic, letters lean past the cell, as in every monospaced italic. The advance stays the same.
- To fit a glyph of your own to the cell, end its recipe with `g.frame(width, 0.5, 0.5)`: the engine
  centers it. Use `g.frame(None, 0.5, 0.5)` to center what was drawn.
