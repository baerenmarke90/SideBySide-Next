# M3 G3, Client, Export, and Cache Boundaries

**Status:** `DECIDED` – effective with merge of this decision PR  
**Date:** August 26, 2026  
**Tracking:** #165  
**Covers:** M3-D21, D22, D24, D25, D27, D29

This document defines early what evidence G3 requires and what is deliberately deferred to M5/G4. It contains no runtime or client code and does not change the existing M3 start condition.

## 1. Binding sources

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/ROADMAP.md`
- `docs/SECURITY.md`
- `docs/m3/README.md`
- `docs/m3/DELIVERY-PLAN.md`

Roadmap boundary:

- G3 verifies consistent Wishes/Plans/Places/Chapters/Collections, complete Private Area isolation, and understandable Delete/409 behavior.
- M5/G4 delivers complete Web/Android productization, parity, Read Cache, Export/Import, Accessibility, and Performance.

Therefore M3 must provide real Runtime/API/PostgreSQL evidence, but no premature complete client parity.

## 2. M3-D24 – G3 Evidence

### Decision

G3 is a **Domain/API/PostgreSQL gate**. Thin Web/Android reference flows are not additionally mandatory for G3. Client parity and systematic Accessibility remain M5/G4.

However, G3 requires real HTTP E2E flows against the production-like FastAPI/PostgreSQL stack, not only Unit Tests or Mock Repository tests.

### Required G3 E2E flows

At minimum these five flows must be demonstrably green on the final G3 commit:

1. **Wish -> Plan -> Complete**
   - create OPEN Wish;
   - atomically convert to Plan;
   - schedule or complete Plan;
   - source Wish and Plan consistently COMPLETED;
   - cover Retry/Race/Version Conflict.

2. **Place + Relation**
   - Place without and with coordinates;
   - at least one typed Place Relation on existing Shared Content;
   - Cross-Space/private target negative path;
   - Place Delete preserves Domain originals.

3. **Chapter + Relation + Delete**
   - create Chapter;
   - connect Memory/SHARED HeartMoment/Milestone;
   - verify deterministic derived order;
   - delete Chapter;
   - originals remain readable.

4. **Shared Collection**
   - Collection + multiple Items;
   - Completion;
   - atomic Reorder;
   - stale/concurrent Reorder -> deterministic 409;
   - Delete Cascade only to Items.

5. **Private Area Owner/Partner negative path**
   - Owner creates PrivateNote, GiftIdea, and PrivateCollection with Item;
   - Owner can read/change;
   - partner sees neither GET nor LIST/Count/Item;
   - partner mutation returns Privacy-safe non-existence semantics;
   - Logout/session switch creates no server-side leak.

### Required negative tests

G3 blocks on failures in:

- Cross-Tenant Isolation;
- OWNER_ONLY Isolation;
- Relation to private/non-readable targets;
- Wish->Plan double submit/half transactions;
- Relation/Privacy races;
- Collection Reorder consistency;
- Delete Cascades on Domain originals;
- Event/log leaks of protected content.

### Gate-blocking findings

G3 cannot pass with:

- open `Critical` or `High` Security/Privacy/Tenant Finding;
- any actual Tenant or OWNER_ONLY leak;
- data loss/Cascade of a Domain original outside documented Parent-Child semantics;
- reproducible Race producing invalid Domain state;
- missing real PostgreSQL/HTTP evidence for required flows.

### Evidence format

The final G3 review is a new dated snapshot under:

```text
docs/reviews/YYYY-MM-DD-g3-gate-review.md
```

It names final SHA, relevant PRs/Issues, workflow runs, test status, E2E results, findings, and explicit G3 result.

## 3. G3 vs M5/G4

G3 validates Domain/API/Persistence/Authorization evidence. It does not mean complete client parity, final Accessibility, final Performance, or complete Export.

M5/G4 contains:

- full Web/Android productization;
- parity;
- Read Cache;
- Export/Import;
- Deep Links;
- Accessibility acceptance;
- Client Performance Gate.

## 4. M3-D21 – Export boundary

M3 implements no Export. The later contract separates:

- Shared Space Export: only `SPACE_SHARED` content.
- Personal Export: own `OWNER_ONLY` content only.

Never export:

- partner private data;
- private counts/manifests revealing existence;
- passwords, tokens, sessions, security credentials.

Bundle/Import implementation remains M5.

## 5. M3-D22 – Client Cache

M3 introduces no persistent Private Area Offline/Read Cache.

M5 cache namespace:

```text
accountId + spaceId + privacyContext
```

For `OWNER_ONLY`:

```text
accountId + spaceId + ownerId
```

Clear on:

- Logout;
- Session revoke/re-authentication;
- Account switch;
- Space switch;
- Owner context switch;
- local reset.

Web before M5:

- no Private payloads in localStorage;
- no uncontrolled IndexedDB persistence;
- no signed URL/token cache keys.

Android Private Room Cache remains M5 scope.

## 6. M3-D25 – Private Area Information Architecture

The Private Area is a secondary personal area, not shared primary navigation.

M5 concept:

```text
More / My Area
  -> Private Notes
  -> Gift Ideas
  -> Private Lists
```

Rules:

- no private counts/badges in shared areas;
- Deep Links re-authorize server-side;
- hiding in the client is not the security boundary;
- partner cannot infer private resource quantity.

## 7. M3-D27 – Plan Richness

Not pulled into M3:

- Plan Checklist;
- Plan media;
- structured Plan notes beyond current Core.

M3 Plan remains:

```text
title
description?
status
plannedStart?
plannedEnd?
experiencedOn?
placeId?
```

Later Richness requires separate scope, model, API, Privacy, Media, and Reuse review.

## 8. M3-D29 – Collection Multi-select

Multi-select is client interaction state only:

- no `selected` column;
- no Selection table;
- no server persistence of UI selection;
- batch operations use normal Domain operations or explicit later APIs.

## 9. G3 preparation for M4

G3 requires prepared boundaries:

- M3 Events contain no ProtectedPayloads;
- OWNER_ONLY Events cannot enter Shared Activity/Dashboard;
- full-text Search remains M4-A;
- M3 creates no private Search index;
- IDs/status/Privacy classes are sufficient for controlled later Read Models.

## 10. Reuse-before-build

Not relevant for this Gate/Client boundary decision. Later Export, Cache, Deep Link, or Client technology must be reviewed again in its implementation PR.
