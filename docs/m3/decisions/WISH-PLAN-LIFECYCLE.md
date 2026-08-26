# M3 Wish-/Plan-Lifecycle – verbindliche Entscheidungen

**Status:** `DECIDED` – wirksam mit Merge dieses Decision-PRs  
**Datum:** 26.08.2026  
**Tracking:** #162  
**Betrifft:** M3-D01, M3-D02, M3-D03, M3-D04, M3-D05, M3-D30

Dieses Dokument schließt die blockierenden M3-Entscheidungen für Wish und Plan. Es enthält ausschließlich Domain-, API-, Persistenz-, Concurrency- und Testentscheidungen. Es gibt **keinen M3-Runtime-Code frei**; die Gate-Regel aus `docs/m3/README.md` bleibt bestehen.

## 1. Verbindliche Quellen

Die Entscheidungen bauen auf folgenden source-bound Grenzen auf:

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/SECURITY.md`
- `docs/m3/README.md`
- `docs/m3/DOMAIN-MODEL.md`
- `docs/m3/API-DESIGN.md`
- `docs/m3/SECURITY-TEST-MATRIX.md`

Source-bound sind insbesondere:

- Wish ist `SPACE_SHARED` mit `OPEN | PLANNED | COMPLETED`.
- Plan ist `SPACE_SHARED` mit `IDEA | PLANNED | COMPLETED`.
- `Plan.sourceWishId` ist optional.
- Wish -> Plan -> Completed -> optional Chapter ist vorgesehen.
- ein nicht abgeschlossener source-bound Plan kann in den Wish-Zustand zurückgeführt werden.
- veränderbare Ressourcen verwenden Version/`If-Match`; Konflikte liefern HTTP 409.
- Cross-Tenant-Zugriffe bleiben privacy-sicher.

## 2. M3-D01 – Shared Write Ownership

### Entscheidung

Für die gemeinsamen M3-Domänen **Wish, Plan, Place, Chapter und Collection** gilt als Grundregel **collaborative write**:

- beide aktiven Mitglieder des Space dürfen gemeinsame Ressourcen erstellen, lesen und – soweit der jeweilige Domainzustand es erlaubt – ändern und löschen;
- `createdBy` dient Attribution/Audit, **nicht** als ACL;
- `createdBy`, `spaceId` und technische Ownership-Felder sind clientseitig nicht überschreibbar;
- domain-spezifische State-, Delete- oder Relation-Regeln können eine konkrete Mutation trotz aktiver Membership blockieren;
- Cross-Space oder fehlende Membership bleibt 404-/Tenant-denied gemäß bestehender Security-Konvention.

Diese Regel ändert **nicht** die author-only-Regeln anderer Domänen wie Memory. Sie gilt nur für die hier benannten kollaborativen M3-Planungs-/Listenressourcen.

### API-Folge

- kein creator-only-403 für Wish/Plan;
- verbotene Lifecycle-Aktionen werden als fachlicher Konflikt (`409`) modelliert, nicht als Berechtigungsfehler;
- Clients dürfen `capabilities` anzeigen, aber die Serverautorisierung bleibt allein verbindlich.

### Audit/Event-Folge

Jede Mutation hält mindestens Actor-ID, Resource-ID, Zeitpunkt, Aktion und Ergebnis fest. Fachliche Titel/Beschreibungen werden nicht in Audit-/Event-Payloads kopiert. Der endgültige M3-Event-Envelope bleibt M3-D23.

## 3. M3-D02 – Wish -> Plan Kardinalität, Atomizität und Idempotenz

### Entscheidung

Ein Wish kann zu einem Zeitpunkt **höchstens einen originären Plan** besitzen.

Persistenz:

- `Plan.sourceWishId` ist nullable;
- wenn gesetzt, referenziert es einen Wish desselben Space;
- `sourceWishId` ist eindeutig;
- ein zurückgeführter Plan wird gelöscht, dadurch kann derselbe Wish später erneut zu einem neuen Plan konvertiert werden.

`Wish.status=PLANNED` darf ausschließlich durch die atomare Wish->Plan-Operation entstehen.

### Operation

```text
POST /api/v1/spaces/{spaceId}/wishes/{wishId}/plan
If-Match: "<wish-version>"
```

Request:

```text
WishToPlanRequest
- title?        # optionaler Plan-Titel; Default = aktueller Wish-Titel
- description?
- placeId?
```

Nicht clientseitig setzbar:

```text
sourceWishId
status
createdBy
spaceId
version
plannedStart
plannedEnd
experiencedOn
```

Erster erfolgreicher Aufruf:

```text
201 Created
WishToPlanResponse
- wish
- plan
```

Ein Retry nach bereits erfolgreicher Konvertierung ist idempotent, solange der Wish noch `PLANNED` ist und der originäre Plan existiert:

```text
200 OK
WishToPlanResponse
- derselbe wish
- derselbe plan
```

Der Retry erzeugt **niemals** einen zweiten Plan.

Wenn der Wish bereits `COMPLETED` ist, ist eine erneute Konvertierung kein Retry mehr und liefert einen fachlichen Konflikt.

### Transaktionsablauf

In einer PostgreSQL-Transaktion:

1. aktive Membership prüfen;
2. Wish space-scoped laden und `FOR UPDATE` sperren;
3. existierenden originären Plan prüfen;
4. bei `PLANNED` + vorhandenem Plan idempotent denselben Plan zurückgeben;
5. bei `OPEN` `If-Match` prüfen;
6. optionales `placeId` same-space/autorisierbar prüfen;
7. Plan mit `sourceWishId=wish.id`, Status `IDEA` und eigener Version erzeugen;
8. Wish auf `PLANNED` setzen und Version erhöhen;
9. sichere Outbox-/Audit-Metadaten schreiben;
10. genau einmal committen.

Rollback an jeder Stelle hinterlässt weder Plan noch halbe Wish-Transition.

### Race-Vertrag

Zwei parallele Convert-Requests auf denselben OPEN-Wish ergeben deterministisch:

- genau einen Plan in der Datenbank;
- ein Request erzeugt den Plan;
- der zweite wartet auf den Wish-Lock und erhält anschließend denselben originären Plan als idempotente Antwort;
- DB-Unique ist zusätzliche letzte Integritätsgrenze.

### DB-Constraints

Mindestens:

- FK `plans.source_wish_id -> wishes.id`;
- Same-Space-Enforcement für `(source_wish_id, space_id)` über passende zusammengesetzte Integritätsgrenze oder äquivalent belastbare DB-/Service-Absicherung;
- `UNIQUE(source_wish_id)`; PostgreSQL erlaubt dabei mehrere `NULL` für Direct Plans;
- kein clientseitiges Setzen von `sourceWishId`.

## 4. M3-D03 – Plan -> Wish Rückführung

### Entscheidung

`return-to-wish` ist nur für **nicht abgeschlossene originäre Plans** erlaubt:

- `sourceWishId != null`;
- Plan-Status `IDEA` oder `PLANNED`;
- source Wish ist `PLANNED`.

Ein Direct Plan ohne `sourceWishId` kann nicht „zurück“ in einen Wish geführt werden. Dafür müsste der Nutzer explizit einen neuen Wish erstellen.

### Semantik

Die Rückführung:

1. reaktiviert **denselben ursprünglichen Wish** mit Status `OPEN`;
2. löscht den nicht abgeschlossenen Plan;
3. entfernt ausschließlich Plan-eigene Relation-/Join-Zeilen;
4. löscht niemals Place, Chapter oder andere fachliche Originalressourcen;
5. kopiert **keinen** Plan-Titel, keine Beschreibung und keine Plan-Termine automatisch in den Wish zurück.

Damit gibt es keine stille Überschreibung divergierter ProtectedPayloads. Plan-spezifische Daten werden bei der ausdrücklich gewählten Rückführung verworfen; die UI muss diese destruktive Folge vor Bestätigung verständlich machen.

### Operation

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
If-Match: "<plan-version>"
```

