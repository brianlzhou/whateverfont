# Teacloth

## Brief

Make me a font like the cross-stitch letters on a sampler that hangs in a kitchen.

- **What is it for?** Short lines at a large size: "Home Sweet Home", a name and a date, an alphabet row, a kitchen sign, a card, a label for a jar. It still reads at 28 px, but it is not for running text. (I chose this.)
- **How should it feel?** Homemade, warm and patient: thread on linen, every letter worked square by square. (I chose this, from the request.)
- **What must it not look like?** A pixel font with a stitch texture laid over it, a printed pattern, or letters too blurred by the stitches to read. (I chose this.)
- **Which styles and palettes?** One style in each family. Two families: `Teacloth`, and `Teacloth Initials` with a framed capital for each letter A to Z. Four palettes, each made for its own cloth: Linen (red on natural linen, the showpiece), Blue (blue on white), Garden (bands of green, rose and gold) and Night (white on dark cloth). A color font has no variable file. (I chose this.)

## Decisions

1. **A color font with an effect of its own.** No stock effect stitches, so `stitch.py` holds one, wrapped around every recipe of `latin()`. I worked from the description of a sampler. I did not open or trace any chart, pattern or font.
2. **One square of cloth is 70 units.** The x-height is 7 squares (490 units), the capitals 10 (700), the ascenders 11 (770) and the descenders 3 (210). The baseline and these heights are grid lines, so every letter starts and stops on a whole row. `overshoot` is 0 for the same reason.
3. **The base letters.** The `grotesk` preset at `weight=140`, `cap_weight=1.0`, `contrast=0.45`, `superness=0.5`, `aperture=0.2` and `apex=0.25`. A stem is 140 units, exactly two squares, in capitals and lowercase alike. A horizontal stroke is about 55 units and becomes one row. This gives thick downstrokes and thin crossbars, as a sampler alphabet has, and it leaves room in 7 rows for the two counters of `e`, `a` and `s`. At contrast 0.6 the diagonals of `A V W x k` turned into blocks; at 0.45 they are a clean staircase. Squarish rounds (superness 0.5) and closed apertures end the curves on whole rows.
4. **How a square is kept.** The letter is drawn on a raster of 15 pixels to a square. It may slide sideways by a fraction of a square; the effect keeps the position where the fewest squares are half covered, so stems land on two whole columns. A square is stitched when 56% of it is ink. A stroke that lies half in one row and half in the next is settled by a line through the middle of each column (and each row): the crossing is rounded to whole squares (at most 2.6 squares long, and the square must be at least 25% ink), and a tie goes up. So a crossbar is always one row, wherever the engine put it.
5. **Clean-up rules.** A stitch with no neighbor is dropped. A bare square closed in on four sides and outside any counter is filled. Every counter keeps at least one bare square. Every separate part keeps at least one stitch. Every dot (of `i j ! ? : ;`, a period) is the same block of 2 by 2 stitches. Parts that would touch move apart by whole rows.
6. **Accents come from small charts.** An accented letter is the chart of its base letter, so `é` has the same `e` as `e`. A mark above is drawn from a chart in `stitch.MARKS` (acute, grave, circumflex, caron, breve, tilde, macron, dot, diaeresis, ring, double acute, hook), centered where the engine put the mark, with one bare row between it and the letter. A cedilla and an ogonek grow from the letter; a comma and a dot below hang one row under it. Two marks stack; after a circumflex, a second mark goes beside it, one row up, as Vietnamese sets them. A Greek tonos stays beside its capital. The caron of `ď ľ ť Ľ` is an apostrophe beside the stem. The spacing accents and the combining marks use the same charts.
7. **Some glyphs are charted by hand** in `font.py` (`HAND`), each for a reason I saw on a proof:
   - `a`: the rules gave its bowl a diagonal top, and "Mary" read as "Møry".
   - `A V X K k v x`: the rules left uneven steps and lopsided points. By hand they are mirrored staircases two stitches wide.
   - `w W`: the rules made a block where four strokes cross.
   - `I` with bars and `l` with a foot, so that `I l 1 |` differ. `ł ŀ` follow `l`.
   - The parentheses, brackets and braces, whose curves are too shallow for the grid.
   - The quotes, the comma, the semicolon and the guillemets, which came out as blobs.
   - `$ # * ^ ~ °`, and the math signs `+ = < > × ÷ ± ≠ ≈ ≤ ≥ ∞`, centered on row 5 like the minus.

   A Greek or Cyrillic letter drawn exactly like a hand-charted one (`Α Κ Χ Ι`, `А К Х І а х`) takes the same chart: the effect compares the drawings. The `M` keeps the engine's form, with its V stopped at a third of the height.
