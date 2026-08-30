# M4 Decision Log

**As of:** August 30, 2026  
**M4-A S0 status:** all M4-A blocking decisions below are `DECIDED`  
**Rule:** Search/Dashboard semantics are not invented silently in runtime code.

## Status

- `OPEN` — decision missing;
- `PROPOSED` — preferred option documented but not binding;
- `DECIDED` — binding for the affected M4 slice.

## Priority

- `BLOCKING` — decide before the first affected runtime slice;
- `BEFORE_CLIENTS` — decide before stable Web/Android integration;
- `BEFORE_EVIDENCE` — decide before M4-A integrated evidence;
- `LATER` — deliberately outside the current slice.

## Decision matrix

| ID | Priority | Status | Topic | Binding decision |
|---|---|---|---|---|
| M4-D01 | BLOCKING | DECIDED | M4 risk split | M4-A = Search + Dashboard, M4-B = Activity + Notifications, M4-C = Reminders + Rules. One risk class does not silently pull another forward. |
| M4-D02 | BLOCKING | DECIDED | Search backend | v1 uses PostgreSQL Full Text Search behind an application Search abstraction. No Elasticsearch/OpenSearch service is introduced. |
| M4-D03 | BLOCKING | DECIDED | Search shared targets | Initial shared targets: Memory, SHARED HeartMoment, Milestone, Wish, Plan, Place, Chapter, Collection and CollectionItem. Wish is included because the Master Spec list is an `at minimum` set and basic shared planning must be discoverable consistently. |
| M4-D04 | BLOCKING | DECIDED | Search private targets | The caller may search their own PRIVATE HeartMoments, PrivateNotes, GiftIdeas, PrivateCollections and PrivateCollectionItems. Partner-private rows are excluded by SQL/authorized joins before ranking/projection. |
| M4-D05 | BLOCKING | DECIDED | Deferred Search targets | Questions wait for M6. Comments, Profiles, RelatedPersons and ImportantDates are outside the first global Search contract. Adding them later requires an explicit contract/privacy review. |
| M4-D06 | BLOCKING | DECIDED | Search text fields | Search only user-authored human-readable fields. Titles/names receive higher ranking weight than body/description/address/item text. Statuses, IDs, coordinates, privacy classes, URLs, enum emotions and technical metadata are not lexemes merely to make them searchable. |
| M4-D07 | BLOCKING | DECIDED | Query normalization | Normalize query to Unicode NFC, trim leading/trailing Unicode whitespace, collapse internal whitespace runs, require 2-200 Unicode characters after normalization. Invalid/empty input returns a stable validation error. |
| M4-D08 | BLOCKING | DECIDED | FTS configuration | v1 uses PostgreSQL `simple` text-search configuration to avoid locale inference and stop-word/stemming data loss across multilingual user-generated content. Locale-specific stemming may be introduced later behind the Search abstraction. |
| M4-D09 | BLOCKING | DECIDED | Query parser | The repository may use PostgreSQL `websearch_to_tsquery('simple', ...)` or an equivalent bounded helper internally. Provider/parser syntax is not exposed as an API contract; the public contract is a plain user query string. |
| M4-D10 | BLOCKING | DECIDED | Ranking | Rank by weighted PostgreSQL FTS coverage/density only; no recency boost. Recency is a deterministic tie-breaker so old relationship history is not systematically demoted merely for age. Ranking score is internal and not an API field. |
| M4-D11 | BLOCKING | DECIDED | Search pagination | Signed opaque keyset cursor. Order: normalized rank descending, deterministic domain sort timestamp/date descending where present, result type ascending, resource ID ascending. Cursor binds Account, Space, normalized query, normalized type filter set and sort-contract version. |
| M4-D12 | BLOCKING | DECIDED | Search page size | Default `limit=25`, allowed range 1-50. Offset pagination is not part of the contract. |
| M4-D13 | BLOCKING | DECIDED | Search index storage | No universal search table and no copied plaintext search document. Use per-table weighted `to_tsvector('simple', ...)` expressions over existing ProtectedPayload JSONB with GIN expression indexes. Child item tables receive their own indexes. |
| M4-D14 | BLOCKING | DECIDED | Search consistency | Search index state is transactionally maintained by PostgreSQL expression indexes with source-row writes. No outbox/worker indexing pipeline in v1; therefore no accepted eventual-consistency window. |
| M4-D15 | BLOCKING | DECIDED | Search result contract | Result DTO carries type, resource ID, optional parent ID for child items, server-derived scope (`SHARED`/`PRIVATE`), title/label where the domain has one, bounded plain-text excerpt where useful, and optional domain date. No HTML highlight, rank score, raw payload, coordinates, or technical metadata. |
| M4-D16 | BLOCKING | DECIDED | Search cache/observability | Search responses use private/no-store semantics in v1. Query text, result excerpts and private resource identifiers are not logged or metric labels. Aggregate latency/result-count metrics may not carry user content. |
| M4-D17 | BLOCKING | DECIDED | Dashboard persistence | Dashboard is derived from real Domain tables at request time. No dashboard table, copied ProtectedPayload or persisted section counters in M4-A. |
| M4-D18 | BLOCKING | DECIDED | Dashboard first sections | First response: Space/partner summary, optional relationship duration, basic retrospective, upcoming items and recent shared items. No fake Activity/Notification/Reminder/Question/Year Summary data. |
| M4-D19 | BLOCKING | DECIDED | Dashboard privacy | Dashboard is a shared Space surface and therefore excludes all `OWNER_ONLY` rows even for their owner. Private counts/existence/timestamps cannot influence section presence, totals or ordering. |
| M4-D20 | BLOCKING | DECIDED | Relationship duration | Return a derived duration object only when `showRelationshipDuration` is enabled and a start date exists. Use caller-local calendar date for day-count derivation; clients localize presentation according to `durationDisplayMode`. |
| M4-D21 | BLOCKING | DECIDED | Retrospective | Basic `Weißt du noch?` uses authorized shared Memory/Milestone/SHARED HeartMoment with an exact month/day match from a prior year. Most recent prior year wins; stable type/ID tie-breakers apply. If no candidate exists, omit the section. No private data and no plaintext scoring. |
| M4-D22 | BLOCKING | DECIDED | Upcoming items | Initial upcoming set: future PLANNED Plan starts, ImportantDate next occurrences, RelatedPerson birthdays when present, and relationship anniversary when derivable. Date-only recurrence is evaluated using the caller's configured timezone; clients receive typed dates/instants, not localized prose. |
| M4-D23 | BLOCKING | DECIDED | Recent shared items | Use newly created shared root content from Memory, Milestone, SHARED HeartMoment, Wish, Plan, Place, Chapter and Collection ordered by `createdAt DESC`, type, ID. Edits/reorders do not masquerade as Activity; Activity belongs to M4-B. Default section limit 8. |
| M4-D24 | BLOCKING | DECIDED | `Ich denke an dich` boundary | M4-A does not emit a placeholder/false status. The field/section is absent until the owning M4 runtime slice exists and has its own contract. |
| M4-D25 | BLOCKING | DECIDED | Dashboard empty behavior | Optional sections are omitted when empty; the response does not fabricate zero-state domain rows. Stable top-level structure may expose explicit nullable/empty collections only where the final OpenAPI contract benefits clients. |
| M4-D26 | BLOCKING | DECIDED | Dashboard consistency/cache | Use one application unit of work with normal authorized reads; cross-section atomic snapshot semantics are not promised because Dashboard is not a transactional report. Short-lived inconsistencies under concurrent writes are acceptable, Privacy violations are not. Response is `private, no-store` in v1. |
| M4-D27 | BEFORE_CLIENTS | DECIDED | Client boundary | M4-A runtime must publish OpenAPI and regenerate TypeScript/Kotlin clients. Full Search/Dashboard screen productization, offline Read Cache and systematic parity remain M5 unless a thin evidence flow is explicitly scoped. |
| M4-D28 | BLOCKING | DECIDED | Freemium | Basic authorized global Search and the basic relationship Dashboard are Free/Core in both Cloud and Self-Hosted. Semantic/AI search, saved analytical views or richer Premium presentation remain separate future decisions. |
| M4-D29 | BEFORE_EVIDENCE | DECIDED | Mandatory evidence | Real PostgreSQL tests must prove index-backed matching, cursor binding, Cross-Tenant isolation, partner-private non-generation, private child-parent authorization, deterministic ordering, Dashboard owner-only exclusion and no private influence on shared section shape. |
| M4-D30 | LATER | DECIDED | Search backend replacement/E2EE | A later backend or real E2EE search strategy may replace server-side plaintext FTS behind the Search abstraction. M4-A does not claim server-side FTS is compatible with real E2EE ciphertext. |

## Closure rule

A `DECIDED` M4-A semantic is not silently changed in a runtime PR. A change requires an explicit decision update with:

- API/client compatibility impact;
- persistence/index migration impact;
- Privacy/Tenant implications;
- Self-Hosted/Cloud implications;
- business/freemium impact;
- required negative/integration tests.
