# M3 Wish/Plan Lifecycle – Binding Decisions

**Status:** `DECIDED` – effective when this decision PR is merged  
**Date:** August 26, 2026  
**Tracking:** #162  
**Affects:** M3-D01, M3-D02, M3-D03, M3-D04, M3-D05, M3-D30

This document closes the blocking M3 decisions for Wish and Plan. It contains only domain, API, persistence, concurrency, and test decisions. It **does not approve M3 runtime code**; the gate rule from `docs/m3/README.md` remains in effect.

## 1. Authoritative sources

The decisions build on these source-bound boundaries:

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/SECURITY.md`
- `docs/m3/README.md`
- `docs/m3/DOMAIN-MODEL.md`
- `docs/m3/API-DESIGN.md`
- `docs/m3/SECURITY-TEST-MATRIX.md`

The following are source-bound in particular:

- Wish is `SPACE_SHARED` with `OPEN | PLANNED | COMPLETED`.
- Plan is `SPACE_SHARED` with `IDEA | PLANNED | COMPLETED`.
- `Plan.sourceWishId` is optional.
- Wish -> Plan -> Completed -> optional Chapter is intended.
- a non-completed source-bound Plan can be returned to the Wish state.
- mutable resources use Version/`If-Match`; conflicts return HTTP 409.
- cross-tenant access remains privacy-safe.

## 2. M3-D01 – Shared Write Ownership

### Decision

For the shared M3 domains **Wish, Plan, Place, Chapter, and Collection**, the base rule is **collaborative write**:

- both active space members may create, read, and — where the relevant domain state permits it — change and delete shared resources;
- `createdBy` is attribution/audit, **not** an ACL;
- `createdBy`, `spaceId`, and technical ownership fields are not client-overwritable;
- domain-specific state, delete, or relation rules may block a concrete mutation despite active membership;
- missing membership, foreign space, or foreign resource ID remains privacy-safe according to the existing tenant convention.

This rule does **not** change author-only rules of other domains such as Memory. It applies only to the named collaborative M3 planning/list resources.

### Wish/Plan specifically

- both partners may change the Wish title regardless of who created the Wish;
- both partners may change Plan title, description, and Place assignment;
- status fields are never set through normal PATCH;
- Wish and Plan remain separate domain objects after conversion: changing the Wish title does not automatically synchronize the Plan title, and vice versa;
- `createdBy` remains unchanged.

### API/audit consequence

- no creator-only 403 for Wish/Plan;
- forbidden lifecycle actions are domain conflicts (`409`), not permission errors;
- clients may display `capabilities`, but only the server decides whether a mutation is allowed;
- Audit/Event records actor ID, resource ID, timestamp, action, and result, but no domain titles/descriptions.

## 3. Wish lifecycle – binding derivation from D02/D03/D04

Wish has exactly this state machine:

```text
OPEN
  | convert-to-plan
  v
PLANNED
  | plan complete
  v
COMPLETED

