# M3 API Design

**Status:** `PROPOSED` – template for later decisions and OpenAPI work  
**As of:** August 26, 2026

This file does **not** change the production OpenAPI contract. It describes a consistent target surface so the M3-S0 decisions can be made concretely against routes, DTOs, errors, and transactions.

## 1. Binding API principles

M3 adopts the existing project conventions:

- REST under `/api/v1/...`;
- all domain resources are space-scoped;
- UUIDv7 IDs;
- external JSON fields use `camelCase`;
- consistent Problem Details with stable `code`;
- membership before resource resolution;
- privacy-safe 404 for unreadable/owner-only resources;
- 403 only for known readable resources where the action is not allowed;
- mutable resources use `version`/ETag and `If-Match`;
- stale mutation -> `409 RESOURCE_VERSION_CONFLICT`;
- client authorization is never a security boundary;
- no polymorphic universal relation without a server-side target allowlist and DB foreign keys.

## 2. List and pagination convention

`PROPOSED`: growing M3 lists use the same opaque cursor convention as existing APIs.

Shared parameters where appropriate:

```text
limit
cursor
order
```

Domain filters:

- Wish: `status`, optional `createdBy`
- Plan: `status`, optional `createdBy`, optional date range
- Place: no global full-text search in M3; simple stable ordering
- Chapter: optional date range
- Collection: no global content search in M3
- Private Area: owner scope only; no partner view

A `q` parameter for global full-text search is **not part of M3**. Search belongs to M4-A.

## 3. Wish API

### Proposed routes

```text
POST   /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes/{wishId}
PATCH  /api/v1/spaces/{spaceId}/wishes/{wishId}
DELETE /api/v1/spaces/{spaceId}/wishes/{wishId}
```

Whether `PATCH` permits arbitrary status changes is explicitly **not** decided in this draft. Dedicated domain operations are preferred when a transition affects relations/transactions.

### Proposed DTO

```text
WishCreateRequest
- title

WishUpdateRequest
- title?

WishResponse
- id
- spaceId
- title
- status
- createdBy
- createdAt
- updatedAt
- version
- capabilities?
```

`capabilities` may later avoid UI guesswork (`canEdit`, `canDelete`, `canConvertToPlan`) but never replaces server authorization.

## 4. Wish -> Plan as a dedicated domain operation

Conversion is not a normal `PATCH status=PLANNED` because at least two domain objects and a relation are affected atomically.

### Proposed route

```text
POST /api/v1/spaces/{spaceId}/wishes/{wishId}/plan
If-Match: "<wish-version>"
```

Request, depending on M3-D02/D04:

```text
WishToPlanRequest
- title?          # if a title differing from the Wish title is allowed
- description?
- plannedStart?
- plannedEnd?
- placeId?
```

Response:

```text
WishToPlanResponse
- wish: WishResponse
- plan: PlanResponse
```

### Transaction contract

A successful request must, in **one commit**:

1. authorize Wish and check current version,
2. create exactly one allowed Plan or apply the idempotency decision,
3. set `sourceWishId`,
4. transition Wish to the decided successor state,
5. write safe Domain Events.

Duplicate concurrent confirmation must never create two Plans.

### Proposed error codes

```text
WISH_NOT_FOUND                  404
WISH_NOT_EDITABLE               403 or 404 according to final ownership rule
WISH_STATUS_TRANSITION_INVALID  409
WISH_ALREADY_PLANNED            409 or idempotent 200/201 – M3-D02
RESOURCE_VERSION_CONFLICT       409
PLACE_NOT_FOUND                 404
```

The exact idempotency response remains open in this draft.

## 5. Plan API

### Proposed routes

```text
POST   /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans/{planId}
PATCH  /api/v1/spaces/{spaceId}/plans/{planId}
DELETE /api/v1/spaces/{spaceId}/plans/{planId}
```

Direct `POST /plans` creates a Plan without `sourceWishId` and is not excluded by the Product Specification.

### Transition routes – proposed

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/schedule
POST /api/v1/spaces/{spaceId}/plans/{planId}/complete
POST /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
```

Why dedicated operation routes are proposed:

- status transitions may enforce date invariants;
- Completion may set `experiencedOn`;
- Return-to-Wish affects at least two resources;
- events and races are more explicit than with unrestricted `PATCH status`.

M3-D03/D04 decide which of these routes actually enter v1.

### Proposed Plan DTO

```text
PlanCreateRequest
- title
- description?
- plannedStart?
- plannedEnd?
- placeId?

PlanUpdateRequest
- title?
- description?
- plannedStart?
- plannedEnd?
- placeId?

PlanResponse
- id
- spaceId
- sourceWishId?
- title
- description?
- status
- plannedStart?
- plannedEnd?
- experiencedOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version
- capabilities?
```

Status is preferably not freely set through normal update requests.

## 6. Plan -> Wish return

### Proposed route

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
If-Match: "<plan-version>"
```

