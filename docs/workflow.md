# The design loop

This is the method an agent follows to make a font with WhateverFont. A person can follow it too.

## 1. Write the brief down

Put the request in `BRIEF.md` in the person's own words. Then answer four questions under it. If the request
does not answer one, choose, and say that you chose.

- What is it for? Titles, long text, labels, one word on a poster.
- What should it feel like? Three adjectives are enough.
- What must it not look like?
- Which styles are needed? Weights, an italic, widths.

## 2. Propose directions

Do not start with one answer. Define three families in `font.py` that read the brief differently, and list
them in `DIRECTIONS`. Start each from a preset. Give each a name and one sentence in `description` that says
what it is for. The person will see that sentence on the review board.

Make the directions differ in kind. Start each from a different preset, or change at least two of contrast,
proportions and terminals. Run `whateverfont look DIR --directions` and check that the rows look different at a
glance.

Change parameters first. Write a recipe only when no parameter gives the shape.

## 3. Build, look, fix

```sh
whateverfont build DIR
whateverfont look DIR --family "Name"            # the full sheet
whateverfont look DIR --family "Name" --styles   # one row per style
whateverfont probe DIR --family "Name" --problems   # what the numbers say is wrong
```

Open every image you render and read it. Check these, in this order:

1. **Color.** In the paragraph at the bottom of the sheet, is the gray even? Dark spots are letters that are
   too heavy or too tight. Light spots are too open.
2. **Rhythm.** In `nnnonnoonnn`, is the white between letters about equal to the white inside the `n`?
3. **Family likeness.** Do `a e s c` end the same way? Do `b d p q` share one bowl?
4. **The extremes.** Look at the lightest and the boldest style. Bold counters must stay open.
5. **Problem letters.** `S s a g e & @ 2 5` and every diagonal. Use `--xray` on any that look wrong.

Fix what you see by changing a number, then build and look again. Stop when a pass finds nothing new, not
when the build succeeds. Record each decision in `BRIEF.md` with its reason.

## 4. Hand over

Show the person a proof image first, so they see the result at once. Then run `whateverfont board DIR --serve`
and give them the address it prints. Tell them what to do there: type their own text, compare the
directions, move the axes, press **Pick this one**, write notes, and press **Send to the agent**. That
writes `DIR/feedback.json`.

Without a server, give them `DIR/board.html`. The page then lets them download the feedback, or they paste
it into the conversation.

Many people just answer in the conversation: "chunkier", "the tails on g and y hang too low", "now put snow
on it". That is feedback too. Do not make them open the board to be heard.

## 5. Revise

Read `feedback.json`, or the person's words. `picked` names the chosen directions, and `general` holds the
notes for the whole project. `directions[NAME]` holds what the person did with each direction: its `notes`,
the named style they chose (`style`), the palette they chose (`palette`), and in `axes` the slider positions
they left. The positions often say more than the notes: a weight slider left at 460 means the regular is too
light.

Make the chosen direction `FAMILY`. Move its defaults to the positions the person chose. Apply the notes.
Add the date and the feedback to `BRIEF.md`. Build, look, and hand over the board again. Two or three rounds
are normal.

## 6. Deliver

`DIR/fonts/Name/` holds `ttf/`, `woff2/`, `variable/` and a stylesheet. Tell the person which file is for
what: the TTF files install on a computer, the WOFF2 files and the stylesheet go on a website, and the
variable font carries every style in one file.

## What to say about quality

Say what is weak. A font from this engine is consistent and usable. It has not been tuned by a type
designer's eye, its italics are slanted romans, and it has no hinting. If the person needs a face for a brand
or a book, say that this is a strong draft and that a type designer should finish it.
