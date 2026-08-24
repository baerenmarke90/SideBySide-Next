# SideBySide API/UI Contracts

**Status:** Verbindliche Integrationsgrundlage  
**Version:** 1.0  
**Stand:** 24.08.2026

Dieses Dokument definiert die gemeinsame Sprache zwischen REST API, React-WebApp und Android-App. OpenAPI unter `/api/v1` bleibt der ausführbare Vertrag; diese Datei legt fest, wie fachliche und technische Zustände in beiden Clients verstanden und dargestellt werden.

## 1. Quellen und Vorrang

Bei Widersprüchen gilt folgende Reihenfolge:

1. Clean-Room Master Specification.
2. Produktspezifikation und Security-Invarianten.
3. veröffentlichter OpenAPI-Vertrag.
4. dieses Dokument und UX-Dokumentation.
5. plattformspezifische Implementierungsdetails.

Ein Client darf keine fachliche Regel ergänzen, die nur lokal existiert.

## 2. Transportkonventionen

| Thema | Vertrag |
|---|---|
| Basis | HTTPS, REST, `/api/v1/...` |
| Format | JSON |
| externe Feldnamen | `camelCase` |
| persistente IDs | nicht aufzählbare UUIDv7 als String |
| technischer Zeitpunkt | RFC-3339/ISO-8601 mit Zeitzone, serverseitig UTC |
| fachlicher Tag | `YYYY-MM-DD`, keine Zeitzone |
| Create | 201 |
| Read | 200 |
| Update | 200 |
| Delete | 204 |
| Validation | 400 oder 422 gemäß OpenAPI |
| Unauthenticated | 401 |
| Forbidden | 403, außer privacy-sicheres 404 |
| Not found / verborgen | 404 |
| Version conflict | 409 |
| Rate limit | 429 |

- Android authentifiziert API-Aufrufe mit kurzlebigem Bearer Token und sicher gespeicherter, rotierender Session.
- Credentials, Tokens und Einladungswerte erscheinen nie in URLs nach Abschluss, Analytics, Crashdaten oder Logs.
- Clients verwenden ausschließlich OpenAPI-Felder; unbekannte zusätzliche Felder werden tolerant ignoriert.
- Entfernen oder Bedeutungsänderung veröffentlichter Felder ist innerhalb von v1 nicht kompatibel.

## 3. Gemeinsame Typen

Die folgenden TypeScript-ähnlichen Definitionen beschreiben Semantik, nicht eine konkrete generierte Datei.

```ts
type UUID = string;
type Instant = string;  // RFC 3339, z. B. 2026-08-24T10:15:30Z
type LocalDate = string; // YYYY-MM-DD

type PrivacyClass =
  | "SPACE_SHARED"
  | "OWNER_ONLY"
  | "TEMPORARY_SHARED"
  | "EPHEMERAL_CONTEXT"
  | "SYSTEM_METADATA";

interface EntityMeta {
  id: UUID;
  version: number;
  createdAt: Instant;
  updatedAt: Instant;
}

interface SpaceResourceMeta extends EntityMeta {
  spaceId: UUID;
  privacyClass: PrivacyClass;
  authorId?: UUID;
}
```

`spaceId` und Berechtigungsangaben im DTO ersetzen niemals serverseitige Membership- und Tenant-Prüfungen.

## 4. Privacy-Klassen und UI-Abbildung

| API-Wert | Fachliche Bedeutung | reguläres UI-Label | Client-Verhalten |
|---|---|---|---|
| `SPACE_SHARED` | beide aktiven Partner im Space | Geteilt | im gemeinsamen Bereich sichtbar |
| `OWNER_ONLY` | ausschließlich Eigentümer | Nur für mich | nie für Partner anfordern, cachen oder indirekt anzeigen |
| `TEMPORARY_SHARED` | zeitlich begrenzte Freigabe | Zeitlich geteilt | erst anzeigen, wenn Domain und Ablauf spezifiziert sind |
| `EPHEMERAL_CONTEXT` | kurzlebiger Kontext mit Ablauf | kontextabhängig | nicht als dauerhaften Inhalt darstellen |
| `SYSTEM_METADATA` | technischer Nicht-Nutzerinhalt | kein Endnutzerlabel | nur für notwendige Systemfunktionen |

- Die vereinfachten UI-Zustände `private` und `shared` sind Präsentationswerte, keine API-Enums.
- `public` ist kein zulässiger Wert.
- Nicht jede Domain unterstützt einen Wechsel der Privacy-Klasse.
- Memory, Wish und Plan sind im aktuellen Core `SPACE_SHARED`; private Inhalte verwenden eigene Owner-only-Domänen.
- HeartMoment unterstützt `OWNER_ONLY` und `SPACE_SHARED`.

## 5. Problem Details

Jeder API-Fehler verwendet ein Problem-Details-artiges Schema:

