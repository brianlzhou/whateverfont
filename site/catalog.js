// The library: find a font by a mood, order the shelf, vote for a font, count the views of a font's page.
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------------------------------------------------------------- votes and views
  // The counts live in a store behind three small functions (api/). Until the store answers, and where
  // there is none, the buttons and the numbers stay hidden: the page never shows a made-up number.
  const votes = $$(".vote");
  const kept = {
    get: () => { try { return new Set(JSON.parse(localStorage.getItem("wf-voted") || "[]")); } catch (e) { return new Set(); } },
    set: (ids) => { try { localStorage.setItem("wf-voted", JSON.stringify([...ids])); } catch (e) { /* no storage */ } },
  };
  const count = new Map();          // font id -> votes
  const seen = new Map();           // font id -> views
  const number = (n) => n.toLocaleString(document.documentElement.lang || "en");
  let mine = kept.get(), live = false;
  let order = "picked", arrange = () => {};       // the shelf sets these; a font's own page has no shelf
  const paint = (button) => {
    const id = button.dataset.id, n = count.get(id) || 0;
    button.hidden = !live;
    button.setAttribute("aria-pressed", String(mine.has(id)));
    $(".vote-n", button).textContent = n ? number(n) : "";
  };
  // The views of a font: an eye and a number, next to its vote. A font that nobody has opened shows none.
  const eyes = $$(".views");
  const show = (el) => {
    const n = seen.get(el.dataset.id) || 0;
    el.hidden = !live || !n;
    $(".views-n", el).textContent = number(n);
    el.setAttribute("aria-label", number(n) + (n === 1 ? " view" : " views"));
  };
  // Where the counts are: the address of a small Worker (worker/ in the repository), named in the page's head.
  // A page with no address asks for nothing.
  const base = (($('meta[name="counts"]') || {}).content || "").replace(/\/+$/, "");
  const answer = (r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status))));
  // the body goes as plain text, so the browser does not ask the Worker for permission before every press
  const send = (path, data) => (base ? fetch(`${base}/${path}`, { method: "POST", body: JSON.stringify(data) }).then(answer)
    : Promise.reject(new Error("no counts")));
  for (const button of votes) {
    button.addEventListener("click", () => {
      const id = button.dataset.id, on = !mine.has(id), before = count.get(id) || 0;
      // the press shows at once, and goes back if the store refuses it
      if (on) mine.add(id); else mine.delete(id);
      count.set(id, Math.max(0, before + (on ? 1 : -1)));
      votes.filter((b) => b.dataset.id === id).forEach(paint);
      send("vote", { id, on }).then((reply) => {
        count.set(id, reply.votes);
        kept.set(mine);
        votes.filter((b) => b.dataset.id === id).forEach(paint);
        if (order === "top") arrange();
      }).catch(() => {
        if (on) mine.delete(id); else mine.add(id);
        count.set(id, before);
        votes.filter((b) => b.dataset.id === id).forEach(paint);
      });
    });
  }
  const stats = (base ? fetch(`${base}/stats`).then(answer) : Promise.reject(new Error("no counts"))).then((data) => {
    live = true;
    for (const [id, f] of Object.entries(data.fonts || {})) { count.set(id, f.votes || 0); seen.set(id, f.views || 0); }
    mine = new Set(data.mine || []);
    kept.set(mine);
    votes.forEach(paint);
    eyes.forEach(show);
    return data;
  }).catch(() => null);

  // The page of one font counts a view, once a day for a visitor, and shows the number.
  const font = document.body.dataset.font;
  if (font) {
    stats.then((data) => {
      if (!data) return;
      send("view", { id: font }).then((reply) => {
        seen.set(font, reply.views || 0);
        eyes.filter((el) => el.dataset.id === font).forEach(show);
      }).catch(() => {});
    });
  }

  // ---------------------------------------------------------------- the shelf
  const shelf = $("#shelf"), input = $("#mood");
  if (!shelf || !input) return;
  const fonts = JSON.parse($("#catalog-data").textContent);       // [{id, name, moods, more}], in the picked order
  const books = new Map($$(".book", shelf).map((b) => [b.dataset.id, b]));
  const next = $("#mood-next"), none = $("#shelf-none"), sorts = $("#sorts"), note = $("#mood-note"), total = $("#shelf-count");
  let found = null, ready = null, prepared = null, asked = "";

  // A word can be too long for its tile. It is made smaller until it fits.
  const snug = () => {
    for (const word of $$(".tile-word", shelf)) {
      word.style.setProperty("--fit", 1);
      const room = word.parentElement.clientWidth * 0.84, wide = word.getBoundingClientRect().width;
      if (wide > room) word.style.setProperty("--fit", (room / wide).toFixed(3));
    }
  };
  // Put the books in an order, with a short fade so the eye does not have to follow twenty moves.
  // Only a change moves: the same fonts in the same order stay as they are.
  let placed = fonts.map((f) => f.id).join(" ");
  const place = (ids, shown) => {
    const want = ids.filter((id) => !shown || shown.has(id)).join(" ");
    if (want === placed) return requestAnimationFrame(snug);
    placed = want;
    const move = () => {
      for (const id of ids) shelf.append(books.get(id));
      for (const [id, book] of books) book.hidden = shown ? !shown.has(id) : false;
      shelf.classList.remove("turning");
      requestAnimationFrame(snug);
    };
    if (calm) return move();
    shelf.classList.add("turning");
    setTimeout(move, 100);
  };
  arrange = () => {
    if (found) return;
    const ids = fonts.map((f) => f.id);
    if (order === "name") ids.sort((a, b) => books.get(a).dataset.name.localeCompare(books.get(b).dataset.name));
    if (order === "top") ids.sort((a, b) => (count.get(b) || 0) - (count.get(a) || 0));
    if (order === "views") ids.sort((a, b) => (seen.get(b) || 0) - (seen.get(a) || 0));
    place(ids, null);
  };
  for (const button of $$("button", sorts)) {
    button.addEventListener("click", () => {
      order = button.dataset.sort;
      $$("button", sorts).forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
      arrange();
    });
  }
  stats.then((data) => {
    // "Most loved" and "Most viewed" are orders only when there is something to order by
    if (data && Object.values(data.fonts || {}).some((f) => f.votes > 0)) $('[data-sort="top"]', sorts).hidden = false;
    if (data && Object.values(data.fonts || {}).some((f) => f.views > 0)) $('[data-sort="views"]', sorts).hidden = false;
  });

  // The words under the line: ways to start, or ways to go on from what was found.
  // A word that was there already stays without a move. Only a new word arrives.
  const offer = (words, starters) => {
    const was = next.classList.contains("starters") === starters ? new Map($$("button", next).map((b) => [b.textContent, b])) : new Map();
    next.classList.toggle("starters", starters);
    next.replaceChildren(...words.map((w) => {
      const old = was.get(w);
      if (old) { old.classList.remove("new"); return old; }
      const b = document.createElement("button");
      b.type = "button";
      b.className = "new";
      b.textContent = w;
      b.addEventListener("click", () => {
        input.value = next.classList.contains("starters") ? w : input.value.trim() + " " + w;
        input.focus();
        look();
      });
      return b;
    }));
  };
  // The words to start with can take more lines than the words to go on with. The place keeps the height of
  // the first, so the fonts under it do not jump when a search starts.
  const hold = () => {
    if (!next.classList.contains("starters")) return;
    next.style.minHeight = "";
    next.style.minHeight = next.offsetHeight + "px";
  };
  const starters = () => { offer((next.dataset.starters || "").split("|").filter(Boolean), true); hold(); };
  // A long need still fits the line: its letters get smaller, and the line keeps its height.
  const fitLine = () => {
    input.style.setProperty("--mood-fit", 1);
    const room = input.clientWidth, wide = input.scrollWidth;
    if (wide > room + 1) input.style.setProperty("--mood-fit", Math.max(0.42, room / wide).toFixed(3));
  };

  // The word of a tile: what the reader typed, set in that font, or the font's own word.
  const words = [...books.values()].map((book) => $(".tile-word", book));
  for (const word of words) word.dataset.own = word.innerHTML;
  let dressed = "";
  const dress = (text) => {
    dressed = text;
    for (const word of words) { if (text) word.textContent = text; else word.innerHTML = word.dataset.own; }
  };

  const look = async () => {
    const query = input.value.trim();
    fitLine();
    if (query === asked) return;
    asked = query;
    const url = new URL(location.href);
    if (query) url.searchParams.set("q", query); else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    if (!query) {
      found = null;
      for (const book of books.values()) $(".book-why", book).textContent = "";
      dress("");
      none.hidden = true;
      total.parentElement.classList.remove("finding");
      starters();
      return arrange();
    }
    if (!ready) ready = FontSearch.load().then(() => { prepared = FontSearch.prepare(fonts); });
    try { await ready; } catch (e) { ready = null; return; }
    if (input.value.trim() !== query) return;                       // the reader typed on while the words loaded
    const results = FontSearch.search(query, prepared);
    const best = results[0] ? results[0].score : 0;
    // what fits: close to the best one, and never a font that answers none of the words
    const fits = results.filter((r, k) => r.score >= 0.5 && (r.score >= best - 0.18 || k < 3));
    found = fits;
    total.parentElement.classList.add("finding");      // the count and the orders make room, and keep their height
    none.hidden = fits.length > 0;
    for (const r of results) {
      const why = r.why.filter((w) => w[2] >= 0.5).map((w) => w[1]);
      $(".book-why", books.get(r.id)).textContent = fits.includes(r) ? [...new Set(why)].slice(0, 3).join(" ") : "";
    }
    dress(fits.length && query.length <= 26 ? query : "");
    place(results.map((r) => r.id), fits.length ? new Set(fits.map((r) => r.id)) : null);
    if (fits.length) offer(FontSearch.branches(query, fits, prepared), false); else next.replaceChildren();
  };
  let timer = 0;
  input.addEventListener("input", () => { fitLine(); clearTimeout(timer); timer = setTimeout(look, 140); });
  input.addEventListener("keydown", (ev) => { if (ev.key === "Escape") { input.value = ""; look(); } });
  input.addEventListener("focus", () => { if (!ready && window.FontSearch) ready = FontSearch.load().then(() => { prepared = FontSearch.prepare(fonts); }).catch(() => { ready = null; }); }, { once: true });
  $("#shelf-clear").addEventListener("click", () => { input.value = ""; look(); input.focus(); });
  addEventListener("resize", () => { snug(); hold(); fitLine(); });
  document.fonts.ready.then(() => { snug(); hold(); fitLine(); });
  // the search knows English words: a page in another language says so
  new MutationObserver(() => {
    note.hidden = (document.documentElement.lang || "en") === "en";
    // the page has just set the tiles' words in the new language: those are the fonts' own words now
    for (const word of words) if (word.dataset.fontText) word.dataset.own = word.innerHTML;
    if (dressed) dress(dressed);
    requestAnimationFrame(snug);
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });

  starters();
  const first = new URL(location.href).searchParams.get("q");
  if (first) { input.value = first; look(); }
})();
