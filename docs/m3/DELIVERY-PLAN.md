# M3 Delivery Plan

**Status:** Planungsentwurf – keine Runtime-Freigabe  
**Stand:** 26.08.2026

## 1. Gate vor Runtime

Dieser Delivery Plan beschreibt die **Reihenfolge nach Freigabe**, nicht die aktuelle Erlaubnis zur Implementierung.

Vor dem ersten M3-Runtime-Commit müssen:

1. #145 abgeschlossen sein,
2. #147 G2 auf aktuellem `main` als `BESTANDEN` bewerten,
3. #146 die aktiven Statusquellen synchronisieren und M3 freigeben,
4. die für den ersten M3-Slice relevanten `BLOCKING`-Decisions auf `DECIDED` stehen.

Die S0-Planung selbst darf vorher abgeschlossen werden.

## 2. Zielbild

M3 liefert die fachliche Grundlage für den gemeinsamen Alltag:

```text
Wish --------> Plan --------> Completed
                  |               |
                  |               +------> optional Chapter
                  |
                  +------> Place

Memory ---------+
HeartMoment ----+----> typed relations ----> Chapter / Place
Milestone ------+

Shared Collections

PrivateNote / GiftIdea / PrivateCollection
              |
              +---- OWNER_ONLY, vollständig getrennt
```

M3 ist kein vollständiger Client-Completion-Milestone. Welche minimale Client-/E2E-Evidenz G3 braucht, wird vor Runtime-Ende mit M3-D24 explizit entschieden.

## 3. S0 – Readiness und Decisions

### S0-A – Domain/Lifecycle Decisions

Schließt mindestens:

- M3-D01 Shared Write Ownership,
- M3-D02 Wish->Plan Kardinalität/Idempotenz,
- M3-D03 Return-to-Wish,
- M3-D04 Plan Lifecycle,
- M3-D05 Wish/Plan Delete,
- M3-D30 Direct Plan Create.

**Ergebnis:** Wish/Plan können implementiert werden, ohne Produktsemantik im Code zu erfinden.

### S0-B – Place/Relation/Chapter Decisions

Schließt mindestens:

- M3-D06/D28 Location-Klassifizierung,
- M3-D07 Place Identity,
- M3-D08/D09 Relationfläche und Privacy,
- M3-D10/D11 Chapter Ordering/Dates,
- M3-D26 Relation Races,
- M3-D31 Chapter/Place Wahrheitsquelle.

### S0-C – Collections/Private Area Decisions

Schließt mindestens:

- M3-D13/D14/D15 Collection Aggregate,
- M3-D16 Private ProtectedPayload,
- M3-D17 GiftIdea Status,
- M3-D18/D32 PrivateCollection Persistenz/Auth,
- M3-D19 Private API,
- M3-D23 Events.

### S0-D – Gate-/Client-Grenzen

Vor dem ersten stabilen Client-Slice bzw. spätestens deutlich vor G3:

- M3-D21 Export,
- M3-D22 Cache,
- M3-D24 G3 Evidence,
- M3-D25 Private IA,
- M3-D27 Plan Richness,
- M3-D29 Multi-select.

Nicht alle `BEFORE_CLIENTS`-Decisions müssen den ersten Backend-Slice blockieren.

## 4. S1 – Wish Foundation

### Scope

- Wish DB-Modell + Migration,
- `OPEN/PLANNED/COMPLETED`-Enum gemäß finaler Decision,
- ProtectedPayload-Klassifizierung,
- CRUD/List API,
- Author/Shared-Write-Regel,
- `If-Match`/409,
- Tenant Guard,
- sichere Events,
- PostgreSQL-/HTTP-/Cross-Tenant-Tests.

### Nicht in S1

- Plan,
- Konvertierung,
- Place,
- globale Suche,
- Web-/Android-Produktisierung.

### Exit

- Wish ist als eigenständige Shared-Domain belastbar.
- Keine Statusmutation umgeht späteren Wish->Plan-Vertrag.

## 5. S2 – Plan Foundation + Wish->Plan

### Scope

- Plan DB-Modell + Migration,
- Direct Plan Create gemäß M3-D30,
- Plan CRUD/List,
- erlaubte Statusübergänge,
- Datumsinvarianten,
- `sourceWishId`,
- atomare Wish->Plan-Operation,
- Idempotenz/Unique Constraint/Row-Lock gemäß M3-D02,
- Return-to-Wish gemäß M3-D03, falls im M3-MVP beschlossen,
- Completion,
- PostgreSQL-Race-Tests.

### Kritischer Nachweis

```text
HTTP Wish Create
-> Wish->Plan
-> exactly one Plan
-> Wish state consistent
-> Plan Complete
```

Parallel Double-Submit muss deterministisch sein.

## 6. S3 – Place Foundation

### Scope

