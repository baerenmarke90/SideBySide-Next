# M3 Decision Log

**Stand:** 26.08.2026  
**Regel:** Eine offene M3-Frage wird nicht stillschweigend im Runtime-Code entschieden.

## Status

- `OPEN` – Entscheidung fehlt.
- `PROPOSED` – bevorzugte Option ist dokumentiert, aber nicht bindend.
- `DECIDED` – durch Source oder explizite Projektentscheidung bindend.

## Priorität

- `BLOCKING` – vor dem ersten betroffenen Runtime-Slice entscheiden.
- `BEFORE_CLIENTS` – vor stabiler Web-/Android-Integration entscheiden.
- `BEFORE_GATE` – vor dem finalen G3-Nachweis entscheiden.
- `LATER` – bewusst außerhalb M3 verschiebbar, solange M3 nicht davon abhängt.

## Decision-Matrix

| ID | Priorität | Status | Thema | Frage / Grenze | Vorschlag / Quelle |
|---|---|---|---|---|---|
| M3-D01 | BLOCKING | DECIDED | Shared Writes | Wer darf Wish, Plan, Place, Chapter und gemeinsame Collection ändern/löschen? | Collaborative write für beide aktiven Space-Mitglieder; `createdBy` ist Attribution, keine ACL. Domainzustände dürfen Aktionen zusätzlich begrenzen. Entscheidung #162. |
| M3-D02 | BLOCKING | DECIDED | Wish -> Plan | Ist `sourceWishId` 1:1, wie werden Double-Submit/Races/idempotente Retries behandelt? | Höchstens ein originärer Plan je Wish; Wish-Row-Lock + `UNIQUE(sourceWishId)`; Retry auf PLANNED liefert denselben Plan. Entscheidung #162. |
| M3-D03 | BLOCKING | DECIDED | Plan -> Wish | Was bedeutet die erlaubte Rückführung eines nicht abgeschlossenen Plans? | Nur source-bound IDEA/PLANNED: denselben Wish auf OPEN reaktivieren, Plan löschen, keine Payload zurückkopieren. Entscheidung #162. |
| M3-D04 | BLOCKING | DECIDED | Plan Lifecycle | Welche Statusübergänge und Datumsinvarianten gelten exakt? | IDEA->PLANNED, PLANNED->IDEA, IDEA/PLANNED->COMPLETED; COMPLETED terminal; Schedule/Complete als Operationsrouten. Entscheidung #162. |
| M3-D05 | BLOCKING | DECIDED | Delete | Was geschieht bei Wish-/Plan-Delete mit `sourceWishId` und Relationen? | State-basierte Delete-Matrix; keine Cascade auf fachliche Originale; nicht abgeschlossene source Plans nur via return-to-wish entfernen. Entscheidung #162. |
| M3-D06 | BLOCKING | OPEN | Place Privacy | Wie werden Adresse/Beschreibung/Koordinaten in ProtectedPayload und API klassifiziert? | Präzise Location niemals Logs/Analytics/Events; Storage-Klassifizierung festlegen. |
| M3-D07 | BLOCKING | PROPOSED | Place Identity | Werden Places implizit dedupliziert/zusammengeführt? | Nein: keine automatische Zusammenführung anhand Name/Adresse/Koordinaten. |
| M3-D08 | BLOCKING | OPEN | Relation Contract | Welche Relationstypen liefert M3 und wie sieht die externe API aus? | DB immer typisierte FK-Tabellen; API Option A typisierte Routen oder kontrollierte Union. |
| M3-D09 | BLOCKING | PROPOSED | Relation Privacy | Dürfen Shared Chapter/Place auf OWNER_ONLY Targets zeigen? | Nein; nicht lesbares/private Target -> privacy-sicher 404, keine Relation/Count. |
| M3-D10 | BLOCKING | OPEN | Chapter Ordering | Sind Chapter-Inhalte chronologisch abgeleitet oder manuell positionierbar? | Nicht aus UI-Wunsch ableiten; DB-Modell vor Relationstabellen entscheiden. |
| M3-D11 | BLOCKING | OPEN | Chapter Dates | Welche Regeln gelten für `startOn`/`endOn` und leere Grenzen? | PROPOSED: beide optional, falls beide gesetzt `endOn >= startOn`. |
| M3-D12 | BLOCKING | DECIDED | Chapter Delete | Löscht Chapter seine Originalinhalte? | **Nein.** Master Spec: Relationen entfernen, Originale erhalten. |
| M3-D13 | BLOCKING | OPEN | Collection Ownership | Hat Collection `createdBy`; wer darf Collection/Items ändern/löschen? | M3-D01 setzt collaborative write als Grundregel; konkrete Root-/Item-Persistenz und Delete-Grenzen bleiben hier zu entscheiden. |
| M3-D14 | BLOCKING | OPEN | Collection Concurrency | Wie werden Item-Version, Completion, Position und Reorder konfliktfrei? | PROPOSED: atomarer Reorder, keine N unabhängigen Positions-Patches. |
| M3-D15 | BLOCKING | OPEN | Collection Delete | Löscht Collection ihre Items, und welche Relationen existieren? | PROPOSED: Items sind Parent-Children und werden mit Parent gelöscht; keine externen Originale. |
| M3-D16 | BLOCKING | PROPOSED | Private Payload | Welche Private-Area-Felder liegen in ProtectedPayload? | PrivateNote title/body; GiftIdea inhaltliche Felder; private Collection-Titel/Items. |
| M3-D17 | BLOCKING | OPEN | GiftIdea | Welche Werte besitzt `GiftIdea.status`? | Quelle nennt Feld, aber keinen Enum – vor Modell/OpenAPI entscheiden. |
| M3-D18 | BLOCKING | OPEN | Private Collection | Welche IDs/Timestamps/Versionen besitzen PrivateCollectionItem und Parent? | Globale Versionierungsregel mit knapper Master-Feldliste versöhnen. |
| M3-D19 | BLOCKING | PROPOSED | Private API | Welche Route-/Pagination-Konvention besitzt die Private Area? | Space-scoped `/private/...`; Owner wird aus Auth Context abgeleitet. |
| M3-D20 | LATER | DECIDED | Search | Muss M3 globale Volltextsuche liefern? | Nein. Roadmap legt globale Suche in M4-A; M3-Listen dürfen einfache Filter haben. |
| M3-D21 | BEFORE_CLIENTS | OPEN | Export | Wie erscheinen private M3-Daten in persönlichem/gemeinsamem Export? | Mit M2-D17/M5 gemeinsam entscheiden; Partnerexport darf Private nie enthalten. |
| M3-D22 | BEFORE_CLIENTS | OPEN | Client Cache | Welche Retention/Clear-Regeln gelten für Private Area auf Web/Android? | Mit M2-D18/M5 entscheiden; Logout/Space-Wechsel müssen private Caches isolieren/löschen. |
| M3-D23 | BLOCKING | PROPOSED | Events | Welches minimale Event-Envelope gilt für M3? | IDs, sichere States, Version; keine Titel, URLs, Adressen, Koordinaten oder Private-Inhalte. |
| M3-D24 | BEFORE_GATE | OPEN | G3 Evidence | Welche Client-/E2E-Evidenz ist für G3 nötig, ohne M5 vorzuziehen? | Vor Runtime-Ende explizit festlegen; nicht erst im Gate-Review entdecken. |
| M3-D25 | BEFORE_CLIENTS | OPEN | Private IA | Wo liegt Private Area in Navigation/Routen, ohne Privacy als Hauptnavigation zu behandeln? | Bestehende IA respektieren; eigener sekundärer Bereich unter `more` oder anderer klarer Ort prüfen. |
| M3-D26 | BLOCKING | OPEN | Relation Races | Wie werden Link/Create gegen Delete oder Privacy-Wechsel serialisiert? | Constraints + Row Locks/transactionale Re-Checks; kein check-then-insert ohne Schutz. |
| M3-D27 | LATER | OPEN | Plan Richness | Gehören Checkliste/Medien/Notizen aus IA bereits zu M3 Plan? | Höhere Product/Master Spec nennt keine Plan-Checklist/Attachments. Nicht implementieren ohne Scope-Decision. |
| M3-D28 | BLOCKING | OPEN | Location Leakage | Welche Genauigkeit/Retention/Redaction gilt für Koordinaten? | Keine Telemetrie/Events; Datenklassifizierung vor Schema entscheiden. |
| M3-D29 | BEFORE_CLIENTS | OPEN | Collection Multi-select | Bedeutet „Mehrfachauswahl“ Domainzustand oder nur UI-Batchauswahl? | PROPOSED: UI-Interaktion, solange keine persistente Semantik spezifiziert ist. |
| M3-D30 | BLOCKING | DECIDED | Direct Plan Create | Darf ein Plan ohne Wish entstehen und mit welchem Startstatus? | Ja; Direct Plan startet immer als IDEA ohne Plantermine/experiencedOn. Scheduling/Completion erfolgen über Operationsrouten. Entscheidung #162. |
| M3-D31 | BLOCKING | OPEN | Chapter/Place Relation | Ist `Chapter.placeId` kanonisch oder zusätzlich `place_chapters`? | Doppelte Wahrheitsquelle vermeiden; genau ein Persistenzmodell entscheiden. |
| M3-D32 | BLOCKING | OPEN | Private Item Auth | Tragen PrivateCollectionItems eigenen owner/space oder erben sie ausschließlich über Parent? | Beide Varianten müssen dieselbe zentrale owner-only Query-Grenze garantieren. |

