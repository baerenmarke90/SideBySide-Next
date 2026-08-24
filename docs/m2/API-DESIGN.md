# M2 API Design

**Status:** Operations- und Contract-Entwurf; noch kein OpenAPI-Code  
**Version:** 1.0

Dieses Dokument beschreibt, welche fachlichen Operationen M2 benötigt. Exakte URI-Namen, Schemas und Beispiele werden in Issue #8 bzw. dem danach versionierten OpenAPI-Vertrag verbindlich. Dadurch entsteht kein paralleler Eingriff in den laufenden OpenAPI-/CI-Strang.

## 1. Gemeinsame Regeln

- Basis: `/api/v1/spaces/{spaceId}/...`.
- Externe JSON-Felder sind `camelCase`.
- Persistente IDs sind UUIDv7-Strings.
- Jeder Zugriff prüft Authentifizierung, aktive Membership, Space-Zuordnung und Ressourcenberechtigung.
- Privacy-relevante Nichtberechtigung antwortet neutral mit 404.
- Veränderbare Ressourcen verwenden `version`; veraltete Änderungen liefern 409.
- Technische Zeitpunkte sind UTC-Instants, fachliche Tage `YYYY-MM-DD`.
- Fehler verwenden das gemeinsame Problem-Details-Schema mit stabilem `code`.
- Story und wachsende Listen verwenden Cursor-Pagination.

## 2. Operation Catalog

Die Bezeichner sind stabiler Planungswortschatz; konkrete Routes werden im OpenAPI-Review festgelegt.

### Memory

| Operation ID | Zweck | wesentliche Eingabe | Ergebnis |
|---|---|---|---|
| `createMemory` | gemeinsame Erinnerung anlegen | title, body, happenedOn?, attachmentIds? | 201 MemoryDetail |
| `listMemories` | Space-Memories lesen | cursor, limit, optional Filter | CursorPage<MemorySummary> |
| `getMemory` | Detail laden | memoryId | MemoryDetail |
| `updateMemory` | Autorinhalt ändern | version + Änderungen | MemoryDetail mit neuer Version |
| `deleteMemory` | Erinnerung löschen | version | 204 |

### HeartMoment

| Operation ID | Zweck | wesentliche Eingabe | Ergebnis |
|---|---|---|---|
| `createHeartMoment` | privaten/geteilten Moment anlegen | text, emotion, visibility, happenedOn, attachmentId? | 201 HeartMomentDetail |
| `listHeartMoments` | nur berechtigte Momente lesen | cursor, limit, visibility? | CursorPage<HeartMomentSummary> |
| `getHeartMoment` | Detail laden | heartMomentId | HeartMomentDetail oder neutrales 404 |
| `updateHeartMoment` | eigenen Moment ändern | version + Änderungen | neue Version |
| `changeHeartMomentVisibility` | Privacy bewusst wechseln | version + visibility | neue Version |
| `deleteHeartMoment` | eigenen Moment löschen | version | 204 |

Ein Partner darf `PRIVATE` weder über Listen noch per ID erkennen. Ein generischer „forbidden“ Unterschied ist nicht zulässig.

### Milestone

| Operation ID | Zweck | wesentliche Eingabe | Ergebnis |
|---|---|---|---|
| `createMilestone` | Meilenstein anlegen | title, body?, happenedOn | 201 MilestoneDetail |
| `listMilestones` | Space-Meilensteine lesen | cursor, limit, year? | CursorPage<MilestoneSummary> |
| `getMilestone` | Detail laden | milestoneId | MilestoneDetail |
| `updateMilestone` | Inhalt ändern | version + Änderungen | neue Version |
| `deleteMilestone` | Meilenstein löschen | version | 204 |

### Attachment

| Operation ID | Zweck | wesentliche Eingabe | Ergebnis |
|---|---|---|---|
| `createAttachmentUpload` | PENDING-Attachment und Uploadziel erzeugen | mediaType, originalName, erwartete Größe/MIME | UploadDescriptor |
| `finalizeAttachmentUpload` | Upload prüfen und finalisieren | attachmentId, ggf. Uploadnachweis | PROCESSING/READY/FAILED Status |
| `getAttachment` | sichere Metadaten lesen | attachmentId im autorisierten Ressourcenkontext | AttachmentDetail |
| `createAttachmentReadAccess` | kurzlebigen Abruf ermöglichen | attachmentId + autorisierte Zielreferenz | ReadDescriptor |
| `deleteAttachment` | unreferenziertes eigenes Medium entfernen | attachmentId | 204/Conflict |

Der konkrete Direct-Upload-/Streamingmechanismus bleibt MediaStore-Adapterentscheidung. API und Client benötigen unabhängig davon dieselben Lifecycle-Zustände.

### Comment

