# Writing recipes

A recipe is a function that draws one letter on a builder, `g`. Replace a recipe when parameters cannot give
you the shape you want, or add one for a character that WhateverFont does not have.

```python
from whateverfont import Family, H

FAMILY = Family(name="Example")

@FAMILY.recipes.add("l", "l")            # glyph name, character
def l(g):
    g.stem(g.L, 0, g.asc)                # a stem whose left edge is at x = 0
    g.frame(g.sw)                        # the drawing is one stem wide
```

Look at a recipe while you write it: `whateverfont look DIR --xray "l"` draws the outline with the skeleton, the
nodes and the metric lines on top.

`FAMILY.recipes.add(name, character, case="lower")` registers a recipe. `case` is `"lower"`, `"upper"` or
`"figure"`: capitals and figures get slightly heavier strokes (`cap_weight`) and wider sidebearings, so
give a sign that stands beside figures `case="figure"`.

## The rules

1. **Measure with the builder.** Never write a bare number for a position that should move with the design.
2. **Draw the same structure every time.** A recipe must not add, drop or reorder strokes and nodes depending
   on a parameter. The variable font needs every master to match.
3. **Keep curves wider than the pen.** If the radius of a curve is less than half the stroke width, the inside
   folds. Tie radii to `g.cw` and `g.sw` so they grow with weight.
4. **Bury the ends of joins.** A stroke that joins another should end inside it.

## Measurements

| Name | Meaning |
|---|---|
| `g.sw`, `g.hw`, `g.rw` | Thickness of a vertical stem, a horizontal stroke, a round stroke at its side. |
| `g.xh`, `g.cap`, `g.asc`, `g.desc`, `g.o` | Heights, and the overshoot. |
| `g.L` | x of a stem centerline whose left edge is at 0 (`g.sw / 2`). |
| `g.cw` | The counter of the `n` for this case. Use it as the unit of width. |
| `g.top(h)`, `g.bot` | Centerline y of a round stroke that overshoots height `h`, or the baseline. |
| `g.flat_top(h)` | Centerline y of a bar whose top edge is exactly at `h`. |
| `g.thick(direction)` | Thickness of a stroke that travels along `direction`. |
| `g.capw(even, roman)` | A capital width that follows the `classical` setting. |
| `g.p` | The parameters. |

## Strokes

