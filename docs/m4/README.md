# M4 Technical Readiness Package

**Status:** M4-A S0 decisions complete; runtime not started  
**As of:** August 30, 2026  
**Tracking:** #272

This package starts **M4 — Engage** after M3/G3 completion. It closes the blocking decisions for **M4-A: Search + Dashboard Read Models** before runtime code is allowed to define those semantics implicitly.

M4 remains split into separate risk classes:

- **M4-A:** Search + Dashboard Read Models;
- **M4-B:** Activity + Notifications;
- **M4-C:** Reminders + Rules.

Only M4-A is released by this package. M4-B and M4-C require their own readiness/runtime ownership and are not pulled forward by #272.

## Binding sources and precedence

If sources conflict, use this order:

1. `specification/CLEAN-ROOM-MASTER-SPEC.md`;
2. `specification/PRODUCT-SPEC.md`;
3. `docs/SECURITY.md` and existing authorization/privacy invariants;
4. `docs/REUSE-BEFORE-BUILD.md`;
5. `docs/CROSS-CUTTING-QUALITY.md`;
6. `docs/BUSINESS-MODEL.md` and `docs/FREEMIUM-FEATURE-MATRIX.md`;
7. published OpenAPI contract;
8. explicitly `DECIDED` M4 documents in this package.

No M4 decision may weaken Clean-Room separation, Tenant Isolation, `OWNER_ONLY` protection, authorization, data rights, or existing security gates.

## M4-A product boundary

### Search

Version 1 uses PostgreSQL Full Text Search behind an application-facing Search abstraction. Elasticsearch/OpenSearch is not required. Search authorization happens in SQL/service selection before any result DTO exists.

The initial searchable surface is:

- Memory;
- HeartMoment, including the caller's own private HeartMoments but never a partner's private HeartMoments;
- Milestone;
- Wish;
- Plan;
- Place;
- Chapter;
- shared Collection and CollectionItem;
- the caller's PrivateNote;
- the caller's GiftIdea;
- the caller's PrivateCollection and PrivateCollectionItem.

Questions remain M6. Comments, Profiles, RelatedPersons and ImportantDates are deliberately not part of the first global Search contract. Their exclusion is a bounded product decision, not evidence that they can never be searchable.

The detailed contract is in [Search Design](./SEARCH-DESIGN.md).

### Dashboard

Dashboard is a derived Read Model. There is no `dashboard` table, no copied domain payload, and no separate persisted dashboard truth.

The first M4-A Dashboard derives only data whose owning domain already exists:

- Space/partner summary;
- optional relationship duration;
- deterministic basic retrospective (`Weißt du noch?`) from authorized shared history;
- upcoming scheduled Plans and date-based relationship items;
- recent shared root content.

`Ich denke an dich` is an M4 feature but is not faked by M4-A. It is added when its owning M4 slice exists. Activity/Notification/Reminder/Rule data is likewise absent until M4-B/M4-C deliver it. Questions/Year Summary remain M6.

The detailed contract is in [Dashboard Design](./DASHBOARD-DESIGN.md).

## Privacy rule

M4-A Read Models are **authorization-first**, not projection-first.

For Search:

- shared results require active Membership and matching `space_id`;
- owner-only rows require `owner_id == current_account_id` in the SQL/repository predicate;
- child private collection items are reachable only through an owner-authorized parent join;
- partner-private rows do not enter ranking, pagination, result counts, excerpts, or cursor positions.

For Dashboard:

- only shared relationship data enters the shared Dashboard;
- owner-only data is excluded even for its owner so the couple Dashboard has one stable shared privacy meaning;
- no private counts, timestamps, existence flags, or indirect metadata are projected.

See [Privacy and Test Matrix](./PRIVACY-TEST-MATRIX.md).

## Reuse-before-build result

Reuse review is **relevant** because M4-A introduces search/indexing behavior.

Selected platform capability:

- PostgreSQL built-in Full Text Search (`to_tsvector`, `websearch_to_tsquery`/equivalent bounded query construction, GIN indexes).

Alternatives reviewed:

- Elasticsearch/OpenSearch: rejected for v1 because the binding specification does not require them, they add a separate service, replication/index synchronization, operational burden, additional privacy surface, and Self-Hosted complexity without a demonstrated need;
- custom search engine/index service: rejected because PostgreSQL already provides the required capability;
- unindexed `ILIKE` scans: rejected as the primary global-search design because they do not provide the intended ranked FTS behavior and scale poorly across growing content.

The application still exposes a Search-service abstraction so a later implementation can change without leaking provider/query details into API clients.

## ProtectedPayload and index rule

Current sensitive text is stored in PostgreSQL JSONB through the `ProtectedPayload` persistence boundary. M4-A must not create an independent plaintext search table.

The approved v1 strategy is **per-table derived FTS expressions plus GIN expression indexes** over the existing ProtectedPayload JSONB fields.

Consequences:

- ProtectedPayload remains the only plaintext source of truth;
- the index is transactionally updated by PostgreSQL with the source row;
- there is no outbox-driven eventual-consistency window for Search;
- there is no search-backfill table containing copied user text;
- index data is treated as sensitive derived data and is never exported, logged, or used for analytics;
- future real E2EE work may replace server-side plaintext search; the Search abstraction and rebuildable indexes deliberately keep that migration boundary open.

## Business / freemium result

M4-A is consistent with the current freemium model:

- **basic global Search of the user's own authorized SideBySide content is Free/Core**;
- **the basic relationship Dashboard is Free/Core**;
- advanced semantic/AI Search, saved analytical views, or richer premium presentation may be classified separately later;
- no Cloud-only feature restriction or managed-resource quota is introduced by M4-A;
- Self-Hosted and Cloud use the same functional Search/Dashboard contract.

The M4-A runtime PRs must repeat the mandatory business/freemium review and update the authoritative feature matrix if product-tier scope changes.

## Definition of Ready for M4-A runtime

A runtime slice may start only when:

- [x] M3 is complete and G3 passed;
- [x] all M4-A `BLOCKING` decisions in [Decision Log](./DECISION-LOG.md) are `DECIDED`;
- [x] Search privacy, query, ranking, cursor and indexing semantics are fixed;
- [x] Dashboard sections, ordering, time semantics and privacy rules are fixed;
- [x] PostgreSQL FTS reuse decision is traceable;
- [x] basic Search and Dashboard are confirmed Free/Core;
- [x] required negative/privacy/performance evidence is specified;
- [ ] the affected runtime slice implements and publishes the concrete OpenAPI contract;
- [ ] the affected runtime slice passes normal CI/security/reuse/business/cross-cutting gates.

The last two items are per-runtime-slice conditions and are intentionally not satisfied by S0 documentation alone.

## Runtime sequence after S0

The current M4-A delivery sequence is defined in [Delivery Plan](./DELIVERY-PLAN.md):

1. **M4-A-S1 — Search Foundation**;
2. **M4-A-S2 — Dashboard Read Model**;
3. **M4-A-S3 — integrated M4-A evidence and contract/client-generation check**.

M4-B and M4-C start only through separately scoped issues after their own blocking decisions are explicit.

## Deliberately not pulled forward

- Activity feed and Notification delivery — M4-B;
- `Ich denke an dich` runtime — later M4 owning slice, not a fake M4-A placeholder;
- Reminders and Rules — M4-C;
- full Web/Android productization, Offline Read Cache and parity — M5;
- Questions and Recaps — M6;
- semantic/AI Search — later explicit scope;
- external Search provider/service — not needed for v1;
- real E2EE — MX;
- Premium entitlement runtime — M9/#262.