PLANNED -- return-to-wish --> OPEN
```

Binding rules:

- `OPEN -> PLANNED` only through the atomic Wish->Plan operation;
- `PLANNED -> OPEN` only through `return-to-wish` on the originating Plan;
- `PLANNED -> COMPLETED` only through completion of the originating Plan;
- `COMPLETED` is terminal for the state machine;
- there is no direct Wish-complete route;
- there is no unrestricted Wish status PATCH;
- normal title corrections remain versioned content updates and do not change status.

## 4. M3-D02 – Wish -> Plan cardinality, atomicity, and idempotency

### Decision

A Wish may have **at most one originating Plan at a time**.

Persistence:

- `Plan.sourceWishId` is nullable;
- when set, it references a Wish in the same space;
- `sourceWishId` is unique;
- a returned Plan is deleted, allowing the same Wish to be converted later into a new Plan.

### Operation

```text
POST /api/v1/spaces/{spaceId}/wishes/{wishId}/plan
If-Match: "<wish-version>"
```

Request:

```text
WishToPlanRequest
- title?        # optional Plan title; default = current Wish title
- description?
- placeId?
```

Not client-settable:

```text
sourceWishId
status
createdBy
spaceId
version
plannedStart
plannedEnd
experiencedOn
```

First successful call:

```text
201 Created
WishToPlanResponse
- wish
- plan
```

The operation creates:

```text
Wish.status       = PLANNED
Plan.status       = IDEA
Plan.sourceWishId = Wish.id
```

### Idempotent retry

If the Wish is already `PLANNED` and exactly one originating Plan exists, another Convert call returns the same Plan:

```text
200 OK
WishToPlanResponse
- same wish
- same plan
```

The retry **never** creates a second Plan. A differing request does not overwrite the already existing Plan; further changes occur through the Plan itself.

If the Wish is already `COMPLETED`, another conversion is not a retry and returns a domain conflict.

### Transaction flow

Within one PostgreSQL transaction:

1. verify active membership;
2. load the Wish space-scoped and lock it `FOR UPDATE`;
3. check for an existing originating Plan;
4. for `PLANNED` + existing Plan, idempotently return that same Plan;
5. for `OPEN`, check `If-Match`;
6. validate optional `placeId` as same-space/authorized;
7. create Plan with `sourceWishId=wish.id`, status `IDEA`, and its own version;
8. set Wish to `PLANNED` and increment its version;
9. write safe Outbox/audit metadata;
10. commit exactly once.

A rollback at any point leaves neither a Plan nor a partial Wish transition.

### Race contract

Two concurrent Convert requests for the same OPEN Wish deterministically result in:

- exactly one Plan in the database;
- one request creates the Plan;
- the second waits on the Wish lock and then receives the same originating Plan as an idempotent response;
- the DB unique constraint is the final integrity boundary.

## 5. M3-D03 – Plan -> Wish return

### Decision

`return-to-wish` is allowed only for **non-completed originating Plans**:

- `sourceWishId != null`;
- Plan status `IDEA` or `PLANNED`;
- source Wish is `PLANNED`.

A Direct Plan without `sourceWishId` cannot be “returned” to a Wish. The user must explicitly create a new Wish instead.

### Semantics

The return operation:

1. reactivates **the same original Wish** with status `OPEN`;
2. increments the Wish version;
3. deletes the non-completed Plan;
4. removes only Plan-owned relation/join rows;
5. never deletes Place, Chapter, or other domain original resources;
6. does **not** automatically copy Plan title, description, or Plan dates back into the Wish.

This avoids silent overwriting of diverged ProtectedPayloads. Plan-specific data is discarded by the explicitly chosen return operation; the UI must explain this destructive consequence before confirmation.

### Operation

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
If-Match: "<plan-version>"
```

Response:

```text
200 OK
PlanReturnToWishResponse
- wish
- removedPlanId
```

The Plan is no longer readable under its ID afterward.

## 6. M3-D04 – Plan lifecycle and date invariants

### Binding state machine

```text
IDEA -- schedule --> PLANNED
IDEA -- complete --> COMPLETED
PLANNED -- unschedule --> IDEA
PLANNED -- complete --> COMPLETED
```

Allowed:

- `IDEA -> PLANNED`
- `PLANNED -> IDEA`
- `IDEA -> COMPLETED`
- `PLANNED -> COMPLETED`

Forbidden:

- every transition from `COMPLETED` to another status;
- freely setting `status` through normal `PATCH`;
- status self-transitions as dedicated operations.

`return-to-wish` is **not a Plan status edge**, but a separate domain operation under M3-D03 that removes the Plan and reactivates the Wish.

### Time semantics

For the runtime slice:

- `plannedStart`: `TIMESTAMPTZ`, optional;
- `plannedEnd`: `TIMESTAMPTZ`, optional;
- `experiencedOn`: `DATE`, optional outside COMPLETED, required for COMPLETED.

Invariants:

- `plannedEnd` may be set only when `plannedStart` is set;
- when both are set: `plannedEnd >= plannedStart`;
- `IDEA` has no binding schedule: `plannedStart = null`, `plannedEnd = null`;
- `PLANNED` requires `plannedStart`; `plannedEnd` remains optional;
- `COMPLETED` requires `experiencedOn`;
- `experiencedOn` must not be in the future relative to the acting account's local calendar day;
- completion from `PLANNED` preserves planned times as history;
- completion from `IDEA` is allowed for spontaneous experiences and requires no planned times.

