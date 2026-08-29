# M2 Delivery Plan

**Goal:** deliver M2 as small, vertical, independently reviewable product increments  
**As of:** August 24, 2026

This plan starts only after the open M0/M1 gates. It creates no issue numbers and does not modify ongoing issues #5–#11. Each package is scoped so it can become exactly one issue, one branch, and one pull request.

## Entry gates

M2 implementation starts only when:

- transport and initial self-hosted registration are secure,
- auth, tenant, and concurrency invariants are protected over HTTP,
- reproducible build, dependency scan, and OpenAPI contract are established,
- provider and ProtectedPayload boundaries are sound,
- private authorization and relationship profiles are complete,
- blocking M2 decisions in the [Decision Log](./DECISION-LOG.md) are resolved.

## Delivery sequence

```text
S0 Readiness
   │
   ├── S1 Attachments ──┐
   │                    ├── S3 Memory + Media ──┐
   └── S2 Memory CRUD ──┘                       │
                                                ├── S7 Story ── S8 Clients & Hardening
       S4 HeartMoment Privacy ──────────────────┤
       S5 Milestone ────────────────────────────┤
       S6 Comments + Outbox ────────────────────┘
```

S4 and S5 may be prepared in parallel with S1–S3 after S0. S7 starts only when all four source types and their visibility rules are stable.

## S0 – M2 Readiness & contract decisions

**Outcome:** implementable, internally consistent M2 contract.

**Deliverables**

- resolve open points in the Decision Log,
- confirm domain and privacy invariants,
- adopt OpenAPI schemas and error codes from `API-DESIGN.md`,
- design migration/index plan including rollback,
- create security test cases as executable test structure,
- document M2 observability and retention rules.

**Acceptance**

- no blocking decision remains open,
- API lint and contract tests are green,
- threat review for owner-only and media is complete,
- every later slice has a clear contract and test path.

## S1 – Attachment Foundation & MediaStore

**Outcome:** secure attachment lifecycle foundation that is not yet bound to domain content.

**Deliverables**

- `Attachment` persistence and state model,
- `MediaStore` port plus local and S3-compatible adapters,
- create upload, finalize, validation, authorized read, and delete,
- random storage keys, size/MIME/dimension checks,
- cleanup for failed and orphaned uploads,
- adapter contract tests and abuse tests.

**Acceptance**

- only validated attachments reach `READY`,
- both adapters pass the same contract,
- cross-tenant, MIME-spoof, and race tests are green,
- neither bucket nor local storage is readable without authorization.

**Not included:** gallery and Memory UI. Thumbnail and poster frame are part of S1 under M2-D15; transcoding, multiple resolution levels, and adaptive streaming explicitly are not.

**Split under M2-D23:** S1 is divided into three deliverable pieces.

- **S1-a Images:** persistence, state machine, LocalMediaStore, upload, asynchronous validation including stripping and thumbnail, authorized read, delete, and cleanup — for JPEG, PNG, WebP, HEIC, and HEIF.
- **S1-b S3 Adapter:** presigned upload and Read URL against the same contract tests as the local adapter.
- **S1-c Video:** ffmpeg, MP4/QuickTime, and poster frames. Resolve image size, CVE tracking, and resource limits first.

The split ensures no intermediate state reaches `READY` without M2-D14 having been applied; otherwise an unstripped file would temporarily exist in the store.

## S2 – Memory CRUD without media

**Outcome:** Memories with author, domain date, and safe concurrency.

**Deliverables**

- Create/Get/List/Update/Delete,
- `happenedOn` separate from `createdAt`,
- author projection and space scope,
- ProtectedPayload boundary for title/body,
- optimistic concurrency and error contract,
- HTTP, tenant, and authorization tests.

**Acceptance**

- author and partner see only permitted space data,
- author can change/delete according to the decided contract,
- stale version deterministically produces `409`,
- logs/events contain no protected content.

## S3 – Memory with multiple media items

**Outcome:** a Memory can present multiple authorized media items in stable order.

**Deliverables**

- attachment relation and stable ordering,
- atomic bind/unbind operations,
- gallery projection for Web and Android,
- handle parent-delete/finalize race,
- tolerate missing/failed media in presentation.

**Acceptance**

- no cross-space binding,
- order remains stable across update and read,
- deleted/invalid parents leave no visible orphans,
- no attachment grants more visibility than its parent.

## S4 – HeartMoment with owner-only privacy

**Outcome:** `SHARED` and `PRIVATE` are separated correctly in every access path.

**Deliverables**

- CRUD with emotion, visibility, date, and optional attachment,
- owner-only policy as a central reusable rule,
- list/search/projection filters,
- privacy-safe error semantics,
- complete canary and indirect leak tests.

**Acceptance**

