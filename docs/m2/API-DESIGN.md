# M2 API Design

**Status:** Verbindlicher Pre-Runtime-Contract nach M2-S0 #70  
**Version:** 2.0

Dieses Dokument friert Routen, DTO-Namen, Concurrency- und Pagination-Semantik für M2 ein. Die maschinenlesbare Planungsquelle ist `API-CONTRACT.json`. `backend/openapi.json` bleibt weiterhin ausschließlich der vom tatsächlich implementierten FastAPI-Code erzeugte Vertrag und wird erst mit dem jeweiligen Runtime-Slice aktualisiert. Damit gibt es keine vorgetäuschten Runtime-Endpunkte.

## 1. Globale Regeln

- Basis: `/api/v1/spaces/{spaceId}/...`.
- externe JSON-Felder: `camelCase`.
- persistente IDs: UUIDv7-Strings.
- Authentifizierung und aktive Membership werden vor jeder Space-Ressource geprüft.
- fremde oder privacy-geschützte Ressourcen liefern neutral `404`.
- `visibility` ist der öffentliche Domainwert; `privacyClass` ist intern und kein schreibbares oder regulär auszulieferndes Clientfeld.
- alle veränderbaren Ressourcen besitzen `version` und liefern `ETag`.
- `PATCH`/`DELETE` und explizite Relations-/Privacy-Mutationen verlangen `If-Match`.
- stale `If-Match` liefert `409 RESOURCE_VERSION_CONFLICT`.
- Problem Details und stabile `code`-Werte folgen dem bestehenden API-Stil.
- fachliche Tage sind `YYYY-MM-DD`; technische Zeitpunkte UTC-Instants.
- Collection- und Story-Seiten verwenden opake Keyset-Cursor.

## 2. Verbindlicher Routenkatalog

### Memory

| Methode | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/memories` | `createMemory` | `MemoryCreate` | `201 MemoryDetail` |
| GET | `/spaces/{spaceId}/memories` | `listMemories` | `cursor?`, `limit?`, `year?` | `MemoryPage` |
| GET | `/spaces/{spaceId}/memories/{memoryId}` | `getMemory` | – | `MemoryDetail` |
| PATCH | `/spaces/{spaceId}/memories/{memoryId}` | `updateMemory` | `If-Match`, `MemoryUpdate` | `MemoryDetail` |
| DELETE | `/spaces/{spaceId}/memories/{memoryId}` | `deleteMemory` | `If-Match` | `204` |
| PUT | `/spaces/{spaceId}/memories/{memoryId}/attachments` | `replaceMemoryAttachments` | `If-Match`, `MemoryAttachmentSet` | `MemoryDetail` |

`MemoryCreate` enthält in S2 **keine** Attachments; der Relation-Endpunkt wird erst mit dem Media-Integrationsslice implementiert. Der Contract ist dennoch jetzt festgelegt.

### HeartMoment

| Methode | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/heart-moments` | `createHeartMoment` | `HeartMomentCreate` | `201 HeartMomentDetail` |
| GET | `/spaces/{spaceId}/heart-moments` | `listHeartMoments` | `cursor?`, `limit?`, `visibility?` | `HeartMomentPage` |
| GET | `/spaces/{spaceId}/heart-moments/{heartMomentId}` | `getHeartMoment` | – | `HeartMomentDetail` |
| PATCH | `/spaces/{spaceId}/heart-moments/{heartMomentId}` | `updateHeartMoment` | `If-Match`, `HeartMomentUpdate` | `HeartMomentDetail` |
| PATCH | `/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility` | `changeHeartMomentVisibility` | `If-Match`, `HeartMomentVisibilityChange` | `HeartMomentDetail` |
| DELETE | `/spaces/{spaceId}/heart-moments/{heartMomentId}` | `deleteHeartMoment` | `If-Match` | `204` |

`SHARED -> PRIVATE` ist die in #68 definierte atomare Privacy-Operation. Private HeartMoments sind nur für den Owner sichtbar und niemals Story-Items.

### Milestone

