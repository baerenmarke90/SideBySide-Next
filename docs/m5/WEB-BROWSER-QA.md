# M5 Web Browser QA — #192 Part A

## Purpose

This document defines the automated browser and accessibility gate introduced
by #192 Part A. It verifies the production Web client in a real Chromium
browser without adding a second product runtime, API layer, router, or test
backend.

Android Compose Semantics and manual TalkBack coverage remain #192 Part B and
are explicitly outside this branch.

## Reuse-before-build decision

The gate reuses the existing Vite Web application, generated OpenAPI contract,
React Router route model, German i18n copy, and GitHub Actions Node image.

Two development-only dependencies are added in a separately locked
`web/e2e` package:

| Dependency | Version | Purpose | License |
|---|---:|---|---|
| `@playwright/test` | 1.62.1 | real Chromium navigation, keyboard, focus, viewport and history assertions | Apache-2.0 |
| `@axe-core/playwright` | 4.13.0 | WCAG-oriented automated accessibility analysis in the real browser | MPL-2.0 |

The complete transitive browser-QA graph and integrity hashes are frozen in
`web/e2e/package-lock.json`. CI installs both Web and browser-QA dependencies
with `npm ci` and audits both lock states at `high` severity.

No browser-testing dependency is shipped with the production Web bundle. No
external testing SaaS or user-data provider is introduced.

## Automated coverage

`web/e2e/tests/product-accessibility.spec.ts` covers two representative states:

1. **Compact unauthenticated entry at 320 px**
   - German document language and long product copy;
   - keyboard order from email to password to sign-in action;
   - no horizontal document overflow;
   - axe scan against WCAG 2 / 2.1 / 2.2 A and AA tags.
2. **Expanded authenticated product shell at 1440 px**
   - direct entry through the shipped legacy `/dashboard` Deep Link;
   - canonical redirect to `/today` after authentication;
   - generated-contract-shaped mock responses for sign-in, Membership,
     Dashboard and own PartnerProfile reads;
   - successful Dashboard content, not an error-state surrogate;
   - skip-link keyboard focus into `#main-content`;
   - primary navigation to `/more` and browser Back to `/today`;
   - no horizontal document overflow;
   - the same axe gate;
   - failure on any unplanned `/api/v1/**` request, so mocks cannot silently
     drift into an invented API surface.

The API is intercepted only inside the browser test. Product code continues to
use the generated OpenAPI clients unchanged.

## CI gate

`.github/workflows/web-browser-qa.yml` runs for Web changes and changes to the
gate itself. It uses the repository's existing pinned Node 22.19.0 container,
then performs:

```text
npm ci + npm audit (web)
npm ci + npm audit (web/e2e)
production Web build
Playwright-managed Chromium install
Playwright + axe tests
```

The Chromium revision is selected by the exactly pinned Playwright package.
Browser installation is test infrastructure only and is not part of the
production image.

## Local execution

From the repository root:

```bash
cd web
npm ci
cd e2e
npm ci
./node_modules/.bin/playwright install chromium
npm test
```

Playwright starts the existing Vite application automatically. To run with a
visible browser, use `npm run test:headed` from `web/e2e`.

## Manual accessibility remains a release requirement

Automated axe and Playwright checks do **not** prove complete accessibility.
Before a release is declared accessible, representative Web flows still need
manual keyboard and screen-reader verification, including focus visibility,
focus order, announcements, zoom/text scaling and behavior that automated DOM
rules cannot assess reliably.

Android TalkBack/Compose Semantics verification is not claimed by this Part A
work and remains open under #192 Part B.
