# SideBySide Next - Implementation Rules

These rules apply to AI-assisted and human implementation work in this repository.

## Mandatory sources

Before relevant work, read at least these documents:

1. `docs/ENGINEERING-LANGUAGE.md`
2. `specification/CLEAN-ROOM-MASTER-SPEC.md`
3. `docs/REUSE-BEFORE-BUILD.md`
4. `docs/CROSS-CUTTING-QUALITY.md`
5. `docs/EXTERNAL-PROVIDER-CANDIDATES.md` when providers, infrastructure, or platform components are affected
6. `docs/ROADMAP.md` and the relevant milestone/project-control documentation

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

## Semantic design tokens

Reusable visual values must use semantic design tokens instead of repeated component-level literals.

Rules:

- define reusable colors, spacing, radii, typography, shadows, and similar visual constants through semantic tokens;
- name tokens by interface meaning, not by their current literal value;
- consume tokens through `var(...)` in components;
- keep literal values at the token-definition boundary unless a value is genuinely one-off and does not provide reusable meaning;
- tokenize theme-, branding-, and accessibility-sensitive values so they can be adjusted centrally.

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

This rule does not require meaningless token proliferation for isolated values without reuse or semantic value. See `docs/DESIGN-PRINCIPLES.md` for the design-system guidance.

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

Reuse or cross-cutting decisions must never weaken Clean-Room, security, privacy, tenant-isolation, provenance, licensing, or engineering-language rules.

## Pull requests

A relevant pull request without a traceable reuse review is not merge-ready. Pure domain changes may mark the review as `not relevant` with a short rationale.

Larger runtime slices, client features, and production user flows must document their relevant cross-cutting consequences in the pull request. The pull-request template is the minimum review surface; deeper decisions belong in the owning issue, decision document, or ADR.

A pull request that introduces non-English engineering content without an allowed exception from `docs/ENGINEERING-LANGUAGE.md` is not merge-ready.
