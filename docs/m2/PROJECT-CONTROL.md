# M2 Project Control

**As of:** August 26, 2026  
**Status:** M2 complete; G2 passed; M3 approved  
**Current `main`:** `3a7adc28643ef00de51db678ec77a82be652283d` (merge of #170)

## Binding gate status

The dated [final G2 Gate Review](../reviews/2026-08-26-g2-final-gate-review.md) is the current gate decision:

- **G2: PASSED**
- **M2: COMPLETE**
- **M3: APPROVED**
- M3-S0 readiness is complete; all M3-D01 through M3-D32 are `DECIDED`
- M3 runtime slices may begin according to `docs/m3/README.md` and `docs/m3/DELIVERY-PLAN.md` once the corresponding production REST/OpenAPI contract is concretely contract-testable
- public/managed exposure is not yet approved; #59 and #60 remain pre-exposure gates
- #25 remains repository hardening

Older dated reviews remain historical snapshots and are not rewritten. In particular, the earlier G2 interim review remains unchanged as evidence of the incomplete gate status at that time.

## Milestone boundaries

### M2 – Remember / Story Alpha

M2 delivers the domain and API for Attachment, Memory, HeartMoment, Milestone, Comment, and Story plus **minimal vertical reference flows** on Web and Android. These reference flows prove the critical end-to-end contract; they do not yet mean full client parity.

The G2 minimum evidence was completed in full:

- M2 domain and versioned API contract complete for G2 scope; Attachment/Media is limited to images,
- tenant/owner-only/media security gates green,
- real critical Memory/Media/Story flow validated on Web and Android against the same SideBySide stack,
- no open high/critical M2 security/privacy/data-integrity gap,
- current CI, secret-scan, supply-chain, and deployment gates green.

Manual accessibility acceptance is intentionally **no longer a G2 blocker**. It was not claimed as passed and remains part of M5/G4 as final client/release QA.

Global full-text search is not part of G2. For G2, Story requires `type`, `year`, `order`, `cursor`, and `limit`; global search belongs to M4-A.

### M3 – Plan & Private Area

Wishes, Plans, Places, Chapters, Collections, and Private Area. Domain S0 readiness is complete; all M3-D01 through M3-D32 are `DECIDED`. The binding next source is the [M3 Technical Readiness Package](../m3/README.md) with the [M3 Delivery Plan](../m3/DELIVERY-PLAN.md).

Private Area is a security domain with hard `OWNER_ONLY` semantics, not merely a visual folder. Runtime starts slice by slice and only with an unambiguously contract-testable production REST/OpenAPI contract.

### M4 – Accompany

The milestone remains domain-coherent but is internally split into three deliverable slices:

- **M4-A:** Search + Dashboard Read Models
- **M4-B:** Activity + Notifications
- **M4-C:** Reminders + Rules

### M5 – Client Completion & Parity

M5 completes Web and Android: full domain integration, navigation, Deep Links, Read Cache, Export/Import, accessibility, performance, and systematic feature parity. The M2 reference flows become production-ready here; the deferred manual accessibility acceptance also occurs here.

### M6–M9

M6 Rich Features, M7 Integrations, M8 voluntary Context, and M9 Productization remain in their established order. M9 is the launch gate for managed/self-hosted operation, including pre-exposure hardening, backup/restore, update/rollback, retention/deletion, monitoring, entitlements, and support readiness.

## Privacy terminology

- `SHARED` / `PRIVATE`: public domain values when a resource includes a user visibility decision.
- `SPACE_SHARED` / `OWNER_ONLY`: internal authorization/privacy classes.
- Clients do not redundantly write `privacyClass` as a second source of truth.
- `PRIVATE` is enforced server-side as `OWNER_ONLY`; client filters are not a security boundary.

## M2-S0 — complete

1. **#67 Planning** — synchronized project control with G1=passed and the milestone boundaries defined here.
2. **#68 Domain/Privacy** — closed Memory, Comment, HeartMoment, and event/delete decisions.
3. **#69 Media** — closed attachment relation, limits, validation, retention, upload transport, and orphan rules.
4. **#70 API** — transferred routes, DTOs, error codes, concurrency, pagination, and Story sorting into the versioned contract.
5. **#78 Media metadata** — decided M2-D14 (strip on ingest) and M2-D15 (one derived variant, no transcoding). Both were classified `BEFORE_CLIENTS`, but they affect the ingest path and were therefore raised to `BLOCKING`.
6. **#85 Media ordering** — M2-D23: images first with Pillow and pillow-heif. Video was initially planned as its own slice and has since moved outside M2/G2 to future backlog #88.

The `BLOCKING` decisions relevant to M2 were closed before their respective runtime code. `BEFORE_CLIENTS` points for Notification Preview, Export/Backup, Client Cache, and search index are handled in their responsible later milestones.

During implementation, four additional `BLOCKING` decisions emerged only from the code or next slice. Each was closed before the code depending on it, as required by the runtime-start rule:

- **M2-D23** (#85) — ordering and parser for media processing.
- **M2-D24** (#79) — read access to still-unbound attachments.
- **M2-D25** (#94) — write permissions for Milestone.
- **M2-D22** (#104) — owner view for private HeartMoments. It was classified `BEFORE_CLIENTS` but shapes the Story route and was therefore raised to `BLOCKING` before S7.

## Runtime-start rule

A runtime slice starts only when **all BLOCKING decisions relevant to that exact slice** are `DECIDED` and its versioned OpenAPI contract is available in contract-testable form. Runtime code does not silently decide an open question: if a slice encounters an unresolved question, it is closed as a Decision Log entry rather than answered in code.

This rule also applies to M3 and later milestones. Completing a milestone gate does not replace slice-specific contract and reuse review.

## M2 delivery status

### Delivered

- #71 — Memory CRUD without media (PR #77). Validates M2 migration style, ProtectedPayload boundary, Tenant Guard, author rule, optimistic concurrency, and signed keyset cursor on a media-free surface.
- #80 — HeartMoment with owner-only privacy (PR #84). First type with a real user visibility choice; `SHARED -> PRIVATE` as a separate atomic operation, Emotion as ProtectedPayload.
- #79 — Attachment lifecycle for images (PR #89). State machine, LocalMediaStore, asynchronous validation with stripping per M2-D14 and thumbnail per M2-D15, authorized reads, retention, and cleanup. Video remains fail-closed and is tracked outside M2/G2 in #88.
- #90 — Bind attachments to Memory and HeartMoment (PR #93). `MemoryAttachment` with stable `position`, HeartMoment with at most one attachment, atomic bind/unbind within the M2-D20 binding window, no cross-space and no multiple binding under M2-D03.
- #94 — Milestone domain and API (PR #95). Distinct model rather than type flag on Memory; M2-D25 retains the author rule from M2-D01 here as well.
- #97 — Comments, Outbox, and Notification Hook (PR #98). Create/List nested under parent, Update/Delete space-scoped, enumerated targets, atomic Outbox entry, and idempotent retry. Fulfills the commitment from #80.
- #87 — S3-compatible MediaStore adapter (PR #100). Presigned Upload and Read URL using the TTLs from M2-D13, against the same contract tests as the local adapter.
- #113 — Story Read Model and `/timeline` (PR #114). Derived timeline over Memory, Milestone, and shared HeartMoments only; sort key `(effectiveDate, createdAt, kindRank, id)` and keyset cursor per M2-D08. Private HeartMoments are never Story items, even for their owner (M2-D22). No persisted Read Model.
- S8 — thin Web/Android reference flows: delivered.
- #144 — real Web/Android G2 E2E evidence against API, Worker, PostgreSQL, and LocalMediaStore: delivered.
- #147 / PR #170 — final G2 Gate Review: **G2: PASSED**.

### Future backlog outside M2/G2

- #88 — `Future: Video uploads and poster frames`

#88 is not implemented now. Prototype #109 was closed without merge because of a production image of roughly 755 MiB and the additional ffmpeg operational, supply-chain, and security burden. `main` remains fail-closed for MP4 and QuickTime. Resuming this work requires a new architecture and security decision that explicitly evaluates a separate optional processing model rather than an enlarged shared image.

### Commitment from #80 — fulfilled

The atomic comment deletion required by M2-D07 when changing `SHARED -> PRIVATE` depended on `_delete_dependent_comments` and could not be proven without Comments. With #97 the cascade is wired — additionally protected by mapper listeners in `comments/cascades.py` — and demonstrated in `test_shared_to_private_loescht_comments_und_resurrected_nichts`. The tracking item is therefore closed.

## G2 — complete

The binding decision source is the [final G2 Gate Review](../reviews/2026-08-26-g2-final-gate-review.md). It explicitly evaluates G2 as **PASSED**.

M2 is therefore formally complete. M3 is the approved next milestone. The first planned runtime slice is M3-S1 **Wish Foundation**; its contract and verification are controlled by the M3 package.

## Active status sources

The living status sources are synchronized to the same state:

- [`README.md`](../../README.md)
- [`docs/ROADMAP.md`](../ROADMAP.md)
- [`docs/IMPLEMENTATION-STATUS.md`](../IMPLEMENTATION-STATUS.md)
- [`docs/m2/PROJECT-CONTROL.md`](./PROJECT-CONTROL.md)

Current M3 control sources:

- [`docs/m3/README.md`](../m3/README.md)
- [`docs/m3/DELIVERY-PLAN.md`](../m3/DELIVERY-PLAN.md)

Historical reviews intentionally remain unchanged and may therefore contain earlier gate states.
