# M3 Security Test Matrix

**Status:** binding readiness matrix; concrete expected values follow decisions  
**As of:** August 26, 2026

This matrix defines the minimum test classes required by an M3 slice. It does not replace slice-specific tests, but prevents tenant, owner-only, relation, or race cases from first appearing at the gate.

## 1. Test levels

| Level | Purpose |
|---|---|
| Domain Unit | state machines, validation, safe pure rules |
| PostgreSQL Integration | constraints, foreign keys, locks, races, cascades, tenant/owner queries |
| HTTP Integration | real auth/membership/API/Problem Details/ETag semantics |
| Contract/OpenAPI | DTOs, enums, error codes, generatable contract |
| Client/Gate | according to M3-D24; no implicit assumption before decision |

SQLite is not a substitute for PostgreSQL race/constraint evidence.

## 2. Shared tenant matrix

For **Wish, Plan, Place, Chapter, Collection** at minimum:

| Case | Expectation |
|---|---|
| active member, own space, GET | allowed |
| active member, own space, List | own space only |
| ID from foreign space in own path | privacy-safe 404 |
| foreign `spaceId` without membership | 404/standardized tenant response |
| mutation against foreign space | no row changed |
| Delete against foreign space | no row changed |
| cursor/filter from another space | not reusable / no foreign data |

The concrete partner-write expectation depends on M3-D01 and is added after that decision.

## 3. Wish

### CRUD / concurrency

- Create sets `createdBy` from Auth Context, not the request.
- Request cannot overwrite `createdBy`, `spaceId`, or `version`.
- Update with current version succeeds.
- stale Update -> 409, no partial change.
- stale Delete -> 409 when Delete is versioned.
- invalid status patch is not accepted as a normal Update when a transition API is chosen.

### Wish -> Plan

Mandatory cases:

1. OPEN Wish -> Plan succeeds.
2. Wish + Plan become visible in the same DB transaction.
3. failure after Plan insert and before Wish update -> complete rollback.
4. two concurrent conversions -> exactly according to M3-D02, never two disallowed Plans.
5. identical retry after successful commit -> deterministic idempotency/conflict semantics.
6. stale `If-Match` -> no Plan created.
7. Wish from foreign space -> 404.
8. Place from foreign space in conversion request -> 404, no Plan.
9. Wish Delete concurrently with conversion -> exactly one domain-valid ordering wins.

## 4. Plan

### Status

For every edge allowed by M3-D04:

- happy path,
- stale version,
- duplicate transition,
- invalid source/target combination,
- date validation,
- cross-space Place,
- partner write according to M3-D01.

For every forbidden edge, an explicit negative test.

### Completion

- `COMPLETED` sets/validates `experiencedOn` according to the decision.
- concurrent Completion is idempotent or a deterministic conflict.
- Completion vs. Return-to-Wish is serialized.
- Completion changes source Wish only according to the explicit decision; no implicit cascade.

### Return-to-Wish

After M3-D03, test:

- only allowed non-completed states,
- behavior with/without `sourceWishId`,
- no silent payload overwrite,
- Plan/Wish versions consistent,
- race with Plan Update/Delete/Complete.

## 5. Place

### Validation

- Place without coordinates is allowed.
- coordinates outside allowed limits are rejected.
- pair/null semantics according to M3-D06.
- address/description do not appear in error/audit/event logs.

### Tenant / write

- cross-space CRUD negative.
- partner write according to M3-D01.
- no automatic deduplication of similarly named Places when M3-D07 confirms this rule.

### Delete / relation

- Delete with existing relation according to M3-D05/D26.
- Delete vs. concurrent Relation Create with a real PostgreSQL race.
- no dangling FK row.

## 6. Content Relations

For **every actually approved relation type**, use the same base matrix:

| Case | Expectation |
|---|---|
| parent + target in same space, authorized | link possible |
| parent foreign space | 404 |
| target foreign space | 404 |
| target unknown | 404 |
| target owner-only/unreadable | 404, no existence disclosure |
| duplicate link | deterministic conflict/idempotency according to contract |
| unlink missing | defined safe semantics |
| target Delete | join row removed according to FK/lifecycle or Delete blocked |
| parent Delete | join row removed |
| Relation Create vs. target Delete | no phantom link |
| Relation Create vs. privacy revoke | no private link after commit |

### HeartMoment privacy race

Mandatory PostgreSQL test:

1. shared HeartMoment is `SHARED`;
2. transaction A attempts relation to Chapter/Place;
3. transaction B sets HeartMoment `PRIVATE`;
4. after both commits, no shared Read Model/relation may reveal existence of the private HeartMoment.

## 7. Chapter

### CRUD

- tenant matrix.
- `startOn/endOn` according to M3-D11.
- partner write according to M3-D01.
- stale update/delete -> 409.

### Delete invariant

Mandatory test:

1. link Chapter to Memory, shared HeartMoment, and Milestone.
2. delete Chapter.
3. join rows are removed.
4. Memory, HeartMoment, and Milestone continue to exist unchanged.
5. their versions are not incremented by Chapter Delete.
6. no Delete events for targets.

