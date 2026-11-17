# Panework

## Brief

Make me a font like Mondrian's grid paintings. Black lines divide each letter into rectangles: most of them white, a few of them red, yellow or blue.

The source is the grid paintings of Piet Mondrian and the De Stijl movement, such
as "Composition with Red, Blue and Yellow", and the late "Broadway Boogie Woogie". Each letter is such a
painting: thick horizontal and vertical lines divide it into rectangles, most of them white, a few of them
red, yellow or blue.

- **What is it for?** A few words at a large size: a gallery poster, a museum sign, a jazz flyer, a title.
  Not running text. (I chose this.)
- **What should it feel like?** Bright, modern, balanced, a little playful. (I chose this.)
- **What must it not look like?** A plain sans with a checkerboard on it, a pixel font, or a letter that the
  grid makes hard to read. No curved or diagonal lines inside a letter. (I chose this.)
- **Which styles?** One style in each of two families: `Panework` (the classic grids) and `Panework Boogie`
  (the late, busy grid). A color font has no variable file. (I chose this.)

I worked from what is known about the paintings: only horizontal and vertical lines, unequal rectangles, a
balance without symmetry, large quiet white areas, one or two color fields per picture, lines that sometimes
stop short of the edge, and in the late painting, yellow lines broken by small squares of red, blue and gray.
I did not open, trace or sample any image.

## What is delivered

| Family | Files | Characters | WOFF2 |
|---|---|---|---|
| Panework | `fonts/Panework/ttf`, `woff2`, `Panework.css` | the full set of the engine: 605 characters, with the `frac`, `sups`, `subs`, `zero`, `case` and `pnum` features | 154 KB |
| Panework Boogie | `fonts/PaneworkBoogie/ttf`, `woff2`, `PaneworkBoogie.css` | the same 605 characters and features | 224 KB |

Palettes (in CSS, `font-palette`). `GROUNDS` in `font.py` holds the same table.

| Family | Palette | Lines | Planes | Ground | Ink beside it |
|---|---|---|---|---|---|
| Panework | Primary | black | white, red, yellow, blue | `#F3F1EC` (or white) | `#141414` |
| Panework | Stone | soft black | white, light grays, earthy red, yellow, blue | `#FFFFFF` | `#2A2A2A` |
| Panework | Night | light | dark planes, bright red, yellow, blue | `#101217` | `#F2EEE3` |
| Panework Boogie | Broadway | yellow, with red, blue and gray squares | off-white, red, blue, gray | `#1B1C21` | `#F2C511` |
| Panework Boogie | Midtown | black, with red, blue and yellow squares | white, red, blue, gray | `#F3F1EC` (or white) | `#151515` |

Primary and Broadway are after the paintings. Stone, Night and Midtown are my own, in the same spirit.

## Decisions

1. **A letter needs an edge, so the letter has a frame.** Most rectangles are white, and a white letter
   disappears on a white page. I chose a frame first: the letter's own edge is a line as thick as the lines
   inside it, as if the painting's lines also ran around the letter. On a white page the frame draws the
   letter. On a dark page the frame melts into the ground and the white planes draw the letter. I checked
   both: Primary on `#15171C`, Night on white, Broadway on white.
2. **A custom effect, `composition` in `planes.py`.** The stock `mosaic` gives even tiles and `banded` gives
   stripes. Neither divides a letter like a plan of rooms. The effect is written with `effects.wrapped` and
   gives flat COLR version 0 layers, which suits flat paint exactly.
3. **The letter is a window cut out of one painting.** The effect splits the letter's box again and again.
   Each split is one line across the part that it divides, so a line ends where it meets another line (a
   T-junction), and a line that crosses a counter comes out again on the other side. A split is never in the
   middle (unequal rectangles), and never closer than 56 units of white to the letter's edge or to another
   line, so no thin strip of white is left. In a stem (187 units at most) that leaves room for horizontal
   lines only; vertical lines fall in the wide parts: bars, bowls, junctions.
4. **Curves and diagonals cut the grid.** The lines stay horizontal and vertical in every letter, and the
   curve or the diagonal is the edge of the canvas, as the edge of a diamond-shaped canvas cuts the grid.
   So the round letters (`O S C G 0 8 @`) are drawn with squared rounds (`superness=0.85`): most of their
   edge is straight, and the curve is only a corner.