| Methode | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/milestones` | `createMilestone` | `MilestoneCreate` | `201 MilestoneDetail` |
| GET | `/spaces/{spaceId}/milestones` | `listMilestones` | `cursor?`, `limit?`, `year?` | `MilestonePage` |
| GET | `/spaces/{spaceId}/milestones/{milestoneId}` | `getMilestone` | – | `MilestoneDetail` |
| PATCH | `/spaces/{spaceId}/milestones/{milestoneId}` | `updateMilestone` | `If-Match`, `MilestoneUpdate` | `MilestoneDetail` |
| DELETE | `/spaces/{spaceId}/milestones/{milestoneId}` | `deleteMilestone` | `If-Match` | `204` |

### Attachment

| Methode | Route | operationId | Request | Response |
|---|---|---|---|---|
| POST | `/spaces/{spaceId}/attachments` | `createAttachmentUpload` | `AttachmentUploadCreate` | `201 UploadDescriptor` |
| PUT | `/spaces/{spaceId}/attachments/{attachmentId}/content` | `uploadAttachmentContent` | LocalMediaStore Stream | `204` |
| POST | `/spaces/{spaceId}/attachments/{attachmentId}/finalize` | `finalizeAttachmentUpload` | `AttachmentFinalize` | `202 AttachmentDetail` |
| GET | `/spaces/{spaceId}/attachments/{attachmentId}` | `getAttachment` | – | `AttachmentDetail` |
| POST | `/spaces/{spaceId}/attachments/{attachmentId}/read-access` | `createAttachmentReadAccess` | `AttachmentReadRequest` | `ReadDescriptor` |
| DELETE | `/spaces/{spaceId}/attachments/{attachmentId}` | `deleteAttachment` | `If-Match` | `204` |

`uploadAttachmentContent` ist nur bei `STREAM`-Descriptor zulässig. Bei S3 liefert `createAttachmentUpload` einen `SIGNED_UPLOAD`-Descriptor. `finalize` bedeutet nur Annahme zur asynchronen Validierung, nicht `READY`.

### Comment

Create/List sind bewusst am Parent verschachtelt; Update/Delete sind Space-scoped über die Comment-ID.

| Methode | Route | operationId |
|---|---|---|
| POST | `/spaces/{spaceId}/memories/{memoryId}/comments` | `createMemoryComment` |
| GET | `/spaces/{spaceId}/memories/{memoryId}/comments` | `listMemoryComments` |
| POST | `/spaces/{spaceId}/heart-moments/{heartMomentId}/comments` | `createHeartMomentComment` |
| GET | `/spaces/{spaceId}/heart-moments/{heartMomentId}/comments` | `listHeartMomentComments` |
| POST | `/spaces/{spaceId}/milestones/{milestoneId}/comments` | `createMilestoneComment` |
| GET | `/spaces/{spaceId}/milestones/{milestoneId}/comments` | `listMilestoneComments` |
| PATCH | `/spaces/{spaceId}/comments/{commentId}` | `updateComment` |
| DELETE | `/spaces/{spaceId}/comments/{commentId}` | `deleteComment` |

Create verwendet `CommentCreate { body }`; Listen verwenden `cursor?`, `limit?`; Update verwendet `If-Match` + `CommentUpdate`; Delete verwendet `If-Match`. Ein Client sendet weder `targetType` noch `targetId` im Body; der Parent ist ausschließlich durch die Route bestimmt.

### Story

| Methode | Route | operationId |
|---|---|---|
| GET | `/spaces/{spaceId}/timeline` | `getStoryTimeline` |

G2-Filter:

- `type`: wiederholbarer Query-Parameter aus `MEMORY | HEART_MOMENT | MILESTONE`.
- `year`: `1900..2100`.
- `order`: `DESC` default, alternativ `ASC`.
- `cursor`: opak.
- `limit`: Default `50`, Maximum `100`.

`q` ist **nicht** Bestandteil des M2/G2-Vertrags und bleibt M4 Search.

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

Capabilities sind UX-Hilfe, keine Autorisierungsquelle.

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

`authorId`, `spaceId`, `version` und Capabilities sind nicht schreibbar. Partner lesen gemeinsame Memories; Update/Delete bleiben author-only.

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

`privacyClass` wird weder geschrieben noch als reguläres DTO-Feld veröffentlicht. `visibility` ist die einzige fachliche Clientwahrheit.

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

Öffentlicher Status wird auf die für Clients sinnvollen Zustände begrenzt:

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

Interne Zustände wie `VALIDATING`, `DELETING`, `DELETE_FAILED`, Storage Keys, Bucketnamen, Provider, Dateisystempfade und Credentials sind keine Clientfelder.

`AttachmentReadRequest` enthält die autorisierte Parentreferenz als geschlossenes Objekt:

```ts
type AttachmentReadRequest =
  | { parentType: "MEMORY"; parentId: UUID }
  | { parentType: "HEART_MOMENT"; parentId: UUID };
```

Der Server prüft Parent, Space und Privacy neu; eine Parentreferenz ist kein Capability-Token.

## 4. Story-Union

```ts
type StoryItem =
  | { kind: "MEMORY"; effectiveDate: LocalDate; memory: MemorySummary }
  | { kind: "HEART_MOMENT"; effectiveDate: LocalDate; heartMoment: SharedHeartMomentSummary }
  | { kind: "MILESTONE"; effectiveDate: LocalDate; milestone: MilestoneSummary };
