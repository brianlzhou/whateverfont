# Haystack

## Brief

"Make me a font like Monet's haystacks." A color display face after that series of paintings: one motif in
a field, painted again and again at different hours and seasons, in short broken touches of color.

## Decisions

- The series is about light, not about hay. So the font has one drawing and four palettes: Noon, Sunset,
  Snow and Dusk. Changing the palette changes the hour.
- **Haystack** paints each letter with `effects.painted`: short marks (62 by 29 units) that wobble 24
  degrees off the stroke, so the touch looks broken, not combed. The tone function lights each letter from
  the upper left: warm colors there, violet shadow at the lower right.
- **Haystack Initials** stands every capital in a field. The lower 40% of the tile is land and the rest is
  sky, both `effects.field_marks`. The letter throws a short shadow on the ground to its right.
- The base is broad and soft (weight 156, width 1.04): a stack of hay has no thin parts.
- In every palette the shadow side of the hay is a cool color, never a darker brown. That is what makes
  the color read as light.

## Weak points

- The fonts are large for the web: about 620 KB and 790 KB as WOFF2.
- In Dusk the letters are dark on a dark tile. Use that palette on a pale page.
- The cast shadow is a thin strip. A longer one would need a taller tile.

## Feedback

Notes from the review board go here, with the date.
