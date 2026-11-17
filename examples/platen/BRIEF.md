# Platen

## Brief

Monospaced fonts with more character than a plain coding face, in the spirit of the return to typewriter
and early-computer looks that recent coding fonts made popular. A typewriter face first.

- **What it is for:** letters, notes and code that should look typed: a blog in the voice of a 1960s office,
  a zine, a terminal theme with character. Also posters, where the typed look is the point. (I chose this.
  The person did not say.)
- **How it should feel:** a 1960s portable typewriter. Friendly, a little round, printed black.
- **What it must not look like:** Courier. It must not be thin, and it must not copy any one machine's type.
- **Styles:** Light, Regular and Bold, with a weight axis. An inked companion that looks typed through a
  ribbon, which still reads as text.

## Decisions

- Started from the new `typewriter` preset: a 600-unit cell, slab serifs (`serif=56`), round ends
  (`roundness=0.85`) and nearly no contrast (`contrast=0.9`). The serifs are engine work done for this
  project: free stem ends get slabs, arms of E F L T Z get vertical beaks, and slabs that meet across a narrow
  counter are shortened so they never touch.
- Weight 84, not the preset's 74. Courier is thin on screen; a portable with a fresh ribbon prints black.
- `width=1.08` widens only the letters that do not fill the cell (o a e s c). n, m and H are already as wide
  as the cell allows. That is where the letters look wide and friendly.
- Ball terminals on `a c f j r 2 3 6 9 ?`. They are what sets a portable's type apart from an office machine's.
  Each ball sits back on its stroke, so it grows out of the stroke rather than sitting on its tip.
- `cap_weight` 1.02: a typewriter strikes every letter with the same force, so capitals are no heavier than
  lowercase. At 1.10, words in capitals made dark spots in a paragraph.
- `M` stops its V at a quarter of the height, and `W` and `w` stop their middle points low, with lighter inner
  strokes. With slabs in a 600-unit cell, the plain shapes were black wedges. The engine does this for
  any monospaced family with serifs.
- The `m` has short outer feet and shorter inner ones, so its two counters keep their white.
- `@` is drawn in this project: a round a inside a ring drawn in one turn, lighter as the weight rises. The
  built-in one had a tiny a in a thin, wide ring.
- The typewriter `l` (a flag and a foot) replaces the coding `l` with a tail. `il1I` stay apart: the i has a
  dot, the l a flat flag, the 1 a slanted flag, the I a bar across the top.
- The zero keeps the dot of the `mono()` set, so code reads.
- Bold has shorter, lighter slabs (`serif` 44, `serif_weight` 0.84 at wght 700); Light has longer ones (60).
  The slab length is on the weight axis, which the variable font carries.
- **Platen Ribbon** is the inked companion (`ribbon.py`): the ink spreads 7 units, the edge wobbles a little,
  each letter sits up to 7 units off the line and turns up to 0.9 degrees, the same way every time, as a
  bent type slug does, and small dry specks show inside the strokes. It is drawn at weight 78, because the
  spread adds weight back. Box drawings stay clean so that they join.

## Weak points

- `&` is the engine's: it is a little small, and in Bold its loops close up.
- In Bold, `g`, `M` and `@` are dark at text sizes. A monospaced bold has no room to spare.
- The balls on `a` and `j` stand a little proud of their strokes at poster sizes.
- The signs of code (`{ } [ ] < > * ~`) are the plain monoline ones of the `mono()` set; they have no serifs.
- Platen Ribbon is static (an effect redraws the outline), and every copy of a letter is identical: a real
  page would vary from strike to strike.

## Feedback

Notes from the review board go here, with the date.