- partner can neither directly nor indirectly detect private entries,
- changing `SHARED → PRIVATE` removes comment/Story/cache visibility according to contract,
- optional attachment follows parent visibility exactly,
- export, event, and notification paths are tested.

## S5 – Milestone

**Outcome:** Milestones are a distinct domain model.

**Deliverables**

- CRUD, author, and `happenedOn`,
- tenant/concurrency/ProtectedPayload rules,
- projection for Story and later Chapter/Recap integration,
- HTTP and isolation tests.

**Acceptance**

- no hidden reuse of Memory tables or type flags,
- Story-relevant fields are stable,
- later extensions require no M2 data migration out of a catch-all model.

## S6 – Comments, Outbox & Notification Hook

**Outcome:** comments work only on allowed shared targets and reliably emit a minimal event.

**Deliverables**

- enumerated targets `MEMORY`, `MILESTONE`, `HEART_MOMENT`,
- Create/List/Update/Delete according to author rule,
- central target-existence and visibility checks,
- atomic Outbox entry for a comment on another person's shared content,
- idempotent worker/notification interface.

**Acceptance**

- no comments on private or foreign content,
- domain change and Outbox commit atomically,
- retry creates no duplicate domain notifications,
- event/preview contains no unauthorized content.

## S7 – Story Read Model

**Outcome:** a derived, performant timeline without private leaks.

**Deliverables**

- Query Service for Memory, Milestone, and shared HeartMoment only,
- author and attachment projection,
- filters `type`, `year`, `order`, `cursor`, `limit`,
- stable cursor pagination and month groups,
- query/index analysis using realistic data volumes.

`q` is intentionally no longer listed here. M2-D08 moved global full-text search to M4-A, and M2-D21 leaves open whether it is implemented directly in Postgres or through a separate index. The earlier entry came from the version before #70 and would have made S7 implement search that the frozen contract does not contain.

Under M2-D22 (#104), the owner area for private HeartMoments is not part of this route: `/timeline` remains a purely shared Read Model without a `visibility` parameter, and the owner view is served by the existing HeartMoment collection.

**Acceptance**

- `PRIVATE` is excluded before search, count, grouping, and cursor construction,
- sorting and tie-breaker match the decision,
- pages are stable and duplicate-free,
- Read Model is derived and not a second domain source of truth.

## S8 – Initial Web/Android flows & hardening

**Outcome:** the same core flow works end to end on both clients.

**Deliverables**

- view Story, create Memory, add multiple media items,
- intentionally create HeartMoment as shared or private,
- loading/empty/error/offline-read states,
- accessibility, dynamic type, touch targets, and keyboard flow,
- cache clearing on logout/space change,
- end-to-end and release smoke tests.

**Acceptance**

- Web and Android use the same published API contract,
- privacy decision is understandable before saving,
- no illusion of offline writes,
- core flow is operable with screen reader/keyboard or TalkBack.

## Issue-ready work packages

The following titles can be created directly as issues after S0:

1. **[M2][Media] Implement attachment lifecycle and MediaStore contract**
2. **[M2][Media] Validate LocalMediaStore and S3MediaStore against a shared contract**
3. **[M2][Memory] Deliver Memory CRUD, ProtectedPayload, and concurrency**
4. **[M2][Memory] Integrate multiple attachments and ordered gallery**
5. **[M2][Privacy] Deliver HeartMoment shared/private with complete owner-only protection**
6. **[M2][Milestone] Deliver distinct Milestone model and API**
7. **[M2][Comments] Implement allowed targets, Outbox, and Notification Hook**
8. **[M2][Story] Deliver derived Read Model with search and cursor pagination**
9. **[M2][Web] Integrate Story, Memory, and privacy core flow**
10. **[M2][Android] Integrate Story, Memory, and privacy core flow**
11. **[M2][Security] Complete cross-tenant, owner-only, and media-abuse suite**
12. **[M2][Release] Accept performance, accessibility, and observability**

Each issue adopts the relevant rows from the [Security Test Matrix](./SECURITY-TEST-MATRIX.md) as acceptance criteria. Cross-cutting work is not hidden in a catch-all PR.

## PR rules

- one issue, one branch, one domain purpose,
- migration and rollback in the same PR as the model,
- contract first or in the same PR; clients never target undocumented endpoints,
- do not duplicate auth/tenant logic per controller,
- security tests must be demonstrably red before the fix and green afterward,
- record new decisions in the Decision Log,
- validate screens and API together against empty, error, and authorization states.

## M2 Exit Criteria

M2 is complete when:

- all six domain building blocks are production-usable,
- Web and Android share at least one complete Memory/Media/Story flow,
- private HeartMoments pass all leak tests,
- local and S3 media satisfy the same security contract,
- OpenAPI, migrations, observability, and operational documentation are current,
- no critical or high security gap remains open,
- performance budgets and accessibility acceptance are satisfied,
- real E2EE is neither claimed nor architecturally blocked.
