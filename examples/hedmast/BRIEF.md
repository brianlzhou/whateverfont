# Hedmast

## Brief

Make me a tall, narrow sans for newspaper headlines. Heavy enough to shout, and still clear in a long headline.

- **What it is for:** headlines of five to ten words at 40 to 140 pixels, in capitals or in mixed case, on
  news pages, posters, video titles and sports scores. The Regular also sets a short paragraph at 18 pixels.
- **How it should feel:** loud and plain. A long headline must stay easy to read in the heaviest weight.
- **What it must not look like:** Caliper, the light condensed flare serif in `examples/caliper`. Hedmast
  has no flare and its weights go much heavier.
- **Styles:** Regular, Medium, Semibold, Bold and Heavy, and one variable font with a weight axis and a
  width axis. No italic: the brief did not ask for one.

## Decisions

- I drew three drafts at the Regular weight: condensed at width 0.72, compressed at width 0.6 with almost
  square rounds, and a narrower grotesk at width 0.8 with rounder letters. I kept the first as the family.
  The second became the narrow end of the width axis. The third looked like a plain sans that was squeezed.
- Started from the `condensed` preset: low contrast, closed `c e s`, level cuts on the round letters.
- `cut="flat"`: the hooks of `f`, `t` and `j` and the arm of `r` stop when they are level and end upright,
  and the tail of `g` is cut square. With the preset's `"horizontal"` cut they ended in a point in the heavy
  weights.
- `xh` 560 against a `cap` of 720 (78%). A tall x-height makes mixed-case headlines look as big as capitals.
  `asc` is 760, so that the dot of the `i` has room above the x-height. `desc` is -200, shorter than usual,
  for headlines set in tight stacks.
- `superness` 0.55 gives the round letters flat sides, which suits narrow letters. With `round_width` 1.04
  the `o` is only a little wider than the `n`.
- `width` 0.72 with `counter` 285 gives an `n` counter of 201 units. At the heavy end `counter` goes to 318,
  so the counter stays at 202 units while the stem grows from 92 to 146. The heavy weights get wider (a
  headline in Heavy is 24% longer than in Regular) and keep their counters.
- The heaviest stem is 146 (153 on the capitals, with `cap_weight` 1.05 at that end). I also tried 152 and
  158. At 158 the openings of `s`, the upper loop of `&` and the hooks of `6` and `9` closed to slits, and
  `probe` said the stems were as wide as the counters.
- `contrast` goes from 0.84 to 0.74 at the heavy end. With the engine's own correction the horizontals are
  0.82 of the stem in the Regular and 0.64 in the Heavy. The thin horizontals keep the eye of `e` and the
  bowl of `a` open in the tall, narrow letters.
- `aperture` goes from 0.3 to 0.62. The Regular has the closed `c e s` of a grotesk. The Heavy opens them so
  the ends do not touch.
- `arm` 0.95, and 1.05 at the heavy end. A first draft had 1.2 there, and the `r` left a hole before the
  next letter.
- `spacing` 0.88, and 0.82 at the heavy end. `word_space` 0.95. Headlines are set tight, and the counters
  are tall, so the spacing still looks even.
- The width axis goes from 60 to 90, with 75 as the default (`width` 0.6 to 0.88). I tried 0.58 at the
  narrow end. At 0.6 the heavy, narrow corner keeps its `s` and `&` open.
- Figures are tabular by default, so scores and times line up. `pnum` gives proportional ones.
- `ascent` is 960. In the Heavy the marks of `Ǘ` and `ĥ` reach 952, above the default top of 940.
- These letters are redrawn in `font.py` from the stock recipes:
  - `i` and `j`: the dot keeps a gap of 0.11 of the x-height over the stem. The stock dot came down to 30
    units over the stem in the Heavy, and the `i` read as an `l` at text sizes.
  - `Ï` and `ï`: the dots get smaller in the heavy weights (to 0.83 of the stock size). The stock dots
    reached far past the narrow letter. `Ї ї Ϊ` follow.
  - `Ő ő Ű ű`: the two strokes of the double acute stand 1.3 times as far apart (1.5 in the Heavy). They ran
    together before.
  - `&`: 12% more counter (up to 36% in the Heavy, narrow corner), so the upper loop stays open.
  - `s`: up to 10% more counter in the Heavy and up to 10% more at the narrow end.
- `round_weight` is 1.01 at the heavy end, not 1.0. At exactly 1.0 the engine draws `6`, `9`, `б` and `∂`
  with a different structure, and leaves them out of the variable font.

## Weak points

- The `r` has a long arm, so mixed case in the Heavy shows a gap after it (`Voters`, `Farmers`).
- The crossbar of `t` is short on the left.
- In the Heavy the acute, the grave and the caron are short and thick, almost wedges.
- At the heavy, narrow corner of the variable font the upper loop of `&` is a narrow slot, and the bowl of
  `a` is small.
- `+`, `=` and the other math signs are sized for text and look small next to heavy capitals.
- There is no hinting. Nobody who reads Greek or a Cyrillic language has reviewed those letters.

## Feedback

Notes from the review board go here, with the date.
