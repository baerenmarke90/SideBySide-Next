# M2 Client & QA Implementation Issues

**Status:** templates, no GitHub issues created yet  
**As of:** August 24, 2026

These packages complement the [M2 Delivery Plan](./DELIVERY-PLAN.md). They start only when the corresponding backend/OpenAPI increment is stable. One issue maps to one branch and one pull request.

## Shared PR boundaries

- no changes to auth/tenant foundations in a feature PR,
- no client-side invention of missing API fields,
- no divergent Web/Android terminology or privacy rules,
- no content in analytics, logs, or Push Preview,
- required states and demo fixtures land in the same PR as the screen,
- visual, accessibility, and privacy evidence before merge.

## C1 – Shared M2 client contracts

**Title:** `[M2][Clients] Integrate shared route, DTO, and error contracts`

**Dependencies:** published M2 OpenAPI contract, M2 domain decisions.  
**Scope:** route IDs, typed DTOs, error mapping, query keys, privacy/space-bound cache keys, test doubles.

**Acceptance**

- Web and Android generate/use the same contract.
- 401, 404, 409, 429, and 5xx are distinguished semantically.
- Cache keys contain owner/space context, never content values.
- PRIVATE is not merely a visual filter.
- Contract and fixture tests run reproducibly.

**Not included:** finished screens, a separate backend model.

## C2 – Story Timeline & Search Web

**Title:** `[M2][Web] Deliver Story Timeline, search, and detail pane`

**Dependencies:** Story Query API, C1.  
**Scope:** Compact/Medium/Expanded, month groups, filters, cursor, search, detail pane, Back/Deep Link.

**Acceptance**

- Memory, Milestone, and shared HeartMoment appear; PRIVATE never does.
- Filters/scroll/selection are restored on return.
- Cursor retry creates no duplicates.
- Keyboard, 200% zoom, and privacy-safe 404 pass.
- Web performance budgets are measured.

## C3 – Story Timeline Android

**Title:** `[M2][Android] Deliver Story Timeline, search, and detail navigation`

**Dependencies:** Story Query API, C1.  
**Scope:** Navigation Destination, month groups, filter Sheet, cursor, Deep Link, Offline Read Cache.

**Acceptance**

- TalkBack/Switch Access/back path are complete.
- Largest font does not clip required copy.
- Cache is owner/space-bound and locked after logout/change.
- PRIVATE canary is absent from UI, cache, and network projection.
- Startup/scroll performance budgets are measured.

## C4 – Memory Creator & Media Queue Web

**Title:** `[M2][Web] Deliver Memory form with secure media queue`

**Dependencies:** Memory CRUD, Attachment Lifecycle, C1.  
**Scope:** Create/Edit, `happenedOn`, multiple media items, ordering, status, Retry/Remove, shared indication.

**Acceptance**

- all media states are visible and actionable per file,
- an invalid file destroys neither text nor valid media,
- reorder is possible without drag,
- Offline Write remains unsaved,
- double submission creates no duplicate,
- 409 preserves own input.

## C5 – Memory Creator & Media Queue Android

**Title:** `[M2][Android] Deliver Memory form with Photo Picker and media status`

**Dependencies:** Memory CRUD, Attachment Lifecycle, C1.  
**Scope:** System Photo Picker, form, media tiles, Retry/Remove/Reorder, processing/network status.

**Acceptance**

- no permission request at app startup,
- TalkBack names file, status, and action,
- no Read URL or private file in Share Sheet/clipboard/backup,
- WorkManager creates no Offline Write Sync,
- draft remains in the current secure context.

## C6 – HeartMoment Privacy Flow Web & Android

**Title:** `[M2][Privacy] Deliver HeartMoment owner-only and shared UX on both clients`

**Dependencies:** HeartMoment API/policy, Attachment Parent Auth, `M2-D06`, `M2-D07`.  
**Scope:** required selection, first-share explanation, owner area, shared detail, visibility changes, cache/deep-link rules.

**Acceptance**

- no preselected visibility without a documented decision,
- PRIVATE has no comment/Story/partner action,
- partner Deep Link and all indirect paths are neutral,
- change requires online + current version,
- canary is absent from Story, search, cache, analytics, logs, Push, and export,
- privacy group is fully understandable via keyboard/TalkBack.

## C7 – Milestone Web & Android

**Title:** `[M2][Clients] Integrate a distinct Milestone flow`

**Dependencies:** Milestone CRUD, C1.  
**Scope:** Create/Edit/Detail, Story Card, date, concurrency.

**Acceptance**

- Milestone is not a Memory type flag in the client,
- distinct Story type with understandable semantics,
- no disabled Chapter/Recap future controls,
- 404/409/Offline/accessibility checked on both platforms.

## C8 – Comments & privacy-safe notification UX

**Title:** `[M2][Clients] Integrate comments and safe notification preview`

**Dependencies:** Comment API, Outbox/Notification Hook, preview decision.  
**Scope:** List/Composer/Edit/Delete according to contract, send state, retry, Deep Link from notification.

**Acceptance**

- Composer exists only on allowed shared targets,
- send state creates exactly one comment,
- parent 404 remains neutral,
- Push Preview contains no comment/title text without explicit approval,
- Notification Deep Link re-authorizes,
- screen-reader status and focus after sending are correct.

## C9 – System states, offline & conflict

**Title:** `[M2][Clients] Unify M2 system states, Offline Read, and 409 conflict`

**Dependencies:** C1 and at least one integrated M2 flow.  
**Scope:** Skeleton, Empty, Partial, Offline Cache, Offline Write Block, 401/404/409/429/5xx, draft preservation.

**Acceptance**

- State Matrix exists as visual tests for every M2 screen,
- no state leaks private counts or existence,
- Offline Write never shows success,
- 409 has no automatic last-write-wins,
- focus and input remain stable.

## C10 – M2 Accessibility & Performance Gate

**Title:** `[M2][QA] Accept accessibility and performance budgets for Web and Android`

**Dependencies:** C2–C9.  
**Scope:** keyboard, TalkBack, Switch Access, large text, contrast, motion, focus, reference measurements.

**Acceptance**

- all core flows from `DEMO-SCENARIO.md` are exercised,
- no critical WCAG/TalkBack barrier remains open,
- touch/click targets match tokens,
- performance budgets are documented; deviations have an owner and decision,
- privacy authorization is not bypassed for performance.

## C11 – M2 Privacy Abuse & Release Sign-off

**Title:** `[M2][Security] Exclude client, cache, and notification leaks before release`

**Dependencies:** backend security suite, C2–C10.  
**Scope:** canary search in DOM/cache/logs/events/Push/export, cross-tenant, revocation, Read URLs, Recents.

**Acceptance**

- all client paths relevant to `TM-01` through `TM-18` are assessed,
- private canary appears only in owner context,
- logout/space change deletes or locks caches,
- Deep Links and notifications re-authorize,
- open high/critical risks block release,
- result is documented as security/privacy acceptance.

## Recommended order

```text
C1
├── C2 ── C4 ──┐
├── C3 ── C5 ──┤
├── C6 ────────┤
├── C7 ────────┤── C9 ── C10 ── C11
└── C8 ────────┘
```

C2/C3 and C4/C5 may run in parallel by platform but share the contract, fixtures, copy, and acceptance criteria. C6 remains one shared privacy package so Web and Android do not diverge semantically.
