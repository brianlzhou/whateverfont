# Pinout

## Brief

Monospaced fonts with more character than a plain coding face, in the spirit of the return to typewriter
and early-computer looks that recent coding fonts made popular. This one reads the brief as the
technical documents of early computers.

- **What it is for:** code, tables and terminals that should feel like a 1975 to 1985 datasheet, a terminal
  manual or a machine listing. (I chose this reading. The person did not say.)
- **How it should feel:** engineered, square, tight but clear. Read at a glance in a table of figures.
- **What it must not look like:** Tally Mono, the plain monospace of this repository. No rounded corners.
- **Styles:** Light, Regular and Bold on a weight axis.

## Decisions

- Started from the `technical` preset with `superness=0.80`: rounds are squares with round corners. `cut` is
  horizontal and `roundness` is 0, so every terminal is a flat cut.
- A 560-unit cell, narrower than the usual 600, and `width=0.92`. Letters stand close, as in a manual set on
  a narrow column. The x-height is 548 of a 700 cap height, so lowercase holds up at table sizes.
- What sets it apart from Tally Mono: square rounds, flat cuts, the narrow cell, a single-story `a`, a slashed
  zero (Tally's is dotted), and the `g` and `y` below.
- `g` and `y` share one descender: the stem drops straight and turns left in a square hook. The `y` is a `u`
  whose right stem runs on, so it has no diagonals at all.
- `l` has a flag and a foot that turns right in a square corner, so `il1I|` are five different shapes.
- `M` stops its V at a third of the height, and `W` and `w` stop their middle points low with lighter inner
  strokes. In a 560-unit cell the plain shapes filled in. These use the engine's `em` and `double_vee`
  helpers, which keep the default shapes for other families.
- Box drawings and blocks come from the `mono()` set and join on the default line height.

## Weak points

- `&` is the engine's, and narrow in this cell.
- In Bold, `m` and `M` are dense; a narrow cell has little room for a third stem.
- The braces and parentheses are the round ones of the `mono()` set. Square brackets would suit the face; a
  later round could draw angular braces.

## Feedback

Notes from the review board go here, with the date.
