# Wassail

## Brief

"I'd like to see a font that's illuminated, like medieval text. I'd like it to be slightly colorful. I'd like
it to maybe even be Christmas-themed." The capitals should be extravagant. The rest must stay readable.

## Decisions

- The lowercase is a round book hand, not blackletter. Textura is hard to read and does not look friendly.
  A broad pen at 32 degrees with a thin-to-thick ratio of 0.34 gives the written look with ordinary letter shapes.
- The decorated capitals live in a second family, `Wassail Initials`. Text set in plain `Wassail` reads the same
  in every program, and the initials are a choice the reader makes for a title or a first letter.
- Each initial is a gold letter on a framed field. Fields alternate vermilion and holly green from letter to
  letter, the way red and blue alternate in a manuscript. Two corners carry holly with three berries, and the
  other two carry a curl of vine. The ornament stops 30 units short of the letter so the letter stays clear.
- The color format is COLR version 0: flat color that Chrome, Firefox, Safari and macOS all draw. Gradients
  need version 1, which Safari does not draw.
- Three palettes ship in the file: Christmas, Ultramarine and Frost. CSS selects one with `font-palette`.
- Without color support the font shows the plain gold letter's outline in the text color.

## Feedback

None yet.
