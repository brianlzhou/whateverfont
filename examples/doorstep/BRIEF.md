# Doorstep

## Brief

Make me a friendly slab serif for a newsletter. Easy to read in long paragraphs, with a bold for headlines.

- **What it is for:** the body text of a newsletter, set at 15 to 18 pixels on a screen, and its headlines
  at 40 to 80 pixels.
- **How it should feel:** sturdy and warm. A paragraph should look even, and the slabs should be plain to
  see at headline size.
- **What it must not look like:** a typewriter (monospaced, round ends) or a display face with a look of
  its own.
- **Styles:** Light, Regular, Medium, Semibold and Bold, an Italic and a Bold Italic, and one variable font
  with weight and slant.

## Decisions

- I drew three directions first: slabs on the `humanist` preset, slabs on the `grotesk` preset, and a
  softer, wider version of the first. At 16 pixels they looked almost the same. I kept the third, because
  its headlines looked the friendliest, and I dropped the other two.
- Started from the `humanist` preset: open `c e s a`, a pen angle of 6 degrees and capitals with Roman
  widths (`classical` 0.5, so `O` is wide and `E S` are narrow, but less so than in a book face).
- `serif` 48 and `serif_weight` 1.0. In the Regular a slab is 73 units thick, as thick as a hairline and
  0.85 of the stem. That is what makes the face look sturdy.
- `roundness` 0.18 softens the corners of the stems and slabs a little. The ends stay square, so it does
  not look like a typewriter.
- `contrast` 0.85 and `weight` 86. Low contrast keeps the thin parts strong at 15 pixels. The stem is a
  little heavier than the engine's regular (82), so a paragraph is a solid gray on a screen.
- `xh` 515 against a `cap` of 700 (74%). A tall x-height reads bigger at the same size.
- `counter` 284 with `round_width` 1.12 and `cap_width` 1.04: wide round letters next to a plain `n`
  give an open, relaxed rhythm.
- `spacing` 1.08 and `word_space` 1.1. The slabs reach into the space between letters, and at 1.06 the
  slabs of `nn` and `mi` came too close.
- The Light (weight 58) gets `spacing` 1.14. At the base spacing its thin letters looked crowded.
- The Bold is at weight 130. At the bold end the slabs get shorter (`serif` 44) and heavier
  (`serif_weight` 1.15), `counter` goes to 292, `aperture` to 0.85 and `arm` to 1.2. So `a e s g` keep
  open counters and `f t r` keep their arms. `spacing` 1.02 at the bold end, because headlines looked
  loose at the base spacing.
- Figures are proportional by default, for text. The `tnum` feature gives tabular figures for tables.
- The italic leans 9 degrees. It is a slanted roman, because WhateverFont has no cursive forms yet.

## Weak points

- The italic is a slanted roman, with no cursive forms.
- Capital accents sit close to the letter. The caron of `Č Š` in the Regular and the marks of `Ò Ó Ś`
  in the Bold come within 4 to 12 units, and the ring of `Å` in the Bold is 18 units above the apex.
- `6` and `9` show a small step where the hook meets the bowl. It is visible only above about 100 pixels.
- In the Bold the small `a` inside `@` is tight, and `*` is small and sits high.
- The slabs have no brackets.
- There is no hinting, so small text on a low-resolution Windows screen is softer than in a hinted font.
- Nobody who reads Greek or a Cyrillic language has reviewed those letters yet.

## Feedback

Notes from the review board go here, with the date.