```json
{
  "type": "validation_error",
  "title": "Invalid request",
  "status": 400,
  "detail": "The title must not be empty.",
  "code": "MEMORY_TITLE_REQUIRED",
  "requestId": "0191...",
  "fieldErrors": [
    { "field": "title", "code": "REQUIRED", "message": "Titel fehlt." }
  ]
}
```

### Pflicht und optional

| Feld | Pflicht | Verwendung |
|---|---:|---|
| `type` | ja | grobe maschinenlesbare Kategorie |
| `title` | ja | kurze technische Standardüberschrift |
| `status` | ja | HTTP-Status |
| `detail` | ja | sichere, verständliche Erklärung |
| `code` | ja | stabiler fachlicher Fehlercode |
| `requestId` | empfohlen | Supportkorrelation, keine Ressource-ID |
| `fieldErrors` | bei Feldfehlern | direkte Formularzuordnung |

- UI-Logik verzweigt nach `code` und `status`, nie nach übersetztem `detail`.
- Clients dürfen sichere, lokalisierte Texte anhand stabiler Codes anzeigen.
- `detail` verrät keine Existenz oder Metadaten fremder/privater Ressourcen.
- Unbekannte Codes fallen auf eine sichere generische Meldung mit Retry/Supportweg zurück.

## 6. Fehler-zu-UI-Mapping

| Status | Clientzustand | Nutzerreaktion |
|---:|---|---|
| 400/422 | Feld- oder Formfehler | Eingabe erhalten, Fehler inline anzeigen |
| 401 | Sitzung ungültig | sichere Re-Authentifizierung, Zielkontext erhalten |
| 403 | bekannte fehlende Fähigkeit | Voraussetzung erklären; keine Retry-Schleife |
| 404 | nicht verfügbar | neutraler Zustand ohne Existenzbestätigung |
| 409 | Versionskonflikt | aktuelle Version laden, bewusst entscheiden |
| 413/415 | Medien nicht zulässig | betroffene Datei erklären/entfernen |
| 429 | Rate Limit | Wartezeit anzeigen, automatische Wiederholung begrenzen |
| 5xx | temporärer Dienstfehler | vorhandene Daten behalten, Retry anbieten |
| Netzwerkfehler | offline/unterbrochen | kein Erfolg; Android-Read-Cache ggf. anzeigen |

## 7. Optimistic Concurrency

Veränderbare Ressourcen tragen `version`.

```ts
interface UpdateCommand<T> {
  version: number;
  changes: T;
}
```

- Der Client sendet die zuletzt geladene Version gemäß OpenAPI, beispielsweise als Feld oder `If-Match`.
- Bei 409 wird nichts lokal als gespeichert markiert.
- Konfliktantworten enthalten nur Inhalte, für die der aktuelle Account weiterhin berechtigt ist.
- Web invalidiert die betroffene TanStack-Query; Android aktualisiert Read-Cache erst nach erfolgreicher autorisierter Antwort.
- Delete, Privacy-Wechsel und Membership-Zustände werden nie automatisch zusammengeführt.

## 8. Cursor-Pagination

Story und andere wachsende Listen verwenden Cursor statt Seitennummer:

```ts
interface CursorPage<T> {
  items: T[];
  nextCursor: string | null;
  hasMore: boolean;
}
```

- Cursor ist undurchsichtig und wird nicht interpretiert.
- Filter, Sortierung und Suchparameter gehören zur Cache-Identität.
- Ein Cursor aus einem anderen Filterkontext wird nicht wiederverwendet.
- Private Filterung erfolgt serverseitig vor Pagination und Trefferzählung.
- Doppelte IDs beim Nachladen werden anhand `id` zusammengeführt, ohne neuere `version` zu überschreiben.

## 9. Abgeleitete Sichten

Story, Dashboard, „Weißt du noch?“ und Rückblicke sind Read Models, keine unabhängig editierbaren Ressourcen.

```ts
type StoryItem =
  | { kind: "MEMORY"; item: MemorySummary }
  | { kind: "HEART_MOMENT"; item: SharedHeartMomentSummary }
  | { kind: "MILESTONE"; item: MilestoneSummary };
```

- Ein StoryItem verlinkt auf das Original.
- `OWNER_ONLY` ist als Story-Variante nicht zulässig.
- Leere Statistikblöcke dürfen fehlen; Clients erwarten keine künstlichen Nullkarten.
- Read Models enthalten die minimale Information für die jeweilige Ansicht.

## 10. Fähigkeiten statt UI-Raten

Wenn fachliche Berechtigungen variieren, liefert die API explizite Fähigkeiten:

```ts
interface ResourceCapabilities {
  canEdit: boolean;
  canDelete: boolean;
  canComment: boolean;
  canChangePrivacy: boolean;
}
```

- Capabilities verbessern Darstellung, sind aber keine Autorisierung; der Server prüft jede Aktion erneut.
- Clients leiten Berechtigung nicht aus Autorname, Farbe oder sichtbaren Buttons ab.
- Nicht verfügbare Aktionen werden ausgeblendet oder erklärt, abhängig davon, ob die Funktion grundsätzlich relevant ist.