- Place Modell + Migration,
- name/description/address/lat/lon nach M3-D06/D28,
- CRUD/List,
- Koordinaten optional,
- keine Provider-/Geocoding-Integration,
- Tenant/Write/Concurrency,
- Event-/Log-Redaction.

### Exit

Place ist eine vollständig nutzbare Domainressource ohne Kartenabhängigkeit.

## 7. S4 – Typisierte Content Relations

### Startbedingung

M3-D08, D09, D26 und betroffene Write-Regeln `DECIDED`.

### Scope

Nur die in S0 ausdrücklich freigegebenen Relationstypen. Kandidaten mit hohem M3-Nutzen:

- Plan <-> Place,
- Chapter <-> Memory,
- Chapter <-> shared HeartMoment,
- Chapter <-> Milestone,
- Chapter <-> Place / kanonische Alternative nach D31.

Weitere mögliche Master-Spec-Relationen werden nicht automatisch umgesetzt.

### Technische Regeln

- eigene FK-Tabellen,
- Unique Constraints,
- kein freies `(targetType,targetId)`,
- same-space enforcement,
- Target Authorization,
- private HeartMoment nicht relationierbar im Shared-Kontext,
- Delete/Privacy-Races PostgreSQL-basiert getestet.

## 8. S5 – Chapter

### Scope

- Chapter Modell + Migration,
- CRUD/List,
- Datumsregeln,
- Place-Verknüpfung gemäß D31,
- freigegebene typed relations,
- Chapter Delete entfernt ausschließlich Relationstabellen,
- keine Original-Cascade,
- Concurrency/Write Policy,
- Tests.

### Kritischer Exit-Test

```text
Chapter + Memory + HeartMoment + Milestone
-> DELETE Chapter
-> relations gone
-> all original resources unchanged
```

## 9. S6 – Gemeinsame Collections

### Scope

- Collection + CollectionItem Modell,
- Ownership/Write Policy,
- CRUD,
- Completion,
- atomarer Reorder,
- Position-/Versionierungsstrategie,
- Parent-Delete gemäß D15,
- Cross-Tenant + Concurrency.

### Nicht enthalten

- ShoppingList,
- Rezeptlisten als eigene Shoppingfunktion,
- Providerinhalte,
- private Collections.

PrivateCollection bleibt bewusst eigener Slice, damit Shared-/Owner-only-Querypfade nicht vermischt werden.

## 10. S7 – PrivateNote + GiftIdea

### Warum gemeinsam, aber getrennte Tabellen

Beide nutzen dieselbe Owner-only-Sicherheitsfläche und sind klein genug für einen gemeinsamen Privacy-Härtungsslice. Fachlich bleiben sie getrennte Modelle/Services/Routen.

### Scope

- PrivateNote Modell/CRUD,
- GiftIdea Modell/CRUD mit entschiedenem Statusenum,
- `PrivateResourceMixin`/zentrale Owner-Autorisierung soweit passend,
- ProtectedPayload,
- owner-scoped Lists,
- privacy-sicheres 404,
- keine externen URL-Fetches,
- Event-/Log-Redaction,
- Partner-Negativtests.

### Exit

Für beide Domänen wird bewiesen, dass der Partner weder Inhalt noch Existenz über API/Listen/Events erkennen kann.

## 11. S8 – PrivateCollection

### Scope

- PrivateCollection + Item Modell,
- owner-only Parent/Child Query,
- Completion/Reorder,
- Position/Version nach D18,
- Parent-Delete,
- Cross-Space/Partner-Negativmatrix,
- keine Shared Collection Wiederverwendung als Tabelle.

### Kritischer Exit

Shared Collection und PrivateCollection dürfen trotz ähnlicher UX nicht dieselbe Privacy-Query oder denselben Positionsraum verwenden.

## 12. S9 – M3 integrierter Backend/API-Nachweis

Dieser Slice ergänzt keine neue Fachfunktion, sondern führt die M3-Ketten zusammen.

Mindestens:

1. Wish erstellen.
2. atomar in Plan überführen.
3. Place anlegen/zuordnen.
4. Plan abschließen.
5. Chapter anlegen und vorhandene Story-Inhalte relationieren.
6. Chapter löschen und Originale erhalten.
7. Shared Collection erstellen/reordern.
8. PrivateNote/GiftIdea/PrivateCollection als Owner nutzen.
9. Partner-negative Private-Area-Aufrufe beweisen.
10. Cross-Space Relation und Race-Suites laufen.

Der Nachweis läuft gegen reale SideBySide-API + PostgreSQL, nicht nur gegen Mocks.

## 13. S10 – G3 Evidence / Review Vorbereitung

Startet nur nach M3-D24.

Mögliche Artefakte:

- reproduzierbare E2E-Harnesses,
- datierte Security-/Privacy-Evidenz,
- ggf. dünne Web-/Android-Referenzflows, falls G3 dies verlangt,
- Gate-Matrix,
- keine Umschreibung historischer Reviews.

Danach eigener G3-Review als datierter Snapshot.

