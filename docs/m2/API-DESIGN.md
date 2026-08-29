# M2 API Design

**Status:** binding pre-runtime contract after M2-S0 #70  
**Version:** 2.0

This document freezes routes, DTO names, concurrency, and pagination semantics for M2. The machine-readable planning source is `API-CONTRACT.json`. `backend/openapi.json` remains exclusively the contract generated from actually implemented FastAPI code and is updated only with the corresponding runtime slice. This avoids pretending that runtime endpoints already exist.

## 1. Global rules

- Base: `/api/v1/spaces/{spaceId}/...`.
- External JSON fields: `camelCase`.
- Persistent IDs: UUIDv7 strings.
- Authentication and active membership are checked before every space resource.
- Foreign or privacy-protected resources return neutral `404`.
- `visibility` is the public domain value; `privacyClass` is internal and is neither writable nor normally exposed as a client field.
- All mutable resources have `version` and return `ETag`.
- `PATCH`/`DELETE` and explicit relation/privacy mutations require `If-Match`.
- Stale `If-Match` returns `409 RESOURCE_VERSION_CONFLICT`.
- Problem Details and stable `code` values follow the existing API style.
- Domain dates use `YYYY-MM-DD`; technical timestamps are UTC instants.
- Collection and Story pages use opaque keyset cursors.

## 2. Binding route catalog

### Memory

| Method | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/memories` | `createMemory` | `MemoryCreate` | `201 MemoryDetail` |
| GET | `/spaces/{spaceId}/memories` | `listMemories` | `cursor?`, `limit?`, `year?` | `MemoryPage` |
| GET | `/spaces/{spaceId}/memories/{memoryId}` | `getMemory` | – | `MemoryDetail` |
| PATCH | `/spaces/{spaceId}/memories/{memoryId}` | `updateMemory` | `If-Match`, `MemoryUpdate` | `MemoryDetail` |
| DELETE | `/spaces/{spaceId}/memories/{memoryId}` | `deleteMemory` | `If-Match` | `204` |
| PUT | `/spaces/{spaceId}/memories/{memoryId}/attachments` | `replaceMemoryAttachments` | `If-Match`, `MemoryAttachmentSet` | `MemoryDetail` |

`MemoryCreate` contains **no** attachments in S2; the relation endpoint is implemented only with the media-integration slice. The contract is nevertheless fixed now.

### HeartMoment

| Method | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/heart-moments` | `createHeartMoment` | `HeartMomentCreate` | `201 HeartMomentDetail` |
| GET | `/spaces/{spaceId}/heart-moments` | `listHeartMoments` | `cursor?`, `limit?`, `visibility?` | `HeartMomentPage` |
| GET | `/spaces/{spaceId}/heart-moments/{heartMomentId}` | `getHeartMoment` | – | `HeartMomentDetail` |
| PATCH | `/spaces/{spaceId}/heart-moments/{heartMomentId}` | `updateHeartMoment` | `If-Match`, `HeartMomentUpdate` | `HeartMomentDetail` |
| PATCH | `/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility` | `changeHeartMomentVisibility` | `If-Match`, `HeartMomentVisibilityChange` | `HeartMomentDetail` |
| DELETE | `/spaces/{spaceId}/heart-moments/{heartMomentId}` | `deleteHeartMoment` | `If-Match` | `204` |

`SHARED -> PRIVATE` is the atomic privacy operation defined in #68. Private HeartMoments are visible only to the owner and are never Story items.

### Milestone

