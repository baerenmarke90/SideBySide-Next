# M5 Web Client Completion

- **Status:** delivery started with M5-Web-S0A
- **Parent issue:** #295
- **Current implementation issue:** #296

This package controls the staged productization of the SideBySide Next Web
client. M5 Web may progress in parallel with M4 only where the required Domain
and OpenAPI contracts are already stable on `main`. It does not change or
pre-commit open M4 contracts, and it does not declare M5 or G4 complete.

## Binding sources

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `docs/ROADMAP.md`
- `docs/IMPLEMENTATION-STATUS.md`
- `docs/DESIGN-PRINCIPLES.md`
- `docs/DESIGN-TOKEN-POLICY.md`
- `docs/ACCESSIBILITY-QA-MATRIX.md`
- `docs/CROSS-CUTTING-QUALITY.md`
- `docs/BUSINESS-MODEL.md`
- `docs/FREEMIUM-FEATURE-MATRIX.md`
- the relevant M1-M4 decisions and the authoritative generated Web client

The two independently created clickable product references supplied for this
work are visual comparison material, not a replacement for the binding product,
Privacy, Accessibility, or API contracts:

- `SideBySide-Next-clickable-demo-expanded.html`
- `SideBySide-Next-clickable-mockup.html`

## Current Web client assessment

The existing client is a sound M2 vertical reference/product flow rather than a
complete application. Its strongest foundations should be retained:

- React, React Router, TanStack Query, i18next, and the generated OpenAPI client;
- a real sign-in -> Memory/image upload -> Story flow;
- image upload orchestration with validation polling and authorized reads;
- localized product copy and locale-aware Story date grouping;
- Light, Dark, and System appearance preferences;
- semantic Story markup, focus indicators, reduced-motion behavior, and theme
  contrast tests;
- Vitest coverage for generated discriminators, uploads, Story presentation,
  i18n, theme behavior, and the real G2 client flow.

## M5 Web gap analysis

| Area | Current baseline | M5 Web gap |
| --- | --- | --- |
| Architecture | most product composition lives in one `App.tsx` | route layouts, feature boundaries, shared state/error patterns, and a scalable API composition layer |
| Navigation | only `/story` and `/memory/new` | shallow responsive product navigation, active state, Deep Links, Back behavior, and no dead links |
| Identity context | ephemeral token plus build-time reference Space ID | real session/Space context, account and relationship flows, recovery, and safe cache lifecycle |
| M1 UI | sign-in only | Space, Invitations, Profiles, Preferences, people, dates, and settings |
| M2 UI | Story plus Memory create/image upload | list/detail/update/delete, HeartMoments, Milestones, Comments, media management, filters, conflicts, and author capabilities |
| M3 UI | absent | Wishes, Plans, Places, Chapters, shared Collections, and the owner-only Private Area |
| Stable M4 UI | absent | Search, Dashboard, Activity, in-app Notifications, unread/read actions, and safe target navigation |
| Async states | local Story/form states | reusable loading, empty, error, permission, conflict, rate-limit, and offline-read patterns |
| Error handling | localized fallbacks in the M2 flow | centralized ProblemDetails mapping with Privacy-safe product copy and no raw API errors |
| Forms | native validation in one form | reusable labeling, validation summary, field association, draft retention, destructive confirmations, and 409 recovery |
| i18n | German resource with locale-aware Story dates | complete product copy coverage, long-text resilience, locale-aware dates/numbers/plurals, and future locale structure |
| Accessibility | useful foundations, no complete production audit | skip navigation, complete landmarks/focus/dialog behavior, 200% scaling, keyboard flows, browser automation through #192, and manual G4 QA |
| Responsive design | entry, Story, and Memory form adapt | shared Compact/Medium/Expanded templates and production checks at all QA matrix boundaries |
| Offline/cache | in-memory TanStack Query cache only | explicitly decided owner/Space-bound Read Cache, data age/read-only state, and complete logout/Space-change clearing |
| Portability | no Web integration | versioned Export/Import contract and UI after M2-D17 and the server contract are resolved |
| Test architecture | node-based unit/static rendering plus real G2 API E2E | routing/component coverage now; browser E2E and automated accessibility through existing issue #192 |

## Design comparison and direction

The references succeed through a restrained visual hierarchy: warm off-white
surfaces, one dominant purple action, generous spacing, serif display moments,
soft shared/private accents, shallow navigation, visible Privacy language, and
content-first cards. M5 Web adopts those qualities without copying demo-only
behavior or presenting unimplemented features.

Production adjustments are mandatory:

- navigation contains only working routes;
- decorative visuals never reduce contrast, focus visibility, text scaling, or
  content density;
- Privacy state uses text and an icon, never color alone;
- generic demo data does not become production content;
- mobile layouts remain first-class while desktop uses available space rather
  than imitating a phone frame;
- appearance uses local/system fonts and existing assets so no runtime font or
  tracking request is introduced;
- every user-visible state is localized and accessible.

## First safe slice

M5-Web-S0A (#296) is the first implementation slice. It establishes semantic
visual tokens, independently authored brand primitives, and production-quality
setup/sign-in surfaces while preserving the existing API behavior. It has no
dependency on incomplete M4 work and introduces no new Domain or commercial
contract.

The complete slice sequence and dependency rules are in
[`WEB-DELIVERY-PLAN.md`](./WEB-DELIVERY-PLAN.md).
