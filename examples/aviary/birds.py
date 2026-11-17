"""The birds of Aviary, one construction per letter. Font units, facing right, ground at y = 0."""

from aviary import (GAP, LEG, P, ang, band, clip, crescent, cut, disc, egg, hull, leg, lens, lines, merge, pol, poly,
                    ring, rod, side)

EYE = 17.0          # the eye of every bird but the owl

# ------------------------------------------------------------------------------------------- shared parts


def legs(b, *pairs, key="ink", toe=40.0, back=20.0):
    """Legs as one piece: ((hip, foot), ...)."""
    return b.add([leg(h, f, toe, back) for h, f in pairs], key)


def beak(b, head, r, deg, length, depth, key="ink"):
    """A triangle from the edge of the head to a tip ``length`` beyond it."""
    head = P(head)
    base = head + pol(deg, r - depth * 0.45)
    tip = head + pol(deg, r + length)
    n = pol(deg + 90, depth / 2)
    return b.add(poly(base + n, tip, base - n), key)


def bill(b, head, r, deg, length, depth, droop, key="ink"):
    """A curved bill: thickest (``depth``) at the edge of the head, tapering to a tip ``length`` beyond it.

    It is a crescent of two circular arcs. The tip ends ``droop`` below the line ``deg`` (above if negative).
    """
    head = P(head)
    d = pol(deg)
    n = d * 1j
    s = 1 if droop >= 0 else -1
    bend = max(abs(droop) - depth / 2, 1.0)
    mid = head + d * r - n * s * abs(droop)
    p0, tip = mid - d * length, mid + d * length
    shape = lens(p0, tip, bend + depth, -bend) if s > 0 else lens(p0, tip, -bend, bend + depth)
    return b.add(clip(shape, side(head, deg - 90)), key)


def tail(root, deg, length, w0, w1, end="flat", notch=0.0):
    """A straight tail from ``root``: a trapezoid with a flat, forked or pointed end."""
    root = P(root)
    d, n = pol(deg), pol(deg + 90)
    tip = root + d * length
    if end == "point":
        return poly(root + n * w0 / 2, tip, root - n * w0 / 2)
    pts = [root + n * w0 / 2, tip + n * w1 / 2]
    if end == "fork":
        pts.append(tip - d * notch)
    return poly(*pts, tip - n * w1 / 2, root - n * w0 / 2)


def wing(b, p, q, belly, back, key, count=3, start=0.42):
    """A folded wing from the shoulder ``p`` to the tip ``q``, with cut lines for the primaries.

    ``belly`` and ``back`` are the bulges of its two edges. The cut lines run along the wing, on the
    belly side of its middle, from ``start`` (a share of the length) to the tip.
    """
    p, q = P(p), P(q)
    d = (q - p) / abs(q - p)
    left_is_belly = d.real <= 0               # a wing that points back has its belly on its left
    w = b.add(lens(p, q, *((belly, back) if left_is_belly else (back, belly))), key)
    if count:
        n = d * 1j if left_is_belly else -d * 1j
        step = (belly + back) / (count + 1.2)
        cuts = []
        for i in range(count):
            o = p + d * abs(q - p) * start + n * (step * (i + 0.5) - back * 0.5)
            cuts.append(band(o, o + d * 2000, GAP))
        b.cut(clip(w, cuts))
    return w


def stripes(b, region, origin, deg, step, key, width=None, gap=False, mono=False):
    """Bars across a region: a pattern of plumage."""
    return b.add(lines(region, origin, deg, step, width or step * 0.42), key, gap=gap, mono=mono, pattern=True)


def dots(b, region, origin, step, r, key, rows_offset=True, mono=False):
    origin = P(origin)
    out = []
    for j in range(-12, 13):
        for i in range(-12, 13):
            out.append(disc(origin + complex(step * i + (step / 2 if rows_offset and j % 2 else 0),
                                             step * 0.86 * j), r))
    return b.add(clip(region, out), key, gap=False, mono=mono, pattern=True)


def scallops(b, region, origin, step, key, r=14.0):
    """Rows of small arcs, open at the top: feathers seen end-on."""
    origin = P(origin)
    out = []
    for j in range(-8, 9):
        for i in range(-10, 11):
            c = origin + complex(step * i + (step / 2 if j % 2 else 0), step * 0.88 * j)
            out.append(ring(c, r, r + GAP, 200, 340))
    return b.add(clip(region, out), key, gap=False, mono=False, pattern=True)


