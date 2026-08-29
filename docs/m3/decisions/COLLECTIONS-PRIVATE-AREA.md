# M3 Collections and Private Area – Binding Decisions

**Status:** `DECIDED` – effective when this decision PR is merged  
**Date:** August 26, 2026  
**Tracking:** #164  
**Affects:** M3-D13, D14, D15, D16, D17, D18, D19, D23, D32

This document closes the blocking M3 decisions for shared Collections and the hard `OWNER_ONLY` Private Area. It contains no runtime code and does not change the existing M3 gate rule.

## 1. Authoritative sources

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/SECURITY.md`
- `docs/ROADMAP.md`
- `docs/m3/README.md`
- `docs/m3/DOMAIN-MODEL.md`
- M3-D01 from #162: collaborative write for shared M3 resources

Source-bound:

- `Collection`/`CollectionItem` are `SPACE_SHARED`.
- ShoppingList/ShoppingItem remain separate later domains.
- `PrivateNote`, `GiftIdea`, `PrivateCollection`, `PrivateCollectionItem` are `OWNER_ONLY`.
- Owner-only must be enforced server-side; partner access must not leak existence.
- mutable domain objects use optimistic concurrency.
- `GiftIdea.status` exists; its values were not previously source-bound.

## 2. M3-D13 – Collection Ownership and Shared Writes

### Decision

Shared Collections use the M3-D01 **collaborative write** rule.

Persistence:

```text
Collection
- id
- spaceId
- title
- icon?
- createdBy
- createdAt
- updatedAt
- version

CollectionItem
- id
- collectionId
- title
- completed
- position
- createdBy
- createdAt
- updatedAt
- version
```

Rules:

- `createdBy` is set server-side for root and item and remains immutable;
- both active space members may change Collection title/icon;
- both may create, rename, complete, and delete items;
- both may delete the entire Collection;
- `createdBy` is attribution/audit, not an ACL;
- ShoppingList is not modeled as a special Collection.

## 3. M3-D14 – Collection Concurrency, Versioning, and Reorder

### Two concurrency boundaries

M3 separates **item content** from **aggregate ordering**:

- `Collection.version` protects root fields and the order/structure of the item list;
- `CollectionItem.version` protects item content (`title`, `completed`).

`position` is an ordering field managed by the Collection aggregate. A reorder therefore requires the Collection version, not N independent item versions.

### Position

- integer, non-null;
- canonical contiguous `0..n-1` per Collection;
- Unique Constraint `(collection_id, position)`;
- Create appends to the end and increments `Collection.version`;
- Delete compacts positions transactionally and increments `Collection.version`.

Runtime must not violate the unique boundary during reordering through naive sequential position updates. The PostgreSQL slice therefore must either use a `DEFERRABLE` Unique Constraint until transaction end or an equivalent collision-free temporary renumbering within the same transaction. The only visible and post-commit allowed order is canonical `0..n-1`.

### Atomic reorder

```text
PUT /api/v1/spaces/{spaceId}/collections/{collectionId}/order
If-Match: "<collection-version>"

{
  "itemIds": ["...", "...", "..."]
}
```

Contract:

- request must contain **exactly** every currently existing item ID once;
- no foreign/cross-collection ID;
- lock Collection `FOR UPDATE`;
- revalidate current item set within the same transaction;
- rewrite all positions atomically;
- increment `Collection.version` exactly once;
- no visible intermediate state with duplicate/missing positions.

### Item update

```text
PATCH /collections/{collectionId}/items/{itemId}
If-Match: "<item-version>"
```

- changing title/completed increments `CollectionItem.version`;
- completion alone does not automatically change Collection order or root version.

### Item delete

Deleting an item changes the item set and therefore the order aggregate:

- lock Collection `FOR UPDATE`, then lock item;
- `If-Match` checks item version;
- delete item;
- compact positions;
- increment `Collection.version`.

A separate Collection version in the Delete request is not required: the Collection lock serializes Delete against Reorder/Add/Delete. If Delete commits first, a reorder already started with the old root version fails with `409`; if Reorder commits first, a subsequent Delete may succeed when the item version is still current and compacts the new order consistently again.

## 4. M3-D15 – Collection Delete

### Decision

`CollectionItem` is a true child of the Collection aggregate.

```text
DELETE Collection
  -> delete CollectionItems
  -> do not delete other domain resources
