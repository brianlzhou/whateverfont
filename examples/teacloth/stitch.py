"""Cross stitch for Teacloth: every letter is a chart of X stitches on one grid of cloth.

A sampler is worked on even-weave linen. Each stitch covers one square of the weave: a thread goes
from the lower left hole to the upper right one (the under thread), and a second thread crosses it
from the upper left to the lower right (the top thread). Every top thread lies the same way. A
stitcher works a letter from a chart: a square is stitched, or it is left bare.

This effect makes the chart from the engine's own letter and stitches it:

1. The plain letter is drawn on a fine raster whose rows line up with the rows of the cloth: the
   baseline, the x-height and the cap height are grid lines (font.py chooses them so).
2. The letter may slide sideways by a fraction of a square. The effect tries every position and
   keeps the one where the fewest squares are half covered, so that stems fall on whole squares.
3. A square is stitched when 56% of it is inside the letter. A stroke that lies across two rows or
   two columns, half in each, is settled by its middle: a line through the middle of the square
   column (or row) crosses the stroke, the crossing is rounded to whole squares, and those squares
   are stitched. So a bar one square thick always gives one row, and a stem two squares wide two
   columns, wherever the engine put them.
4. Clean-up: a stitch with no neighbor is dropped, a bare square inside a stroke is filled, every
   counter keeps at least one bare square, every separate part (a dot) keeps at least one stitch,
   and parts that would touch are moved apart by whole rows.
5. An accented letter is the chart of its base letter, so `é` has the same `e` as `e`, with the
   mark on top. A mark above the letter is drawn from a small chart (``MARKS``), centered where the
   engine put the mark, with one bare row between it and the letter. Other marks (a cedilla, an
   ogonek, a tonos beside a capital) are charted from the engine's drawing on the same grid.
6. A glyph that the rules cannot chart well is charted by hand in font.py.
7. The chart is placed in a glyph that is a whole number of squares wide, with a bare column on
   each side, so every letter on a line sits on the same grid.

Each stitch is two bars with slightly round ends. The color layers are the under threads, row by
row, then the top threads, row by row: keys ``u0`` to ``u9`` and ``t0`` to ``t9``, by the row of the
stitch counted from the baseline, modulo ten. A one-color palette gives every row the same thread;
a banded one (:func:`banded`) changes thread from one band of rows to the next.
"""

from __future__ import annotations

import math
import unicodedata

from PIL import Image, ImageDraw

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, flatten_contour, transform_contour
from whateverfont.glyph import G, Recipe, Recipes
from whateverfont.outline import difference, union

#: Raster pixels along one side of a square. Odd, so one pixel sits on the middle of the square.
RES = 15
#: Share of a square that must be inside the letter for a stitch.
KEEP = 0.56
#: A stroke crossing that is settled by its middle may be at most this many squares long.
THIN = 2.6
#: Rows of the color cycle: keys u0 to u9 and t0 to t9.
CYCLE = 10
#: The highest row a stack of two marks may reach (on a capital of ten rows). font.py sets the top
#: of the line just above it.
TOP_ROW = 14

NEAR8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
NEAR4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]

#: Marks above a letter, as small charts: rows from the top, "#" for a stitch.
MARKS = {
    "\u0300": ["##.", ".##"],                      # grave
    "\u0301": [".##", "##."],                      # acute
    "\u0302": [".##.", "#..#"],                    # circumflex
    "\u0303": [".##.#", "#.##."],                  # tilde
    "\u0304": ["####"],                            # macron
    "\u0306": ["#...#", ".###."],                  # breve
    "\u0307": ["##", "##"],                        # dot above
    "\u0308": ["##.##", "##.##"],                  # diaeresis
    "\u0309": ["##.", "..#", ".#."],               # hook above
    "\u030A": [".##.", "#..#", ".##."],            # ring above
    "\u030B": [".##.##", "##.##."],                # double acute
    "\u030C": ["#..#", ".##."],                    # caron
}
#: Marks below a letter. A cedilla and an ogonek grow from the letter; a comma and a dot hang under it.
BELOW = {
    "cedilla": [".#.", "..#", "##."],
    "ogonek": [".#.", "#..", ".##"],
    "comma": ["##", "#."],
    "dot": ["##", "##"],
    "apostrophe": ["##", ".#", "#."],               # the caron of ď ľ ť Ľ, beside the stem
}
#: The letters that lose their dot under a mark above.
DOTLESS = {"i": "dotlessi", "j": "dotlessj", "uni0456": "dotlessi", "uni0458": "dotlessj"}
#: Spacing accents drawn from the same charts as the marks above letters.
SPACING = {"grave": "\u0300", "acute": "\u0301", "circumflex": "\u0302", "tilde": "\u0303", "macron": "\u0304",
           "breve": "\u0306", "dotaccent": "\u0307", "dieresis": "\u0308", "ring": "\u030A",
           "hungarumlaut": "\u030B", "caron": "\u030C", "tonos": "\u0301"}