| Method | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/milestones` | `createMilestone` | `MilestoneCreate` | `201 MilestoneDetail` |
| GET | `/spaces/{spaceId}/milestones` | `listMilestones` | `cursor?`, `limit?`, `year?` | `MilestonePage` |
| GET | `/spaces/{spaceId}/milestones/{milestoneId}` | `getMilestone` | – | `MilestoneDetail` |
| PATCH | `/spaces/{spaceId}/milestones/{milestoneId}` | `updateMilestone` | `If-Match`, `MilestoneUpdate` | `MilestoneDetail` |
| DELETE | `/spaces/{spaceId}/milestones/{milestoneId}` | `deleteMilestone` | `If-Match` | `204` |

### Attachment

| Method | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/attachments` | `createAttachmentUpload` | `AttachmentUploadCreate` | `201 UploadDescriptor` |
| PUT | `/spaces/{spaceId}/attachments/{attachmentId}/content` | `uploadAttachmentContent` | LocalMediaStore Stream | `204` |
| POST | `/spaces/{spaceId}/attachments/{attachmentId}/finalize` | `finalizeAttachmentUpload` | `AttachmentFinalize` | `202 AttachmentDetail` |
| GET | `/spaces/{spaceId}/attachments/{attachmentId}` | `getAttachment` | – | `AttachmentDetail` |
| POST | `/spaces/{spaceId}/attachments/{attachmentId}/read-access` | `createAttachmentReadAccess` | `AttachmentReadRequest` | `ReadDescriptor` |
| DELETE | `/spaces/{spaceId}/attachments/{attachmentId}` | `deleteAttachment` | `If-Match` | `204` |

`uploadAttachmentContent` is allowed only for a `STREAM` descriptor. With S3, `createAttachmentUpload` returns a `SIGNED_UPLOAD` descriptor. `finalize` means acceptance for asynchronous validation, not `READY`.

### Comment

Create/List are intentionally nested under the parent; Update/Delete are space-scoped by Comment ID.

| Method | Route | operationId |
|---|---|---|
| POST | `/spaces/{spaceId}/memories/{memoryId}/comments` | `createMemoryComment` |
| GET | `/spaces/{spaceId}/memories/{memoryId}/comments` | `listMemoryComments` |
| POST | `/spaces/{spaceId}/heart-moments/{heartMomentId}/comments` | `createHeartMomentComment` |
| GET | `/spaces/{spaceId}/heart-moments/{heartMomentId}/comments` | `listHeartMomentComments` |
| POST | `/spaces/{spaceId}/milestones/{milestoneId}/comments` | `createMilestoneComment` |
| GET | `/spaces/{spaceId}/milestones/{milestoneId}/comments` | `listMilestoneComments` |
| PATCH | `/spaces/{spaceId}/comments/{commentId}` | `updateComment` |
| DELETE | `/spaces/{spaceId}/comments/{commentId}` | `deleteComment` |

Create uses `CommentCreate { body }`; lists use `cursor?`, `limit?`; Update uses `If-Match` + `CommentUpdate`; Delete uses `If-Match`. A client sends neither `targetType` nor `targetId` in the body; the parent is determined exclusively by the route.

### Story

| Method | Route | operationId |
|---|---|---|
| GET | `/spaces/{spaceId}/timeline` | `getStoryTimeline` |

G2 filters:

- `type`: repeatable query parameter from `MEMORY | HEART_MOMENT | MILESTONE`.
- `year`: `1900..2100`.
- `order`: `DESC` by default, alternatively `ASC`.
- `cursor`: opaque.
- `limit`: default `50`, maximum `100`.

`q` is **not** part of the M2/G2 contract and remains M4 Search.

## 3. DTOs

### Shared

```ts
interface AuthorSummary {
  id: UUID;
  displayName: string;
  profileAttachmentId?: UUID;
}

interface ResourceCapabilities {
  canEdit: boolean;
  canDelete: boolean;
  canComment: boolean;
}
```

Capabilities are a UX aid, not an authorization source.

### Memory

