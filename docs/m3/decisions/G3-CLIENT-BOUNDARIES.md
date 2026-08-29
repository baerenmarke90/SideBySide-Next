# M3 G3, Client, Export, and Cache Boundaries

**Status:** `DECIDED` – effective when this decision PR is merged  
**Date:** August 26, 2026  
**Tracking:** #165  
**Affects:** M3-D21, D22, D24, D25, D27, D29

This document defines early which evidence G3 requires and what is intentionally deferred until M5/G4. It contains no runtime or client code and does not change the existing M3 start condition.

## 1. Authoritative sources

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/ROADMAP.md`
- `docs/SECURITY.md`
- `docs/m3/README.md`
- `docs/m3/DELIVERY-PLAN.md`

Roadmap boundary:

- G3 verifies consistent Wishes/Plans/Places/Chapters/Collections, complete Private Area isolation, and understandable Delete/409 effects.
- M5/G4 deliver complete Web/Android productization, parity, Read Cache, Export/Import, accessibility, and performance.

Therefore M3 must provide real runtime/API/PostgreSQL evidence, but does not pull forward complete client parity.

## 2. M3-D24 – G3 Evidence

### Decision

G3 is a **Domain/API/PostgreSQL gate**. Thin Web/Android reference flows are not additionally mandatory for G3. Client parity and systematic accessibility remain M5/G4 scope.

G3 does, however, require real HTTP E2E flows against the production-like FastAPI/PostgreSQL stack, not only unit tests or mocked repository tests.

### Mandatory G3 E2E flows

At least these five flows must demonstrably pass on the final G3 commit:

1. **Wish → Plan → Complete**
   - create an OPEN Wish;
   - atomically convert it to a Plan;
   - schedule or spontaneously complete the Plan;
   - source Wish and Plan consistently become COMPLETED;
   - cover retry/race/version-conflict paths.

2. **Place + Relation**
   - Place without and with coordinates;
   - at least one typed Place relation to existing shared content;
   - negative cross-space/private-target path;
   - deleting the Place preserves the domain originals.

3. **Chapter + Relation + Delete**
   - create a Chapter;
   - link Memory/SHARED HeartMoment/Milestone;
   - verify deterministic derived order;
   - delete the Chapter;
   - original content remains readable.

4. **Shared Collection**
   - Collection + multiple items;
   - completion;
   - atomic reorder;
   - stale/concurrent reorder → deterministic 409;
   - delete cascade affects only items.

5. **Private Area owner/partner negative path**
   - owner creates PrivateNote, GiftIdea, and PrivateCollection with an item;
   - owner can read/change them;
   - partner sees neither GET nor LIST/count/item;
   - partner mutation returns privacy-safe non-existence semantics;
   - logout/session change creates no server-side leak.

### Mandatory negative tests

G3 is blocked by failures in:

- cross-tenant isolation;
- OWNER_ONLY isolation;
- relation to private/non-readable targets;
- Wish→Plan double-submit/partial transactions;
- relation/privacy races;
- Collection reorder consistency;
- delete cascades affecting domain originals;
- event/log leaks of protected content.

### Gate-blocking findings

G3 cannot pass while any of the following remains open:

- `Critical` or `High` security/privacy/tenant finding;
- **any actual tenant or OWNER_ONLY leak**, regardless of an otherwise assigned severity;
- data loss/cascade of a domain original outside documented parent-child semantics;
- reproducible race that creates an invalid domain state;
- missing real PostgreSQL/HTTP evidence for one of the five mandatory flows.

Medium/Low findings without a tenant/privacy leak may remain open only with a dedicated follow-up issue and explicit risk acceptance in the G3 review.

### Evidence format

The final G3 review is a **new dated document** under:

```text
docs/reviews/YYYY-MM-DD-g3-gate-review.md
```

It names at least:

- final `main` commit SHA;
- relevant PRs/issues;
- workflow run IDs;
- OpenAPI/backend/PostgreSQL test status;
- the five E2E flows with results;
- open findings with severity;
- explicitly `G3: BESTANDEN` or `G3: NICHT BESTANDEN`.

Historical gate reviews are not rewritten.

## 3. G3 vs. M5/G4

G3 is intentionally a **milestone gate**, not the final project-wide Definition of Done for an M3 feature. The Web/Android portions, Export support, and complete client product maturity required by the Product Specification are completed in M5/G4 according to the Roadmap. `G3: BESTANDEN` therefore does not mean “M3 is already a fully production-ready client feature”; it means “the M3 domain, API, persistence, authorization, and gate evidence are robust enough for the next milestone”. The project-wide DoD for these features is complete only after the later client/export portions.

### Mandatory in G3

- domain model/migration/API for M3;
- tenant/owner authorization;
- optimistic concurrency/races;
- real HTTP/PostgreSQL E2E evidence;
- privacy/security negative tests;
- current OpenAPI;
- documented Delete/409 semantics.

### Mandatory only in M5/G4

- complete Web UI for all M3 features;
- complete Android UI for all M3 features;
- systematic Web/Android parity;
- Offline Read Cache;
- Export/Import implementation;
- Deep Links;
- comprehensive accessibility acceptance;
- client performance gate.

M3 may later build small technical reference surfaces when useful for development, but they are **not a G3 requirement** and must not represent M5 as complete.

## 4. M3-D21 – Export boundary

### Decision

M3 implements **no Export**. The following privacy semantics are already binding for M5.

Conceptually there are two export contexts:

### Shared space export

Contains:

- `SPACE_SHARED` data from the space;
- jointly authorized attachments/relations according to the export contract.

Never contains:

- PrivateNote;
- GiftIdea;
- PrivateCollection/items;
- the partner's private HeartMoments;
- private counts/manifest entries that reveal their existence.

### Personal export

An authenticated account may additionally receive **its own** `OWNER_ONLY` data in a personal export.

- own PrivateNote/GiftIdea/PrivateCollection may be included;
- the partner's private data is excluded;
- owner association must remain intact in the neutral transfer format;
- manifest/checksums must not indirectly prove the partner's private resources.

The technical bundle/import implementation remains M5 scope.

## 5. M3-D22 – Client Cache

### Decision

M3 introduces **no persistent Offline/Read Cache** for the Private Area. Until M5, private data remains only in process/memory state in technical reference clients, where such a client exists at all.

For M5, the following namespace boundary is binding:

```text
accountId + spaceId + privacyContext
```

For `OWNER_ONLY`, at minimum:

```text
accountId + spaceId + ownerId
```

### Clear/isolation rules

Private cache data must be removed from the active client context on at least:

- logout;
- session revocation / re-authentication;
- account change;
- space change;
- owner-context change;
- local data deletion/reset.

### Web

Until the explicit M5 cache design:

- no Private Area payloads in `localStorage`;
- no uncontrolled persistence in IndexedDB;
- no tokens/signed URLs as persistent cache keys;
- query caches must namespace account/space/owner correctly and be cleared on logout.

### Android

A persistent Room Read Cache for the Private Area is M5 scope. Before then, no ad-hoc SharedPreferences/file persistence of private payloads.

The final encryption/retention strategy is part of the M5 security/cache review.

## 6. M3-D25 – Private Area Information Architecture

### Decision

The Private Area is a **secondary personal area**, not shared primary navigation.

Canonical client idea for M5:

```text
Mehr / Mein Bereich
  -> Private Notizen
  -> Geschenkideen
  -> Private Listen
