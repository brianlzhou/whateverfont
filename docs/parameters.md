# Parameters

A `Params` object is one style of a typeface. `preset("flare")` returns one, and `.but(...)` or keyword
arguments to `preset` change it. All lengths are in font units, 1000 per em.

Run `whateverfont probe DIR` after a change. It reports the stem, hairline and counter that the numbers produce.

## Vertical metrics

| Name | Default | Meaning | Usual range |
|---|---|---|---|
| `cap` | 700 | Capital height. | 660 to 740 |
| `xh` | 500 | x-height. A larger value reads bigger at the same size. | 440 (bookish) to 540 (interface) |
| `asc` | 740 | Height of b, d, h, k, l. | `cap` to `cap + 60` |
| `desc` | -215 | Depth of g, j, p, q, y. | -180 to -250 |
| `overshoot` | 11 | How far round letters pass the baseline and x-height. | 8 to 15 |

## Stroke

| Name | Default | Meaning | Usual range |
|---|---|---|---|
| `weight` | 82 | Thickness of a lowercase vertical stem. | 40 thin, 60 light, 82 regular, 110 semibold, 150 bold |
| `cap_weight` | 1.10 | Capital stems relative to lowercase stems. | 1.05 to 1.15 |
| `contrast` | 0.86 | Thin stroke divided by thick stroke. 1 is monoline. | 0.9 sans, 0.6 flare, 0.35 broad pen, 0.2 didone |
| `stress` | 0 | Pen angle in degrees. 0 puts the thin parts at the top and bottom of an `o`. | 0 to 35 |
| `round_weight` | 1.04 | Round strokes relative to straight stems. | 1.0 to 1.08 |
| `join` | 0.74 | Thinning where an arch leaves a stem. | 0.65 to 1.0 |

Bold weights get thinner horizontals and less flare automatically (`eff_contrast`, `eff_flare`).

## Proportions

| Name | Default | Meaning | Usual range |
|---|---|---|---|
| `width` | 1.0 | Scales every counter. | 0.56 compressed, 0.75 condensed, 1.15 wide |
| `counter` | 285 | White inside the `n` at width 1. | 250 to 310 |
| `round_width` | 1.0 | Width of the round letters `o c e b d p q s` and of the figures, relative to the `n`. | 1.0 even, 1.17 interface sans, 1.28 an `o` close to a circle |
| `cap_width` | 1.0 | Width of the capitals, relative to the lowercase. | 1.0 to 1.15 |
| `classical` | 0 | 0 gives capitals of even width. 1 gives Roman widths: wide `O`, narrow `E` and `S`. | 0 to 1 |
| `superness` | 0 | 0 gives elliptical rounds. 1 gives squarish rounds. | 0 to 0.9 |
| `aperture` | 0.5 | How open `c`, `e`, `s` and `a` are. | 0.2 closed, 0.9 open |

## Terminals

| Name | Default | Meaning | Usual range |
|---|---|---|---|
| `flare` | 0 | How much a stem widens at its end. 0.3 means 30% wider. | 0 sans, 0.2 hint, 0.35 flare serif, 0.7 wedge |
| `flare_len` | 190 | Length of the widening zone. | 140 short and sharp, 260 long and gentle |
| `flare_taper` | 1.9 | 1 is a straight wedge. Higher values make the flare start late and suddenly. | 1 to 2.5 |
| `roundness` | 0 | 0 gives sharp corners. 1 gives fully round ends. | 0 to 1 |
| `cut` | `"square"` | How curved strokes end: `"square"` to the stroke, `"horizontal"`, `"vertical"` or `"flat"`. With `"flat"`, `c e s a` end level, the arm of `r` and the hooks of `f t j` stop when they are level and end upright, and the tails of `g J 3 5 6 9` are cut square, as in a grotesque. | |
| `apex` | 0.75 | Flat width of the points of `V`, `A`, `W`, relative to the stem. 0 is a sharp point. | 0 to 1 |
| `arm` | 1.0 | Reach of the arm of `r`, the hooks of `f`, `t` and `j`, and the bars of `f` and `t`. | 1.0, and 1.15 to 1.25 at a bold pole |

## Serifs

| Name | Default | Meaning | Usual range |
|---|---|---|---|
| `serif` | 0 | Slab serifs: how far a slab reaches past the edge of a stem, on each side. 0 gives no serifs. | 30 to 70 |
| `serif_weight` | 1.0 | Thickness of a slab, relative to a horizontal stroke. | 0.7 to 1.1 |

With `serif` above 0, every free end of a vertical stem gets a slab: a foot on both sides at the baseline
and the descender, and a head at the x-height, the ascender and the cap height. A lowercase head has a slab
on the left only (`n m r i u b h k l p`); a capital has one on both sides. The arms of `E F L T Z` and of
`2 5 7` end in short vertical beaks. `a` and `d` get a short spur at the foot, `q` and `g` one at the top.
Diagonals get a slab across their horizontally cut ends. Slabs that face each other across a narrow
counter (`m`, `n`, `H` in a monospaced cell) are shortened, so their ends never touch.