```ts
interface MemoryCreate {
  title: string;
  body: string;
  happenedOn?: LocalDate;
}

interface MemoryUpdate {
  title?: string;
  body?: string;
  happenedOn?: LocalDate | null;
}

interface MemoryDetail {
  id: UUID;
  spaceId: UUID;
  authorId: UUID;
  title: string;
  body: string;
  happenedOn?: LocalDate;
  version: number;
  createdAt: Instant;
  updatedAt: Instant;
  author: AuthorSummary;
  attachments: AttachmentSummary[];
  capabilities: ResourceCapabilities;
}

interface MemoryAttachmentSet {
  attachments: Array<{ attachmentId: UUID; position: number }>;
}
```

`authorId`, `spaceId`, `version`, and capabilities are not writable. Partners can read shared Memories; Update/Delete remain author-only.

### HeartMoment

```ts
type HeartEmotion = "LOVED" | "SEEN" | "APPRECIATED" | "SUPPORTED" | "GRATEFUL" | "HAPPY";
type HeartVisibility = "SHARED" | "PRIVATE";

interface HeartMomentCreate {
  text: string;
  emotion: HeartEmotion;
  visibility: HeartVisibility;
  happenedOn: LocalDate;
  attachmentId?: UUID;
}

interface HeartMomentUpdate {
  text?: string;
  emotion?: HeartEmotion;
  happenedOn?: LocalDate;
  attachmentId?: UUID | null;
}

interface HeartMomentVisibilityChange { visibility: HeartVisibility; }
```

`privacyClass` is neither writable nor published as a regular DTO field. `visibility` is the only domain-level client source of truth.

### Milestone

```ts
interface MilestoneCreate { title: string; body?: string; happenedOn: LocalDate; }
interface MilestoneUpdate { title?: string; body?: string | null; happenedOn?: LocalDate; }
```

### Comment

```ts
interface CommentCreate { body: string; }
interface CommentUpdate { body: string; }
interface CommentDetail {
  id: UUID;
  spaceId: UUID;
  authorId: UUID;
  body: string;
  version: number;
  createdAt: Instant;
  updatedAt: Instant;
  author: AuthorSummary;
}
```

### Attachment

Public status is limited to states meaningful to clients:

```ts
type AttachmentStatus = "PENDING" | "PROCESSING" | "READY" | "FAILED";

interface AttachmentSummary {
  id: UUID;
  status: AttachmentStatus;
  mediaType: "IMAGE" | "VIDEO";
  mimeType: string;
  size: number;
  width?: number;
  height?: number;
  durationSeconds?: number;
  version: number;
  createdAt: Instant;
}

interface UploadDescriptor {
  attachment: AttachmentSummary;
  method: "STREAM" | "SIGNED_UPLOAD";
  uploadUrl: string;
  expiresAt?: Instant;
  requiredHeaders: Record<string, string>;
}

interface ReadDescriptor {
  method: "STREAM" | "SIGNED_URL";
  url: string;
  expiresAt?: Instant;
}
```

Internal states such as `VALIDATING`, `DELETING`, `DELETE_FAILED`, storage keys, bucket names, provider, filesystem paths, and credentials are not client fields.

`AttachmentReadRequest` contains the authorized parent reference as a closed object:

```ts
type AttachmentReadRequest =
  | { parentType: "MEMORY"; parentId: UUID }
  | { parentType: "HEART_MOMENT"; parentId: UUID }
  | { parentType: "NONE" };
```

The server rechecks parent, space, and privacy; a parent reference is not a capability token.

`parentType: "NONE"` denotes the owner's still-unbound upload within the M2-D20 binding window (M2-D24). It is not an authorization shortcut: the server requires owner identity, `READY`, and an unexpired window. This variant is invalid for a bound attachment — only parent reachability applies there.

## 4. Story union

```ts
type StoryItem =
  | { kind: "MEMORY"; effectiveDate: LocalDate; memory: MemorySummary }
  | { kind: "HEART_MOMENT"; effectiveDate: LocalDate; heartMoment: SharedHeartMomentSummary }
  | { kind: "MILESTONE"; effectiveDate: LocalDate; milestone: MilestoneSummary };
```

No `PRIVATE` HeartMoment variant exists in the Story schema.

