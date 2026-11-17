"""The poses of Hopstep: one figure (two where a letter needs it) for each letter.

Every pose is a function that returns ``Fig`` objects. Positions are font units; a pose may sit anywhere,
because the drawing is moved onto the baseline and measured. Angles are degrees: 0 east, 90 north.
"""

import math

from body import (GROUND, HEAD, KNEEL, LINE, LIMB, NECK, SEAT, SHIN, SHOULDER, THIGH, TORSO, TORSO_LEN, Bones, Disc,
                  Fig, Hull, Thing, To, air, burst, pol, size, tube)

LEG = THIGH + SHIN
UP = TORSO_LEN - SHOULDER       # from the hip to the shoulders


def m(a: float) -> float:
    """An angle seen in a mirror."""
    return 180.0 - a


def stand(dx: float = 0.0, slack: float = 3.0) -> float:
    """The height of a hip whose leg stands on the floor ``dx`` to the side, nearly straight."""
    return GROUND + math.sqrt((LEG - slack) ** 2 - dx * dx)


def foot(x: float, bend: int = 1, toe: float | None = None) -> To:
    """A leg whose foot stands on the floor at ``x``."""
    return To(x, GROUND, bend, toe)


HIP = stand(34)                 # a figure standing with its feet a little apart
HIP1 = stand(0)                 # a figure standing on one straight leg
HANG_L = Bones(-98, -93)        # arms that hang at the sides
HANG_R = Bones(-82, -87)
BEHIND = ("la", "ra", "ll", "rl", "torso", "head")


# ------------------------------------------------------------------------------- shared constructions


def leaning(s: int, lean: float, ankle_x: float):
    """A figure whose leg, torso and head make one straight line, leaning ``lean`` degrees to the right
    for s = -1 and to the left for s = 1. Returns (hip, axis)."""
    axis = 90 + lean * s
    hip = complex(ankle_x, GROUND) + pol(axis, LEG - 3)
    return hip, axis


def half(s: int, hip_y: float = 274, head: float = 62, dx: float = 0.0):
    """Half of the ring of O. s = -1 is "(": arms up and over to the right, legs down and under to the
    right, head thrown back to the left. s = 1 is the same figure in a mirror, ")"."""
    hip = complex(230 * s + dx, hip_y)
    if s < 0:
        arms = dict(la=Bones(70, 32), ra=Bones(60, 20))
        legs = dict(ll=Bones(-62, -14, foot=0), rl=Bones(-70, -20, foot=0))
        order = ("la", "ll", "rl", "torso", "head", "ra")
    else:
        arms = dict(la=Bones(m(60), m(20)), ra=Bones(m(70), m(32)))
        legs = dict(ll=Bones(m(-70), m(-20), foot=180), rl=Bones(m(-62), m(-14), foot=180))
        order = ("ra", "rl", "ll", "torso", "head", "la")
    return Fig(hip, 90, 90 - head * s, order=order, **arms, **legs)


def hugger(rl=None, hip=complex(200, 392)):
    """P, R and B: a friend hugs the stem from the right. Its arms reach over to the stem's shoulders and
    its head leans in (the top of the bowl), its torso stands upright (the side of the bowl) and one leg
    hooks back to the stem's hip (the bottom of the bowl). ``rl`` is the other leg."""
    return Fig(hip, 100, 150, la=Bones(150, 176), ra=Bones(140, 170), ll=To(-30, 400, -1, foot=180),
               rl=rl or To(-20, 440, -1, foot=180), face=1, order=("rl", "torso", "head", "la", "ra", "ll"))


def stem(x: float = -60):
    """A figure that stands straight: the stem of P, R, D."""
    return Fig(complex(x, HIP), la=HANG_L, ra=HANG_R, order=BEHIND)


# ------------------------------------------------------------------------------------------- letters


def A():
    """Two figures lean together, head to head; their inner hands meet in the middle: the bar."""
    figs = []
    for s in (-1, 1):
        hip, axis = leaning(s, 18, 291 * s)
        inner = Bones(-95, -12) if s < 0 else Bones(m(-95), m(-12))
        outer = Bones(axis + 178, axis + 182) if s < 0 else Bones(m(m(axis) + 178), m(m(axis) + 182))
        out_leg = foot(291 * s, s, 180 if s < 0 else 0)
        in_leg = foot(257 * s, -s, 0 if s < 0 else 180)
        if s < 0:
            f = Fig(hip, axis, la=outer, ra=inner, ll=out_leg, rl=in_leg, order=("la", "ll", "rl", "torso", "head", "ra"),
                    dashes=(burst("head", 120, n=2, spread=32),))
        else:
            f = Fig(hip, axis, la=inner, ra=outer, ll=in_leg, rl=out_leg, order=("ra", "rl", "ll", "torso", "head", "la"),
                    dashes=(burst("head", 60, n=2, spread=32),))
        figs.append(f)
    return figs


