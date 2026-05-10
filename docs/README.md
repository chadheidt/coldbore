# Cold Bore landing page

This is the public marketing/install site, served by GitHub Pages from the `docs/` folder of this repo.

## URLs

- **Default**: `https://chadheidt.github.io/coldbore/`
- **Custom domain (when set up)**: `https://coldbore.app`

## How it's served

GitHub Pages is configured (in repo Settings → Pages) to publish from the `docs/` folder of `main`. Every push to `main` that touches `docs/` causes GitHub to redeploy within ~1 minute.

## Editing

- `index.html` — single-page site. All content + styles inlined. No build step, no JavaScript framework, no dependencies.
- `assets/` — images. Add `screenshot.png` (the main hero screenshot) and update the placeholder div in `index.html`.

## Custom domain setup (when ready)

1. Buy `coldbore.app` from a registrar (Namecheap, Porkbun, Cloudflare). The .app TLD requires HTTPS — GitHub Pages handles that automatically.
2. In your DNS provider, add a CNAME record: `@` → `chadheidt.github.io` (and `www` → same).
3. In GitHub repo Settings → Pages, enter `coldbore.app` as the custom domain. Wait a few minutes for GitHub to verify.
4. Check **Enforce HTTPS** once verification completes.

## What's NOT here yet

- Real screenshot (placeholder divs say where to add)
- Beta sign-up form (could add via Formspree / Netlify Forms / similar — TBD)
- Demo video (would replace or complement the screenshot)
- Pricing page (will add when the buy flow is built)
