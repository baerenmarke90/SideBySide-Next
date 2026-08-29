# M3 Domain Model

**Status:** readiness draft; source-bound statements and open decisions are separated  
**As of:** August 26, 2026

## 1. Principles

M3 extends the modular monolith with clearly separated domain areas. It does **not** create a shared `items`/`content` table.

Shared invariants:

- shared resources belong to exactly one `space_id`;
- every access starts with active membership in that space;
- mutable resources have a `version` for optimistic concurrency;
- creator/owner IDs are set server-side from the Authorization Context and are not transferred through normal updates;
- domain content is not duplicated into logs, analytics, or Domain Event payloads;
- `OWNER_ONLY` is enforced in the data query, not through client filters;
- relations must never bypass authorization of the target;
- cross-space relations are invalid;
- Shared and Private remain separate domains. Private storage is not modeled through a `visibility` flag on Wish/Plan/Collection.

## 2. Privacy and ownership matrix

| Domain | Source-bound visibility | Owner/author field | Write rule |
|---|---|---|---|
| Wish | `SPACE_SHARED` | `createdBy` | **OPEN – M3-D01** |
| Plan | `SPACE_SHARED` | `createdBy` | **OPEN – M3-D01** |
| Place | `SPACE_SHARED` | `createdBy` | **OPEN – M3-D01** |
| Chapter | shared space content | `createdBy` | **OPEN – M3-D01** |
| Collection | `SPACE_SHARED` | add `createdBy`? **OPEN – M3-D13** | **OPEN – M3-D13** |
| CollectionItem | inherits Collection | `createdBy` according to Master Spec | **OPEN – M3-D13** |
| PrivateNote | `OWNER_ONLY` | `ownerId` | owner-only, server-side |
| GiftIdea | `OWNER_ONLY` | `ownerId` | owner-only, server-side |
| PrivateCollection | `OWNER_ONLY` | `ownerId` | owner-only, server-side |
| PrivateCollectionItem | inherits PrivateCollection / owner | not fully specified | owner-only; exact persistence **OPEN – M3-D18** |

Private Area models should reuse the existing central owner/privacy authorization. Whether every model directly carries `PrivateResourceMixin` or child items are loaded exclusively through the authorized parent is decided per table; there must not be a second, weaker private-authorization path.

## 3. Wish

### Source-bound model

```text
Wish
- id
- spaceId
- title
- createdBy
- createdAt
- updatedAt
- version
- status: OPEN | PLANNED | COMPLETED
```

The source defines no free `description`/`body` field. M3 therefore does not silently assume one.

### Source-bound behavior

- Wish is shared space content.
- Users can search, filter, sort, and see progress of Wishes; global full-text search itself belongs to the later Search milestone.
- A Wish can become the starting point for a Plan.

### Still to decide

- partner write/delete rights relative to the creator.
- whether `PLANNED` may arise only from a successful Wish->Plan transaction.
- whether `COMPLETED` without a Plan is valid or may be reached only through a completed Plan.
- deleting a Wish with an existing `sourceWishId` Plan.
- whether a Wish remains editable after Plan conversion and which fields stay synchronized — preferably **no automatic content coupling** after conversion.

## 4. Plan

### Source-bound model

```text
Plan
- id
- spaceId
- sourceWishId?
- title
- description?
- status: IDEA | PLANNED | COMPLETED
- plannedStart?
- plannedEnd?
- experiencedOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version
```

### Source-bound workflow

```text
Wish
  -> Plan
  -> COMPLETED / experienced
  -> optional Chapter
```

A non-completed Plan may generally be returned to a Wish state. Exact semantics are still open in this readiness draft.

### State machine – proposed form

```text
IDEA --------> PLANNED --------> COMPLETED
  \               |
   \--------------/
        before completion
        controlled return to Wish
```

The diagram is `PROPOSED`. In particular, it remains to decide:

- whether `PLANNED -> IDEA` is allowed as a normal Plan state transition,
- whether “return to Wish” deletes, archives, or preserves the Plan as history,
- whether a `COMPLETED` Plan can be reopened,
- which combinations of `plannedStart`, `plannedEnd`, `experiencedOn`, and status are valid.

### Date invariants – proposal, not yet binding

- `plannedEnd >= plannedStart` when both are set;
- `COMPLETED` requires `experiencedOn` or an explicit decision why it is valid without a date;
- `IDEA` may exist without a schedule;
- `PLANNED` may require at least one domain planning indicator — a mandatory schedule has not yet been decided in this draft.

## 5. Atomic Wish -> Plan conversion

The User Flow specification requires conversion to be understandable and domain-transactional. This yields the following readiness requirement:

```text
lock/read Wish in space
  -> authorize
  -> validate current version/status
  -> create exactly one Plan with sourceWishId
  -> update Wish status/relation
  -> emit safe events
  -> commit once
```

The exact idempotency strategy remains open in this readiness draft. Possible approaches:

1. Unique Constraint on `(space_id, source_wish_id)` – simple if a Wish may have at most one active/originating Plan.
2. explicit Idempotency Key – more general, but additional infrastructure/semantics.
3. serialized row-lock transaction plus Unique Constraint – preferred candidate if 1:1 cardinality is approved.

The decision is M3-D02. Duplicate confirmation must never create two domain-equivalent Plans.

## 6. Plan -> Wish return

The Product Specification allows a non-completed Plan to be returned. It is **not specified** in this readiness draft whether:

- the original Wish is reactivated,
- a new Wish is created,
- the Plan is preserved/archived/deleted,
- Plan changes already made are copied back into the Wish.

This semantic is BLOCKING (M3-D03). An implementation must not improvise it as `DELETE Plan + PATCH Wish`.

## 7. Place

### Source-bound model

```text
Place
- id
- spaceId
- name
- description?
- address?
- latitude?
- longitude?
- createdBy
- createdAt/updatedAt
- version
```

### Invariants

- coordinates are optional.
- a Place without coordinates is valid.
- M3 does not require a Maps/Geocoding provider to deliver Place as a domain feature.
- Places can be linked to Memories, HeartMoments, Milestones, Plans, and Chapters.

### Sensitive location data

`latitude`, `longitude`, free description, and potentially address can reveal sensitive information about whereabouts. Therefore M3 already requires:

- no precise location data in logs, analytics, event payloads, or metric labels;
- no server-side URL/provider enrichment in this milestone;
- partner access only through normal space authorization;
- classification as ProtectedPayload or another specifically protected field is **BLOCKING – M3-D06/M3-D28**.

### Deduplication

Automatic Place deduplication is not source-bound. A name or coordinate is not a stable global identifier. The preferred safe starting point is **no implicit merging**; a final decision is M3-D07.

## 8. Content Relations

### Source-bound architecture

A shared Relation Service may exist externally. Internally, real foreign keys and typed relation tables should be used. A universal relation

```text
targetType
targetId
```

without referential integrity is excluded.

The Master Spec names in particular:

```text
chapter_memories
chapter_heart_moments
chapter_milestones

place_memories
place_heart_moments
place_milestones
place_plans
place_chapters
```

### Security invariants

A relation may be created only when:

1. the actor has active membership in the space,
2. relation parent and target belong to the same space,
3. the actor may read the target,
4. the actor may change the relation on the parent,
5. the target combination is allowed by the domain.

A shared Chapter or Place must **not reveal OWNER_ONLY existence**. A private HeartMoment therefore must not be visible or relationally provable through a shared Chapter/Place. Relation Create against an unreadable target responds privacy-safely as “not found”.

### Relation lifecycle

For every relation table, define:

- Unique Constraint,
- sorting/position field if required by the domain,
- `ON DELETE` semantics,
- concurrency/reorder behavior,
- event payload,
- behavior when target privacy changes.

The concrete M3 relation surface is M3-D08/M3-D09/M3-D26.

## 9. Chapter

### Source-bound model

```text
Chapter
- id
- spaceId
- title
- description?
- startOn?
- endOn?
- placeId?
- createdBy
- createdAt/updatedAt
- version
```

Chapter groups:

- Memories,
- shared HeartMoments,
- Milestones.

### Source-bound Delete rule

```text
DELETE Chapter
  -> remove Chapter relations
  -> DO NOT delete original Memory/HeartMoment/Milestone
```

This rule is already decided and is tracked in the Decision Log as source-bound `DECIDED`.

### Open points

- partner write rights.
- `startOn <= endOn` and handling empty boundaries.
- ordering of Chapter content: chronologically derived or manually positionable?
- direct `placeId` column plus `place_chapters` appears partly redundant in the Master Spec; the canonical relation must be decided before migration.
- may a target belong to multiple Chapters? The source does not forbid it.

## 10. Collection / CollectionItem

### Source-bound model

```text
Collection
- id
- spaceId
- title
- icon
- createdAt/updatedAt

CollectionItem
- id
- collectionId
- title
- completed
- position
- createdBy
- createdAt/updatedAt
```

The Product Specification describes freely definable shared lists with completion, ordering, and multi-selection. The Shopping List is explicitly **not** a Collection.

### Readiness gaps

Global project conventions require versioning for mutable objects, while the Master field list for Collection/Item names no `version`. This conflict is not ignored: M3-D14/M3-D18 decide the concurrency surface.