Response:

```text
200 OK
PlanReturnToWishResponse
- wish
- removedPlanId
```

Der Plan ist danach unter seiner ID nicht mehr lesbar.

### Locking

Wenn Wish und Plan gemeinsam betroffen sind, gilt die kanonische Lock-Reihenfolge:

```text
Wish -> Plan
```

Ein Plan-Service darf die Plan-ID zunächst ohne Lock auflösen, muss anschließend den source Wish sperren und danach den Plan unter derselben Transaktion erneut sperren/revalidieren. Diese Reihenfolge gilt auch für Completion und source-bound Deletes, damit Return/Complete/Delete nicht gegeneinander deadlocken.

## 5. M3-D04 – Plan Lifecycle und Datumsinvarianten

### Verbindlicher Statusautomat

```text
            schedule
IDEA --------------------> PLANNED
  |                           |
  | complete                  | complete
  v                           v
COMPLETED <---------------- COMPLETED

PLANNED -- unschedule --> IDEA
```

Erlaubt:

- `IDEA -> PLANNED`
- `PLANNED -> IDEA`
- `IDEA -> COMPLETED`
- `PLANNED -> COMPLETED`

Verboten:

- jede Transition aus `COMPLETED` in einen anderen Status;
- freies Setzen von `status` über normales `PATCH`;
- `IDEA -> IDEA` oder `PLANNED -> PLANNED` als Statusoperation; normale Inhalts-/Terminänderungen bleiben separate Updates.

