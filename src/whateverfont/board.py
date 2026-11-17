"""The review board: one HTML page where a person compares directions,
moves the axes, and sends feedback back to the designer.

The page is self-contained (fonts are embedded), so it opens from disk and can
be sent to someone else. With ``whateverfont board --serve`` the Send button writes
``feedback.json`` into the project; without a server the person copies the
feedback and pastes it into the conversation.
"""

from __future__ import annotations

import base64
import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HTTPServer.allow_reuse_address = False
from pathlib import Path

from .compile import slug

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
__FACES__
:root {
  --paper: #ffffff; --ink: #18181b; --muted: #71717a; --panel: #f4f4f5; --panel-ink: #3f3f46;
  --accent: #c2410c; --pick: #18181b; --pick-ink: #ffffff;
  --ui: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #111113; --ink: #f4f4f5; --muted: #a1a1aa; --panel: #1f1f23; --panel-ink: #d4d4d8;
  --accent: #fb923c; --pick: #f4f4f5; --pick-ink: #111113; } }
:root[data-theme="dark"] {
  --paper: #111113; --ink: #f4f4f5; --muted: #a1a1aa; --panel: #1f1f23; --panel-ink: #d4d4d8;
  --accent: #fb923c; --pick: #f4f4f5; --pick-ink: #111113; }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; overflow-anchor: none; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 15px/1.5 var(--ui); }
main { max-width: 1180px; margin: 0 auto; padding: 40px 24px 120px; }
h1 { font: 600 22px/1.3 var(--ui); margin: 0 0 6px; }
.brief { color: var(--muted); max-width: 68ch; margin: 0 0 28px; white-space: pre-line; }
.controls { position: sticky; top: 12px; z-index: 5; background: var(--panel); color: var(--panel-ink);
  border-radius: 14px; padding: 14px 16px; display: flex; flex-wrap: wrap; gap: 12px 22px; align-items: center; }
.controls input[type=text] { flex: 1 1 320px; min-width: 200px; font: 15px var(--ui); padding: 9px 12px; border: 0;
  border-radius: 9px; background: var(--paper); color: var(--ink); }
.controls label, .axes label { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
input[type=range] { accent-color: var(--ink); width: 130px; }
.num { font-variant-numeric: tabular-nums; min-width: 3.2ch; text-align: right; color: var(--muted); }
.seg { display: flex; background: var(--paper); border-radius: 9px; padding: 3px; }
.seg button { font: 14px var(--ui); border: 0; background: none; color: var(--panel-ink); padding: 6px 11px;
  border-radius: 7px; cursor: pointer; }
.seg button[aria-pressed=true] { background: var(--ink); color: var(--paper); }
section.dir { padding: 56px 0 8px; }
.head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 18px; margin-bottom: 4px; }
.head h2 { font: 600 17px/1.3 var(--ui); margin: 0; }
.head p { margin: 0; color: var(--muted); max-width: 70ch; }
.stage { margin: 18px 0 14px; overflow-wrap: anywhere; outline: none; }
.stage.text { max-width: 62ch; }
.stage.glyphs { display: grid; grid-template-columns: repeat(auto-fill, minmax(64px, 1fr)); gap: 4px; }
.stage.glyphs span { text-align: center; font-size: 40px; line-height: 1.5; background: var(--panel); border-radius: 8px; }
.stage.sizes div { white-space: nowrap; overflow: hidden; text-overflow: clip; }
.axes { background: var(--panel); color: var(--panel-ink); border-radius: 14px; padding: 12px 16px; display: flex;
  flex-wrap: wrap; gap: 10px 22px; align-items: center; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips button, .act button { font: 14px var(--ui); border: 0; border-radius: 999px; padding: 6px 12px; cursor: pointer;
  background: var(--paper); color: var(--panel-ink); }
.chips button[aria-pressed=true] { background: var(--ink); color: var(--paper); }
.act { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 12px; }
.act button.pick { background: var(--panel); padding: 9px 16px; }
.act button.pick[aria-pressed=true] { background: var(--pick); color: var(--pick-ink); }
.act input { flex: 1 1 280px; font: 15px var(--ui); padding: 9px 12px; border: 0; border-radius: 9px;
  background: var(--panel); color: var(--ink); }
.send { margin-top: 72px; background: var(--panel); border-radius: 14px; padding: 18px; }
.send h2 { font: 600 17px/1.3 var(--ui); margin: 0 0 4px; }
.send p { margin: 0 0 12px; color: var(--muted); }
.send textarea { width: 100%; min-height: 70px; font: 15px var(--ui); padding: 10px 12px; border: 0; border-radius: 9px;
  background: var(--paper); color: var(--ink); resize: vertical; }
.send .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 12px; }
.send button { font: 600 15px var(--ui); border: 0; border-radius: 999px; padding: 10px 18px; cursor: pointer;
  background: var(--ink); color: var(--paper); }
.send button.quiet { background: var(--paper); color: var(--panel-ink); font-weight: 400; }
.send output { color: var(--accent); }
pre { font: 12px/1.5 ui-monospace, Menlo, monospace; color: var(--muted); white-space: pre-wrap; margin: 12px 0 0; display: none; }
pre.show { display: block; }
@media (max-width: 640px) { main { padding: 24px 16px 96px; } .controls { position: static; } }
</style>
</head>
<body>
<main>
  <h1>__TITLE__</h1>
  <p class="brief">__BRIEF__</p>
  <div class="controls">
    <input id="sample" type="text" aria-label="Sample text" placeholder="Type your own text">
    <div class="seg" id="views" role="group" aria-label="View"></div>
    <label>Size <input id="size" type="range" min="14" max="220" value="84"><span class="num" id="sizeN"></span></label>
    <label>Spacing <input id="track" type="range" min="-60" max="200" value="0"><span class="num" id="trackN"></span></label>
    <label>Leading <input id="lead" type="range" min="90" max="200" value="120"><span class="num" id="leadN"></span></label>
    <div class="seg" id="theme" role="group" aria-label="Theme"></div>
  </div>
  <div id="dirs"></div>
  <div class="send">
    <h2>Send feedback</h2>
    <p>Your picks, slider settings and notes go back to the agent, which then revises the fonts.</p>
    <textarea id="general" placeholder="Anything else? For example: make the capitals wider, I want a heavier bold, try a rounder g."></textarea>
    <div class="row">
      <button id="send">__SEND_LABEL__</button>
      <button class="quiet" id="download">Download feedback.json</button>
      <output id="status"></output>
    </div>
    <pre id="json"></pre>
  </div>
</main>
<script>
const DATA = __DATA__;
const PARA = "A typeface is a set of decisions that repeat. The stem that holds up an n holds up an h, an m and a u; the curve that closes an o returns in c, e, d and q. When the decisions agree, a page of text settles into an even gray and the reader stops seeing letters at all. On 14 March 2027, 86 people read this paragraph and nobody noticed the font.";
const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;!?‘’“”-–—()[]{}/&@#%$*+=";
const $ = (id) => document.getElementById(id);
const state = { view: "Headline", picked: {}, notes: {}, axes: {}, style: {}, palette: {} };
const el = (tag, attrs = {}, kids = []) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) { if (k === "text") n.textContent = v; else if (k === "on") for (const [e, f] of Object.entries(v)) n.addEventListener(e, f); else n.setAttribute(k, v); }
  for (const k of [].concat(kids)) n.append(k);
  return n;
};
function seg(host, names, get, set) {
  host.replaceChildren(...names.map((name) => el("button", { text: name, "aria-pressed": String(get() === name), on: { click: () => { set(name); seg(host, names, get, set); render(); } } })));
}
function variation(d) {
  const a = state.axes[d.id] || {};
  return d.axes.map((x) => `"${x.tag}" ${a[x.tag] ?? x.def}`).join(", ");
}
function stageFor(d) {
  const size = +$("size").value, track = +$("track").value / 1000, lead = +$("lead").value / 100;
  const text = $("sample").value || DATA.sample;
  const pal = d.palettes.length ? ` font-palette: --${d.face}-${state.palette[d.id] || 0};` : "";
  const base = `font-family: "${d.face}"; font-variation-settings: ${variation(d) || "normal"}; letter-spacing: ${track}em;${pal}`;
  if (state.view === "Text") return el("div", { class: "stage text", style: `${base} font-size: ${Math.min(size, 28)}px; line-height: ${Math.max(lead, 1.35)};`, text: text + " " + PARA });
  if (state.view === "Glyphs") return el("div", { class: "stage glyphs", style: base }, [...GLYPHS].map((c) => el("span", { text: c })));
  if (state.view === "Sizes") return el("div", { class: "stage sizes", style: base }, [96, 64, 44, 30, 22, 16, 13].map((s) => el("div", { style: `font-size:${s}px; line-height:1.3`, text })));
  return el("div", { class: "stage", contenteditable: "true", spellcheck: "false", style: `${base} font-size: ${size}px; line-height: ${lead};`, text });
}
function renderDir(d) {
  const sec = el("section", { class: "dir", id: "dir-" + d.id });
  sec.append(el("div", { class: "head" }, [el("h2", { text: d.name }), el("p", { text: d.note })]));
  sec.append(stageFor(d));
  if (d.axes.length) {
    const box = el("div", { class: "axes" });
    for (const x of d.axes) {
      const cur = (state.axes[d.id] || {})[x.tag] ?? x.def;
      const num = el("span", { class: "num", text: String(Math.round(cur)) });
      const input = el("input", { type: "range", min: x.min, max: x.max, step: (x.max - x.min) / 200, value: cur, "aria-label": x.name, on: { input: (e) => {
        (state.axes[d.id] ||= {})[x.tag] = +e.target.value; state.style[d.id] = null; num.textContent = Math.round(+e.target.value);
        sec.querySelector(".stage").style.fontVariationSettings = variation(d); summary(); } } });
      box.append(el("label", {}, [x.name, input, num]));
    }
    const chips = el("div", { class: "chips" });
    for (const [name, loc] of Object.entries(d.styles)) chips.append(el("button", { text: name, on: { click: () => {
      state.axes[d.id] = Object.fromEntries(d.axes.map((x) => [x.tag, loc[x.tag] ?? x.def])); state.style[d.id] = name; render(); } } }));
    box.append(chips);
    sec.append(box);
  }
  if (d.palettes.length) {
    const box = el("div", { class: "axes" }, ["Palette"]);
    const chips = el("div", { class: "chips" });
    d.palettes.forEach((name, k) => chips.append(el("button", { text: name, "aria-pressed": String((state.palette[d.id] || 0) === k), on: { click: () => { state.palette[d.id] = k; render(); } } })));
    box.append(chips);
    sec.append(box);
  }
  const act = el("div", { class: "act" });
  act.append(el("button", { class: "pick", "aria-pressed": String(!!state.picked[d.id]), text: state.picked[d.id] ? "Picked" : "Pick this one", on: { click: () => { state.picked[d.id] = !state.picked[d.id]; render(); } } }));
  act.append(el("input", { type: "text", placeholder: `Notes on ${d.name}`, value: state.notes[d.id] || "", on: { input: (e) => { state.notes[d.id] = e.target.value; summary(); } } }));
  sec.append(act);
  return sec;
}
function feedback() {
  return { project: DATA.title, sample: $("sample").value || DATA.sample,
    picked: DATA.directions.filter((d) => state.picked[d.id]).map((d) => d.name),
    directions: Object.fromEntries(DATA.directions.map((d) => [d.name, { picked: !!state.picked[d.id], notes: state.notes[d.id] || "", axes: state.axes[d.id] || {}, style: state.style[d.id] || null, palette: d.palettes[state.palette[d.id] || 0] || null }])),
    view: { size: +$("size").value, tracking: +$("track").value, leading: +$("lead").value },
    general: $("general").value, time: new Date().toISOString() };
}
function summary() { $("json").textContent = JSON.stringify(feedback(), null, 2); }
// A change of text or size changes the height of every direction. The one at the top of the view
// stays where it is, so the page does not jump under the reader.
let pin = null;
function steady(change) {
  const bar = document.querySelector(".controls");
  // "at the top" is just under the bar: the direction that crosses that line, or the first one below it
  const line = (bar ? bar.getBoundingClientRect().bottom : 0) + 48;
  // While the reader does not scroll, the same direction stays at the same place, so key presses add no creep.
  if (pin && Math.abs(scrollY - pin.y) > 2) pin = null;
  if (!pin) {
    const at = [...document.querySelectorAll(".dir")].find((s) => s.getBoundingClientRect().bottom > line);
    pin = at ? { id: at.id, top: at.getBoundingClientRect().top, y: scrollY } : null;
  }
  change();
  const now = pin && document.getElementById(pin.id);
  if (!now) return;
  const moved = now.getBoundingClientRect().top - pin.top;
  if (Math.abs(moved) >= 0.5) scrollBy({ top: moved, behavior: "instant" });
  pin.y = scrollY;
}
function render() {
  $("sizeN").textContent = $("size").value; $("trackN").textContent = $("track").value; $("leadN").textContent = (+$("lead").value / 100).toFixed(2);
  const keep = document.activeElement && document.activeElement.id;
  steady(() => $("dirs").replaceChildren(...DATA.directions.map(renderDir)));
  if (keep && $(keep)) $(keep).focus({ preventScroll: true });
  summary();
}
seg($("views"), ["Headline", "Text", "Sizes", "Glyphs"], () => state.view, (v) => { state.view = v; });
const themes = ["Auto", "Light", "Dark"]; let theme = "Auto";
seg($("theme"), themes, () => theme, (v) => { theme = v; if (v === "Auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", v.toLowerCase()); });
for (const id of ["sample", "size", "track", "lead"]) $(id).addEventListener("input", () => { if (id === "sample") { steady(() => document.querySelectorAll(".stage:not(.glyphs):not(.sizes):not(.text)").forEach((s) => {
      // a stage never gets shorter than it was, so a short word moves nothing below it
      if (!s.style.minHeight) s.style.minHeight = s.getBoundingClientRect().height + "px";
      s.textContent = $("sample").value || DATA.sample; })); summary(); } else render(); });
