# M3 Domain Model

**Status:** Readiness-Entwurf; source-bound Aussagen und offene Entscheidungen sind getrennt  
**Stand:** 26.08.2026

## 1. Grundsätze

M3 erweitert den modularen Monolithen um klar getrennte Fachdomänen. Es entsteht **keine** gemeinsame `items`-/`content`-Tabelle.

Gemeinsame Invarianten:

- gemeinsame Ressourcen gehören genau einem `space_id`;
- jeder Zugriff beginnt mit aktiver Membership in diesem Space;
- veränderbare Ressourcen besitzen eine `version` für Optimistic Concurrency;
- Ersteller-/Owner-IDs werden serverseitig aus dem Authorization Context gesetzt und nicht durch normale Updates übertragen;
- fachliche Inhalte werden nicht in Logs, Analytics oder Domain-Event-Payloads dupliziert;
- `OWNER_ONLY` wird in der Datenabfrage erzwungen, nicht durch Clientfilter;
- Relationen dürfen die Authorization des Targets niemals umgehen;
- Cross-Space-Relationen sind unzulässig;
- Shared und Private bleiben getrennte Domänen. Eine private Ablage wird nicht durch ein `visibility`-Flag auf Wish/Plan/Collection modelliert.

## 2. Privacy- und Ownership-Matrix

| Domain | Source-bound Sichtbarkeit | Owner/Author-Feld | Schreibregel |
|---|---|---|---|
| Wish | `SPACE_SHARED` | `createdBy` | **OPEN – M3-D01** |
| Plan | `SPACE_SHARED` | `createdBy` | **OPEN – M3-D01** |
| Place | `SPACE_SHARED` | `createdBy` | **OPEN – M3-D01** |
| Chapter | gemeinsamer Space-Inhalt | `createdBy` | **OPEN – M3-D01** |
| Collection | `SPACE_SHARED` | ggf. `createdBy` ergänzen? **OPEN – M3-D13** | **OPEN – M3-D13** |
| CollectionItem | erbt Collection | `createdBy` laut Master Spec | **OPEN – M3-D13** |
| PrivateNote | `OWNER_ONLY` | `ownerId` | Owner-only, serverseitig |
| GiftIdea | `OWNER_ONLY` | `ownerId` | Owner-only, serverseitig |
| PrivateCollection | `OWNER_ONLY` | `ownerId` | Owner-only, serverseitig |
| PrivateCollectionItem | erbt PrivateCollection / Owner | nicht vollständig spezifiziert | Owner-only; genaue Persistenz **OPEN – M3-D18** |

Für Private-Area-Modelle soll die vorhandene zentrale Owner-/Privacy-Autorisierung wiederverwendet werden. Ob jedes Modell direkt `PrivateResourceMixin` trägt oder Child-Items ausschließlich über den autorisierten Parent geladen werden, wird pro Tabelle entschieden; es darf aber keine zweite, schwächere Privatlogik entstehen.

## 3. Wish

### Source-bound Modell

```text
Wish
- id
- spaceId
- title
- createdBy
- createdAt
- updatedAt
- version
- status: OPEN | PLANNED | COMPLETED
```

Die Quelle nennt kein freies `description`-/`body`-Feld. Ein solches Feld wird deshalb in M3 nicht stillschweigend vorausgesetzt.

### Source-bound Verhalten

- Wish ist gemeinsamer Space-Inhalt.
- Nutzer können Wishes suchen, filtern, sortieren und ihren Fortschritt sehen; globale Volltextsuche selbst liegt jedoch im späteren Search-Milestone.
- Ein Wish kann Ausgangspunkt eines Plans werden.

### Noch zu entscheiden

- Schreib-/Löschrechte des Partners gegenüber dem Ersteller.
- Ob `PLANNED` ausschließlich aus einer erfolgreichen Wish->Plan-Transaktion entstehen darf.
- Ob `COMPLETED` ohne Plan zulässig ist oder nur über einen abgeschlossenen Plan erreicht wird.
- Delete eines Wishes mit existierendem `sourceWishId`-Plan.
- ob ein Wish nach Plan-Konvertierung weiter editierbar ist und welche Felder synchron bleiben – bevorzugt **keine automatische Inhaltskopplung** nach der Konvertierung.

## 4. Plan

### Source-bound Modell

```text
Plan
- id
- spaceId
- sourceWishId?
- title
- description?
- status: IDEA | PLANNED | COMPLETED
- plannedStart?
- plannedEnd?
- experiencedOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version
```

### Source-bound Workflow

```text
Wish
  -> Plan
  -> COMPLETED / erlebt
  -> optional Chapter
```