`return-to-wish` ist **keine Plan-Statuskante**, sondern eine eigene Domainoperation nach M3-D03, die den Plan entfernt und den Wish reaktiviert.

### Zeitsemantik

Für den Runtime-Slice gilt:

- `plannedStart`: `TIMESTAMPTZ`, optional;
- `plannedEnd`: `TIMESTAMPTZ`, optional;
- `experiencedOn`: `DATE`, optional außerhalb COMPLETED, verpflichtend bei COMPLETED.

Invarianten:

- `plannedEnd` darf nur gesetzt sein, wenn `plannedStart` gesetzt ist;
- wenn beide gesetzt sind: `plannedEnd >= plannedStart`;
- `IDEA` besitzt keinen verbindlichen Termin: `plannedStart = null`, `plannedEnd = null`;
- `PLANNED` verlangt `plannedStart`; `plannedEnd` bleibt optional;
- `COMPLETED` verlangt `experiencedOn`;
- `experiencedOn` darf nicht in der Zukunft relativ zum lokalen Kalendertag des handelnden Accounts liegen;
- Completion aus `PLANNED` erhält die geplanten Zeiten als Historie;
- Completion aus `IDEA` ist für spontan Erlebtes erlaubt und benötigt keine geplanten Zeiten.

### Lifecycle-Operationen

```text
POST /api/v1/spaces/{spaceId}/plans/{planId}/schedule
POST /api/v1/spaces/{spaceId}/plans/{planId}/unschedule
POST /api/v1/spaces/{spaceId}/plans/{planId}/complete
```

Alle benötigen `If-Match`.

`schedule`:

```text
- plannedStart   # Pflicht
- plannedEnd?    # optional
```

`unschedule` setzt Status `IDEA` und löscht `plannedStart/plannedEnd`.

`complete`:

```text
- experiencedOn # Pflicht
```

Bei einem source-bound Plan setzt Completion in derselben Transaktion zusätzlich den ursprünglichen Wish von `PLANNED` auf `COMPLETED` und erhöht dessen Version. Bei einem Direct Plan wird kein Wish erzeugt oder verändert.

### Normales PATCH

`PATCH Plan` darf kein `status` setzen. Es darf fachliche Nicht-Lifecycle-Felder ändern, insbesondere `title`, `description` und `placeId`, sofern die übrigen Invarianten eingehalten werden.

Terminänderungen eines bereits `PLANNED`en Plans dürfen über eine erneute Schedule-/Reschedule-Operation mit `If-Match` erfolgen. `experiencedOn` wird durch Completion gesetzt; eine spätere Korrektur eines Completed-Datums darf als versioniertes fachliches Update zugelassen werden, solange es nicht in der Zukunft liegt.

## 6. M3-D05 – Delete-Semantik

### Grundregel

Delete entfernt nur das gewählte Aggregate bzw. seine eigenen Join-/Child-Zeilen. Keine Operation löscht Place, Chapter, Memory oder andere fachliche Originalressourcen als Nebenwirkung.