def B():
    """A friend leans on the stem in the shape of 3: its arms reach to the stem's neck, its shoulder is out
    (the upper bowl), its hip rests on the stem's waist, its knee is out and its feet come back to the
    stem's shin (the lower bowl)."""
    hip = complex(40, 391)
    friend = Fig(hip, 58, 62, la=To(-30, 640, 1), ra=To(-20, 620, 1), ll=To(10, 150, 1, foot=200),
                 rl=To(24, 170, 1, foot=200), face=1, order=("la", "ll", "rl", "torso", "head", "ra"),
                 dashes=(burst("head", 30, n=2, spread=34),))
    return [stem(-80), friend]


@size(1.28)
def C():
    """The left half of the ring of O: arms up and over, legs down and under, head thrown back."""
    f = half(-1)
    f.la, f.ra = Bones(66, 14), Bones(58, 4)
    f.ll, f.rl = Bones(-60, -4, foot=0), Bones(-68, -12, foot=0)
    f.dashes = (burst("rh", 40, n=2, spread=34),)
    return f


def D():
    """One figure stands (the stem); a second makes the right half of the ring of O against it."""
    bow = half(1, hip_y=300, dx=40)
    bow.dashes = (burst("head", 20, n=2, spread=34),)
    post = stem(-80)
    post.dashes = (burst("head", 120, n=2, spread=34),)
    return [post, bow]


@size(1.62)
def E():
    """Sits like L: the legs out along the floor (the bottom bar), one arm straight forward (the middle
    bar), one forearm forward high (the top bar)."""
    hip = complex(0, SEAT)
    return Fig(hip, 92, 112, la=Bones(-20, 0), ra=Bones(96, 2), ll=Bones(-4, 0, foot=90), rl=Bones(-3, 2, foot=80),
               face=1, order=("ll", "rl", "torso", "head", "ra", "la"),
               dashes=(burst("rh", 30, n=2, spread=34),))


def F():
    """One forearm high (the top bar), one leg kicked straight forward (the middle bar)."""
    hip = complex(0, HIP1)
    return Fig(hip, 90, 112, la=HANG_L, ra=Bones(100, 4), ll=foot(0, -1, 0), rl=Bones(2, 0, foot=60), face=1,
               order=("la", "ll", "rl", "torso", "head", "ra"),
               dashes=(burst("rf", 0, n=2, spread=34),))


@size(1.35)
def G():
    """C, with one leg curled up at the right: its shin is the spur and its foot the bar."""
    f = C()
    f.rl = Bones(-58, 40, foot=150)
    f.dashes = (burst("rh", 40, n=2, spread=34),)
    return f


def H():
    """Two figures hold hands."""
    figs = []
    for s in (-1, 1):
        hip = complex(200 * s, HIP)
        if s < 0:
            figs.append(Fig(hip, la=HANG_L, ra=Bones(-60, 0), order=BEHIND, dashes=(burst("head", 120, n=2),)))
        else:
            figs.append(Fig(hip, la=Bones(m(-60), m(0)), ra=HANG_R, order=("ra", "la", "ll", "rl", "torso", "head"),
                            dashes=(burst("head", 60, n=2),)))
    return figs


def I():
    """Stands straight."""
    return Fig(complex(0, HIP), la=HANG_L, ra=HANG_R, dashes=(burst("head", 90, n=3, spread=34),))


def J():
    """Kneels, arms straight up; the shins lie back along the floor and the feet turn up: the hook."""
    hip = complex(0, KNEEL + THIGH)
    return Fig(hip, 90, 90, la=Bones(84, 88), ra=Bones(80, 84), ll=To(-170, GROUND, 1, 90), rl=To(-150, GROUND, 1, 90),
               face=1, order=("la", "ra", "ll", "rl", "torso", "head"),
               dashes=(burst("rh", 60, n=2, spread=34),))


def K():
    """Kicks: stands on one leg, the other kicks forward and down, one arm up and forward."""
    return Fig(complex(0, HIP1), ll=foot(0, -1, 0), rl=Bones(-38, -42, foot=-42),
               la=Bones(-86, -92), ra=Bones(48, 52), face=1, order=("rl", "la", "torso", "head", "ll", "ra"),
               dashes=(burst("rf", -20, n=3, spread=28), burst("rh", 80, n=2, spread=30)))


