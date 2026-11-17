# Hopstep

## Brief

A font of people in the manner of 1980s New York subway chalk drawings and pop street art: simple faceless
figures drawn with one thick even line, bodies in flat bright colors, caught mid-dance, with short dashes
around them that show movement.

The idea is a human alphabet. Each capital letter is one figure, or two where a letter needs it, whose body
makes the shape of that letter, so that people can type real words and the words dance. `DANCE`, `LOVE`,
`PARTY` and `HELLO` must read as words at 100 px and still be clearly made of people. Lowercase letters are
the same figures, so that typing in lowercase works.

## The system

Every glyph obeys the same rules. The kit is in `body.py` and the poses are in `poses.py`.

- **One body.** A round head that floats a little above the torso, a torso, two arms and two legs. Arms and
  legs are tubes 64 units wide with round ends, mitten hands and mitten feet, and no fingers, faces, clothes
  or hair. Each limb bends once, at the elbow or the knee. The bone lengths are constants: a pose says only
  where a hand or a foot goes (or which way the bones point), and the kit works out the elbow or the knee.
  So every figure has the same proportions. The figures of one letter are the same size, and a letter of
  seated figures has larger people (see Ground and scale).
- **One line.** A black line 22 units wide around the whole body (the body grown by 22 units), with the flat
  color inside. Where a limb lies in front of the body or of another limb, its line is cut into the part
  behind it. There is no line at a shoulder or a hip, where the parts grow out of each other.
- **Dashes.** Two to five short round-ended dashes per letter, as wide as the line, radiating from a moving
  hand, a foot or a head. They sit outside the letter shape: above heads, beyond a kicking foot, under a
  figure in the air.
- **Color.** Each figure is one flat color: orange, red, yellow, blue, pink or green. The letters are sorted
  into the six colors so that neighbors in English words seldom match (a search over the letter pairs of a
  word list leaves about 2% alike), and no two neighbors in the alphabet match. A lowercase letter is the
  same figure in the next color, mirrored when the letter is symmetric (`A H I M O T U V W X Y`).
- **Ground and scale.** Every figure stands, sits or kneels on the baseline. X is the one figure in the air,
  with dashes under its feet. Standing figures are about 830 units tall, and raised arms reach 920. A person
  who sits or kneels is only 500 to 630 units tall, so the letters of seated figures (C, E, G, L, S, W, Z)
  are drawn with larger people, 1.3 to 1.6 times the size (`@size` in `poses.py`), and stand about 780
  tall. The black line keeps its width: it is the same marker, drawing a bigger person. At first these
  letters kept the common body and stood half as tall, and W and E looked lost in a word. Each glyph has
  36 units of white on each side. Kerning is off, so a word reads as a row of dancers.

A few constructions come back across letters, which is what makes the set hang together:

- A **leaning pair** makes A (heads together) and V (feet together).
- The **ring** of O is two figures whose hands meet on top and feet meet below. Its left half is C and G,
  and its right half is the bowl of D.
- A **standing stem** with a friend makes D, P, R and B. In P and R the friend hugs the stem; in B it leans
  on the stem in the shape of 3.
- **Sitting with the legs out** gives L (arms up) and E (arms forward).
- **Kneeling with the shins back** gives J, S and Z.

## The letters

A two figures lean together, head to head; their inner hands meet in the middle (the bar).
B a friend leans on the stem in the shape of 3: shoulder out, hip at the stem's waist, knee out.
C the left half of the ring: arms up and over, legs down and under, head thrown back.
D one figure stands (the stem); a friend makes the right half of the ring against it.
E sits with the legs out (the bottom bar), one arm straight forward (the middle), one forearm high (the top).
F stands on one leg: a forearm high (the top bar), the other leg kicked straight forward (the middle bar).
G C, with one leg curled up on the right: the shin is the spur and the foot the bar.
H two figures hold hands.
I stands straight.
J kneels with the arms straight up; the shins lie back along the floor and the feet turn up (the hook).
K stands on one leg and kicks forward and down, one arm up and forward.
L sits with the legs out and the arms up.
M two figures; their inner arms reach down to meet in the middle (the V).
N one figure stands; a second does a one-hand handstand and leans its legs on the first (the diagonal),
its free arm straight up (the right stem).
O two figures in a ring: hands meet on top, feet below, heads thrown back.
P a friend hugs the stem: arms over the stem's shoulders, torso upright, legs hooked to the stem's hip.
Q the ring of O, with one foot kicking out below (the tail).
R the hug of P; the friend's other leg steps out to the floor (the leg).
S kneels and leans far back: the head thrown back at the top left, the arms over the top, the torso the
spine, the knees at the bottom right, the shins back along the floor.
T arms straight out.
U two figures lean apart with their heads thrown back; their knees bend in so the feet meet below.
V two figures lean apart from their feet, one arm up each.
W two figures in a V-sit, side by side.
X a jumping jack, in the air.
Y arms up.
Z kneels on one knee and leans back: the arms reach forward along the top, the front leg and the torso make
the diagonal, the back shin lies along the floor.

Signs: `.` a ball as big as a head, on the floor. `,` the ball with one dash falling away under it. `!` a
torso-thick tube over the ball. `?` a hook bent like an arm over the ball. The space is 300 units.

## Families

- **Hopstep**: the color font (COLR). Each glyph has two layers: `ink` (the line and the dashes) and the
  letter's color. Palettes:
  - **Bright**: the six colors in a black line.
  - **Chalk**: a chalk-white line, with the bodies in the color of the board (`#141416`). Use it on that
    ground.
  - **Poster**: the bright colors in a white line, for a black ground.
  - **Quiet**: one cream for every figure, in a dark gray line.
- **Hopstep Solid**: one color. The bodies are solid, half a line fuller than the color figure, with a white
  line where one part crosses another. Best at small sizes, and where color fonts do not work.
- **Hopstep Line**: one color, the line and the dashes only, like chalk on a board.

## Weak points

- **Heights vary.** C, E, G, L, S, W and Z sit or kneel, at 500 to 660 units against 830 for a standing
  figure. A word bounces, and `HELLO` has a short E and two short L's.
- **B, P and R are two figures hugging.** They read at 80 px and up. Under about 40 px their counters close:
  B can pass for P, and R for N or A.
- **S and Z read in a word more than alone.** On its own, each looks first like a kneeling figure.
- **W is small.** Two V-sits make a W of lowercase height.
- **M's V starts at the shoulders,** under the heads, not at the top of the stems.
- **The ring letters are wide.** O is about 1000 units and Q about 1150. The heads at their sides float as
  separate balls.
- **The comma** is a ball with a dash under it, and looks a little like a ball on a string.
- **Not drawn:** digits and `&`. A good figure for each did not come in the time.
- **Chalk is drawn for one ground.** On another dark ground the bodies show as dark shapes.
  `whateverfont look --palette Chalk --bg "#141416"` paints a light band behind the row, because the engine
  takes the body color for a hidden color. `proofs/showcase-chalk.png` was made with
  `whateverfont.proof.compare(..., bands=False)`.
- **No real lowercase.** Lowercase letters are the capitals in the next color, mirrored where they can be.
