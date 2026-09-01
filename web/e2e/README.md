# Web browser QA

This package contains #192 Part A only: Playwright browser E2E and axe
accessibility checks for the Web client.

From this directory, after `npm ci`:

```bash
./node_modules/.bin/playwright install chromium
npm test
```

The Playwright configuration starts the existing Web Vite server from the
parent directory. See `docs/m5/WEB-BROWSER-QA.md` for scope and release-gate
boundaries.
