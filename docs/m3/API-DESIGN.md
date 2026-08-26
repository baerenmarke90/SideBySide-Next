# M3 API Design

**Status:** `PROPOSED` – Vorlage für spätere Decisions und OpenAPI-Arbeit  
**Stand:** 26.08.2026

Diese Datei ändert **nicht** den produktiven OpenAPI-Vertrag. Sie beschreibt eine konsistente Zieloberfläche, damit die M3-S0-Decisions konkret gegen Routen, DTOs, Fehler und Transaktionen entschieden werden können.

## 1. Verbindliche API-Grundsätze

M3 übernimmt die bestehenden Projektkonventionen:

- REST unter `/api/v1/...`;
- alle fachlichen Ressourcen space-scoped;
- UUIDv7-IDs;
- externe JSON-Felder `camelCase`;
- einheitliche Problem Details mit stabilem `code`;
- Membership vor Ressourcenauflösung;
- privacy-sicheres 404 für nicht lesbare/owner-only Ressourcen;
- 403 nur für bekannte lesbare Ressourcen, bei denen die Aktion nicht erlaubt ist;
- veränderbare Ressourcen mit `version`/ETag und `If-Match`;
- stale mutation -> `409 RESOURCE_VERSION_CONFLICT`;
- keine Client-Autorisierung als Sicherheitsgrenze;
- keine polymorphe Universalrelation ohne serverseitige Target-Allowlist und DB-FKs.

## 2. List- und Pagination-Konvention

`PROPOSED`: wachsende M3-Listen verwenden dieselbe opake Cursor-Konvention wie bestehende APIs.

Gemeinsame Parameter, soweit fachlich sinnvoll:

```text
limit
cursor
order
```

Domainfilter:

- Wish: `status`, optional `createdBy`
- Plan: `status`, optional `createdBy`, optional Zeitraum
- Place: keine globale Volltextsuche in M3; einfache stabile Sortierung
- Chapter: optional Datumsbereich
- Collection: keine globale Contentsuche in M3
- Private Area: nur Owner-Scope; keine Partneransicht

Ein `q`-Parameter für globale Volltextsuche ist **nicht Teil von M3**. Search gehört M4-A.

## 3. Wish API

### Proposed Routen

```text
POST   /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes/{wishId}
PATCH  /api/v1/spaces/{spaceId}/wishes/{wishId}
DELETE /api/v1/spaces/{spaceId}/wishes/{wishId}
```

Ob `PATCH` beliebige Statusänderungen erlaubt, ist ausdrücklich **nicht** entschieden. Bevorzugt werden fachliche Statuswechsel über eigene Operationen, wenn dabei Relationen/Transaktionen betroffen sind.

### Proposed DTO

```text
WishCreateRequest
- title

WishUpdateRequest
- title?

WishResponse
- id
- spaceId
- title
- status
- createdBy
- createdAt
- updatedAt
- version
- capabilities?
```

`capabilities` kann später UI-Raten vermeiden (`canEdit`, `canDelete`, `canConvertToPlan`), ersetzt aber nie Serverautorisierung.

## 4. Wish -> Plan als eigene Domainoperation

Die Konvertierung ist keine normale `PATCH status=PLANNED`, weil mindestens zwei Domainobjekte und eine Relation atomar betroffen sind.

### Proposed Route

```text
POST /api/v1/spaces/{spaceId}/wishes/{wishId}/plan
If-Match: "<wish-version>"
```

Request, abhängig von M3-D02/D04:

```text
WishToPlanRequest
- title?          # wenn Abweichung vom Wish-Titel erlaubt wird
- description?
- plannedStart?
- plannedEnd?
- placeId?
```

Response:

```text
WishToPlanResponse
- wish: WishResponse
- plan: PlanResponse
```

### Transaktionsvertrag

Ein erfolgreicher Request muss in **einem Commit**:

1. Wish autorisieren und aktuelle Version prüfen,
2. genau einen zulässigen Plan erzeugen bzw. die Idempotenzentscheidung anwenden,
3. `sourceWishId` setzen,
4. Wish in den beschlossenen Folgezustand überführen,
5. sichere Domain Events schreiben.

Doppelte parallele Bestätigung darf nie zwei Plans erzeugen.

### Proposed Fehlercodes

```text
WISH_NOT_FOUND                  404
WISH_NOT_EDITABLE               403 oder 404 gemäß finaler Ownership-Regel
WISH_STATUS_TRANSITION_INVALID  409
WISH_ALREADY_PLANNED            409 oder idempotenter 200/201 – M3-D02
RESOURCE_VERSION_CONFLICT       409
PLACE_NOT_FOUND                 404
```