# --------------------------------------------------------------------------------------------- raster


def _polys(contours: list) -> list:
    out = []
    for c in contours:
        pts = flatten_contour(c, 1.0)
        if len(pts) >= 3:
            a = contour_area(c)
            out.append((abs(a), a < 0, pts))
    return sorted(out, key=lambda t: -t[0])          # larger first, so counters punch holes


class Sheet:
    """A fine raster of one glyph, lined up with the rows of the cloth.

    Pixel column 0 is at ``left``, a grid line (of the grid through ``origin``, if given); pixel row 0
    is the top of row ``top - 1``.
    """

    def __init__(self, box: tuple, cell: float, origin: float = 0.0):
        x0, y0, x1, y1 = box
        self.cell = cell
        self.px = cell / RES
        self.left = origin + (math.floor((x0 - origin) / cell) - 2) * cell
        self.top = math.ceil(y1 / cell) + 1
        bottom = math.floor(y0 / cell) - 1
        self.rows = self.top - bottom
        self.cols = math.ceil((x1 - self.left) / cell) + 2
        self.w = self.cols * RES + RES
        self.h = self.rows * RES

    def draw(self, contours: list) -> Image.Image:
        img = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(img)
        for _, solid, pts in _polys(contours):
            d.polygon([((q.real - self.left) / self.px, (self.top * self.cell - q.imag) / self.px) for q in pts],
                      fill=255 if solid else 0)
        return img

    def coverage(self, img: Image.Image, k: int) -> list:
        """Share of each square that is ink, for the grid shifted ``k`` pixels: [column][row from the top]."""
        small = img.crop((k, 0, k + self.cols * RES, self.h)).reduce(RES)
        data = small.load()
        return [[data[i, r] / 255.0 for r in range(self.rows)] for i in range(self.cols)]


def _runs(values) -> list:
    """(start, end) of each run of ink in a line of pixels."""
    out, start = [], None
    for n, v in enumerate(values):
        if v > 127 and start is None:
            start = n
        elif v <= 127 and start is not None:
            out.append((start, n))
            start = None
    if start is not None:
        out.append((start, len(values)))
    return out


def _settle(a: float, b: float) -> list:
    """The whole squares that a crossing from ``a`` to ``b`` (in squares) stands for, or [] if it is long."""
    length = b - a
    if length > THIN:
        return []
    n = max(1, math.floor(length + 0.5))
    start = math.floor((a + b) / 2 - n / 2 + 0.5 - 1e-6)   # a tie goes up (or left)
    return list(range(start, start + n))


def _votes(sheet: Sheet, img: Image.Image, k: int) -> set:
    """Squares that the middle lines of the columns and the rows settle (step 3)."""
    data = img.load()
    out = set()
    half = RES // 2
    for i in range(sheet.cols):
        x = k + i * RES + half
        for a, b in _runs([data[x, y] for y in range(sheet.h)]):
            for r in _settle(a / RES, b / RES):
                if 0 <= r < sheet.rows:
                    out.add((i, r))
    for r in range(sheet.rows):
        y = r * RES + half
        line = [data[x, y] for x in range(k, k + sheet.cols * RES)]
        for a, b in _runs(line):
            for i in _settle(a / RES, b / RES):
                if 0 <= i < sheet.cols:
                    out.add((i, r))
    return out


# ------------------------------------------------------------------------------------------- the chart


def _parts(ink: list) -> list:
    """Each outside contour with the counters inside it: the body of a letter, a dot, an accent."""
    outers = [c for c in ink if contour_area(c) < 0]
    holes = [c for c in ink if contour_area(c) > 0]
    tests = [effects.inside([c]) for c in outers]
    groups = [[c] for c in outers]
    for h in holes:
        p = h[0][0]
        best, best_area = None, None
        for i, test in enumerate(tests):
            if test(p):
                a = abs(contour_area(outers[i]))
                if best is None or a < best_area:
                    best, best_area = i, a
        if best is not None:
            groups[best].append(h)
    return sorted(groups, key=lambda g: contour_area(g[0]))     # the largest first


def _flip(c: list) -> list:
    """A counter drawn as ink, so that it can be measured on its own."""
    return [tuple(reversed(seg)) for seg in reversed(c)]


