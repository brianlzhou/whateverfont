"""Proofs: pictures of the real font files, so the designer can look at the work.

Text is shaped with HarfBuzz (so kerning and variable axes apply) and drawn
with FreeType through Pillow. What a proof shows is what the font file does.
"""

from __future__ import annotations

from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from .geom import apply_affine, flatten_seg
from .outline import raster

INK = (24, 24, 27)
PAPER = (255, 255, 255)
MUTED = (150, 150, 156)

PANGRAM = "Sphinx of black quartz, judge my vow."
PARAGRAPH = (
    "A typeface is a set of decisions that repeat. The stem that holds up an n holds up "
    "an h, an m and a u; the curve that closes an o returns in c, e, d and q. When the "
    "decisions agree, a page of text settles into an even gray and the reader stops "
    "seeing letters at all. When they disagree, 27 pairs like AV, To and r. give it away."
)
SPACING = ["nnnonnoonnn HHHOHHOOHHH", "minimum illumination hillbilly", "AVATAR Type Wave Toy Yes LT, P. f) (j) “r.”",
           "1234567890 $42.50 (1967) 10:45 a@b.c"]
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
OTHER = "0123456789 .,:;!?‘’“”-–—()[]{}/&@#%$*+=<>"
CODE = "_|\\^~'\"`"
CYRILLIC = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ абвгдежзийклмнопрстуфхцчшщъыьэюя"
GREEK = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ αβγδεζηθικλμνξοπρσςτυφχψω"


def _fill(image: Image.Image, shapes: list, matrix, ink, ss: int = 3, alpha: float = 1.0):
    """Paint glyphs onto ``image``, rasterizing only the area they cover.

    ``shapes`` is a list of glyphs, each a list of contours that do not cross. Whether a contour
    is ink or a counter is decided by how many contours of its glyph contain it, not by its
    direction: fonts from other tools do not all wind the same way.
    """
    from .geom import flatten_contour, polygon_area
    polys = []                                    # (depth, area, points)
    for contours in shapes:
        flat = [[apply_affine(matrix, q) for q in flatten_contour(c, 0.3)] for c in contours]
        flat = [pts for pts in flat if len(pts) >= 3]
        boxes = [(min(q.real for q in pts), max(q.real for q in pts), min(q.imag for q in pts),
                  max(q.imag for q in pts)) for pts in flat]
        for i, pts in enumerate(flat):
            q = pts[0]
            depth = 0
            for j, other in enumerate(flat):
                if i == j or not (boxes[j][0] <= q.real <= boxes[j][1] and boxes[j][2] <= q.imag <= boxes[j][3]):
                    continue
                depth += _inside(other, q)
            polys.append((depth, abs(polygon_area(pts)), pts))
    if not polys:
        return
    xs = [q.real for _, _, pts in polys for q in pts]
    ys = [q.imag for _, _, pts in polys for q in pts]
    x0, y0 = max(0, int(min(xs)) - 2), max(0, int(min(ys)) - 2)
    x1, y1 = min(image.width, int(max(xs)) + 3), min(image.height, int(max(ys)) + 3)
    if x1 <= x0 or y1 <= y0:
        return
    w, h = x1 - x0, y1 - y0
    mask = Image.new("L", (w * ss, h * ss), 0)
    draw = ImageDraw.Draw(mask)
    for depth, _, pts in sorted(polys, key=lambda t: (t[0], -t[1])):
        draw.polygon([((q.real - x0) * ss, (q.imag - y0) * ss) for q in pts], fill=255 if depth % 2 == 0 else 0)
    mask = mask.resize((w, h), Image.LANCZOS)
    if alpha < 1.0:
        mask = mask.point(lambda v: int(v * alpha))
    image.paste(Image.new("RGB", (w, h), ink), (x0, y0), mask)


def rgb(value) -> tuple:
    """(r, g, b) from "#rrggbb"."""
    if isinstance(value, (tuple, list)):
        return tuple(int(v) for v in value[:3])
    h = value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ink_for(paper) -> tuple:
    """Dark ink on light paper, light ink on dark paper."""
    r, g, b = rgb(paper)
    return INK if 0.299 * r + 0.587 * g + 0.114 * b > 140 else (240, 238, 232)


