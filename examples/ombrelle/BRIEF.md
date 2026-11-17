# Ombrelle

## Brief

Make me a font like Seurat's A Sunday Afternoon on the Island of La Grande Jatte. Build every letter from small dots of pure color, with a sunny side and a violet shadow side.

It follows Georges Seurat and Paul Signac, above all Seurat's "A Sunday
Afternoon on the Island of La Grande Jatte". The letters are painted the way they painted: small separate dots
of pure color that mix in the eye. An ombrelle is the sun parasol that the people in that painting carry.

- **What is it for?** Titles, posters and labels, from about 40 px up. Not for running text. (I chose this.)
- **What should it feel like?** Sunny, calm and solid: a letter is a thing standing in afternoon light. (I chose this.)
- **What must it not look like?** Confetti: a flat fill of random dots. Also not a halftone screen or a grid. (I chose this.)
- **Which styles?** One style in each family, with three palettes: Afternoon, Harbor and Circus. A color font has no
  variable file. (I chose this.)

## Decisions

1. **A color font with its own effect.** The stock `effects.dotted` effect (the Pointille family in
   `examples/effects`) gives each dot a random color. Here each dot takes its color from the light. The effect is in
   `seurat.py` and is written with `effects.wrapped`. I worked from what is known about the method. I did not open,
   trace or sample an image.
2. **Two families.**
   - `Ombrelle`: every glyph in dots. This is `FAMILY`.
   - `Ombrelle Initials`: each capital A to Z on a square of dotted lawn inside a painted border. Every other glyph is
     Ombrelle.
3. **The light comes from the upper left.** The effect blurs the letter and reads the blur as a relief. Where the
   relief rises toward the sun, the form faces the light. So each stroke has a lit side and a shadow side, like a
   rounded solid. The right part of each letter is a little cooler than its left part, and low parts are a little
   cooler than high ones. The whole letter is then one lit form, not a set of lit edges.
4. **Seven colors from shadow to sun, and one complement.** Each palette has a ladder: deep violet-blue, blue, the
   cool neighbor of the local color, the local color, its warm neighbor, sun, full sun. A little noise mixes each dot
   with its neighbors on the ladder, so the local color has dots of its neighbors in it. In the shadow, 22% of the
   dots take the complement: orange in the blue. In Afternoon, orange is not used on the lit side, so that it reads as
   the complement.
5. **Every dot is whole.** A dot's center lies in the letter shrunk by the dot's radius and 3 units, so no edge cuts
   it. The dots go down in three passes:
   - a row along the edge, which draws the letter;
   - the inside, each new dot near one already placed, with a gap of 0.22 radius;
   - smaller dots (0.58 radius) in the narrow parts and the holes that are left.

   An accent or a period too small for a full dot gets dots of 0.6 radius.
6. **Dots 40 units across.** That is about 5 px at 120 px, so the dots read as dots, and three or four fit across a
   stem.
7. **A deep underpainting.** Under the dots lies the letter in a deep color (dark blue-green, deep blue, crimson). It
   makes each dot stand out, and it keeps the word legible down to 13 px. I also tried a mid-tone underpainting. The
   mid-tone dots disappeared into it.
8. **A soft edge.** The underpainting is shrunk by 11 units, so the row of edge dots makes a beaded edge, not a cut
   line. Pale dots spill out on the shadow side, mostly to the right, close to the edge. They are the halo that those
   painters put where a dark form meets a light ground. They do not go into the counters. A first version put them
   under the baseline too, where they looked like crumbs.
9. **The letters: a heavy geometric sans.** The figures in those paintings are upright, simple and solid. The base is
   `geometric` with weight 148, width 1.06, counter 312, x-height 520 and roundness 0.4. At weight 152 the capital
   stems reached 167 units, and `probe` warned that counters could close. Weight 148 gives 163.
10. **Three palettes, each for its own ground.**
    - Afternoon: a sunlit park (greens, yellow sun, violet-blue shadow) on cream `#F3EBD5`.
    - Harbor: Signac's evening water (blues, with pink and gold light) on peach `#F4DED2`.
    - Circus: reds, oranges and yellows under gaslight, with blue-violet shadow, on night blue `#1F1B47`.

    `GROUNDS` in `font.py` holds these colors. The engine writes `grounds` in `fonts/index.json` only for a palette
    that white paper would hide, so that entry is empty here. A page should set the ground itself.
11. **The initials.** The tile is 900 units square. The capital is scaled to 0.8 (wide capitals a little less) and
    stands on a lawn of pale dots. It casts a long shadow toward the lower right: the letter laid down on the ground,
    in violet dots with orange in them. A border of dots runs around the tile, like the border Seurat painted around
    his canvases. Its color answers the lawn next to it: deep blue beside sun, orange and red beside shade.
12. **The whole set.** Both families use `latin()`: 605 characters and all the engine's OpenType features. Ombrelle is
    430 KB and Ombrelle Initials 459 KB as WOFF2, and the project builds in about 30 seconds. Both set `ascent=955`,
    so the capitals with two marks (`Ấ Ế Ố`) are not clipped.
13. **The name.** I searched each name with "font" and "typeface". I rejected these names:
    - "Jatte": "Grande Jatte" is a typeface by The Ampersand Forest.
    - "Dimanche": Nick's Fonts sells Dimanche NF, and a 2011 font has the same name.
    - "Parasol": a Dover font has that name.

    I found no typeface named "Ombrelle".

## Weak points

- The dots of a letter are the same each time the letter appears: the two `n` in "Sunday on" are twins.
- In Ombrelle Initials only A to Z are tiled. `Á` or `Ç` is a plain dotted letter, so "Ángel" has no tile.
- A tiled capital is 560 units tall, shorter than the ascenders of the lowercase (740). Next to "he", the `T` in its
  tile looks small.
- The Circus halo is a violet made for the night ground. On white it shows as dark specks to the right of each letter.
- Thin parts (`- = + ~ _` and the bar of `e`) hold only small dots, so they look finer than the letters.
- On the lit side of Afternoon, pale yellow dots on cream have little contrast. The underpainting carries that edge.
- Below about 30 px the dots merge, and the letters read as a speckled green, blue or red. This is a display font.

## Feedback

Notes from the review board go here, with the date.
