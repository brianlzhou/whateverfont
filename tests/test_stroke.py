import math

import pytest

from whateverfont.geom import contour_area, contour_bounds
from whateverfont.stroke import Cap, Node, Pen, Stroke, expand


def stem(flare=0.0):
    return Stroke([Node(0j, 1 + flare, 1.9), Node(100j, 1, 0.0), Node(600j, 1, 0.0), Node(700j, 1 + flare, 1.9)],
                  [None, None, None], start=Cap(1 + 0j), end=Cap(1 + 0j))


def test_stem_is_a_rectangle():
    (c,) = expand(stem(), Pen.for_stems(80, 1.0))
    assert math.isclose(-contour_area(c), 80 * 700, rel_tol=1e-6)
    assert contour_bounds([c]) == (-40.0, 0.0, 40.0, 700.0)


def test_outer_contours_run_clockwise():
    (c,) = expand(stem(0.3), Pen.for_stems(80, 0.6))
    assert contour_area(c) < 0


def test_flare_widens_the_ends_only():
    (c,) = expand(stem(0.5), Pen.for_stems(80, 1.0))
    x0, _, x1, _ = contour_bounds([c])
    assert math.isclose(x1 - x0, 120, abs_tol=0.5)      # 80 * 1.5 at the ends
    assert -contour_area(c) < 120 * 700                 # but the middle stays 80 wide


def test_contrast_thins_horizontal_strokes():
    bar = Stroke([Node(0j), Node(500 + 0j)], [None])
    (c,) = expand(bar, Pen.for_stems(80, 0.5))
    _, y0, _, y1 = contour_bounds([c])
    assert math.isclose(y1 - y0, 40, abs_tol=1e-6)


def ring():
    k = 0.5523
    pts = [200 + 0j, 0 + 250j, -200 + 0j, 0 - 250j]
    hs = [(200 + 250j * k, 200 * k + 250j), (-200 * k + 250j, -200 + 250j * k),
          (-200 - 250j * k, -200 * k - 250j), (200 * k - 250j, 200 - 250j * k)]
    return Stroke([Node(p) for p in pts], hs, closed=True)


def test_closed_stroke_gives_outer_and_counter():
    outer, inner = expand(ring(), Pen.for_stems(80, 0.8))
    assert contour_area(outer) < 0 < contour_area(inner)
    assert abs(contour_area(outer)) > abs(contour_area(inner))


def test_structure_does_not_depend_on_the_pen():
    shapes = []
    for weight, contrast, roundness in ((40, 1.0, 0.0), (150, 0.4, 1.0), (90, 0.7, 0.3)):
        for stroke in (stem(0.0), stem(0.6), ring()):
            contours = expand(stroke, Pen.for_stems(weight, contrast), roundness, keep_structure=True)
            shapes.append([[len(seg) for seg in c] for c in contours])
    assert shapes[0:3] == shapes[3:6] == shapes[6:9]


def test_roundness_rounds_the_cap():
    square = expand(stem(), Pen.for_stems(80, 1.0), 0.0)[0]
    round_ = expand(stem(), Pen.for_stems(80, 1.0), 1.0)[0]
    assert -contour_area(round_) < -contour_area(square)
    assert contour_bounds([round_]) == contour_bounds([square])


def test_dilate_keeps_counters_and_islands():
    from whateverfont.geom import contour_area, reverse_contour
    from whateverfont.outline import circle, depths, dilate, union
    # a ring with a dot in the middle: an outside, a counter, and an island in it
    shape = [circle(0, 0, 300), reverse_contour(circle(0, 0, 200)), circle(0, 0, 60)]
    assert sorted(depths(union(shape))) == [0, 1, 2]
    for amount in (3, 7, 10, 12, 25, 40):
        out = dilate(shape, amount)
        areas = sorted(round(contour_area(c)) for c in out)
        assert len(out) == 3, (amount, areas)
        assert sum(1 for a in areas if a > 0) == 1, amount                         # the counter is still there
        import math
        want = -math.pi * ((300 + amount) ** 2 - (200 - amount) ** 2 + (60 + amount) ** 2)
        assert sum(areas) == pytest.approx(want, rel=0.01), amount
    # a counter that is narrower than twice the amount closes
    assert len(dilate([circle(0, 0, 300), reverse_contour(circle(0, 0, 20))], 30)) == 1


def test_dilate_keeps_the_counter_of_every_round_letter():
    from whateverfont import latin
    from whateverfont.geom import contour_area
    from whateverfont.glyph import G
    from whateverfont.outline import dilate, union
    from whateverfont.presets import preset
    recipes = latin()
    for name in ("O", "zero", "Q", "o", "D"):
        for p in (preset("geometric", weight=150), preset("rounded", weight=144, width=1.1)):
            g = G(p, name, recipes[name].case)
            recipes[name].fn(g)
            ink = union(g.outlines())
            for amount in (5, 7, 10, 12):
                grown = dilate(ink, amount)
                assert sum(1 for c in grown if contour_area(c) > 5000) == 1, (name, amount)
