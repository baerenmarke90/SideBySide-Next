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

## Blocking decisions

### M6-B01 — Final #262 product/entitlement semantics

**Status:** `BLOCKING` for #523 and every launch provider adapter.

#262 must explicitly freeze before runtime:

- capability classification and versioned Free/Premium matrix;
- relationship/couple vs. purchaser/account entitlement ownership;
- lifecycle states actually supported (trial/grace/grandfathering/refund/revocation,
  only where accepted);
- downgrade read/create/edit/export behavior;
- migration policy for previously available features/data;
- Self-Hosted commercial licensing/offline behavior;
- restore/reconciliation rules;
- commercial channels required for the first launch.

M6-S0 deliberately does not choose these product semantics on behalf of #262.

### M6-B02 — Complete Account deletion/retention matrix

**Status:** `BLOCKING` for G5, owner #520, coordinated with #518.

The launch contract must decide hard-delete/anonymize/retain behavior for Account,
authentication, Membership history, shared/private content, media, jobs, Audit and
commercial references, including how a restore of an older backup re-applies a
previous deletion request.

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
