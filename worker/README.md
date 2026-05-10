# Cloudflare Worker — `coldbore-download`

The Cold Bore download proxy. Validates beta access codes and serves the `.dmg`/`.zip` from Cloudflare R2 via short-lived HMAC-signed URLs.

**This folder is a BACKUP copy** of what's deployed at:
https://coldbore-download.cheidt182.workers.dev

The live source-of-truth lives in the Cloudflare dashboard:
`dash.cloudflare.com → Workers & Pages → coldbore-download → Edit code`

## Files

- `coldbore-download.js` — full Worker source. Synced manually whenever the live version changes; check the dashboard's "Last deployed" timestamp if you're unsure.

## How the live deployment is configured

Visible only in the Cloudflare dashboard (never committed):

| Setting | Where | Value |
|---|---|---|
| Worker URL | dashboard | `https://coldbore-download.cheidt182.workers.dev` |
| R2 binding `BUCKET` | Worker → Bindings tab | points at the `coldbore-releases` R2 bucket |
| Encrypted env var `HMAC_SECRET` | Worker → Settings → Variables and secrets | 64-character hex string (NOT in git) |
| VALID_CODES (hardcoded in source) | this file | mirrors `app/license.py`'s `VALID_KEYS` |

## How to redeploy this Worker

1. Open the dashboard: dash.cloudflare.com → Workers & Pages → `coldbore-download` → **Edit code**.
2. Select all the existing code in the editor (Cmd+A), delete it.
3. Open `coldbore-download.js` (this folder), copy the entire contents.
4. Paste into the dashboard editor.
5. Click **Deploy**.

Changes are live within seconds.

## Disaster recovery — if the Worker gets deleted

1. Create a new Worker (Workers & Pages → Create application → Workers → Hello World).
2. Name: `coldbore-download` (preserves the URL).
3. Paste the contents of `coldbore-download.js` into the editor, deploy.
4. **Bindings tab** → add R2 bucket binding: name `BUCKET`, target `coldbore-releases`.
5. **Settings → Variables and secrets** → add encrypted secret `HMAC_SECRET`. Generate a fresh value with `python3 -c "import secrets; print(secrets.token_hex(32))"` (you don't need the old value — generating a new one just means any in-flight signed URLs immediately expire, which is at most a 5-minute disruption).

## Long-term: version-control via wrangler

The dashboard editor is fine for a hobbyist project, but if you outgrow it, install wrangler:

```sh
npm install -g wrangler
cd worker/
wrangler login        # auths via browser
wrangler init         # creates wrangler.toml — pick "Hello World" then edit
wrangler deploy       # pushes coldbore-download.js to production
```

Once that's set up, this folder becomes the actual source of truth and the dashboard editor becomes read-only.