The response depends on M3-D03. Possible semantics:

- reactivate the original `sourceWishId` and preserve Plan,
- reactivate original Wish and delete Plan,
- create a new Wish and preserve Plan as history.

Until this decision is `DECIDED`, no route may be transferred into the OpenAPI contract.

## 7. Place API

### Proposed routes

```text
POST   /api/v1/spaces/{spaceId}/places
GET    /api/v1/spaces/{spaceId}/places
GET    /api/v1/spaces/{spaceId}/places/{placeId}
PATCH  /api/v1/spaces/{spaceId}/places/{placeId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}
```

### Proposed DTO

```text
PlaceCreateRequest
- name
- description?
- address?
- latitude?
- longitude?

PlaceResponse
- id
- spaceId
- name
- description?
- address?
- latitude?
- longitude?
- createdBy
- createdAt
- updatedAt
- version
```

M3 delivers **no** endpoint family such as `/geocode`, `/nearby`, `/map-search`, or provider proxy. Such surfaces require separate reuse/privacy/provider decisions later.

### Validation – proposed

- `latitude` and `longitude` only together or explicitly individually? **M3-D06**
- numeric values within geographic limits;
- coordinates are not mandatory;
- `address` is user content, not a server-validated provider record.

## 8. Content Relations API

The DB side remains typed. Two forms are possible for the external API.

### Option A – typed nested routes

```text
PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}

PUT    /api/v1/spaces/{spaceId}/places/{placeId}/plans/{planId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/plans/{planId}
```

Advantages:

- contract and authorization are very explicit,
- no uncontrolled discriminator,
- simple OpenAPI types.

Disadvantage: more routes.

### Option B – shared controlled Relation Service

```text
POST /api/v1/spaces/{spaceId}/relations
```

with a strictly enumerated union, for example:

```text
{ relation: "CHAPTER_MEMORY", chapterId, memoryId }
{ relation: "PLACE_PLAN", placeId, planId }
```

Internally still separate FK tables.

Advantage: one shared client entry point.  
Risk: must not degrade into unrestricted `targetType/targetId` polymorphism.

**M3-D08 decides A/B or a justified hybrid.**

### Relation security response

When a target belongs to another space or is `OWNER_ONLY`/unreadable:

```text
404 RELATION_TARGET_NOT_FOUND
```

No response may distinguish whether the ID exists, is private, or belongs to another space.

## 9. Chapter API

### Proposed routes

```text
POST   /api/v1/spaces/{spaceId}/chapters
GET    /api/v1/spaces/{spaceId}/chapters
GET    /api/v1/spaces/{spaceId}/chapters/{chapterId}
PATCH  /api/v1/spaces/{spaceId}/chapters/{chapterId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}
```

### Proposed DTO

```text
ChapterCreateRequest
- title
- description?
- startOn?
- endOn?
- placeId?

ChapterResponse
- id
- spaceId
- title
- description?
- startOn?
- endOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version
- relationSummary?  # safe shared counts only; M3-D10
```

A relation count must never include private targets. The simpler safe start is to count only actually relationable shared targets or initially omit counts.

Delete Chapter returns 204 and removes only Chapter + its relation entries. Original content remains.

## 10. Collection API

### Proposed routes

```text
POST   /api/v1/spaces/{spaceId}/collections
GET    /api/v1/spaces/{spaceId}/collections
GET    /api/v1/spaces/{spaceId}/collections/{collectionId}
PATCH  /api/v1/spaces/{spaceId}/collections/{collectionId}
DELETE /api/v1/spaces/{spaceId}/collections/{collectionId}

POST   /api/v1/spaces/{spaceId}/collections/{collectionId}/items
PATCH  /api/v1/spaces/{spaceId}/collections/{collectionId}/items/{itemId}
DELETE /api/v1/spaces/{spaceId}/collections/{collectionId}/items/{itemId}
```

### Reorder – proposed

Do not use a sequence of N individual `PATCH position` requests. Prefer one atomic operation:

```text
PUT /api/v1/spaces/{spaceId}/collections/{collectionId}/item-order
If-Match: "<collection-or-order-version>"

{
  "itemIds": ["...", "...", "..."]
}
```

or a rank-based single-move model. M3-D14 decides the strategy.

### Completion

`completed` may be modeled as a normal item mutation if item versioning is approved. With parent-based versioning, the whole Collection state must remain conflict-free.

## 11. Private Area routing

All routes remain space-scoped even though the current account is implicitly the owner. This keeps tenant isolation explicit and prevents an account with multiple spaces from referencing a private resource from the wrong space.

### Proposed PrivateNote

```text
POST   /api/v1/spaces/{spaceId}/private/notes
GET    /api/v1/spaces/{spaceId}/private/notes
GET    /api/v1/spaces/{spaceId}/private/notes/{noteId}
PATCH  /api/v1/spaces/{spaceId}/private/notes/{noteId}
DELETE /api/v1/spaces/{spaceId}/private/notes/{noteId}
```