Ein nicht abgeschlossener Plan darf grundsätzlich wieder in einen Wunschzustand zurückgeführt werden. Die genaue Semantik ist noch offen.

### Statusautomat – vorgeschlagene Form

```text
IDEA --------> PLANNED --------> COMPLETED
  \               |
   \--------------/
        vor Abschluss
        kontrollierte Rückführung zu Wish
```

Das Diagramm ist `PROPOSED`. Insbesondere bleibt zu entscheiden:

- ob `PLANNED -> IDEA` als normaler Planstatuswechsel zulässig ist,
- ob „zurück zu Wish“ den Plan löscht, archiviert oder als Historie erhält,
- ob ein `COMPLETED` Plan wieder geöffnet werden darf,
- welche Kombinationen aus `plannedStart`, `plannedEnd`, `experiencedOn` und Status gültig sind.

### Datumsinvarianten – Vorschlag, noch nicht bindend

- `plannedEnd >= plannedStart`, wenn beide gesetzt sind;
- `COMPLETED` verlangt `experiencedOn` oder eine explizite Entscheidung, warum es ohne Datum zulässig ist;
- `IDEA` darf ohne Termin existieren;
- `PLANNED` kann mindestens einen fachlichen Planungsindikator verlangen – Terminpflicht ist noch nicht entschieden.

## 5. Atomare Wish -> Plan-Konvertierung

Die User-Flow-Spezifikation verlangt, dass die Konvertierung nachvollziehbar und fachlich transaktional erfolgt. Daraus folgt als Readiness-Anforderung:

```text
lock/read Wish in space
  -> authorize
  -> validate current version/status
  -> create exactly one Plan with sourceWishId
  -> update Wish status/relation
  -> emit safe events
  -> commit once
```

Offen bleibt die genaue Idempotenzstrategie. Mögliche Ansätze:

1. Unique Constraint auf `(space_id, source_wish_id)` – einfach, wenn ein Wish höchstens einen aktiven/ursprünglichen Plan besitzen darf.
2. expliziter Idempotency-Key – allgemeiner, aber zusätzliche Infrastruktur/Semantik.
3. serialisierte Row-Lock-Transaktion plus Unique Constraint – bevorzugter Kandidat, falls die Kardinalität 1:1 beschlossen wird.

Die Entscheidung steht in M3-D02. Doppelte Bestätigung darf niemals zwei fachlich identische Plans erzeugen.

## 6. Rückführung Plan -> Wish

Die Produktspezifikation erlaubt die Rückführung eines nicht abgeschlossenen Plans. **Nicht spezifiziert** ist, ob dabei:

- der ursprüngliche Wish reaktiviert wird,
- ein neuer Wish entsteht,
- der Plan erhalten/archiviert/gelöscht wird,
- bereits vorgenommene Planänderungen in den Wish zurückkopiert werden.

Diese Semantik ist BLOCKING (M3-D03). Eine Implementierung darf nicht per `DELETE Plan + PATCH Wish` improvisieren.

## 7. Place

### Source-bound Modell

```text
Place
- id
- spaceId
- name
- description?
- address?
- latitude?
- longitude?
- createdBy
- createdAt/updatedAt
- version
```

### Invarianten

- Koordinaten sind optional.
- Ein Ort ohne Koordinaten ist gültig.
- M3 braucht keinen Karten-/Geocoding-Provider, um Place fachlich zu liefern.
- Places können mit Memories, HeartMoments, Milestones, Plans und Chapters verbunden werden.

### Sensible Ortsdaten

`latitude`, `longitude`, freie Beschreibung und ggf. Adresse können sensible Rückschlüsse auf Aufenthaltsorte zulassen. Für M3 gilt deshalb bereits:

- keine präzisen Ortsdaten in Logs, Analytics, Event-Payloads oder Metriklabels;
- keine serverseitige URL-/Provideranreicherung in diesem Milestone;
- Partnerzugriff nur über normale Space-Autorisierung;
- Klassifizierung als ProtectedPayload oder gesondert geschütztes Feld ist **BLOCKING – M3-D06/M3-D28**.

### Deduplizierung

Automatische Place-Deduplizierung ist nicht source-bound. Ein Name oder eine Koordinate ist kein stabiler globaler Identifikator. Der bevorzugte sichere Start ist **keine implizite Zusammenführung**; eine endgültige Entscheidung steht in M3-D07.

## 8. Content Relations

### Source-bound Architektur

Nach außen darf ein gemeinsamer Relation Service existieren. Intern sollen echte FKs und typisierte Relationstabellen verwendet werden. Eine Universalrelation

