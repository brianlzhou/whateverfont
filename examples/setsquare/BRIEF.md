# Setsquare

## Brief

Make me a geometric sans for a landing page. Round o's, a one-story a, and sharp points on A and V.

- **What it is for:** headlines and short paragraphs on a landing page, a logo line, a slide. 16 pixels and
  larger.
- **How it should feel:** drawn with a compass and a ruler: clear, modern, a little cool.
- **What it must not look like:** an interface font with a two-story `a`, or a soft rounded face.
- **Styles:** Light, Regular, Medium, Semibold and Bold, an italic, and one variable font.

## Decisions

- Started from the `geometric` preset: a one-story `a`, almost no contrast, sharp points.
- `round_width` 1.28 with `counter` 262 makes the `o` as wide as it is tall, close to a circle, while `n`
  and `h` stay narrow. `b d p q` share that bowl.
- `xh` 506 against an `asc` of 754: a lower x-height and long ascenders, as the genre has. It reads smaller
  than Dayshift at the same size, so it is for 16 pixels and up.
- `classical` 0.5 gives the capitals Roman widths: a wide `O`, `C` and `G` next to a narrow `E`, `F`, `S`.
- `apex` 0.25: the points of `A V W M` are nearly sharp, and they overshoot the lines a little.
- `dot="round"` for round dots on `i`, `j` and the punctuation.
- `aperture` 0.55, and 0.8 at the bold end, so `c e s` do not close when heavy.
- The bold is at weight 126, with `arm` 1.2 for longer arms on `f t r`.

## Weak points

- The bold `a` gets a small bowl, and the bold `s` is narrow next to the round `o`.
- At 13 pixels the one-story `a` and the `o` are easy to mix up. Use Dayshift for small text.

## Feedback

Notes from the review board go here, with the date.
