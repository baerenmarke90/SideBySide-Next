# Implementation Status

As of: August 30, 2026
Current repository state: GitHub `main` is the canonical SHA source; this living status document deliberately stores no static current SHA.  
Current gate status: **G2 passed; M2 complete; M3 released**

## Document roles

- **Binding source:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Compact product overview:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Current gate decision:** [2026-08-26-g2-final-gate-review.md](reviews/2026-08-26-g2-final-gate-review.md)
- **Status sources and drift rules:** [STATUS-SOURCES.md](STATUS-SOURCES.md)
- **Binding development rule:** [REUSE-BEFORE-BUILD.md](REUSE-BEFORE-BUILD.md) and [AGENTS.md](../AGENTS.md)
- **Architecture/operations decisions:** dated ADRs under [docs/decisions](decisions)
- **M2 project control:** [m2/PROJECT-CONTROL.md](m2/PROJECT-CONTROL.md)
- **M3 readiness and delivery:** [m3/README.md](m3/README.md) and [m3/DELIVERY-PLAN.md](m3/DELIVERY-PLAN.md)
- **Historical reviews:** dated files under `docs/reviews/`; they are never modified retroactively.
- **This document:** living work and progress list.

If sources conflict, the Master Specification takes precedence. A new gate decision always receives a new dated review.

## Working rules

1. Modify only this repository.
2. Before implementation, read the relevant specification, Decision Log, and current Issues.
3. One Issue = one clear scope = its own branch/PR.
4. No direct changes to `main`, no rebase, no force push.
5. Before merge, freshly check current `main`, PR HEAD, complete diff, mergeability, and CI.
6. Record findings outside scope as a separate Issue.
7. Do not rewrite historical reviews.
8. Before building technical commodity functionality in-house, perform the Reuse review defined in [REUSE-BEFORE-BUILD.md](REUSE-BEFORE-BUILD.md) and document it in the Issue or PR. A relevant PR without a traceable review is not merge-ready; CI enforces the decision.

## M0 — Foundation

**Status: complete.**

- [x] FastAPI, SQLAlchemy 2, PostgreSQL, Alembic
- [x] REST API v1, camelCase, Problem Details
- [x] UUIDv7 and time/date conventions
- [x] Transactional Outbox and PostgreSQL Job Queue
- [x] MediaStore/Provider abstractions
- [x] ProtectedPayload base abstraction
- [x] reproducible dependencies and Lockfile
- [x] OpenAPI contract + contract check
- [x] PostgreSQL integration tests
- [x] dependency/vulnerability scan, container build, Secret Scan, Provenance

## M1 — Identity & Relationship

**Status: runtime scope complete; G1 passed.**

- [x] Account, AccountEmail, AuthIdentity
- [x] local password login with Argon2
- [x] Device Sessions and rotating tokens
- [x] Space, Membership, central Tenant Guard
- [x] race-safe Invitations
- [x] SpaceProfile with ETag/If-Match and 409
- [x] PartnerProfile and ProfilePreference
- [x] RelatedPerson and ImportantDate
- [x] central SQL-side `SPACE_SHARED`/`OWNER_ONLY` Authorization
- [x] OIDC Authorization Code + PKCE/State/Nonce/Discovery/JWKS
- [x] OIDC Invitation onboarding without email merge
- [x] Passkey/WebAuthn Registration and Authentication
- [x] Magic Link, email verification, and Recovery
- [x] Refresh replay protection
- [x] #61: RelatedPerson deletion with explicit `preserve`/`cascade` policy and no destructive default
- [x] G1 Gate Review after #61: **PASSED**

### Completed M1/repository hardening

- [x] **#59 — Pre-Exposure:** Passkey Authentication start protected against challenge flooding.
- [x] **#60 — Pre-Exposure:** Rate Limit thresholds are enforced atomically under concurrency.
- [x] **#25 — Repository Hardening:** active ruleset for `main` enforces Pull Request, Merge Commit, current required checks, no force pushes, and no branch deletion.

The Pre-Exposure/repository hardening items that were previously listed as open in the Living Status are therefore complete. GitHub remains the operational source for each Issue state.

### Operations: Self-Hosted startup path

