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
- fehlende Membership, fremder Space oder fremde Resource-ID bleibt privacy-sicher gemäß bestehender Tenant-Konvention.

Diese Regel ändert **nicht** author-only-Regeln anderer Domänen wie Memory. Sie gilt nur für die benannten kollaborativen M3-Planungs-/Listenressourcen.

### Wish/Plan konkret

- beide Partner dürfen den Wish-Titel ändern, unabhängig davon, wer den Wish erstellt hat;
- beide Partner dürfen Plan-Titel, Beschreibung und Place-Zuordnung ändern;
- Statusfelder werden niemals über normales PATCH gesetzt;
- Wish und Plan bleiben nach der Konvertierung getrennte Domainobjekte: eine Änderung am Wish-Titel synchronisiert den Plan-Titel nicht automatisch und umgekehrt;
- `createdBy` bleibt unverändert.

### API-/Audit-Folge

- kein creator-only-403 für Wish/Plan;
- verbotene Lifecycle-Aktionen sind fachliche Konflikte (`409`), keine Berechtigungsfehler;
- Clients dürfen `capabilities` anzeigen, aber nur der Server entscheidet über die Mutation;
- Audit/Event hält Actor-ID, Resource-ID, Zeitpunkt, Aktion und Ergebnis fest, aber keine fachlichen Titel/Beschreibungen.

## 3. Wish-Lifecycle – verbindliche Ableitung aus D02/D03/D04

Wish besitzt exakt diesen Statusautomaten:

```text
OPEN
  | convert-to-plan
  v
PLANNED
  | plan complete
  v
COMPLETED

PLANNED -- return-to-wish --> OPEN
```

Verbindlich:

- `OPEN -> PLANNED` ausschließlich durch die atomare Wish->Plan-Operation;
- `PLANNED -> OPEN` ausschließlich durch `return-to-wish` des originären Plans;
- `PLANNED -> COMPLETED` ausschließlich durch Completion des originären Plans;
- `COMPLETED` ist für den Statusautomaten terminal;
- es gibt keine direkte Wish-Complete-Route;
- es gibt keinen freien Wish-Status-PATCH;
- normale Titelkorrekturen bleiben versionierte Inhaltsupdates und verändern den Status nicht.

## 4. M3-D02 – Wish -> Plan Kardinalität, Atomizität und Idempotenz

### Entscheidung

Ein Wish kann zu einem Zeitpunkt **höchstens einen originären Plan** besitzen.

Persistenz:

- `Plan.sourceWishId` ist nullable;
- wenn gesetzt, referenziert es einen Wish desselben Space;
- `sourceWishId` ist eindeutig;
- ein zurückgeführter Plan wird gelöscht, dadurch kann derselbe Wish später erneut zu einem neuen Plan konvertiert werden.

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

Die Operation erzeugt:

```text
Wish.status      = PLANNED
Plan.status      = IDEA
Plan.sourceWishId = Wish.id
```

### Idempotenter Retry

Wenn der Wish bereits `PLANNED` ist und genau der originäre Plan existiert, liefert ein erneuter Convert-Aufruf denselben Plan:

```text
200 OK
WishToPlanResponse
- derselbe wish
- derselbe plan
```

Der Retry erzeugt **niemals** einen zweiten Plan. Ein abweichender Request überschreibt dabei den bereits existierenden Plan nicht; weitere Änderungen erfolgen über den Plan selbst.

Wenn der Wish bereits `COMPLETED` ist, ist eine erneute Konvertierung kein Retry und liefert einen fachlichen Konflikt.

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
- der zweite wartet auf den Wish-Lock und erhält danach denselben originären Plan als idempotente Antwort;
- DB-Unique ist die letzte Integritätsgrenze.

## 5. M3-D03 – Plan -> Wish Rückführung

### Entscheidung

`return-to-wish` ist nur für **nicht abgeschlossene originäre Plans** erlaubt:

- `sourceWishId != null`;
- Plan-Status `IDEA` oder `PLANNED`;
- source Wish ist `PLANNED`.