5. **One or two colored rectangles in a letter, and only whole ones.** A rectangle can get a color only if
   the letter shows at least 80% of its box. So a color always reads as a plane, never as a scrap or a cross
   (the `4` had a yellow cross before). Red comes up most often. Blue and yellow come up less.
6. **Some lines stop short of the edge.** About a third of the long lines stop 50 to 90 units before the
   frame at one end, and the white runs past. Only long lines do this (at least 170 units of white are left),
   and never where another line ends on the part that goes. Short ones turned into stubs and broke T-junctions.
7. **A second white.** A quarter of the white rectangles are in a second white: barely different in Primary,
   light gray in Stone. The early grids have whites and grays of several values.
8. **Small parts.** A dot (`i j ! ? . : ;`) is too small to divide, so it is one colored square in a frame.
   A thin mark (an accent, the tail of a comma, `°`) is solid, in the color of the lines. Thin strokes that
   are not square (`# %`, brackets) stay white, because a whole `#` in red was a heavy blot.
9. **The base: the grotesk at weight 170, squared and wide.** `preset("grotesk", weight=170, superness=0.85,
   counter=330, width=1.12, cut="horizontal")`. A stroke must be wide enough for a frame on both sides and
   white between. The technical and geometric presets at weight 165 to 190 put kinks in `S s e t 5 6 8 9 &`,
   and the geometric one dropped `s`. The grotesk stayed clean. The lines are 32 units and the frame 34.
10. **Panework Boogie: a finer grid with squares.** The same letters, split about twice as often (lines of 28,
    46 units of white). Small squares sit along every line and along the straight parts of the frame, one
    every two to four line widths, in red, blue and gray. The colored blocks are red, blue and gray, and three
    of four get a smaller square of another color inside. Yellow is kept out of the blocks: a yellow block
    next to a yellow line merged into a yellow blot.
11. **The squares are layers of their own.** In Broadway they are red, blue and gray. In Midtown they are red,
    blue and yellow on black lines. In the Panework palettes they take the color of the lines and vanish,
    so both families share one palette function.
12. **A workaround: `sealed` closes notches before the effect runs.** At this weight the engine leaves a slit
    or a notch where a hook meets a bowl (`9 6 5 s`). The frame outlined each one and drew a black knot. The
    effect grows the letter by 14 units, shrinks it back, and drops counters under 5000 square units. If that
    joins two parts or changes the ink by more than 4%, the letter stays as it was.
13. **Line height.** `ascent=975` on both families: `whateverfont probe` reported that `Ö Ẅ Ǘ` and the
    other capitals with two marks reach 961 units.
14. **The whole character set.** `latin()`: 605 characters, so no accent, currency sign or arrow falls back
    to another font. The files are small (154 KB and 224 KB as WOFF2), because a rectangle is four points.
15. **Grounds.** The engine picks a dark ground by itself only when a third of a palette is near white. It
    does so for Night, but not for Broadway, whose off-white planes need a dark ground. `GROUNDS` in
    `font.py` names the ground and the ink for every palette, for the page that shows the fonts.
16. **The name.** Panework: window panes divided by bars. A web search found no typeface of that name.
    "Muntin" (the bar between panes) was my first choice, but a font file named "JI Muntin" exists.

## Weak points

- Repeated letters are twins: the two `l` in "Yellow" and the `nn` in "Anna" have the same grid. A font gives
  one letter one drawing.
- Below about 22 px Panework reads as an outline face with specks of color, and Panework Boogie as a dotted
  outline. These are display fonts.
- The acute and grave accents are short and thick, so they look like small black diamonds. The engine draws
  them so at this weight.
- `s S a e B` keep small bumps where their curves join, and the `9` keeps a small notch where its tail ends.
  The frame shows them more than a plain letter would.
- Broadway on a white page is faint at small sizes (a yellow frame on white). Use Midtown on white.
- `= - _` and the dashes are thin. They get a line or two and a color, but no real grid.
- No hinting, automatic kerning, Latin only, one weight. This is a strong draft made in minutes, not a face
  tuned by a type designer.

## Feedback

Notes from the review board go here, with the date.
