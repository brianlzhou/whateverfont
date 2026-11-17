# Aviary

## Brief

"Make me a font like birds." A picture font in the spirit of Wingdings: type a letter, get a bird, cut from
colored paper in the style of a mid-century field guide.

## The system

Every bird obeys the same few rules, which is what makes 26 drawings one set.

- **Shapes.** Only circles and straight lines: discs, two discs joined by their tangents (a teardrop when one
  disc is a point), lenses and crescents of two arcs, Moss's egg, ring sectors, polygons and bands. No free
  curves. The kit is in `aviary.py`.
- **Paper.** Each part is a flat piece. A piece that lies on another leaves a gap of paper 12 units wide
  around itself, as if it were cut out and inlaid. Feather lines are cuts of the same width.
- **Pattern is plumage.** Each bird gets two or three field marks and nothing else: a breast disc clipped by
  the body, a cap, a mask, bars on a wing or tail, dots on a back, scallops on a belly.
- **One eye, one leg.** A cream disc with an ink pupil, the same size on every bird but the owl. Legs are
  straight bands 13 units wide with one foot: a toe forward and a short toe back.
- **One palette.** Fourteen colors shared by all birds: ink, cream, gray, slate, blue, sky, teal, green,
  yellow, orange, red, pink, brown, tan. A palette maps these keys, so every palette colors every bird.
- **Scale and ground.** Songbirds share one size, large birds are larger on purpose. Every bird stands on the
  baseline, sits on a branch or on water lines, clings to a trunk, or flies at one shared height.

## The birds

A avocet, B bluebird, C cardinal, D mallard, E bald eagle, F flamingo, G Canada goose, H hummingbird,
I scarlet ibis, J blue jay, K kingfisher, L loon, M magpie, N night heron, O owl, P king penguin,
Q California quail, R robin, S swallow, T toucan, U hoopoe (*Upupa*), V turkey vulture (soaring, a V),
W red-headed woodpecker, X crossbill (its bill crosses), Y yellow warbler, Z zebra finch.

Capitals face right and lowercase letters face left, so `Rr` is two robins face to face. The figures are
things birds know: 0 egg, 1 feather, 2 nest, 3 footprints, 4 worm, 5 twig, 6 birdhouse, 7 berries,
8 pine cone, 9 acorn.

## Families

- **Aviary Color**: color layers. Palettes: Field Guide (the fourteen colors), Letterpress (one ink in
  tints), Risograph (fluorescent pink, blue and their overprint), Chalk (light tints for a dark background).
- **Aviary**: one color. The gaps keep the parts apart, eyes and white marks are cut out, and large white
  fields (a penguin's front, an eagle's head) are drawn as an outline.
- **Aviary Line**: a coloring book. Every piece is an outline, and the patterns are printed solid.

## Decisions

- Each bird is a short construction in `birds.py`, built from the kit in `aviary.py`. Nothing is traced
  from a picture.
- Kerning is off and each bird has 46 units of white on each side, so a word reads as a row of birds.
- `ascent=960` and `descent=-80`: the flamingo's head and the water lines fit in the line.
