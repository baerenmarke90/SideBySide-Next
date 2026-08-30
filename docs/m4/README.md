# M4 Technical Readiness Package

**Status:** M4-A and M4-B S0 decisions complete; M4-C readiness tracked by #277  
**As of:** August 30, 2026  
**M4-A tracking:** #272  
**M4-B tracking:** #276  
**M4-C tracking:** #277

M4 — Engage follows M3/G3 and remains split into separate risk classes:

- **M4-A:** Search + Dashboard Read Models;
- **M4-B:** Activity + Notifications;
- **M4-C:** Reminders + Rules.

M4-A and M4-B now have explicit readiness contracts. M4-C remains blocked from runtime until its own S0 decision package is merged.

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

Questions remain M6. Comments, Profiles, RelatedPersons and ImportantDates are deliberately not part of the first global Search contract.

Detailed contract: [Search Design](./SEARCH-DESIGN.md).

### Dashboard

Dashboard is a derived Read Model. There is no `dashboard` table, copied Domain payload, or separate persisted dashboard truth.

The first M4-A Dashboard derives only data whose owning Domain already exists:

- Space/partner summary;
- optional relationship duration;
- deterministic basic retrospective (`Weißt du noch?`) from authorized shared history;
- upcoming scheduled Plans and date-based relationship items;
- recent shared root content.

`Ich denke an dich` is not faked by M4-A. M4-B owns its runtime contract. Activity/Notification/Reminder/Rule data remains absent until its owning M4 slice delivers it. Questions/Year Summary remain M6.

Detailed contract: [Dashboard Design](./DASHBOARD-DESIGN.md).

### M4-A privacy rule

M4-A Read Models are authorization-first, not projection-first.

For Search:

- shared results require active Membership and matching `space_id`;
- owner-only rows require `owner_id == current_account_id` in SQL/authorized joins;
- partner-private rows do not enter ranking, pagination, counts, excerpts or cursor positions.

For Dashboard:

- only shared relationship data enters the shared Dashboard;
- owner-only data is excluded even for its owner;
- no private counts, timestamps, existence flags or indirect metadata are projected.

Detailed evidence contract: [M4-A Privacy and Test Matrix](./PRIVACY-TEST-MATRIX.md).

## M4-B product boundary

M4-B keeps four concepts separate:

```text
OutboxEvent   = internal transactional integration fact
Activity      = user-visible shared Space event
Notification  = recipient-specific state
PushDelivery  = technical delivery attempt/channel
```

Detailed contract: [Activity and Notification Design](./ACTIVITY-NOTIFICATIONS-DESIGN.md).

### Activity

Activity is a persisted, minimized asynchronous projection of a controlled set of committed safe Outbox facts.

The initial feed includes only selected shared meaningful events such as creation of Memory/Milestone/SHARED HeartMoment/Wish/Plan/Place/Chapter/Collection, Plan completion and Comment creation.

It deliberately excludes:

- `OWNER_ONLY` events;
- ordinary edits/reorders/item toggles;
- Auth/Audit/Job/Outbox/Attachment-processing internals;
- worker/provider attempts;
- `Ich denke an dich` in v1.

Activity stores stable kinds/references, not copied ProtectedPayload plaintext. Current target authorization is re-evaluated before projection.

### Notifications

Notification is Account+Space recipient state with server-authored read/unread status.

- recipients are derived server-side;
- a Notification never grants target access;
- stale/deleted/newly-private targets cannot continue to leak through rows or unread counts;
- mark-one-read is idempotent;
- mark-all-read uses a server transaction cutoff so newer Notifications stay unread;
- Notification persistence stores safe references/kinds, not copied relationship plaintext.

### `Ich denke an dich`

M4-B owns the v1 content-free partner nudge.

- no free-text payload;
- no separate durable content object;
- recipient derived from the other active Space Membership;
- caller-generated `clientRequestId` provides retry idempotency;
- one new logical send per sender/Space per rolling 60 seconds, plus normal rate limiting;
- creates recipient Notification and optional PushDelivery;
- does not create Activity feed noise in v1.

### Push

Push is optional delivery for an existing Notification through a provider-neutral adapter.

Default push/lock-screen presentation contains no protected relationship plaintext. Rich previews require a later explicit opt-in privacy decision.

Self-Hosted without configured push remains fully functional for Activity, in-app Notifications/read state and in-app `Ich denke an dich` delivery.

