# M3 Place, Relations, and Chapter Semantics

**Status:** `DECIDED` – effective when this decision PR is merged  
**Date:** August 26, 2026  
**Tracking:** #163  
**Affects:** M3-D06, D07, D08, D09, D10, D11, D12, D26, D28, D31

This document closes the blocking M3 decisions for Places, typed Content Relations, and Chapters. It contains only domain, persistence, API, privacy, concurrency, and test decisions. It **does not approve M3 runtime code**; the existing G2/status-sync gate rule remains unchanged.

## 1. Authoritative sources

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/SECURITY.md`
- `docs/ROADMAP.md`
- `docs/m3/README.md`
- `docs/m3/DOMAIN-MODEL.md`
- `docs/m3/API-DESIGN.md`
- `docs/m3/SECURITY-TEST-MATRIX.md`
- M3-D01 from #162: collaborative write for shared M3 planning resources

The following remain source-bound in particular:

- Place is `SPACE_SHARED` and may exist without coordinates.
- Place can be linked to Memories, HeartMoments, Milestones, Plans, and Chapters.
- Relations require real referential integrity; no uncontrolled `(targetType,targetId)` universal relation.
- Chapter groups Memories, shared HeartMoments, and Milestones.
- Chapter Delete removes relations, never original content.
- `OWNER_ONLY` must not leak indirectly through relations, counts, errors, or ordering gaps.
- exact location data must not enter logs, analytics, events, or metric labels.

## 2. M3-D06 / D28 – Place Privacy, Field Classification, and Location Leakage

### Decision

Place remains a **shared `SPACE_SHARED` object**. Both active space members may read its domain content. M3 has no per-Place visibility level.

The following are **protected domain content**:

- `name`
- `description`
- `address`
- `latitude`
- `longitude`

These fields belong to the ProtectedPayload/E2EE-readiness boundary. In version 1, `latitude`/`longitude` may exist as typed DB columns for clean validation and future provider/map extensibility; their classification remains `sensitive protected content`. The technical column representation does not make them telemetry or event data.

Technical metadata outside the ProtectedPayload boundary:

- `id`
- `spaceId`
- `createdBy`
- `createdAt`
- `updatedAt`
- `version`

### Coordinate invariants

- both coordinates are set or both are `NULL`;
- Latitude: `-90 <= latitude <= 90`;
- Longitude: `-180 <= longitude <= 180`;
- M3 persistence precision: maximum 6 decimal places;
- no automatic rounding in API responses beyond that persistence precision;
- a Place without coordinates is fully valid;
- address may exist without coordinates and coordinates may exist without an address.

### Output / privacy

An active partner in the same space receives the stored exact Place values. Non-members or IDs from other spaces receive no distinguishable existence information.

Forbidden in particular:

- coordinates in application logs;
- coordinates/address in error context;
- coordinates/address in Domain Events;
- coordinates/address in analytics or metric labels;
- automatic geocoding/reverse-geocoding calls;
- server-side provider IDs or map metadata in M3.

Maps, geocoding, current position, and provider data remain reserved for M7/M8 or a later explicit provider scope.

## 3. M3-D07 – Place Identity and Deduplication

### Decision

**No automatic or implicit deduplication.**

- every Create request creates a new Place;
- name, address, and coordinates are not unique keys;
- equal or nearly equal coordinates are not merged automatically;
- no fuzzy matching in the write path;
- a later explicit merge/duplicate UX is separate scope.

Rationale: Places with the same name or address may intentionally be separate domain objects; automatic merging would mutate data and create privacy risk.

## 4. M3-D08 / D31 – Canonical Relation Surface

### Decision

M3 uses **typed relations and direct foreign keys**, not a generic relation table.

### 4.1 Direct single-Place foreign keys

For Plans and Chapters there is exactly one canonical truth:

```text
Plan.placeId?    -> places.id
Chapter.placeId? -> places.id
```

Therefore M3 has **no** additional `place_plans` or `place_chapters` tables.

Semantics:

- a Plan has at most one primary Place;
- a Chapter has at most one primary Place;
- `placeId` is nullable;
- deleting a Place sets these FKs to `NULL` (`ON DELETE SET NULL` or equivalent transactional semantics);
- Plan/Chapter remain after Place deletion.

This decides M3-D31: `Chapter.placeId` is canonical; `place_chapters` is not introduced in parallel.

### 4.2 Place relations to existing content

M3 provides these typed many-to-many relations:

```text
place_memories
place_heart_moments
place_milestones
```

Each table contains at least:

```text
- place_id      FK places.id
- target_id     FK to concrete target type
- created_by
- created_at
UNIQUE(place_id, target_id)
```

- Place Delete removes only join rows;
- target Delete removes only affected join rows;
- original resources are never deleted with them.

Only `SHARED` HeartMoments are allowed in `place_heart_moments`.

### 4.3 Chapter relations

M3 provides:

```text
chapter_memories
chapter_heart_moments
chapter_milestones
```

Each table contains at least:

```text
- chapter_id    FK chapters.id
- target_id     FK to concrete target type
- created_by
- created_at
UNIQUE(chapter_id, target_id)
```

A target may appear in multiple Chapters; there is **no** global unique constraint on `target_id`.

### 4.4 External API

The external API is **typed**, not polymorphic.

Example form:

```text
PUT    /api/v1/spaces/{spaceId}/places/{placeId}/memories/{memoryId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/memories/{memoryId}

PUT    /api/v1/spaces/{spaceId}/places/{placeId}/heart-moments/{heartMomentId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/heart-moments/{heartMomentId}

PUT    /api/v1/spaces/{spaceId}/places/{placeId}/milestones/{milestoneId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/milestones/{milestoneId}

PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}

PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/heart-moments/{heartMomentId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/heart-moments/{heartMomentId}

PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/milestones/{milestoneId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/milestones/{milestoneId}
```

Plan/Chapter Place is set through the normal versioned update or the resource operation defined for it; no additional generic Relation Service is introduced.

## 5. M3-D09 – Relation Privacy

### Decision

A shared relation may reference only a target that is allowed as shared content for both shared space members.

In particular:

- private HeartMoments must not be bound to Place or Chapter;
- `OWNER_ONLY` targets are generally forbidden for shared relations;
- unknown, foreign, cross-space, or unreadable targets are handled identically as privacy-safe `404` during Create;
- lists/counts exclude private targets;
- an error must not distinguish whether a target exists, is private, or belongs to another space.

### HeartMoment privacy change

When changing `SHARED -> PRIVATE`, all shared relations are removed **in the same DB transaction**, before or together with the visibility change:

```text
place_heart_moments
chapter_heart_moments
```

The commit must not expose any state in which a private HeartMoment remains provable through shared relations.

A later `PRIVATE -> SHARED` change does **not** automatically reconstruct old relations.

## 6. M3-D10 – Chapter Ordering

### Decision

Chapter content has **no manually persisted order** in M3.

Presentation order is derived deterministically from linked original resources:

1. domain event date (`happenedOn`) ascending;
2. if no domain date exists: `createdAt`;
3. stable tie-breaker: resource type and UUID.

Consequences:

- no `position` column in Chapter relation tables;
- no Chapter reorder endpoint in M3;
- relation tables remain simple and fully referential;
- a later curated manual order is separate decision/migration scope.

## 7. M3-D11 – Chapter Dates

### Decision

`startOn` and `endOn` are independently optional.

Valid:

- both `NULL`;
- only `startOn`;
- only `endOn`;
- both set, when `endOn >= startOn`.

Date boundaries are not automatically derived from linked content and are not silently changed by relation updates.

## 8. M3-D12 – Chapter Delete

Source-bound and unchanged:

```text
DELETE Chapter
  -> delete Chapter itself
  -> remove chapter_memories / chapter_heart_moments / chapter_milestones
  -> preserve Memory / HeartMoment / Milestone
  -> preserve Place
```

If the Chapter has a `placeId` reference, only the Chapter is deleted; the Place remains.

## 9. Place Delete

Place Delete is allowed and has these semantics:

| Relation | Effect |
|---|---|
| `place_memories` | delete join rows |
| `place_heart_moments` | delete join rows |
| `place_milestones` | delete join rows |
| `Plan.placeId` | set to `NULL` |
| `Chapter.placeId` | set to `NULL` |
| Memory/HeartMoment/Milestone | original remains |
| Plan/Chapter | original remains |

There is no Place cascade to domain originals.

## 10. M3-D26 – Concurrency and Relation Races

### Base rule

No relation Create uses unsafe `check-then-insert` without locks/constraints.

### Relation Create

Transactional order for join relations:

```text
1. verify Membership
2. load parent space-scoped and lock FOR UPDATE
3. load target space-scoped and lock FOR UPDATE
4. re-check target privacy
5. insert UNIQUE/FK-protected join
6. write safe Outbox/audit metadata
7. commit
```

Duplicate `PUT` of the same relation is idempotent and may return the same end state without creating a second join row.

### Parent Delete vs. Relation Create

- whichever obtains the parent lock first wins;
- Delete removes parent + join rows;
- a waiting Create revalidates after acquiring the lock and returns 404/conflict without an orphaned relation.

### Target Delete vs. Relation Create

- target Delete locks the target;
- Relation Create locks parent, then target;
- if Delete wins first, Create sees no target after revalidation;
- if Create wins first, Delete waits until commit and then removes target + join row according to FK semantics.

### HeartMoment SHARED → PRIVATE vs. Relation Create

The privacy change locks the HeartMoment and removes its shared join rows in the same transaction. It does **not** then lock relation parents, avoiding a reversed parent→target lock order.

Relation Create locks parent → target. After target lock, `SHARED` is rechecked. The result is always either:

- shared + relation present, or
- private + relation absent.

A `private + relation present` state is invalid.

### Direct FK updates

`Plan.placeId` and `Chapter.placeId` use normal resource version/`If-Match` semantics and same-space Place revalidation within the same transaction.

## 11. Error codes

At minimum:

```text
PLACE_NOT_FOUND                    404
CHAPTER_NOT_FOUND                  404
MEMORY_NOT_FOUND                   404
HEART_MOMENT_NOT_FOUND             404
MILESTONE_NOT_FOUND                404
RELATION_TARGET_NOT_FOUND          404
RELATION_ALREADY_EXISTS            200/204 idempotent, no error required
RESOURCE_VERSION_CONFLICT          409
CHAPTER_DATE_RANGE_INVALID         422
PLACE_COORDINATE_PAIR_REQUIRED     422
PLACE_LATITUDE_INVALID             422
PLACE_LONGITUDE_INVALID            422
```

No dedicated cross-space/private-target error code is introduced.

## 12. Mandatory tests

### Place

- Place without coordinates is valid;
- Latitude only or Longitude only → 422;
- Latitude/Longitude boundary values;
- no automatic deduplication;
- both partners may write according to M3-D01;
- cross-tenant CRUD fail-closed;
- Place Delete removes relations, sets Plan/Chapter FK to NULL, and preserves originals.

### Relations

For every approved relation type:

- happy path;
- idempotent duplicate PUT;
- same-space FK;
- cross-space target → 404;
- deleted target → 404;
- parent Delete vs. Create race;
- target Delete vs. Create race;
- no domain-original cascade.

HeartMoment additionally:

- PRIVATE target → 404;
- SHARED → PRIVATE atomically removes Place/Chapter relations;
- Relation Create vs. privacy-change race permits no leak state;
- PRIVATE → SHARED reconstructs no old relations.

### Chapter

- date variants: empty/start-only/end-only/both;
- `endOn < startOn` → 422;
- multiple Chapters may reference the same target;
- derived ordering is stable;
- Chapter Delete preserves all original targets;
- `Chapter.placeId` is the only Chapter/Place truth.

## 13. Reuse-before-build

Not relevant for this pure domain/privacy decision. Later Maps, Geocoding, Provider, or Ranking features must again be reviewed under `docs/REUSE-BEFORE-BUILD.md` and `docs/EXTERNAL-PROVIDER-CANDIDATES.md` before building them.
