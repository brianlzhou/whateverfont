// The project site: shared sample text and size, axis sliders, palettes, and the character table.
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;
  const relayout = [];      // what must measure again after the words of the page change
  const lingo = { code: "en", words: null, way: "ltr" };      // the language of the page, and its texts

  // Sticky parts sit under the header, whatever its height.
  const top = $(".top");
  const setTop = () => root.style.setProperty("--top", `${top.offsetHeight}px`);
  setTop();
  addEventListener("resize", setTop);

  // A change of text or size changes the height of every sample, and without care the page
  // jumps under the reader. Two things keep it still:
  // 1. A sample is never shorter than its own text made it, so a short word moves nothing.
  // 2. The font at the top of the view stays where it is when the fonts above it change height.
  const samples = $$(".sample");
  const specs = $$(".spec");
  const tester = $(".tester");
  const lock = () => {
    for (const s of samples) {
      if (s.textContent !== s.dataset.default) continue;       // measure a sample with its own text only
      s.style.minHeight = "";
      const em = parseFloat(getComputedStyle(s).fontSize);
      s.style.minHeight = `${(s.getBoundingClientRect().height / em).toFixed(3)}em`;
    }
  };
  let pin = null;      // the font that stays, where it stays, and the scroll position this script left
  const steady = (change) => {
    // "at the top" is just under the sticky bars: the font that crosses that line, or the first one below it
    const line = top.offsetHeight + (tester ? tester.offsetHeight : 0) + 48;
    // While the reader does not scroll, the same font stays at the same place. Measuring again at every
    // key press would add a rounding error each time, and the page would creep.
    if (pin && Math.abs(scrollY - pin.y) > 2) pin = null;
    if (!pin) {
      const anchor = specs.find((s) => s.getBoundingClientRect().bottom > line);
      pin = anchor ? { anchor, top: anchor.getBoundingClientRect().top, y: scrollY } : null;
    }
    change();
    if (!pin) return;
    const moved = pin.anchor.getBoundingClientRect().top - pin.top;
    if (Math.abs(moved) >= 0.5) scrollBy({ top: moved, behavior: "instant" });
    pin.y = scrollY;
  };
  lock();
  document.fonts.ready.then(lock);
  addEventListener("resize", () => steady(lock));

  // One text box sets every sample.
  // (Only a page that shows samples has these controls.)
  const text = $("#text");
  if (text) {
    text.addEventListener("input", () => {
      steady(() => { for (const s of samples) s.textContent = text.value || s.dataset.default; });
    });
  }

  // One size for every sample.
  const size = $("#size");
  const sizeOut = $("#size-out");
  if (size) {
    size.addEventListener("input", () => {
      steady(() => { root.style.setProperty("--sample", `${size.value}px`); lock(); });
      sizeOut.value = size.value;
    });
  }

  // Axis sliders and palettes, per font.
  const applyAxes = (spec) => {
    const sample = $(".sample", spec);
    const inputs = $$("input[data-tag]", spec);
    sample.style.fontVariationSettings = inputs.map((i) => `"${i.dataset.tag}" ${i.value}`).join(", ");
    for (const i of inputs) i.nextElementSibling.value = i.value;
  };
  for (const spec of $$(".spec")) {
    for (const i of $$("input[data-tag]", spec)) i.addEventListener("input", () => applyAxes(spec));
    const chips = $$("[data-palette]", spec);
    for (const b of chips) {
      b.addEventListener("click", () => {
        const sample = $(".sample", spec);
        sample.style.fontPalette = b.dataset.palette;
        sample.style.background = b.dataset.ground || "";
        sample.style.color = b.dataset.ink || "";
        for (const c of chips) c.setAttribute("aria-pressed", String(c === b));
      });
    }
  }

  if ($("#reset")) $("#reset").addEventListener("click", () => steady(() => {
    text.value = "";
    size.value = 64;
    sizeOut.value = 64;
    root.style.removeProperty("--sample");
    for (const spec of $$(".spec")) {
      const sample = $(".sample", spec);
      sample.textContent = sample.dataset.default;
      for (const i of $$("input[data-tag]", spec)) i.value = i.dataset.default;
      if ($("input[data-tag]", spec)) applyAxes(spec);
      const chips = $$("[data-palette]", spec);
      if (chips.length) {
        sample.style.fontPalette = chips[0].dataset.palette;
        sample.style.background = chips[0].dataset.ground || "";
        sample.style.color = chips[0].dataset.ink || "";
        chips.forEach((c, k) => c.setAttribute("aria-pressed", String(k === 0)));
      }
    }
    lock();
  }));

  // The poster: the same words in one font after another, each with the request that made the font.
  const poster = $("#poster");
  if (poster) {
    const slides = JSON.parse($("#hero-data").textContent);
    const words = $("#poster-text"), ask = $("#poster-ask"), name = $("#poster-name"), by = $("#poster-by");
    const foot = name.parentElement;              // the font's name and the person who made it, at the foot
    const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    // The poster's words follow the language where the font of the slide has the letters. So does the request.
    const english = words.innerHTML;
    const can = (s) => Boolean(lingo.words && lingo.words["poster.text"] && (s.langs || []).includes(lingo.code));
    const line = (s) => (can(s) ? lingo.words["poster.text"] : english);
    const asked = (s) => (lingo.words && lingo.words[s.askKey]) || s.ask;
    const dress = (s) => {
      words.innerHTML = line(s);
      words.lang = can(s) ? lingo.code : "en";
      words.dir = can(s) ? lingo.way : "ltr";
    };
    // a slide's font for the script of the page's language has its own name: "ff-last-bell-snow-ja"
    const part = (s) => (can(s) && s.parts && s.parts[lingo.code]) || "";
    const family = (s) => `"${s.face}", ${part(s) ? `"${part(s)}", ` : ""}var(--fallback)`;
    const ready = (s) => {
      const text = line(s).replace(/<[^>]+>/g, " ");
      const wanted = [document.fonts.load(`100px "${s.face}"`, text)];
      if (part(s)) wanted.push(document.fonts.load(`100px "${part(s)}"`, text));
      return Promise.all(wanted).catch(() => {});
    };
    // In a language that only some of these fonts can set, the poster shows those fonts only.
    const fits = () => {
      const able = slides.map((s, k) => k).filter((k) => can(slides[k]));
      return able.length ? able : slides.map((s, k) => k);
    };
    const next = () => {
      const able = fits();
      return able.find((k) => k > at) ?? able[0];
    };
    let at = 0, run = 0, paused = false, seen = true, timer = 0;
    const fit = () => {
      // the words fill the poster the same way in every font
      words.style.fontSize = "100px";
      const box = poster.getBoundingClientRect(), r = words.getBoundingClientRect();
      if (r.width) words.style.fontSize = `${(100 * Math.min((box.width * 0.86) / r.width, (box.height * 0.58) / r.height)).toFixed(1)}px`;
    };
    const show = async (k) => {
      const mine = ++run, s = slides[k];
      at = k;
      const loaded = ready(s);
      words.classList.add("out");
      foot.style.opacity = 0;
      await wait(calm ? 0 : 200);
      if (mine !== run) return;
      poster.style.background = s.ground;
      poster.style.color = s.ink;
      // the request types itself, and then the words land in the font it made
      poster.classList.add("typing");
      const request = asked(s);
      if (calm) ask.textContent = request;
      else for (let n = 1; n <= request.length; n++) { ask.textContent = request.slice(0, n); await wait(15); if (mine !== run) return; }
      await loaded;
      if (mine !== run) return;
      poster.classList.remove("typing");
      dress(s);
      words.style.fontFamily = family(s);
      words.style.fontPalette = s.palette || "normal";
      words.style.fontVariationSettings = s.fvs || "normal";
      name.textContent = s.name;
      if (by) by.textContent = s.by || "";
      fit();
      words.classList.remove("out");
      foot.style.opacity = "";
    };
    const tick = () => {
      clearTimeout(timer);
      if (calm) return;
      timer = setTimeout(() => { if (!paused && seen && !document.hidden) show(next()); tick(); }, 4400);
    };
    // The poster leaves room in the window for the text and the buttons under it. Their height changes with
    // the width of the window and with the language, so it is measured (see --foot in style.css).
    const under = $(".hero-foot");
    const room = () => {
      if (!under) return;
      const tall = `${Math.ceil(under.getBoundingClientRect().height)}px`;
      if (poster.parentElement.style.getPropertyValue("--foot") === tall) return;
      poster.parentElement.style.setProperty("--foot", tall);
      fit();
    };
    room();
    document.fonts.ready.then(room);
    addEventListener("resize", room);
    relayout.push(room);
    poster.addEventListener("click", () => { show(next()); tick(); });
    poster.addEventListener("pointerenter", () => { paused = true; });
    poster.addEventListener("pointerleave", () => { paused = false; });
    new IntersectionObserver(([e]) => { seen = e.isIntersecting; }).observe(poster);
    addEventListener("resize", fit);
    // a new language: the slide in view takes its words and its request, and is measured again
    relayout.push(() => {
      if (!fits().includes(at)) { show(fits()[0]); tick(); return; }
      const s = slides[at];
      ready(s).then(() => { dress(s); words.style.fontFamily = family(s); ask.textContent = asked(s); fit(); });
    });
    ready(slides[0]).then(() => { fit(); words.classList.remove("out"); });
    slides.slice(1, 3).forEach(ready);          // the next two are on their way before they are due
    tick();
  }

  // The conversation: press a request, and the same letters answer.
  // A word in another language can be longer than the English one. The words of the wall and the lines of
  // the demo are made smaller until they fit their box.
  // A line of several words (the sample of a wide tile, the reader's own text) may wrap, so it has a height
  // to fit too: the largest size at which it fits is found by halving.
  const fitWord = (word) => {
    const tile = word.parentElement;
    const room = tile.clientWidth * 0.84;
    word.style.setProperty("--fit", 1);
    if (getComputedStyle(word).whiteSpace === "nowrap") {
      const wide = word.getBoundingClientRect().width;
      if (wide > room) word.style.setProperty("--fit", (room / wide).toFixed(3));
      return;
    }
    const tall = tile.clientHeight * 0.6;
    const fits = (k) => {
      word.style.setProperty("--fit", k);
      return word.scrollWidth <= Math.ceil(room) + 1 && word.getBoundingClientRect().height <= tall;
    };
    if (fits(1)) return;
    let small = 0.08, large = 1;
    for (let n = 0; n < 7; n++) {
      const k = (small + large) / 2;
      if (fits(k)) small = k; else large = k;
    }
    word.style.setProperty("--fit", small.toFixed(3));
  };
  const snug = () => {
    $$(".tile-word").forEach(fitWord);
    const box = $("#talk-stage");
    if (box) {
      box.style.setProperty("--fit", 1);
      const sets = $$(".talk-words", box);
      const left = sets.length ? sets[0].offsetLeft : 0;
      const room = box.clientWidth - 2 * left, wide = Math.max(...sets.map((s) => s.scrollWidth), 1);
      if (wide > room) box.style.setProperty("--fit", (room / wide).toFixed(3));
    }
  };
  // The wall's text box: the reader's own text, set in every font. An empty box gives each tile its word back.
  const wallText = $("#wall-text"), wall = $("#wall");
  if (wallText && wall) {
    const words = $$(".tile-word", wall);
    const set = () => {
      const typed = wallText.value.trim() ? wallText.value : "";
      wall.classList.toggle("typed", Boolean(typed));
      for (const word of words) {
        if (typed) {
          word.textContent = typed;
          word.removeAttribute("lang");
          word.dir = "auto";
          continue;
        }
        // the tile's own word, in the page's language where the font has the letters
        const can = (word.dataset.langs || "").split(" ").includes(lingo.code);
        word.innerHTML = (can && lingo.words && lingo.words[word.dataset.fontText]) || word.dataset.english;
        word.lang = can ? lingo.code : "en";
        word.dir = can ? lingo.way : "ltr";
      }
      words.forEach(fitWord);
    };
    wallText.addEventListener("input", set);
    relayout.push(() => { if (wall.classList.contains("typed")) set(); });      // a new language keeps the reader's text
    if (wallText.value) set();          // a browser may bring the text back with the page
  }
  relayout.push(() => document.fonts.ready.then(snug));
  addEventListener("resize", snug);
  document.fonts.ready.then(snug);
  // A letter outside a font's first file brings the rest of the font, and the words are measured again.
  let again = 0;
  document.fonts.addEventListener("loadingdone", () => { cancelAnimationFrame(again); again = requestAnimationFrame(snug); });

  // The live numbers under "How it works": each slider is an axis of one font, and its row shows the number
  // of the engine that the axis moves.
  const dials = $("#dials");
  if (dials) {
    const line = $("#dials-line"), stage = line.parentElement, back = $("#dials-reset");
    const sliders = $$("input[data-tag]", dials);
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    // a slider that the build turned over (slant) gives the font its value with the axis' own sign
    const axis = (i, v) => `"${i.dataset.tag}" ${(("turned" in i.dataset ? -1 : 1) * Number(v)).toFixed(2)}`;
    const rest = sliders.map((i) => axis(i, i.dataset.default)).join(", ");
    const number = (i) => {
      const [low, mid, high] = i.dataset.ends.split(" ").map(Number);
      const v = Number(i.value), a = Number(i.min), b = Number(i.dataset.default), c = Number(i.max);
      const n = v <= b ? (b > a ? low + (mid - low) * (v - a) / (b - a) : mid) : mid + (high - mid) * (v - b) / (c - b);
      return n.toFixed(Number(i.dataset.places));
    };
    const apply = () => {
      line.style.fontVariationSettings = sliders.map((i) => axis(i, i.value)).join(", ");
      let moved = false;
      for (const i of sliders) {
        const off = Math.abs(Number(i.value) - Number(i.dataset.default)) > 1e-6;
        i.nextElementSibling.value = number(i);
        i.parentElement.classList.toggle("moved", off);
        moved = moved || off;
      }
      back.hidden = !moved;
    };
    // The line is in two rows, broken at the space nearest its middle, and sized once with every number at
    // rest. A slider then changes the letters and nothing else.
    const lay = () => {
      // the words come from the page's texts and not from the line: the line has lost a space to its break
      const can = (line.dataset.langs || "").split(" ").includes(lingo.code);
      const said = (can && lingo.words && lingo.words[line.dataset.fontText]) || line.dataset.english;
      const text = said.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
      const spaces = [...text].map((ch, k) => (ch === " " ? k : -1)).filter((k) => k > 0);
      const cut = spaces.sort((x, y) => Math.abs(x - text.length / 2) - Math.abs(y - text.length / 2))[0];
      line.textContent = "";
      if (cut === undefined) line.append(text);
      else line.append(text.slice(0, cut), document.createElement("br"), text.slice(cut + 1));
      const now = line.style.fontVariationSettings;
      line.style.fontVariationSettings = rest;
      line.style.fontSize = "100px";
      const box = stage.getBoundingClientRect(), r = line.getBoundingClientRect();
      const room = box.width - 2 * line.offsetLeft;
      if (r.width) line.style.fontSize = `${(100 * Math.min((room * 0.72) / r.width, (box.height * 0.5) / r.height)).toFixed(1)}px`;
      line.style.fontVariationSettings = now;
    };
    let glide = 0, touched = false;
    for (const i of sliders) i.addEventListener("input", () => { touched = true; cancelAnimationFrame(glide); apply(); });
    // The first time the line is in view, its letters come up from the lightest weight to the weight at rest,
    // and the number counts with them. It happens once, and not after the reader has moved a slider.
    const weight = sliders.find((i) => i.dataset.tag === "wght");
    if (weight && !still) {
      const seen = new IntersectionObserver(([e]) => {
        if (!e.isIntersecting) return;
        seen.disconnect();
        if (touched) return;
        const t0 = performance.now(), from = Number(weight.min), to = Number(weight.dataset.default);
        const step = (t) => {
          if (touched) return;
          const k = Math.min(1, (t - t0) / 900), ease = 1 - (1 - k) ** 3;
          weight.value = k === 1 ? weight.dataset.default : from + (to - from) * ease;
          apply();
          back.hidden = true;                          // nothing to take back: the reader has changed nothing
          weight.parentElement.classList.remove("moved");
          if (k < 1) glide = requestAnimationFrame(step);
        };
        glide = requestAnimationFrame(step);
      }, { threshold: 0.6 });
      seen.observe(stage);
    }
    // "Reset" glides every number back to rest
    back.addEventListener("click", () => {
      cancelAnimationFrame(glide);
      const from = sliders.map((i) => Number(i.value)), t0 = performance.now(), long = still ? 1 : 420;
      const step = (t) => {
        const k = Math.min(1, (t - t0) / long), ease = 1 - (1 - k) ** 3;
        sliders.forEach((i, j) => { i.value = k === 1 ? i.dataset.default : from[j] + (Number(i.dataset.default) - from[j]) * ease; });
        apply();
        if (k < 1) glide = requestAnimationFrame(step);
      };
      glide = requestAnimationFrame(step);
    });
    const face = line.style.fontFamily.split(",")[0].replace(/"/g, "").trim();
    const fresh = () => document.fonts.load(`100px "${face}"`, line.textContent).catch(() => {}).then(lay, lay);
    relayout.push(fresh);
    addEventListener("resize", lay);
    apply();
    fresh();
  }

  // A button over a block of commands copies them.
  for (const b of $$(".copy")) {
    let timer = 0;
    b.addEventListener("click", async () => {
      const text = $$(".line", b.closest("figure")).map((l) => l.textContent).join("\n");
      try { await navigator.clipboard.writeText(text); } catch (e) { return; }
      if (!b.classList.contains("done")) b.dataset.label = b.innerHTML;
      b.textContent = b.dataset.said;
      b.classList.add("done");
      clearTimeout(timer);
      timer = setTimeout(() => { b.innerHTML = b.dataset.label; b.classList.remove("done"); }, 1600);
    });
  }

  const stage = $("#talk-stage");
  if (stage) {
    const rounds = $$("#rounds button");
    let auto = 0;
    const go = (k) => {
      stage.dataset.round = k;
      rounds.forEach((b, j) => b.setAttribute("aria-pressed", String(j === k)));
    };
    rounds.forEach((b, k) => b.addEventListener("click", () => { clearInterval(auto); auto = -1; go(k); }));
    // it plays once by itself, the first time it is in view
    const watch = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting || auto) return;
      watch.disconnect();
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      let k = 0;
      auto = setInterval(() => { k += 1; go(k); if (k >= rounds.length - 1) clearInterval(auto); }, 2000);
    }, { threshold: 0.35 });
    watch.observe(stage);
  }

  // The footer: one block for each font. They fall and pile up on the floor, and a mouse can throw them.
  const pile = $("#pile");
  if (pile && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const again = $("#again");
    const library = () => new Promise((ok, no) => {
      if (window.Matter) return ok();
      const s = document.createElement("script");
      s.src = "vendor/matter.min.js";
      s.onload = ok;
      s.onerror = no;
      document.head.append(s);
    });
    let stop = null;
    const begin = async () => {
      await library();
      await document.fonts.ready;
      const { Engine, Bodies, Body, Composite, Constraint, Sleeping } = window.Matter;
      // measure the blocks while they still sit in rows, then let them go
      pile.classList.remove("live");
      const blocks = $$(".drop", pile).filter((b) => b.offsetParent !== null);
      const sizes = blocks.map((b) => [b.offsetWidth, b.offsetHeight]);
      const W = pile.clientWidth, H = pile.clientHeight;
      pile.classList.add("live");
      // The live pile reaches above the footer, so a block shows while it falls in. It cuts off what is
      // outside it, so a block can never make the page longer. `lift` is how far it reaches up.
      const lift = pile.clientHeight - H;
      const engine = Engine.create({ enableSleeping: true });
      engine.gravity.y = 1.15;
      const still = (x, y, w, h) => Bodies.rectangle(x, y, w, h, { isStatic: true, friction: 0.7 });
      const THICK = 3000;
      Composite.add(engine.world, [
        still(W / 2, H + THICK / 2, W + 2 * THICK, THICK),
        still(-THICK / 2, H / 2 - 2000, THICK, H + 8000),
        still(W + THICK / 2, H / 2 - 2000, THICK, H + 8000),
      ]);
      const rnd = (a, b) => a + Math.random() * (b - a);
      // On a wide screen the words of the footer are solid: a block lands on a line of text and slides off.
      let free = null, wordsLeft = W, wordsRight = 0;
      if (W >= 900) {
        const box = pile.getBoundingClientRect();
        const origin = { left: box.left, top: box.top + lift };
        const range = document.createRange();
        for (const part of $$(".foot-text > *")) {
          // one solid bar for each line of text, as wide as its words
          range.selectNodeContents(part);
          const lines = [];
          for (const r of range.getClientRects()) {
            if (r.width < 4 || r.height < 4) continue;
            const line = lines.find((l) => Math.abs(l.top - r.top) < r.height * 0.6);
            if (line) { line.left = Math.min(line.left, r.left); line.right = Math.max(line.right, r.right); line.bottom = Math.max(line.bottom, r.bottom); }
            else lines.push({ left: r.left, right: r.right, top: r.top, bottom: r.bottom });
          }
          for (const l of lines) {
            const w = l.right - l.left, h = l.bottom - l.top;
            Composite.add(engine.world, still(l.left - origin.left + w / 2, l.top - origin.top + h / 2, Math.max(8, w - 8), h * 0.7));
            wordsLeft = Math.min(wordsLeft, l.left - origin.left);
            wordsRight = Math.max(wordsRight, l.right - origin.left);
          }
        }
        // the side of the footer that has no words: the right, or the left where the script runs right to left
        if (wordsRight > 0) free = W - wordsRight >= wordsLeft ? [wordsRight + 30, W] : [0, wordsLeft - 30];
      }
      const bodies = blocks.map((el, i) => {
        const [w, h] = sizes[i];
        // most blocks come down beside the words, and a few on top of them
        const [a, b] = free && Math.random() < 0.72 ? free : [0, W];
        const least = w / 2 + 12, most = Math.max(least, W - w / 2 - 12);
        const from = Math.min(Math.max(a + w / 2, least), most), to = Math.max(from + 1, Math.min(b - w / 2, most));
        const body = Bodies.rectangle(rnd(from, to), -h - rnd(20, 160), w, h, {
          chamfer: { radius: Math.min(h * 0.3, 18) }, restitution: 0.24, friction: 0.55, frictionAir: 0.014, density: 0.0018,
          angle: rnd(-0.55, 0.55),
        });
        Body.setAngularVelocity(body, rnd(-0.06, 0.06));
        el.style.transform = `translate(${-w - 50}px, ${-h - 50}px)`;
        return body;
      });
      const waiting = bodies.slice().sort(() => Math.random() - 0.5);
      const total = waiting.length;
      let born = performance.now(), last = born, running = false, seen = true, grab = null, alive = true;
      const draw = () => bodies.forEach((b, i) => {
        if (!b.added) return;
        const [w, h] = sizes[i];
        blocks[i].style.transform = `translate(${(b.position.x - w / 2).toFixed(1)}px, ${(b.position.y - h / 2 + lift).toFixed(1)}px) rotate(${b.angle.toFixed(3)}rad)`;
      });
      // No block may leave the footer. A fast block is slowed, so it cannot pass through the floor in
      // one step. A block that is outside anyway falls in again from the top.
      const FAST = 38;
      const keep = () => bodies.forEach((b, i) => {
        if (!b.added) return;
        const [w, h] = sizes[i];
        const v = b.velocity, speed = Math.hypot(v.x, v.y);
        if (speed > FAST) Body.setVelocity(b, { x: v.x / speed * FAST, y: v.y / speed * FAST });
        if (Math.abs(b.angularVelocity) > 0.5) Body.setAngularVelocity(b, Math.sign(b.angularVelocity) * 0.5);
        const { x, y } = b.position;
        if (!(y < H + 40 && y > -lift - 4000 && x > -40 && x < W + 40)) {
          if (grab && grab.bodyB === b) { Composite.remove(engine.world, grab); grab = null; }
          Body.setPosition(b, { x: Math.min(Math.max(x || W / 2, w / 2 + 12), Math.max(w / 2 + 12, W - w / 2 - 12)), y: -h - 40 });
          Body.setVelocity(b, { x: 0, y: 0 });
          Body.setAngularVelocity(b, 0);
          Sleeping.set(b, false);
        }
      });
      const frame = (now) => {
        if (!alive || !seen) { running = false; return; }
        // the blocks come one after another
        while (waiting.length && now - born > (total - waiting.length) * 95) {
          const b = waiting.shift();
          b.added = true;
          Composite.add(engine.world, b);
        }
        // two short steps are safer than one long step
        const dt = Math.min(Math.max(now - last, 1), 32) / 2;
        for (let k = 0; k < 2; k++) { Engine.update(engine, dt); keep(); }
        last = now;
        draw();
        const moving = waiting.length || grab || bodies.some((b) => b.added && !b.isSleeping);
        if (moving) requestAnimationFrame(frame);
        else { running = false; if (again) again.hidden = false; }
      };
      const wake = () => { if (!running && alive) { running = true; last = performance.now(); requestAnimationFrame(frame); } };
      // the place of the pointer in the footer, never outside the walls or under the floor
      const at = (ev) => {
        const r = pile.getBoundingClientRect();
        return { x: Math.min(Math.max(ev.clientX - r.left, 0), W), y: Math.min(Math.max(ev.clientY - r.top - lift, -lift), H - 6) };
      };
      const down = (ev) => {
        const i = blocks.indexOf(ev.target.closest(".drop"));
        if (i < 0) return;
        const b = bodies[i];
        Sleeping.set(b, false);
        if (ev.pointerType !== "mouse") {
          // a finger gives the block a kick, and the page still scrolls
          Body.setVelocity(b, { x: rnd(-7, 7), y: rnd(-17, -12) });
          Body.setAngularVelocity(b, rnd(-0.25, 0.25));
        } else {
          ev.preventDefault();
          const p = at(ev);
          grab = Constraint.create({ pointA: p, bodyB: b, pointB: { x: p.x - b.position.x, y: p.y - b.position.y }, length: 0, stiffness: 0.16, damping: 0.12 });
          Composite.add(engine.world, grab);
          try { blocks[i].setPointerCapture(ev.pointerId); } catch (e) { /* the pointer is gone */ }
        }
        wake();
      };
      const move = (ev) => { if (grab) { grab.pointA = at(ev); Sleeping.set(grab.bodyB, false); } };
      const up = () => { if (grab) { Composite.remove(engine.world, grab); grab = null; } };
      pile.addEventListener("pointerdown", down);
      pile.addEventListener("pointermove", move);
      pile.addEventListener("pointerup", up);
      pile.addEventListener("pointercancel", up);
      const watch = new IntersectionObserver(([e]) => { seen = e.isIntersecting; if (seen) wake(); });
      watch.observe(pile);
      wake();
      stop = () => {
        alive = false;
        watch.disconnect();
        pile.removeEventListener("pointerdown", down);
        pile.removeEventListener("pointermove", move);
        pile.removeEventListener("pointerup", up);
        pile.removeEventListener("pointercancel", up);
        for (const el of blocks) el.style.transform = "";
      };
    };
    const restart = () => { if (stop) stop(); stop = null; begin().catch(() => pile.classList.remove("live")); };
    // they start to fall when the footer comes into view for the first time
    const first = new IntersectionObserver(([e]) => { if (e.isIntersecting) { first.disconnect(); restart(); } }, { threshold: 0.2 });
    first.observe(pile);
    if (again) again.addEventListener("click", restart);
    relayout.push(() => { if (stop) restart(); });      // the words of the footer are solid, so the blocks fall again
    let width = innerWidth, timer = 0;
    addEventListener("resize", () => {
      if (innerWidth === width || !stop) return;
      width = innerWidth;
      clearTimeout(timer);
      timer = setTimeout(restart, 300);
    });
  }

  // The character table: pick a font, point at a character.
  const body = $(".charset-body");
  if (body) {
    const fonts = $$(".charset-fonts [data-font]");
    const grid = $(".charset-grid", body);
    const row = $(".charset-scripts");            // the other scripts of the picked font, where it has whole fonts of them
    const count = $("#characters h2[data-n]");    // on a font's page the heading says how many characters show
    const home = [...grid.childNodes];            // the font's own characters, as the page came
    const own = count ? count.dataset.n : "";
    const cells = () => $$("button", grid);
    // "20-7E A0 ..." in hexadecimal: a list of characters
    const listed = (text) => {
      const have = new Set();
      for (const run of text.split(" ")) {
        const [a, b = a] = run.split("-").map((x) => parseInt(x, 16));
        for (let c = a; c <= b; c++) have.add(c);
      }
      return have;
    };
    const big = $(".glyph-big", body);
    const name = $(".glyph-name", body);
    const code = $(".glyph-code", body);
    let current = null;
    const show = (b) => {
      if (!b || b === current) return;
      current?.removeAttribute("aria-current");
      b.setAttribute("aria-current", "true");
      current = b;
      big.textContent = b.textContent;
      name.textContent = b.dataset.name;
      code.textContent = `U+${b.dataset.cp}`;
    };
    const first = () => { current = null; show($("button:not([hidden])", grid)); };
    // the number in the heading follows what the table shows
    const says = (n) => {
      if (!count || count.dataset.n === String(n)) return;
      count.innerHTML = count.innerHTML.replace(count.dataset.n, n);
      count.dataset.n = n;
    };

    // A long table starts folded: its first rows show, and the button under it opens the rest and closes it
    // again. A table of a few rows has no button.
    const more = $(".charset-more"), toggle = more && $("button", more);
    let open = false;
    const fold = () => {
      if (!toggle) return;
      const long = cells().filter((c) => !c.hidden).length > 60;
      more.hidden = !long;
      body.classList.toggle("folded", long && !open);
      toggle.setAttribute("aria-expanded", String(long && open));
      if (!open) grid.scrollTop = 0;
    };
    if (toggle) {
      toggle.addEventListener("click", () => {
        const before = toggle.getBoundingClientRect().top;
        open = !open;
        fold();
        // the table closes above the button: the page follows, so that the button stays where the reader pressed it
        if (!open) scrollBy({ top: toggle.getBoundingClientRect().top - before, behavior: "instant" });
      });
    }
    // a character under the fold that takes the focus (the Tab key) opens the table
    const reach = (b) => {
      if (!b || !body.classList.contains("folded")) return;
      if (b.getBoundingClientRect().top > grid.getBoundingClientRect().bottom - 8 || grid.scrollTop > 0) { open = true; fold(); }
    };

    // The fonts of a family for other scripts. Each is a whole font of some megabytes, so its characters and
    // the font itself load only when the reader picks the script.
    const files = {};
    let script = null;                            // the script in the table, or null for the font's own characters
    const label = (key, text) => (lingo.words && lingo.words[key]) || text;
    const draw = (data) => {
      const nodes = [];
      for (const [key, text, runs] of data.groups) {
        const head = document.createElement("h3"), word = document.createElement("span"), n = document.createElement("span");
        const box = document.createElement("div");
        const have = [...listed(runs)];
        head.className = "label";
        head.dataset.key = key;
        head.dataset.english = text;
        word.textContent = label(key, text);
        n.className = "muted";
        n.textContent = have.length;
        head.append(word, " ", n);
        box.className = "glyphs";
        for (const cp of have) {
          const b = document.createElement("button"), hex = cp.toString(16).toUpperCase().padStart(4, "0");
          b.type = "button";
          b.dataset.cp = hex;
          b.dataset.name = data.names[hex] || `cjk unified ideograph-${hex}`;     // a Han character has no other name
          b.setAttribute("aria-label", b.dataset.name);
          b.textContent = String.fromCodePoint(cp);
          box.append(b);
        }
        nodes.push(head, box);
      }
      grid.replaceChildren(...nodes);
      fold();
    };
    const back = () => {                          // the font's own characters again
      script = null;
      grid.replaceChildren(...home);
      body.style.fontFamily = `"${body.dataset.font}", var(--fallback)`;
      says(own);
      fold();
    };
    const pick = async (s, button) => {
      for (const c of $$("button", row)) c.setAttribute("aria-pressed", String(c === button));
      if (!s) { back(); return first(); }
      script = s;
      if (!files[s.file]) files[s.file] = fetch(s.file).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))));
      let data;
      try { data = await files[s.file]; } catch (e) { delete files[s.file]; return; }
      if (script !== s) return;                   // another one was picked in the meantime
      body.style.fontFamily = `"${s.font}", var(--fallback)`;
      draw(data);
      says(data.count);
      first();
    };
    // The row of scripts for the picked family: its own letters first, then each script it has a whole font of.
    const offer = (list) => {
      if (!row) return;
      row.replaceChildren();
      row.hidden = !list.length;
      const add = (text, s) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = text;
        b.setAttribute("aria-pressed", String(!s));
        b.addEventListener("click", () => pick(s, b));
        row.append(b);
      };
      if (list.length) add("Latin", null);
      for (const s of list) add(s.name, s);
    };
    const scriptsOf = (el) => { try { return JSON.parse(el.dataset.scripts || "[]"); } catch (e) { return []; } };
    for (const b of fonts) {
      b.addEventListener("click", () => {
        body.dataset.font = b.dataset.font;
        back();
        body.style.fontVariationSettings = b.dataset.fvs || "normal";
        // a color font brings its first palette, and the ground that it was drawn for
        body.style.fontPalette = b.dataset.palette || "";
        body.classList.toggle("dressed", Boolean(b.dataset.ground));
        body.style.setProperty("--ground", b.dataset.ground || "");
        body.style.setProperty("--tone", b.dataset.ink || "");
        for (const c of fonts) c.setAttribute("aria-pressed", String(c === b));
        if (b.dataset.has) {
          // only the characters of this font show, and each group counts its own
          const have = listed(b.dataset.has);
          for (const c of cells()) c.hidden = !have.has(parseInt(c.dataset.cp, 16));
          for (const group of $$(".glyphs", grid)) {
            const n = $$("button:not([hidden])", group).length, head = group.previousElementSibling;
            group.hidden = head.hidden = n === 0;
            $(".muted", head).textContent = n;
          }
          fold();
        }
        offer(scriptsOf(b));
        first();
      });
    }
    offer(scriptsOf(body));
    grid.addEventListener("pointerover", (ev) => show(ev.target.closest("button")));
    grid.addEventListener("focusin", (ev) => { reach(ev.target.closest("button")); show(ev.target.closest("button")); });
    grid.addEventListener("click", (ev) => show(ev.target.closest("button")));
    show($("button", grid));
    fold();
    // a new language: the names of the groups in a script's table follow it
    relayout.push(() => { for (const head of $$("h3[data-key]", grid)) head.firstChild.textContent = label(head.dataset.key, head.dataset.english); });
  }

  // Languages. English is in the page. Every other language is one small file, loaded when it is chosen.
  const menu = $("#lang");
  if (menu) {
    const keyed = $$("[data-i18n]");
    const named = $$("[data-i18n-attr]").map((el) => {
      const [attr, key] = el.dataset.i18nAttr.split(":");
      return { el, attr, key, en: el.getAttribute(attr) };
    });
    // the English text of each key. A text with a number keeps a place for it, because the number can change
    const english = new Map(keyed.map((el) => [el, el.dataset.n ? el.innerHTML.replace(el.dataset.n, "{n}") : el.innerHTML]));
    const fontTexts = $$("[data-font-text]");
    const shown = $("#lang-name");
    const codes = [...menu.options].map((o) => o.value);
    const saved = {
      get: () => { try { return localStorage.getItem("wf-lang"); } catch (e) { return null; } },
      set: (v) => { try { localStorage.setItem("wf-lang", v); } catch (e) { /* no storage */ } },
    };
    const files = {};
    const load = (code) => {
      if (code === "en") return Promise.resolve(null);
      if (!files[code]) {
        files[code] = fetch("i18n/" + code + ".json").then((r) => {
          if (!r.ok) throw new Error(String(r.status));
          return r.json();
        });
      }
      return files[code];
    };
    let wanted = "en";
    const use = async (code, remember) => {
      // a code from the address or from storage may differ in case: ?lang=zh-hant is zh-Hant
      code = codes.find((c) => c.toLowerCase() === String(code).toLowerCase()) || "en";
      wanted = code;
      let words = null;
      try { words = await load(code); } catch (e) { delete files[code]; if (wanted === code) wanted = "en"; code = "en"; }
      if (wanted !== code) return;        // another language was chosen in the meantime
      const option = [...menu.options].find((o) => o.value === code);
      const way = option.dataset.dir || "ltr";
      // what the reader looks at stays where it is
      const line = top.offsetHeight + 8;
      const held = scrollY > 4 ? [...keyed, ...specs].find((el) => {
        const r = el.getBoundingClientRect();
        return r.height > 0 && r.bottom > line;
      }) : null;
      const before = held ? held.getBoundingClientRect().top : 0;
      root.lang = code;
      root.dir = way;
      for (const el of keyed) {
        const text = words && words[el.dataset.i18n];
        el.innerHTML = (text || english.get(el)).replace("{n}", el.dataset.n || "");
        if (code === "en") { el.removeAttribute("lang"); el.removeAttribute("dir"); continue; }
        // a text that has no translation yet says that it is English
        el.lang = text ? code : "en";
        // inside a sample of a font, which runs left to right, a translated label keeps its own direction
        if (el.parentElement.closest("[dir]") !== root) el.dir = text ? way : "ltr";
      }
      for (const { el, attr, key, en } of named) el.setAttribute(attr, (words && words[key]) || en);
      lingo.code = code;
      lingo.words = words;
      lingo.way = way;
      // Words that are set in a font (the wall, the footer blocks, the demo) follow the language where that
      // font has every letter. They never fall back to another font: without the letters they stay English.
      for (const el of fontTexts) {
        const can = (el.dataset.langs || "").split(" ").includes(code);
        const next = (can && words && words[el.dataset.fontText]) || el.dataset.english;
        if (el.innerHTML !== next) el.innerHTML = next;
        el.lang = can ? code : "en";
        el.dir = can ? way : "ltr";
      }
      // A sample is set in the language too, where its font has every letter of the translation. A sample
      // that the reader has changed stays as it is.
      for (const s of samples) {
        const can = (s.dataset.sampleLangs || "").split(" ").includes(code);
        const next = (can && words && words[s.dataset.sample]) || s.dataset.english;
        if (!next) continue;
        if (s.textContent === s.dataset.default) {
          s.textContent = next;
          s.lang = can ? code : "en";
          s.dir = can ? way : "ltr";          // an Arabic sample runs right to left inside its left-to-right frame
        }
        s.dataset.default = next;
      }
      menu.value = code;
      for (const row of $$(".lang-option")) row.setAttribute("aria-selected", String(row.dataset.code === code));
      shown.textContent = option.textContent;
      // on a phone the menu shows a short label: the code, or a word where two codes would look the same
      shown.dataset.code = option.dataset.short || code.toUpperCase();
      setTop();
      lock();
      if (held) {
        const moved = held.getBoundingClientRect().top - before;
        if (Math.abs(moved) >= 0.5) scrollBy({ top: moved, behavior: "instant" });
      }
      pin = null;
      for (const again of relayout) again();
      if (remember) saved.set(code);
    };
    menu.addEventListener("change", () => use(menu.value, true));

    // The list of languages opens under its button. Arrow keys move in it, Enter chooses, Escape closes.
    const button = $("#lang-button"), list = $("#lang-list");
    if (button && list) {
      const rows = $$(".lang-option", list);
      const current = () => rows.find((r) => r.getAttribute("aria-selected") === "true") || rows[0];
      const shut = (back) => {
        if (list.hidden) return;
        list.hidden = true;
        button.setAttribute("aria-expanded", "false");
        if (back) button.focus({ preventScroll: true });
      };
      const open = () => {
        list.hidden = false;
        button.setAttribute("aria-expanded", "true");
        current().focus({ preventScroll: true });
      };
      button.addEventListener("click", () => (list.hidden ? open() : shut(true)));
      button.addEventListener("keydown", (ev) => {
        if (ev.key === "ArrowDown" || ev.key === "ArrowUp") { ev.preventDefault(); open(); }
      });
      list.addEventListener("keydown", (ev) => {
        const at = rows.indexOf(document.activeElement);
        const to = { ArrowDown: Math.min(at + 1, rows.length - 1), ArrowUp: Math.max(at - 1, 0), Home: 0, End: rows.length - 1 }[ev.key];
        if (to !== undefined) { ev.preventDefault(); rows[to].focus({ preventScroll: true }); }
        else if (ev.key === "Escape") { ev.preventDefault(); shut(true); }
        else if (ev.key === "Tab") shut(false);
      });
      for (const row of rows) {
        row.addEventListener("click", () => {
          shut(true);
          if (row.dataset.code !== menu.value) { menu.value = row.dataset.code; use(row.dataset.code, true); }
        });
      }
      // a press anywhere else closes the list
      addEventListener("pointerdown", (ev) => { if (!ev.target.closest("#lang-box")) shut(false); });
      addEventListener("blur", () => shut(false));
    }
    const first = new URLSearchParams(location.search).get("lang") || saved.get();
    if (first && first !== "en") use(first, false);
  }
})();