def _chart_part(sheet: Sheet, part: list, k: int) -> set:
    """The stitched squares of one part of a letter, as (column, raster row) pairs."""
    img = sheet.draw(part)
    f = sheet.coverage(img, k)
    holes = [c for c in part if contour_area(c) > 0]
    hole_f = sheet.coverage(sheet.draw([_flip(c) for c in holes]), k) if holes else None
    cols, rows = sheet.cols, sheet.rows
    keep = {(i, r) for i in range(cols) for r in range(rows) if f[i][r] >= KEEP}
    keep |= {(i, r) for i, r in _votes(sheet, img, k) if f[i][r] >= 0.25}
    if hole_f is not None:
        # a square that is mostly counter stays bare, whatever the votes said
        keep = {(i, r) for i, r in keep if hole_f[i][r] < 0.5 or f[i][r] >= 0.75}
    # a stitch with no neighbor is a crumb
    if len(keep) > 1:
        lone = {q for q in keep if not any((q[0] + dx, q[1] + dy) in keep for dx, dy in NEAR8)}
        if len(lone) < len(keep):
            keep -= lone
    # a bare square closed in on four sides, and not part of a counter, is a pinhole
    for i in range(cols):
        for r in range(rows):
            if (i, r) in keep or f[i][r] < 0.2:
                continue
            if hole_f is not None and hole_f[i][r] >= 0.15:
                continue
            if all((i + dx, r + dy) in keep for dx, dy in NEAR4):
                keep.add((i, r))
    # every counter keeps a bare square
    for h in holes:
        hf = sheet.coverage(sheet.draw([_flip(h)]), k)
        inside = [(hf[i][r], (i, r)) for i in range(cols) for r in range(rows) if hf[i][r] >= 0.15]
        if inside and all(q in keep for _, q in inside):
            keep.discard(max(inside)[1])
    # every part keeps a stitch
    if not keep:
        best = max((f[i][r], (i, r)) for i in range(cols) for r in range(rows))
        if best[0] > 0:
            keep.add(best[1])
    return keep


def _touch(a: set, b: set) -> bool:
    return any((i + dx, j + dy) in b for i, j in a for dx, dy in NEAR8 + [(0, 0)])


def _apart(got: set, placed: set) -> set:
    """Move a part (a dot, a mark) off what is already stitched, by whole rows (rows count up).

    It moves up if it sits above the rest and down if below. A part beside the rest (the slash of
    a %) stays where it is: it may touch.
    """
    lo_g, hi_g = min(j for _, j in got), max(j for _, j in got)
    lo_p, hi_p = min(j for _, j in placed), max(j for _, j in placed)
    if lo_g > (lo_p + hi_p) / 2 and hi_g > hi_p - 1:
        step = 1
    elif hi_g < (lo_p + hi_p) / 2 and lo_g < lo_p + 1:
        step = -1
    else:
        return got
    for _ in range(3):
        if not _touch(got, placed):
            break
        got = {(i, j + step) for i, j in got}
    return got


def auto_chart(ink: list, cell: float, origin: float | None = None) -> tuple:
    """The stitches of a drawing: a set of (column, row) squares and the x of column 0.

    Rows count up from the baseline (row 0 sits on it). Without ``origin`` the drawing may slide
    sideways by a fraction of a square to land its stems on whole squares; with it, the grid lines
    go through ``origin``.
    """
    box = contour_bounds(ink)
    sheet = Sheet(box, cell, 0.0 if origin is None else origin)
    k = 0
    if origin is None:
        whole = sheet.draw(ink)
        best = None
        for kk in range(RES):
            f = sheet.coverage(whole, kk)
            doubt = sum(min(v, 1 - v) for col in f for v in col)
            if best is None or doubt < best[0] - 1e-9:
                best = (doubt, kk)
        k = best[1]
    x0 = sheet.left + k * sheet.px
    placed: set = set()
    for part in _parts(ink):
        dot = _dot(part, cell, x0)
        got = dot if dot is not None else {(i, sheet.top - 1 - r) for i, r in _chart_part(sheet, part, k)}
        if placed and got and _touch(got, placed):
            got = _apart(got, placed)
        placed |= got
    return placed, x0


def _dot(part: list, cell: float, x0: float):
    """A dot (of i, j, a period, a colon) as a block of two by two stitches, or None for any other part.

    The engine's dot is a little wider than a stem, so it covers two or three squares each way
    depending on where it falls. Every dot of the font is the same block instead.
    """
    if len(part) != 1:
        return None
    b = contour_bounds(part)
    w, h = (b[2] - b[0]) / cell, (b[3] - b[1]) / cell
    if not (1.2 <= w <= 3.3 and 1.2 <= h <= 3.3) or max(w, h) > 1.5 * min(w, h):
        return None
    if abs(contour_area(part[0])) < 0.7 * (b[2] - b[0]) * (b[3] - b[1]):
        return None
    col = round(((b[0] + b[2]) / 2 - x0) / cell - 1)
    row = round((b[1] + b[3]) / 2 / cell - 1)
    return {(col, row), (col + 1, row), (col, row + 1), (col + 1, row + 1)}