## 5. Story sorting and cursor – M2-D08

`effectiveDate` is determined per resource as:

1. domain `happenedOn`, when present,
2. otherwise the UTC calendar date of `createdAt`.

Canonical sort key:

```text
(effectiveDate, createdAt, kindRank, id)
```

with `kindRank`: `MEMORY=1`, `HEART_MOMENT=2`, `MILESTONE=3`.

- `DESC`: all four keys descending.
- `ASC`: all four keys ascending.
- Keyset pagination uses strict `>` or `<` over the complete tuple, never offset.
- Tenant and privacy filters are applied **before** sorting and cursor comparison.
- Identical date/time values create neither tie duplicates nor tie gaps because of `kindRank + id`.

Cursor format is opaque to clients. Server-side version 1 encodes at least:

```json
{
  "v": 1,
  "order": "DESC",
  "filterHash": "...",
  "effectiveDate": "2026-08-25",
  "createdAt": "2026-08-25T07:00:00Z",
  "kind": "MEMORY",
  "id": "..."
}
```

The cursor is integrity-protected/signed and bound to space, `type`, `year`, `order`, and filter context independent of `limit`. A cursor from another space or with changed filters is rejected neutrally as `400 INVALID_CURSOR`. `limit` may decrease or increase between pages without changing the logical continuation point.

Concurrent domain changes to sort fields do not promise a historical snapshot; clients may reload after refresh. The invariant “no tie duplicates/gaps” applies to an unchanged sorted data set between two pages.

## 6. Collection pagination

Memories, Milestones, HeartMoments, and Comments use the same base cursor contract. The concrete sort key is documented per collection but is at least uniquely determined by `createdAt, id`. Default `limit=50`, maximum `100`.

## 7. Error codes

Binding M2 codes:

| Code | HTTP | Meaning |
|---|---:|---|
| `RESOURCE_NOT_FOUND` | 404 | neutrally invisible/not present |
| `RESOURCE_VERSION_CONFLICT` | 409 | stale If-Match |
| `INVALID_CURSOR` | 400 | manipulated, foreign context, or incompatible version |
| `ATTACHMENT_TYPE_NOT_ALLOWED` | 415 | not in allowlist |
| `ATTACHMENT_TOO_LARGE` | 413 | server-side limit exceeded |
| `ATTACHMENT_VALIDATION_FAILED` | 422 | media validation failed |
| `ATTACHMENT_NOT_READY` | 409 | bind/read before READY |
| `ATTACHMENT_ALREADY_LINKED` | 409 | exclusive binding violated |
| `ATTACHMENT_LIMIT_EXCEEDED` | 409 | parent cardinality/total-size limit violated |
| `COMMENT_TARGET_NOT_AVAILABLE` | 404 | parent invisible/not commentable |
| `RATE_LIMITED` | 429 | existing rate-limit convention |

Pydantic form validation remains `422` with the existing Problem Details transport. Privacy-relevant errors must contain no existence/count/metadata leaks.

## 8. OpenAPI handoff

`API-CONTRACT.json` is a pre-runtime manifest, not a second production OpenAPI document. The CI test checks:

- unique operation IDs and method/routes,
- space-scoped paths,
- required If-Match for mutable resources,
- Story filters and cursor contract,
- exclusion of `q` from G2,
- exclusion of `privacyClass` from client write fields,
- exclusion of internal storage fields from attachment descriptors,
- no PRIVATE Story variant.

For each runtime slice, the implemented FastAPI contract in `backend/openapi.json` must be brought into exact alignment with the manifest operations belonging to that slice. `backend/openapi.json` continues to be generated exclusively with `uv run python scripts/openapi_contract.py write`.

## Related documents

- [API Contract Manifest](./API-CONTRACT.json)
- [Domain Model](./DOMAIN-MODEL.md)
- [Media Pipeline](./MEDIA-PIPELINE.md)
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md)
- [Decision Log](./DECISION-LOG.md)