8. **The grid holds across a line.** Every advance is a whole number of squares and stitches sit at whole squares from the origin, so a line of text is one piece of cloth. Kerning is off (`kerning=0`): a kerning pair would move a letter by part of a square. Each letter has one bare column on each side, counted beside its body (between the baseline and the x-height, or the cap height). A hook or a tail outside the body may reach into those columns (`f`, `j`, accents). The em dash and the underscore have none, so a row of them is one line. A space is 3 squares (`word_space=0.8`). Figures are proportional by default; the tabular ones (`tnum`) are centered in 9 squares.
9. **A stitch is two bars with slightly round ends.** The thread is 30% of the square (21 units) wide. Each bar runs from near one corner of the square to the opposite one and stops 3 units short of the next stitch's thread, so stitches that meet at a corner nearly touch, as threads that share a hole in the cloth do. Each end bows out by 30% of the thread width, in one curve. All stitches have the same size.
10. **Layers, from the bottom up:** the under threads (lower left to upper right) row by row, keys `u0` to `u9`; the under threads of a frame (`border_u`, `heart_u`, `leaf_u`, `petal_u`); the top threads (upper left to lower right) row by row, keys `t0` to `t9`; the top threads of a frame. The key of a stitch is its row from the baseline, modulo 10. The top thread is a little lighter than the under thread, as the thread on top catches more light, so the X reads as thread.
11. **Palettes.** Each palette is drawn for its ground, which is the page, not a layer. `GROUNDS` in `font.py` lists them:

    | Palette | Thread (under, top) | Ground |
    |---|---|---|
    | Linen (showpiece) | turkey red `#9A1D28`, `#C7363C` | natural linen `#E6DCC6` |
    | Blue | dark blue `#1D3A82`, `#3159AA` | white cotton `#F8F7F2` |
    | Garden | rows 0 to 2 moss green, rows 3 to 6 rose, rows 7 to 9 gold | cream linen `#EDE5D2` |
    | Night | cream `#D9D2C2`, white `#FBF8F1` | dark cloth `#232B38` |

    In Garden, the lower half of the x-height is green, its upper half rose, and the capitals and ascenders above it gold; descenders take the gold of rows 7 to 9. I tried bands of two rows in five colors first. Each lowercase letter then had four colors, and a line looked like a rainbow; three bands that follow the parts of a letter look worked on purpose. The engine fills `grounds` in `fonts/index.json` only for a palette that white would hide, so only Night gets one there. The site must take the grounds from this table.
12. **Teacloth Initials.** Each capital A to Z sits in a frame: two bare rows and columns of cloth around the letter, a border of single stitches, and a rose at each corner (a heart and eight petals) with two leaves inside the corner. The frame runs from row -4 to row 13, so the family has `descent=-290`. One bare column on each side keeps the roses of two frames apart. The frame takes its colors from the same palette: a green border with red roses and gold hearts on Linen, all blue on Blue, a blue border on Garden, pale pink roses on Night. Every other glyph is Teacloth.
13. **The line.** Two marks on a capital reach row 14, so both families have `ascent=1050`. A line is 1.31 em (1.34 em for the Initials).
14. **The second family.** I chose framed capitals over a plain one-color family. A color font already carries a one-color drawing of every stitch, which programs without color fonts show in the text color, so a plain family would add little.
15. **Full character set.** `latin()`: 800 code points in each family. Teacloth is about 133 KB as WOFF2 and Teacloth Initials about 141 KB, because the outlines of all stitches are alike and compress well. Both families build in about 30 seconds.
16. **The name.** A tea cloth is the embroidered cloth of a kitchen or a tea table. I searched for "Teacloth" with "font" and "typeface" and found no typeface with that name.

## Weak points

- The diagonals charted by the rules (`Y y Z z N M 4 7`, the Cyrillic `Ж ж к Я`, the Greek `Λ λ`) have steps that are not all even.
- `s` has a single-stitch upper terminal and `S` none at its upper right. The crossbars of `f` and `t` reach only one stitch past the stem, and `G` ends in a small spur.
- `&`, `@`, `%`, `§` and `¶` are charted by the rules and are rough at 7 to 10 rows.
- Signs drawn small by the engine (superscripts, fractions, `ª º`, the numerator and denominator figures) are only 4 to 6 rows tall, and their figures are hard to tell apart.
- A combining mark typed after a letter (`q́`) is placed by the font's mark positioning, which does not know the grid, so it may sit half a square off. Precomposed letters (`é`, `ấ`) are exact.
- The Vietnamese letters with two marks are crowded above capitals; the second mark of `Ẳ` goes beside the breve instead of on top.
- Below about 20 px the stitches blur into a light, even texture.
- Nobody who reads Greek or a Cyrillic language has reviewed those letters.

## Feedback

Notes from the review board go here, with the date.
