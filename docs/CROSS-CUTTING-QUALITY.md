# Cross-Cutting Quality Review

## Purpose

SideBySide Next treats cross-cutting requirements as architecture and product requirements, not late release cleanup.

Larger runtime slices, client features, and production user flows must be reviewed against the areas below before implementation and before merge. Not every area applies to every change; `not relevant` is acceptable when the decision is intentional and traceable.

The review complements existing Clean-Room, Security, Privacy, Reuse, and milestone gates.

## Review areas

### Security

Consider authentication, authorization, abuse resistance, tenant isolation, input validation, safe defaults, and fail-closed behavior.

### Privacy and data lifecycle

Consider visibility, retention, deletion, exports, backups, logs, events, caches, notifications, and third-party data flows.

### Internationalization and locale

Consider localization keys, date/time/number formatting, pluralization, long text layouts, RTL implications where relevant, and avoiding localized backend text as client contracts.

### Accessibility

Consider semantics, focus, keyboard/system navigation, screen readers, text scaling, contrast, motion, and loading/error/empty states.

### Concurrency and consistency

Consider parallel writes, idempotency, conflicts, races, delete transitions, and database consistency.

### Resilience

Consider network failures, retries, offline behavior, partial failures, and recovery semantics.

### Observability

Consider diagnostics, correlation IDs, metrics, and redaction. Never expose secrets, tokens, private payloads, or sensitive data.

### Performance and resources

Consider queries, pagination, payload size, media, memory, CPU, client rendering, and resource limits.

### Contracts and migrations

Consider OpenAPI/DTO changes, generated clients, database migrations, compatibility, and versioning.

### Operations and release

Consider configuration, containers, health checks, Self-Hosted behavior, upgrades, backups, and release impact.

### Testing

Consider appropriate unit, integration, contract, E2E, accessibility, and negative-case coverage.

## Pull request usage

Relevant pull requests include a Cross-Cutting Quality section. Non-relevant areas may be summarized together if the reasoning is clear.

A PR is not merge-ready when a recognizable cross-cutting consequence is untreated or deferred in a way that creates an incompatible contract, privacy/security gap, or difficult-to-reverse architecture.

## Example

A new date card may document:

- i18n: content through translation keys and dates through active locale;
- accessibility: semantic heading and keyboard behavior reviewed;
- privacy: no new data visibility;
- performance/API: not affected;
- tests: locale and rendering regression covered.