### Lifecycle operations

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/schedule
POST /api/v1/spaces/{spaceId}/plans/{planId}/unschedule
POST /api/v1/spaces/{spaceId}/plans/{planId}/complete
```

All require `If-Match`.

`schedule`:

```text
- plannedStart   # required
- plannedEnd?    # optional
```

- on `IDEA`: status becomes `PLANNED`;
- on `PLANNED`: schedule is updated with versioning, status remains `PLANNED`.

`unschedule`:

- only on `PLANNED`;
- sets status `IDEA`;
- clears `plannedStart/plannedEnd`.

`complete`:

```text
- experiencedOn # required
```

For a source-bound Plan, completion additionally sets the original Wish from `PLANNED` to `COMPLETED` and increments its version in the same transaction. A Direct Plan creates or changes no Wish.

### Normal PATCH

`PATCH Plan` must not set `status`. It may change non-lifecycle domain fields, in particular:

- `title`
- `description`
- `placeId`

A `COMPLETED` Plan may still be changed with versioning for domain corrections; this does **not** reopen its status. `experiencedOn` may be corrected on a Completed Plan with versioning as long as the date is not in the future.

## 7. M3-D05 – Delete semantics

### Base rule

Delete removes only the selected aggregate and its own join/child rows. No operation deletes Place, Chapter, Memory, or another domain original resource as a side effect.

### Wish matrix

| Wish state | Originating Plan | DELETE Wish |
|---|---|---|
| `OPEN` | no | allowed, `204` |
| `OPEN` | yes | inconsistent state -> `409`, no mutation |
| `PLANNED` | yes | blocked; use active Plan or `return-to-wish` |
| `PLANNED` | no | integrity violation -> `409`, no mutation |
| `COMPLETED` | yes | blocked while originating Plan exists |
| `COMPLETED` | no | allowed, `204` |

A completed lifecycle can therefore be removed completely by explicitly deleting the completed Plan first and then the remaining completed Wish. There is no hidden Wish -> Plan cascade.

### Plan matrix

| Plan type/status | DELETE Plan |
|---|---|
| Direct Plan (`sourceWishId=null`), `IDEA` | allowed |
| Direct Plan, `PLANNED` | allowed |
| Direct Plan, `COMPLETED` | allowed |
| Source Plan, `IDEA` | blocked; use `return-to-wish` |
| Source Plan, `PLANNED` | blocked; use `return-to-wish` |
| Source Plan, `COMPLETED` | allowed; source Wish remains `COMPLETED` |

When deleting a Plan:

- Plan relation/join rows are removed;
- referenced Places/Chapters/other originals remain;
- a completed source Wish remains and can then be deleted separately.

## 8. M3-D30 – Direct Plan Create

### Decision

A Plan may be created without a Wish because `sourceWishId` is source-bound optional.

Direct Create **always** creates a Plan with:

```text
sourceWishId   = null
status         = IDEA
plannedStart   = null
plannedEnd     = null
experiencedOn  = null
```

Request:

```text
PlanCreateRequest
- title        # required
- description?
- placeId?
```

Not allowed in the Create request:

```text
sourceWishId
status
plannedStart
plannedEnd
experiencedOn
createdBy
spaceId
version
```

A Direct Plan is scheduled only through `/schedule` or spontaneously completed through `/complete`.

## 9. API contract – binding operation form

Wish:

```text
POST   /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes/{wishId}
PATCH  /api/v1/spaces/{spaceId}/wishes/{wishId}
DELETE /api/v1/spaces/{spaceId}/wishes/{wishId}
POST   /api/v1/spaces/{spaceId}/wishes/{wishId}/plan
```

Plan:

```text
POST   /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans/{planId}
PATCH  /api/v1/spaces/{spaceId}/plans/{planId}
DELETE /api/v1/spaces/{spaceId}/plans/{planId}
POST   /api/v1/spaces/{spaceId}/plans/{planId}/schedule
POST   /api/v1/spaces/{spaceId}/plans/{planId}/unschedule
POST   /api/v1/spaces/{spaceId}/plans/{planId}/complete
POST   /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
```

Status fields are read-only in normal PATCH requests.

## 10. Stable error codes

At minimum:

```text
WISH_NOT_FOUND                    404
PLAN_NOT_FOUND                    404
PLACE_NOT_FOUND                   404
RESOURCE_VERSION_CONFLICT         409
WISH_STATUS_TRANSITION_INVALID    409
WISH_ALREADY_COMPLETED            409
WISH_HAS_ACTIVE_PLAN              409
WISH_HAS_COMPLETED_PLAN           409
WISH_PLAN_STATE_CONFLICT          409
PLAN_STATUS_TRANSITION_INVALID    409
PLAN_SOURCE_WISH_REQUIRED         409
PLAN_HAS_SOURCE_WISH              409
PLAN_SCHEDULE_START_REQUIRED      422
PLAN_DATE_RANGE_INVALID           422
PLAN_EXPERIENCED_ON_REQUIRED      422
PLAN_EXPERIENCED_ON_IN_FUTURE     422
```

Unreadable/foreign resources remain privacy-safe 404. No separate cross-space error code is introduced.

## 11. DB constraints and locking

At minimum:

- FK `plans.source_wish_id -> wishes.id`;
- same-space enforcement for `(source_wish_id, space_id)` through a composite integrity boundary or an equivalently robust DB safeguard;
- `UNIQUE(source_wish_id)`; PostgreSQL permits multiple `NULL` values for Direct Plans;
- check: `plannedEnd IS NULL OR plannedStart IS NOT NULL`;
- check: `plannedEnd IS NULL OR plannedEnd >= plannedStart`;
- status/date invariants additionally in the domain service and, where useful, as DB checks.

When Wish and source Plan are affected together, the canonical lock order is:

```text
Wish -> Plan
```

A Plan service may first resolve the Plan ID without locking, but must then lock the source Wish and afterward lock/revalidate the Plan again in the same transaction. This order applies to Completion, Return, and source-bound Delete checks.

Concurrency principles:

- `DELETE Wish`, `DELETE Plan`, Convert, Return, Schedule, Unschedule, and Complete use `If-Match`;
- stale mutation -> `409 RESOURCE_VERSION_CONFLICT`;
- Delete vs. Convert/Complete/Return is decided deterministically through locks + FK/Unique + revalidation;
- no race may leave a `PLANNED` Wish without an originating Plan or create a second originating Plan.

## 12. Mandatory PostgreSQL/HTTP tests

### Shared writes / tenant

- both active partners can change/delete Wish/Plan according to domain state;
- `createdBy` remains immutable;
- Wish and Plan titles may be changed independently;
- account without membership / ID from another space -> no data mutation, privacy-safe error;
- stale `If-Match` -> 409.

### Wish lifecycle

- Create -> `OPEN`;
- no unrestricted status PATCH;
- OPEN -> PLANNED only through Convert;
- PLANNED -> OPEN only through Return;
- PLANNED -> COMPLETED only through source Plan Completion;
- COMPLETED has no status reverse edge.

### Wish -> Plan

- OPEN Wish -> 201 + exactly one Plan + Wish PLANNED;
- Plan starts in IDEA;
- identical retry while PLANNED -> 200 with same Plan ID;
- differing retry does not overwrite existing Plan;
- two concurrent Convert requests -> exactly one Plan;
- failure between Plan insert and Wish update -> complete rollback;
- stale OPEN Wish -> 409 and no Plan;
- COMPLETED Wish -> 409;
- foreign `placeId` -> 404 and no Plan.

### Plan lifecycle

Test happy path + stale version for every allowed edge.

Explicit negative tests:

- `COMPLETED -> IDEA` forbidden;
- `COMPLETED -> PLANNED` forbidden;
- PLANNED without `plannedStart` forbidden;
- `plannedEnd < plannedStart` forbidden;
- future `experiencedOn` forbidden;
- completion from IDEA allowed;
- completion from PLANNED allowed and preserves planned times;
- reschedule PLANNED -> PLANNED changes only schedule + version;
- unschedule clears planned times.

### Source Wish completion

- source Plan Complete -> Plan COMPLETED + Wish COMPLETED in one commit;
- failure after either mutation -> complete rollback;
- concurrent Complete/Return/Delete -> deterministic result without a partial lifecycle.

### Return-to-Wish

- source IDEA/PLANNED -> Wish OPEN + Plan deleted;
- Direct Plan -> 409;
- COMPLETED source Plan -> 409;
- Plan payload is not automatically copied back into Wish;
- Plan join rows disappear, original targets remain.

### Delete

Every row of the Wish/Plan Delete matrix receives an HTTP and PostgreSQL test. Additionally:

- Delete vs. Convert;
- Delete vs. Complete;
- Delete vs. Return;
- no original-resource cascade;
- after deleting a completed source Plan, Wish remains COMPLETED and separately deletable.

## 13. Privacy/telemetry consequence

Wish and Plan titles/descriptions do not belong in logs, analytics, error context, or Domain Event payloads. Technical IDs, actor, space, version, event type, and safe status values are allowed according to the later-finalized M3-D23.

## 14. Consequence for M3-S1/S2

After the M3 runtime approval defined in the repository, Wish/Plan runtime slices may build on this contract. The following remain outside this decision scope:

- Place field classification and relation details (#163),
- Collections/Private Area (#164),
- G3/client/export/cache boundaries (#165),
- global search,
- Plan checklist/attachments,
- complete Web/Android productization.
