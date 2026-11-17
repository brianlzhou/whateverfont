// The counts on your own computer: the same code as the Worker, with SQLite in memory (node:sqlite, Node 22.5
// or newer). The tests use it (tests/counts_harness.mjs), and so does scripts/try_site.js. Every count is gone
// when the process stops.
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { Counts } from "./src/counts.js";

export { handle } from "./src/counts.js";

// A Counts like the one in the Durable Object. `fonts` defaults to the list that the site's build wrote.
export function memory(fonts) {
  const db = new DatabaseSync(":memory:");
  const sql = { exec: (query, ...values) => { const rows = db.prepare(query).all(...values); return { toArray: () => rows }; } };
  const names = fonts === undefined ? JSON.parse(readFileSync(new URL("./fonts.json", import.meta.url), "utf8")) : fonts;
  return Object.assign(new Counts(sql, names), { db });
}