def from_rows(rows: list, top: int) -> set:
    """Squares from a hand chart: rows of "#" (stitch) and "." (bare), the first one at row ``top``."""
    return {(i, top - n) for n, row in enumerate(rows) for i, ch in enumerate(row) if ch == "#"}


# ----------------------------------------------------------------------------------- charts of glyphs


class Charter:
    """Charts every glyph of a set once: by hand, from its base letter and marks, or by the rules."""

    def __init__(self, cell: float, hand: dict, x_rows: int):
        self.cell = cell
        self.hand = hand            # glyph name -> (top row, rows)
        self.x_rows = x_rows
        self.cache: dict = {}
        self.sigs: dict = {}        # (hand-charted glyph, params) -> signature of its plain drawing

    def mark_chart(self, g: G, ink: list):
        """A mark: from ``MARKS`` if it sits above a letter, else by the rules. Columns count from x = 0."""
        rec = g.recipes[g.name]
        m = SPACING.get(g.name) or (chr(rec.unicode) if rec.unicode is not None else None)
        b = contour_bounds(ink)
        if m in MARKS and b[1] > self.x_rows * self.cell * 0.5:
            rows = MARKS[m]
            width = max(len(r) for r in rows)
            col = round((b[0] + b[2]) / 2 / self.cell - width / 2)
            # one bare row above the x-height; the mark feature lifts it onto a capital by whole rows
            cells = {(i + col, j) for i, j in from_rows(rows, self.x_rows + len(rows))}
            return cells, 0.0
        cells, x0 = auto_chart(ink, self.cell, origin=0.0)
        shift = round(x0 / self.cell)
        return {(i + shift, j) for i, j in cells}, 0.0

    def twin(self, g: G, name: str, ink: list):
        """The hand-charted glyph that ``name`` is drawn exactly like, or None."""
        if name in self.hand or not ink or "." in name:
            return None
        sig = _signature(ink)
        for other in self.hand:
            if other not in g.recipes:
                continue
            if (other, g.p) not in self.sigs:
                self.sigs[(other, g.p)] = _signature(self.plain_ink(g, other))
            if self.sigs[(other, g.p)] == sig:
                return other
        return None

    def plain_ink(self, g: G, name: str) -> list:
        rec = g.recipes[name]
        g2 = G(g.p, name, rec.case)
        g2.recipes = g.recipes
        (rec.plain or rec.fn)(g2)
        return effects.ink(g2)

    def chart(self, g: G, name: str, ink: list | None = None) -> tuple:
        """(squares, x of column 0) for glyph ``name``, drawn with the parameters of ``g``."""
        key = (name, g.p)
        if key in self.cache:
            return self.cache[key]
        if ink is None:
            ink = self.plain_ink(g, name)
        got = None
        twin = self.twin(g, name, ink)
        if twin is not None:
            # the same drawing as a glyph charted by hand (the Greek and the Cyrillic I): the same chart
            self.cache[key] = self.chart(g, twin)
            return self.cache[key]
        stem = name.split(".")[0]
        if name in self.hand or (name.endswith(".case") and stem in self.hand):
            top, rows = self.hand.get(name) or self.hand[stem]
            if name not in self.hand and ink:
                # the form for capitals: the same chart, moved as far as the engine moved the sign
                plain = self.plain_ink(g, stem)
                if plain:
                    lift = (sum(contour_bounds(ink)[1::2]) - sum(contour_bounds(plain)[1::2])) / 2
                    top += round(lift / self.cell)
            cells = from_rows(rows, top)
            b = contour_bounds(ink) if ink else (0, 0, 0, 0)
            width = max(len(r) for r in rows)
            got = (cells, (b[0] + b[2]) / 2 - width * self.cell / 2)
        if got is None and name in SPACING and ink:
            got = self.mark_chart(g, ink)
        if got is None and ink:
            got = self.composed(g, name, ink)
        if got is None and ink:
            got = auto_chart(ink, self.cell)
        self.cache[key] = got
        return got

    def composed(self, g: G, name: str, ink: list):
        """The chart of an accented letter: its base letter's chart, and the marks on top."""
        rec = g.recipes[name]
        if rec.unicode is None:
            return None
        parts = unicodedata.normalize("NFD", chr(rec.unicode))
        if len(parts) < 2:
            return None
        cmap = {r.unicode: n for n, r in g.recipes.items() if r.unicode is not None}
        base = cmap.get(ord(parts[0]))
        marks = parts[1:]
        if base is None or base == name:
            return None
        if base in DOTLESS and any(m in MARKS for m in marks):
            base = DOTLESS[base]
            if base not in g.recipes:
                return None
        base_ink = self.plain_ink(g, base)
        if not base_ink:
            return None
        area = lambda cs: abs(sum(contour_area(c) for c in cs))
        # The base letter must be drawn whole in the accented one. A Greek capital with a tonos is
        # moved right to make room for it: find how far by the largest part, and move the base too.
        dx = 0.0
        try:
            if area(difference(base_ink, ink)) > 0.01 * area(base_ink):
                big = contour_bounds(_parts(ink)[0])
                dx = big[2] - contour_bounds(_parts(base_ink)[0])[2]
                moved = [transform_contour(ct, lambda q: q + dx) for ct in base_ink]
                if area(difference(moved, ink)) > 0.01 * area(base_ink):
                    return None
            rest = [ct for ct in difference(ink, [transform_contour(ct, lambda q: q + dx) for ct in base_ink])
                    if abs(contour_area(ct)) > 0.02 * self.cell ** 2]
        except Exception:
            return None
        if not rest:
            return None
        base_cells, x0 = self.chart(g, base, base_ink)
        x0 += dx
        base_ink = [transform_contour(ct, lambda q: q + dx) for ct in base_ink]
        cells = set(base_cells)
        bb = contour_bounds(base_ink)
        c = self.cell
        # Sort the engine's marks by where they sit: on the letter, above it, below it, or beside it.
        groups: dict = {"joined": [], "above": [], "below": [], "beside": []}
        for part in _parts(rest):
            pb = contour_bounds(part)
            if pb[1] > bb[3] - 0.25 * c:
                groups["above"].append((part, pb))
            elif _joined(part, base_ink):
                groups["joined"].append((part, pb))
            elif (pb[1] + pb[3]) / 2 < bb[1] + c:
                groups["below"].append((part, pb))
            else:
                groups["beside"].append((part, pb))
        top_row = max(j for _, j in base_cells)
        low_row = min(j for _, j in base_cells)

        def middle(parts) -> float:
            """The middle of some parts, in columns."""
            return ((min(b[0] for _, b in parts) + max(b[2] for _, b in parts)) / 2 - x0) / c

        ups = [m for m in marks if m in MARKS]
        downs = [m for m in marks if m in ("\u0323", "\u0326", "\u0327", "\u0328")]
        leftover = []
        # marks above: from the charts, centered where the engine put them (two marks: on the letter)
        if groups["above"] and ups and len(ups) <= 2:
            center = ((bb[0] + bb[2]) / 2 - x0) / c if len(ups) > 1 else middle(groups["above"])
            cells |= self.stack(ups, top_row, center)
        else:
            leftover += [p for p, _ in groups["above"]]
        # marks below: a cedilla or an ogonek grows from the letter, a comma or a dot hangs under it
        for kind in ("joined", "below"):
            parts = groups[kind]
            if not parts:
                continue
            chart = None
            if kind == "joined" and downs == ["\u0327"] and min(b[1] for _, b in parts) < bb[1] + c:
                chart, top = BELOW["cedilla"], low_row - 1
            elif downs == ["\u0328"]:
                chart, top = BELOW["ogonek"], low_row - 1
            elif kind == "below" and downs and downs[0] in ("\u0326", "\u0327"):
                chart, top = BELOW["comma"], low_row - 2
            elif kind == "below" and downs == ["\u0323"]:
                chart, top = BELOW["dot"], low_row - 2
            if chart is None:
                leftover += [p for p, _ in parts]
                continue
            width = max(len(r) for r in chart)
            col = round(middle(parts) - width / 2)
            cells |= {(i + col, j) for i, j in from_rows(chart, top)}
        # a tonos beside a Greek capital: the acute, where the engine put it
        if len(groups["beside"]) == 1 and ups == ["\u0301"] and not groups["above"]:
            pb = groups["beside"][0][1]
            chart = MARKS["\u0301"]
            col = round(middle(groups["beside"]) - len(chart[0]) / 2)
            top = round((pb[1] + pb[3]) / 2 / c + len(chart) / 2 - 1)
            mark = {(i + col, j) for i, j in from_rows(chart, top)}
            cells |= _apart(mark, cells) if _touch(mark, cells) else mark
            groups["beside"] = []
        # the caron of ď ľ ť Ľ is an apostrophe beside the stem: moved right until it stands free
        if len(groups["beside"]) == 1 and ups == ["\u030C"] and not groups["above"]:
            pb = groups["beside"][0][1]
            chart = BELOW["apostrophe"]
            col = round(middle(groups["beside"]) - 1)
            top = min(top_row, round(pb[3] / c) - 1)
            mark = {(i + col, j) for i, j in from_rows(chart, top)}
            while _touch(mark, cells):
                mark = {(i + 1, j) for i, j in mark}
            cells |= mark
            groups["beside"] = []
        # anything else (a horn): by the rules, on the same grid
        if groups["beside"]:
            leftover += [p for p, _ in groups["beside"]]
        if leftover:
            ink_left = [ct for p in leftover for ct in p]
            mark, mx0 = auto_chart(ink_left, c, origin=x0)
            shift = round((mx0 - x0) / c)
            mark = {(i + shift, j) for i, j in mark}
            if _touch(mark, cells) and not _joined(ink_left, base_ink):
                mark = _apart(mark, cells)
            cells |= mark
        return cells, x0

    def stack(self, ups: list, top_row: int, center: float) -> set:
        """One or two marks above a letter whose top row is ``top_row``, with one bare row between.

        ``center`` is the middle of the marks, in columns. A second mark goes on top of the first;
        after a circumflex, an acute, a grave or a hook goes beside it, one row up, as Vietnamese
        sets them.
        """
        first = MARKS[ups[0]]
        w1 = max(len(r) for r in first)
        col1 = round(center - w1 / 2)
        bottom1 = top_row + 2
        out = {(i + col1, j) for i, j in from_rows(first, bottom1 + len(first) - 1)}
        if len(ups) == 2:
            second = MARKS[ups[1]]
            w2 = max(len(r) for r in second)
            col2 = round(col1 + w1 / 2 - w2 / 2)
            bottom2 = bottom1 + len(first) + 1
            if bottom2 + len(second) - 1 > TOP_ROW:
                bottom2 -= 1                         # a capital: no bare row between the two marks
            beside = ups[0] == "\u0302" and ups[1] in ("\u0300", "\u0301", "\u0309")
            if beside or bottom2 + len(second) - 1 > TOP_ROW:
                col2 = col1 + w1
                bottom2 = bottom1 + 1
            out |= {(i + col2, j) for i, j in from_rows(second, bottom2 + len(second) - 1)}
        return out


