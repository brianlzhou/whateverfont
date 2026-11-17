// Search the fonts by meaning, in the reader's browser. Nothing that a reader types leaves the page.
//
// Each font has mood words. Each word of a query takes its best match among them, by the angle between
// two word vectors (search/vectors.bin, made by scripts/build_search.py). "ocean" is near "sea" and
// "wave", so a reader can type a need in their own words. The vectors are English.
(() => {
  const DIM = 50, FULL = 127 * 127;
  const STOP = new Set(("a an the of for and or to in on with like that this it is are was be as at by from my me i we you " +
    "your make made font fonts letter letters typeface something some want need looking look feels feel").split(" "));
  let loading = null, words = [], rank = new Map(), vectors = new Int8Array(0);

  const tokens = (text) => (String(text).toLowerCase().match(/[a-z]+/g) || []).filter((w) => !STOP.has(w));

  // Fetch the words and their vectors once. `get` is fetch by default; a test passes its own.
  const load = (base = "search/", get = (url) => fetch(url)) => {
    if (!loading) {
      loading = Promise.all([get(base + "vocab.txt").then((r) => r.text()), get(base + "vectors.bin").then((r) => r.arrayBuffer())])
        .then(([text, bytes]) => {
          words = text.trim().split("\n");
          rank = new Map(words.map((w, i) => [w, i]));
          vectors = new Int8Array(bytes);
        })
        .catch((err) => { loading = null; throw err; });
    }
    return loading;
  };

  // A word as the vocabulary has it: itself, or without a plain ending ("signs" -> "sign").
  const known = (w) => {
    for (const form of [w, w.replace(/s$/, ""), w.replace(/ies$/, "y"), w.replace(/(ing|ed)$/, ""), w.replace(/(ing|ed)$/, "e")]) {
      if (rank.has(form)) return rank.get(form);
    }
    return undefined;
  };

  const near = (a, b) => {
    let sum = 0;
    for (let k = 0, i = a * DIM, j = b * DIM; k < DIM; k++) sum += vectors[i + k] * vectors[j + k];
    return sum / FULL;
  };

  // fonts: [{id, moods: "words ...", more: "other text ..."}]. Call it after load().
  // `moods` are the words that someone chose for the font: a query is compared with them by meaning.
  // `more` is other text about the font (its name, its description). A query finds a word of it only when
  // it is the same word, and the thousand most common words of English are left out ("should", "one").
  // A font without mood words is compared by meaning with its other text.
  const prepare = (fonts) => fonts.map((f) => {
    const lead = [...new Set(tokens(f.moods))];
    const rest = [...new Set(tokens(f.more || ""))].filter((w) => !(rank.get(w) < 1000));
    const meant = lead.length ? lead : rest;
    return { id: f.id, own: new Set([...lead, ...rest]), lead: meant,
             spots: meant.map((w) => [w, rank.get(w)]).filter((p) => p[1] !== undefined) };
  });

  // The fonts in the order of how well they fit the query, each with the reason:
  // [{id, score 0..1, why: [[word of the query, mood word that answers it, how near 0..1]]}]
  const search = (query, prepared) => {
    const asked = tokens(query);
    return prepared.map((font) => {
      let total = 0, weight = 0;
      const why = [];
      for (const w of asked) {
        const at = known(w);
        // a rare word says more than a common one
        const heavy = Math.log(2 + (at === undefined ? words.length : at));
        let best = 0, by = "";
        if (font.own.has(w)) { best = 1; by = w; }
        else if (at !== undefined) {
          for (const [mood, spot] of font.spots) {
            const s = spot === at ? 1 : near(at, spot);
            if (s > best) { best = s; by = mood; }
          }
        }
        total += heavy * best;
        weight += heavy;
        if (by) why.push([w, by, best]);
      }
      return { id: font.id, score: weight ? total / weight : 0, why };
    }).sort((a, b) => b.score - a.score);
  };

  // Words to go on with: the mood words that the best results share and the query does not have.
  const branches = (query, results, prepared, most = 6) => {
    const asked = new Set(tokens(query)), seen = new Map();
    const by = new Map(prepared.map((f) => [f.id, f]));
    results.slice(0, 5).forEach((r, place) => {
      for (const w of by.get(r.id).lead) {
        if (!asked.has(w) && w.length > 3) seen.set(w, (seen.get(w) || 0) + (5 - place) * r.score);
      }
    });
    // prefer a word that is near the query but is not the same thing said again
    const spots = [...asked].map(known).filter((s) => s !== undefined);
    return [...seen.entries()].map(([w, votes]) => {
      const at = rank.get(w);
      const close = at === undefined || !spots.length ? 0 : Math.max(...spots.map((s) => near(s, at)));
      return [w, votes * (close > 0.86 ? 0.2 : 0.6 + close)];
    }).sort((a, b) => b[1] - a[1]).slice(0, most).map((p) => p[0]);
  };

  const api = { load, prepare, search, branches, tokens };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else window.FontSearch = api;
})();