def water(b, x0, x1, key="sky"):
    """Two lines of water under a swimming bird."""
    b.add([rod((x0, 6), (x1, 6), LEG), rod((x0 + 70, -34), (x1 - 110, -34), LEG)], key)


def branch(b, x0, x1, key="brown"):
    b.add(rod((x0, 18), (x1, 18), 36), key)


def afloat(shape, y=26.0):
    """The part of a shape above the water line."""
    return clip(shape, side((0, y), 0))


# ---------------------------------------------------------------------------------------------- the birds


def avocet(b):
    """Wader. Marks: the upturned bill, the black-and-white back, blue-gray legs."""
    legs(b, ((300, 380), (296, 0)), ((332, 380), (376, 0)), key="sky")
    b.add(lens((230, 446), (36, 480), 12, 22), "ink")
    bill(b, (466, 592), 34, 6, 150, 13, -40)
    neck = merge(hull((372, 470), 44, (458, 582), 24), disc((466, 592), 34))
    b.add(merge(hull((300, 440), 88, (56, 470)), neck), "cream")
    b.add(clip(neck, side((474, 600), 54)), "ink")
    w = wing(b, (420, 482), (96, 468), 30, 22, "ink", count=0)
    b.add(clip(w, band((440, 462), (150, 452), 26)), "cream")
    b.eye((478, 598), EYE)


def bluebird(b):
    """Small songbird. Marks: blue back, rust breast, white belly."""
    legs(b, ((236, 120), (226, 0)), ((276, 116), (282, 0)))
    b.add(tail((214, 178), 222, 200, 54, 62), "blue")
    beak(b, (378, 336), 72, -6, 40, 40)
    body = b.add(hull((252, 214), 120, (378, 336), 72), "blue")
    b.add(clip(body, disc((404, 190), 128)), "orange")
    b.add(clip(body, disc((262, 40), 112)), "cream")
    wing(b, (336, 280), (112, 128), 58, 16, "blue")
    b.eye((400, 350), EYE)


def cardinal(b):
    """Small songbird. Marks: red all over, the pointed crest, the black mask around a heavy orange beak."""
    legs(b, ((236, 120), (226, 0)), ((276, 116), (282, 0)))
    b.add(tail((210, 180), 220, 236, 54, 70), "red")
    beak(b, (378, 336), 72, -10, 50, 62, "orange")
    body = b.add(merge(hull((252, 214), 120, (378, 336), 72), hull((372, 338), 58, (316, 480))), "red")
    b.add(clip(body, disc((456, 318), 52)), "ink")
    wing(b, (336, 280), (112, 128), 58, 16, "red")
    b.eye((398, 356), EYE)


def duck(b):
    """Swimming. Marks: green head, white collar, chestnut breast, a black stern."""
    water(b, 40, 600)
    body = b.add(afloat(hull((376, 150), 122, (160, 176), 64)), "gray")
    b.add(afloat(hull((150, 180), 62, (30, 244))), "ink")
    b.add(clip(body, disc((500, 130), 124)), "brown")
    w = wing(b, (400, 212), (120, 204), 40, 22, "tan", count=2, start=0.55)
    b.add(clip(w, band((214, 300), (196, 100), 34)), "blue")
    b.add(hull((506, 318), 24, (574, 300), 19), "yellow")
    head = b.add(merge(hull((424, 204), 54, (456, 312), 56), disc((460, 328), 60)), "green")
    b.add(clip(head, band((360, 248), (540, 222), 16)), "cream")
    b.eye((478, 344), EYE)


def eagle(b):
    """Big, upright. Marks: white head and tail, hooked yellow beak, yellow feet."""
    legs(b, ((270, 190), (258, 0)), ((316, 190), (326, 0)), key="yellow", toe=44, back=26)
    b.add(tail((226, 220), 244, 200, 80, 104), "cream", mono="line")
    b.add(lens((404, 660), (552, 590), 60, -14), "yellow")
    body = b.add(merge(hull((330, 500), 128, (230, 210), 70), disc((360, 652), 84)), "brown")
    b.add(clip(body, disc((396, 716), 150)), "cream", mono="line")
    wing(b, (392, 520), (176, 150), 70, 30, "brown")
    b.cut(clip(disc((360, 652), 84), band((340, 712), (446, 680), GAP)))
    b.eye((396, 668), EYE, ring_key="yellow")


