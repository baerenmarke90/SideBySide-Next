# M3 Privacy Threat Model

**Status:** Readiness foundation for M3  
**As of:** August 26, 2026

M3 significantly expands the Privacy surface: shared planning content is added alongside several intentionally private owner-only domains and precise location data. This document defines threats that must be considered in models, APIs, and tests before runtime implementation.

## 1. Protected assets

### Shared M3 content

- Wish and status
- Plan, descriptions, schedule/experience data
- Place, address, and coordinates
- Chapter and Relations
- Collection and Items

These resources are `SPACE_SHARED`, but **not public**. Only active members of the same Space may receive them.

### Owner-only content

- PrivateNote
- GiftIdea
- PrivateCollection
- PrivateCollectionItem

For these resources, the partner must not learn not only the content but, where possible, the existence.

### Particularly sensitive metadata

- exact coordinates and address,
- GiftIdea URL, recipient, occasion, price text,
- titles/free text of private notes and lists,
- Relations that could reveal private interests or locations,
- counts/order positions if they expose hidden private entries.

## 2. Trust boundaries

```text
Web / Android
    |
    | HTTPS + Bearer/Auth
    v
FastAPI / Authorization
    |
    +--> PostgreSQL
    |
    +--> Outbox/Worker
    |
    +--> Logs/Metrics/Error Tracking
```

M3 introduces **no new external Provider boundary**. Maps, Geocoding, URL previews, and Discovery are not called server-side.

## 3. Central invariants

### T1 — Space first

No M3 read/write is resolved only by Resource ID. Always:

1. authentication,
2. active Membership in `spaceId`,
3. query within this Space,
4. additional owner/write rule.

### T2 — Owner-only in the query

Private Area data is not loaded and discarded later in a service. The owner condition is part of the query/Authorization boundary.

### T3 — No indirect private disclosure

`OWNER_ONLY` must not become visible through:

- foreign GET-by-ID,
- lists,
- counts,
- Relations,
- error messages,
- sorting gaps,
- Search/Autocomplete,
- Chapter/Place,
- Dashboard/Activity/Notifications,
- Export,
- Domain Events,
- Logs/Metrics,
- Deep Links.

### T4 — Relation never extends rights

A Relation is not a Capability token. Reading a Chapter or Place never grants access to a Target that would otherwise be unreadable.

### T5 — No Shared/Private mixed domain

Wish/Plan/Collection are not turned into private storage through a visibility flag. PrivateNote/GiftIdea/PrivateCollection remain separate Domain models.

## 4. Threats and controls

### M3-T01 — Private Area ID enumeration

**Attack:** Partner guesses note/gift/private collection IDs and compares responses.

**Controls:**

- owner-scoped query,
- identical privacy-safe 404 for unknown/foreign/other Space/deleted,
- no separate existence query without owner filter.

**Tests:** Partner ID sweep produces the same response class.

### M3-T02 — Cross-Space ID substitution

**Attack:** Valid ID from Space A is used against Space B.

**Controls:**

- Membership in route Space first,
- resource query contains `space_id`,
- Relation tables enforce Space consistency where possible.

### M3-T03 — Cross-Space Relation

**Attack:** Place/Chapter from Space A is linked to content from Space B.

**Controls:**

- both targets loaded Space-scoped,
- DB constraints where possible,
- transaction re-check before insert,
- externally privacy-safe 404.

### M3-T04 — Private HeartMoment through shared Chapter/Place

**Attack:** Private HeartMoment becomes observable through shared Relations.

**Controls:**

- Target must be readable and relationable in the shared context,
- `OWNER_ONLY` HeartMoment behaves as not found for shared Relations,
- existing semantics remove or prevent Relations during `SHARED -> PRIVATE`.

### M3-T05 — Relation race against Privacy change

**Attack:** Concurrent Relation Create and `SHARED -> PRIVATE` leaves a private Relation.

**Controls:**

- Row Lock/serialized order on Target/Relation,
- Privacy re-check before commit,
- no state `Private + shared Relation`.

### M3-T06 — Wish->Plan double submit

**Attack/error:** Two clients create two Plans.

**Controls:**

- defined cardinality,
- DB Unique Constraint,
- Row Lock/atomic transaction,
- stable conflict/idempotency response.

### M3-T07 — Delete vs Relation race

**Attack/error:** Target deleted during Relation creation.

**Controls:**

- FK prevents dangling Relation,
- service translates Integrity/Lock outcome into stable errors,
- no silent acceptance.

### M3-T08 — Partner edits creator-owned Shared Content

**Controls:**

- M3-D01 defines server-side write policy,
- capabilities only improve presentation,
- service enforces authorization.

### M3-T09 — Private count leakage

**Controls:**