```text
targetType
targetId
```

ohne referentielle Integrität ist ausgeschlossen.

Die Master Spec nennt insbesondere:

```text
chapter_memories
chapter_heart_moments
chapter_milestones

place_memories
place_heart_moments
place_milestones
place_plans
place_chapters
```

### Sicherheitsinvarianten

Eine Relation darf nur entstehen, wenn:

1. Actor aktive Membership im Space besitzt,
2. Relation-Parent und Target demselben Space angehören,
3. Actor das Target lesen darf,
4. Actor die Relation am Parent ändern darf,
5. die Zielkombination fachlich erlaubt ist.

Ein gemeinsamer Chapter oder Place darf **keine OWNER_ONLY-Existenz verraten**. Ein privater HeartMoment ist deshalb nicht über einen gemeinsamen Chapter/Place sichtbar oder relational beweisbar. Relation-Create gegen ein nicht lesbares Target antwortet privacy-sicher wie „nicht vorhanden“.

### Relation-Lifecycle

Für jede Relationstabelle müssen feststehen:

- Unique Constraint,
- Sortier-/Positionsfeld, falls fachlich nötig,
- `ON DELETE`-Semantik,
- Concurrency/Reorder-Verhalten,
- Event-Payload,
- Verhalten bei Privacy-Wechsel des Targets.

Die konkrete M3-Relationfläche ist M3-D08/M3-D09/M3-D26.

## 9. Chapter

### Source-bound Modell

```text
Chapter
- id
- spaceId
- title
- description?
- startOn?
- endOn?
- placeId?
- createdBy
- createdAt/updatedAt
- version
```

Chapter bündelt:

- Memories,
- geteilte HeartMoments,
- Milestones.

### Source-bound Delete-Regel

```text
DELETE Chapter
  -> Chapter-Relationen entfernen
  -> Original-Memory/HeartMoment/Milestone NICHT löschen
```

Diese Regel ist bereits entschieden und wird im Decision Log als source-bound `DECIDED` geführt.

### Offene Punkte

- Partner-Schreibrechte.
- `startOn <= endOn` und Umgang mit leeren Grenzen.
- Reihenfolge der Chapter-Inhalte: chronologisch abgeleitet oder manuell positionierbar?
- direkte `placeId`-Spalte plus `place_chapters` wirkt in der Master Spec teilweise redundant; die genaue kanonische Relation ist vor Migration zu entscheiden.
- darf ein Target gleichzeitig mehreren Chapters angehören? Die Quelle verbietet es nicht.

## 10. Collection / CollectionItem

### Source-bound Modell

```text
Collection
- id
- spaceId
- title
- icon
- createdAt/updatedAt

CollectionItem
- id
- collectionId
- title
- completed
- position
- createdBy
- createdAt/updatedAt
```

Die Produktspezifikation beschreibt frei definierbare gemeinsame Listen mit Abhaken, Sortierung und Mehrfachauswahl. Die Einkaufsliste ist ausdrücklich **keine** Collection.

### Readiness-Lücken

Die globalen Projektkonventionen verlangen Versionierung für veränderbare Objekte, während die Master-Feldliste für Collection/Item kein `version` nennt. Dieser Konflikt wird nicht ignoriert: M3-D14/M3-D18 entscheiden die Concurrency-Fläche.

Weiter offen:

- Ersteller/Ownership der Collection selbst,
- wer Collection und Items ändern/löschen darf,
- Positionsstrategie (dense integer, fractional rank o. ä.),
- atomarer Reorder und Concurrent Reorder,
- ob Mehrfachauswahl eine reine UI-Batchaktion oder zusätzliche Domainsemantik ist,
- Delete Collection -> Items: bevorzugt Parent-Cascade, aber noch BLOCKING.

## 11. PrivateNote

### Source-bound Modell

```text
PrivateNote
- id
- spaceId
- ownerId
- title
- body
- pinned
- createdAt/updatedAt
- version
```

### Harte Invarianten

- `OWNER_ONLY` ohne Partner-Ausnahme.
- Partner erhält kein positives Signal über ID, Listen, Counts, Suche, Dashboard, Deep Link oder Fehlerdetail.
- `title` und `body` sind sensible Nutzerinhalte und gehören in die ProtectedPayload-Grenze bzw. deren spätere E2EE-fähige Struktur.
- `ownerId` ist unveränderlich.

## 12. GiftIdea

### Source-bound Modell

```text
GiftIdea
- id
- spaceId
- ownerId
- title
- description?
- recipient?
- occasion?
- targetOn?
- priceText?
- url?
- status
- pinned
- createdAt/updatedAt
- version
```