def flamingo(b):
    """Tall wader. Marks: pink, one leg folded like a 4, the bent beak with a black tip."""
    legs(b, ((262, 400), (262, 0)), key="pink", toe=48, back=24)
    b.add([band((300, 400), (214, 268), LEG), band((214, 268), (318, 322), LEG), disc((214, 268), LEG / 2)],
          "pink")
    b.add(lens((250, 440), (36, 500), 18, 40), "ink")
    neck = [ring((288, 626), 80, 112, -52, 90), ring((288, 788), 50, 82, -90, -270)]
    bill = merge(hull((330, 874), 22, (414, 860), 18), hull((414, 860), 18, (418, 788), 9))
    b.add(cut(bill, side((0, 834), 0)), "ink")
    b.add(clip(bill, side((0, 834), 0)), "cream")
    b.add(merge(hull((290, 480), 104, (64, 506)), neck, disc((322, 878), 38)), "pink")
    wing(b, (364, 512), (120, 500), 34, 30, "pink", count=2, start=0.5)
    b.eye((336, 888), 13)


def goose(b):
    """Big. Marks: the long black neck, the white chinstrap, a pale breast and a black tail."""
    legs(b, ((240, 200), (232, 0)), ((292, 196), (302, 0)), toe=46, back=22)
    b.add(lens((180, 330), (40, 374), 30, 22), "ink")
    body = b.add(hull((404, 290), 128, (190, 320), 92), "tan")
    b.add(clip(body, disc((150, 236), 70)), "cream")
    b.add(clip(body, disc((540, 240), 104)), "cream")
    wing(b, (430, 356), (130, 330), 46, 26, "brown")
    beak(b, (490, 664), 50, -10, 46, 34)
    head = b.add(merge(hull((448, 360), 46, (480, 640), 32), disc((490, 664), 50)), "ink")
    b.add(clip(head, lens((470, 616), (470, 694), 0, 30)), "cream", mono=False)
    b.eye((508, 680), EYE)


def hummingbird(b):
    """Flying. Marks: the needle bill, the ruby throat, wings raised in a blur."""
    wing(b, (300, 516), (180, 800), 44, 18, "sky", count=2, start=0.3)
    b.add(tail((210, 380), 236, 110, 34, 56, end="fork", notch=30), "green")
    beak(b, (322, 522), 50, 4, 150, 14)
    body = b.add(merge(hull((262, 440), 66, (196, 352), 22), disc((322, 522), 50)), "green")
    b.add(clip(body, disc((372, 458), 64)), "red")
    b.add(clip(body, disc((262, 330), 66)), "cream")
    wing(b, (292, 500), (60, 650), 48, 18, "sky", count=2, start=0.3)
    b.eye((336, 536), EYE)


def ibis(b):
    """Wader. Marks: scarlet all over, the long down-curved bill, black wing tips."""
    legs(b, ((270, 360), (264, 0)), ((300, 360), (344, 0)), key="red")
    b.add(lens((214, 418), (40, 446), 10, 20), "ink")
    bill(b, (440, 614), 36, -26, 156, 18, 64)
    b.add(merge(hull((290, 440), 96, (60, 462)), hull((352, 480), 46, (432, 604), 28), disc((440, 614), 36)),
          "red")
    wing(b, (384, 470), (110, 452), 30, 24, "red", count=2, start=0.5)
    b.eye((452, 624), 14)


def jay(b):
    """Songbird. Marks: the crest, the black necklace, black bars on a blue wing and tail."""
    legs(b, ((236, 120), (226, 0)), ((276, 116), (282, 0)))
    t = b.add(tail((206, 184), 220, 232, 60, 80), "blue")
    stripes(b, t, (130, 110), 130, 36, "ink")
    b.add(clip(t, disc(P(206, 184) + pol(220, 232), 40)), "cream")
    beak(b, (378, 336), 72, -6, 40, 34)
    body = b.add(merge(hull((252, 214), 120, (378, 336), 72), hull((372, 340), 56, (300, 486))), "blue")
    b.add(clip(body, disc((412, 212), 132)), "cream")
    b.add(clip(body, ring((404, 300), 96, 96 + 20, 196, 336)), "ink")
    w = wing(b, (336, 280), (112, 128), 58, 16, "blue", count=0)
    stripes(b, w, (200, 200), 120, 34, "ink")
    b.eye((400, 352), EYE)