## Source-bound Entscheidungen

### M3-D12 – Chapter Delete

**Status:** DECIDED  
**Quelle:** Clean-Room Master Specification / Product Spec  
**Entscheidung:** Beim Löschen eines Chapters werden seine Relationen entfernt. Memories, HeartMoments und Milestones bleiben als Originalressourcen erhalten.

Folgen:

- keine FK-Cascade von Chapter auf Originalinhalte;
- Join-Zeilen dürfen `ON DELETE CASCADE` zum Chapter besitzen;
- Tests beweisen, dass Originale nach Chapter-Delete weiter lesbar sind;
- Event beschreibt Chapter-Delete, nicht Delete der Targets.

### M3-D20 – Globale Suche

**Status:** DECIDED für M3-Scope  
**Quelle:** Roadmap / M4-A-Abgrenzung  
**Entscheidung:** Globale Volltextsuche wird in M3 nicht vorgezogen. M3 darf domainlokale Filter/Sortierung liefern, aber kein allgemeines Search-Read-Model bauen.

Folgen:

- kein M3-Blocker durch M2-D21/Search-Provider;
- keine privaten M3-Inhalte in einem neuen Index;
- Search-Privacy wird später in M4-A explizit entworfen.

## Projektentscheidungen

### M3-D01/D02/D03/D04/D05/D30 – Wish-/Plan-Vertrag

