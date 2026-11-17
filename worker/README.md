# The counts: votes and views

This Cloudflare Worker counts the votes and the views of the fonts in the library. It keeps them in the
SQLite storage of one Durable Object, so there is no outside database and no key to keep. It runs on the
Workers Free plan.

| Address | What it does |
|---|---|
| `GET .../stats` | The votes and views of every font, and the fonts that this visitor voted for. |
| `POST .../vote` with `{"id": "arroyo", "on": true}` | Gives a font a vote. `"on": false` takes it back. One visitor has one vote for a font. |
| `POST .../view` with `{"id": "arroyo"}` | Counts one view of a font's page. A visitor counts once a day for a font. |

A visitor is a hash of the address that the request came from, with a secret that the Worker makes once.
The address itself is never kept. Only the fonts in `fonts.json` count: `scripts/build_site.py` writes that
file. Only the pages named in `ORIGINS` (`wrangler.jsonc`) may ask.

## Try it on your computer

```sh
python3 scripts/build_site.py && node scripts/try_site.js --seed
```

That serves the site with the same code and SQLite in memory. To run the Worker itself on Cloudflare's
local runtime:

```sh
cd worker && npx --yes wrangler@4.128.0 dev
curl http://localhost:8787/api/fonts/stats
curl -X POST -d '{"id":"arroyo","on":true}' http://localhost:8787/api/fonts/vote
```

## Deploy

```sh
cd worker
npx --yes wrangler@4.128.0 login
npx --yes wrangler@4.128.0 deploy
```

The route in `wrangler.jsonc` is `www.brianzhou.org/api/fonts/*`. Only requests to that path reach the
Worker. To use another address, change the route there and `COUNTS_ADDRESS` in `scripts/build_site.py`:
a test checks that the two agree.

Then turn the counts on in the site: set `COUNTS = COUNTS_ADDRESS` in `scripts/build_site.py`, and build and
deploy the site. Until then the pages ask for nothing, and they show no vote buttons and no numbers.

Deploy the Worker again when the library gets a new font, so that the new font can get votes: the build of
the site writes the new name into `fonts.json`.