## 11. Netzwerk- und Cache-Vertrag

```ts
type DataFreshness = "LIVE" | "STALE_CACHE";
type WriteAvailability = "AVAILABLE" | "OFFLINE_BLOCKED" | "SESSION_BLOCKED";
```

### Android MVP

- Room dient als autorisierter Read-Cache.
- `STALE_CACHE` zeigt letzten erfolgreichen Stand und Zeitbezug.
- Offline-Schreiben, lokale Outbox und automatischer späterer Sync sind **nicht** Teil des MVP.
- Ein Formularentwurf darf lokal erhalten bleiben, wird aber nicht als Domainobjekt oder `synced` markiert.
- Accountabmeldung, Sitzungswiderruf und Space-Wechsel behandeln Cache und Entwürfe nach Sicherheitskonzept.

### Web

- Query-Caches sind flüchtige Darstellungscaches, keine zweite Datenquelle.
- Nach Mutationen werden betroffene Query Keys gezielt invalidiert.
- Sensible Inhalte werden nicht ohne gesonderte Entscheidung dauerhaft im Browser gespeichert.

## 12. Upload-Vertrag

Unabhängig von direkter autorisierter Route oder signiertem Upload benötigt die UI diese Zustände:

```ts
type UploadState =
  | "SELECTED"
  | "VALIDATING"
  | "UPLOADING"
  | "PROCESSING"
  | "READY"
  | "FAILED";
```

Ein Attachment DTO enthält mindestens stabile ID, Status, sicheren Medientyp, Größe, optionale Dimensionen und eine autorisierte Abrufmöglichkeit. Original-Dateiname ist niemals Storage Key und wird nicht für Autorisierung verwendet.

## 13. Auth- und Einladungsvertrag

- Auth-Methoden sind Adapter um denselben Account-/Session-Kern.
- Android-Sessions sind einzeln widerrufbar und rotieren Refresh Tokens.
- Invitation besitzt Status, Ablauf, Widerruf und einmalige Einlösung.
- Ein Einladungsfehler unterscheidet intern stabile Codes für `EXPIRED`, `REVOKED`, `USED`, `SPACE_FULL`, `INVALID`; die UI verrät keine weiteren Space-Daten.
- Gleichzeitige Annahmen werden serverseitig atomar entschieden.

## 14. Feature Configuration und Entitlement

Technische Aktivierung und tarifliche Berechtigung bleiben getrennt:

```ts
interface FeatureAccess {
  enabled: boolean;
  entitled: boolean;
  reason?: "NOT_CONFIGURED" | "NOT_ENTITLED" | "NOT_AVAILABLE";
}
```

Der Client zeigt keine kostenbezogene Erklärung, wenn eine Funktion technisch nicht konfiguriert ist, und umgekehrt.

## 15. Analytics-Vertrag

Jedes UI-Ereignis besteht aus:

```ts
interface AnalyticsEvent {
  name: string;
  schemaVersion: number;
  platform: "web" | "android";
  appVersion: string;
  result?: "success" | "failure" | "cancelled";
  errorCode?: string;
}
```

Nicht enthalten: Freitext, Suchtext, E-Mail, Partnername, Resource-ID, Token, genaue private Daten, Dateiname, Medieninhalt, Präferenzwert oder präziser Standort.

## 16. Contract Delivery

- Backend veröffentlicht OpenAPI aus dem tatsächlichen API-Code.
- Web und Android generieren oder kapseln Modelle aus derselben OpenAPI-Version.
- Contract-Tests prüfen Beispielantworten, Fehlercodes, Privacy-Klassen und unbekannte Felder.
- Jede Domain erhält Cross-Tenant- und Owner-only-Tests vor Clientfreigabe.
- Mock-Daten verwenden ausschließlich synthetische Inhalte.
- Breaking Changes erfordern eine neue API-Version oder dokumentierte Migration.

## 17. Definition of Done

Ein UI-fähiges API-Feature ist erst fertig, wenn:

- OpenAPI Request, Response und Fehlercodes beschreibt,
- UUID, Datum, Timestamp, Privacy-Klasse und `version` korrekt modelliert sind,
- 401, privacy-sicheres 404, 409, 429 und Netzwerkfehler im Client behandelt sind,
- Cursor-/Cache-Verhalten festgelegt ist,
- Web und Android dieselbe fachliche Validierung zeigen,
- Analytics und Logs keine sensiblen Inhalte erhalten,
- Tenant-, Owner-only- und Uploadtests vorhanden sind,
- Offline-Schreiben im MVP nicht fälschlich suggeriert wird.

## Verwandte Dokumente

- [Architektur](./ARCHITECTURE.md)
- [Security](./SECURITY.md)
- [User Flows](./USER-FLOWS.md)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Content- und Privacy-Guidelines](./CONTENT-PRIVACY-GUIDELINES.md)