def kingfisher(b):
    """Perched. Marks: the dagger bill, a turquoise back with pale spots, orange below, a white throat."""
    branch(b, 70, 470)
    b.add([rod((262, 80), (250, 36), 16), rod((292, 80), (300, 36), 16)], "red")
    b.add(tail((214, 150), 236, 120, 54, 50), "teal")
    beak(b, (340, 410), 88, -8, 150, 52)
    body = b.add(merge(hull((262, 230), 110, (340, 410), 88)), "teal")
    b.add(clip(body, disc((390, 206), 150)), "orange")
    b.add(clip(body, disc((420, 396), 40)), "orange")
    b.add(clip(body, disc((420, 334), 30)), "cream", mono=False)
    w = wing(b, (330, 330), (150, 140), 56, 20, "teal", count=0)
    dots(b, w, (240, 240), 34, 7, "sky")
    b.eye((372, 430), EYE)


def loon(b):
    """Swimming. Marks: black head with a striped collar, a checkered back, the red eye."""
    water(b, 30, 620)
    b.add(afloat(hull((120, 124), 34, (40, 150))), "ink")
    body = b.add(afloat(hull((210, 110), 88, (410, 120), 100)), "ink")
    dots(b, clip(body, side((0, 92), 0)), (300, 110), 32, 8, "cream")
    beak(b, (480, 272), 56, -6, 96, 32)
    head = b.add(merge(hull((436, 160), 60, (472, 262), 52), disc((480, 272), 56)), "ink")
    b.add(clip(head, merge(band((380, 212), (560, 196), 34))), "cream", gap=False, mono=False)
    stripes(b, clip(head, band((380, 212), (560, 196), 34)), (440, 200), 90, 18, "ink", width=9)
    b.eye((498, 288), EYE, ring_key="red")


def magpie(b):
    """Songbird. Marks: black and white, the long green tail, the white shoulder."""
    legs(b, ((260, 140), (250, 0)), ((292, 136), (300, 0)))
    t = b.add(hull((230, 220), 34, (-150, 130), 22), "teal")
    b.cut(clip(t, band((240, 222), (-200, 120), GAP)))
    beak(b, (382, 336), 66, -6, 46, 30)
    body = b.add(hull((272, 232), 108, (382, 336), 66), "ink")
    b.add(clip(body, disc((300, 120), 104)), "cream", mono="line")
    w = wing(b, (360, 292), (150, 186), 52, 16, "ink", count=0)
    b.add(clip(w, band((420, 320), (200, 230), 36)), "cream", mono=False)
    b.eye((404, 350), EYE)


def night_heron(b):
    """Stocky wader. Marks: black crown and back, gray wings, white plumes, the red eye, yellow legs."""
    legs(b, ((280, 240), (270, 0)), ((316, 240), (334, 0)), key="yellow")
    beak(b, (430, 450), 70, -10, 78, 38)
    body = b.add(merge(hull((290, 330), 126, (84, 330)), disc((430, 450), 70)), "gray")
    b.add(clip(body, merge(side((0, 386), 0), disc((404, 520), 76))), "ink")
    b.add(clip(body, merge(disc((470, 330), 120), disc((452, 420), 52), side((0, 250), 180))), "cream",
          mono="line")
    wing(b, (370, 360), (110, 300), 56, 22, "gray")
    b.add([rod((400, 506), (200, 450), 10), rod((396, 494), (226, 418), 10)], "cream", mono=False)
    b.eye((452, 470), EYE, ring_key="red")


def owl(b):
    """Front view. Marks: ear tufts, facial discs with big yellow eyes, a barred belly."""
    branch(b, 40, 480)
    for x in (206, 314):
        b.add([rod((x, 70), (x + dx, 22), 18) for dx in (-26, 0, 26)], "ink")
    b.add([poly((150, 640), (114, 790), (214, 690)), poly((370, 640), (406, 790), (306, 690))], "brown")
    body = b.add(hull((260, 262), 182, (260, 520), 172), "brown")
    belly = b.add(clip(body, disc((260, 214), 132)), "cream")
    scallops(b, belly, (260, 156), 52, "brown")
    for s in (-1, 1):
        out, inside = 44, 18
        b.add(lens((260 + s * 170, 470), (260 + s * 138, 104), *((out, inside) if s > 0 else (inside, out))), "tan")
    b.add(merge(disc((196, 528), 86), disc((324, 528), 86)), "tan")
    b.add(poly((236, 486), (284, 486), (260, 420)), "ink")
    for x in (196, 324):
        b.eye((x, 530), 44, 22, ring_key="yellow")


