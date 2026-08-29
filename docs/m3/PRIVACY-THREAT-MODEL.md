# M3 Privacy Threat Model

**Status:** readiness baseline for M3  
**As of:** August 26, 2026

M3 significantly expands the privacy surface: in addition to shared planning content, it introduces several deliberately private owner-only domains and precise location data for the first time. This document defines the threats that must be considered in model, API, and tests before runtime code.

## 1. Protected assets

### Shared M3 content

- Wish and status
- Plan, description, schedule/experience dates
- Place, address, and coordinates
- Chapter and relations
- Collection and items

This content is `SPACE_SHARED`, but **not public**. Only active members of the same space may receive it.

### Owner-only content

- PrivateNote
- GiftIdea
- PrivateCollection
- PrivateCollectionItem

For this content, the partner must not learn not only the content but, where possible, **its existence**.

### Particularly sensitive metadata

- precise coordinates and address,
- GiftIdea URL, recipient, occasion, and price text,
- titles/free text of private notes and lists,
- relations from which private interests or whereabouts could be inferred,
- counts/sort positions when they could reveal hidden private entries.

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

M3 introduces **no new external provider boundary**. In particular, Maps, Geocoding, URL previews, and Discovery are not called server-side.

## 3. Central invariants

### T1 – Space first

No M3 read/write is resolved solely through a resource ID. Always:

1. authentication,
2. active membership in `spaceId`,
3. query within that space,
4. additional owner/write rule.

### T2 – Owner-only in the query

Private Area data is not loaded and then discarded in the service. The owner condition is part of the query/authorization.

### T3 – No indirect private disclosure

`OWNER_ONLY` must not become visible through:

- foreign GET-by-ID,
- lists,
- counts,
- relations,
- error messages,
- ordering gaps,
- Search/Autocomplete,
- Chapter/Place,
- Dashboard/Activity/Notifications,
- Export,
- Domain Events,
- logs/metrics,
- Deep Links.

### T4 – A relation never expands rights

A relation is not a capability token. Reading a Chapter or Place grants no access to a target that would otherwise be unreadable.

### T5 – No shared/private mixed domain

Wish/Plan/Collection are not turned into private storage through a privacy flag. PrivateNote/GiftIdea/PrivateCollection remain separate domain models. This prevents a misinterpreted shared filter from exposing private data.

## 4. Threats and controls

### M3-T01 – ID enumeration in Private Area

**Attack:** partner guesses `noteId`/`giftIdeaId`/private Collection ID and compares responses.

**Controls:**

- owner-scoped query,
- identical privacy-safe 404 for unknown/foreign/other-space/deleted,
- no different error message,
- no prior Exists query without owner filter.

**Tests:** partner ID sweep against existing and non-existing IDs returns the same semantic response class.

### M3-T02 – Cross-space ID substitution

**Attack:** valid ID from Space A is inserted into a route for Space B.

**Controls:**

- membership in route space first,
- resource query includes `space_id`,
- relation tables enforce space consistency in service/constraints.

**Tests:** all M3 domains and all relation types.

### M3-T03 – Cross-space relation

**Attack:** Place/Chapter from Space A is linked to Memory/Plan from Space B.

**Controls:**

- load both targets space-scoped,
- DB constraints where possible,
- transaction rechecks before insert,
- external 404 without foreign-space disclosure.

### M3-T04 – Private HeartMoment through shared Chapter/Place

**Attack:** user knows a private HeartMoment ID and tries to link it to a shared Chapter/Place; partner infers existence from relation or count.

**Controls:**

- target must be readable and relationable by the actor in shared context,
- `OWNER_ONLY` HeartMoment is treated as not found for shared relation,
- any existing relation must be removed atomically/serially during `SHARED -> PRIVATE`, or prevented before commit — final semantics M3-D09/M3-D26.

### M3-T05 – Relation race against privacy change

**Attack:** concurrently `link shared HeartMoment -> Chapter` and `SHARED -> PRIVATE`.

**Risk:** relation remains after privacy commit and reveals private existence.

**Controls:**

- row lock/serialized ordering on target/relation,
- privacy recheck before commit,
- privacy change must include M3 relations in its cascade/listener boundary once this domain exists.

### M3-T06 – Wish->Plan double submit

**Attack/failure:** two devices or retry create two Plans from one Wish.

**Controls:**

- defined cardinality,
- DB Unique Constraint,
- row lock/atomic transaction,
- stable conflict/idempotency response.

### M3-T07 – Delete-vs-relation race

**Attack/failure:** target is deleted while relation is being created.

**Controls:**

- FK prevents dangling relation,
- domain service translates integrity/lock result to a stable error,
- no catch-and-ignore logic that confirms a phantom relation.

### M3-T08 – Partner edits creator-owned shared content

**Attack:** client hides action, partner sends request manually.

**Controls:**

- M3-D01 defines write policy server-side,
- Capabilities are presentation only,
- query/service enforces the rule.

### M3-T09 – Private count leakage

**Attack:** shared response includes for example `privateItemCount`, total count, or pagination behavior from which partner infers private content.

**Controls:**

- shared endpoints count only the shared domain,
- Private Collections have separate owner-only lists,
- no combined Shared+Private Collection list with client-side filtering.

### M3-T10 – Ordering/position leak

**Attack:** visible shared items have positions `1,4,7` because private items are ordered in the same table.

**Control:** Shared and Private Collections are separate tables/aggregates; position spaces are not mixed.

### M3-T11 – Location leakage through telemetry

