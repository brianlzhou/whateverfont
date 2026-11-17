# Dayshift

## Brief

Make me a plain sans for the interface of my app. Even and quiet, easy to read at 13 pixels, with a bold
for headings.

- **What it is for:** the text of an app or a dashboard: menus, buttons, tables, settings pages, and the
  headings over them. Mostly 12 to 18 pixels on a screen.
- **How it should feel:** neutral and even. A reader should see the words and not the font.
- **What it must not look like:** a display face with a look of its own, or a narrow, bookish sans.
- **Styles:** Light, Regular, Medium, Semibold and Bold, an italic, and one variable font.

## Decisions

- Started from the `grotesk` preset: low contrast, closed `c e s a`, round strokes that end in level cuts.
- `cut="flat"`: the arm of `r` and the hooks of `f`, `t` and `j` stop when they are level and end in an
  upright cut. With the preset's `"horizontal"` cut those four ended in a sharp wedge.
- `xh` 540 against a `cap` of 720. A tall x-height is what keeps 13-pixel text large.
- `counter` 264 with `round_width` 1.17: the `n` is narrow and the `o` is wide next to it. The open fonts
  that people use for interfaces have this proportion; I measured it on two of them and set these numbers
  to give the same kind of rhythm. The letter shapes are the engine's own.
- `cap_width` 1.14 makes the capitals wide, so a word in capitals on a button does not look condensed.
- `spacing` 1.22 and `word_space` 1.22. Small text on a screen needs more room than the engine gives by
  default.
- `superness` 0.14 squares the rounds a little. More than that started to look technical.
- The bold is at weight 128, not higher. Above that the hooks of `f`, `t` and `r` and the terminals of `s`
  got crowded. At the bold end `aperture` goes to 0.5 and `arm` to 1.2, so `c e s` open up and the arms of
  `f t r` get longer.
- Figures are proportional by default, for text. The `tnum` feature gives tabular figures for tables.
- The italic is a slanted roman. WhateverFont has no cursive forms yet.

## Weak points

- The bold is rougher than the regular: look at `s` and `a`.
- The tilde of `ñ` is large.
- There is no hinting, so on a low-resolution Windows screen small text is softer than a hinted font.

## Feedback

Notes from the review board go here, with the date.