### Proposed GiftIdea

```text
POST   /api/v1/spaces/{spaceId}/private/gift-ideas
GET    /api/v1/spaces/{spaceId}/private/gift-ideas
GET    /api/v1/spaces/{spaceId}/private/gift-ideas/{giftIdeaId}
PATCH  /api/v1/spaces/{spaceId}/private/gift-ideas/{giftIdeaId}
DELETE /api/v1/spaces/{spaceId}/private/gift-ideas/{giftIdeaId}
```

`status` remains domain-undefined for Create/Update until M3-D17 defines an enum.

### Proposed PrivateCollection

```text
POST   /api/v1/spaces/{spaceId}/private/collections
GET    /api/v1/spaces/{spaceId}/private/collections
GET    /api/v1/spaces/{spaceId}/private/collections/{collectionId}
PATCH  /api/v1/spaces/{spaceId}/private/collections/{collectionId}
DELETE /api/v1/spaces/{spaceId}/private/collections/{collectionId}

POST/PATCH/DELETE .../{collectionId}/items[/...]
PUT .../{collectionId}/item-order
```

### Privacy contract

Partner access to known or guessed private IDs:

```text
404 PRIVATE_RESOURCE_NOT_FOUND
```

The same safe response applies to:

- unknown ID,
- partner's private ID,
- ID from another space,
- resource after deletion.

No different `detail` text, timing-optimized existence check, or count may distinguish the cases.

## 12. ETag / If-Match

Proposed standard:

```text
ETag: "<version>"
If-Match: "<version>"
```

Required for:

- update/delete of mutable root resources,
- transition operations,
- relational reorder operations when they change root state.

For child items, M3-D14/M3-D18 must decide whether an item version or parent version protects consistency.

## 13. Error-code catalog – proposed

General:

```text
RESOURCE_VERSION_CONFLICT       409
INVALID_CURSOR                  400
RELATION_TARGET_NOT_FOUND       404  # unifies unknown/private/foreign space
RELATION_ALREADY_EXISTS         409
RELATION_NOT_FOUND              404
STATUS_TRANSITION_INVALID       409
```

There is intentionally **no** separate cross-space error code for relation targets. Foreign space, `OWNER_ONLY`/unreadable, and unknown IDs remain externally indistinguishable.

Wish:

```text
WISH_NOT_FOUND
WISH_TITLE_REQUIRED
WISH_ALREADY_PLANNED
WISH_STATUS_TRANSITION_INVALID
```

Plan:

```text
PLAN_NOT_FOUND
PLAN_TITLE_REQUIRED
PLAN_STATUS_TRANSITION_INVALID
PLAN_DATE_RANGE_INVALID
PLAN_ALREADY_COMPLETED
```

Place:

```text
PLACE_NOT_FOUND
PLACE_NAME_REQUIRED
PLACE_COORDINATES_INVALID
PLACE_IN_USE                   # only if Delete is blocked; M3-D05/D26
```

Chapter:

```text
CHAPTER_NOT_FOUND
CHAPTER_TITLE_REQUIRED
CHAPTER_DATE_RANGE_INVALID
```

Collection:

```text
COLLECTION_NOT_FOUND
COLLECTION_ITEM_NOT_FOUND
COLLECTION_TITLE_REQUIRED
COLLECTION_ORDER_INVALID
```

Private:

```text
PRIVATE_RESOURCE_NOT_FOUND
PRIVATE_NOTE_TITLE_REQUIRED
GIFT_IDEA_TITLE_REQUIRED
GIFT_IDEA_STATUS_INVALID
PRIVATE_COLLECTION_NOT_FOUND
PRIVATE_COLLECTION_ITEM_NOT_FOUND
```

The final list becomes binding only with OpenAPI/domain decisions.

## 14. Delete semantics

The API must not turn `DELETE` into a generic cascade switch. Each domain decides in advance:

- which owned child rows are deleted,
- which external relations are only removed,
- which linked originals remain,
- whether `If-Match` is required.

For Chapter, source-bound: Delete removes relations, not original content.

## 15. No server-side fetching of GiftIdea URLs

`GiftIdea.url` is a stored string in the M3 core. M3 introduces **no** URL preview, OpenGraph, screenshot, or metadata fetcher.

Reason:

- SSRF surface,
- tracking/privacy exfiltration,
- additional provider/parser/supply-chain scope.

A later preview requires a dedicated reuse/security design.

## 16. No Maps/Geocoding API in M3

`Place` is not mixed with technical endpoints for maps or search. M3 stores only domain data supplied by the user/client through the normal contract. Provider integration follows separately later.

## 17. G3 API evidence – still to decide in this draft

Before G3, it must be decided whether pure Backend/OpenAPI/PostgreSQL evidence is sufficient or whether — analogous to M2 — a thin Web/Android reference flow is required. M5 remains the complete client productization milestone.

This question is **M3-D24** and must not first appear during the Gate Review.