```

Eine `PRIVATE` HeartMoment-Variante existiert im Story-Schema nicht.

## 5. Story-Sortierung und Cursor – M2-D08

`effectiveDate` wird pro Ressource bestimmt als:

1. fachliches `happenedOn`, falls vorhanden,
2. sonst UTC-Kalendertag von `createdAt`.

Kanonischer Sortierschlüssel:

```text
(effectiveDate, createdAt, kindRank, id)
```

mit `kindRank`: `MEMORY=1`, `HEART_MOMENT=2`, `MILESTONE=3`.

- `DESC`: alle vier Schlüssel absteigend.
- `ASC`: alle vier Schlüssel aufsteigend.
- Keyset-Pagination verwendet strikt `>` bzw. `<` auf dem vollständigen Tupel, nie Offset.
- Tenant- und Privacy-Filter werden **vor** Sortierung und Cursorvergleich angewandt.
- gleiche Datums-/Zeitwerte erzeugen dank `kindRank + id` weder Tie-Duplikate noch Tie-Lücken.

Cursorformat ist opak für Clients. Serverseitig kodiert Version 1 mindestens:

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

Der Cursor ist integritätsgeschützt/signiert und an Space, `type`, `year`, `order` und `limit`-unabhängigen Filterkontext gebunden. Ein Cursor aus einem anderen Space oder mit geänderten Filtern wird neutral als `400 INVALID_CURSOR` abgewiesen. `limit` darf zwischen Seiten verkleinert/vergrößert werden, ohne den logischen Fortsetzungspunkt zu ändern.

Bei konkurrierenden fachlichen Änderungen an Sortierfeldern ist kein historischer Snapshot versprochen; Clients können nach Refresh neu laden. Die Invariante „keine Tie-Duplikate/-Lücken“ bezieht sich auf den unveränderten sortierten Datenbestand zwischen zwei Seiten.

## 6. Collection-Pagination

Memories, Milestones, HeartMoments und Comments verwenden denselben Cursor-Grundvertrag. Der konkrete Sortierschlüssel ist pro Collection dokumentiert, mindestens jedoch eindeutig durch `createdAt, id`. Default `limit=50`, Maximum `100`.

## 7. Fehlercodes

Verbindliche M2-Codes:

| Code | HTTP | Bedeutung |
|---|---:|---|
| `RESOURCE_NOT_FOUND` | 404 | neutral nicht sichtbar/nicht vorhanden |
| `RESOURCE_VERSION_CONFLICT` | 409 | stale If-Match |
| `INVALID_CURSOR` | 400 | manipuliert, fremder Kontext oder inkompatible Version |
| `ATTACHMENT_TYPE_NOT_ALLOWED` | 415 | nicht in Allowlist |
| `ATTACHMENT_TOO_LARGE` | 413 | serverseitiges Limit überschritten |
| `ATTACHMENT_VALIDATION_FAILED` | 422 | Medienvalidierung fehlgeschlagen |
| `ATTACHMENT_NOT_READY` | 409 | Bind/Read vor READY |
| `ATTACHMENT_ALREADY_LINKED` | 409 | exklusive Bindung verletzt |
| `ATTACHMENT_LIMIT_EXCEEDED` | 409 | Parent-Kardinalität/Gesamtgröße verletzt |
| `COMMENT_TARGET_NOT_AVAILABLE` | 404 | Parent nicht sichtbar/nicht kommentierbar |
| `RATE_LIMITED` | 429 | bestehende Rate-Limit-Konvention |

Pydantic-Formvalidierung bleibt `422` mit dem bestehenden Problem-Details-Transport. Privacy-relevante Fehler dürfen keine Exists-/Count-/Metadata-Leaks enthalten.

## 8. OpenAPI-Übergabe

`API-CONTRACT.json` ist ein pre-runtime Manifest, kein zweites produktives OpenAPI-Dokument. Der CI-Test prüft:

- eindeutige operationIds und Methoden/Routen,
- Space-scoped Pfade,
- Pflicht-If-Match für veränderbare Ressourcen,
- Story-Filter und Cursorvertrag,
- Ausschluss von `q` aus G2,
- Ausschluss von `privacyClass` aus Client-Write-Feldern,
- Ausschluss interner Storagefelder aus Attachment-Deskriptoren,
- keine PRIVATE-Story-Variante.

Beim jeweiligen Runtime-Slice muss der implementierte FastAPI-Vertrag in `backend/openapi.json` exakt auf die zu diesem Slice gehörenden Manifestoperationen gezogen werden. `backend/openapi.json` wird weiterhin ausschließlich mit `uv run python scripts/openapi_contract.py write` erzeugt.

## Verwandte Dokumente

- [API Contract Manifest](./API-CONTRACT.json)
- [Domain Model](./DOMAIN-MODEL.md)
- [Media Pipeline](./MEDIA-PIPELINE.md)
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md)
- [Decision Log](./DECISION-LOG.md)