```

- FK `collection_items.collection_id -> collections.id` with `ON DELETE CASCADE` is allowed;
- items are not referenced outside their Collection;
- Collection Delete is versioned (`If-Match`);
- there are no hidden relations to ShoppingList or other original resources.

## 5. M3-D16 – ProtectedPayload of the Private Area

### PrivateNote

Protected content:

- `title`
- `body`

Structural owner-only metadata:

- `pinned`
- technical IDs/timestamps/version

`pinned` is not public/safe; despite structural storage it remains strictly owner-only.

### GiftIdea

Protected content:

- `title`
- `description`
- `recipient`
- `occasion`
- `targetOn`
- `priceText`
- `url`

Structural owner-only metadata:

- `status`
- `pinned`
- technical IDs/timestamps/version

Structural fields also must never be exposed to partners, shared counts, logs, or events.

`url` is stored user content only. M3 performs **no server-side fetch, preview, OpenGraph request, or redirect check**.

### PrivateCollection

Protected content:

- root `title`
- root `icon` when user-defined/domain content
- item `title`

Structural owner-only metadata:

- item `completed`
- item `position`
- technical IDs/timestamps/version

## 6. M3-D17 – GiftIdea Status

### Enum

M3 uses exactly:

```text
IDEA
BOUGHT
GIVEN
```

Initial state:

```text
IDEA
```

Allowed transitions:

```text
IDEA   -> BOUGHT
IDEA   -> GIVEN       # e.g. homemade, experience, no purchase
BOUGHT -> IDEA        # purchase reversed / correction
BOUGHT -> GIVEN
GIVEN  -> BOUGHT      # status correction only
```

Not allowed:

```text
GIVEN -> IDEA
```

For a complete reset to a new idea, create a new GiftIdea or use a deliberate two-step correction. There is no `ARCHIVED` in the M3 core; Delete/Pinning cover these basic cases.

A status change is an explicit versioned domain operation or strictly validated field update; arbitrary unknown enum values are invalid.

## 7. M3-D18 / D32 – PrivateCollection Persistence and Authorization

### Root

```text
PrivateCollection
- id
- spaceId
- ownerId
- title
- icon?
- createdAt
- updatedAt
- version
```

### Item

```text
PrivateCollectionItem
- id
- collectionId
- title
- completed
- position
- createdAt
- updatedAt
- version
```

### Owner/space persistence decision

`PrivateCollectionItem` does **not** duplicate `ownerId` and `spaceId`.

Owner/space are derived exclusively through the authorized parent. This avoids two potentially conflicting sources of truth.

Every item access therefore must semantically include at least:

```text
item
JOIN private_collection parent
  ON item.collection_id = parent.id
WHERE parent.id = :collectionId
  AND parent.space_id = :spaceId
  AND parent.owner_id = :currentAccountId
```

A direct query on `item.id` without an owner-scoped parent is forbidden.

### Private reorder

PrivateCollection uses the same concurrency model as Shared Collection:

- root version protects order/item set;
- item version protects title/completed;
- positions are contiguous `0..n-1`;
- atomic full-list reorder with the same collision-free PostgreSQL strategy;
- item Delete locks root → item, checks item version, compacts positions, and increments root version;
- owner-only.

### Delete

`PrivateCollectionItem` is parent-child and may be deleted through FK cascade when the root is deleted. No other domain resource is deleted with it.

## 8. M3-D19 – Private API

### Route namespace

Private resources remain space-scoped; owner is **always derived from Auth Context**:

```text
/api/v1/spaces/{spaceId}/private/notes
/api/v1/spaces/{spaceId}/private/gift-ideas
/api/v1/spaces/{spaceId}/private/collections
```

Examples:

```text
GET    /private/notes
POST   /private/notes
GET    /private/notes/{noteId}
PATCH  /private/notes/{noteId}
DELETE /private/notes/{noteId}