Die exakte Idempotenzantwort bleibt offen.

## 5. Plan API

### Proposed Routen

```text
POST   /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans/{planId}
PATCH  /api/v1/spaces/{spaceId}/plans/{planId}
DELETE /api/v1/spaces/{spaceId}/plans/{planId}
```

Direktes `POST /plans` erzeugt einen Plan ohne `sourceWishId` und ist fachlich durch die Produktspezifikation nicht ausgeschlossen.

### Transition-Routen – Proposed

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/schedule
POST /api/v1/spaces/{spaceId}/plans/{planId}/complete
POST /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
```

Warum eigene Operationsrouten vorgeschlagen werden:

- Statuswechsel können Datumsinvarianten erzwingen;
- Completion setzt ggf. `experiencedOn`;
- Return-to-Wish betrifft mindestens zwei Ressourcen;
- Events und Races sind expliziter als bei freiem `PATCH status`.

M3-D03/D04 entscheiden, welche dieser Routen tatsächlich in v1 kommen.

### Proposed Plan DTO

```text
PlanCreateRequest
- title
- description?
- plannedStart?
- plannedEnd?
- placeId?

PlanUpdateRequest
- title?
- description?
- plannedStart?
- plannedEnd?
- placeId?

PlanResponse
- id
- spaceId
- sourceWishId?
- title
- description?
- status
- plannedStart?
- plannedEnd?
- experiencedOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version
- capabilities?
```

Status wird bei normalen Update-Requests bevorzugt nicht frei gesetzt.

## 6. Plan -> Wish Rückführung

### Proposed Route

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
If-Match: "<plan-version>"
```

Die Response hängt von M3-D03 ab. Mögliche Semantiken:

- ursprünglichen `sourceWishId` reaktivieren und Plan erhalten,
- ursprünglichen Wish reaktivieren und Plan löschen,
- neuen Wish erzeugen und Plan als Historie erhalten.

Bis diese Entscheidung `DECIDED` ist, darf keine Route in den OpenAPI-Vertrag übernommen werden.

## 7. Place API

### Proposed Routen

```text
POST   /api/v1/spaces/{spaceId}/places
GET    /api/v1/spaces/{spaceId}/places
GET    /api/v1/spaces/{spaceId}/places/{placeId}
PATCH  /api/v1/spaces/{spaceId}/places/{placeId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}
```

### Proposed DTO

```text
PlaceCreateRequest
- name
- description?
- address?
- latitude?
- longitude?

PlaceResponse
- id
- spaceId
- name
- description?
- address?
- latitude?
- longitude?
- createdBy
- createdAt
- updatedAt
- version
```

M3 liefert **keine** Endpointfamilie wie `/geocode`, `/nearby`, `/map-search` oder Provider-Proxy. Solche Flächen benötigen später eigene Reuse-/Privacy-/Provider-Entscheidungen.

### Validation – proposed

- `latitude` und `longitude` nur zusammen oder explizit einzeln? **M3-D06**
- numerische Werte innerhalb geographischer Grenzen;
- kein Zwang zu Koordinaten;
- `address` ist Nutzerinhalt, kein vom Server validierter Providerdatensatz.

## 8. Content Relations API

Die DB-Seite bleibt typisiert. Für die externe API sind zwei Formen denkbar.

### Option A – typisierte verschachtelte Routen

```text
PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}

PUT    /api/v1/spaces/{spaceId}/places/{placeId}/plans/{planId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/plans/{planId}
```

Vorteile:

- Vertrag und Autorisierung sehr explizit,
- kein unkontrollierter Discriminator,
- einfache OpenAPI-Typen.

Nachteil: mehr Routen.

### Option B – gemeinsamer kontrollierter Relation Service

```text
POST /api/v1/spaces/{spaceId}/relations
```

mit streng enumerierter Union, z. B.:

```text
{ relation: "CHAPTER_MEMORY", chapterId, memoryId }
{ relation: "PLACE_PLAN", placeId, planId }
```

Intern weiterhin eigene FK-Tabellen.

Vorteil: ein gemeinsamer Client-Einstieg.  
Risiko: darf nicht in freie `targetType/targetId`-Polymorphie abrutschen.

**M3-D08 entscheidet A/B bzw. eine begründete Mischform.**

### Relation-Sicherheitsantwort