- [x] **#110 — Startup path and migration decoupled** (PR #111): `alembic upgrade head` no longer depends on Cursor Signing Key, SMTP, and public address; Compose separates migration from runtime configuration; CI exercises the real startup path instead of merely parsing it.
- [x] **#115 — Network and port readiness hardened** (PR #118): an occupied API port or missing network path no longer leaves the instance appearing healthy; dedicated Deployment Guard in CI.

Two operational commitments resulting from this are binding and documented in [ADR 0002](decisions/0002-self-hosted-first-start-mode.md):

- The provided Compose stack starts as a **clearly marked local test mode**. Real operation requires `SBS_ENVIRONMENT=production` in `.env`; the application reports its operating mode on every startup.
- SMTP access is **not a startup prerequisite**. `SBS_MAIL_TRANSPORT=none` is allowed in production; mail-dependent sign-in paths then return `503 MAIL_TRANSPORT_UNAVAILABLE`, while sign-in remains available through password, Passkey, and OIDC. `log` remains forbidden in production.

## M2-S0 — Readiness & contract decisions

**Status: complete.** All `BLOCKING` decisions in the [Decision Log](m2/DECISION-LOG.md) are `DECIDED`.

- [x] **#67 — Planning:** synchronized G1 status, Roadmap, and milestone boundaries.
- [x] **#68 — Domain/Privacy:** closed Memory, Comment, and Privacy decisions.
- [x] **#69 — Media:** decided Attachment lifecycle, limits, validation, and Retention.
- [x] **#70 — API:** defined routes, DTOs, Concurrency, Pagination, and Story sorting.
- [x] **#78 — Media metadata:** decided EXIF/GPS stripping during ingest and variant scope (M2-D14/D15).

Only `BEFORE_CLIENTS` decisions that become relevant before stable full integration remain open: M2-D10 (Notification Preview), M2-D17 (Export/Backup), M2-D18 (Client Cache), and M2-D21 (Search Index). They did not block G2 and are handled in their respective later milestones.

M2-D22 (owner view) is no longer in that category: the question shapes the Story route and was therefore promoted to `BLOCKING` and decided in #104 — just as M2-D14 and M2-D15 had previously been in #78.

## M2 — Runtime and G2

**Status: complete; G2 passed.**

- [x] **#71 — Memory CRUD without media** (PR #77): Memory Domain with ProtectedPayload for title/body, author-only writes with shared readability, `If-Match`/409, signed Keyset Cursor, and `resourceVersion` in the Outbox envelope.
- [x] **#80 — HeartMoment with owner-only Privacy** (PR #84): first type with a real user visibility choice; `SHARED -> PRIVATE` as a dedicated atomic operation, emotion in ProtectedPayload.
- [x] **#79 — Attachment lifecycle for images** (PR #89): state machine, LocalMediaStore, asynchronous validation with metadata stripping and Thumbnail, authorized reads, Retention, and Cleanup.
- [x] **#90 — Bind Attachments to Memory and HeartMoment** (PR #93): `MemoryAttachment` with stable `position`, HeartMoment with at most one Attachment, atomic Bind/Unbind against the binding window from M2-D20, and no Cross-Space binding.
- [x] **#94 — Milestone Domain and API** (PR #95): dedicated model instead of a type flag on Memory, author rule from M2-D25, `If-Match`/409, and Story-ready fields.
- [x] **#97 — Comments, Outbox, and Notification Hook** (PR #98): Create/List nested under the parent, Update/Delete space-scoped, enumerated targets `MEMORY`/`MILESTONE`/`HEART_MOMENT`, atomic Outbox entry, and idempotent Retry.
- [x] **#87 — S3-compatible MediaStore adapter** (PR #100): presigned Upload and Read URL with the TTLs from M2-D13, tested against the same contract test as the local adapter.
- [x] **#113 — Story Read Model and `/timeline`** (PR #114): derived Timeline over Memory, Milestone, and shared HeartMoments only; sort key and Keyset Cursor per M2-D08, private HeartMoments never in the result — not even for their owner (M2-D22). No Story table.
- [x] **S8 — thin Web/Android reference flows:** Web and Android deliver the critical Memory/Media/Story reference path.
- [x] **#144 — real G2 client E2E evidence:** Web and Android run against the same real SideBySide stack of API, Worker, PostgreSQL, and LocalMediaStore.
- [x] **#147 / PR #170 — final G2 Gate Review:** **G2: PASSED**.