$("general").addEventListener("input", summary);
$("sample").value = DATA.sample;
$("download").addEventListener("click", () => { const a = el("a", { href: URL.createObjectURL(new Blob([JSON.stringify(feedback(), null, 2)], { type: "application/json" })), download: "feedback.json" }); a.click(); });
$("send").addEventListener("click", async () => {
  const body = JSON.stringify(feedback(), null, 2);
  if (DATA.served) { try { const r = await fetch("feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body }); $("status").textContent = r.ok ? "Sent. The agent can read feedback.json now." : "The server refused it."; return; } catch (e) { /* fall through to copy */ } }
  try { await navigator.clipboard.writeText(body); $("status").textContent = "Copied. Paste it into the conversation with your agent."; }
  catch (e) { $("json").classList.add("show"); $("status").textContent = "Select the text below and copy it."; }
});
render();
</script>
</body>
</html>
"""


def _face(css_name: str, path: Path, weight: str = "") -> str:
    data = base64.b64encode(Path(path).read_bytes()).decode()
    extra = f" font-weight: {weight};" if weight else ""
    return (f'@font-face {{ font-family: "{css_name}"; src: url(data:font/woff2;base64,{data}) format("woff2");'
            f'{extra} font-display: block; }}')


def build_board(project, results: dict, out: Path | None = None, served: bool = False) -> Path:
    """Write ``board.html`` for a built project."""
    faces, dirs = [], []
    for i, fam in enumerate(project.families):
        res = results.get(fam.name)
        if res is None:
            continue
        face = f"ff-{i}-{slug(fam.name)}"
        out_dir = project.out_dir(fam)
        if res.variable is not None:
            faces.append(_face(face, res.variable.with_suffix(".woff2")))
            axes = [dict(tag=a.tag, name=a.name, min=a.minimum, max=a.maximum, **{"def": a.default}) for a in fam.axes]
        else:
            first = next(iter(res.statics.values()))
            faces.append(_face(face, out_dir / "woff2" / (first.stem + ".woff2")))
            axes = []
        for k in range(len(fam.palettes)):
            faces.append(f'@font-palette-values --{face}-{k} {{ font-family: "{face}"; base-palette: {k}; }}')
        dirs.append(dict(id=f"d{i}", name=fam.name, note=fam.description, face=face, axes=axes,
                         styles={k: v for k, v in fam.styles.items()} if axes else {},
                         palettes=list(fam.palettes)))
    sample = next((f.sample for f in project.families if f.sample), "") or "Sphinx of black quartz, judge my vow."
    title = (project.family.name if len(dirs) < 2
             else f"{project.family.name}: {len(dirs)} directions")
    brief = _brief_text(project.brief)
    data = dict(title=title, sample=sample, directions=dirs, served=served)
    page = (PAGE.replace("__FACES__", "\n".join(faces))
            .replace("__TITLE__", html.escape(title))
            .replace("__BRIEF__", html.escape(brief))
            .replace("__SEND_LABEL__", "Send to the agent" if served else "Copy feedback")
            .replace("__DATA__", json.dumps(data).replace("</", "<\\/")))
    out = out or (project.path / "board.html")
    out.write_text(page)
    return out


def _brief_text(brief_md: str) -> str:
    """The text under '## Brief' in BRIEF.md, or nothing."""
    lines, on = [], False
    for line in brief_md.splitlines():
        if line.startswith("## "):
            on = line.strip().lower() == "## brief"
            continue
        if on:
            lines.append(line.strip())
    # join wrapped lines; keep blank lines as paragraph breaks
    paragraphs = [" ".join(part.split()) for part in "\n".join(lines).split("\n\n")]
    return "\n\n".join(p for p in paragraphs if p)


def serve(project, results: dict, port: int = 8765):
    """Serve the board and write the feedback it sends into the project folder."""
    page = build_board(project, results, served=True)
    target = project.path / "feedback.json"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = page.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(min(n, 1_000_000))
            try:
                data = json.loads(raw)
            except ValueError:
                self.send_response(400)
                self.end_headers()
                return
            target.write_text(json.dumps(data, indent=2))
            print(f"feedback written to {target}", flush=True)
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = None
    for candidate in range(port, port + 30):
        try:
            server = HTTPServer(("127.0.0.1", candidate), Handler)
            port = candidate
            break
        except OSError:
            continue    # the port belongs to something else; leave it alone
    if server is None:
        raise OSError(f"no free port between {port} and {port + 29}")
    print(f"Review board: http://127.0.0.1:{port}/  (Ctrl-C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