Wenn Target fremder Space oder `OWNER_ONLY`/nicht lesbar ist:

```text
404 RELATION_TARGET_NOT_FOUND
```

Keine Antwort darf unterscheiden, ob die ID existiert, privat ist oder zu einem anderen Space gehört.

## 9. Chapter API

### Proposed Routen

```text
POST   /api/v1/spaces/{spaceId}/chapters
GET    /api/v1/spaces/{spaceId}/chapters
GET    /api/v1/spaces/{spaceId}/chapters/{chapterId}
PATCH  /api/v1/spaces/{spaceId}/chapters/{chapterId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}
```

### Proposed DTO

```text
ChapterCreateRequest
- title
- description?
- startOn?
- endOn?
- placeId?

ChapterResponse
- id
- spaceId
- title
- description?
- startOn?
- endOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version
- relationSummary?  # nur sichere gemeinsame Counts; M3-D10
```

Ein Relation-Count darf niemals private Targets mitzählen. Der einfachere sichere Start ist, Counts nur über tatsächlich relationierbare shared Targets zu berechnen oder zunächst wegzulassen.

Delete Chapter antwortet 204 und entfernt nur Chapter + seine Relationseinträge. Originalinhalte bleiben erhalten.

## 10. Collection API

### Proposed Routen

```text
POST   /api/v1/spaces/{spaceId}/collections
GET    /api/v1/spaces/{spaceId}/collections
GET    /api/v1/spaces/{spaceId}/collections/{collectionId}
PATCH  /api/v1/spaces/{spaceId}/collections/{collectionId}
DELETE /api/v1/spaces/{spaceId}/collections/{collectionId}

POST   /api/v1/spaces/{spaceId}/collections/{collectionId}/items
PATCH  /api/v1/spaces/{spaceId}/collections/{collectionId}/items/{itemId}
DELETE /api/v1/spaces/{spaceId}/collections/{collectionId}/items/{itemId}
```

### Reorder – Proposed

Keine Folge von N einzelnen `PATCH position`-Requests. Bevorzugt eine atomare Operation:

```text
PUT /api/v1/spaces/{spaceId}/collections/{collectionId}/item-order
If-Match: "<collection-or-order-version>"

{
  "itemIds": ["...", "...", "..."]
}
```

oder ein rank-basiertes Einzelmove-Modell. M3-D14 entscheidet die Strategie.

### Completion

`completed` kann als normale Itemmutation modelliert werden, sofern Item-Versionierung beschlossen wird. Bei parent-basierter Versionierung muss der gesamte Collection-Stand konfliktfrei bleiben.

## 11. Private Area Routing

Alle Routen bleiben space-scoped, obwohl der aktuelle Account implizit Owner ist. Dadurch bleibt Tenant-Isolation sichtbar und ein Account mit mehreren Spaces kann keine private Ressource aus dem falschen Space referenzieren.

### Proposed PrivateNote

```text
POST   /api/v1/spaces/{spaceId}/private/notes
GET    /api/v1/spaces/{spaceId}/private/notes
GET    /api/v1/spaces/{spaceId}/private/notes/{noteId}
PATCH  /api/v1/spaces/{spaceId}/private/notes/{noteId}
DELETE /api/v1/spaces/{spaceId}/private/notes/{noteId}
```

### Proposed GiftIdea

```text
POST   /api/v1/spaces/{spaceId}/private/gift-ideas
GET    /api/v1/spaces/{spaceId}/private/gift-ideas
GET    /api/v1/spaces/{spaceId}/private/gift-ideas/{giftIdeaId}
PATCH  /api/v1/spaces/{spaceId}/private/gift-ideas/{giftIdeaId}
DELETE /api/v1/spaces/{spaceId}/private/gift-ideas/{giftIdeaId}
```

`status` bleibt aus Create/Update fachlich unbestimmt, bis M3-D17 einen Enum festlegt.

### Proposed PrivateCollection

```text
POST   /api/v1/spaces/{spaceId}/private/collections
GET    /api/v1/spaces/{spaceId}/private/collections
GET    /api/v1/spaces/{spaceId}/private/collections/{collectionId}
PATCH  /api/v1/spaces/{spaceId}/private/collections/{collectionId}
DELETE /api/v1/spaces/{spaceId}/private/collections/{collectionId}

POST/PATCH/DELETE .../{collectionId}/items[/...]
PUT .../{collectionId}/item-order
```

### Privacy-Vertrag

Partnerzugriff auf bekannte oder erratene private IDs:

```text
404 PRIVATE_RESOURCE_NOT_FOUND
```

