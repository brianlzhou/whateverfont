#!/usr/bin/env node
// Serve the built site with votes and views that work, on your own computer.
//
//     python3 scripts/build_site.py && node scripts/try_site.js [PORT]
//
// The pages come from out/site. The counts are the code of the Cloudflare Worker (worker/), with SQLite in
// memory: every count is gone when this stops. It needs Node 22.5 or newer.
//   --seed       start with some votes and views, so the "Most loved" and "Most viewed" orders show
//   --no-counts  show the pages as they are before the Worker is deployed: no vote buttons, no numbers
// A header can stand in for another visitor:  curl -H "x-real-ip: 2" -X POST -d '{"id":"arroyo"}' localhost:8788/counts/vote
const http = require("http"), fs = require("fs"), path = require("path");

const repo = path.resolve(__dirname, "..");
const root = path.join(repo, "out", "site");
const flags = process.argv.slice(2).filter((a) => a.startsWith("--"));
const port = Number(process.argv.slice(2).find((a) => /^\d+$/.test(a)) || 8788);
if (!fs.existsSync(path.join(root, "index.html"))) {
  console.error("out/site is not there. Run: python3 scripts/build_site.py");
  process.exit(1);
}
const on = !flags.includes("--no-counts");
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".woff2": "font/woff2", ".svg": "image/svg+xml", ".png": "image/png", ".txt": "text/plain; charset=utf-8",
  ".bin": "application/octet-stream", ".zip": "application/zip" };

(async () => {
  const { memory, handle } = await import(path.join(repo, "worker", "local.js"));
  const counts = memory();
  if (flags.includes("--seed")) {
    const add = counts.db.prepare("INSERT INTO fonts (id, votes, views) VALUES (?, ?, ?)");
    for (const [id, votes, views] of [["neon", 41, 912], ["kanagawa", 37, 640], ["lastbell", 28, 388], ["arroyo", 19, 1204],
      ["aviary", 12, 77], ["hopstep", 9, 51], ["pebble", 4, 0]]) add.run(id, votes, views);
  }
  http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://localhost:${port}`);
    if (on && url.pathname.startsWith("/counts/")) {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const headers = { "X-Real-IP": req.headers["x-real-ip"] || req.socket.remoteAddress || "local" };
      if (req.headers.origin) headers.Origin = req.headers.origin;
      const body = req.method === "GET" || req.method === "HEAD" ? undefined : Buffer.concat(chunks);
      const answer = await handle(new Request(url, { method: req.method, headers, body }), counts, [`http://localhost:${port}`, `http://127.0.0.1:${port}`]);
      res.writeHead(answer.status, Object.fromEntries(answer.headers));
      return res.end(await answer.text());
    }
    let file = path.join(root, decodeURIComponent(url.pathname));
    if (!file.startsWith(root)) { res.statusCode = 403; return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
      if (!url.pathname.endsWith("/")) { res.statusCode = 308; res.setHeader("Location", url.pathname + "/" + url.search); return res.end(); }
      file = path.join(file, "index.html");
    }
    if (!fs.existsSync(file)) { res.statusCode = 404; return res.end("not found"); }
    res.setHeader("Content-Type", types[path.extname(file)] || "application/octet-stream");
    if (on && file.endsWith(".html")) {
      // the pages are built for the Worker's address: here they ask this server
      return res.end(fs.readFileSync(file, "utf8").replace(/<meta name="counts" content="[^"]*">/, '<meta name="counts" content="/counts">'));
    }
    fs.createReadStream(file).pipe(res);
  }).listen(port, () => console.log(`http://localhost:${port}/library/`));
})();
