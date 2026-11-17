# Tally Mono

## Brief

A monospaced font for a terminal and an editor. Calm, a little friendly, not too light. Regular, bold and an
italic. 0 must not look like O, and l, 1 and I must differ.

## Decisions

- Started from the `mono` preset: every glyph is 600 units wide, which is the usual cell for code fonts.
- `superness` 0.33 squares the rounds a little, so `o`, `c` and `e` stay open at 12 pixels.
- `roundness` 0.42 softens the stroke ends. More than that made the letters look inflated at small sizes.
- Weight 88 for the regular: lighter weights looked thin on a dark terminal.
- The signs of code come from the `mono()` recipe set: `+ - = < >` share one axis, so `->` and `=>` are
  level, brackets are deep, and the comma has a long tail. A first-time agent redrew them while it
  made a coding font with WhateverFont, and its drawings were folded into the engine.
- The engine draws `m` and `w` with narrower counters to fit the cell, and widens `r`, `f` and `t`.
- The italic is a slanted roman. WhateverFont has no cursive forms yet.

## Feedback

Notes from the review board go here, with the date.