- Shared endpoints count only shared domains,
- Private Collections have separate owner-only lists,
- no combined Shared+Private list with client filtering.

### M3-T10 — Position leakage

**Control:** Shared and Private Collections use separate aggregates; position spaces are never mixed.

### M3-T11 — Location leakage through telemetry

**Controls:**

- structured redaction,
- Events without location payload,
- request logging must not capture unsanitized bodies,
- tests on Event/log representation.

### M3-T12 — Location leakage through Read Models

M3 creates no new Dashboard/Search projections. Later Read Models must apply Space/Privacy rules again.

### M3-T13 — GiftIdea URL SSRF/Tracking

**Control:** M3 stores URL only as content and performs no server-side fetch.

Later Preview requires dedicated Security/Reuse design.

### M3-T14 — GiftIdea URL in partner client

**Control:** Partner never receives GiftIdea. Owner opens URL only through deliberate interaction; automatic external requests are not part of M3.

### M3-T15 — Private content in Domain Events

**Control:** Event envelopes contain IDs and safe states only. No ProtectedPayload.

### M3-T16 — Private content in Audit

Audit may retain security metadata, not private plaintext. Allowed: Actor, action, Resource ID, timestamp, result.

### M3-T17 — Private export of partner data

M3 implements no Export but preserves:

- owner export may contain own private resources,
- shared/partner export never contains another person's owner-only resources,
- Relations must not reveal private targets.

### M3-T18 — Cache after Logout/Space change

M3 does not implement M5 cache. Future caches must be account+Space+owner scoped and have secure clear rules.

### M3-T19 — Chapter delete data loss

**Failure:** DB cascade deletes Memory/HeartMoment/Milestone instead of Join rows.

**Control:** FK direction and `ON DELETE` only on Join parent; integration test checks original data.

### M3-T20 — Duplicate Chapter/Place truth source

**Failure:** `chapter.place_id` differs from `place_chapters`.

**Control:** M3-D31 decides one canonical model before migration.

## 5. Privacy classification

| Data | Shared/Private | Sensitivity | Telemetry |
|---|---|---|---|
| Wish title | shared | relationship/interests | no plaintext |
| Plan title/description | shared | plans/dates | no plaintext |
| plannedStart/End | shared | scheduling | no high-cardinality raw telemetry |
| Place name/address | shared | potential location | no plaintext |
| lat/lon | shared but highly sensitive | precise location | strictly forbidden |
| Chapter title/description | shared | relationship content | no plaintext |
| Collection/Item title | shared | interests/checklists | no plaintext |
| PrivateNote | owner-only | highly sensitive | strictly forbidden |
| GiftIdea | owner-only | highly sensitive | strictly forbidden |
| PrivateCollection | owner-only | highly sensitive | strictly forbidden |

## 6. Error semantics

### Not readable

Foreign Space, partner private resource, unknown ID, and deleted private resource are not distinguished externally.

### Readable but not writable

If a shared visible resource is readable but mutation is not allowed, 403 may be correct according to the existing Security convention.

### Relations

Unreadable Target -> 404. No `RELATION_TARGET_PRIVATE` or similar code.

## 7. Logging / Analytics / Error Tracking

Allowed technical events:

```text
wish_created
plan_transition_completed
relation_create_failed
private_note_create_failed
```

Allowed dimensions are coarse technical classes only, such as result, stable error code, platform/app version.

Not allowed:

- Resource ID as Analytics dimension,
- title/text,
- exact sensitive dates,
- address/coordinates,
- URL,
- recipient/occasion/priceText,
- private Item counts.

## 8. Provider and network boundary

M3 has no business need for outgoing requests caused by Place/GiftIdea content.

Therefore:

- no Geocoding API,
- no map tile integration,
- no Link Preview,
- no URL validation through Fetch,
- no automatic Location resolution.

A later Provider slice requires Reuse-before-build, Privacy, cost, ToS, Self-Hosted, and Threat review.

## 9. Security Gate for M3 slice

A slice is not merge-ready if:

- Cross-Tenant negative test is missing,
- owner-only negative test is missing for private domains,
- Relation bypasses Target Authorization,
- Race is only protected by assumed ordering instead of DB/Transaction primitives,
- Event/Log copies sensitive content,
- Delete Cascade is not tested against original data loss,
- new external data transfer is introduced without explicit scope.

## 10. G3 Privacy minimum evidence

Before G3:

- all Shared M3 domains are cross-tenant isolated,
- every Private Area domain is owner-only for List/GET/Mutation,
- private resources cannot be proven through Shared Relations,
- Wish->Plan and relevant Relation/Delete races have PostgreSQL tests,
- Chapter Delete preserves originals,
- Events/Logs contain no protected M3 payloads,
- Place coordinates do not appear in telemetry,
- G3-specific client/E2E evidence follows M3-D24.