def _luma(color) -> float:
    r, g, b = rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b


#: The ground a proof gets when a color of the palette would not show on the paper.
DARK_GROUND, LIGHT_GROUND = "#262A31", "#F4EFE6"


def ground_for(colors: list, paper=PAPER):
    """``paper``, or a contrasting ground if the paper would hide a large part of the palette.

    White snow on red letters is half of a palette of two, and it does not show on white paper. One
    cream among the fourteen colors of a bird does, because the other colors border it.
    """
    base = _luma(paper)
    hidden = [c for c in colors
              if abs(_luma(c) - base) < 24 and max(abs(a - b) for a, b in zip(c, rgb(paper))) < 40]
    if colors and len(hidden) * 3 >= len(colors):
        return DARK_GROUND if base > 140 else LIGHT_GROUND
    return paper


def _inside(poly: list, q: complex) -> bool:
    hit = False
    n = len(poly)
    x, y = q.real, q.imag
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.imag > y) != (b.imag > y) and x < a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag):
            hit = not hit
    return hit


class Renderer:
    """Draws text with one font file at one variable-axis location."""

    def __init__(self, font_path: str | Path, variations: dict | None = None, palette=None):
        """``palette`` picks the palette of a color font: its name, or its number from 0."""
        self.path = str(font_path)
        self.variations = dict(variations or {})
        tt = TTFont(self.path, lazy=True)
        self.upm = tt["head"].unitsPerEm
        self.axes = [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in tt["fvar"].axes] if "fvar" in tt else []
        self.has_color = "COLR" in tt and "CPAL" in tt
        self.ascent = tt["hhea"].ascent
        self.descent = tt["hhea"].descent
        self.cmap = set(tt.getBestCmap() or {})
        self.layers: dict = {}          # glyph id -> [(layer glyph id, (r, g, b), alpha) or (id, None, 1.0)]
        self.palettes: list = []
        self.colors: list = []          # the colors of the chosen palette
        if self.has_color:
            cpal = tt["CPAL"]
            labels = getattr(cpal, "paletteLabels", None) or []
            self.palettes = [(tt["name"].getDebugName(labels[i]) if i < len(labels) and labels[i] not in (None, 0xFFFF)
                              else f"Palette {i}") for i in range(len(cpal.palettes))]
            index = 0
            if isinstance(palette, int):
                index = palette
            elif palette:
                found = [i for i, n in enumerate(self.palettes) if n and n.lower() == str(palette).lower()]
                if not found:
                    raise ValueError(f"no palette named {palette!r}; this font has: {', '.join(self.palettes)}")
                index = found[0]
            if not 0 <= index < len(cpal.palettes):
                raise ValueError(f"palette {index} does not exist; this font has {len(cpal.palettes)}")
            colors = cpal.palettes[index]
            self.colors = [(c.red, c.green, c.blue) for c in colors if c.alpha > 96]
            ids = tt.getReverseGlyphMap()
            for base, records in tt["COLR"].ColorLayers.items():
                rows = []
                for rec in records:
                    if rec.colorID == 0xFFFF:
                        rows.append((ids[rec.name], None, 1.0))          # the text color
                    else:
                        c = colors[rec.colorID]
                        rows.append((ids[rec.name], (c.red, c.green, c.blue), c.alpha / 255))
                self.layers[ids[base]] = rows
        tt.close()
        self._face = hb.Face(hb.Blob.from_file_path(self.path))
        self._hb = hb.Font(self._face)
        if self.axes and self.variations:
            self._hb.set_variations(self.variations)
        self._pil: dict = {}
        self._outlines: dict = {}

    def _font(self, px: float):
        key = round(px, 2)
        if key not in self._pil:
            f = ImageFont.truetype(self.path, px, layout_engine=ImageFont.Layout.BASIC)
            if self.axes:
                f.set_variation_by_axes([max(lo, min(hi, self.variations.get(tag, d))) for tag, lo, d, hi in self.axes])
            self._pil[key] = f
        return self._pil[key]

    def shape(self, text: str, features: dict | None = None):
        """Glyph positions in font units: a list of (character, x)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hb, buf, features or {})
        out, x = [], 0
        # an empty line gives HarfBuzz nothing to shape: it returns None, not an empty list
        for info, pos in zip(buf.glyph_infos or [], buf.glyph_positions or []):
            out.append((text[info.cluster], x + pos.x_offset))
            x += pos.x_advance
        return out, x

    def glyph_run(self, text: str, features: dict | None = None):
        """What HarfBuzz chose: a list of (glyph id, character, x, y offset) in font units, and the advance."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hb, buf, features or {})
        out, x = [], 0
        for info, pos in zip(buf.glyph_infos or [], buf.glyph_positions or []):
            out.append((info.codepoint, text[info.cluster], x + pos.x_offset, pos.y_offset))
            x += pos.x_advance
        return out, x

    def outline(self, gid: int) -> list:
        """The outline of one glyph at this renderer's axis location, in font units."""
        from .outline import ContourPen
        pen = ContourPen()
        self._hb.draw_glyph_with_pen(gid, pen)
        pen._close()
        return pen.contours

    def width(self, text: str, px: float, tracking: float = 0.0) -> float:
        _, w = self.shape(text)
        return w * px / self.upm + tracking * px * len(text)

    def draw(self, image: Image.Image, x: float, baseline: float, text: str, px: float, ink=INK,
             tracking: float = 0.0, features: dict | None = None) -> float:
        """Draw one line. Returns the x where it ends."""
        from .outline import union
        s = px / self.upm
        run, total = self.glyph_run(text, features)
        if self.has_color:
            # Draw each color layer in the colors of the chosen palette, bottom layer first.
            from .geom import transform_contour
            for i, (gid, ch, gx, gy) in enumerate(run):
                dx = gx + tracking * self.upm * i
                move = lambda c, dx=dx, gy=gy: transform_contour(c, lambda q: q + complex(dx, gy))
                for layer, color, alpha in self.layers.get(gid, [(gid, None, 1.0)]):
                    outline = self._outlines.get(layer)
                    if outline is None:
                        outline = self._outlines[layer] = union(self.outline(layer))
                    if outline:
                        _fill(image, [[move(c) for c in outline]], (s, 0.0, 0.0, -s, x, baseline),
                              ink if color is None else color, alpha=alpha)
            return x + total * s + tracking * px * len(text)
        # Draw the glyphs HarfBuzz chose, where it put them: marks, ligatures and alternates show as they will.
        # A space is drawn too: in a picture font it can carry ink (a wire, a rule).
        from .geom import transform_contour
        shapes = []
        for i, (gid, ch, gx, gy) in enumerate(run):
            dx = gx + tracking * self.upm * i
            outline = self._outlines.get(gid)
            if outline is None:
                # Contours may overlap: in a variable font, and in a static one too (a composite glyph,
                # a font from another tool). Merged by non-zero winding, as renderers fill them, the
                # overlap is ink; the parity fill below would leave it blank.
                outline = union(self.outline(gid))
                self._outlines[gid] = outline
            if outline:
                shapes.append([transform_contour(c, lambda q, dx=dx, gy=gy: q + complex(dx, gy)) for c in outline])
        _fill(image, shapes, (s, 0.0, 0.0, -s, x, baseline), ink)
        return x + total * s + tracking * px * len(text)

    def wrap(self, text: str, px: float, max_width: float) -> list:
        lines, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if cur and self.width(trial, px) > max_width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines


