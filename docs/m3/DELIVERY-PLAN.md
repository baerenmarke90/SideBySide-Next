# M3 Delivery Plan

**Status:** S0 complete; runtime approved; S1 through S4 delivered  
**As of:** August 26, 2026

## 1. Gate before runtime

This plan describes the sequence **after runtime approval**.

Before the first M3 runtime commit, the current project rule requires:

1. the final G2 review on current `main` to state `G2: BESTANDEN` (#147),
2. #146 to synchronize status sources and approve M3,
3. the concrete runtime PR to handle the production OpenAPI contract and reuse-before-build correctly.

Items 1 and 2 are satisfied. Item 3 remains a condition **per runtime PR** and is not discharged by the gate.

The domain S0 decisions are complete: M3-D01 through M3-D32 are `DECIDED`.

## 2. S0 – complete

### #162 Wish / Plan

- collaborative write;
- atomic/idempotent Wish->Plan conversion;
- Return-to-Wish;
- Plan lifecycle and date invariants;
- Delete matrix;
- Direct Plan Create.

Contract: [`decisions/WISH-PLAN-LIFECYCLE.md`](./decisions/WISH-PLAN-LIFECYCLE.md)

### #163 Place / Relations / Chapters

- Place privacy and coordinates;
- no automatic deduplication;
- typed relation surface;
- `Plan.placeId`/`Chapter.placeId` as canonical single-Place foreign keys;
- relation privacy and races;
- Chapter dates, derived ordering, and Delete.

Contract: [`decisions/PLACE-RELATIONS-CHAPTERS.md`](./decisions/PLACE-RELATIONS-CHAPTERS.md)

### #164 Collections / Private Area

- Shared Collection root/item versioning;
- atomic reorder;
- Private ProtectedPayload;
- GiftIdea status;
- PrivateCollection schema/auth;
- owner-scoped Private API;
- M3 event redaction.

Contract: [`decisions/COLLECTIONS-PRIVATE-AREA.md`](./decisions/COLLECTIONS-PRIVATE-AREA.md)

### #165 G3 / Clients / Export / Cache

- G3 as a Domain/API/PostgreSQL gate;
- five mandatory real HTTP E2E flows;
- M5/G4 boundary for clients/accessibility/performance;
- later export/cache privacy;
- Private IA;
- Plan Richness later;
- multi-select as client state.

Contract: [`decisions/G3-CLIENT-BOUNDARIES.md`](./decisions/G3-CLIENT-BOUNDARIES.md)

## 3. Target model

```text
Wish OPEN
  -> Plan IDEA
  -> PLANNED optional
  -> COMPLETED
  -> optional Chapter

Plan --------> Place (max. one primary Place)
Chapter -----> Place (max. one primary Place)

Memory -----------+
SHARED HeartMoment+---- typed relations ----> Chapter / Place
Milestone --------+

Shared Collection
  -> CollectionItems + atomic reorder

PrivateNote / GiftIdea / PrivateCollection
  -> OWNER_ONLY, completely separate query/API boundary
```

## 4. S1 – Wish Foundation – delivered

Scope:

- Wish model + migration;
- `OPEN | PLANNED | COMPLETED`;
- title/createdBy/version;
- CRUD/List;
- collaborative write;
- `If-Match`/409;
- Tenant Guard;
- safe events;
- PostgreSQL/HTTP/cross-tenant tests.

Exit:

- Wish is robust as an independent shared domain;
- no unrestricted status mutation bypasses the Wish->Plan contract.

Delivered. The two points deliberately left open in S1 — the first real status transition and the Plan-dependent rows of the Delete matrix — were completed with S2.

## 5. S2 – Plan + Wish->Plan – delivered

Scope:

- Plan model + migration;
- `IDEA | PLANNED | COMPLETED`;
- Direct Plan Create;
- Plan CRUD/List;
- schedule/unschedule/complete;
- `sourceWishId` + Unique/FK;
- atomic Wish->Plan operation;
- Return-to-Wish;
- Wish/Plan lock order;
- race/rollback tests.

Mandatory evidence:

```text
Wish Create
-> Convert
-> exactly one Plan
-> Complete
-> Wish + Plan consistently COMPLETED
```

Delivered, including the mandatory race and rollback tests from the decision document: concurrent Convert creates exactly one Plan, a failure between Plan insert and Wish transition leaves nothing behind, and Delete vs. Convert or Complete vs. Return ends deterministically without a partial lifecycle.

Not included and explicitly assigned to S3: `Plan.placeId`. M3-D02 and M3-D30 name the field for Create, PATCH, and conversion; without the Place domain it could not point anywhere, and a contract with an unusable field would promise an association the server cannot establish.

## 6. S3 – Place Foundation – delivered

Scope:

- Place model + migration;
- `name/description/address/latitude/longitude`;
- Lat/Lon as a pair, max. 6 decimal places;
- CRUD/List;
- no automatic deduplication;
- no Maps/Geocoding provider;
- redaction in logs/events;
- Delete sets Plan/Chapter Place foreign keys to NULL and removes only join relations;
- add `Plan.placeId` as field, migration, and contract surface (moved from S2).

Delivered. Two execution details:

- Place Delete detaches assigned Plans **versioned in the service**, not only through `ON DELETE SET NULL`. A Plan whose location disappears has changed; without a new version, a partner could continue writing from a state that still shows a Place that no longer exists. The foreign key remains as the integrity boundary.
- Log redaction became more than a domain rule: bound parameters previously appeared in every database error and therefore in the application log. This affected coordinates and all existing ProtectedPayloads alike. The fix was applied at the engine boundary.

`Chapter.placeId` remains with S5 — there is no Chapter table before the Chapter domain exists.

## 7. S4 – Typed Content Relations – delivered

This slice implements:

```text
place_memories
place_heart_moments
place_milestones
```

The three `chapter_*` relations belong to S5 in section 8 and were previously listed here by mistake. They cannot be built in S4: the `chapters` table is created only with the Chapter domain, so a foreign key would have no target until then. This is the same reason `Plan.placeId` moved from S2 to S3.

Technical rules:

- real foreign keys + Unique Constraints;
- no unrestricted `(targetType,targetId)` polymorphism;
- same-space enforcement;
- SHARED HeartMoments only;
- typed REST routes;
- Relation Create locks/revalidates Parent->Target;
- privacy change SHARED->PRIVATE removes relations atomically;
- Delete/privacy races tested with PostgreSQL.

`place_plans` and `place_chapters` are not built; `Plan.placeId` and `Chapter.placeId` are canonical.

Delivered. Three execution details:

- Same-space is not merely a service rule; it is a schema property. The join row carries `space_id` once, and the *same* column participates in both composite foreign keys. A cross-space relation is therefore not just forbidden but unrepresentable.
- Exclusion of private HeartMoments is also encoded in the schema. `place_heart_moments` carries the target privacy class as part of the foreign key, with `ON UPDATE CASCADE` and a CHECK for `SPACE_SHARED`. If a moment switches to `OWNER_ONLY` without its relations being removed first, the transaction fails. The service removes them in the same transaction and never hits that barrier; the barrier protects the code path that does not exist yet.
- `change_visibility` now locks the HeartMoment exclusively instead of merely authorizing it. Without the lock, there was a window between removing relations and changing the class where a concurrent Relation Create could still insert its row as shared.

## 8. S5 – Chapter

Scope:

- Chapter model + migration;
- CRUD/List;
- optional `startOn`/`endOn`, with `endOn >= startOn` when both are set;
- `placeId`;
- typed Content Relations (`chapter_memories`, `chapter_heart_moments`, `chapter_milestones`) using the same join form as S4;
- derived chronological presentation;
- multiple Chapters may reference the same target;
- Delete removes only Chapter + relations.

Mandatory test:

```text
Chapter + Memory + SHARED HeartMoment + Milestone
-> DELETE Chapter
-> relations removed
-> all originals remain readable unchanged
```

## 9. S6 – Shared Collections

Scope:

- Collection + CollectionItem;
- `createdBy` attribution, collaborative write;
- root version for structure/order;
- item version for title/completed;
- position `0..n-1`;
- atomic full-list reorder;
- item Delete + compaction;
- parent Delete cascades only items;
- cross-tenant/concurrency tests.

Not included: ShoppingList and persisted multi-select state.

## 10. S7 – PrivateNote + GiftIdea

Scope:

- separate tables/services;
- owner-only CRUD/List;
- `/spaces/{spaceId}/private/...`;
- PrivateNote title/body as protected content;
- GiftIdea `IDEA | BOUGHT | GIVEN`;
- no URL preview/server fetches;
- privacy-safe 404;
- event/log redaction;
- partner negative tests.

## 11. S8 – PrivateCollection

Scope:

- PrivateCollection root with id/space/owner/version;
- items with parent FK, id/version/position;
- authorize owner/space exclusively through parent;
- owner-only Reorder/Completion;
- parent Delete cascades only items;
- partner/cross-space negative tests.

Shared Collection and PrivateCollection share neither a table nor an unsafe query path.

## 12. S9 – Integrated M3 Backend/API evidence

The five mandatory G3 flows are demonstrated against the real SideBySide API + PostgreSQL:

1. Wish -> Plan -> Complete;
2. Place + typed relation + Delete;
3. Chapter + relations + Delete without original-data loss;
4. Collection Completion + Reorder + Conflict;
5. PrivateNote/GiftIdea/PrivateCollection with partner negative path.

Cross-tenant, race, event/log redaction, and Delete suites also run.

## 13. S10 – G3 Review

The final review is created as a new dated snapshot:

```text
docs/reviews/YYYY-MM-DD-g3-gate-review.md
```

It references final `main` SHA, CI runs, the five E2E flows, and open findings and ends with:

```text
G3: BESTANDEN
```

or

```text
G3: NICHT BESTANDEN
```

G3 does not require complete Web/Android reference flows. Systematic client parity, accessibility, Read Cache, Export/Import, and performance remain M5/G4.

## 14. Dependency graph

```text
G2 BESTANDEN + #146
        |
        v
S1 Wish
  |
  v
S2 Plan + Conversion
  |
  +------> S3 Place
  |           |
  |           v
  |        S4 Relations
  |           |
  |           v
  |        S5 Chapter
  |
  +------> S6 Shared Collections
  |
  +------> S7 PrivateNote/GiftIdea
              |
              v
           S8 PrivateCollection

S2 + S3 + S4 + S5 + S6 + S7 + S8
              |
              v
           S9 E2E
              |
              v
           S10 G3
```

S3/S6/S7 may be partially parallelized after runtime approval as long as their schema/migrations remain cleanly coordinated.