Detailed evidence contract: [M4-B Activity and Notification Privacy/Test Matrix](./ACTIVITY-NOTIFICATIONS-PRIVACY-TEST-MATRIX.md).

## Reuse-before-build results

Reuse review is relevant for M4-A and M4-B.

### M4-A

Selected:

- PostgreSQL built-in Full Text Search (`to_tsvector`, bounded tsquery construction, GIN indexes);
- existing signed cursor infrastructure.

Rejected for v1:

- Elasticsearch/OpenSearch;
- custom search/index service;
- unindexed `ILIKE` as primary global Search.

### M4-B

Selected/reused:

- existing transactional Outbox;
- existing minimized safe event payload boundary;
- existing PostgreSQL Job Queue;
- existing `FOR UPDATE SKIP LOCKED` lease behavior;
- existing retry/exponential backoff;
- existing content-free COMMENT_CREATED notification hook as a proven pattern.

Not introduced by M4-B:

- Redis;
- Celery;
- Kafka/RabbitMQ;
- another event store/message broker;
- copied plaintext Activity documents;
- a provider-specific push dependency inside Domain services.

## Business / freemium results

M4 currently promotes the following runtime classifications:

- basic authorized global Search: **Free/Core**;
- basic relationship Dashboard: **Free/Core**;
- basic shared Activity: **Free/Core**;
- basic in-app Notification/read state: **Free/Core**;
- basic `Ich denke an dich`: **Free/Core**;
- basic push capability when infrastructure is configured: **Free/Core capability**, with transport availability/configuration treated separately from product entitlement.

Potential later Premium extensions remain separate decisions, for example semantic/AI Search, advanced analytical views, notification digests/routing, rich preview customization or advanced automation.

M4-B introduces no Premium entitlement runtime. M9/#262 remains the entitlement/billing implementation boundary.

## Definition of Ready for M4-A runtime

- [x] M3 complete and G3 passed;
- [x] all M4-A blocking decisions `DECIDED`;
- [x] Search privacy/query/ranking/cursor/index semantics fixed;
- [x] Dashboard sections/ordering/time/privacy semantics fixed;
- [x] PostgreSQL FTS reuse decision traceable;
- [x] Search and Dashboard confirmed Free/Core;
- [x] required negative/privacy/performance evidence specified;
- [ ] each runtime slice publishes its concrete OpenAPI contract;
- [ ] each runtime slice passes normal CI/security/reuse/business/cross-cutting gates.

## Definition of Ready for M4-B runtime

- [x] Activity/Notification/PushDelivery/Outbox distinction fixed;
- [x] Activity event catalog and exclusions fixed;
- [x] Activity/Notification privacy-transition semantics fixed;
- [x] read/unread/unread-count semantics fixed;
- [x] cursor/pagination semantics fixed;
- [x] `Ich denke an dich` ownership/idempotency/cooldown fixed;
- [x] generic push privacy and Self-Hosted-unconfigured behavior fixed;
- [x] existing Outbox/Job infrastructure selected for reuse;
- [x] M4-B Free/Core classification fixed;
- [x] mandatory negative/concurrency/delivery evidence specified;
- [ ] each runtime slice publishes its concrete OpenAPI contract;
- [ ] each runtime slice passes normal CI/security/reuse/business/cross-cutting gates.

## M4 runtime sequence

See [Delivery Plan](./DELIVERY-PLAN.md).

Current sequences:

1. **M4-A-S1 — Search Foundation** (#274/#275 at the time of this decision);
2. **M4-A-S2 — Dashboard Read Model**;
3. **M4-A-S3 — integrated M4-A evidence**;
4. **M4-B-S1 — Activity + in-app Notification foundation**;
5. **M4-B-S2 — `Ich denke an dich` + PushDelivery boundary**;
6. **M4-B-S3 — integrated M4-B evidence**;
7. **M4-C** only after #277 freezes its own blocking semantics.

Parallel implementation is allowed only where migration/router/OpenAPI/generated-client surfaces are coordinated and authoritative contracts do not conflict.

## Deliberately not pulled forward

- M4-C Reminder/Rule runtime before #277 readiness;
- full Web/Android productization, Offline Read Cache and parity — M5;
- Questions and Recaps — M6;
- semantic/AI Search — later explicit scope;
- real E2EE — MX;
- Premium entitlement runtime — M9/#262.