GET    /private/gift-ideas
POST   /private/gift-ideas
GET    /private/gift-ideas/{giftIdeaId}
PATCH  /private/gift-ideas/{giftIdeaId}
DELETE /private/gift-ideas/{giftIdeaId}

GET    /private/collections
POST   /private/collections
GET    /private/collections/{collectionId}
PATCH  /private/collections/{collectionId}
DELETE /private/collections/{collectionId}
```

Child routes live under the authorized parent.

Not allowed in request bodies:

```text
ownerId
spaceId
privacyClass
```

### 404 rule

For the current account, these cases must be semantically indistinguishable:

- unknown ID;
- partner's private resource;
- private resource in another space;
- item under another owner's private parent.

Response: privacy-safe `404` without confirming details.

### Lists, counts, and pagination

- lists contain only `ownerId=currentAccount`;
- counts/pagination totals are computed only **after owner filtering**;
- no shared Dashboard/Collection count mentions private resources;
- M3 builds no global private search index.

## 9. M3-D23 – Domain Events and Redaction

### Envelope

M3 freezes this minimal envelope:

```text
eventId
eventType
occurredAt
spaceId
actorId
resourceType
resourceId
resourceVersion
privacyClass
safeState?
```

### Shared resources

For `SPACE_SHARED`, `safeState` may carry only small, non-content enum/lifecycle values when a concrete consumer requires them.

### OWNER_ONLY resources

For `OWNER_ONLY`:

- `privacyClass=OWNER_ONLY`;
- `actorId` is the owner/actor;
- `safeState` defaults to `null`;
- no status, pin, count, title, URL, price, recipient, or other domain information in the event;
- consumers must explicitly handle `OWNER_ONLY` and must not create partner notifications, shared Activity, or Dashboard views from it.

### Never in events/logs

- Collection/item titles;
- PrivateNote title/body;
- GiftIdea fields including `status`, `url`, `priceText`, `recipient`;
- PrivateCollection/item titles or completion;
- Place address/coordinates;
- private counts.

## 10. Error codes

At minimum:

```text
COLLECTION_NOT_FOUND                    404
COLLECTION_ITEM_NOT_FOUND               404
COLLECTION_ORDER_CONFLICT               409
COLLECTION_ORDER_INVALID                422
PRIVATE_NOTE_NOT_FOUND                  404
GIFT_IDEA_NOT_FOUND                     404
GIFT_IDEA_STATUS_TRANSITION_INVALID     409
PRIVATE_COLLECTION_NOT_FOUND            404
PRIVATE_COLLECTION_ITEM_NOT_FOUND       404
RESOURCE_VERSION_CONFLICT               409
```

There is no error code such as `PRIVATE_RESOURCE_OWNED_BY_PARTNER`.

## 11. Mandatory tests

### Shared Collection

- both partners may write root and items;
- `createdBy` remains immutable;
- item completion with stale version → 409;
- reorder with stale Collection version → 409;
- reorder must contain exactly the current item set;
- concurrent reorder → exactly one wins;
- reorder vs. item Delete → deterministic 409/success, no duplicate positions;
- parent Delete cascades only items;
- cross-tenant CRUD/item access → fail-closed.

### PrivateNote / GiftIdea

- owner CRUD works;
- partner GET/LIST/PATCH/DELETE → privacy-safe 404/no list entry;
- foreign space ID is semantically identical;
- counts/pagination leak nothing;
- GiftIdea starts in IDEA;
- all allowed/forbidden status edges are tested;
- URL is never fetched server-side.

### PrivateCollection

- owner-only root and child;
- item query without authorized parent is impossible in service/repository;
- reorder/Delete concurrency matches Shared Collection;
- parent Delete cascades child items;
- partner learns neither parent nor item through IDs/counts/errors.

### Events

- shared events contain no ProtectedPayloads;
- private events contain no `safeState` with domain data;
- no partner notification/shared Activity from OWNER_ONLY events;
- log/error-capture tests redact private content.

## 12. Reuse-before-build

Not relevant for this pure domain/privacy decision. If later ordering/ranking requires a technical helper component, a current reuse review occurs before building it. The M3 base model requires only PostgreSQL transactions, FKs, Unique Constraints, and optimistic concurrency.
