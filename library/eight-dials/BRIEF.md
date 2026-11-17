# Eight Dials

## Brief

A calm, open sans with a slider for every decision: weight, width, slant, contrast, flare, roundness,
spacing and x-height.

- **What it is for:** showing what a parametric typeface is. The "How it works" part of the project site
  sets a line in this font with a slider for each of its eight axes, and each slider shows the parameter
  that it moves.
- **How it should feel:** plain and even at the default, so that every change reads.
- **What it must not look like:** a display face. The default has to be a text sans you could use.
- **Styles:** one Regular, and a variable font with eight axes.

## Decisions

- The base is the `humanist` preset with open apertures and Roman capitals, at weight 84 and contrast 0.78.
- Each axis moves one parameter, so the axes are independent: any corner of the design space is a font.
- Four tags are registered or common (`wght`, `wdth`, `slnt`, `ROND`). Four are this family's own:
  `CNTR` contrast, `FLAR` flare, `SPAC` spacing and `XHGT` x-height.
- The spacing axis runs from 0.62 to 1.9 of the default sidebearings: tight for a headline, wide for capitals.

## Weak points

- At the far corners (heaviest, narrowest, highest contrast together) counters close and joins clot.
- The slant axis leans the roman. There are no cursive forms.