**Status:** DECIDED  
**Datum:** 26.08.2026  
**Projektentscheidung:** #162  
**Vollständiger Vertrag:** [`decisions/WISH-PLAN-LIFECYCLE.md`](./decisions/WISH-PLAN-LIFECYCLE.md)

Verbindliche Kernaussagen:

- M3-Shared-Planning-/Listenressourcen verwenden collaborative write für beide aktiven Space-Mitglieder; `createdBy` ist Attribution, keine ACL.
- ein Wish besitzt höchstens einen gleichzeitig existierenden originären Plan; `sourceWishId` ist eindeutig.
- Wish->Plan ist atomar, Wish-row-locked und bei einem Retry im `PLANNED`-Zustand idempotent.
- die Konvertierung erzeugt einen Plan im Status `IDEA`; `Wish.status=PLANNED` entsteht nur durch diese Operation.
- return-to-wish ist nur für source-bound `IDEA`/`PLANNED` erlaubt, reaktiviert denselben Wish auf `OPEN` und löscht den Plan ohne automatische Payload-Rückkopplung.
- Planstatus: `IDEA -> PLANNED`, `PLANNED -> IDEA`, `IDEA|PLANNED -> COMPLETED`; `COMPLETED` ist terminal.
- `PLANNED` benötigt `plannedStart`; `COMPLETED` benötigt `experiencedOn`; ein spontanes `IDEA -> COMPLETED` bleibt erlaubt.
- Direct Plans sind erlaubt und starten immer als `IDEA` ohne `sourceWishId` und ohne Plantermine.
- Wish-/Plan-Delete folgt der dokumentierten State-Matrix und kaskadiert niemals auf fachliche Originale.
- für Transaktionen, die source Wish + Plan gemeinsam sperren, gilt die Lock-Reihenfolge `Wish -> Plan`.
- API nutzt explizite Operationsrouten für Convert, Schedule, Unschedule, Complete und Return; normales PATCH setzt keinen Status.
- PostgreSQL-, HTTP-, Race-, Rollback-, Tenant- und Delete-Matrix-Tests sind verpflichtend.

### M3-D06 / D28 – Place und präzise Location

Die Source erlaubt `address`, `latitude`, `longitude`; sie verbietet genaue Location in Analytics/Logs.

Vor Schema festlegen:

- ProtectedPayload vs. separate sensitive columns,
- ob Latitude/Longitude nur als Paar gültig sind,
- numerische Präzision,
- ob API exakte Werte an beide Space-Partner liefert,
- spätere Export-/Cache-Effekte,
- keine providerbedingte Speicherung zusätzlicher Place IDs in M3.

### M3-D08 – Relationfläche

Source nennt mögliche Relationstabellen. Nicht automatisch entschieden ist, ob **alle** davon im M3-MVP nötig sind.

Mindestens priorisieren:

- Plan <-> Place,
- Chapter <-> Memory,
- Chapter <-> shared HeartMoment,
- Chapter <-> Milestone,
- Chapter <-> Place bzw. `placeId`.