Die gleiche sichere Antwort gilt für:

- unbekannte ID,
- private ID des Partners,
- ID aus anderem Space,
- Ressource nach Löschung.

Kein unterschiedlicher `detail`-Text, Timing-optimierte Existenzprüfung oder Count darf die Fälle auflösbar machen.

## 12. ETag / If-Match

Proposed Standard:

```text
ETag: "<version>"
If-Match: "<version>"
```

Pflicht für:

- Update/Delete veränderbarer Root-Ressourcen,
- Transition-Operationen,
- relationale Reorder-Operationen, sofern sie den Rootzustand verändern.

Für Child-Items muss M3-D14/M3-D18 entscheiden, ob eine eigene Item-Version oder Parent-Version die Konsistenz schützt.

## 13. Fehlercode-Katalog – Proposed

Allgemein:

```text
RESOURCE_VERSION_CONFLICT       409
INVALID_CURSOR                  400
RELATION_TARGET_NOT_FOUND       404
RELATION_ALREADY_EXISTS         409
RELATION_NOT_FOUND              404
RELATION_CROSS_SPACE_FORBIDDEN  404  # nach außen ggf. auf NOT_FOUND vereinheitlichen
STATUS_TRANSITION_INVALID       409
```

Wish:

```text
WISH_NOT_FOUND
WISH_TITLE_REQUIRED
WISH_ALREADY_PLANNED
WISH_STATUS_TRANSITION_INVALID
```

Plan:

```text
PLAN_NOT_FOUND
PLAN_TITLE_REQUIRED
PLAN_STATUS_TRANSITION_INVALID
PLAN_DATE_RANGE_INVALID
PLAN_ALREADY_COMPLETED
```

Place:

```text
PLACE_NOT_FOUND
PLACE_NAME_REQUIRED
PLACE_COORDINATES_INVALID
PLACE_IN_USE                   # nur falls Delete blockiert wird; M3-D05/D26
```

Chapter:

```text
CHAPTER_NOT_FOUND
CHAPTER_TITLE_REQUIRED
CHAPTER_DATE_RANGE_INVALID
```

Collection:

```text
COLLECTION_NOT_FOUND
COLLECTION_ITEM_NOT_FOUND
COLLECTION_TITLE_REQUIRED
COLLECTION_ORDER_INVALID
```

Private:

```text
PRIVATE_RESOURCE_NOT_FOUND
PRIVATE_NOTE_TITLE_REQUIRED
GIFT_IDEA_TITLE_REQUIRED
GIFT_IDEA_STATUS_INVALID
PRIVATE_COLLECTION_NOT_FOUND
PRIVATE_COLLECTION_ITEM_NOT_FOUND
```

Die endgültige Liste wird erst mit OpenAPI/Domain-Decisions verbindlich.

## 14. Delete Semantik

Die API darf `DELETE` nicht zu einem generischen Cascade-Schalter machen. Pro Domain wird vorher entschieden:

- welche eigenen Child-Zeilen gelöscht werden,
- welche externen Relationen nur entfernt werden,
- welche verknüpften Originale erhalten bleiben,
- ob `If-Match` Pflicht ist.

Für Chapter ist source-bound: Delete entfernt Relationen, nicht Originalinhalte.

## 15. Kein serverseitiges Fetching von GiftIdea URLs

`GiftIdea.url` ist im M3-Core ein gespeicherter String. M3 führt **keinen** URL-Preview-, OpenGraph-, Screenshot- oder Metadaten-Fetcher ein.

Grund:

- SSRF-Fläche,
- Tracking-/Privacy-Ausleitung,
- zusätzlicher Provider-/Parser-/Supply-Chain-Scope.

Eine spätere Vorschau braucht ein eigenes Reuse-/Security-Design.

## 16. Keine Maps-/Geocoding-API in M3

`Place` wird nicht mit technischen Endpunkten für Karten oder Suche vermischt. M3 speichert nur die fachlichen Daten, die der Nutzer/Client über den normalen Vertrag liefert. Providerintegration folgt später separat.

## 17. G3-API-Evidenz – noch zu entscheiden

Vor G3 muss feststehen, ob ein reiner Backend-/OpenAPI-/PostgreSQL-Nachweis genügt oder ob – analog zu M2 – ein dünner Web-/Android-Referenzflow verlangt wird. M5 bleibt die vollständige Client-Produktisierung.

Diese Frage ist **M3-D24** und darf nicht erst im Gate-Review auftauchen.
