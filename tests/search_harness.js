// Runs the search of the site (site/search.js) on the real word vectors and prints the best fonts for some
// queries as JSON. tests/test_search.py starts it with node.
const fs = require("fs"), path = require("path");
const root = path.join(__dirname, "..", "site");
const search = require(path.join(root, "search.js"));
const moods = JSON.parse(fs.readFileSync(path.join(root, "search", "moods.json"), "utf8"));
const get = async (url) => {
  const data = fs.readFileSync(path.join(root, url));
  return { text: async () => data.toString("utf8"), arrayBuffer: async () => data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength) };
};
(async () => {
  await search.load("search/", get);
  const fonts = search.prepare(Object.entries(moods).map(([id, text]) => ({ id, moods: text })));
  const out = {};
  for (const q of JSON.parse(process.argv[2])) {
    const found = search.search(q, fonts);
    out[q] = { top: found.slice(0, 3).map((r) => [r.id, Number(r.score.toFixed(2))]), why: found[0].why.map((w) => [w[0], w[1]]),
               next: search.branches(q, found, fonts) };
  }
  console.log(JSON.stringify(out));
})();
