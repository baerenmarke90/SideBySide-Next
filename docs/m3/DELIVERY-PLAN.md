# M3 Delivery Plan

**Status:** S0 complete; runtime released; S1 through S5 delivered  
**As of:** August 30, 2026

## 1. Gate before runtime

This plan describes the sequence **after runtime release**.

Before the first M3 runtime commit, the current project rule requires:

1. the final G2 review on current `main` to determine `G2: PASSED` (#147),
2. #146 to synchronize the status sources and release M3,
3. the concrete runtime PR to address the production OpenAPI contract and Reuse-before-build cleanly.

Items 1 and 2 are satisfied. Item 3 remains a condition **for each runtime PR** and is not discharged by the gate.

The domain-level S0 decisions are complete: M3-D01 through M3-D32 are `DECIDED`.

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

- Place Privacy and coordinates;
- no automatic deduplication;
- typed relation surface;
- `Plan.placeId`/`Chapter.placeId` as canonical single-Place FKs;
- Relation Privacy and races;
- Chapter dates, derived ordering, and Delete.

Contract: [`decisions/PLACE-RELATIONS-CHAPTERS.md`](./decisions/PLACE-RELATIONS-CHAPTERS.md)

### #164 Collections / Private Area

- Shared Collection root/item versioning;
- atomic Reorder;
- Private ProtectedPayload;
- GiftIdea status;
- PrivateCollection schema/Auth;
- owner-scoped Private API;
- M3 Event Redaction.

Contract: [`decisions/COLLECTIONS-PRIVATE-AREA.md`](./decisions/COLLECTIONS-PRIVATE-AREA.md)

### #165 G3 / Clients / Export / Cache

- G3 as a Domain/API/PostgreSQL gate;
- five mandatory real HTTP E2E flows;
- M5/G4 boundary for clients/Accessibility/Performance;
- later Export/cache Privacy;
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
SHARED HeartMoment+---- typed Relations ----> Chapter / Place
Milestone --------+

Shared Collection
  -> CollectionItems + atomic Reorder

PrivateNote / GiftIdea / PrivateCollection
  -> OWNER_ONLY, completely separate Query/API boundary
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
- safe Events;
- PostgreSQL/HTTP/Cross-Tenant tests.

Exit:

- Wish is robust as an independent Shared Domain;
- no free status mutation can bypass the Wish->Plan contract.

Implemented. The two points left open in S1 — the first real status transition and the Plan-dependent rows of the Delete matrix — were completed in S2.

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

Implemented, including the mandatory race and rollback tests from the decision document: parallel Convert creates exactly one Plan, a failure between Plan insert and Wish transition leaves nothing behind, and Delete vs. Convert or Complete vs. Return ends deterministically without a half lifecycle.

Not included and explicitly deferred to S3: `Plan.placeId`. M3-D02 and M3-D30 name the field for Create, PATCH, and conversion; without a Place Domain it could point to nothing, and a contract with an unusable field would promise an association the server could not establish.

## 6. S3 – Place Foundation – delivered

Scope:

- Place model + migration;
- `name/description/address/latitude/longitude`;
- lat/lon as a pair, max. 6 decimal places;
- CRUD/List;
- no automatic deduplication;
- no Maps/Geocoding Provider;
- Redaction in logs/Events;
- Delete sets Plan/Chapter Place FKs to NULL and removes only Join Relations;
- add `Plan.placeId` as field, migration, and contract surface (moved from S2).

Implemented. Two execution details:

- Place Delete unlinks assigned Plans **versionedly in the service** rather than relying only on `ON DELETE SET NULL`. A Plan whose Place disappears has changed; without a new version, a partner could continue writing from a state that still shows a Place that no longer exists. The foreign key remains as the integrity boundary.
- Log Redaction became more than a Domain rule: bound parameters had previously appeared in every database error message and therefore in the application log. This affected coordinates as well as all existing ProtectedPayloads. Fixed at the engine level.

`Chapter.placeId` remains in S5 — without a Chapter Domain there is no column.

## 7. S4 – Typed Content Relations – delivered

This slice implements:

```text
place_memories
place_heart_moments
place_milestones
```

The three `chapter_*` Relations are listed in section 8 under S5 and had previously been carried here by mistake. They are not buildable in S4: the `chapters` table is created only with the Chapter Domain, so a foreign key would have no target until then. This is the same reasoning used when `Plan.placeId` was moved from S2 to S3.

Technical rules:

- real FKs + Unique Constraints;
- no free `(targetType,targetId)` polymorphism;
- Same-Space enforcement;
- SHARED HeartMoments only;
- typed REST routes;
- Relation Create locks/revalidates Parent->Target;
- Privacy transition SHARED->PRIVATE removes Relations atomically;
- Delete/Privacy races tested with PostgreSQL.

`place_plans` and `place_chapters` are not built; `Plan.placeId` and `Chapter.placeId` are canonical.

Implemented. Three execution details:

- Same-Space became a schema property rather than a service rule. The Join row carries `space_id` once, and *the same* column participates in both composite foreign keys. A Cross-Space relation is therefore not merely forbidden; it cannot be represented.
- Excluding private HeartMoments also lives in the schema. `place_heart_moments` carries the target Privacy class as part of the foreign key, with `ON UPDATE CASCADE` and a CHECK for `SPACE_SHARED`. If a moment changes to `OWNER_ONLY` without first removing its Relations, the transaction fails. The service removes them in the same transaction and therefore never hits the guard; the guard protects code paths that do not yet exist.
- `change_visibility` now locks the HeartMoment exclusively instead of merely authorizing it. Without the lock, there was a window between removing Relations and changing the class in which a concurrent Relation Create could still insert its row as shared.

## 8. S5 – Chapter – delivered

Scope:

- Chapter model + migration;
- CRUD/List;
- optional `startOn`/`endOn`, with `endOn >= startOn` when both are set;
- `placeId`;
- typed Content Relations (`chapter_memories`, `chapter_heart_moments`, `chapter_milestones`) using the same Join shape as S4;
- derived chronological presentation;
- multiple Chapters may reference the same target;
- Delete removes only Chapter + Relations.

Mandatory test:

```text
Chapter + Memory + SHARED HeartMoment + Milestone
-> DELETE Chapter
-> Relations gone
-> all originals remain readable unchanged
```

Implemented. Chapter CRUD/List is exposed through the versioned REST/OpenAPI contract with `If-Match`/409 semantics; all four decided date shapes and the invalid-range error are covered. `Chapter.placeId` is canonical and Same-Space, Place deletion detaches it versionedly, and the three typed relation families reuse the S4 integrity/privacy/locking model. Derived content ordering is computed from original resources without a persisted position. Chapter deletion removes relation rows only and preserves Memory, SHARED HeartMoment, Milestone, and Place originals.

## 9. S6 – Shared Collections

Scope:

- Collection + CollectionItem;
- `createdBy` Attribution, collaborative write;
- root version for structure/order;
- item version for Title/Completed;
- positions `0..n-1`;
- atomic full-list Reorder;
- Item Delete + compaction;
- Parent Delete cascades only Items;
- Cross-Tenant/Concurrency tests.

Not included: ShoppingList and persisted multi-select state.

## 10. S7 – PrivateNote + GiftIdea

Scope:

- separate tables/services;
- owner-only CRUD/List;
- `/spaces/{spaceId}/private/...`;
- PrivateNote title/body as Protected Content;
- GiftIdea `IDEA | BOUGHT | GIVEN`;
- no URL Preview/server Fetches;
- Privacy-safe 404;
- Event/log Redaction;
- partner negative tests.

## 11. S8 – PrivateCollection

Scope:

- PrivateCollection root with id/space/owner/version;
- Items with Parent FK, id/version/position;
- authorize owner/space exclusively through Parent;
- owner-only Reorder/Completion;
- Parent Delete cascades only Items;
- partner/Cross-Space negative tests.

Shared Collection and PrivateCollection share neither a table nor an unsafe query path.

## 12. S9 – Integrated M3 backend/API evidence

The five mandatory G3 flows are demonstrated against the real SideBySide API + PostgreSQL:

1. Wish -> Plan -> Complete;
2. Place + typed Relation + Delete;
3. Chapter + Relations + Delete without original loss;
4. Collection Completion + Reorder + Conflict;
5. PrivateNote/GiftIdea/PrivateCollection with partner negative path.

Additionally, Cross-Tenant, race, Event/log Redaction, and Delete suites run.

## 13. S10 – G3 Review

The final review is created as a new dated snapshot:

```text
docs/reviews/YYYY-MM-DD-g3-gate-review.md
```

It references the final `main` SHA, CI runs, the five E2E flows, and open findings and ends with:

```text
G3: PASSED
```

or

```text
G3: NOT PASSED
```

G3 does not require complete Web/Android reference flows. Systematic client parity, Accessibility, Read Cache, Export/Import, and Performance remain M5/G4.

## 14. Dependency graph

```text
G2 PASSED + #146
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

S3/S6/S7 may be partially parallelized after runtime release as long as their schema/migrations remain cleanly coordinated.