def penguin(b):
    """Upright. Marks: black back, white front, the orange ear patch and breast."""
    b.add([lens((140, 0), (250, 0), 22, 0), lens((290, 0), (424, 0), 24, 0)], "ink")
    bill(b, (312, 590), 84, -8, 110, 22, 16)
    body = b.add(merge(hull((270, 192), 170, (304, 504), 96), disc((312, 590), 84)), "ink")
    front = b.add(clip(body, disc((470, 274), 236)), "cream", mono="line")
    b.add(clip(front, disc((440, 484), 92)), "yellow", gap=False)
    b.add(hull((300, 534), 22, (264, 620)), "orange")
    b.add(lens((262, 444), (196, 144), 36, 8), "ink")
    b.eye((338, 608), EYE)


def quail(b):
    """Plump, on the ground. Marks: the plume, the black face edged in white, a scaled belly."""
    legs(b, ((236, 80), (226, 0)), ((276, 76), (282, 0)), key="gray", toe=34, back=16)
    b.add(tail((140, 190), 200, 76, 56, 60), "slate")
    b.add(lens((372, 372), (446, 470), 26, -10), "ink")
    beak(b, (372, 316), 64, -16, 26, 30)
    body = b.add(hull((256, 196), 134, (372, 316), 64), "slate")
    belly = b.add(clip(body, disc((290, 60), 132)), "tan")
    scallops(b, belly, (290, 70), 40, "brown", r=10)
    b.add(clip(body, disc((420, 270), 46)), "ink")
    b.cut(clip(body, ring((420, 270), 46, 46 + GAP, 90, 300)))
    w = wing(b, (330, 250), (120, 150), 50, 14, "brown", count=0)
    b.cut(lines(w, (200, 200), 30, 32, GAP))
    b.eye((392, 336), EYE)


def robin(b):
    """Round. Marks: the orange face and breast edged in gray, a brown back."""
    legs(b, ((250, 100), (240, 0)), ((292, 98), (302, 0)))
    b.add(tail((176, 190), 206, 130, 56, 66), "brown")
    beak(b, (386, 330), 80, -4, 36, 26)
    body = b.add(hull((270, 240), 148, (386, 330), 80), "brown")
    b.add(clip(body, disc((430, 250), 138)), "gray")
    b.add(clip(body, disc((430, 250), 118)), "orange", gap=False)
    b.add(clip(body, disc((280, 40), 120)), "cream")
    wing(b, (300, 300), (130, 150), 52, 14, "brown")
    b.eye((410, 352), EYE)


def swallow(b):
    """Flying. Marks: forked tail streamers, dark blue back, rust throat, buff belly."""
    b.add(lens((330, 470), (196, 800), 52, -18), "blue")
    b.add([tail((222, 420), 190, 250, 30, 6, end="point"), tail((222, 406), 162, 226, 30, 6, end="point")],
          "blue")
    beak(b, (434, 458), 44, -4, 30, 26)
    body = b.add(merge(hull((350, 440), 54, (200, 418), 16), disc((434, 458), 44)), "blue")
    b.add(clip(body, disc((474, 446), 38)), "orange")
    b.add(clip(body, side((100, 412), 176)), "cream")
    b.add(lens((372, 452), (110, 760), 66, -22), "blue")
    b.eye((450, 466), 15)
    b.shift(0, -60)


def toucan(b):
    """Perched. Marks: the huge orange beak with a black tip, the white bib, a blue eye ring."""
    branch(b, 60, 440)
    b.add([rod((250, 90), (240, 36), 16), rod((280, 90), (290, 36), 16)], "sky")
    b.add(tail((214, 220), 238, 190, 70, 80), "ink")
    beak_shape = b.add(lens((364, 566), (660, 470), 74, 14), "orange")
    b.add(clip(beak_shape, disc((660, 470), 64)), "ink")
    body = b.add(merge(hull((256, 280), 118, (300, 470), 86), disc((316, 548), 84)), "ink")
    b.add(clip(body, disc((388, 470), 92)), "cream", mono="line")
    b.add(clip(body, disc((180, 176), 66)), "red")
    b.add(disc((338, 566), 32), "yellow", gap=False)
    b.eye((338, 566), EYE, ring_key="sky")


def hoopoe(b):
    """Songbird. Marks: the fan crest with black tips, zebra-barred wings and tail, a thin curved bill."""
    legs(b, ((236, 110), (226, 0)), ((276, 106), (282, 0)))
    t = b.add(tail((212, 170), 214, 180, 56, 64), "ink")
    b.add(clip(t, band(P(212, 170) + pol(214, 110), P(212, 170) + pol(214, 140), 200)), "cream")
    fan = b.add(merge(*[hull((372, 356), 16, P(372, 356) + pol(a, 136), 14) for a in (70, 92, 114, 136, 158)]),
                "tan")
    b.add(clip(fan, crescent((372, 356), 160, (372, 356), 112)), "ink", gap=False)
    bill(b, (372, 330), 62, -20, 120, 14, 30)
    b.add(hull((260, 204), 112, (372, 330), 62), "tan")
    w = wing(b, (350, 270), (120, 150), 52, 16, "ink", count=0)
    stripes(b, w, (240, 200), 104, 34, "cream")
    b.eye((394, 344), EYE)


