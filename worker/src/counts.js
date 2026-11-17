// The votes and views of the library's fonts, in one small SQLite database.
//
// On Cloudflare the database is the storage of a Durable Object (index.js). In the tests and in
// scripts/try_site.js it is SQLite in memory (local.js). Nothing else is needed: no outside database, no key.
//
// What is kept:
//   fonts   one row for each font: its votes and its views
//   voted   one row for each vote: the mark of a visitor and the font, so a visitor has one vote for a font
//           and can take it back
//   seen    the day a visitor last opened a font's page, so a reload does not count as a new view
//   kept    a secret made once, for the marks
// The mark of a visitor is a hash of the address the request came from, with the secret. The address itself
// is never kept.

export const ID = /^[a-z0-9][a-z0-9-]{0,59}$/;
const DAY = 86_400_000;
const hex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");

export class Counts {
  // sql: exec(query, ...values) gives { toArray() }, as the SQLite of a Durable Object does.
  // fonts: the names of the fonts that have a page. A vote or a view for any other name is refused.
  constructor(sql, fonts) {
    this.sql = sql;
    this.fonts = fonts ? new Set(fonts) : null;
    this.rate = new Map();          // the mark of a visitor -> [minute, votes in that minute]
    sql.exec("CREATE TABLE IF NOT EXISTS fonts (id TEXT PRIMARY KEY, votes INTEGER NOT NULL DEFAULT 0, views INTEGER NOT NULL DEFAULT 0)");
    sql.exec("CREATE TABLE IF NOT EXISTS voted (who TEXT NOT NULL, font TEXT NOT NULL, PRIMARY KEY (who, font))");
    sql.exec("CREATE TABLE IF NOT EXISTS seen (who TEXT NOT NULL, font TEXT NOT NULL, day INTEGER NOT NULL, PRIMARY KEY (who, font))");
    sql.exec("CREATE TABLE IF NOT EXISTS kept (name TEXT PRIMARY KEY, value TEXT NOT NULL)");
  }

  known(id) {
    return typeof id === "string" && ID.test(id) && (!this.fonts || this.fonts.has(id));
  }

  rows(query, ...values) {
    return this.sql.exec(query, ...values).toArray();
  }

  // The secret of the marks. It is made the first time and stays in the database.
  salt() {
    if (!this.secret) {
      const row = this.rows("SELECT value FROM kept WHERE name = 'salt'")[0];
      this.secret = row ? row.value : hex(crypto.getRandomValues(new Uint8Array(24)));
      if (!row) this.sql.exec("INSERT INTO kept (name, value) VALUES ('salt', ?)", this.secret);
    }
    return this.secret;
  }