Ein Direct Plan ohne `sourceWishId` kann nicht „zurück“ in einen Wish geführt werden. Dafür muss der Nutzer explizit einen neuen Wish erstellen.

### Semantik

Die Rückführung:

1. reaktiviert **denselben ursprünglichen Wish** mit Status `OPEN`;
2. erhöht die Wish-Version;
3. löscht den nicht abgeschlossenen Plan;
4. entfernt ausschließlich Plan-eigene Relation-/Join-Zeilen;
5. löscht niemals Place, Chapter oder andere fachliche Originalressourcen;
6. kopiert **keinen** Plan-Titel, keine Beschreibung und keine Plan-Termine automatisch in den Wish zurück.

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

## 6. M3-D04 – Plan Lifecycle und Datumsinvarianten

### Verbindlicher Statusautomat

```text
IDEA -- schedule --> PLANNED
IDEA -- complete --> COMPLETED
PLANNED -- unschedule --> IDEA
PLANNED -- complete --> COMPLETED
```

Erlaubt:

- `IDEA -> PLANNED`
- `PLANNED -> IDEA`
- `IDEA -> COMPLETED`
- `PLANNED -> COMPLETED`

Verboten:

- jede Transition aus `COMPLETED` in einen anderen Status;
- freies Setzen von `status` über normales `PATCH`;
- Status-Self-Transitions als eigene Operation.

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

- auf `IDEA`: Status wird `PLANNED`;
- auf `PLANNED`: Termin wird versioniert aktualisiert, Status bleibt `PLANNED`.

`unschedule`:

- nur auf `PLANNED`;
- setzt Status `IDEA`;
- löscht `plannedStart/plannedEnd`.

`complete`:

```text
- experiencedOn # Pflicht
```

Bei einem source-bound Plan setzt Completion in derselben Transaktion zusätzlich den ursprünglichen Wish von `PLANNED` auf `COMPLETED` und erhöht dessen Version. Bei einem Direct Plan wird kein Wish erzeugt oder verändert.

### Normales PATCH

`PATCH Plan` darf kein `status` setzen. Es darf fachliche Nicht-Lifecycle-Felder ändern, insbesondere:

- `title`
- `description`
- `placeId`

Auch ein `COMPLETED` Plan darf für fachliche Korrekturen versioniert bearbeitet werden; daraus entsteht **keine** Status-Rücköffnung. `experiencedOn` darf bei einem Completed Plan versioniert korrigiert werden, solange das Datum nicht in der Zukunft liegt.

## 7. M3-D05 – Delete-Semantik

### Grundregel

Delete entfernt nur das gewählte Aggregate bzw. seine eigenen Join-/Child-Zeilen. Keine Operation löscht Place, Chapter, Memory oder andere fachliche Originalressourcen als Nebenwirkung.

### Wish-Matrix

| Wish-Zustand | Originärer Plan | DELETE Wish |
|---|---|---|
| `OPEN` | nein | erlaubt, `204` |
| `OPEN` | ja | inkonsistenter Zustand -> `409`, keine Mutation |
| `PLANNED` | ja | blockiert; aktiven Plan verwenden bzw. `return-to-wish` |
| `PLANNED` | nein | Integritätsverletzung -> `409`, keine Mutation |
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

## 8. M3-D30 – Direct Plan Create

### Entscheidung

Ein Plan darf ohne Wish entstehen, weil `sourceWishId` source-bound optional ist.

Direct Create erzeugt **immer** einen Plan mit:

```text
sourceWishId   = null
status         = IDEA
plannedStart   = null
plannedEnd     = null
experiencedOn  = null
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

## 9. API-Vertrag – verbindliche Operationsform

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

## 10. Stabile Fehlercodes

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

## 11. DB-Constraints und Locking

Mindestens:

- FK `plans.source_wish_id -> wishes.id`;
- Same-Space-Enforcement für `(source_wish_id, space_id)` über eine zusammengesetzte Integritätsgrenze oder äquivalent belastbare DB-Absicherung;
- `UNIQUE(source_wish_id)`; PostgreSQL erlaubt mehrere `NULL` für Direct Plans;
- Check: `plannedEnd IS NULL OR plannedStart IS NOT NULL`;
- Check: `plannedEnd IS NULL OR plannedEnd >= plannedStart`;
- Status-/Datumsinvarianten zusätzlich im Domainservice und – soweit sinnvoll – als DB-Checks.

Wenn Wish und source Plan gemeinsam betroffen sind, gilt die kanonische Lock-Reihenfolge:

```text
Wish -> Plan
```

Ein Plan-Service darf die Plan-ID zunächst ohne Lock auflösen, muss anschließend den source Wish sperren und danach den Plan in derselben Transaktion erneut sperren/revalidieren. Diese Reihenfolge gilt für Completion, Return und source-bound Delete-Prüfungen.

Concurrency-Grundsätze:

- `DELETE Wish`, `DELETE Plan`, Convert, Return, Schedule, Unschedule und Complete verwenden `If-Match`;
- stale Mutation -> `409 RESOURCE_VERSION_CONFLICT`;
- Delete vs Convert/Complete/Return wird durch Locks + FK/Unique + Revalidation deterministisch entschieden;
- kein Race darf einen `PLANNED` Wish ohne originären Plan oder einen zweiten originären Plan hinterlassen.

## 12. Verpflichtende PostgreSQL-/HTTP-Tests

### Shared Writes / Tenant

- beide aktiven Partner können Wish/Plan gemäß Domainzustand ändern/löschen;
- `createdBy` bleibt unveränderlich;
- Wish- und Plan-Titel dürfen unabhängig voneinander geändert werden;
- Account ohne Membership / ID aus anderem Space -> keine Datenänderung, privacy-sicherer Fehler;
- stale `If-Match` -> 409.

### Wish Lifecycle

- Create -> `OPEN`;
- kein freier Status-PATCH;
- OPEN -> PLANNED nur durch Convert;
- PLANNED -> OPEN nur durch Return;
- PLANNED -> COMPLETED nur durch source Plan Completion;
- COMPLETED besitzt keine Status-Rückkante.

### Wish -> Plan

- OPEN Wish -> 201 + genau ein Plan + Wish PLANNED;
- Plan startet IDEA;
- identischer Retry bei PLANNED -> 200 mit derselben Plan-ID;
- abweichender Retry überschreibt existierenden Plan nicht;
- zwei parallele Convert-Requests -> exakt ein Plan;
- Fehler zwischen Plan-Insert und Wish-Update -> vollständiger Rollback;
- stale OPEN-Wish -> 409 und kein Plan;
- COMPLETED Wish -> 409;
- fremdes `placeId` -> 404 und kein Plan.

### Plan Lifecycle

Für jede erlaubte Kante Happy Path + stale Version testen.

Explizite Negativtests:

- `COMPLETED -> IDEA` verboten;
- `COMPLETED -> PLANNED` verboten;
- PLANNED ohne `plannedStart` verboten;
- `plannedEnd < plannedStart` verboten;
- zukünftiges `experiencedOn` verboten;
- Completion aus IDEA erlaubt;
- Completion aus PLANNED erlaubt und erhält Plantermine;
- Reschedule PLANNED -> PLANNED ändert nur Termine + Version;
- Unschedule löscht geplante Termine.

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

## 13. Privacy-/Telemetry-Folge

Wish- und Plan-Titel/Beschreibungen gehören nicht in Logs, Analytics, Error Context oder Domain-Event-Payloads. Zulässig sind technische IDs, Actor, Space, Version, Eventtyp und sichere Statuswerte gemäß später finalisiertem M3-D23.

## 14. Folge für M3-S1/S2

Nach der im Repository definierten M3-Runtime-Freigabe dürfen Wish-/Plan-Runtime-Slices auf diesen Vertrag bauen. Weiterhin außerhalb dieses Decision-Scopes bleiben:

- Place-Feldklassifizierung und Relationdetails (#163),
- Collections/Private Area (#164),
- G3-/Client-/Export-/Cache-Grenzen (#165),
- globale Suche,
- Plan-Checklist/Attachments,
- vollständige Web-/Android-Produktisierung.