def _signature(ink: list) -> tuple:
    """A short description of a drawing that two identical drawings share: its box, area and parts."""
    if not ink:
        return ()
    b = contour_bounds(ink)
    return (len(ink), round(abs(sum(contour_area(c) for c in ink))), *(round(v) for v in b))


def _joined(a: list, b: list) -> bool:
    """True if two drawings touch (a cedilla or an ogonek that grows from the letter)."""
    try:
        from whateverfont.outline import dilate, intersection
        return bool(intersection(dilate(a, 2.0), b))
    except Exception:
        return False


# --------------------------------------------------------------------------------------------- stitches


def bar(a: complex, b: complex, half: float, bulge: float) -> list:
    """One thread from ``a`` to ``b``: a straight band ``2 * half`` wide whose ends bow out by ``bulge``.

    Each end is one quadratic curve. Drawn clockwise.
    """
    d = (b - a) / abs(b - a)
    n = d * 1j
    p1, p2, p3, p4 = a + n * half, b + n * half, b - n * half, a - n * half

    def cap(s: complex, e: complex, tip: complex) -> tuple:
        ctrl = tip * 2 - (s + e) / 2                       # a quadratic through the tip
        return (s, s + (ctrl - s) * 2 / 3, e + (ctrl - e) * 2 / 3, e)

    c = [(p1, p2), cap(p2, p3, b + d * bulge), (p3, p4), cap(p4, p1, a - d * bulge)]
    if contour_area(c) > 0:
        c = [tuple(reversed(seg)) for seg in reversed(c)]
    return c


