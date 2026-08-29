# M2 Technical Readiness Package

**Status:** implementation preparation, not a replacement for OpenAPI or the master specification  
**Version:** 1.0  
**As of:** August 24, 2026

This package prepares **M2 – Memory Core** technically without interfering with the ongoing Foundation issues #5–#11. It contains planning files only. Runtime code, auth/session, transport, CI, project scaffolds, OpenAPI, and profiles remain untouched.

## Goal

After the M0/M1 gates are complete, M2 should be implementable as reviewable vertical slices without repeating foundational design work:

```text
Memory + Media + HeartMoment + Milestone + Comment
                         │
                         └── Story Read Model
```

## Contents

- [Domain Model](./DOMAIN-MODEL.md) – entities, invariants, privacy, and events
- [API Design](./API-DESIGN.md) – operations, DTOs, errors, and concurrency as an OpenAPI template
- [Media Pipeline](./MEDIA-PIPELINE.md) – upload, validation, storage, and authorized retrieval
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md) – tenant, owner-only, media, and leak tests
- [Delivery Plan](./DELIVERY-PLAN.md) – vertical slices and issue-ready work packages
- [Decision Log](./DECISION-LOG.md) – M2 decisions to settle before coding begins
- [Architecture diagram](./m2-architecture.svg) – human-readable overview

## Authoritative sources

1. [Clean-Room Master Specification](../../specification/CLEAN-ROOM-MASTER-SPEC.md), especially sections 14–21.
2. [Product Specification](../../specification/PRODUCT-SPEC.md).
3. [Security invariants](../SECURITY.md).
4. [Architecture](../ARCHITECTURE.md).
5. The versioned OpenAPI contract current when M2 is implemented.

If sources conflict, the higher-ranked source takes precedence. This package must not silently decide an unresolved domain gap.

## M2 scope

| Domain | M2 content |
|---|---|
| Memory | CRUD, author, domain date, multiple media items, comments, Story |
| HeartMoment | text, emotion, `SHARED`/`PRIVATE`, optional attachment, Story only when shared |
| Milestone | distinct model, CRUD, Story, later Chapter/Recap |
| Attachment | MediaStore abstraction, upload lifecycle, validation, safe read URL/route |
| Comment | controlled targets, shared content only, notification event |
| Story | derived Read Model, filters, search, sorting, cursor pagination |

## Not in M2

- real end-to-end encryption,
- Offline Write Sync,
- Chapter/Place implementation,
- annual recap,
- public Share Links,
- AI image analysis or automated content analysis,
- shopping, discovery, location, and additional provider integrations,
- freely polymorphic comments on arbitrary tables.

## Entry conditions

M2 implementation starts only when:

- open Foundation/M1 security gates are closed,
- owner-only authorization exists server-side,
- the OpenAPI contract is versioned and contract-testable,
- ProtectedPayload boundaries can be technically enforced on sensitive models,
- Web/Android foundations exist for the planned client slices,
- `BLOCKING` decisions in the Decision Log are resolved.

## Definition of Ready

- [ ] every model has confirmed fields, privacy class, and write permissions,
- [ ] every operation has request, response, error codes, and a concurrency rule,
- [ ] Story filtering excludes private content server-side,
- [ ] media limits and allowlist are decided,
- [ ] attachment lifecycle and orphan cleanup are specified,
- [ ] domain events contain no unnecessary plaintext payloads,
- [ ] tenant/owner-only/media test matrix is accepted,
- [ ] delivery slices have explicit dependencies,
- [ ] no M2 statement promises existing E2EE.

## Working rule

A slice is complete only when domain model, migration, service, authorization, API/OpenAPI, error codes, unit/integration/cross-tenant tests, privacy tests, export impact, client behavior, and documentation are satisfied together. A single working endpoint or screen is not sufficient.