## 14. Abhängigkeitsgraph

```text
G2 BESTANDEN + #146
        |
        v
     M3-S0
        |
        +------> S1 Wish
        |          |
        |          v
        |       S2 Plan + conversion
        |          |
        |          +------+
        |                 |
        +------> S3 Place |
        |          |      |
        |          v      v
        +------> S4 Relations
                    |
                    v
                 S5 Chapter

S0-C ------> S6 Shared Collections
   |
   +-------> S7 PrivateNote/GiftIdea
   |            |
   +----------> S8 PrivateCollection

S1..S8 ----> S9 integrated evidence
                 |
                 v
              S10 G3
```

S6/S7 können nach ihren Decisions parallel zu Place/Chapter laufen, solange sie keine gemeinsam geänderten Grundlagen konfliktträchtig anfassen.

## 15. Empfohlene Issue-Struktur nach S0

Nach Abschluss der Decisions sollte **jeder Slice ein eigenes Issue + Branch + PR** erhalten:

```text
[M3-S1][Wish] Wish Foundation liefern
[M3-S2][Plan] Plan und atomaren Wish->Plan-Lifecycle liefern
[M3-S3][Place] Place Foundation ohne Providerabhängigkeit liefern
[M3-S4][Relations] Typisierte M3-Content-Relations liefern
[M3-S5][Chapter] Chapters und sichere Relation-Lifecycles liefern
[M3-S6][Collections] Gemeinsame Collections und atomaren Reorder liefern
[M3-S7][Private] PrivateNote und GiftIdea owner-only liefern
[M3-S8][Private] PrivateCollections owner-only liefern
[M3-S9][Gate] M3-Backend/API-E2E und Security-Evidenz konsolidieren
[M3-G3][Gate] G3 formal prüfen
```

Keine Sammel-PRs über mehrere dieser Slices.

## 16. Parallelisierungsregeln

Parallel zulässig, wenn:

- keine gemeinsame offene Decision betroffen ist,
- keine konkurrierenden Migrationen dieselbe Tabelle/Enum anfassen,
- Relation-Slice nicht vor Parent/Target-Modellen startet,
- Private Area nicht denselben Shared-Aggregate-Code zu einer generischen Universalabstraktion umbaut.

Nicht sinnvoll parallel:

- S1 Wish und S2 Plan vor finalem Conversion-Vertrag,
- S3 Place und S4 Relation, wenn Place-Schema noch offen ist,
- S6 Shared Collection und S8 PrivateCollection über eine gemeinsame generische Persistenzschicht, bevor Privacy-Modell geprüft ist.

## 17. Scope-Schutz gegen Milestone Creep

Wenn während M3 folgende Wünsche auftauchen, werden sie **nicht** in den aktuellen Slice gezogen:

- Volltextsuche -> M4-A,
- Dashboard-Karten -> M4-A,
- Notifications bei Planänderung -> M4-B,
- Erinnerungen an Plantermine -> M4-C,
- vollständige Navigation/Deep Links/Offline Cache -> M5,
- Fragen/Recaps -> M6,
- Restaurant-/Event-/Shoppingprovider -> M7,
- Kartenanbieter/Geocoding/Geofencing -> M7/M8,
- Link Preview für GiftIdea -> eigenes späteres Security-/Provider-Issue,
- Plan-Checklist/Plan-Attachments -> nur nach M3-D27/gesondertem Scope.

## 18. G3 – vorgeschlagene fachliche Exit Criteria

Die endgültige Gate-Definition wird M3-D24 entscheiden. Als Readiness-Baseline sollte G3 mindestens verlangen:

- Wish/Plan Lifecycle einschließlich Double-Submit/Races konsistent,
- Places und freigegebene Relationen cross-tenant sicher,
- Chapters löschen keine Originalinhalte,
- gemeinsame Collections konfliktfrei editierbar/reorderbar gemäß Write Policy,
- PrivateNote/GiftIdea/PrivateCollection vollständig owner-only,
- keine Owner-only-Leaks über relation/count/error/event,
- OpenAPI + PostgreSQL-Suites grün,
- keine sensiblen Location-/Private-Payloads in Telemetrie,
- Delete-/409-Auswirkungen im vereinbarten Client-/Gate-Nachweis verständlich,
- M4-Read-Model-Grenzen werden nicht durch M3-Datenmodell blockiert.

## 19. Reihenfolge direkt nach diesem Readiness-PR

Solange G2 noch offen ist:

1. #159 Readiness-Paket reviewen/mergen,
2. M3-S0-Decisions als getrennte Decision-Issues schließen,
3. **keinen M3-Runtime-Code starten**,
4. parallel #145 abschließen,
5. #147 finalen G2-Review,
6. #146 Status-Sync,
7. erst dann M3-S1 starten.

Damit ist nach G2 keine erneute Grundsatzphase nötig; die erste Runtime-Arbeit kann direkt auf entschiedenem Vertrag beginnen.