class Thread:
    """The shape of one stitch in a square of side ``cell``.

    ``width`` is the thread, as a share of the square. ``gap`` is the bare cloth left between the
    ends of two stitches that meet at a corner, in units. ``bulge`` is how far the round end bows
    out, as a share of the thread width.
    """

    def __init__(self, cell: float, width: float = 0.30, gap: float = 3.0, bulge: float = 0.30):
        self.cell = cell
        self.half = cell * width / 2
        self.bulge = cell * width * bulge
        # The corners of the band reach half the width sideways, 0.707 of it in x and in y: the end
        # of a bar stays that far, plus half the gap, inside its square.
        self.inset = self.half * 0.7072 + gap / 2

    def under(self, x: float, y: float) -> list:
        """The under thread of the square whose lower left corner is (x, y): lower left to upper right."""
        e, c = self.inset, self.cell
        return bar(complex(x + e, y + e), complex(x + c - e, y + c - e), self.half, self.bulge)

    def top(self, x: float, y: float) -> list:
        """The top thread: upper left to lower right."""
        e, c = self.inset, self.cell
        return bar(complex(x + e, y + c - e), complex(x + c - e, y + e), self.half, self.bulge)


# ------------------------------------------------------------------------------------------- the effect


def _natural(g: G) -> tuple:
    """(left, right) sidebearings the plain letter asked for, and its fixed advance or None."""
    if g._advance is not None:
        return 0.0, 0.0, g._advance
    width, l, r = g._frame if g._frame is not None else (None, "s", "s")
    return g.sidebearing(l), g.sidebearing(r), None