### Private target

- attempt to link a private HeartMoment ID -> safe 404.
- partner cannot infer private target inventory from Chapter count/response.

## 8. Collection / CollectionItem

### Shared ownership

After M3-D13:

- creator/partner actions positive/negative as decided,
- `createdBy` cannot be manipulated,
- cross-space parent ID.

### Completion

- item Completion with current version/parent version.
- stale Completion -> 409.
- concurrent toggle -> no lost update.

### Reorder

Mandatory cases independent of chosen strategy:

- valid complete reorder,
- unknown item ID,
- item from another Collection,
- duplicate item ID in order request,
- missing IDs when complete list is required,
- Reorder vs. item Delete,
- two concurrent Reorders,
- Reorder vs. item Create,
- no duplicate/invalid positions after commit.

### Parent Delete

After M3-D15:

- Collection Delete handles owned items as decided,
- no impact on Shopping or other domain objects,
- no orphaned items.

## 9. PrivateNote

Mandatory matrix:

| Actor | Operation | Expectation |
|---|---|---|
| Owner | create/list/get/update/delete | allowed |
| Partner in same space | list | only own Notes; never partner-owned Notes |
| Partner with foreign Note ID | get/update/delete | identical 404 |
| Account without space membership | all | 404/tenant denial |
| Owner from another space | get through wrong space | 404 |

Additionally:

- `ownerId` only from Auth Context.
- request cannot change privacy to shared.
- title/body absent from Domain Event.
- title/body absent from audit/log representation.
- stale update/delete -> 409.

## 10. GiftIdea

Same as PrivateNote plus:

- every enum value from M3-D17 tested positively,
- unknown status -> Validation Error,
- `url` is stored but triggers **no outbound HTTP request** from Backend/Worker,
- URL/recipient/occasion/priceText absent from events/logs,
- partner receives no GiftIdea counts/existence hints.

A test may store an intentionally unreachable/internal URL value and confirm that network access is not part of the operation.

## 11. PrivateCollection / PrivateCollectionItem

### Owner isolation

- owner CRUD/List.
- partner sees only their own private Collections in their private list.
- partner ID access to foreign PrivateCollection/item -> identical 404.
- item cannot be referenced from a foreign PrivateCollection.
- cross-space negative cases.

### Reorder / Completion

Same concurrency matrix as Shared Collection, plus:

- no shared position space,
- no IDs from partner inventory in conflict/validation details,
- parent-owner condition is part of every child query.

## 12. Privacy-leak matrix

For every `OWNER_ONLY` domain, test:

- GET by ID
- List
- pagination/cursor
- Count when present
- sorting
- error details
- Relation Create/Unlink
- Deep Link/API direct navigation when a client exists
- Events
- Audit
- Logs/Error Tracking
- Export later as a contract-test checkpoint
- Search later as an M4 checkpoint

Negative tests should compare not only status codes but also response body/form where existence leaks are possible.

## 13. Event/Outbox tests

For every event-producing M3 slice:

- event and domain mutation are atomic.
- rollback -> no event.
- event contains only the M3-D23 envelope.
- JSON snapshot contains no domain titles/text.
- no address/lat/lon.
- no GiftIdea URL/recipient/priceText.
- no PrivateNote/Collection titles.
- consumer retry creates no duplicate domain effect.

## 14. Delete/cascade races

Mandatory races:

- Wish Delete vs. Convert-to-Plan.
- Plan Delete vs. Complete.
- Place Delete vs. Relation Create.
- Chapter Delete vs. Relation Create.
- target Delete vs. Chapter/Place Link.
- Collection Delete vs. item Create/Reorder.
- PrivateCollection Delete vs. item Create/Reorder.

Tests must use real independent PostgreSQL transactions, not only sequential service calls.

## 15. API/OpenAPI tests

Every M3 API slice:

- generated OpenAPI deterministic,
- no unintended unrestricted string enums for status-like fields,
- `If-Match` documented,
- 409 documented,
- privacy-safe 404 documented,
- unknown-field/contract rules according to project standard,
- Web/Android generator remains functional once the client surface consumes the contract.

## 16. G3 evidence checklist

The exact gate form is decided by M3-D24. Regardless, the following server evidence should exist:

- [ ] Wish->Plan real HTTP/PostgreSQL flow including race.
- [ ] Plan lifecycle with every allowed/forbidden transition.
- [ ] Place + at least one approved relation type through the real API.
- [ ] Chapter Delete preserves all original targets.
- [ ] Collection reorder/complete concurrency.
- [ ] PrivateNote/GiftIdea/PrivateCollection owner-only negative matrix.
- [ ] Cross-space relation tests.
- [ ] Private HeartMoment cannot leak through an M3 relation.
- [ ] Events/logs contain no sensitive M3 payloads.
- [ ] OpenAPI/PostgreSQL/CI fully green.
- [ ] additional client/accessibility evidence according to M3-D24.

## 17. Merge rule

A runtime PR that introduces a new M3 domain or relation is not merge-ready if the corresponding row of this matrix is neither implemented nor demonstrably justified as not relevant.
