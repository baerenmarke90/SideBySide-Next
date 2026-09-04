# M6 Decision Log

**Owner:** #437  
**Baseline:** `main` at `7564800df85f53f9f0c9a99a7414de22906ade73`

This log records the decisions that M6 runtime work may rely on. `BLOCKING` means
runtime must not guess the answer. `BEFORE_RELEASE` means implementation may proceed
within the stated boundary, but G5 cannot pass until the item is resolved and
evidenced. `LATER` is explicitly outside G5 unless a future gate decision changes
that classification.

## Frozen decisions

| ID | Decision | Status | Source / owner |
|---|---|---|---|
| M6-D01 | M6 is Operate & Launch after M5/G4; M7-M9 product expansion is not a G5 prerequisite. | FROZEN | ADR 0006 / #433 / #437 |
| M6-D02 | Operational backup/recovery reuses #190. The M5 Transfer Bundle remains a separate user-portability contract. | FROZEN | #190, #345 |
| M6-D03 | Persistent Development -> Production promotion, immutable deployed revision, migration-before-Production and rollback/forward-fix semantics reuse #375. | FROZEN | #375 |
| M6-D04 | Public Demo is isolated from Development/Production and is not the release gate. | FROZEN | #304, #375 |
| M6-D05 | Android release application ID is `de.sidebyside.app`; debug is separate; `versionCode` is publisher-supplied and signing material is never committed. | FROZEN | #194 |
| M6-D06 | Self-Hosted vs. Cloud/Managed is an operating-model axis separate from Free/Core vs. Premium. | FROZEN | `BUSINESS-MODEL.md`, `FREEMIUM-FEATURE-MATRIX.md` |
| M6-D07 | Security, Privacy, Accessibility, Account/data deletion and essential portability are non-paywallable. | FROZEN | #262 baseline, freemium matrix |
| M6-D08 | Entitlement enforcement is capability-oriented, centralized and backend-authoritative; payment/store/provider concepts do not belong in Domain feature code. | FROZEN BOUNDARY | #262, #437, #523 |
| M6-D09 | Self-Hosted remains operable without a mandatory external telemetry SaaS. | FROZEN | #189, #437 |
| M6-D10 | ServerAdmin is an application-operations surface, not a host/container shell and not a private-content browser. | FROZEN | #335, #437 |
| M6-D11 | Account deletion is distinct from Space/relationship offboarding and both are launch data-lifecycle concerns. | FROZEN BOUNDARY | #518, #520 |
| M6-D12 | No new orchestration/queue/backup/export platform is introduced without Reuse-before-build evidence and demonstrated need. | FROZEN | repository governance |
| M6-D13 | Commercial entitlements are Space/couple-scoped, downgrade is strictly non-destructive, Self-Hosted is offline-resilient, and domain gating uses normalized capabilities. | FROZEN | #262, `FREEMIUM-FEATURE-MATRIX.md` v1.1, ADR 0006 |
| M6-D14 | V1 Space offboarding is self-exit only for normal clients: `ACTIVE -> LEFT`, no partner removal, no implicit reconnect, and a new relationship always receives a new Space. | FROZEN | #518, `SPACE-OFFBOARDING-LIFECYCLE.md` v1.0 |

## Blocking decisions

### M6-B01 — Final #262 product/entitlement semantics

**Status:** `FROZEN / RESOLVED` via #262, `FREEMIUM-FEATURE-MATRIX.md` (v1.1) and ADR 0006. Unblocks #523.

- Capability matrix across M0–M8 finalized.
- Space/couple-scoped entitlement ownership with purchaser sponsorship.
- Lifecycle states: `ACTIVE`, `TRIAL`, `GRACE_PERIOD` (14 days), `EXPIRED`, `REVOKED`, `GRANDFATHERED`.
- Guaranteed zero data loss on downgrade; existing history remains 100% readable and exportable.
- Self-Hosted is 100% offline-resilient; optional commercial license uses Ed25519 offline tokens.
- Restores are idempotent and normalized across all channels.

### M6-B02 — Complete Account deletion/retention matrix

**Status:** `FROZEN / RESOLVED` by `ACCOUNT-DELETION-RETENTION.md` v1.0 under #520. Runtime, public self-service API/mail and Web/Android cleanup are completed through #651-#654; final integrated G5 evidence remains owned by #524.

The frozen contract requires:

- one server-authoritative Account-deletion lifecycle, distinct from Space/relationship offboarding;
- removal of authentication/profile/private data while a minimal disabled/pseudonymized Account identity may remain for legitimate historical references;
- hard deletion of the deleted Account's `OWNER_ONLY` data without transfer or reclassification;
- retention of legitimate `SPACE_SHARED` history without blind `accounts` cascade deletion or ownership transfer;
- reuse of the existing session, Membership, Job/Outbox, MediaStore cleanup and #345 portability primitives;
- stale side effects to fail closed against current deletion state and authorization;
- a minimal forward-only deletion reconciliation journal outside the point-in-time application database so #190 restores predating deletion cannot reactivate the Account before API/worker startup;
- #518 to remain authoritative for orphaned-Space retention/destruction and deliberate reconnect semantics.

### M6-B03 — Cloud/Managed launch topology