Slabs reach into the sidebearings, as in any serif face: the stems keep their distance. In a monospaced
family the cell fitting counts them, and with slabs `m w M W` are drawn lighter and more open. Round ends
(`roundness` near 1) and low contrast give a typewriter; square ends and `serif_weight` near 1 give a
Clarendon-like slab serif. Bracketed serifs (curved where the slab meets the stem) are not available yet.

`serif` is also a structure choice, because slabs are extra strokes. In a variable font every master must
have `serif` above 0, or every master 0. The length and the weight of the slabs may vary along an axis:
`{700: {"weight": 112, "serif": 44}}`. `whateverfont build` warns and builds no variable font if a family mixes
the two.

## Slope and rhythm

| Name | Default | Meaning | Usual range |
|---|---|---|---|
| `slant` | 0 | Degrees. Positive leans right. | 8 to 12 for an italic |
| `spacing` | 1.0 | Scales every sidebearing. | 0.9 tight display, 1.08 small text, 1.2 interface text |
| `word_space` | 1.0 | Scales the space between words. | 1.0 to 1.25 |
| `kerning` | 1.0 | Scales automatic kerning. 0 turns it off. | 0 to 1.2 |
| `mono` | 0 | 0 is proportional. Any other value is the width of every glyph: a monospaced font. | 580 to 620 |

A sans for an interface has a narrow `n` next to a wide `o`, wide capitals and loose spacing: lower `counter`
to about 265, then raise `round_width`, `cap_width`, `spacing` and `word_space`. `whateverfont examples dayshift`
prints a project that does this. In a heavy weight the arms of `f`, `t` and `r` get short next to their stems:
raise `arm` at the bold pole of the weight axis.

Stems heavier than about 165 units (weight 150 with the capital and round multipliers) start to close the
counters and hooks of `a`, `e`, `s`, `g`, `5`, `6`, `9` and `&`. Raise `counter` and `width` with the weight,
and look at those letters on a proof. `whateverfont probe` warns when a design passes this point. Letters stay
whole to about weight 200.

## Structure

These cannot vary along an axis.

| Name | Default | Meaning |
|---|---|---|
| `a_story` | 2 | 2 draws the two-story `a`. 1 draws the round one. |
| `dot` | `"auto"` | Shape of dots: `"round"`, `"square"`, `"diamond"`. `"auto"` decides from flare and roundness. |

Whether `serif` is 0 is a structure choice too: see [Serifs](#serifs).

## Axes

An axis maps a number the reader chooses to parameter values:

```python
Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 50}, 800: {"weight": 150}})
```

The arguments are the tag, the name, the minimum, the default and the maximum, then the poles. The default
must not have a pole: it is the family's base style. To change the regular style, change the base. A pole may set several parameters, for example an italic that
also narrows: `{-11: {"slant": 11, "width": 0.955}}`.

Registered tags are lowercase: `wght`, `wdth`, `slnt`, `opsz`. Your own tags are four capitals: `FLAR`, `ROND`.
The effects of several axes add up. Any numeric parameter can be on an axis.

## Presets

`whateverfont presets` lists them: `grotesk`, `humanist`, `geometric`, `flare`, `glyphic`, `rounded`, `broadnib`,
`condensed`, `mono`, `technical`, `typewriter`. A preset is a starting point that already hangs together.
`typewriter` is monospaced, with slab serifs, round ends, low contrast and a generous x-height.

## The family

`Family(...)` takes the design (`name`, `base`, `axes`, `styles`, `recipes`) and what goes into the font
file: `description`, `designer`, `copyright`, `license`, `sample`. Two more settings are for drawings that
are taller than letters, such as framed capitals or a picture font: `ascent` and `descent` set the top and
the bottom of a line of text. Leave them out and they follow `asc` and `desc`: the top is `asc` + 70, and at
least 940; the bottom is `desc` - 40, and at most -260.

`figures` sets the default figures. `"tabular"` (the default) gives every figure one advance, so columns of
numbers line up; the `pnum` feature gives proportional ones. `"proportional"` gives each figure the width of
its shape, for a text face; the `tnum` feature gives the tabular ones back. A monospaced family keeps one
width whatever this says.

The basic set has 800 code points: GF Latin Core, Vietnamese, Pinyin, letters for Azerbaijani, Yoruba, Igbo
and Hausa, currency, math, arrows, shapes, superscripts, subscripts and fractions (605), and modern Greek
and Cyrillic (195). `latin(greek=False, cyrillic=False)` leaves Greek and Cyrillic out. Every font gets the
OpenType features `frac`, `numr`, `dnom`, `sups`, `subs`, `sinf`, `ordn`, `zero`, `case` and `pnum` for the
glyphs it has (see [recipes](recipes.md)).

The Vietnamese capitals with two marks (`Ẫ`, `Ấ`, `Ẳ`) are drawn to fit under that top: their marks get
flatter and closer, and in heavy weights lighter, until they fit. So Vietnamese needs no taller line. An
effect that grows the letters (snow, a glow) can still reach past it; `whateverfont probe` names those
glyphs. Windows clips at the font's `usWinAscent` and `usWinDescent`, and those always hold the tallest and
the deepest glyph, in every master of a variable font.
