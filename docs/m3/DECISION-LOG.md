# M3 Decision Log

**Stand:** 26.08.2026  
**Status S0:** alle M3-D01 bis M3-D32 sind `DECIDED`  
**Regel:** Keine M3-Grundsatzfrage wird stillschweigend im Runtime-Code entschieden.

Dieses Log ist die kompakte Uebersicht. Die vollstaendigen Verträge stehen in den verlinkten Decision-Dokumenten.

## Status

- `OPEN` – Entscheidung fehlt.
- `PROPOSED` – bevorzugte Option ist dokumentiert, aber nicht bindend.
- `DECIDED` – durch Source oder explizite Projektentscheidung bindend.

## Prioritaet

- `BLOCKING` – vor dem ersten betroffenen Runtime-Slice entscheiden.
- `BEFORE_CLIENTS` – vor stabiler Web-/Android-Integration entscheiden.
- `BEFORE_GATE` – vor dem finalen G3-Nachweis entscheiden.
- `LATER` – Entscheidung darf die Umsetzung bewusst in einen spaeteren Scope verschieben.

## Decision-Matrix

| ID | Prioritaet | Status | Thema | Verbindliche Entscheidung |
|---|---|---|---|---|
| M3-D01 | BLOCKING | DECIDED | Shared Writes | Wish, Plan, Place, Chapter und gemeinsame Collection: collaborative write fuer beide aktiven Space-Mitglieder; `createdBy` ist Attribution, keine ACL. #162 |
| M3-D02 | BLOCKING | DECIDED | Wish -> Plan | Hoechstens ein originärer Plan je Wish; atomare Conversion mit Wish-Row-Lock + Unique; Retry auf PLANNED liefert denselben Plan. #162 |
| M3-D03 | BLOCKING | DECIDED | Plan -> Wish | Nur source-bound IDEA/PLANNED; denselben Wish auf OPEN reaktivieren, Plan loeschen, keine Payload zurueckkopieren. #162 |
| M3-D04 | BLOCKING | DECIDED | Plan Lifecycle | IDEA->PLANNED, PLANNED->IDEA, IDEA/PLANNED->COMPLETED; COMPLETED terminal; explizite Operationsrouten. #162 |
| M3-D05 | BLOCKING | DECIDED | Wish/Plan Delete | State-basierte Delete-Matrix; keine Cascade auf fachliche Originale. #162 |
| M3-D06 | BLOCKING | DECIDED | Place Privacy | Place-Inhalt inklusive Adresse/Koordinaten ist geschuetzter Shared Content; exakte Werte nur im autorisierten Space, keine Telemetrie. #163 |
| M3-D07 | BLOCKING | DECIDED | Place Identity | Keine automatische/implizite Deduplizierung oder Zusammenfuehrung. #163 |
| M3-D08 | BLOCKING | DECIDED | Relation Contract | Typisierte FK-Relationen; Plan/Chapter verwenden kanonisches `placeId`, Content-Relations eigene Join-Tabellen; externe API typisiert. #163 |
| M3-D09 | BLOCKING | DECIDED | Relation Privacy | Keine Relation auf OWNER_ONLY/private Targets; nicht lesbare Targets privacy-sicher 404; SHARED->PRIVATE entfernt Relations atomar. #163 |
| M3-D10 | BLOCKING | DECIDED | Chapter Ordering | Keine persistierte manuelle Reihenfolge in M3; deterministisch aus Ereignisdatum/createdAt abgeleitet. #163 |
| M3-D11 | BLOCKING | DECIDED | Chapter Dates | `startOn`/`endOn` unabhaengig optional; falls beide gesetzt: `endOn >= startOn`. #163 |
| M3-D12 | BLOCKING | DECIDED | Chapter Delete | Chapter-Delete entfernt Relations, nie Memory/HeartMoment/Milestone-Originale. Source-bound. |
| M3-D13 | BLOCKING | DECIDED | Collection Ownership | Root bekommt `createdBy`; Root/Items collaborative write; Attribution ist keine ACL. #164 |
| M3-D14 | BLOCKING | DECIDED | Collection Concurrency | Root-Version schuetzt Struktur/Order, Item-Version schuetzt Inhalt; atomarer Full-List-Reorder mit contiguous Integerpositionen. #164 |
| M3-D15 | BLOCKING | DECIDED | Collection Delete | CollectionItem ist Child; Parent-Delete darf Items cascaden, keine anderen Originale. #164 |
| M3-D16 | BLOCKING | DECIDED | Private Payload | PrivateNote title/body; GiftIdea inhaltliche Felder; PrivateCollection-/Item-Titel sind geschuetzter Owner-only Content. #164 |
| M3-D17 | BLOCKING | DECIDED | GiftIdea Status | `IDEA | BOUGHT | GIVEN` mit explizit validierten Transitionen. #164 |
| M3-D18 | BLOCKING | DECIDED | Private Collection | Vollstaendiges Root-/Item-Schema mit IDs/Timestamps/Version; Root-Version fuer Order, Item-Version fuer Inhalt. #164 |
| M3-D19 | BLOCKING | DECIDED | Private API | Space-scoped `/private/...`; Owner nur aus Auth Context; fremd/unbekannt/Partner identisch 404. #164 |
| M3-D20 | LATER | DECIDED | Search | Keine globale Volltextsuche in M3; M4-A. Domainlokale Filter bleiben erlaubt. Roadmap. |
| M3-D21 | BEFORE_CLIENTS | DECIDED | Export | M3 implementiert Export nicht; gemeinsamer Export enthaelt nie Owner-only, persoenlicher Export spaeter nur eigene Private Area. #165 |
| M3-D22 | BEFORE_CLIENTS | DECIDED | Client Cache | Kein persistenter Private-Read-Cache in M3; M5 muss Account+Space+Owner namespacen und bei Logout/Wechsel loeschen. #165 |
| M3-D23 | BLOCKING | DECIDED | Events | Minimaler redigierter Event-Envelope; OWNER_ONLY ohne fachlichen `safeState`; keine ProtectedPayloads/Private Counts. #164 |
| M3-D24 | BEFORE_GATE | DECIDED | G3 Evidence | G3 ist Domain/API/PostgreSQL-Gate mit fuenf realen HTTP-E2E-Flows; volle Client-Paritaet/Accessibility bleibt M5/G4. #165 |
| M3-D25 | BEFORE_CLIENTS | DECIDED | Private IA | Sekundaerer persoenlicher Bereich `Mehr / Mein Bereich`; keine gemeinsamen Counts/Badges; Security bleibt serverseitig. #165 |
| M3-D26 | BLOCKING | DECIDED | Relation Races | Relation Create sperrt Parent->Target, revalidiert Privacy und wird durch FK/Unique abgesichert; Delete/Privacy-Races deterministisch. #163 |
| M3-D27 | LATER | DECIDED | Plan Richness | Checklist/Plan-Medien/strukturierte Zusatznotizen werden bewusst nicht in M3 vorgezogen; spaeter eigener Scope. #165 |
| M3-D28 | BLOCKING | DECIDED | Location Leakage | Lat/Lon als Paar, Wertebereiche und max. 6 Nachkommastellen; keine Logs/Analytics/Events/Provideranreicherung. #163 |
| M3-D29 | BEFORE_CLIENTS | DECIDED | Collection Multi-select | Reiner Client-Batchselection-State; kein persistiertes Domainfeld/Selection-Modell. #165 |
| M3-D30 | BLOCKING | DECIDED | Direct Plan Create | Erlaubt; startet immer IDEA ohne `sourceWishId`, Plantermine oder `experiencedOn`. #162 |
| M3-D31 | BLOCKING | DECIDED | Chapter/Place | `Chapter.placeId` ist einzige kanonische Wahrheit; keine parallele `place_chapters`-Tabelle. #163 |
| M3-D32 | BLOCKING | DECIDED | Private Item Auth | PrivateCollectionItem dupliziert owner/space nicht; Autorisierung immer ueber owner-scoped Parent-Join. #164 |

