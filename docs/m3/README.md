# M3 Technical Readiness Package

**Status:** S0 decisions complete; runtime approved since #146, per-slice contract requirement remains  
**As of:** August 26, 2026  
**Tracking:** #159, #162, #163, #164, #165

This package prepares **M3 – Shared Life / Planning & Private Area** technically and functionally. The M3-S0 decisions are complete. Runtime code, migrations, and the production OpenAPI contract continue to be implemented only in the corresponding runtime slices.

## Gate rule

Planning was allowed before G2 completion. **Completing the M3-S0 decisions does not automatically approve M3 runtime work.**

Under the currently documented project rule, runtime work begins only when:

1. the final G2 review explicitly evaluates G2 as `BESTANDEN` (#147),
2. the subsequent status sync #146 lists M3 as an approved milestone,
3. the affected REST/OpenAPI contract is concretely contract-testable for the corresponding runtime slice.

Items 1 and 2 are satisfied: #147 ends with `G2: BESTANDEN`, and #146 lists M3 as approved. Item 3 remains a **per-slice** requirement and is fulfilled in the corresponding runtime PR.

All M3-D01 through M3-D32 are now `DECIDED`; functional S0 readiness is therefore no longer an additional blocker.

## Authoritative sources and precedence

In case of conflict, precedence is:

1. `specification/CLEAN-ROOM-MASTER-SPEC.md`
2. `specification/PRODUCT-SPEC.md`
3. `docs/SECURITY.md`
4. published OpenAPI contract
5. `docs/INFORMATION-ARCHITECTURE.md`, `docs/USER-FLOWS.md`, `docs/API-UI-CONTRACTS.md`
6. explicit `DECIDED` M3 decision documents
7. other readiness drafts in `docs/m3/`

**Important:** Older `OPEN`/`PROPOSED` wording in `DOMAIN-MODEL.md` or `API-DESIGN.md` is readiness history. For points that have since been decided, the current [Decision Log](./DECISION-LOG.md) and decision documents are binding.

## M3 scope

| Area | M3 content | Privacy basis |
|---|---|---|
| Wish | shared wishes and atomic Wish→Plan lifecycle | `SPACE_SHARED` |
| Plan | concrete planning, dates, completion, optional origin from Wish | `SPACE_SHARED` |
| Place | shared place, optional coordinates, no provider requirement | `SPACE_SHARED`, location data is sensitive |
| Content Relations | typed relations with real foreign keys | target authorization remains binding |
| Chapter | grouping of existing Memories, SHARED HeartMoments, and Milestones | `SPACE_SHARED` |
| Collection | shared list with items, completion, and atomic reorder | `SPACE_SHARED` |
| PrivateNote | private personal note | `OWNER_ONLY` |
| GiftIdea | private gift idea | `OWNER_ONLY` |
| PrivateCollection | private list and items | `OWNER_ONLY` |

Shared Planning, shared Collections, and the Private Area remain separate domain models. There is no universal table for all content.

## S0 decisions

### #162 – Wish / Plan

[`decisions/WISH-PLAN-LIFECYCLE.md`](./decisions/WISH-PLAN-LIFECYCLE.md)

Among other things, it defines:

- collaborative write;
- Wish/Plan state machines;
- atomic, idempotent Wish→Plan conversion;
- Return-to-Wish;
- Direct Plan Create;
- date invariants;
- Delete/Concurrency matrix.

### #163 – Place / Relations / Chapters

[`decisions/PLACE-RELATIONS-CHAPTERS.md`](./decisions/PLACE-RELATIONS-CHAPTERS.md)

Among other things, it defines:

- protection and precision of location data;
- no automatic Place deduplication;
- typed relation tables;
- `Plan.placeId` and `Chapter.placeId` as canonical single-Place foreign keys;
- no relations to private targets;
- derived Chapter ordering;
- relation/delete/privacy races.

### #164 – Collections / Private Area

[`decisions/COLLECTIONS-PRIVATE-AREA.md`](./decisions/COLLECTIONS-PRIVATE-AREA.md)

Among other things, it defines:

- Shared Collection write/versioning model;
- atomic reorder;
- parent-child deletion;
- ProtectedPayload boundaries of the Private Area;
- GiftIdea `IDEA | BOUGHT | GIVEN`;
- PrivateCollection root/item schema;
- owner-scoped `/private/...` API;
- redacted M3 event contract.

### #165 – G3 / Client boundaries

[`decisions/G3-CLIENT-BOUNDARIES.md`](./decisions/G3-CLIENT-BOUNDARIES.md)

Among other things, it defines:

- G3 as a Domain/API/PostgreSQL gate;
- five mandatory real HTTP E2E flows;
- full client parity/accessibility only in M5/G4;
- export/cache privacy boundaries for later implementation;
- Private Area as secondary `Mein Bereich`;
- Plan checklist/media intentionally deferred;
- multi-select as client state only.

## Additional readiness documents

- [Domain Model](./DOMAIN-MODEL.md) – original model/risk draft; decided points are governed by the decision documents
- [API Design](./API-DESIGN.md) – original API target surface; concrete operation semantics are bound by decisions and later transferred into OpenAPI
- [Decision Log](./DECISION-LOG.md) – current compact matrix of all M3-D01 through D32
- [Privacy Threat Model](./PRIVACY-THREAT-MODEL.md) – tenant, owner-only, relation, and location leaks
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md) – negative paths, races, and privacy evidence
- [Delivery Plan](./DELIVERY-PLAN.md) – vertical runtime slices after gate approval

## Do not pull forward into M3

- global full-text search / general Search Read Model – M4-A;
- Dashboard, Activity, Notifications, Reminders, and Rules – M4;
- complete Web/Android productization, parity, Read Cache, Export/Import, Deep Links, comprehensive accessibility/performance – M5/G4;
- Questions, Check-in, and Recaps – M6;
- Discovery, Shopping, Recipe, Event, and other providers – M7;
- Maps/Geocoding providers, Geofencing, Presence, and active location context – M7/M8;
- ShoppingList/ShoppingItem – separate later domain;
- real E2EE – MX;
- Video – future backlog #88;
- Plan checklist and Plan attachments – later explicit scope.

`Place` in M3 means domain + stored location data + relations, not address search, map view, or geocoding.

## Definition of Ready for an M3 runtime slice

A slice is ready when:

- [x] G2 has formally passed and M3 is approved through #146;
- [x] relevant BLOCKING decisions are `DECIDED`;
- [x] model fields, privacy class, creator/owner, and write permissions are functionally settled;
- [x] status/delete/relation/concurrency boundaries for the affected M3 core are settled;
- [ ] the production request/response/OpenAPI contract for the concrete slice is implemented or unambiguously contract-testable;
- [x] mandatory cross-tenant/privacy/race tests are specified in advance;
- [x] event payload requires no sensitive plaintext;
- [ ] reuse-before-build for technical commodity functionality is completed in the concrete runtime PR where relevant.

## G3 target

After M3 runtime, G3 requires at least:

- consistent Wishes/Plans/Places/Chapters/Collections;
- complete Private Area isolation;
- deterministic Delete/409/race effects;
- five real HTTP/PostgreSQL E2E flows according to `G3-CLIENT-BOUNDARIES.md`;
- no open High/Critical security/privacy findings and no tenant/OWNER_ONLY leak.

The final G3 review is a new dated snapshot under `docs/reviews/` and ends explicitly with `G3: BESTANDEN` or `G3: NICHT BESTANDEN`.