**Status:** `BLOCKING` for managed launch support, owner #521.

The initial managed deployment must freeze API/Web/worker/migrate/database/media,
secret ownership, ingress, backup responsibility, capacity assumptions and one
versioned supported deployment representation. It must reuse #375/#190 rather than
creating Cloud-only Domain semantics.

### M6-B04 — Launch entitlement-source adapters

**Status:** `BLOCKING` after #262/#523 for every commercial source actually used at
launch.

One focused issue/PR is required per selected source. Examples may include Google
Play, a hosted subscription provider or a Self-Hosted commercial license, but M6-S0
does not assume that all examples are required. Each adapter maps provider evidence
into #523; no provider SDK/state may leak into feature code.

### M6-B05 — Space/relationship offboarding lifecycle

**Status:** `FROZEN / RESOLVED` by `SPACE-OFFBOARDING-LIFECYCLE.md` v1.0 under #518. Runtime/client implementation and final G5 evidence remain open.

The frozen V1 contract requires:

- normal clients may end only their own active Membership (`ACTIVE -> LEFT`); no unilateral partner-removal control is exposed;
- ordinary self-exit preserves shared history while another active member remains and never transfers ownership;
- the leaving Account's Space-scoped `OWNER_ONLY` data is deleted rather than stranded as inaccessible ghost data; #345 `PERSONAL` export is the optional pre-exit portability path;
- pending/running Transfer work does not gain post-exit authorization and no special breakup archive/grace credential is added;
- a Space with any ended Membership is relationship-history locked: stale invitations cannot add a new partner and ordinary `add_member()` cannot reactivate an ended Membership;
- V1 has no reconnect; a new or renewed relationship creates a new Space;
- zero-active Spaces are inaccessible immediately and enter a bounded 30-day retention window before existing cleanup primitives purge the orphaned shared Space;
- account sessions remain valid after leaving one Space while Web/Android clear only the exited Space state/cache/drafts and move to another active Space or the existing awaiting-Space state;
- membership-sensitive jobs/provider effects must revalidate current authorization at the side-effect boundary;
- exit, privacy cleanup and essential portability remain non-paywallable.

## Before-release decisions

### M6-R01 — Release artifact publication model

**Status:** `BEFORE_RELEASE`, owner #519.

#375 already permits immutable-source builds for v1 and does not require a registry.
#519 must decide whether G5 continues that model or publishes build-once versioned
OCI artifacts. Either choice must provide one immutable release identity, a
release manifest/digests and deterministic previous-known-good selection.

### M6-R02 — Android store signing operations

**Status:** `BEFORE_RELEASE`, owner #519; code boundary already delivered by #194.

Before first store release decide and document:

- Play App Signing use;
- upload-key custody;
- protected publishing environment;
- escrow/recovery/rotation responsibility where supported;
- least-privilege access.

No private key or password is stored in repository documentation.

### M6-R03 — SBOM/attestation attachment

**Status:** `BEFORE_RELEASE`, owner #193.

SBOM/provenance must identify the exact #519 release artifacts. `DEPENDENCIES.md`
remains the human dependency policy; it is not a substitute for machine-readable
release SBOMs.

### M6-R04 — Recovery objectives and measured drill evidence

**Status:** `BEFORE_RELEASE`, owners #190/#521/#522/#524.

M6 will record measured recovery timings and launch-topology limits. It will not
turn one drill into an unsupported contractual RPO/RTO/SLA claim.

### M6-R05 — Administration lockout safety

**Status:** `BEFORE_RELEASE`, owners #334/#335/#524.

Maintenance/registration controls must preserve authorized ServerAdmin recovery
access and bootstrap safety. ServerAdmin cannot bypass privacy or become host
orchestration.

### M6-R06 — Observability redaction and incident runbooks

**Status:** `BEFORE_RELEASE`, owners #189/#522/#524.

Diagnostics must be technically actionable without ProtectedPayload, `OWNER_ONLY`,
tokens, signed URLs, raw provider secrets or arbitrary private content.

### M6-R07 — Final launch capacity assumption

**Status:** `BEFORE_RELEASE`, owners #521/#524.

The initial topology and tested synthetic load must be recorded. G5 requires bounded
evidence, not a speculative scale architecture.

## Later / explicitly not G5

| ID | Item | Status |
|---|---|---|
| M6-L01 | Kubernetes/multi-region architecture without a proven launch need | LATER |
| M6-L02 | Mandatory external APM/telemetry SaaS | LATER / not Core requirement |
| M6-L03 | Byte-identical registry promotion if #519 proves immutable-source publication sufficient for G5 | LATER unless #519 selects it now |
| M6-L04 | M7 Relationship Depth features | LATER |
| M6-L05 | M8 Discovery/Integration expansion | LATER |
| M6-L06 | M9 location/context expansion | LATER |
| M6-L07 | E2EE | LATER |
| M6-L08 | Custom payment processing | REJECTED; use platform/provider mechanisms |
| M6-L09 | Host/container shell in ServerAdmin | REJECTED |

## Change rule

A runtime PR may not silently change a `FROZEN` or `BLOCKING` decision. If new
evidence requires a change, update the authoritative product/ADR/issue owner first,
record the supersession here, and then implement the new accepted contract.