## Verbindliche Decision-Dokumente

### Wish / Plan – #162

[`decisions/WISH-PLAN-LIFECYCLE.md`](./decisions/WISH-PLAN-LIFECYCLE.md)

Enthaelt:

- Wish-/Plan-Statusautomaten;
- Wish->Plan-Atomizitaet und Idempotenz;
- Return-to-Wish;
- Direct Plan Create;
- Delete-Matrix;
- Locking, DB-Constraints, Fehlercodes und Pflichtests.

### Place / Relations / Chapters – #163

[`decisions/PLACE-RELATIONS-CHAPTERS.md`](./decisions/PLACE-RELATIONS-CHAPTERS.md)

Enthaelt:

- Place Protected Content und Koordinatenregeln;
- keine automatische Deduplizierung;
- freigegebene typisierte Relationstabellen;
- kanonische Plan-/Chapter-Place-FKs;
- Relation Privacy und SHARED->PRIVATE-Cleanup;
- Chapter-Dates und abgeleitete Reihenfolge;
- Delete-/Race-Matrix und Tests.

### Collections / Private Area – #164

[`decisions/COLLECTIONS-PRIVATE-AREA.md`](./decisions/COLLECTIONS-PRIVATE-AREA.md)

Enthaelt:

- Shared Collection Write-/Ownership-Modell;
- atomaren Reorder-/Versionierungsvertrag;
- Collection-Delete-Cascade;
- Private ProtectedPayload-Grenzen;
- GiftIdea Statusenum;
- PrivateCollection Root-/Child-Schema;
- owner-scoped Private API;
- M3 Event-/Redaction-Vertrag.

