// Runs the Worker's code for votes and views (worker/src/counts.js) with SQLite in memory, and prints the
// results as JSON. tests/test_counts.py starts it with node.
import { memory, handle } from "../worker/local.js";

const counts = memory(["arroyo", "tally"]);
const origins = ["https://fonts.example", "https://freefont-*.vercel.app"];
const call = async (path, method, body, ip, origin, store = counts) => {
  const headers = { "X-Real-IP": ip };
  if (origin) headers.Origin = origin;
  const request = new Request(`https://counts.example/api/fonts/${path}`, { method, headers, body: body === undefined ? undefined : typeof body === "string" ? body : JSON.stringify(body) });
  const response = await handle(request, store, origins);
  const text = await response.text();
  return { status: response.status, cors: response.headers.get("Access-Control-Allow-Origin"), ...(text ? JSON.parse(text) : {}) };
};

const out = {};
out.first = await call("vote", "POST", { id: "arroyo", on: true }, "1.1.1.1");
out.again = await call("vote", "POST", { id: "arroyo", on: true }, "1.1.1.1");            // the same visitor: no second vote
out.other = await call("vote", "POST", { id: "arroyo", on: true }, "2.2.2.2");
out.back = await call("vote", "POST", { id: "arroyo", on: false }, "1.1.1.1");            // takes the vote back
out.backAgain = await call("vote", "POST", { id: "arroyo", on: false }, "1.1.1.1");
out.bad = await call("vote", "POST", { id: "../etc", on: true }, "1.1.1.1");
out.unknown = await call("vote", "POST", { id: "not-a-font", on: true }, "1.1.1.1");      // only a font of the library counts
out.unknownView = await call("view", "POST", { id: "not-a-font" }, "1.1.1.1");
out.get = await call("vote", "GET", undefined, "1.1.1.1");
out.broken = await call("vote", "POST", "{not json", "1.1.1.1");
out.nowhere = await call("other", "GET", undefined, "1.1.1.1");
out.view = await call("view", "POST", { id: "arroyo" }, "1.1.1.1");
out.reload = await call("view", "POST", { id: "arroyo" }, "1.1.1.1");                     // a reload is not a new view
out.viewOther = await call("view", "POST", { id: "arroyo" }, "3.3.3.3");
out.nextDay = await counts.view("1.1.1.1", "arroyo", Date.now() + 86_400_000);            // the next day it is one
// a font that is not in the library any more keeps its numbers, and the page does not get them
counts.db.prepare("INSERT INTO fonts (id, votes, views) VALUES ('left-the-library', 7, 7)").run();
out.statsOne = await call("stats", "GET", undefined, "1.1.1.1");
out.statsTwo = await call("stats", "GET", undefined, "2.2.2.2");
// the database never holds an address
const kept = JSON.stringify(["voted", "seen", "kept", "fonts"].map((table) => counts.db.prepare(`SELECT * FROM ${table}`).all()));
out.addresses = kept.includes("1.1.1.1") || kept.includes("2.2.2.2");
// which pages may ask
out.fromSite = await call("stats", "GET", undefined, "4.4.4.4", "https://fonts.example");
out.fromPreview = await call("stats", "GET", undefined, "4.4.4.4", "https://freefont-git-new-me.vercel.app");
out.fromElsewhere = await call("vote", "POST", { id: "arroyo", on: true }, "4.4.4.4", "https://elsewhere.example");
out.preflight = await call("vote", "OPTIONS", undefined, "4.4.4.4", "https://fonts.example");
// views do not use up the votes of a minute, and too many votes in a minute are refused
for (let i = 0; i < 45; i++) out.manyViews = await call("view", "POST", { id: "tally" }, "9.9.9.9");
out.voteAfterViews = await call("vote", "POST", { id: "tally", on: true }, "9.9.9.9");
for (let i = 0; i < 45; i++) out.flood = await call("vote", "POST", { id: "tally", on: i % 2 === 0 }, "9.9.9.9");
// two stores have two secrets: a mark from one says nothing in the other
out.salts = memory([]).salt() !== counts.salt() && counts.salt().length === 48;
console.log(JSON.stringify(out));