**Attack/failure:** coordinates/address appear in logs, metrics, analytics, error context, or Outbox.

**Controls:**

- structured redaction,
- events without location payload,
- request logging must not capture unscrubbed bodies,
- tests over event/log representations.

### M3-T12 – Location leakage through relation/read model

**Attack:** Place is later projected into Dashboard/Search and reveals more than the authorized parent.

**Control in M3:** no new Dashboard/Search projections. Later Read Models must reapply space/privacy rules; M3 stores no “public” Place variant.

### M3-T13 – GiftIdea URL SSRF/tracking

**Attack:** user stores an internal URL; backend loads preview/metadata and becomes an SSRF proxy.

**Control:** M3 stores URL only as content and performs no server-side fetch.

A later preview needs its own security/reuse design covering URL allow/block rules, DNS rebinding, redirects, content limits, and privacy.

### M3-T14 – GiftIdea URL in partner client

**Attack/failure:** shared client prefetches/instruments URLs from an owner-only GiftIdea.

**Control:** partner never receives GiftIdea at all. Owner client may open the URL only through deliberate interaction; automatic external requests are not part of M3.

### M3-T15 – Private content in Domain Events

**Failure:** event contains title/body for consumer convenience.

**Controls:** event envelope carries IDs + safe states; no ProtectedPayloads. Consumers load authorized data only in their own context or operate without content.

### M3-T16 – Private content in audit

Audit may retain required security metadata but no private plaintext. Examples of allowed fields are actor, action, resource ID, timestamp, and result. Title/body/GiftIdea details/coordinates do not belong there.

### M3-T17 – Partner private export

M3 does not implement Export, but must keep the data architecture such that M5 can clearly separate:

- owner export may contain the owner's own private resources,
- shared/partner export never contains the other person's owner-only resources,
- relation tables must not reveal private targets through shared bundle metadata.

### M3-T18 – Cache after logout/space change

M3 does not implement the M5 Read Cache. The architecture prerequisite still applies:

- do not persist private DTOs in uncontrolled browser storage,
- future Android caches are scoped by account+space+owner,
- logout/session revocation/space change receives safe cache-clear rules (M3-D22/M2-D18).

### M3-T19 – Chapter Delete as data loss

**Failure:** DB cascade deletes Memory/HeartMoment/Milestone instead of join row.

**Control:** FK direction and `ON DELETE` only on join parent; integration test verifies original data remains.

### M3-T20 – Duplicate source of truth for Chapter/Place

**Failure:** `chapter.place_id` points to Place A while `place_chapters` contains Place B.

**Control:** M3-D31 decides exactly one canonical model before migration.

## 5. Privacy classification

| Data | Shared/private | Sensitivity | Telemetry |
|---|---|---|---|
| Wish title | shared | relationship/interests | no plaintext |
| Plan title/description | shared | plans/schedule | no plaintext |
| plannedStart/End | shared | scheduling | no high-cardinality raw telemetry |
| Place name/address | shared | potentially location | no plaintext |
| lat/lon | shared but highly sensitive | precise location | strictly forbidden |
| Chapter title/description | shared | relationship content | no plaintext |
| Collection/item title | shared | interests/checklists | no plaintext |
| PrivateNote | owner-only | highly sensitive | strictly forbidden |
| GiftIdea | owner-only | highly sensitive | strictly forbidden |
| PrivateCollection | owner-only | highly sensitive | strictly forbidden |

## 6. Error semantics

### Unreadable

Foreign space, partner's private resource, unknown ID, and deleted private resource are not distinguished externally.

### Readable but not writable

If M3-D01 chooses creator-only writes, a 403 for a visible shared resource may be domain-correct — analogous to the existing security convention. It confirms nothing the partner could not already read.

### Relations

Unreadable target -> 404. No `RELATION_TARGET_PRIVATE` or similar code.

## 7. Logging / analytics / error tracking

M3 may count technical events such as:

```text
wish_created
plan_transition_completed
relation_create_failed
private_note_create_failed
```

Allowed dimensions are coarse technical classes only, for example `result`, stable error code, platform/app version.

Not allowed:

- resource ID as an analytics dimension,
- title/text,
- precise dates/times in sensitive flows,
- address/coordinates,
- URL,
- recipient/occasion/price text,
- private item counts.

## 8. Provider and network boundary

M3 has no domain need for outbound requests based on Place/GiftIdea content.

Therefore:

- no Geocoding API,
- no map-tile integration,
- no Link Preview,
- no URL validation by fetch,
- no automatic location resolution.

A later provider slice requires `REUSE-BEFORE-BUILD`, privacy/cost/ToS/self-hosted evaluation, and its own threats.

## 9. Security gate for an M3 slice

A slice is not merge-ready when:

- cross-tenant negative test is missing,
- owner-only negative test is missing for a private domain,
- a relation enables target authorization bypass,
- a race is protected only by “probably sequential” rather than a DB/transaction primitive,
- event/log copies sensitive content,
- Delete cascade is not tested against original-data loss,
- new external data transfer is introduced without explicit scope.

## 10. Minimum G3 privacy evidence

Before G3, at least the following must be robustly demonstrated:

- all shared M3 domains cross-tenant isolated,
- every Private Area domain owner-only for List/GET/Mutation,
- no private resource provable through a shared relation,
- Wish->Plan and relevant relation/delete races tested with PostgreSQL,
- Chapter Delete preserves original content,
- events/logs contain no protected M3 payloads,
- Place coordinates do not appear in telemetry,
- G3-specific client/E2E evidence documented according to M3-D24.