def _margin(sb: float, cell: float) -> int:
    """Bare columns for a side: one at least, or none for a glyph made to join its neighbor (_ —)."""
    if abs(sb) <= 1.0:
        return 0
    return max(1, round(sb / cell))


def stitched(recipes: Recipes, cell: float = 70.0, x_rows: int = 7, cap_rows: int = 10, width: float = 0.30,
             gap: float = 3.0, bulge: float = 0.30, hand: dict | None = None, framed=(), names=None) -> Recipes:
    """Every glyph of ``recipes`` worked in cross stitch on squares of ``cell`` units.

    ``x_rows`` and ``cap_rows`` are the x-height and the cap height in rows: they bound the band
    that sets the bare columns beside a letter. ``hand`` maps a glyph name to a hand chart:
    (top row, [rows of "#" and "."]). The glyphs named in ``framed`` are set in a stitched frame
    with a flower at each corner (:func:`frame`). Keys: ``u0`` to ``u9`` (under threads) and ``t0``
    to ``t9`` (top threads), by row; a frame adds ``border``, ``petal``, ``heart`` and ``leaf``,
    each with ``_u`` and ``_t``.
    """
    thread = Thread(cell, width, gap, bulge)
    charter = Charter(cell, hand or {}, x_rows)
    framed = set(framed)
    out = recipes.copy()
    for name in (names or list(recipes)):
        rec = recipes[name]
        plain = rec.plain or rec.fn

        def draw(g: G, plain=plain, boxed=name in framed):
            plain(g)
            _stitch(g, cell, x_rows, cap_rows, thread, charter, boxed)

        out[name] = Recipe(name, draw, rec.unicode, rec.case, plain)
    return out