@size(1.43)
def L():
    """Sits with the legs out, arms straight up."""
    hip = complex(0, SEAT)
    return Fig(hip, 92, 92, la=Bones(98, 96), ra=Bones(102, 100), ll=Bones(-4, 0, foot=90), rl=Bones(-3, 2, foot=80),
               face=1, order=("la", "ra", "ll", "rl", "torso", "head"),
               dashes=(burst("lh", 90, n=3, spread=30),))


def M():
    """Two figures; their inner arms reach down to meet in the middle: the V."""
    figs = []
    for s in (-1, 1):
        hip = complex(180 * s, HIP)
        inner = To(-4 * s, 362, -s)
        if s < 0:
            figs.append(Fig(hip, la=HANG_L, ra=inner, order=BEHIND, dashes=(burst("head", 125, n=2, spread=32),)))
        else:
            figs.append(Fig(hip, la=inner, ra=HANG_R, order=("ra", "la", "ll", "rl", "torso", "head"),
                            dashes=(burst("head", 55, n=2, spread=32),)))
    return figs


def N():
    """One figure stands (the left stem). A second does a one-hand handstand beside it, leaning its legs on
    the first (the diagonal); its free arm points straight up (the right stem)."""
    shoulder = complex(170, GROUND + 5 + 265)
    torso = -58
    hip = shoulder - pol(torso) * UP
    flip = Fig(hip, torso, -100, la=Bones(-90, -90), ra=Bones(90, 90), ll=To(-70, 760, 1, foot=120),
               rl=To(-56, 724, 1, foot=120), order=("ll", "rl", "torso", "head", "la", "ra"),
               dashes=(burst("rh", 60, n=3, spread=30),))
    return [stem(-150), flip]


def O():
    """Two figures make a ring: their hands meet at the top, their feet at the bottom, heads thrown back."""
    left, right = half(-1), half(1)
    left.dashes = (burst(complex(0, 640), 90, n=3, spread=30, gap=60),)
    return [left, right]


def P():
    """A friend hugs the stem from the right, its legs hooked to the stem's hip: the bowl."""
    hug = hugger()
    hug.dashes = (burst("hip", -10, n=3, spread=30),)
    return [stem(), hug]


def Q():
    """The ring of O; one foot kicks out below: the tail."""
    figs = O()
    figs[1].rl = Bones(-62, -26, foot=-26)
    figs[1].dashes = (burst("rf", -30, n=2, spread=34),)
    return figs


def R():
    """The hug of P; the friend's other leg steps out to the floor: the leg of R."""
    hug = hugger(rl=To(258, 60, 1, 0))
    hug.dashes = (burst("rf", 40, n=2, spread=34),)
    return [stem(), hug]


@size(1.59)
def S():
    """Kneels and leans far back: the head thrown back is the top left, the arms reach forward and down
    over the top, the torso is the spine, the knees the bottom right and the shins lie back along the
    floor with the feet turned up."""
    hip = complex(40, 214)
    return Fig(hip, 132, 160, la=Bones(56, -20), ra=Bones(48, -30), ll=To(-80, GROUND, 1, 90), rl=To(-60, GROUND, 1, 90),
               face=1, order=("la", "ll", "rl", "torso", "head", "ra"),
               dashes=(burst("rh", -20, n=2, spread=34),))


def T():
    """Arms straight out."""
    return Fig(complex(0, HIP), la=Bones(180, 180), ra=Bones(0, 0),
               dashes=(burst("lh", 120, n=2, spread=34), burst("rh", 60, n=2, spread=34)))


def U():
    """Two figures lean apart, heads thrown back; their legs bend in so that the feet meet below."""
    figs = []
    for s in (-1, 1):
        hip = complex(218 * s, 330)
        torso = 90 - 10 * s
        head = 90 - 42 * s
        arm = Bones(torso + 180 + 6 * s, torso + 180 + 2 * s)
        arm2 = Bones(torso + 180 + 14 * s, torso + 180 + 10 * s)
        leg = To(40 * s, GROUND, s, foot=90 + 90 * s)
        leg2 = To(84 * s, GROUND, s, foot=90 - 90 * s)
        if s < 0:
            f = Fig(hip, torso, head, la=arm2, ra=arm, ll=leg2, rl=leg, order=("la", "ra", "ll", "rl", "torso", "head"),
                    dashes=(burst("head", 100, n=2, spread=34),))
        else:
            f = Fig(hip, torso, head, la=arm, ra=arm2, ll=leg, rl=leg2, order=("ra", "la", "rl", "ll", "torso", "head"),
                    dashes=(burst("head", 80, n=2, spread=34),))
        figs.append(f)
    return figs