### Future backlog outside M2/G2

- [ ] **#88 — Video uploads and poster frames:** future development, do not implement now. Prototype #109 was deliberately closed without merge because of a production image of roughly 755 MiB and the additional ffmpeg operational, Supply Chain, and Security burden.

Video remains fail-closed until a new product decision: M2-D04 allows MP4 and QuickTime in the target contract, while the current server rejects them with `ATTACHMENT_TYPE_NOT_ALLOWED`. Clients must not present video as available.

Historical M2 project control and binding milestone boundaries are documented in [M2 Project Control](m2/PROJECT-CONTROL.md). The current gate decision is documented in the [final G2 Gate Review](reviews/2026-08-26-g2-final-gate-review.md).

### Binding M2/M5 boundary

M2 is **Domain + API + minimal vertical Web/Android reference flows**. These reference flows provide technical E2E evidence for the critical Memory/Media/Story Core and do not imply full client parity.

M5 is **Client Completion & Parity**: complete client integration, Deep Links, Read Cache, Export/Import, systematic Web/Android parity, Accessibility, and Performance.

### Privacy terminology

- `SHARED` / `PRIVATE`: public domain values.
- `SPACE_SHARED` / `OWNER_ONLY`: internal Authorization/Privacy classes.
- Clients do not redundantly write `privacyClass`.

### M4 boundary

M4 is internally split into three delivery slices:

- M4-A Search + Dashboard Read Models
- M4-B Activity + Notifications
- M4-C Reminders + Rules

Global full-text Search was not part of G2. The minimum Story contract includes `type`, `year`, `order`, `cursor`, and `limit`; global full-text Search belongs to M4-A.

## M2 runtime sequence after S0