  async mark(address) {
    const bytes = new TextEncoder().encode(`${this.salt()}|${address || "unknown"}`);
    return hex(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)).slice(0, 12));
  }

  // The votes and views of every font, and the fonts that this visitor voted for.
  async stats(address) {
    const who = await this.mark(address), fonts = {};
    for (const row of this.rows("SELECT id, votes, views FROM fonts")) {
      // a font that left the library keeps its numbers here, and the page does not get them
      if (this.known(row.id)) fonts[row.id] = { votes: Math.max(0, Number(row.votes)), views: Number(row.views) };
    }
    const mine = this.rows("SELECT font FROM voted WHERE who = ? ORDER BY font", who).map((row) => row.font);
    return { fonts, mine: mine.filter((id) => this.known(id)) };
  }

  // Give a font a vote, or take it back with on = false. The answer is the font's new count.
  async vote(address, id, on, now = Date.now()) {
    if (!this.known(id)) return { status: 400, error: "no such font" };
    const who = await this.mark(address);
    // nobody presses a vote button more than 40 times a minute
    const minute = Math.floor(now / 60_000), spent = this.rate.get(who);
    const presses = spent && spent[0] === minute ? spent[1] + 1 : 1;
    if (this.rate.size > 20_000) this.rate.clear();
    this.rate.set(who, [minute, presses]);
    if (presses > 40) return { status: 429, error: "too many votes in a minute" };
    // the visitor's own row says whether this vote is new, or was there to take back
    const step = on === false
      ? -this.rows("DELETE FROM voted WHERE who = ? AND font = ? RETURNING font", who, id).length
      : this.rows("INSERT INTO voted (who, font) VALUES (?, ?) ON CONFLICT DO NOTHING RETURNING font", who, id).length;
    const row = step
      ? this.rows("INSERT INTO fonts (id, votes) VALUES (?, MAX(?, 0)) ON CONFLICT (id) DO UPDATE SET votes = MAX(votes + ?, 0) RETURNING votes", id, step, step)[0]
      : this.rows("SELECT votes FROM fonts WHERE id = ?", id)[0];
    return { id, votes: row ? Number(row.votes) : 0, voted: on !== false };
  }

  // Count one view of a font's page. A visitor counts once a day for a font.
  async view(address, id, now = Date.now()) {
    if (!this.known(id)) return { status: 400, error: "no such font" };
    const who = await this.mark(address), day = Math.floor(now / DAY);
    if (day !== this.day) {
      this.sql.exec("DELETE FROM seen WHERE day < ?", day);       // the days before are of no use any more
      this.day = day;
    }
    const fresh = this.rows(
      "INSERT INTO seen (who, font, day) VALUES (?, ?, ?) ON CONFLICT (who, font) DO UPDATE SET day = excluded.day " +
      "WHERE seen.day <> excluded.day RETURNING day", who, id, day).length;
    const row = fresh
      ? this.rows("INSERT INTO fonts (id, views) VALUES (?, 1) ON CONFLICT (id) DO UPDATE SET views = views + 1 RETURNING views", id)[0]
      : this.rows("SELECT views FROM fonts WHERE id = ?", id)[0];
    return { id, views: row ? Number(row.views) : 0 };
  }
}

// May a page of this origin ask? A request with no origin (curl, a server) may. A pattern can hold "*" for
// one part of a host name: "https://freefont-*.vercel.app".
export function allowed(origin, origins) {
  if (!origin) return true;
  return origins.some((pattern) => {
    if (!pattern.includes("*")) return pattern === origin;
    const parts = pattern.split("*").map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&"));
    return new RegExp(`^${parts.join("[a-z0-9-]*")}$`).test(origin);
  });
}

// The three addresses: GET .../stats, POST .../vote {"id": "arroyo", "on": true}, POST .../view {"id": "arroyo"}.
// `store` is a Counts, or the stub of the Durable Object that holds one. Only the last part of the path
// counts, so the Worker can sit under any route.
export async function handle(request, store, origins = []) {
  const origin = request.headers.get("Origin"), may = allowed(origin, origins);
  const headers = { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", Vary: "Origin" };
  if (origin && may) headers["Access-Control-Allow-Origin"] = origin;
  const send = (status, data) => new Response(JSON.stringify(data), { status, headers });
  if (request.method === "OPTIONS") {
    return new Response(null, { status: may ? 204 : 403, headers: { ...headers, "Access-Control-Allow-Methods": "GET, POST",
      "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400" } });
  }
  if (!may) return send(403, { error: "this site may not ask" });
  const what = new URL(request.url).pathname.replace(/\/+$/, "").split("/").pop();
  // Cloudflare sets the first header itself. The second is for a server on your own computer.
  const address = request.headers.get("CF-Connecting-IP") || request.headers.get("X-Real-IP") || "";
  try {
    if (what === "stats") {
      return request.method === "GET" ? send(200, await store.stats(address)) : send(405, { error: "use GET" });
    }
    if (what !== "vote" && what !== "view") return send(404, { error: "not found" });
    if (request.method !== "POST") return send(405, { error: "use POST" });
    const text = await request.text();
    let sent = null;
    try { sent = text.length <= 2000 ? JSON.parse(text) : null; } catch { sent = null; }
    if (!sent || typeof sent !== "object") return send(400, { error: "send JSON" });
    const result = what === "vote" ? await store.vote(address, sent.id, sent.on) : await store.view(address, sent.id);
    return result.error ? send(result.status, { error: result.error }) : send(200, result);
  } catch (err) {
    return send(500, { error: "the counts did not answer" });
  }
}
