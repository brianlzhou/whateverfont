# Effects

## Brief

Five display faces that each show one effect from `whateverfont.effects`, so a reader can see what an effect
does before using it: an engraved line, speed stripes, a block shadow, dots of color, and bands of color.

## Decisions

- Every family has the full Latin set (`latin()`): a sign that falls back to another font looks broken
  even in a few words. Each file is 55 to 95 KB; Pointille, whose glyphs are hundreds of dots, is 750 KB.
  Marquee, Turbo, Pointille and Meridian set `ascent` (980 to 990): at these weights the marks of `Ż` and
  `Ǘ` rise above the default top of the line, where some programs clip.
- **Marquee** (`effects.inline`): tall geometric capitals at weight 168. The line needs a stem at least five
  times its own width, or the two sides of the stem look like hairlines.
- **Turbo** (`effects.stripes`): wide, slanted 12 degrees, five lines through the lower half that get
  thinner toward the top.
- **Billboard** (`effects.layered_shadow`): the shadow is a color layer, so each palette can pair two colors.
- **Pointille** (`effects.dotted`): whole dots, never cut by the outline. The tone rises from the foot of
  each letter to its head, with chance mixed in, so cool dots gather low and warm dots high.
- **Meridian** (`effects.banded`): six bands. The lowest and the highest band reach past the baseline and
  the cap height, so descenders and accents are colored too.

## Feedback

Notes from the review board go here, with the date.