def vulture(b):
    """Soaring, seen from the front. Marks: wings raised in a V, two-tone underwings, the small red head."""
    for s in (-1, 1):
        shoulder, tip = P(400 + s * 40, 470), P(400 + s * 360, 630)
        w = b.add(hull(shoulder, 62, tip, 44), "gray")
        d = (tip - shoulder) / abs(tip - shoulder)
        b.add(clip(w, side(shoulder, ang(d if s > 0 else -d))), "ink")
        n = d * 1j
        b.cut(clip(w, [band(tip - d * 80 + n * k * 24, tip + d * 200 + n * k * 24, GAP) for k in (-1, 0, 1)]))
    b.add(tail((400, 380), 270, 120, 64, 90), "ink")
    b.add(hull((400, 440), 58, (400, 540), 42), "ink")
    b.add(disc((400, 584), 32), "red")
    b.add(poly((390, 572), (410, 572), (400, 534)), "cream")
    b.shift(0, 40)


def woodpecker(b):
    """On a trunk. Marks: an all-red head, black back with a white wing block, white belly."""
    b.add(poly((424, 0), (424, 860), (520, 860), (520, 0)), "brown")
    b.add([band((370, 330), (424, 320), LEG), band((370, 400), (424, 392), LEG),
           rod((424, 300), (424, 340), LEG), rod((424, 372), (424, 412), LEG)], "ink")
    b.add(tail((370, 300), 296, 210, 52, 24, end="point"), "ink")
    beak(b, (330, 590), 74, -2, 32, 30)
    body = b.add(hull((340, 420), 98, (330, 590), 74), "ink")
    b.add(clip(body, disc((470, 420), 100)), "cream", mono="line")
    b.add(clip(body, disc((330, 600), 92)), "red")
    w = wing(b, (320, 520), (300, 260), 40, 34, "ink", count=0)
    b.add(clip(w, side((0, 400), 180)), "cream", mono=False)
    b.eye((352, 606), EYE)


def crossbill(b):
    """Songbird. Marks: the crossed bill, rose body, black wings with two white bars."""
    legs(b, ((236, 120), (226, 0)), ((276, 116), (282, 0)))
    b.add(tail((206, 180), 214, 170, 50, 64, end="fork", notch=22), "ink")
    b.add(lens((410, 370), (512, 290), 34, -12), "ink")
    b.add(lens((404, 296), (510, 352), -12, 34), "ink")
    body = b.add(hull((252, 214), 116, (372, 330), 72), "pink")
    w = wing(b, (336, 276), (112, 130), 56, 16, "ink", count=0)
    d, n = pol(213), pol(123)
    b.add(clip(w, [band(P(336, 276) + d * t - n * 90, P(336, 276) + d * t + n * 90, 18) for t in (78, 132)]),
          "cream", mono=False)
    b.eye((394, 346), EYE)


def warbler(b):
    """Songbird. Marks: yellow all over, red streaks on the breast, olive wings."""
    legs(b, ((236, 120), (226, 0)), ((276, 116), (282, 0)))
    b.add(tail((212, 176), 226, 170, 50, 58), "yellow")
    beak(b, (372, 330), 68, -4, 34, 26)
    body = b.add(hull((252, 210), 114, (372, 330), 68), "yellow")
    breast = clip(body, disc((390, 200), 100))
    streaks = [rod((x + 14 * (j % 2), y), (x + 6 + 14 * (j % 2), y + 22), 11)
               for x in range(260, 480, 28) for j, y in enumerate(range(100, 330, 34))]
    b.add(clip(breast, streaks), "orange", gap=False, mono=False, pattern=True)
    wing(b, (330, 276), (116, 132), 54, 16, "green")
    b.eye((394, 344), EYE)


