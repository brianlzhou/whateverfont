# Starry

## Brief

"Make me a font like Starry Night." A color display face in the manner of that painting: short, loaded
brush marks that follow the form, a night sky that turns, rings of light around everything bright. For
titles and posters. It must stay readable, and it must not copy the painting.

## Decisions

- Nothing is traced. The font takes three habits from the painting: marks that follow the stroke, rings of
  light around bright things, and blues set beside yellows. `starry.py` holds the paint.
- The base is a heavy, soft sans (weight 148, round ends). Paint needs wide strokes to lie in: at a text
  weight there is room for one row of marks and the letter reads as a dashed line.
- **Starry** paints each letter with `effects.painted`. The marks run along the skeleton of the letter, in
  rows across each stroke. A tone function makes currents of light and dark blue and puts sparks of yellow
  down the middle of the stroke.
- **Starry Initials** sets every capital in gold on a square of sky. The sky is `effects.field_marks` with a
  direction field that bends around the letter and around two or three stars, so the marks circle them. The
  tone of a mark depends on its distance from the letter and the stars, which gives the rings of light.
- A dark gap of 16 units is left around the gold letter. Without it the pale ring merges with the letter.
- Three palettes: Night (the blues and golds), Dawn (rose and violet), Ink (a monochrome wash). The drawing
  is the same; only the colors change.
- The character set is `latin().only()`: about 95 glyphs. A painted glyph is several hundred marks, and the
  full Latin set would make a file of several megabytes.

## Weak points

- The fonts are large for the web: about 520 KB and 640 KB as WOFF2.
- Below about 60 pixels the marks close up and the letters read as plain blue.
- `S`, `a` and `e` have less room than the other letters, so their marks are shorter and busier.

## Feedback

Notes from the review board go here, with the date.
