# Last Bell

## Brief

Make me a font that gives me the feeling of winter break and Christmas holidays in middle school.

- **What it is for:** a poster on a classroom door, a holiday card, a title on a slide. Display sizes. (I chose this. The person did not say.)
- **How it should feel:** the last bell before the break. Loud, round, a little clumsy, glad.
- **What it must not look like:** a script, a blackletter "Christmas" font, or a default rounded interface font.
- **Styles:** Regular and Bold, and a color version with snow.

## Rounds

This font was made in four rounds. Last Bell Rounds holds the first three as one variable font, with an
axis for the change of each round, for the demo on the project site.

1. **A first take.** `preset("rounded", weight=90)`, a single-story `a`. Soft and friendly, and too polite.
2. **"Chunkier. Like marker letters on a classroom door."** `weight` 90 to 132, `superness` 0.15 to 0.3 so the
   rounds square up like a chisel marker, `xh` 505 to 540, `counter` 300 and `width` 1.04 so the heavy letters stay
   open.
3. **"The tails on g and y hang too low."** `desc` -215 to -150. Lines of a poster can now sit closer.
4. **"Now put snow on it."** A second family, Last Bell Snow, with an effect written for this project in
   `snow.py`. No effect in WhateverFont gave this look, so the project has its own: 60 lines.

## Decisions

- `cut="horizontal"`: at this weight the square cut left small spurs on the ends of `s`, `e` and `a`.
- The weight stops at 132. Above about 140 the bowls of `a`, `e` and `s` start to close.
- Snow settles only where a letter faces the open sky. The effect finds what a letter covers when it falls
  straight down, and takes the top 112 units of that. An `o` gets a cap, a `u` gets snow in its cup, and the
  inside of an `o` stays clear, because the top of the letter is a roof.
- Snow slides off steep sides: a layer thinner than 67 units is removed, so the diagonals of `v` and `w` stay bare.
- A few lumps hang from the lower edge of each cap, placed by a random source that is seeded with the name
  of the glyph, so every build gives the same snow.
- Four palettes: **Mitten** (red), **Pine** (green), **Cocoa** (brown, cream snow) and **Midnight** (gold, for a
  dark ground). Mitten and Pine are for a dark or a colored ground too: white snow does not show on white paper.
- Last Bell Snow is static. The snow changes the shape of the outline, and a variable font needs the same
  points in every master.

## Weak points

- The single-story `g` ends in a flat tail that is a little stiff.
- The points of `v`, `w` and `y` are flat, and everything else is round.
- At text sizes the snow turns to specks. Use Last Bell Snow at 60 px and up.

## Feedback

Notes from the review board go here, with the date.