```

Routes may internally live under a clearly personal namespace, for example:

```text
/private/notes
/private/gift-ideas
/private/collections
```

Rules:

- the UI identifies this area as personal/for the current user only;
- shared space surfaces show no private counts/badges;
- a Deep Link to a private resource re-authorizes server-side;
- hiding something in the client is never the security boundary;
- a partner must not infer the number of private resources from navigation, badges, or errors.

Exact visual navigation/label polish remains M5 scope; the security and IA boundary is decided here.

## 7. M3-D27 – Plan Richness

### Decision

**Checklist, Plan media, and additional structured Plan notes are not pulled forward into M3.**

The M3 Plan remains the source-bound core:

```text
title
description?
status
plannedStart?
plannedEnd?
experiencedOn?
placeId?
```

Therefore:

- no hidden checklist modeled as a `Collection`;
- no `PlanChecklistItem` table in M3;
- no Plan Attachment relation in M3;
- `description` is the only general free-text field in the Plan core;
- a later richness extension requires dedicated scope plus data-model, API, privacy, media, and reuse review.

M3-D27 is therefore intentionally decided as **later** and does not block an M3 runtime slice.

## 8. M3-D29 – Collection multi-select

### Decision

`Mehrfachauswahl` is **client interaction state only** in M3, not persisted domain semantics.

- no `selected` column;
- no selection table;
- selection disappears on leaving/reload according to client convention;
- later batch actions may use multiple normal domain operations or an explicit batch endpoint;
- the server stores only domain end states such as `completed`, not UI selection.

This avoids an additional sync/privacy state solely for a UI interaction.

## 9. G3 preparation for M4

G3 requires only that M4 Read Model boundaries are **prepared**:

- M3 events carry no ProtectedPayload;
- OWNER_ONLY events cannot accidentally enter shared Activity/Dashboard;
- global full-text search remains M4-A;
- M3 does not pre-build a private search index;
- IDs/status/privacy classes are sufficient for later controlled Read Models where functionally needed.

## 10. Reuse-before-build

Not relevant for this pure gate/client-boundary decision. Later Export, Cache, Deep-Link, or client implementation must again review existing libraries/platform mechanisms and security properties in the corresponding implementation PR.