**Die Spezifikation nennt keinen Enum für `status`.** Kein Code darf Werte dafür erfinden. M3-D17 ist BLOCKING.

Sicherheitsgrenzen:

- gesamter fachlicher Inhalt owner-only;
- `url` wird in M3 nur als Nutzerinhalt gespeichert; keine serverseitige Preview/Fetch-Auflösung ohne separates SSRF-/Provider-Design und Reuse-Review;
- `priceText` bleibt Freitext, solange keine monetäre Domainentscheidung getroffen wurde; keine Währungslogik stillschweigend ableiten.

## 13. PrivateCollection / PrivateCollectionItem

### Source-bound Kern

```text
PrivateCollection
- spaceId
- ownerId
- title
- icon

PrivateCollectionItem
- title
- completed
- position
```

Beide sind `OWNER_ONLY`.

Die Feldliste ist bewusst unvollständiger als bei anderen Modellen (z. B. IDs/Timestamps/Version am Item). M3-D18 muss die Persistenz- und Concurrency-Konvention vervollständigen, bevor Migrationen entstehen.

## 14. ProtectedPayload-Kandidaten

Source-bound ist die Architekturgrenze, nicht jede einzelne M3-Spalte. Für die Entscheidung werden folgende Kandidaten geprüft:

| Domain | Kandidaten |
|---|---|
| Wish | `title` und mögliche spätere Freitextfelder |
| Plan | `title`, `description` |
| Place | `name`, `description`, `address`, präzise Koordinaten |
| Chapter | `title`, `description` |
| Collection | `title`; Item `title` |
| PrivateNote | `title`, `body` |
| GiftIdea | alle inhaltlichen Felder einschließlich URL/Preistext |
| PrivateCollection | `title`; Item `title` |

Status, technische IDs, Versionen und sichere enumartige Zustände können außerhalb des Payloads liegen, sofern sie keine unnötige sensitive Information erzeugen. Die endgültige Klassifizierung gehört in die jeweiligen Decisions.

## 15. Domain Events

M3 folgt der bestehenden M2-Regel: Events transportieren IDs und sichere Zustandsmetadaten, keine geschützten Inhalte.

Proposed Minimal Envelope:

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

Nicht in Events:

- Wish-/Plan-/Chapter-/Collection-Titel,
- PrivateNote/GiftIdea-Inhalt,
- URL einer GiftIdea,
- Adresse oder Koordinaten,
- private Relation-Counts,
- beliebige Partner-private Metadaten.

M3-D23 friert den Eventvertrag vor dem ersten Event-produzierenden Slice ein.

## 16. Delete-/Cascade-Matrix

| Operation | Source-bound | Noch zu entscheiden |
|---|---|---|
| Delete Wish ohne Plan | nein | Hard delete/Retention/Event |
| Delete Wish mit source Plan | nein | verbieten, entkoppeln oder Plan erhalten |
| Delete Plan | nein | Auswirkung auf source Wish/Place/Chapter |
| Delete Place | nein | Relationen entfernen vs. Delete blockieren |
| Delete Chapter | **ja** | Relationen entfernen, Originalinhalte erhalten |
| Delete Collection | nein | bevorzugt Items mit Parent löschen |
| Delete CollectionItem | nein | Position/Reorder danach |
| Delete PrivateNote/GiftIdea | owner-only source-bound | Retention/Audit/Event |
| Delete PrivateCollection | nein | bevorzugt private Items mit Parent löschen |

DB-Cascade darf niemals fachliche Originalinhalte außerhalb des Parent-Aggregats mitreißen.

## 17. Zentrale Race-Szenarien

Vor Runtime müssen mindestens diese Races im Testdesign stehen:

- zwei parallele Wish->Plan-Konvertierungen,
- Wish-Delete gegen Wish->Plan,
- Plan-Completion gegen Plan->Wish-Rückführung,
- Relation-Create gegen Target-Delete,
- Relation-Create gegen HeartMoment `SHARED -> PRIVATE`,
- Chapter-Delete gegen Relation-Create,
- Place-Delete gegen Relation-Create,
- Collection-Reorder gegen Item-Delete/Completion,
- PrivateCollection-Reorder gegen Item-Delete,
- Owner-Read gegen Logout/Membership-Verlust in Client-Caches (später M5).

Die DB-/Service-Lösung muss so gewählt werden, dass ein Race nicht nur zufällig in Tests funktioniert, sondern durch Constraints/Locks/Transactions deterministisch entschieden wird.