1. ~~Memory CRUD without media (#71)~~ — delivered
2. ~~Attachment Foundation / MediaStore Contract (#79)~~ — delivered, images
3. ~~HeartMoment Privacy (#80)~~ — delivered
4. ~~Memory + multiple media (#90)~~ — delivered
5. ~~Milestone (#94)~~ — delivered
6. ~~Comments + Outbox/Notification Hook (#97)~~ — delivered
7. ~~Story Read Model (#113)~~ — delivered
8. ~~thin Web/Android reference flows~~ — delivered
9. ~~G2 Review~~ — **PASSED**

The S3 adapter (#87) ran in parallel and is delivered. Video (#88) is not part of this chain or M2/G2; it is Future Backlog.

## G2 — Story Alpha

**Status: PASSED.** The binding decision source is the [final G2 Gate Review](reviews/2026-08-26-g2-final-gate-review.md).

Demonstrated are M2 Domain/API, Story Privacy, Media/parent Authorization, Cross-Tenant/race/data integrity, OpenAPI, migrations, PostgreSQL integration, and a real critical Memory/Media/Story flow in Web and Android against the same SideBySide stack.

Manual Accessibility acceptance was deliberately moved from G2 into final client/release QA. It is **not** considered passed and remains part of M5/G4. Full client parity likewise remains M5/G4.

## M3 — Planning & Private Area

**Status: released.** The [M3 Technical Readiness Package](m3/README.md) is prepared; all M3-D01 through M3-D32 are `DECIDED`.

The runtime sequence follows the [M3 Delivery Plan](m3/DELIVERY-PLAN.md). A concrete slice starts only when its production Request/Response/OpenAPI contract is unambiguously contract-testable and Reuse-before-build plus the normal PR/CI gates are satisfied.

- [x] **M3-S1 — Wish Foundation:** Wish Domain with ProtectedPayload for title, collaborative write per M3-D01, `status` exclusively server-controlled, `If-Match`/409, status filtering through a Space- and filter-bound Cursor, and redacted `WISH_*` events. The Wish->Plan operation and Plan-dependent rows of the Delete Matrix follow in S2.
- [x] **M3-S2 — Plan + Wish->Plan:** Plan Domain with Direct Create per M3-D30, state machine `IDEA | PLANNED | COMPLETED` with date invariants as both service and DB constraints, `sourceWishId` with `UNIQUE` and a composite Same-Space foreign key, atomic and idempotent Wish->Plan conversion, `return-to-wish`, `schedule`/`unschedule`/`complete`, and canonical lock order `Wish -> Plan` with real PostgreSQL race and rollback tests. The Wish Delete Matrix from M3-D05 is therefore complete.
- [x] **M3-S3 — Place Foundation:** Place Domain with name, description, and address behind the ProtectedPayload boundary; coordinates as typed `NUMERIC` columns with pair, range, and precision invariants in both service and schema; CRUD/List without deduplication; no Geocoding or Maps Provider. `Plan.placeId` was added (canonical and single-column, with composite Same-Space foreign key). Place deletion versionedly unlinks assigned Plans while preserving them. Additionally, bound DB parameters no longer appear in error messages and therefore no longer appear in application logs.
- [x] **M3-S4 — typed Content Relations:** `place_memories`, `place_heart_moments`, and `place_milestones` with real composite foreign keys over `(id, space_id)`, primary key `(place_id, target_id)`, and typed REST routes instead of free `(targetType,targetId)` polymorphism. Same-Space is a schema property rather than a service rule: both foreign keys share the same `space_id` column. Unknown, deleted, foreign, and private targets all resolve indistinguishably to `RELATION_TARGET_NOT_FOUND`. The Privacy transition `SHARED -> PRIVATE` removes relations in the same transaction; beneath it, a schema guard makes the state "private with shared relation" unrepresentable. Lock order `Place -> Target` is verified with PostgreSQL race tests against parent deletion, target deletion, and Privacy transition.
- [x] **M3-S5 — Chapter:** Chapter Domain with optional `startOn`/`endOn`, canonical nullable `placeId`, collaborative CRUD/List with `If-Match`/409, typed `chapter_memories`/`chapter_heart_moments`/`chapter_milestones`, deterministic derived cross-type content ordering, privacy-safe target handling, and delete semantics that remove only the Chapter and its relations while preserving all originals.
- [x] **M3-S6 — Shared Collections:** shared Collection + CollectionItem aggregate with collaborative writes; immutable server-derived `createdBy`; independent root structure/order and Item content versions; contiguous positions; append-on-create, transactional delete compaction, and atomic exact-set full-list reorder; Cross-Tenant fail-closed handling and real PostgreSQL reorder/create/delete/completion race coverage; Collection/Item titles remain out of event payloads. ShoppingList and persisted multi-select state remain outside S6.
- [x] **M3-S7 — PrivateNote + GiftIdea:** dedicated owner-only PrivateNote and GiftIdea tables/services with ProtectedPayload content, server-derived Space/owner/privacy, CRUD/List under `/spaces/{spaceId}/private/...`, `If-Match`/409, GiftIdea lifecycle `IDEA | BOUGHT | GIVEN`, inert URL storage without server fetches, privacy-safe 404 behavior, owner-filtered pagination, redacted private events, and PostgreSQL/HTTP partner/Cross-Tenant coverage.
- [x] **M3-S8 — PrivateCollection:** dedicated owner-only PrivateCollection and PrivateCollectionItem persistence with Parent-derived Item authorization, ProtectedPayload content, root/item optimistic concurrency, append/compaction and atomic full-list reorder, privacy-safe partner/Cross-Tenant handling, redacted private events, real PostgreSQL race coverage, and synchronized OpenAPI plus generated TypeScript/Kotlin clients (Issue #259 / PR #260).

## Later milestones

- [ ] M4 — Search/Dashboard, Activity/Notifications, Reminders/Rules
- [ ] M5 — Client Completion & Parity, Export/Import, Read Cache, final Accessibility QA
- [ ] M6 — Questions, Check-in, monthly/yearly recaps
- [ ] M7 — Integrations/Providers
- [ ] M8 — Location/Context with explicit opt-in
- [ ] M9 — Productization, Managed/Self-Hosted policy, Backup, Entitlements, Launch Hardening
- [ ] MX — real E2EE as a separate later Security milestone

## Next checkpoint

M3-S9 **Integrated M3 backend/API evidence** according to the [M3 Delivery Plan](m3/DELIVERY-PLAN.md): demonstrate the five mandatory G3 flows against the real SideBySide API + PostgreSQL and consolidate Cross-Tenant, race, Event/log Redaction, and Delete evidence before S10/G3 review.