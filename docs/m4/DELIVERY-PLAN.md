# M4 Delivery Plan

**Status:** M4-A and M4-B S0 decisions ready; M4-C readiness pending #277  
**As of:** August 30, 2026  
**M4-A readiness:** #272  
**M4-B readiness:** #276  
**M4-C readiness:** #277

This plan sequences M4 after G3 while keeping Search/Dashboard, Activity/Notifications and Reminders/Rules in separate risk classes.

## M4-A sequence

```text
S0 Readiness / Contract (#272)
        |
        +--> S1 Search Foundation (#274)
        |       |
        |       +--> PostgreSQL FTS expressions + GIN indexes
        |       +--> Search abstraction/repository
        |       +--> /search API + OpenAPI
        |       +--> privacy/cursor/integration evidence
        |
        +--> S2 Dashboard Read Model
        |       |
        |       +--> shared-only projections
        |       +--> relationship duration
        |       +--> retrospective
        |       +--> upcoming
        |       +--> recent shared
        |       +--> /dashboard API + OpenAPI
        |
        +--> S3 Integrated M4-A evidence
                |
                +--> generated client parity check
                +--> cross-target privacy regression set
                +--> performance/query evidence
                +--> status synchronization
```

S1 and S2 may be implemented sequentially from the same S0 contract. They should not be combined into one oversized runtime PR merely because both are read models.

## M4-A-S0 — readiness and contracts

**Owner:** #272  
**Runtime changes:** none  
**Status:** delivered

Deliverables:

- M4 package/precedence;
- complete M4-A blocking Decision Log;
- Search design;
- Dashboard design;
- M4-A Privacy/Test Matrix;
- runtime delivery sequence;
- Reuse-before-build and business/freemium decisions.

## M4-A-S1 — Search Foundation

**Owner:** #274  
**Runtime PR:** #275 at the time of the M4-B readiness decision

Scope:

- per-target PostgreSQL FTS expression indexes/migration;
- application Search abstraction and PostgreSQL implementation;
- authorized multi-target query;
- owner-only/private branches;
- Search DTOs and `/api/v1/spaces/{spaceId}/search`;
- signed Account+Space+query+filter-bound keyset cursor;
- OpenAPI and generated TypeScript/Kotlin clients;
- unit/PostgreSQL/HTTP privacy tests from `PRIVACY-TEST-MATRIX.md`;
- representative query-plan/index evidence.

Explicitly out:

- Dashboard;
- semantic/vector/AI Search;
- external Search service;
- persistent client Search cache;
- full Search client UI.

Business classification:

- basic Search = Free/Core.

Reuse result:

- PostgreSQL built-in FTS + existing signed cursor infrastructure;
- no new search daemon/provider/dependency unless a new explicit decision supersedes S0.

## M4-A-S2 — Dashboard Read Model

Create a dedicated issue after/around S1 only when contract/client overlap is coordinated.

Scope:

- shared-only Dashboard service/read repository;
- Space/partner summary;
- optional relationship duration;
- basic exact-date retrospective;
- upcoming Plans/ImportantDates/birthdays/anniversary;
- recent shared root items;
- `/api/v1/spaces/{spaceId}/dashboard`;
- OpenAPI and regenerated clients;
- privacy/indirect-leakage tests;
- bounded query-count/performance evidence.

Explicitly out:

- Activity;
- Notifications;
- Reminder-derived cards;
- `Ich denke an dich` runtime;
- Rules/Suggestions;
- Questions/Recaps;
- full Dashboard UI productization.

Business classification:

- basic Dashboard = Free/Core.

## M4-A-S3 — integrated evidence and status sync

Goal:

Prove Search and Dashboard together do not introduce a cross-domain privacy/read-model regression.

Evidence includes at minimum:

- real HTTP + PostgreSQL Search across representative shared/private targets;
- partner-private Search non-generation;
- Account-bound cursor replay rejection;
- Search update/delete/privacy-transition consistency;
- Dashboard owner-only non-influence;
- deterministic retrospective/upcoming/recent behavior;
- published OpenAPI and generated-client consistency;
- representative performance/query evidence;
- current normal CI/CodeQL/Supply Chain/Self-Hosted gates.

S3 is evidence/status work, not a feature-expansion opportunity.

---

# M4-B — Activity + Notifications

M4-B readiness is owned by #276.

Binding design:

- `ACTIVITY-NOTIFICATIONS-DESIGN.md`;
- `ACTIVITY-NOTIFICATIONS-PRIVACY-TEST-MATRIX.md`;
- `DECISION-LOG.md` M4-D31 through M4-D46.

## M4-B sequence

```text
S0 Readiness / Contract (#276)
        |
        +--> S1 Activity + in-app Notification Foundation
        |       |
        |       +--> Activity/Notification persistence
        |       +--> safe Outbox projector
        |       +--> controlled event catalog
        |       +--> Activity/Notification APIs
        |       +--> read/unread + unread count
        |       +--> OpenAPI/generated clients
        |
        +--> S2 Thinking-of-you + PushDelivery Boundary
        |       |
        |       +--> idempotent content-free nudge command
        |       +--> server-derived partner recipient
        |       +--> cooldown/abuse safeguard
        |       +--> provider-neutral PushDelivery adapter
        |       +--> generic lock-screen-safe payload
        |       +--> Self-Hosted no-provider behavior
        |
        +--> S3 Integrated M4-B Evidence
                |
                +--> Cross-Tenant/OWNER_ONLY regression
                +--> privacy-transition evidence
                +--> projector/job retry/idempotency
                +--> read-state concurrency
                +--> push payload/privacy evidence
                +--> status synchronization
```

