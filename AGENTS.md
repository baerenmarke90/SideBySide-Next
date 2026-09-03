# SideBySide Next - Implementation Rules

These rules apply to AI-assisted and human implementation work in this repository.

## Mandatory sources

Before relevant work, read at least these documents:

1. `docs/ENGINEERING-LANGUAGE.md`
2. `specification/CLEAN-ROOM-MASTER-SPEC.md`
3. `docs/REUSE-BEFORE-BUILD.md`
4. `docs/CROSS-CUTTING-QUALITY.md`
5. `docs/BUSINESS-MODEL.md`
6. `docs/FREEMIUM-FEATURE-MATRIX.md`
7. `docs/EXTERNAL-PROVIDER-CANDIDATES.md` when providers, infrastructure, or platform components are affected
8. `docs/ROADMAP.md` and the relevant milestone/project-control documentation

For every user-facing Web or Android change, the following are additional mandatory sources before implementation starts:

9. `docs/DESIGN-PRINCIPLES.md`
10. `docs/PARTNER-APP-EXPERIENCE-STANDARD.md`
11. `docs/UX-PATTERNS.md`
12. `docs/SCREEN-TEMPLATES.md`
13. `docs/COMPONENT-CONTRACTS.md`
14. `docs/DESIGN-SYSTEM-DELIVERY.md`
15. `design/tokens.json`

## Engineering language

English is the mandatory engineering language for this repository. Follow `docs/ENGINEERING-LANGUAGE.md`.

Use English for source identifiers, comments/docstrings, tests, logs/internal diagnostics, scripts, CI/developer tooling, API/schema descriptions, active technical documentation, issues, pull requests, reviews, and commit messages.

User-facing product text remains localization-driven. German and other languages belong in the appropriate i18n resources or intentionally locale-specific fixtures; do not replace localized product content with hardcoded English.

## Reuse before build

Before implementing infrastructure, integration logic, or technical commodity functionality from scratch, perform a current reuse review.

Check in particular:

- open standards/protocols
- OS/platform capabilities
- framework/runtime capabilities
- established open-source components
- external providers/APIs

The concrete checklist and decision rules are defined in `docs/REUSE-BEFORE-BUILD.md`.

### Required before implementation starts

When the change is relevant, the issue or pull request must document:

- which alternatives were considered
- which solution was selected
- why it fits
- why custom implementation is necessary, if applicable
- for third-party components: license/ToS, Cloud/Self-Hosted support, privacy, cost, fallback, and user effort

`docs/EXTERNAL-PROVIDER-CANDIDATES.md` is a starting list; it does not replace a current search for better or newer options.

## Business / freemium model consistency

Consistency with `docs/BUSINESS-MODEL.md` and `docs/FREEMIUM-FEATURE-MATRIX.md` is a mandatory development invariant, not a launch-only or monetization-only review.

Every development issue and pull request must explicitly assess whether the change is consistent with the current SideBySide Next business/freemium model. The review is mandatory even when the conclusion is that the change has no business-model impact.

For capabilities already classified in `docs/FREEMIUM-FEATURE-MATRIX.md`, that versioned matrix is the authoritative product-tier baseline. Until remaining future/unimplemented Free/Premium decisions from #262 are promoted into authoritative repository documentation, #262 remains the working source for those pending decisions. It must not become a permanent substitute for versioned repository documentation.

### Required before implementation starts

Assess at least the following when relevant:

- Free, Premium, Mixed, or explicitly non-paywallable capability classification, including the current matrix row or the need to add/update one;
- entitlement/capability boundaries and relationship/couple ownership semantics;
- Self-Hosted versus SideBySide Cloud/Managed behavior;
- managed infrastructure, storage, compute, rendering, provider/API, inference, email/push, or support cost;
- quotas, storage limits, fair-use rules, retention, or other managed-resource constraints;
- downgrade, trial, grandfathering, restore, export, and existing-data behavior;
- whether the change would artificially degrade Self-Hosted solely to promote Cloud;
- whether the authoritative feature/plan matrix or business-model documentation must be updated.

The issue or pull request must record one of:

- **Business/freemium impact reviewed** — with the relevant matrix classification/decision or link to the owning product decision; or
- **No business/freemium impact** — with a short rationale.

A generic unchecked statement such as `not relevant` without rationale is insufficient.

### Required before merge

Re-evaluate the business/freemium result when implementation decisions changed the product surface, entitlement model, Self-Hosted/Cloud behavior, managed-resource usage, storage/quota behavior, operating cost, or downgrade/data semantics.

A pull request is not merge-ready when it introduces or changes a recognizable monetization, entitlement, Premium, Cloud/Self-Hosted, managed-resource, storage/quota, or downgrade behavior that conflicts with the current model or lacks an explicit owning decision.

If the product-tier contract changes, update `docs/FREEMIUM-FEATURE-MATRIX.md` before or with the implementation. Do not silently reinterpret an existing row from Free to Premium, Premium to Free, or change a Mixed boundary without versioned rationale and migration semantics where existing data/users are affected.

Business-model consistency does not replace security, privacy, architecture, accessibility, reuse, or cross-cutting-quality review. All applicable gates remain cumulative.

## Product design and partner-app experience

User-facing client work is product-design work, not a functional implementation followed by optional styling.

SideBySide is a private partner app. Couple-facing screens must follow `docs/PARTNER-APP-EXPERIENCE-STANDARD.md` and must not default to generic CRUD, admin-console, spreadsheet, or dashboard presentation.

