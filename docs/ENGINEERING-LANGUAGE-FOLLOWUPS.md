# Engineering Language Follow-up Work

Issue #212 establishes the policy and migrates the central contributor/developer surfaces. The remaining legacy repository content is intentionally split into reviewable work packages.

## Work package A - Backend and authoritative API sources

Scope:

- backend Python comments, docstrings, internal exception/log/diagnostic text;
- Alembic/migration engineering prose;
- authoritative API/OpenAPI titles, descriptions, summaries, and internal error details;
- backend build/runtime developer messages;
- regenerate Web/Android API output only after the authoritative source is English.

Constraints:

- preserve API behavior and stable machine-readable error codes;
- do not manually translate generated API clients;
- do not change user-facing localization behavior.

## Work package B - Web, Android, CI, and deployment engineering surfaces

Scope:

- non-generated Web and Android source comments, tests, diagnostics, and technical docs;
- remaining shell/Docker/deployment/CI messages and comments not covered by the policy baseline;
- developer-facing configuration guidance.

Constraints:

- locale resources and locale-specific fixtures remain in their target language;
- generated API output follows work package A and is not edited manually;
- no dependency or functional refactor solely for translation.

## Work package C - Active technical documentation and specifications

Scope:

- active architecture, security, privacy, operations, design, milestone, decision, roadmap/status, and specification documents;
- preserve normative meaning, links, decision IDs, and living-status semantics.

Constraints:

- dated historical review/audit snapshots remain immutable under the policy exception;
- translation must not silently alter product scope, privacy rules, release gates, or architectural decisions;
- documents that are active inputs to implementation should be migrated before adding substantial new sections to them.

The concrete GitHub issues for these packages are linked from #212. This file exists so the migration boundary remains visible in the repository after the tracker is closed.
