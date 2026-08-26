# M3 Delivery Plan

**Status:** S0 abgeschlossen; Runtime freigegeben; S1 und S2 geliefert  
**Stand:** 26.08.2026

## 1. Gate vor Runtime

Dieser Plan beschreibt die Reihenfolge **nach Runtime-Freigabe**.

Vor dem ersten M3-Runtime-Commit muessen nach aktueller Projektregel:

1. der finale G2-Review auf aktuellem `main` `G2: BESTANDEN` feststellen (#147),
2. #146 die Statusquellen synchronisieren und M3 freigeben,
3. der konkrete Runtime-PR den produktiven OpenAPI-Vertrag und Reuse-before-build sauber behandeln.

Punkt 1 und 2 sind erfuellt. Punkt 3 bleibt eine Bedingung **je Runtime-PR** und ist mit dem Gate nicht abgegolten.

Die fachlichen S0-Entscheidungen sind abgeschlossen: M3-D01 bis M3-D32 stehen auf `DECIDED`.

## 2. S0 – abgeschlossen

### #162 Wish / Plan

- collaborative write;
- atomare/idempotente Wish->Plan-Konvertierung;
- Return-to-Wish;
- Plan-Lifecycle und Datumsinvarianten;
- Delete-Matrix;
- Direct Plan Create.

Vertrag: [`decisions/WISH-PLAN-LIFECYCLE.md`](./decisions/WISH-PLAN-LIFECYCLE.md)

### #163 Place / Relations / Chapters

- Place-Privacy und Koordinaten;
- keine automatische Deduplizierung;
- typisierte Relationflaeche;
- `Plan.placeId`/`Chapter.placeId` als kanonische Single-Place-FKs;
- Relation Privacy und Races;
- Chapter-Dates, abgeleitete Reihenfolge und Delete.

Vertrag: [`decisions/PLACE-RELATIONS-CHAPTERS.md`](./decisions/PLACE-RELATIONS-CHAPTERS.md)

### #164 Collections / Private Area

- Shared Collection Root-/Item-Versionierung;
- atomarer Reorder;
- Private ProtectedPayload;
- GiftIdea Status;
- PrivateCollection Schema/Auth;
- owner-scoped Private API;
- M3 Event-Redaction.

Vertrag: [`decisions/COLLECTIONS-PRIVATE-AREA.md`](./decisions/COLLECTIONS-PRIVATE-AREA.md)

### #165 G3 / Clients / Export / Cache

- G3 als Domain/API/PostgreSQL-Gate;
- fuenf reale HTTP-E2E-Pflichtflows;
- M5/G4-Grenze fuer Clients/Accessibility/Performance;
- spaetere Export-/Cache-Privacy;
- Private IA;
- Plan Richness spaeter;
- Multi-select als Clientzustand.

Vertrag: [`decisions/G3-CLIENT-BOUNDARIES.md`](./decisions/G3-CLIENT-BOUNDARIES.md)

## 3. Zielbild

```text
Wish OPEN
  -> Plan IDEA
  -> PLANNED optional
  -> COMPLETED
  -> optional Chapter

Plan --------> Place (max. ein primaerer Place)
Chapter -----> Place (max. ein primaerer Place)

Memory -----------+
SHARED HeartMoment+---- typisierte Relations ----> Chapter / Place
Milestone --------+

Shared Collection
  -> CollectionItems + atomarer Reorder

PrivateNote / GiftIdea / PrivateCollection
  -> OWNER_ONLY, komplett getrennte Query-/API-Grenze
```

## 4. S1 – Wish Foundation – geliefert

Scope:

- Wish Modell + Migration;
- `OPEN | PLANNED | COMPLETED`;
- title/createdBy/version;
- CRUD/List;
- collaborative write;
- `If-Match`/409;
- Tenant Guard;
- sichere Events;
- PostgreSQL-/HTTP-/Cross-Tenant-Tests.

Exit:

- Wish ist belastbar als eigenstaendige Shared-Domain;
- keine freie Statusmutation umgeht den Wish->Plan-Vertrag.

Umgesetzt. Die beiden in S1 offen gelassenen Punkte - die erste echte Statustransition und die planabhaengigen Zeilen der Delete-Matrix - sind mit S2 nachgezogen.

## 5. S2 – Plan + Wish->Plan – geliefert

Scope:

- Plan Modell + Migration;
- `IDEA | PLANNED | COMPLETED`;
- Direct Plan Create;
- Plan CRUD/List;
- schedule/unschedule/complete;
- `sourceWishId` + Unique/FK;
- atomare Wish->Plan-Operation;
- Return-to-Wish;
- Wish/Plan Lock-Reihenfolge;
- Race-/Rollback-Tests.

Pflichtnachweis:

```text
Wish Create
-> Convert
-> genau ein Plan
-> Complete
-> Wish + Plan konsistent COMPLETED
```

Umgesetzt, inklusive der Race- und Rollback-Pflichttests aus dem Decision-Dokument: paralleler Convert erzeugt genau einen Plan, ein Fehler zwischen Plan-Insert und Wish-Transition hinterlaesst nichts, und Delete gegen Convert bzw. Complete gegen Return endet deterministisch ohne halben Lifecycle.

Nicht enthalten und ausdruecklich bei S3: `Plan.placeId`. M3-D02 und M3-D30 nennen das Feld fuer Create, PATCH und Konvertierung; ohne Place-Domaene koennte es auf nichts zeigen, und ein Vertrag mit einem unbenutzbaren Feld verspricht eine Zuordnung, die der Server nicht herstellen kann.

## 6. S3 – Place Foundation – naechster Slice

Scope:

- Place Modell + Migration;
- `name/description/address/latitude/longitude`;
- Lat/Lon als Paar, max. 6 Nachkommastellen;
- CRUD/List;
- keine automatische Deduplizierung;
- kein Maps-/Geocoding-Provider;
- Redaction in Logs/Events;
- Delete setzt Plan/Chapter-Place-FKs auf NULL und entfernt nur Join-Relations;
- `Plan.placeId` als Feld, Migration und Vertragsflaeche nachziehen (aus S2 verschoben).

## 7. S4 – Typisierte Content Relations

M3 implementiert:

```text
place_memories
place_heart_moments
place_milestones
chapter_memories
chapter_heart_moments
chapter_milestones
```

Technische Regeln:

- echte FKs + Unique Constraints;
- keine freie `(targetType,targetId)`-Polymorphie;
- same-space enforcement;
- nur SHARED HeartMoments;
- typisierte REST-Routen;
- Relation Create Parent->Target gelockt/revalidiert;
- Privacy-Wechsel SHARED->PRIVATE entfernt Relations atomar;
- Delete-/Privacy-Races mit PostgreSQL getestet.

`place_plans` und `place_chapters` werden nicht gebaut; `Plan.placeId` und `Chapter.placeId` sind kanonisch.

## 8. S5 – Chapter

Scope:

- Chapter Modell + Migration;
- CRUD/List;
- `startOn`/`endOn` optional, bei beiden `endOn >= startOn`;
- `placeId`;
- typisierte Content Relations;
- abgeleitete chronologische Darstellung;
- mehrere Chapters duerfen dasselbe Target referenzieren;
- Delete entfernt nur Chapter + Relations.

Pflichttest:

```text
Chapter + Memory + SHARED HeartMoment + Milestone
-> DELETE Chapter
-> Relations weg
-> alle Originale unveraendert lesbar
```

## 9. S6 – Gemeinsame Collections

Scope:

- Collection + CollectionItem;
- `createdBy` Attribution, collaborative write;
- Root-Version fuer Struktur/Order;
- Item-Version fuer Title/Completed;
- Position `0..n-1`;
- atomarer Full-List-Reorder;
- Item Delete + Verdichtung;
- Parent-Delete cascadiert nur Items;
- Cross-Tenant-/Concurrency-Tests.

Nicht enthalten: ShoppingList und persistierter Multi-select-Zustand.

## 10. S7 – PrivateNote + GiftIdea

Scope:

- getrennte Tabellen/Services;
- Owner-only CRUD/List;
- `/spaces/{spaceId}/private/...`;
- PrivateNote title/body als Protected Content;
- GiftIdea `IDEA | BOUGHT | GIVEN`;
- keine URL Preview/Server-Fetches;
- privacy-sicheres 404;
- Event-/Log-Redaction;
- Partner-Negativtests.

## 11. S8 – PrivateCollection

Scope:

- PrivateCollection Root mit id/space/owner/version;
- Items mit Parent-FK, id/version/position;
- owner/space ausschliesslich ueber Parent autorisieren;
- Owner-only Reorder/Completion;
- Parent-Delete cascadiert nur Items;
- Partner-/Cross-Space-Negativtests.

Shared Collection und PrivateCollection teilen weder Tabelle noch unsicheren Querypfad.

## 12. S9 – integrierter M3 Backend/API-Nachweis

Die fuenf G3-Pflichtflows werden gegen reale SideBySide-API + PostgreSQL nachgewiesen:

1. Wish -> Plan -> Complete;
2. Place + typisierte Relation + Delete;
3. Chapter + Relations + Delete ohne Originalverlust;
4. Collection Completion + Reorder + Conflict;
5. PrivateNote/GiftIdea/PrivateCollection mit Partner-Negativpfad.

Zusaetzlich laufen Cross-Tenant-, Race-, Event-/Log-Redaction- und Delete-Suites.

## 13. S10 – G3 Review

Der finale Review wird als neuer datierter Snapshot angelegt:

```text
docs/reviews/YYYY-MM-DD-g3-gate-review.md
```

Er referenziert finalen `main` SHA, CI-Runs, die fuenf E2E-Flows und offene Findings und endet mit:

```text
G3: BESTANDEN
```

oder

```text
G3: NICHT BESTANDEN
```

G3 benoetigt keine vollstaendigen Web-/Android-Referenzflows. Systematische Client-Paritaet, Accessibility, Read Cache, Export/Import und Performance bleiben M5/G4.

## 14. Abhaengigkeitsgraph

```text
G2 BESTANDEN + #146
        |
        v
S1 Wish
  |
  v
S2 Plan + Conversion
  |
  +------> S3 Place
  |           |
  |           v
  |        S4 Relations
  |           |
  |           v
  |        S5 Chapter
  |
  +------> S6 Shared Collections
  |
  +------> S7 PrivateNote/GiftIdea
              |
              v
           S8 PrivateCollection

S2 + S3 + S4 + S5 + S6 + S7 + S8
              |
              v
           S9 E2E
              |
              v
           S10 G3
```

S3/S6/S7 koennen nach Runtime-Freigabe teilweise parallelisiert werden, solange ihre Schema-/Migrationen sauber koordiniert bleiben.