### Required before implementation starts

For every new or materially changed user-facing Web or Android feature, identify in the issue or PR:

- the owning Screen Template or the reason a new pattern is required;
- the existing design-system components and tokens to reuse;
- the primary human/content focal point;
- the primary action and visual hierarchy;
- Compact and Expanded behavior;
- Loading, Empty, Error, Offline, and Success states where applicable;
- motion and feedback behavior, including reduced-motion behavior;
- privacy and relationship-state presentation where applicable.

A new feature must use the shared product language in its first mergeable implementation. `Functionality first, design later` is not an acceptable UI delivery strategy.

### Couple-facing anti-patterns

Unless an explicit product decision justifies them, do not use these as the primary presentation of relationship content:

- dense tables;
- repeated metadata-heavy bordered rows;
- equal dashboard tiles with no real hierarchy;
- nested card landscapes;
- raw form stacks without product composition;
- technical IDs, enum values, or API terminology in normal-user surfaces;
- layouts whose dominant visual structure is indistinguishable from inventory, invoicing, or server administration software.

Administration and diagnostics may legitimately use denser information design, but that visual language must not leak into normal couple-facing surfaces.

### Motion is required behavior

Every material interaction must deliberately decide whether motion or feedback is needed. Reuse motion tokens and platform capabilities. State changes, reordering, sheets/panes, success feedback, and emotionally meaningful actions should not feel like abrupt DOM/data replacement.

All motion must remain non-blocking, accessible, and understandable with reduced motion enabled.

### Visual evidence before merge

A PR that changes couple-facing UI must include visual evidence sufficient to review the product result, including representative Compact and Expanded states where applicable. Theme-sensitive changes must be checked in Light and Dark. A textual assertion that the UI looks correct is not sufficient evidence by itself.

A user-facing PR is not merge-ready when it is functionally correct but visibly violates the partner-app experience standard.

## Semantic design tokens

Reusable visual values must use semantic design tokens instead of repeated component-level literals.

Rules:

- define reusable colors, spacing, radii, typography, shadows, motion, and similar visual constants through semantic tokens;
- name tokens by interface meaning, not by their current literal value;
- consume tokens through the platform design-system adapter instead of local visual constants;
- keep literal values at the token-definition boundary unless a value is genuinely one-off and does not provide reusable meaning;
- tokenize theme-, branding-, accessibility-, and motion-sensitive values so they can be adjusted centrally.

Prefer:

```css
--color-text-inverse-muted: rgb(255 255 255 / 90%);
color: var(--color-text-inverse-muted);
```

Avoid:

```css
color: rgb(255 255 255 / 90%);
```

or implementation-only names such as `--purple-600` when the semantic role is known.

This rule does not require meaningless token proliferation for isolated values without reuse or semantic value. See `docs/DESIGN-PRINCIPLES.md` and `docs/DESIGN-TOKEN-POLICY.md` for the design-system guidance.

## Cross-cutting quality

Cross-cutting requirements are architecture and product requirements, not late release cleanup.

Before implementation begins and again before merge, apply `docs/CROSS-CUTTING-QUALITY.md` to larger runtime slices, client features, and production user flows. Deliberately assess at least these areas when relevant:

- security, authentication, authorization, and abuse resistance;
- privacy and data lifecycle;
- internationalization and locale behavior;
- accessibility;
- concurrency and consistency;
- resilience, offline behavior, and retry semantics;
- observability;
- performance and resource usage;
- API, contract, and migration consequences;
- operations, Self-Hosted behavior, and release impact;
- testing and negative cases.

Not every area applies to every change. `Not relevant` is acceptable when the decision is traceable. A pull request is not merge-ready when a recognizable cross-cutting consequence is left untreated or deferred in a way that creates an incompatible contract, privacy/security gap, or hard-to-reverse architecture.

For client work in particular, user-facing text, date/number formatting, and pluralization must use the localization layer from the start, and accessibility must be implemented as part of the feature rather than postponed to final UI review.

## User rule

Normal couples must not need to configure technical infrastructure. API keys, technical URLs, provider selection, tokens, and server details belong in the backend or hoster/admin layer.

## Do not weaken existing gates

Reuse, business-model, product-design, or cross-cutting decisions must never weaken Clean-Room, security, privacy, tenant-isolation, provenance, licensing, or engineering-language rules.

## Pull requests

A relevant pull request without a traceable reuse review is not merge-ready. Pure domain changes may mark the review as `not relevant` with a short rationale.

Every development pull request must contain a traceable Business/Freemium Model Consistency result. `No business/freemium impact` is acceptable only with a short rationale. A recognizable conflict with `docs/BUSINESS-MODEL.md`, `docs/FREEMIUM-FEATURE-MATRIX.md`, or the current working decisions for unclassified future features must be resolved before merge or routed through an explicit owning product decision.

Every pull request must also record whether it has user-facing UI/UX impact. A PR with user-facing Web or Android changes must complete the Product Design / UX review from the pull-request template and satisfy the partner-app experience standard.

Larger runtime slices, client features, and production user flows must document their relevant cross-cutting consequences in the pull request. The pull-request template is the minimum review surface; deeper decisions belong in the owning issue, decision document, or ADR.

A pull request that introduces non-English engineering content without an allowed exception from `docs/ENGINEERING-LANGUAGE.md` is not merge-ready.