M4-B runtime must not be combined into one oversized PR merely because Activity and Notification share source events.

## M4-B-S0 — readiness and contracts

**Owner:** #276  
**Runtime changes:** none  
**Status:** ready when the owning documentation PR merges

Deliverables:

- Activity/Notification/PushDelivery model split;
- controlled Activity event catalog;
- Notification recipient/read/unread contract;
- source-deletion/privacy-transition behavior;
- `Ich denke an dich` ownership/idempotency/cooldown;
- push privacy/provider/Self-Hosted boundary;
- Reuse-before-build decision using existing Outbox/Jobs;
- business/freemium classification;
- dedicated privacy/test matrix;
- concrete runtime sequence.

## M4-B-S1 — Activity + in-app Notification foundation

Create a dedicated issue only after M4-B-S0 merges.

Scope:

- Activity and Notification persistence/migrations;
- idempotent safe-Outbox projector;
- controlled v1 Activity/Notification source mapping;
- authorization-first current-target projection;
- Activity API with Account+Space-bound keyset cursor;
- Notification list/unread-count APIs;
- idempotent mark-one-read and cutoff-safe mark-all-read;
- OpenAPI and regenerated TypeScript/Kotlin clients;
- unit/PostgreSQL/HTTP evidence from the M4-B privacy/test matrix.

Explicitly out:

- Push provider selection;
- `Ich denke an dich` send runtime;
- Reminder/Rule scheduling;
- full Activity/Notification client screens (M5).

Business classification:

- basic Activity and in-app Notifications = Free/Core.

Reuse result:

- transactional Outbox + PostgreSQL Job Queue where asynchronous work is required;
- no new broker/queue stack.

## M4-B-S2 — `Ich denke an dich` + PushDelivery boundary

Create a dedicated issue after S1 or in parallel only if migration/API overlap remains low and main is synchronized.

Scope:

- content-free `POST /api/v1/spaces/{spaceId}/thinking-of-you`;
- `clientRequestId` idempotency;
- server-derived active partner recipient;
- rolling 60-second sender/Space cooldown;
- recipient in-app Notification;
- provider-neutral PushDelivery persistence/adapter/job boundary;
- stable logical push idempotency identity;
- generic no-sensitive-plaintext push presentation;
- deterministic Self-Hosted-unconfigured behavior;
- provider fake/adapter tests.

Explicitly out:

- user-authored thinking-of-you text;
- rich lock-screen previews;
- notification digests/routing automation;
- final Android distribution/push-provider commercial setup;
- entitlement runtime.

Business classification:

- basic `Ich denke an dich` and push capability = Free/Core; transport configuration remains an operating-model concern.

## M4-B-S3 — integrated evidence and status sync

Goal:

Prove engagement projections and delivery state do not create a new privacy/tenant leak or duplicate-effect path.

Evidence includes at minimum:

- real HTTP + PostgreSQL Activity/Notification behavior;
- Cross-Tenant isolation;
- `OWNER_ONLY` non-generation/non-influence;
- SHARED-to-PRIVATE target transition suppression;
- source-delete behavior;
- Account-bound cursor replay rejection;
- recipient/read/unread isolation;
- mark-all/new-notification concurrency;
- projector duplicate processing;
- Job Queue retry/worker-crash scenarios;
- safe generic push payload;
- Self-Hosted without push provider;
- `Ich denke an dich` recipient derivation/idempotency/cooldown;
- published OpenAPI/generated-client consistency;
- representative query/performance evidence;
- normal CI/CodeQL/Supply Chain/Self-Hosted gates.

S3 is evidence/status work, not a feature-expansion opportunity.

---

# M4-C — Reminders + Rules

M4-C readiness is owned separately by #277.

No M4-C runtime may start until #277 freezes at least:

- Reminder shared/personal ownership decision;
- `ONCE`/`ANNUAL`/`RELATIONSHIP_DAY_COUNT` schedule parameters;
- timezone/DST/leap-day behavior;
- offset validation;
- manual vs generated Reminder edit/source semantics;
- Rule catalog/`RulePreference` contract;
- scheduling/occurrence/idempotency model;
- M4-C-to-M4-B Notification handoff;
- business/freemium split between basic and advanced automation.

## Parallelism rule

Parallel work is allowed only when branches do not compete for the same authoritative contract/migration/generated-client surface.

Examples:

- M4-A Search code and docs-only M4-B/M4-C readiness may proceed in parallel;
- M4-B-S1 and a later M4-A runtime slice may proceed only when migration/router/OpenAPI/client-generation overlap is coordinated;
- two branches that both edit the same generated OpenAPI/client surfaces should normally serialize or synchronize through merge commits rather than rely on rebase;
- M4-C runtime must not begin from unresolved schedule/time/privacy semantics merely to increase parallelism.

## Definition of Done per runtime slice

A runtime slice is not done until:

- source decision remains satisfied;
- business/freemium result is traceable;
- Reuse-before-build is traceable where relevant;
- API/OpenAPI/generated clients are synchronized;
- Tenant/Privacy negative tests pass;
- PostgreSQL integration evidence exists for persistence/concurrency/query semantics;
- cross-cutting review is complete;
- branch is current enough for repository rules;
- all required CI checks are green before Merge Commit.