def _label(image, x, y, text, scale):
    d = ImageDraw.Draw(image)
    d.text((x, y), text, fill=MUTED, font=ImageFont.load_default(size=13 * scale))


def sheet(font_path: str | Path, out: str | Path, variations: dict | None = None, title: str = "",
          sample: str = "", width: int = 1500, scale: int = 2, palette=None, paper=PAPER) -> Path:
    """The standard proof sheet for one font: character set, sizes, spacing, text."""
    r = Renderer(font_path, variations, palette)
    paper = rgb(paper)
    ink = ink_for(paper)
    W = width * scale
    margin = 56 * scale
    img = Image.new("RGB", (W, 2600 * scale), paper)
    y = margin
    # show only what the font has: a display font may leave out half of these
    have = lambda text: "".join(ch for ch in text if ch == " " or ord(ch) in r.cmap)
    draw_text = r.draw
    r.draw = lambda image, x, base, text, px, **kw: draw_text(image, x, base, have(text), px, ink=ink, **kw)

    def block(label, lines, px, gap=1.32):
        nonlocal y
        _label(img, margin, y, label, scale)
        y += 26 * scale
        for line in lines:
            line = have(line)
            if not line.strip():
                continue
            size = px * scale
            # shrink a line that would not fit
            w = r.width(line, size)
            if w > W - 2 * margin:
                size *= (W - 2 * margin) / w
            y += size * 0.95
            r.draw(img, margin, y, line, size)
            y += size * (gap - 0.95)
        y += 34 * scale

    block(title or Path(font_path).stem, [sample or PANGRAM], 92, 1.25)
    # a line of Cyrillic and one of Greek, if the font has them (``have`` drops the letters it lacks)
    scripts = [line for line in (CYRILLIC, GREEK) if sum(ord(ch) in r.cmap for ch in line) > len(line) // 2]
    block("Character set", [UPPER, LOWER, OTHER + " " + CODE] + scripts, 50)
    _label(img, margin, y, "Sizes", scale)
    y += 26 * scale
    gutter = 62 * scale                       # the size labels sit in their own column, clear of the text
    for px in (64, 44, 30, 22, 16, 13):
        y += px * scale * 1.0
        line, size = (sample or PANGRAM) + " 0123456789", px * scale
        w = r.width(line, size)
        if w > W - 2 * margin - gutter:
            size *= (W - 2 * margin - gutter) / w
        r.draw(img, margin + gutter, y, line, size)
        _label(img, margin, y - 12 * scale, f"{px}px", scale)
        y += px * scale * 0.38
    y += 34 * scale
    block("Spacing and kerning", SPACING, 40)
    _label(img, margin, y, "Text", scale)
    y += 26 * scale
    for px, cols in ((22, 0.62), (15, 0.5)):
        for line in r.wrap(PARAGRAPH, px * scale, (W - 2 * margin) * cols):
            y += px * scale * 1.5
            r.draw(img, margin, y, line, px * scale)
        y += 30 * scale
    img = img.crop((0, 0, W, int(y + margin)))
    img = img.resize((width, img.height // scale), Image.LANCZOS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def lines(font_path: str | Path, out: str | Path, texts: list, px: float = 96, variations: dict | None = None,
          width: int | None = None, scale: int = 2, labels: list | None = None, palette=None, paper=PAPER,
          bands: bool = True) -> Path:
    """A few lines of text at one size."""
    return compare([(font_path, variations or {}, lab) for lab in (labels or [""] * len(texts))], out, texts,
                   px, width, scale, per_row_text=True, palette=palette, paper=paper, bands=bands)


def compare(fonts: list, out: str | Path, text, px: float = 80, width: int | None = None, scale: int = 2,
            per_row_text: bool = False, palette=None, paper=PAPER, bands: bool = True) -> Path:
    """Rows of text in different fonts or axis locations.

    ``fonts`` is a list of (path, variations, label). ``text`` is one text for every row, or with
    ``per_row_text`` a list with one text per row. ``palette`` picks the palette of color fonts,
    and ``paper`` the background ("#rrggbb"); the ink follows the paper. A row whose palette the paper
    would hide gets a band of its own ground, unless ``bands`` is False.
    """
    paper = rgb(paper)
    ink = ink_for(paper)
    rows = []
    cache: dict = {}
    for i, (path, variations, label) in enumerate(fonts):
        key = (str(path), tuple(sorted((variations or {}).items())))
        if key not in cache:
            try:
                cache[key] = Renderer(path, variations, palette)
            except ValueError:
                cache[key] = Renderer(path, variations)        # this family has no palette of that name
        t = text[i] if per_row_text else text
        rows.append((cache[key], t, label))
    size = px * scale
    margin = 40 * scale
    need = max(r.width(t, size) for r, t, _ in rows) + 2 * margin
    W = int(width * scale if width else need)
    line_h = size * 1.45 + 20 * scale
    img = Image.new("RGB", (W, int(line_h * len(rows) + margin)), paper)
    y = margin * 0.6
    for r, t, label in rows:
        if label:
            _label(img, margin, y, label, scale)
        s = size
        w = r.width(t, s)
        if w > W - 2 * margin:
            s *= (W - 2 * margin) / w
        ground = rgb(ground_for(r.colors, paper)) if bands else paper
        if ground != paper:
            # this row's palette would not show on the paper (white snow on white): give the row its own band
            ImageDraw.Draw(img).rectangle([0, y + 20 * scale, W, y + line_h - 4 * scale], fill=ground)
        r.draw(img, margin, y + 22 * scale + size * 0.95, t, s, ink=ink_for(ground))
        y += line_h
    img = img.resize((W // scale, img.height // scale), Image.LANCZOS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


# --------------------------------------------------------------------------
# X-ray: outlines with the skeleton on top, straight from the recipes
# --------------------------------------------------------------------------

def xray(family, text: str, out: str | Path, location: dict | None = None, px: float = 420, scale: int = 2) -> Path:
    """Large glyphs with skeleton, nodes and metric lines. For debugging recipes."""
    p = family.params_at(location)
    by_char = {chr(rec.unicode): name for name, rec in family.recipes.items() if rec.unicode}
    names = [by_char.get(ch, ch) for ch in text if by_char.get(ch, ch) in family.recipes]
    glyphs = [family.recipes.draw(n, p) for n in names]
    s = px * scale / p.upm
    margin = 50 * scale
    total = sum(g.advance for g in glyphs) * s
    H_ = int((p.asc - p.desc + 160) * s + 2 * margin)
    W_ = int(total + 2 * margin)
    img = Image.new("RGB", (W_, H_), PAPER)
    d = ImageDraw.Draw(img)
    base = margin + (p.asc + 80) * s
    for yv, name in ((0, "baseline"), (p.xh, "x-height"), (p.cap, "cap"), (p.asc, "ascender"), (p.desc, "descender")):
        yy = base - yv * s
        d.line([(0, yy), (W_, yy)], fill=(214, 222, 235), width=scale)
        d.text((6 * scale, yy - 16 * scale), f"{name} {yv:g}", fill=MUTED, font=ImageFont.load_default(size=11 * scale))
    x = float(margin)
    for g in glyphs:
        m = (s, 0, 0, -s, x, base)
        raster(g.contours, m, img.size, ink=(205, 208, 214), image=img, ss=2)
        d = ImageDraw.Draw(img)
        for st in g.strokes:
            for seg in st.segments():
                pts = [seg[0]] + flatten_seg(seg, 0.5)
                d.line([(apply_affine(m, q).real, apply_affine(m, q).imag) for q in pts], fill=(214, 60, 48), width=scale)
            for nd in st.nodes:
                q = apply_affine(m, nd.p)
                rr = 3 * scale
                d.ellipse([q.real - rr, q.imag - rr, q.real + rr, q.imag + rr], fill=(36, 92, 220))
        for xv in (0, g.advance):
            d.line([(x + xv * s, margin), (x + xv * s, H_ - margin)], fill=(236, 200, 120), width=scale)
        d.text((x + 4 * scale, H_ - margin + 4 * scale), f"{g.name}  adv {g.advance:g}", fill=MUTED,
               font=ImageFont.load_default(size=11 * scale))
        x += g.advance * s
    img = img.resize((W_ // scale, H_ // scale), Image.LANCZOS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
