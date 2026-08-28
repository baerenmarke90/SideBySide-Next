# M2 UX-to-Engineering Handoff

**Status:** implementation preparation  
**Version:** 1.0  
**As of:** August 24, 2026

This package concretizes the existing SideBySide design foundation for **M2 – Memory Core**. It replaces neither product, API, nor Security specification; instead, it connects them into implementable screens, states, and platform rules.

## Target experience

M2 should feel like the same product on Web and Android:

- shared terminology and identical Domain outcomes,
- platform-appropriate navigation and overlays,
- visible Privacy before, during, and after saving,
- honest Media, Sync, Offline, and error states,
- no private information in Story, Search, Comments, Push, or partner Export,
- a complete core flow without relying on mouse, touch precision, or visual cues alone.

## Files

- [Screen Flows](./SCREEN-FLOWS.md) – navigation, task paths, and transitions
- [Screen State Matrix](./SCREEN-STATE-MATRIX.md) – mandatory states, copy, and actions
- [Platform Handoff](./PLATFORM-HANDOFF.md) – Web/Android adaptation, Accessibility, and performance
- [Graphical Screen Flow](./m2-screenflow.svg) – compact overview for Product, Design, and Engineering
- [Privacy Threat Model](../../docs/m2/PRIVACY-THREAT-MODEL.md) – data flows, threats, and controls
- [Demo Scenario](../../docs/m2/DEMO-SCENARIO.md) – reproducible end-to-end dataset
- [Implementation Issues](../../docs/m2/IMPLEMENTATION-ISSUES.md) – issue-ready Client and QA packages

## Binding foundations

| Topic | Source |
|---|---|
| Navigation and terminology | [Information Architecture](../../docs/INFORMATION-ARCHITECTURE.md) |
| General interactions | [UX Patterns](../../docs/UX-PATTERNS.md) |
| Existing task flows | [User Flows](../../docs/USER-FLOWS.md) |
| Layout types | [Screen Templates](../../docs/SCREEN-TEMPLATES.md) |
| Components | [Component Contracts](../../docs/COMPONENT-CONTRACTS.md) |
| Privacy communication | [Content & Privacy Guidelines](../../docs/CONTENT-PRIVACY-GUIDELINES.md) |
| Accessibility acceptance | [Accessibility QA Matrix](../../docs/ACCESSIBILITY-QA-MATRIX.md) |
| Design Tokens | [tokens.json](../tokens.json) |
| M2 Domain/API/Media | [M2 Technical Readiness](../../docs/m2/README.md) |

If sources conflict, the binding product specification or the OpenAPI contract published when implementation begins takes precedence. Open domain questions are decided in the [M2 Decision Log](../../docs/m2/DECISION-LOG.md), not hidden in the client.

## Definition of Ready for an M2 screen

A screen is ready for implementation when:

1. entry point, success state, and return path are defined.
2. permitted roles and Privacy class are named.
3. data source and relevant API operation are defined.
4. Loading, Empty, Offline, 401, 404, 409, 429, and 5xx are assessed.
5. focus/TalkBack order and large-font behavior are described.
6. Analytics contains no content, Search text, filenames, or private attributes.
7. Web and Android use the same Domain contract.

## Deliberate boundaries

- No real E2EE in the MVP; only E2EE-ready data and Media boundaries.
- Offline Read is allowed; Offline Write deliberately remains disabled.
- Private HeartMoments are a dedicated owner-only path, not a filter in shared Story.
- Chapter, Place, Recap, public links, and temporary sharing are not part of this package.
- This package does not silently decide still-open Domain questions.
