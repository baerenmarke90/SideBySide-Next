# M4 Delivery Plan

**Status:** M4-A S0 ready; runtime slices pending  
**As of:** August 30, 2026  
**Owning readiness issue:** #272

This plan sequences M4-A after G3. It deliberately keeps M4-B and M4-C separate so Search/Dashboard implementation does not silently expand into Notifications/Reminders/Rules.

## M4-A sequence

```text
S0 Readiness / Contract (#272)
        |
        +--> S1 Search Foundation
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

Deliverables:

- M4 package/precedence;
- complete blocking Decision Log;
- Search design;
- Dashboard design;
- Privacy/Test Matrix;
- runtime delivery sequence;
- Reuse-before-build and business/freemium decisions.

Exit:

- all M4-A `BLOCKING` decisions `DECIDED`;
- no runtime Search/Dashboard implementation in S0;
- normal repository gates green.

## M4-A-S1 — Search Foundation

Create a dedicated issue after S0 merge.

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

Create a dedicated issue after S0 merge; it may proceed after S1 or in parallel only if the branch/contract overlap remains low and `main` stays synchronized.

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

## M4-B — Activity + Notifications

M4-B is not released by #272.

Before runtime it needs an owning issue/decision set for at least:

- Activity event sources and retention;
- user-visible Notification vs. internal Outbox distinction;
- notification preview privacy;
- deduplication/idempotency;
- read/unread model;
- push boundary and no sensitive lock-screen content by default;
- `Ich denke an dich` event/notification semantics if owned here;
- business/freemium classification.

## M4-C — Reminders + Rules

M4-C is not released by #272.

Before runtime it needs an owning issue/decision set for at least:

- Reminder ownership/shared vs personal semantics;
- ONCE/ANNUAL/RELATIONSHIP_DAY_COUNT schedule behavior;
- timezone/DST rules;
- offset validation;
- automatic Reminder source and edit restrictions;
- RulePreference/catalog contract;
- idempotent scheduling/delivery;
- business/freemium split between basic and advanced automation.

## Parallelism rule

Parallel work is allowed only when branches do not compete for the same authoritative contract/migration surface.

Examples:

- S1 Search indexes/service and S2 Dashboard service may be parallelized **after S0** if OpenAPI/router/client-generation conflicts are coordinated;
- two branches that both edit the same generated OpenAPI/client surfaces should normally serialize or synchronize through merge commits rather than rely on rebase;
- M4-B/M4-C must not begin from unresolved semantics merely to increase parallelism.

## Definition of Done per runtime slice

A runtime slice is not done until:

- source decision remains satisfied;
- business/freemium result is traceable;
- Reuse-before-build is traceable where relevant;
- API/OpenAPI/generated clients are synchronized;
- Tenant/Privacy negative tests pass;
- PostgreSQL integration evidence exists for query/index semantics;
- cross-cutting review is complete;
- branch is current enough for repository rules;
- all required CI checks are green before Merge Commit.
