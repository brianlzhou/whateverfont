"""Proof images: how glyphs are filled."""

import sys

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

from whateverfont import proof


def _square(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def test_overlapping_contours_of_a_static_font_are_ink(tmp_path):
    """Two squares that overlap, as in a composite glyph or a font from another tool. A renderer fills
    them by non-zero winding: the overlap is ink, and so is all of the second square."""
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({0x41: "A"})
    pen = TTGlyphPen(None)
    _square(pen, 100, 0, 600, 500)
    _square(pen, 300, 200, 800, 700)
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (900, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Overlap", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    path = tmp_path / "Overlap-Regular.ttf"
    fb.save(str(path))
    img = Image.new("RGB", (200, 200), "white")
    proof.Renderer(path).draw(img, 0, 150, "A", 100, ink=(0, 0, 0))
    font_to_px = lambda x, y: (round(x * 0.1), round(150 - y * 0.1))
    assert img.getpixel(font_to_px(450, 350))[0] < 60     # the overlap
    assert img.getpixel(font_to_px(700, 600))[0] < 60     # the second square alone
    assert img.getpixel(font_to_px(200, 100))[0] < 60     # the first square alone
    assert img.getpixel(font_to_px(200, 650))[0] > 200    # outside both


def test_retracing_without_numpy_says_how_to_install_it(monkeypatch):
    import whateverfont
    from whateverfont import trace
    monkeypatch.setitem(sys.modules, "whateverfont.skeleton", None)
    monkeypatch.delattr(whateverfont, "skeleton", raising=False)
    with pytest.raises(trace.MissingDependency, match=r"pip install 'whateverfont\[trace\]'"):
        trace.trace_glyph([])