| Operation ID | Zweck | wesentliche Eingabe | Ergebnis |
|---|---|---|---|
| `createComment` | Kommentar an zulässigem Shared-Target anlegen | targetType, targetId, body | 201 CommentDetail |
| `listComments` | Kommentare eines Targets lesen | targetType, targetId, cursor, limit | CursorPage<CommentDetail> |
| `updateComment` | eigenen Kommentar ändern | commentId, version? + body | CommentDetail |
| `deleteComment` | eigenen Kommentar löschen | commentId, version? | 204 |

Targettypen sind geschlossen enumeriert. Ob `version` für Comment verpflichtend wird, ist eine Blocking Decision.

### Story

| Operation ID | Zweck | Eingabe | Ergebnis |
|---|---|---|---|
| `getStoryTimeline` | abgeleitete gemeinsame Timeline | type?, year?, q?, order?, cursor?, limit? | CursorPage<StoryItem> |

Vorgesehene Route laut Master-Spezifikation: `GET /api/v1/spaces/{spaceId}/timeline`.

## 3. DTO-Skizzen

### Shared metadata

```ts
interface M2EntityMeta {
  id: UUID;
  spaceId: UUID;
  authorId: UUID;
  version: number;
  createdAt: Instant;
  updatedAt: Instant;
}

interface AuthorSummary {
  id: UUID;
  displayName: string;
  profileAttachmentId?: UUID;
}
```

`AuthorSummary` enthält nur UI-notwendige, im Space freigegebene Profildaten.

### Memory

```ts
interface MemoryDetail extends M2EntityMeta {
  title: string;
  body: string;
  happenedOn?: LocalDate;
  author: AuthorSummary;
  attachments: AttachmentSummary[];
  capabilities: {
    canEdit: boolean;
    canDelete: boolean;
    canComment: boolean;
  };
}
```

### HeartMoment

```ts
type HeartEmotion =
  | "LOVED" | "SEEN" | "APPRECIATED"
  | "SUPPORTED" | "GRATEFUL" | "HAPPY";

type HeartVisibility = "SHARED" | "PRIVATE";

interface HeartMomentDetail extends M2EntityMeta {
  text: string;
  emotion: HeartEmotion;
  visibility: HeartVisibility;
  privacyClass: "SPACE_SHARED" | "OWNER_ONLY";
  happenedOn: LocalDate;
  attachment?: AttachmentSummary;
  capabilities: {
    canEdit: boolean;
    canDelete: boolean;
    canComment: boolean;
    canChangePrivacy: boolean;
  };
}
```

Die API kann `visibility` als Domainwert und `privacyClass` als allgemeine Zugriffsklasse führen oder eindeutig ableiten. Eine doppelte, potenziell widersprüchliche Speicherung ist zu vermeiden.

### Milestone

```ts
interface MilestoneDetail extends M2EntityMeta {
  title: string;
  body?: string;
  happenedOn: LocalDate;
  author: AuthorSummary;
  capabilities: ResourceCapabilities;
}
```

### Attachment

```ts
type AttachmentStatus = "PENDING" | "VALIDATING" | "READY" | "FAILED";

interface AttachmentSummary {
  id: UUID;
  status: AttachmentStatus;
  mediaType: string;
  mimeType: string;
  size: number;
  width?: number;
  height?: number;
  duration?: number;
  createdAt: Instant;
}

interface UploadDescriptor {
  attachment: AttachmentSummary;
  method: "STREAM" | "SIGNED_UPLOAD";
  uploadUrl?: string;
  expiresAt?: Instant;
  requiredHeaders?: Record<string, string>;
}

interface ReadDescriptor {
  method: "STREAM" | "SIGNED_URL";
  url: string;
  expiresAt?: Instant;
}
```

`storageKey`, interne Bucketnamen und Providerdetails werden nicht als reguläre Clientfelder veröffentlicht.

### Story

```ts
type StoryItem =
  | { kind: "MEMORY"; occurredOn: LocalDate; memory: MemorySummary }
  | { kind: "HEART_MOMENT"; occurredOn: LocalDate; heartMoment: SharedHeartMomentSummary }
  | { kind: "MILESTONE"; occurredOn: LocalDate; milestone: MilestoneSummary };

interface CursorPage<T> {
  items: T[];
  nextCursor: string | null;
  hasMore: boolean;
}
```

Private HeartMoments sind keine mögliche Story-Union-Variante.

## 4. Validation

Konkrete Längen und Medienlimits werden im Decision Log entschieden. Unabhängig davon gelten:

- `title` nach fachlicher Normalisierung nicht leer,
- `body`/`text` gemäß bestätigter Leer- und Längenregel,
- `happenedOn` ist ein Datum, kein UTC-Timestamp,
- Emotion und Visibility sind geschlossene Enums,
- Attachment-ID muss zum selben Space gehören und verwendbar sein,
- Comment-Target muss zulässig, shared und im selben Space sein,
- `limit` besitzt serverseitige Obergrenze,
- `cursor` ist undurchsichtig und an Filter-/Sortierkontext gebunden,
- unbekannte Targettypen oder Sortierwerte werden stabil abgelehnt.