Still open in this readiness draft:

- creator/ownership of the Collection itself,
- who may change/delete Collection and items,
- position strategy (dense integer, fractional rank, etc.),
- atomic reorder and concurrent reorder,
- whether multi-selection is a pure UI batch action or additional domain semantics,
- Delete Collection -> Items: parent cascade is preferred but still BLOCKING in this draft.

## 11. PrivateNote

### Source-bound model

```text
PrivateNote
- id
- spaceId
- ownerId
- title
- body
- pinned
- createdAt/updatedAt
- version
```

### Hard invariants

- `OWNER_ONLY` without a partner exception.
- the partner receives no positive signal through ID, lists, counts, search, Dashboard, Deep Link, or error detail.
- `title` and `body` are sensitive user content and belong within the ProtectedPayload boundary or its later E2EE-ready structure.
- `ownerId` is immutable.

## 12. GiftIdea

### Source-bound model

```text
GiftIdea
- id
- spaceId
- ownerId
- title
- description?
- recipient?
- occasion?
- targetOn?
- priceText?
- url?
- status
- pinned
- createdAt/updatedAt
- version
```

**The specification defines no enum for `status`.** No code may invent values for it. M3-D17 is BLOCKING in this readiness draft.

Security boundaries:

- all domain content is owner-only;
- `url` is stored only as user content in M3; no server-side preview/fetch resolution without a separate SSRF/provider design and reuse review;
- `priceText` remains free text until a monetary domain decision exists; do not silently infer currency logic.

## 13. PrivateCollection / PrivateCollectionItem

### Source-bound core

```text
PrivateCollection
- spaceId
- ownerId
- title
- icon

PrivateCollectionItem
- title
- completed
- position
```

Both are `OWNER_ONLY`.

The field list is intentionally less complete than for other models (for example IDs/timestamps/version on the item). M3-D18 must complete the persistence and concurrency convention before migrations are created.

## 14. ProtectedPayload candidates

The architecture boundary is source-bound, not every individual M3 column. The following candidates are reviewed in the decisions:

| Domain | Candidates |
|---|---|
| Wish | `title` and possible later free-text fields |
| Plan | `title`, `description` |
| Place | `name`, `description`, `address`, precise coordinates |
| Chapter | `title`, `description` |
| Collection | `title`; item `title` |
| PrivateNote | `title`, `body` |
| GiftIdea | all content fields including URL/price text |
| PrivateCollection | `title`; item `title` |

Status, technical IDs, versions, and safe enum-like states may live outside the payload where they do not create unnecessary sensitive information. Final classification belongs in the corresponding decisions.

## 15. Domain Events

M3 follows the existing M2 rule: events carry IDs and safe state metadata, not protected content.

Proposed minimal envelope:

```text
eventId
eventType
occurredAt
spaceId
actorId
resourceType
resourceId
resourceVersion
safeState?
```

Not in events:

- Wish/Plan/Chapter/Collection titles,
- PrivateNote/GiftIdea content,
- GiftIdea URL,
- address or coordinates,
- private relation counts,
- any partner-private metadata.

M3-D23 freezes the event contract before the first event-producing slice.

## 16. Delete/cascade matrix

| Operation | Source-bound | Still to decide in this draft |
|---|---|---|
| Delete Wish without Plan | no | hard delete/retention/event |
| Delete Wish with source Plan | no | forbid, detach, or preserve Plan |
| Delete Plan | no | effect on source Wish/Place/Chapter |
| Delete Place | no | remove relations vs. block Delete |
| Delete Chapter | **yes** | remove relations, preserve original content |
| Delete Collection | no | preferably delete items with parent |
| Delete CollectionItem | no | position/reorder afterward |
| Delete PrivateNote/GiftIdea | owner-only source-bound | retention/audit/event |
| Delete PrivateCollection | no | preferably delete private items with parent |

A DB cascade must never remove domain original content outside the parent aggregate.

## 17. Central race scenarios

Before runtime, at least these races must exist in the test design:

- two concurrent Wish->Plan conversions,
- Wish Delete vs. Wish->Plan,
- Plan Completion vs. Plan->Wish return,
- Relation Create vs. target Delete,
- Relation Create vs. HeartMoment `SHARED -> PRIVATE`,
- Chapter Delete vs. Relation Create,
- Place Delete vs. Relation Create,
- Collection Reorder vs. item Delete/Completion,
- PrivateCollection Reorder vs. item Delete,
- owner Read vs. logout/membership loss in client caches (later M5).

The DB/service solution must make races deterministic through constraints/locks/transactions rather than merely passing tests by chance.
