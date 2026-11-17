# Greenbar

## Brief

Monospaced fonts with more character than a plain coding face, in the spirit of the return to typewriter
and early-computer looks that recent coding fonts made popular. This one reads the brief as what
computers printed and showed.

- **What it is for:** anything that should look printed by a computer around 1985: an invoice, a boarding pass,
  a fan-fold listing, a receipt. And the same characters on the terminal that sent the job: a phosphor screen.
  (I chose both readings. The person did not say.)
- **How it should feel:** mechanical and exact. Every dot on one grid.
- **What it must not look like:** a pixel font with square pixels, or dots scattered at random.
- **Styles:** Greenbar Regular and Bold (the printer's emphasized mode), and Halation, a color font with
  Green, Amber and White palettes for dark backgrounds, and Paper for a light page.

## Decisions

- A 9-pin head prints at nine fixed rows: seven for a capital, two more for descenders. Letters are five
  columns wide in a 600-unit cell, so an empty column separates them. The grid is 100 units in both
  directions, and every glyph puts its dots on it, so dots line up across letters and lines.
- The letters come from a character ROM written in `font.py`: each character as a 5 by 9 drawing, as a
  printer stored them. Tracing the skeletons of the built-in letters onto the grid (`matrix.fire`) works for
  most letters, but rounds got doubled dots at their corners and `K M N W X & @` came out muddled. The tracer
  stays as the fallback for characters without a drawing.
- A slashed zero, as printers had, so a 0 on an invoice is never an O. The `l` has a tail, so `il1I` differ.
- Punctuation dots are two pins square, so a period survives a worn ribbon and 16 pixels.
- The underscore and the em dash take a sixth dot at the edge of the cell, so a row of them prints as one line.
  The hyphen is three dots, so a row of hyphens is the dashed rule of a fan-fold report.
- Bold is emphasized print: each dot struck twice, half a step apart. Text at 16 pixels is light in Regular,
  as a used ribbon is; Bold is for totals and headings.
- **Halation** uses the same ROM on a screen: on each scanline the lit pixels fuse into one bar, dark lines run
  between scanlines, and a glow in four rings surrounds the beam. The palettes are the three phosphors
  terminals shipped with: P1 green, P3 amber, P4 white. A pale beam vanishes on a white page, so a fourth
  palette, Paper, has a dark green beam. The family's descent is -336 so the glow is not clipped below the
  descenders.
- Both families are static: an effect redraws the outline, and a color font cannot have axes.

## Weak points

- The character set is ASCII and a few signs (`£ ¢ ¥ ° ± × ÷`, curly quotes, dashes): 107 glyphs, no accented
  letters. A 9-pin printer had no room above the capitals for accents either.
- `whateverfont probe` reports missing counters in `e a o B 8`: its counter check does not understand dots.
- Regular is light below 14 pixels.
- Halation's glow overlaps the neighboring cell; on a light background use Greenbar instead.

## Feedback

Notes from the review board go here, with the date.