Weitere Relationen nur mit konkretem M3-Anwendungsfall.

### M3-D09 – Private Targets in Shared Relations

**PROPOSED aufgrund bestehender Security-Invariante:** Shared Chapter/Place darf keine Relation auf ein `OWNER_ONLY` Target erzeugen oder anzeigen. Insbesondere darf ein privater HeartMoment nicht über Relation, Count, Sortierlücke oder Delete-Fehler beweisbar werden.

Vor Runtime als `DECIDED` dokumentieren, damit Relation-Service und Tests dieselbe Regel tragen.

### M3-D13 / D14 / D15 – Collection Aggregate

Vor Migration gemeinsam entscheiden:

- Root-Version und/oder Item-Version,
- Ownership-/Persistenzfelder; die Write-Grundregel aus M3-D01 ist collaborative,
- Positionstyp,
- Reorder-Operation,
- Item-Completion-Concurrency,
- Parent-Delete-Cascade,
- Limits (max Items/Title lengths), falls erforderlich.

Die Einkaufsliste bleibt unabhängig davon außerhalb M3.

### M3-D17 – GiftIdea Status

Die Master Spec definiert:

```text
GiftIdea.status
```

ohne Werte. Beispiele wie `IDEA`, `BOUGHT`, `GIVEN` wären plausibel, aber **nicht source-bound**. Ein Enum wird erst nach Produktentscheidung in Persistenz/OpenAPI geschrieben.

### M3-D18 / D32 – PrivateCollection Persistenz

PrivateCollectionItem ist in der Quelle nur mit `title/completed/position` beschrieben. Für produktive Persistenz fehlen mindestens Identität, Parent-FK, Zeit-/Versionierungsentscheidung und Owner-Autorisierungsstrategie.

Diese Ergänzungen sind technische Notwendigkeiten, ihre konkrete Form muss vor Migration entschieden sein.

### M3-D23 – M3 Domain Events

**PROPOSED Envelope:**

```text
eventId
eventType
occurredAt
spaceId
actorId
resourceType
resourceId
resourceVersion
safeState?
```

Keine:

- Titel/Beschreibungen,
- PrivateNote-/GiftIdea-Inhalte,
- URL/Preistext,
- Adresse/Koordinaten,
- private Counts,
- fremde Owner-only Metadaten.

### M3-D24 – G3 Evidence

Die Roadmap beschreibt G3 fachlich, aber das exakte Beweisformat ist nicht so präzise wie bei G2.

Vor Ende der Runtime festlegen:

- Welche End-to-End-Flows müssen mit echter API/PostgreSQL laufen?
- Braucht G3 dünne Web/Android Referenzflows oder genügt Domain/API-Evidenz bis M5?
- Welche manuelle Accessibility-Evidenz ist M3- vs. M5-Scope?
- Welche Privacy-Negativtests sind Gate-blockierend?

Ziel: keine Wiederholung der G2-Situation, in der Gate-Evidenz erst nach Implementierung als Lücke sichtbar wurde.

### M3-D27 – Plan Checkliste/Medien

Die Informationsarchitektur nennt bei Plan UI-seitig „Checkliste“, „Medien und Notizen“. Die höher priorisierte Master-/Produktspezifikation definiert Plan jedoch ohne Checklist-/Attachment-Subdomain.

Daher gilt bis zu einer expliziten Entscheidung:

- **keine** Plan-Checklist als versteckte Collection,
- **keine** neuen Plan-Attachment-Relationen,
- `description` deckt den source-bound Freitext ab,
- Erweiterung später als eigener Scope.

### M3-D31 – Chapter `placeId` vs. `place_chapters`

Die Master Spec nennt sowohl `Chapter.placeId?` als auch eine mögliche `place_chapters`-Relation. Beides gleichzeitig kann zwei Wahrheitsquellen erzeugen.

Vor Schema entscheiden:

- genau ein primärer Place je Chapter über FK, **oder**
- n:m Relation, **oder**
- begründete Kombination mit klar unterschiedlicher Semantik.

Kein Runtime-PR darf beide Formen ohne Entscheidung einführen.

## Closure-Regel

Ein `BLOCKING`-Eintrag wird nur auf `DECIDED` gesetzt, wenn die Entscheidung mindestens enthält:

- Datum,
- Entscheider/Projektentscheidung,
- konkrete Semantik,
- Auswirkungen auf Persistenz/API,
- Delete-/Concurrency-Folge,
- Privacy-/Tenant-Folge,
- verpflichtende Tests,
- Verweis auf Issue/ADR/Spec.

`PROPOSED` allein macht keinen Runtime-Slice ready.
