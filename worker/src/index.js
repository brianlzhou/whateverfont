// The Cloudflare Worker that counts votes and views for the library of fonts.
//
// One Durable Object holds the SQLite database (counts.js). A Durable Object runs one request at a time, so
// two votes that arrive together never lose a count. It runs on the Workers Free plan.
import { DurableObject } from "cloudflare:workers";
import { Counts, handle } from "./counts.js";
import FONTS from "../fonts.json";          // the fonts that have a page: written by scripts/build_site.py

export class Library extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.counts = new Counts(ctx.storage.sql, FONTS);
  }

  stats(address) { return this.counts.stats(address); }
  vote(address, id, on) { return this.counts.vote(address, id, on); }
  view(address, id) { return this.counts.view(address, id); }
}

export default {
  fetch(request, env) {
    const origins = String(env.ORIGINS || "").split(",").map((origin) => origin.trim()).filter(Boolean);
    return handle(request, env.LIBRARY.getByName("library"), origins);
  },
};