#: The flower at each corner of a frame, centered on the corner: (column, row, key) from its middle.
#: A rose of eight petals around a heart.
FLOWER = [(0, 0, "heart")] + [(dx, dy, "petal") for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def frame(cells: set, rows: tuple = (0, 9), bare: int = 2) -> tuple:
    """A letter in a stitched frame with a flower at each corner, as a sampler sets its initials.

    ``cells`` is the letter's chart and ``rows`` the rows it is centered on (the capitals). Around it
    are ``bare`` columns and rows of cloth, then a border of single stitches, whose corners each hold a
    small rose: a heart and eight petals, with two leaves inside the corner. The roses reach one
    square past the border. Returns (letter squares, {key: squares}, width in columns), with column 0
    the left edge of the roses.
    """
    lo, hi = min(i for i, _ in cells), max(i for i, _ in cells)
    b0, b1 = rows[0] - bare - 1, rows[1] + bare + 1                 # the rows of the border
    c0 = 1
    c1 = c0 + bare + (hi - lo + 1) + bare + 1                         # the columns of the border
    letter = {(i - lo + c0 + bare + 1, j) for i, j in cells}
    border = {(c, r) for c in range(c0, c1 + 1) for r in (b0, b1)} | {(c, r) for c in (c0, c1)
                                                                    for r in range(b0, b1 + 1)}
    motif: dict = {"border": set(), "petal": set(), "heart": set(), "leaf": set()}
    for cx, cy, sx, sy in ((c0, b0, 1, 1), (c1, b0, -1, 1), (c0, b1, 1, -1), (c1, b1, -1, -1)):
        for dx, dy, key in FLOWER:
            motif[key].add((cx + dx, cy + dy))
        # two leaves inside the corner, along the border
        motif["leaf"] |= {(cx + 2 * sx, cy + sy), (cx + sx, cy + 2 * sy)}
    taken = set().union(*motif.values())
    motif["border"] = border - taken
    return letter, motif, c1 + 2


def _stitch(g: G, cell: float, x_rows: int, cap_rows: int, thread: Thread, charter: Charter,
            boxed: bool = False):
    lsb, rsb, fixed = _natural(g)
    shape = effects.ink(g)
    mark = g._frame is not None and g._frame[0] == 0 and g._advance is None
    if not shape:
        # a space: keep its width, in whole squares
        width = fixed if fixed is not None else lsb + ((g._frame[0] or 0.0) if g._frame else 0.0) + rsb
        g._frame = (max(0, round(width / cell)) * cell, 0, 0)
        g._advance = None
        return
    motif: dict = {}
    if mark:
        cells, _ = charter.mark_chart(g, shape)      # a combining mark stays where it was drawn
        advance = 0
    elif boxed:
        cells, _ = charter.chart(g, g.name, shape)
        cells, motif, n = frame(cells, (0, cap_rows - 1))
        # one bare column on each side, so the flowers of two frames do not touch
        cells = {(i + 1, j) for i, j in cells}
        motif = {k: {(i + 1, j) for i, j in v} for k, v in motif.items()}
        advance = (n + 2) * cell
    else:
        cells, _ = charter.chart(g, g.name, shape)
        if not cells:
            return
        # The bare columns are counted beside the body of the letter (between the baseline and the
        # x-height, or the cap height), so a hook or a tail outside it may reach into them.
        top = x_rows if g.case == "lower" else cap_rows
        core = [i for i, j in cells if 0 <= j < top]
        if 2 * len(core) < len(cells):
            core = [i for i, j in cells]
        above = [i for i, j in cells if j >= 0] or [i for i, j in cells]
        below = [i for i, j in cells if j < 0]
        if fixed is not None:
            n = round(fixed / cell)
            shift = (n - (max(core) - min(core) + 1)) // 2 - min(core)
        else:
            ml, mr = _margin(lsb, cell), _margin(rsb, cell)
            shift = max(ml - min(core), -min(above), (-1 - min(below)) if below else -10 ** 6)
            n = max(max(core) + shift + 1 + mr, max(above) + shift + 1, (max(below) + shift) if below else 0)
        cells = {(i + shift, j) for i, j in cells}
        advance = n * cell
    unders: dict = {}
    tops: dict = {}
    for i, j in sorted(cells):
        x, y = i * cell, j * cell
        key = j % CYCLE
        unders.setdefault(f"u{key}", []).append(thread.under(x, y))
        tops.setdefault(f"t{key}", []).append(thread.top(x, y))
    for name in ("border", "leaf", "petal", "heart"):
        for i, j in sorted(motif.get(name, ())):
            unders.setdefault(f"{name}_u", []).append(thread.under(i * cell, j * cell))
            tops.setdefault(f"{name}_t", []).append(thread.top(i * cell, j * cell))
    g._frame = (advance, 0, 0)
    g._advance = None
    whole = union([c for cs in unders.values() for c in cs] + [c for cs in tops.values() for c in cs])
    effects.redraw(g, whole)
    order = lambda d: sorted(d, key=lambda k: (not k[1:].isdigit(), int(k[1:]) if k[1:].isdigit() else k))
    g.layers = [(k, unders[k]) for k in order(unders)] + [(k, tops[k]) for k in order(tops)]
    g.static_only = True


# --------------------------------------------------------------------------------------------- palettes


def palette(under, top, border=None, petal=None, heart=None, leaf=None) -> dict:
    """A palette: the under thread and the top thread, one color each or a list of ten, one per row
    (row 0 sits on the baseline; the list repeats every ten rows).

    ``border``, ``petal``, ``heart`` and ``leaf`` are (under, top) pairs for the frames of the
    initials; each one takes the letter's thread if it is not given.
    """
    unders = under if isinstance(under, (list, tuple)) else [under] * CYCLE
    tops = top if isinstance(top, (list, tuple)) else [top] * CYCLE
    out = {f"u{k}": unders[k] for k in range(CYCLE)}
    out.update({f"t{k}": tops[k] for k in range(CYCLE)})
    for name, pair in (("border", border), ("petal", petal), ("heart", heart), ("leaf", leaf)):
        u, t = pair or (unders[0], tops[0])
        out[f"{name}_u"], out[f"{name}_t"] = u, t
    return out


def banded(threads: list, rows, **motif) -> dict:
    """A palette that changes thread in bands of rows, from the baseline up: ``threads`` is a list of
    (under, top) pairs and ``rows`` the height of each band, in rows, adding up to ten (the cycle).
    A descender takes the bands at the top of the cycle (row -1 is row 9)."""
    unders, tops = [], []
    for (under, top), n in zip(threads, rows):
        unders += [under] * n
        tops += [top] * n
    if len(unders) != CYCLE:
        raise ValueError(f"the bands must add up to {CYCLE} rows")
    return palette(unders, tops, **motif)