def V():
    """Two figures lean apart from one point: their feet together, one arm up."""
    figs = []
    for s in (-1, 1):
        hip, axis = leaning(-s, 20, 26 * s)
        up = Bones(axis - 14 * s, axis - 16 * s)
        down = Bones(axis + 180 + 4 * s, axis + 180)
        in_leg = foot(26 * s, s, 0 if s < 0 else 180)
        out_leg = foot(60 * s, s, 180 if s < 0 else 0)
        if s < 0:
            f = Fig(hip, axis, la=up, ra=down, ll=out_leg, rl=in_leg, order=("ra", "ll", "rl", "torso", "head", "la"),
                    dashes=(burst("lh", 112, n=2, spread=34),))
        else:
            f = Fig(hip, axis, la=down, ra=up, ll=in_leg, rl=out_leg, order=("la", "rl", "ll", "torso", "head", "ra"),
                    dashes=(burst("rh", 68, n=2, spread=34),))
        figs.append(f)
    return figs


@size(1.5)
def W():
    """Two figures in a V-sit: torso back, legs up. The feet of one meet the head of the other."""
    figs = []
    for x in (-140, 140):
        hip = complex(x, SEAT)
        figs.append(Fig(hip, 106, 106, la=Bones(66, 70), ra=Bones(62, 66), ll=Bones(74, 74, foot=90), rl=Bones(70, 70, foot=80),
                        face=1, order=("ll", "rl", "torso", "head", "la", "ra")))
    figs[1].dashes = (burst("rf", 40, n=2, spread=34),)
    figs[0].dashes = (burst("head", 140, n=2, spread=34),)
    return figs


@air(110)
def X():
    """A jumping jack."""
    return Fig(complex(0, 400), la=Bones(138, 136), ra=Bones(42, 44), ll=Bones(-122, -124, foot=180), rl=Bones(-58, -56, foot=0),
               dashes=(burst("lf", -90, n=2, spread=30, length=48), burst("rf", -90, n=2, spread=30, length=48)))


def Y():
    """Arms up."""
    return Fig(complex(0, HIP), la=Bones(124, 118), ra=Bones(56, 62),
               dashes=(burst("lh", 135, n=2, spread=34), burst("rh", 45, n=2, spread=34)))


@size(1.36)
def Z():
    """Kneels on one knee and leans back, facing left: the arms reach forward along the top, the front
    leg and the torso make the diagonal, the back shin lies along the floor."""
    hip = complex(-30, 222)
    return Fig(hip, 56, 50, la=Bones(118, 180), ra=Bones(124, 184), ll=To(-80, GROUND, -1, 180), rl=To(170, GROUND, -1, 90),
               face=-1, order=("ra", "rl", "ll", "torso", "head", "la"),
               dashes=(burst("lh", 180, n=2, spread=34),))


LETTERS = {c: (c, globals()[c]) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}





# --------------------------------------------------------------------------------------------- signs

BALL = HEAD                     # a period is a ball as big as a head, lying on the floor
FLOOR = LINE + BALL


def period():
    """A ball on the floor."""
    return Thing([Disc(complex(0, FLOOR), BALL)])


@air(0)
def comma():
    """The ball, and one dash falling away under it."""
    return Thing([Disc(complex(0, FLOOR), BALL)], dashes=(burst(complex(0, FLOOR), -108, n=1, gap=BALL + 6, length=110),))


def exclam():
    """A torso-thick tube that tapers down, over the ball: they are as far apart as a head from its torso."""
    top = FLOOR + BALL + NECK + LIMB / 2
    return Thing([Disc(complex(0, FLOOR), BALL), Hull(complex(0, top + 520 - TORSO / 2 - LIMB / 2), complex(0, top),
                                                      TORSO / 2, LIMB / 2)],
                 dashes=(burst(complex(0, top + 520), 90, n=3, spread=34, gap=TORSO / 2 + 6),))


def question():
    """A tube bent like an arm into a hook, over the ball."""
    top = FLOOR + BALL + NECK + LIMB / 2
    hook = tube((-118, 640), (-70, 760), (40, 790), (120, 700), (96, 590), (10, 520), (0, top))
    return Thing([Disc(complex(0, FLOOR), BALL)] + hook)


SIGNS = {
    "period": (".", "Ball", period, "c3"),
    "comma": (",", "Ball and dash", comma, "c3"),
    "exclam": ("!", "Tube and ball", exclam, "c1"),
    "question": ("?", "Hook and ball", question, "c5"),
}

