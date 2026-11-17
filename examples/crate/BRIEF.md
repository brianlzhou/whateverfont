# Crate Stencil

## Brief

Make me a stencil font for labels on shipping crates — bold, a bit condensed, with the stencil bridges cut through the letters like real spray-paint stencils. I need a Regular and a Bold.

- **What it is for:** short labels sprayed or printed on wooden shipping crates: words like FRAGILE,
  THIS SIDE UP, crate numbers, port names. Mostly capitals and figures, read from a few meters away.
- **How it should feel:** sturdy, industrial, utilitarian. (Chosen: the person said "bold" and "real
  spray-paint stencils", so I read that as practical and heavy, not decorative.)
- **What it must not look like:** a decorative "stencil effect" with thin hairline gaps, or a military
  costume font with rough edges. The bridges must be wide enough to be real (a cut sheet needs them) and
  every closed counter (A B D O P Q R 0 4 6 8 9, a b d e g o p q) must be opened by a bridge, because
  a real stencil cannot hold a floating counter.
- **Styles:** Regular and Bold, as asked. (Chosen: no italic, because crate labels are never italic. The
  Regular is already heavy, because the person asked for a bold font; the Bold is heavier still.)

## Decisions

Write down each design decision and why you made it, newest last.

1. **Bridges are cut by a wrapper, not a preset.** WhateverFont has no stencil option. `stencil()` in
   `font.py` wraps each recipe and adds vertical strips to the glyph's cutouts. Bridges sit just inside a
   stem ("L", "R"), through the middle ("M"), or at a fraction of the width, optionally limited to a band
   of heights. The width is 0.30 of the stem (at least 20 units). A cut letter cannot be a master of a
   variable font, so the family ships its named styles as static fonts, and `whateverfont build` says so.
   (`whateverfont.effects.stencil` now cuts a bridge through every counter by itself. This project keeps its
   own table because it also bridges letters that have no counter.)
2. **Every closed counter gets a bridge**, because a real stencil cannot hold a floating counter:
   A B D O P Q R U, a b d e g o p q, 0 4 6 8 9, & @ # % and the degree sign. E F H K L M N C G and
   h k m n u get bridges too, so the whole alphabet has the same cut look.
3. **No bridge in r, S, s, I, T, V W X Y Z or 1 2 3 5 7.** They have no counter. A bridge in r left its
   arm floating as a thin spike.
4. **G and & get two short bridges** (top and bottom only). A full-height bridge sliced the G crossbar and
   the & diagonal into slivers.
5. **The g bridge stops above the descender**, so the tail stays on the stem.
6. **Accented letters get their base letter's bridges.** They do not inherit them from the base recipe,
   so `with_accents()` copies them, stopped at 1.03 of the letter height so the accents stay whole.
   Å and å also get a bridge through the ring.
7. **Weight:** the Regular is weight 116 (semibold to bold), because the person asked for a bold font.
   The Bold is wght 700 (stem 158), with `counter` 300 at the heavy end so the counters stay open.
8. **Width:** 0.82 in the main direction ("a bit condensed"). Square is 0.95 and Sprayed is 0.70, so the
   three directions read as different widths at a glance.
9. **Terminals:** `cut="square"` and `aperture` 0.5 in the main direction. The preset's horizontal cut
   put a spike on r, g and j. A vertical cut closed C and e and turned the Bold S into an 8.
10. **apex 0.4** so the Bold A keeps a visible counter under its bridge.
11. **Cap height lowered** (696, 694, 688) so the Bold dieresis on Ä Ö Ü stays inside the line ascent
    of 940 and is not clipped.

### Weakest letters

- `&` reads a little like an arrow at the heavy weights. This comes from the base recipe, not the bridges.
- `j` has a small step at the end of its hook in the Bold.
- `B` has a small notch where the two bowls meet in the Bold.
- In Sprayed Bold, the dieresis on Ï and ï is wider than the letter.
- `%` and `#` bridges work but look busy at small sizes.

## Feedback

Notes from the review board go here, with the date.