def zebra_finch(b):
    """Songbird. Marks: the orange cheek, zebra bars on the throat, a red beak, a barred tail."""
    legs(b, ((236, 110), (226, 0)), ((272, 106), (280, 0)), key="orange")
    t = b.add(tail((206, 176), 214, 150, 46, 56), "ink")
    stripes(b, t, (150, 120), 124, 30, "cream")
    beak(b, (362, 312), 66, -8, 40, 44, "red")
    body = b.add(hull((252, 200), 108, (362, 312), 66), "gray")
    throat = b.add(clip(body, disc((410, 214), 74)), "cream")
    stripes(b, throat, (400, 220), 0, 22, "ink", width=10)
    flank = b.add(clip(body, disc((240, 130), 80)), "brown")
    dots(b, flank, (240, 130), 30, 7, "cream")
    b.add(clip(body, disc((382, 292), 30)), "orange")
    wing(b, (320, 260), (120, 140), 48, 14, "gray")
    b.eye((380, 330), EYE)


BIRDS = {
    "A": ("Avocet", avocet),
    "B": ("Bluebird", bluebird),
    "C": ("Cardinal", cardinal),
    "D": ("Mallard", duck),
    "E": ("Bald eagle", eagle),
    "F": ("Flamingo", flamingo),
    "G": ("Canada goose", goose),
    "H": ("Hummingbird", hummingbird),
    "I": ("Scarlet ibis", ibis),
    "J": ("Blue jay", jay),
    "K": ("Kingfisher", kingfisher),
    "L": ("Loon", loon),
    "M": ("Magpie", magpie),
    "N": ("Night heron", night_heron),
    "O": ("Owl", owl),
    "P": ("King penguin", penguin),
    "Q": ("California quail", quail),
    "R": ("Robin", robin),
    "S": ("Swallow", swallow),
    "T": ("Toucan", toucan),
    "U": ("Hoopoe", hoopoe),
    "V": ("Turkey vulture", vulture),
    "W": ("Red-headed woodpecker", woodpecker),
    "X": ("Crossbill", crossbill),
    "Y": ("Yellow warbler", warbler),
    "Z": ("Zebra finch", zebra_finch),
}

# --------------------------------------------------------------------------------------- the figures 0-9


def blue_egg(b):
    """0: a blue egg with brown speckles."""
    e = b.add(egg((0, 150), 150), "sky")
    dots(b, e, (0, 120), 62, 9, "brown")


def feather(b):
    """1: a blue jay's feather, barred in black."""
    b.add(rod((46, 0), (84, 120), 18), "ink")
    p, q = P(80, 110), P(214, 600)
    vane = b.add(lens(p, q, 74, 52), "blue")
    d = (q - p) / abs(q - p)
    b.add(clip(vane, [band(p + d * t - d * 1j * 200, p + d * t + d * 1j * 200, 30) for t in (170, 270, 370)]),
          "ink", gap=False, mono=False, pattern=True)
    n = d * 1j
    b.cut(clip(vane, [band(p - d * 40, q + d * 40, GAP), band(p + d * 300 + n * 30, p + d * 360 + n * 90, GAP),
                      band(p + d * 220 - n * 20, p + d * 280 - n * 80, GAP)]))


def nest(b):
    """2: a woven nest with three eggs."""
    b.add([egg((x, 190), 52) for x in (-100, 0, 100)], "sky")
    bowl = b.add(lens((-220, 176), (220, 176), 0, 176), "brown")
    b.cut(lines(bowl, (0, 90), 28, 52, GAP))
    b.cut(lines(bowl, (0, 90), -28, 52, GAP))


def track(c, deg):
    c = P(c)
    return [rod(c, c + pol(deg + a, n), 24) for a, n in ((-36, 104), (0, 124), (36, 104), (180, 46))]


def footprints(b):
    """3: two tracks of a walking bird."""
    b.add(track((70, 70), 76) + track((236, 300), 64), "ink")


def worm(b):
    """4: a worm in three humps."""
    body = merge(ring((0, 78), 34, 78, 180, 0), ring((112, 78), 34, 78, 180, 360), ring((224, 78), 34, 78, 180, 0),
                 disc((-56, 78), 22), disc((280, 78), 22))
    w = b.add(body, "pink")
    b.cut(clip(w, [band(P(x, 78) + pol(a, 20), P(x, 78) + pol(a, 90), GAP)
                   for x, angles in ((0, (60, 120)), (112, (240, 300)), (224, (60, 120))) for a in angles]))
    b.eye((272, 82), 13)


def twig(b):
    """5: a twig with three leaves."""
    b.add(rod((0, 40), (380, 300), 26), "brown")
    for a, s in ((0.3, 1), (0.55, -1), (0.85, 1)):
        base = P(0, 40) + (P(380, 300) - P(0, 40)) * a
        tip = base + pol(34 + s * 70, 170)
        leaf = b.add(lens(base, tip, 40, 40), "green")
        b.cut(clip(leaf, band(base, tip, GAP)))