### Wish-Matrix

| Wish-Zustand | Originärer Plan | DELETE Wish |
|---|---|---|
| `OPEN` | nein | erlaubt, `204` |
| `OPEN` | ja | inkonsistenter Zustand -> `409` / keine Mutation |
| `PLANNED` | ja | blockiert; aktiven Plan verwenden bzw. `return-to-wish` |
| `PLANNED` | nein | Integritätsverletzung -> `409` / keine Mutation |
| `COMPLETED` | ja | blockiert, solange der originäre Plan existiert |
| `COMPLETED` | nein | erlaubt, `204` |

Damit kann ein completed Lifecycle vollständig entfernt werden, indem zuerst der completed Plan und anschließend der verbleibende completed Wish explizit gelöscht werden. Es gibt keine versteckte Cascade Wish -> Plan.

### Plan-Matrix

| Plan-Typ/Status | DELETE Plan |
|---|---|
| Direct Plan (`sourceWishId=null`), `IDEA` | erlaubt |
| Direct Plan, `PLANNED` | erlaubt |
| Direct Plan, `COMPLETED` | erlaubt |
| Source Plan, `IDEA` | blockiert; `return-to-wish` verwenden |
| Source Plan, `PLANNED` | blockiert; `return-to-wish` verwenden |
| Source Plan, `COMPLETED` | erlaubt; source Wish bleibt `COMPLETED` |

Beim Löschen eines Plans:

- Plan-Relation-/Join-Zeilen werden entfernt;
- referenzierte Places/Chapters/sonstige Originale bleiben bestehen;
- ein completed source Wish bleibt bestehen und kann anschließend separat gelöscht werden.

### Concurrency

- `DELETE Wish`, `DELETE Plan`, Convert, Return und Complete sind versioniert und verwenden `If-Match`;
- sobald Wish + source Plan gemeinsam betroffen sind, gilt Lock-Reihenfolge `Wish -> Plan`;
- Delete vs Convert/Complete/Return wird durch Locks + FK/Unique + Revalidation deterministisch entschieden;
- stale Mutation -> `409 RESOURCE_VERSION_CONFLICT`;
- kein Race darf einen `PLANNED` Wish ohne originären Plan oder einen zweiten originären Plan hinterlassen.

## 7. M3-D30 – Direct Plan Create

### Entscheidung

Ein Plan darf ohne Wish entstehen, weil `sourceWishId` source-bound optional ist.

Direct Create erzeugt **immer** einen Plan mit:

```text
sourceWishId = null
status       = IDEA
plannedStart = null
plannedEnd   = null
experiencedOn = null
```

Request:

```text
PlanCreateRequest
- title        # Pflicht
- description?
- placeId?
```

Nicht erlaubt im Create-Request:

```text
sourceWishId
status
plannedStart
plannedEnd
experiencedOn
createdBy
spaceId
version
```

Ein Direct Plan wird erst über `/schedule` terminiert oder über `/complete` spontan abgeschlossen.

## 8. API-Vertrag – verbindliche Operationsform

Wish:

```text
POST   /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes
GET    /api/v1/spaces/{spaceId}/wishes/{wishId}
PATCH  /api/v1/spaces/{spaceId}/wishes/{wishId}
DELETE /api/v1/spaces/{spaceId}/wishes/{wishId}
POST   /api/v1/spaces/{spaceId}/wishes/{wishId}/plan
```

Plan:

```text
POST   /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans
GET    /api/v1/spaces/{spaceId}/plans/{planId}
PATCH  /api/v1/spaces/{spaceId}/plans/{planId}
DELETE /api/v1/spaces/{spaceId}/plans/{planId}
POST   /api/v1/spaces/{spaceId}/plans/{planId}/schedule
POST   /api/v1/spaces/{spaceId}/plans/{planId}/unschedule
POST   /api/v1/spaces/{spaceId}/plans/{planId}/complete
POST   /api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish
```

Statusfelder sind bei normalen PATCH-Requests read-only.

## 9. Stabile Fehlercodes

Mindestens:

```text
WISH_NOT_FOUND                    404
PLAN_NOT_FOUND                    404
PLACE_NOT_FOUND                   404
RESOURCE_VERSION_CONFLICT         409
WISH_STATUS_TRANSITION_INVALID    409
WISH_ALREADY_COMPLETED            409
WISH_HAS_ACTIVE_PLAN              409
WISH_HAS_COMPLETED_PLAN           409
WISH_PLAN_STATE_CONFLICT          409
PLAN_STATUS_TRANSITION_INVALID    409
PLAN_SOURCE_WISH_REQUIRED         409
PLAN_HAS_SOURCE_WISH              409
PLAN_SCHEDULE_START_REQUIRED      422
PLAN_DATE_RANGE_INVALID           422
PLAN_EXPERIENCED_ON_REQUIRED      422
PLAN_EXPERIENCED_ON_IN_FUTURE     422
```

Nicht lesbare/fremde Ressourcen bleiben privacy-sicher 404. Ein separater Cross-Space-Fehlercode wird nicht eingeführt.

## 10. Verpflichtende PostgreSQL-/HTTP-Tests

### Shared Writes / Tenant

- beide aktiven Partner können Wish/Plan gemäß Domainzustand ändern/löschen;
- `createdBy` bleibt unveränderlich;
- Account ohne Membership / ID aus anderem Space -> keine Datenänderung, privacy-sicherer Fehler;
- stale `If-Match` -> 409.

### Wish -> Plan

- OPEN Wish -> 201 + genau ein Plan + Wish PLANNED;
- Plan startet IDEA;
- identischer Retry bei PLANNED -> 200 mit derselben Plan-ID;
- zwei parallele Convert-Requests -> exakt ein Plan;
- Fehler zwischen Plan-Insert und Wish-Update -> vollständiger Rollback;
- stale OPEN-Wish -> 409 und kein Plan;
- COMPLETED Wish -> 409;
- fremdes `placeId` -> 404 und kein Plan.

### Lifecycle

Für jede erlaubte Kante Happy Path + stale Version testen.

Explizite Negativtests:

- `COMPLETED -> IDEA` verboten;
- `COMPLETED -> PLANNED` verboten;
- PLANNED ohne `plannedStart` verboten;
- `plannedEnd < plannedStart` verboten;
- zukünftiges `experiencedOn` verboten;
- Completion aus IDEA erlaubt;
- Completion aus PLANNED erlaubt und erhält Plantermine.

### Source Wish Completion

- source Plan Complete -> Plan COMPLETED + Wish COMPLETED in einem Commit;
- Fehler nach einer der beiden Mutationen -> kompletter Rollback;
- paralleles Complete/Return/Delete -> deterministisches Ergebnis ohne halben Lifecycle.

### Return-to-Wish

- source IDEA/PLANNED -> Wish OPEN + Plan gelöscht;
- Direct Plan -> 409;
- COMPLETED source Plan -> 409;
- Plan-Payload wird nicht automatisch in Wish zurückkopiert;
- Plan-Join-Zeilen verschwinden, Originaltargets bleiben bestehen.

### Delete

Jede Zeile der Wish-/Plan-Delete-Matrix erhält einen HTTP- und PostgreSQL-Test. Zusätzlich:

- Delete vs Convert;
- Delete vs Complete;
- Delete vs Return;
- keine Originalresource-Cascade;
- nach Delete completed source Plan bleibt Wish COMPLETED und separat löschbar.

## 11. Privacy-/Telemetry-Folge

Wish- und Plan-Titel/Beschreibungen gehören nicht in Logs, Analytics, Error Context oder Domain-Event-Payloads. Zulässig sind technische IDs, Actor, Space, Version, Eventtyp und sichere Statuswerte gemäß später finalisiertem M3-D23.

## 12. Folge für M3-S1/S2

Nach bestandenem G2 und Status-Sync #146 dürfen Wish-/Plan-Runtime-Slices auf diesen Vertrag bauen. Dabei bleiben weiterhin außerhalb dieses Decision-Scopes:

- Place-Feldklassifizierung und Relationdetails (#163),
- Collections/Private Area (#164),
- G3-/Client-/Export-/Cache-Grenzen (#165),
- globale Suche,
- Plan-Checklist/Attachments,
- vollständige Web-/Android-Produktisierung.
