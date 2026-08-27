# SideBySide Next - Implementation Rules

These rules apply to AI-assisted and human implementation work in this repository.

## Mandatory sources

Before relevant work, read at least these documents:

1. `docs/ENGINEERING-LANGUAGE.md`
2. `specification/CLEAN-ROOM-MASTER-SPEC.md`
3. `docs/REUSE-BEFORE-BUILD.md`
4. `docs/EXTERNAL-PROVIDER-CANDIDATES.md` when providers, infrastructure, or platform components are affected
5. `docs/ROADMAP.md` and the relevant milestone/project-control documentation

## Engineering language

English is the mandatory engineering language for this repository. Follow `docs/ENGINEERING-LANGUAGE.md`.

Use English for source identifiers, comments/docstrings, tests, logs/internal diagnostics, scripts, CI/developer tooling, API/schema descriptions, active technical documentation, issues, pull requests, reviews, and commit messages.

User-facing product text remains localization-driven. German and other languages belong in the appropriate i18n resources or intentionally locale-specific fixtures; do not replace localized product content with hardcoded English.

## Reuse before build

Before implementing technical commodity functionality from scratch, perform a current reuse review.

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

## User rule

Normal couples must not need to configure technical infrastructure. API keys, technical URLs, provider selection, tokens, and server details belong in the backend or hoster/admin layer.

## Do not weaken existing gates

Reuse must never weaken Clean-Room, security, privacy, tenant-isolation, provenance, or licensing rules.

## Pull requests

A relevant pull request without a traceable reuse review is not merge-ready. Pure domain changes may mark the review as `not relevant` with a short rationale.

A pull request that introduces non-English engineering content without an allowed exception from `docs/ENGINEERING-LANGUAGE.md` is not merge-ready.