def birdhouse(b):
    """6: a birdhouse on a post."""
    b.add(band((0, 0), (0, 150), 44), "brown")
    b.add(rod((0, 236), (64, 236), 16), "brown")
    b.add(poly((-120, 140), (-120, 380), (0, 470), (120, 380), (120, 140)), "red")
    b.add(merge(band((0, 500), (-170, 372), 44), band((0, 500), (170, 372), 44), disc((0, 492), 22)), "ink")
    b.add(disc((0, 300), 44), "ink", gap=False, mono=False)


def berries(b):
    """7: a sprig of red berries."""
    b.add([band((10, 470), (-70, 190), 12), band((10, 470), (40, 140), 12), band((10, 470), (120, 240), 12)],
          "brown")
    leaf = b.add(lens((14, 460), (190, 540), 44, 44), "green")
    b.cut(clip(leaf, band((14, 460), (190, 540), GAP)))
    b.add([disc((-70, 150), 64), disc((40, 76), 70), disc((128, 196), 58)], "red")


def pine_cone(b):
    """8: a pine cone, scaled."""
    b.add(rod((0, 420), (34, 480), 20), "brown")
    cone = b.add(hull((0, 156), 120, (0, 360), 74), "brown")
    scallops(b, cone, (0, 120), 56, "tan", r=18)


def acorn(b):
    """9: an acorn with a crosshatched cap."""
    b.add(rod((0, 330), (26, 400), 18), "brown")
    b.add(egg((0, 168), 104, -90), "tan")
    cap = b.add(clip(disc((0, 196), 130), side((0, 196), 0)), "brown")
    b.cut(lines(cap, (0, 300), 45, 38, GAP))
    b.cut(lines(cap, (0, 300), -45, 38, GAP))


EXTRAS = {
    "0": ("Egg", blue_egg),
    "1": ("Feather", feather),
    "2": ("Nest", nest),
    "3": ("Footprints", footprints),
    "4": ("Worm", worm),
    "5": ("Twig", twig),
    "6": ("Birdhouse", birdhouse),
    "7": ("Berries", berries),
    "8": ("Pine cone", pine_cone),
    "9": ("Acorn", acorn),
}

# ----------------------------------------------------------------------------------------------- palettes

#: Every piece of every bird takes one of these colors.
KEYS = ("ink", "cream", "gray", "slate", "blue", "sky", "teal", "green", "yellow", "orange", "red", "pink",
        "brown", "tan")


def _mix(a: str, b: str, t: float) -> str:
    """The color ``t`` of the way from ``a`` to ``b``."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def _tints(ink: str, paper: str, shares: dict) -> dict:
    return {k: _mix(paper, ink, shares[k]) for k in KEYS}


#: How much ink each key gets in a one-ink print, from the paper (0) to solid (1).
_SHARES = dict(ink=1.0, cream=0.15, gray=0.34, slate=0.72, blue=0.72, sky=0.36, teal=0.62, green=0.55,
               yellow=0.22, orange=0.48, red=0.86, pink=0.3, brown=0.86, tan=0.42)

PALETTES = {
    # One harmonized set of fourteen colors for all 26 birds.
    "Field Guide": dict(ink="#26221E", cream="#F2E8D5", gray="#A9A49A", slate="#5D6B74", blue="#2F5E9E",
                        sky="#79A9C9", teal="#2A8381", green="#5C8A3C", yellow="#E8B53A", orange="#DE7A33",
                        red="#C0392B", pink="#E6919B", brown="#7B5236", tan="#C9A27C"),
    # One ink in tints, as from a single plate.
    "Letterpress": _tints("#1F2E46", "#FFFFFF", _SHARES),
    # Two inks, fluorescent pink and blue, and where they print over each other.
    "Risograph": dict(ink="#3B2C7A", cream="#FFD3EA", gray="#9CCBE6", slate="#0078BF", blue="#0078BF",
                      sky="#80BBE0", teal="#0078BF", green="#3D96CF", yellow="#FFB3DC", orange="#FF48B0",
                      red="#FF48B0", pink="#FF8CCB", brown="#6B3C9C", tan="#FFB3DC"),
    # Chalk on a dark ground: light tints, for a dark background such as #17181D.
    "Chalk": _tints("#F4ECDC", "#17181D", {k: 1.0 - 0.62 * (1.0 - v) for k, v in _SHARES.items()} | {"cream": 0.5}),
}