## 5. Concurrency

Update und Delete senden die geladene `version` gemäß globalem API-Pattern. Bei Abweichung:

```json
{
  "type": "conflict",
  "title": "Resource changed",
  "status": 409,
  "detail": "The resource was changed since it was loaded.",
  "code": "RESOURCE_VERSION_CONFLICT"
}
```

- Kein Last-Write-Wins.
- Privacy-Wechsel wird nicht automatisch gemerged.
- Konfliktantwort enthält keine fremden/private Inhalte.
- Gelöschte Ressource wird nicht als Konflikt mit rekonstruierbarem Inhalt geleakt.

## 6. Fehlercode-Katalog

| Code | HTTP | UI-Reaktion |
|---|---:|---|
| `MEMORY_TITLE_REQUIRED` | 400/422 | Feldfehler Titel |
| `HEART_MOMENT_TEXT_REQUIRED` | 400/422 | Feldfehler Text |
| `HEART_MOMENT_EMOTION_INVALID` | 400/422 | Auswahl korrigieren |
| `HEART_MOMENT_VISIBILITY_INVALID` | 400/422 | Auswahl korrigieren |
| `MILESTONE_TITLE_REQUIRED` | 400/422 | Feldfehler Titel |
| `COMMENT_TARGET_INVALID` | 400/422 | generischer nicht verfügbarer Targetzustand |
| `COMMENT_TARGET_NOT_SHARED` | 404 | Existenz/Privacy nicht bestätigen |
| `ATTACHMENT_TYPE_NOT_ALLOWED` | 415 | Datei entfernen/ersetzen |
| `ATTACHMENT_TOO_LARGE` | 413 | Limit nennen, wenn sicher |
| `ATTACHMENT_VALIDATION_FAILED` | 400/422 | Datei ersetzen/Retry gemäß Ursache |
| `ATTACHMENT_NOT_READY` | 409 | Verarbeitung abwarten oder Retry |
| `ATTACHMENT_ALREADY_LINKED` | 409 | Entscheidung gemäß Relationsmodell |
| `RESOURCE_VERSION_CONFLICT` | 409 | aktuelle Version laden |
| `RATE_LIMITED` | 429 | Retry-Zeit anzeigen |
| `RESOURCE_NOT_FOUND` | 404 | neutral „nicht verfügbar“ |

Der finale Codekatalog wird im OpenAPI-Vertrag eingefroren. Fehlerdetails enthalten weder Suchtreffer noch Metadaten fremder Ressourcen.

## 7. Story Query Contract

### Filter

- `type`: kontrollierte Menge `MEMORY`, `HEART_MOMENT`, `MILESTONE`, optional mehrere gemäß finalem API-Design.
- `year`: fachliches Kalenderjahr.
- `q`: serverseitige Suche; Suchtext niemals Analytics/Logs.
- `order`: `ASC` oder `DESC`.
- `cursor`: undurchsichtiger Fortsetzungspunkt.
- `limit`: Default und Maximum serverseitig festgelegt.

### Sortierstabilität

Cursor muss mindestens berücksichtigen:

- effektives Story-Datum,
- stabilen Typ-Tie-Breaker,
- Resource-ID oder gleichwertigen eindeutigen Tie-Breaker,
- Filter-/Sortierrichtung.

Die Abfrage filtert Tenant und Privacy **vor** Sortierung, Pagination und Trefferzählung.

## 8. Cache- und Clientwirkung

- Web Query Keys enthalten Space, Operation, Filter, Sortierung und Cursor.
- Android Read Cache speichert nur zuletzt autorisierte Shared-Daten sowie Owner-only-Daten getrennt nach Account/Space.
- Offline ist Read-only; Writes liefern keinen lokalen Domainerfolg.
- Nach Privacy-Wechsel oder Logout werden betroffene Cacheeinträge sofort invalidiert/gesperrt.
- Attachment-Read-URLs sind kurzlebig und werden nicht als dauerhafte Medienadresse gecacht.

## 9. OpenAPI-Übergabe

Vor M2-Codebeginn wird dieser Entwurf gegen den dann aktuellen OpenAPI-Mechanismus übertragen:

- operation IDs und Pfade,
- Request-/Response-Schemas,
- Enum-Werte,
- Feldgrenzen und Beispiele,
- Problem Details und Fehlercodes,
- Security Schemes,
- Pagination,
- Version/If-Match-Konvention,
- Upload-/Read-Descriptor,
- Contract-Beispiele für Web und Android.

Keine Route wird allein aus diesem Dokument implementiert, wenn der versionierte OpenAPI-Vertrag abweicht.

## Verwandte Dokumente

- [Domain Model](./DOMAIN-MODEL.md)
- [Media Pipeline](./MEDIA-PIPELINE.md)
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md)
- [Decision Log](./DECISION-LOG.md)