### G3 / Clients / Export / Cache – #165

[`decisions/G3-CLIENT-BOUNDARIES.md`](./decisions/G3-CLIENT-BOUNDARIES.md)

Enthaelt:

- fuenf verpflichtende reale G3-E2E-Flows;
- Gate-blockierende Privacy-/Security-Kriterien;
- G3 vs. M5/G4-Abgrenzung;
- spaetere Export-/Cache-Privacy-Vertraege;
- Private-Area-IA;
- Plan-Richness bewusst spaeter;
- Multi-select als Clientzustand.

## Source-bound Entscheidungen

### M3-D12 – Chapter Delete

Beim Loeschen eines Chapters werden seine Relations entfernt. Memories, HeartMoments und Milestones bleiben als Originalressourcen erhalten.

Folgen:

- keine FK-Cascade von Chapter auf Originalinhalte;
- Join-Zeilen duerfen `ON DELETE CASCADE` zum Chapter besitzen;
- Tests beweisen, dass Originale nach Chapter-Delete weiter lesbar sind.

### M3-D20 – Globale Suche

Globale Volltextsuche wird in M3 nicht vorgezogen. Die Roadmap ordnet Search M4-A zu. M3 darf domainlokale Filter/Sortierung liefern, aber kein allgemeines Search-Read-Model bauen.

## S0-Abschluss

Mit Merge der Decision-PRs #162 sowie #163/#164/#165 gilt:

- alle `BLOCKING`-Entscheidungen sind `DECIDED`;
- alle `BEFORE_CLIENTS`-/`BEFORE_GATE`-Grenzen sind frueh festgelegt;
- bewusst spaetere Funktionen sind explizit als solche entschieden;
- kein Runtime-Slice muss fachliche Kernsemantik erfinden.

**Wichtig:** S0-Abschluss ist keine automatische M3-Runtime-Freigabe. Die in `docs/m3/README.md` dokumentierten Projekt-/Gate-Startbedingungen bleiben separat verbindlich.

## Closure-Regel fuer spaetere Aenderungen

Eine bereits `DECIDED`e Semantik wird nicht stillschweigend in einem Runtime-PR veraendert. Eine Aenderung braucht mindestens:

- explizite neue Projektentscheidung/ADR oder Decision-PR;
- Auswirkungen auf Persistenz/API;
- Delete-/Concurrency-Folge;
- Privacy-/Tenant-Folge;
- verpflichtende Tests;
- Migration-/Kompatibilitaetsbetrachtung, falls Runtime bereits existiert.