| Call | Draws |
|---|---|
| `g.stem(x, y0, y1, b=1, t=1)` | A vertical stem. `b` and `t` are the flare at the bottom and top: 1 for a free end, 0 for a buried one. |
| `g.bar(x0, x1, y, l=0, r=0)` | A horizontal bar. |
| `g.line(x0, y0, x1, y1, cut0=H, cut1=H)` | A stroke at any angle. `H` and `V` cut an end horizontally or vertically. |
| `g.ring(x0, y0, x1, y1)` | A closed round, like `o`. The box is the centerline. |
| `g.dot(cx, cy, d=None)` | A dot in the family's dot shape, `d` units across (default: a little wider than a stem). |
| `g.shape(contour)`, `g.polygon(points, radius=0)` | A filled shape of your own. See [contours](effects.md#contours). |
| `g.path(x, y, w=1, fl=0)` | Starts a free stroke. Returns a path builder (below). |

A path builder chains segments and ends with `.done()` or `.close()`:

| Call | Adds |
|---|---|
| `.to(x, y)` | A line. |
| `.arc(x, y, "h")` | A quarter round that leaves horizontally and arrives vertically. `"v"` is the opposite. |
| `.ellipse(cx, cy, rx, ry, a0, a1)` | Part of an ellipse between two angles (0 is east, 90 is north). |
| `.curve(h1, h2, x, y)` | A cubic with explicit handles. |
| `.smooth(x, y, out_len, in_dir, in_len)` | A cubic that continues the current direction. |
| `.flared_from(x, y)`, `.flared_to(x, y)` | A line that leaves or reaches a flared terminal. |

Every segment call takes `w` (a width multiplier at that node), `fl` (flare, for a terminal) and
`corner=True` (for a hard corner next to a curve). `.done(start=H, end=V)` cuts the two ends. `g.stem`,
`g.bar` and `g.line` take `w` too: `w=0.7` draws a stroke at 70% of the usual thickness.

`g.shift(dx, dy=0)`, `g.rotate(deg, cx, cy)`, `g.mirror_x(cx)` and `g.mirror_y(cy)` move what has been
drawn so far.

## Serifs

In a family with `serif` above 0, `g.stem` puts slabs on its free ends by itself (see
[parameters](parameters.md#serifs)). Say otherwise where the rule is wrong for a letter:

| Call | Draws |
|---|---|
| `g.stem(..., serif0=(1, 0), serif1=False)` | Slab lengths at the start and the end: `(left, right)` as shares of `serif`, or `False` for none. |
| `g.slab(x, y, left=1, right=1, top=False, half=None)` | A slab across the end of any stroke whose middle is at `(x, y)`. `top=True` hangs it below `y`. `half` is half the stroke's width there. |
| `g.beak(x, y, side=1, down=True, length=1)` | A short vertical serif at the end of a horizontal arm (`E`, `T`). |
| `g.serifed`, `g.serif_t` | Whether the family has serifs, and the thickness of a slab. |

All three draw nothing in a family without serifs, so a recipe can call them unconditionally. A stroke
that ends under a slab should have a square end there: pass `round_end=0.0 if g.serifed else None` to
`.done(...)`. A recipe may add or drop slabs depending on `g.serifed` (that is a structure choice), but
never on a number, such as the weight.

## Diagonals and points

`g.diagonal(xa, ya, xb, yb, "l", "r")` returns the centerline end points of a diagonal whose horizontally cut
ends have their left or right corner at the given x. Use it so that a diagonal starts exactly at the edge of
the letter.

`g.apex_y(x, far_a, far_b, y_cut)` returns where to put the corner node of a `V` so that its point, cut off
along `y_cut`, has the flat width that the `apex` parameter asks for. The helper `vee` in
`recipes/lower.py` wraps both.

For a crowded cell, `recipes.upper.em(g, vertex=0.34, thin=0.8)` draws an `M` whose V stops at a third of the
cap height with lighter strokes, and `upper.double_vee(g, middle=0.64, thin=0.8)` and
`lower.double_vee(...)` draw a `W` and a `w` whose middle point stops low. `examples/pinout` uses them.

## Width and spacing

End a recipe with `g.frame(width, left, right)`. The drawing sits between x = 0 and `width`. `left` and
`right` describe each side, and set the sidebearing:

| Value | Side | Sidebearing |
|---|---|---|
| `"s"` | A straight stem (`n`, `H`). | Full. |
| `"r"` | A round (`o`). | About half. |
| `"o"` | Open (`c` on its right). | Less than half. |
| `"d"` | A diagonal (`v`, `A`). | A sixth. |
| a number | Anything else. | That multiple of the full sidebearing. |

`g.frame(None, ...)` measures the drawing. `g.fixed_advance(n)` centers it in a fixed advance, which the
figures use so that columns of numbers line up. The last of the two calls decides, so a recipe that reuses
a figure can call `g.frame(...)` afterward to make it proportional. In a monospaced family every glyph is
centered in the cell, and `g.frame(width, 0.5, 0.5)` is the usual ending.

## A complete example

The `n`: a stem, then an arch that leaves the stem thin, rounds over, and comes down as the second stem.

```python
@recipes.add("n", "n")
def n(g):
    w = 2 * g.sw + g.cw                       # two stems and the counter
    top = g.top(g.xh)
    g.stem(g.L, 0, g.xh)
    (g.path(g.L, g.xh * 0.60, g.p.join)       # start inside the stem, thinned
      .arc(w / 2, top, "v", k0=0.42, k1=0.62)  # rise to the top of the arch
      .arc(w - g.L, top - (w / 2 - g.L), "h")  # round the shoulder
      .flared_to(w - g.L, 0)                   # come down to a flared foot
      .done(end=H))
    g.frame(w, "s", 0.94)
```

## Start from a stock letter

A recipe can draw a stock letter first and then add to it or change its spacing. Keep a second copy of the
set, because your recipe replaces the stock one under the same name:

```python
stock = latin()
recipes = latin()

@recipes.add("r", "r")
def r(g):
    stock["r"](g)                     # the stock r
    g.dot(g.L, g.xh + 120)            # and something of your own
    g.frame(None, "s", 0.1)           # the last frame decides: here, a tighter right side
```

`g.frame(None, ...)` measures the drawing. A number for a side is a multiple of the straight sidebearing,
so 0.1 is tight and 1 is the side of an `n`. A change of 0.25 moves the next letter by only a few units:
look at `whateverfont probe DIR --full` for the `rsb` of the glyph before and after.

## Accented letters

Accented letters draw their base letter from your set, then add the marks. Redraw `o` and you get your `o`
in `ó`, `ô`, `ő`, and in Vietnamese `ơ` and `ộ`. `latin()` has GF Latin Core, the Vietnamese alphabet,
Pinyin, and letters for Azerbaijani, Yoruba, Igbo and Hausa, and the signs people type: 605 code points.
It also has Greek and Cyrillic (below): 800 code points in all.

`recipes.accents.mark(g, kind, cx, upper)` draws one mark centered on `cx`: `"acute"`, `"grave"`,
`"circumflex"`, `"tilde"`, `"breve"`, `"hookabove"`, `"dotbelow"` and the others. `recipes.vietnamese` adds
`stack(g, kinds, cx, upper)` for the two marks of `ấ` or `ắ`, `horn(g, x, y, upper)` for the horn of `ơ`,
and `dot_below(g, cx, upper)`. A stack is placed by measuring the outlines of its marks: with a circumflex,
the acute, the grave and the hook above sit at its upper right and a tilde sits on top; on a breve, an
acute, a grave or a hook sits down in its cup and a tilde sits on top. If a stack would rise above the top
of the line, its marks get flatter, closer and lighter until it fits, so the line spacing does not have to
change.

## Greek and Cyrillic

`latin()` and `mono()` have modern Greek and Cyrillic, drawn with the family's pen like the Latin letters:

- **Cyrillic**: U+0400 to U+045F (Russian, Ukrainian, Belarusian, Bulgarian, Serbian, Macedonian), `Ґ ґ`,
  and `Ә Ғ Қ Ң Ө Ұ Ү Һ Җ Ҳ Ҷ Ӣ Ӯ` with their lowercase for Kazakh, Uzbek, Tatar, Tajik and Kyrgyz: 124
  code points, in `recipes.cyrillic`.
- **Greek**: the monotonic alphabet, with the final sigma, the vowels with the tonos and the dialytika, the
  tonos and the dialytika tonos as spacing marks, the question mark `;` and the ano teleia `·`: 71 code
  points, in `recipes.greek`. `Ω` and `π` were in the Latin set already.

A letter that has the shape of a Latin one draws that letter: `А`, `Α` and `A` come from the same recipe,
and so do `р` and `p`, `і` and `i`, `Ё` and `Ë`. Redraw `A` and the Greek and Cyrillic `A` follow, so the
three can never drift apart. `И` and `Я` are `N` and `R` turned over, `Э` is `C` turned over with a bar,
`Є` is `C` with a bar, and `Ю` is a stem and a narrower `O`. Greek `Γ Π Φ` are the Cyrillic `Г П Ф`.

Upright Cyrillic lowercase is mostly small capitals: `в г д ж з и л м н п т ц ч ш щ ъ ы ь я`.
`recipes.cyrillic.small(g, draw)` runs a capital recipe at the x-height with the strokes and counters of
the lowercase, so `н` is the `H` of the lowercase and is as heavy and as wide as `n`. `б ф ђ є э ю` and the
Greek lowercase have recipes of their own. The descenders of `Д Ц Щ Џ Қ Ң` hang from a bar on the baseline
(`recipes.cyrillic.tail(g, x_right)`), shorter than the descender of `p`. On a Greek capital the tonos
stands in front of the letter, at the height of its top, and the letter moves right to make room
(`recipes.greek.tonos_capital(g)`); on a lowercase letter it stands over it, steeper than an acute.

Leave them out with `latin(greek=False, cyrillic=False)` (or `mono(...)`), and keep them in a small set with
`latin().only(greek=True, cyrillic=True)`. They come after every other glyph, so the Latin glyphs keep
their names, outlines, advances and places in the font. Each letter is kerned with the letters of its own
script and with the punctuation, and a font that has them names the `cyrl` and `grek` scripts in its
features. The combining marks attach to the new letters too: `а́` puts the acute over `а`.

The forms are the Russian and the modern Greek ones. Bulgarian and Serbian forms (`locl`) and polytonic
Greek are not drawn. In a monospaced cell `Ж Ш Щ Ы Ю Њ` draw their inner strokes lighter, so their
counters stay open.

## Signs, small figures and features

The signs are drawn from the letters and figures of your set too. A currency sign built on a capital
(`₦ ₩ ₱ ₽ ₲ ₵ ₭`) draws that capital with narrower counters, so it is as wide as a figure and as heavy as
the figures: `recipes.signs.letter_at(g, "N", UPPER, width)` does that for your own signs. A superscript,
a subscript, a numerator, a denominator or a fraction draws the figure smaller and a little heavier
(`recipes.symbols._small_figure`). Redraw `2` and `²`, `₂`, `½` and the `2` of a fraction follow.

Some glyphs have no code point. The OpenType features of `whateverfont.features` choose them:

| Feature | What it does | The glyphs it uses |
|---|---|---|
| `frac` | 1/2 becomes a fraction like ½; 2 3/4 becomes 2 ¾ | the superscripts, `zero.dnom` to `nine.dnom`, `fraction` |
| `numr`, `dnom` | every figure becomes a numerator, or a denominator | the same |
| `sups` | superscript figures | `zerosuperior` to `ninesuperior` (U+2070 to U+2079) |
| `subs`, `sinf` | subscript figures | `zeroinferior` to `nineinferior` (U+2080 to U+2089) |
| `ordn` | `1a` becomes `1ª`, `2o` becomes `2º`, `No.` becomes `№` | `ordfeminine`, `ordmasculine`, `numero` |
| `zero` | a zero with a slash | `zero.zero` |
| `case` | dashes, brackets, guillemets and `·` move up to the middle of the capitals; `¡ ¿` stand on the baseline | `hyphen.case`, `parenleft.case` and 21 more |
| `pnum` | proportional figures | `zero.pnum` to `nine.pnum` |
| `tnum` | tabular figures, in a family whose default figures are proportional | `zero.tnum` to `nine.tnum` |

Each form draws the glyph it replaces, so your own `(` gets a case form. A feature is written only for the
glyphs a font has: a small set from `latin().only()` gets none of them. In a monospaced font every form keeps
the cell, the fraction slash does not move, and there is no `pnum`.

The default figures are tabular: every figure has the same advance, so columns of prices and times line up
and a number that counts does not jitter. `Family(..., figures="proportional")` turns that around for a text
face: each figure gets the width of its shape, and `tnum` gives the tabular ones back.

## Color layers

A recipe may set `g.layers` to a list of `(palette key, contours)`, bottom layer first. The family's
`palettes` give each key a color. `whateverfont.ornament.illuminate` does this for capitals. See
`examples/wassail`. `illuminate(recipes, equal=880)` makes every tile 880 units wide, and `equal=True` makes
every tile as wide as the widest one.
