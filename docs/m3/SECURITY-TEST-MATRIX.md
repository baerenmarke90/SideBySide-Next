# M3 Security Test Matrix

**Status:** verbindliche Readiness-Matrix; konkrete Erwartungswerte folgen Decisions  
**Stand:** 26.08.2026

Diese Matrix legt fest, welche Testklassen ein M3-Slice mindestens benötigt. Sie ersetzt keine Slice-spezifischen Tests, verhindert aber, dass Tenant-, Owner-only-, Relation- oder Race-Fälle erst beim Gate auffallen.

## 1. Testebenen

| Ebene | Zweck |
|---|---|
| Domain Unit | Statusautomaten, Validierung, sichere pure Regeln |
| PostgreSQL Integration | Constraints, FKs, Locks, Races, Cascades, Tenant-/Owner-Queries |
| HTTP Integration | echte Auth/Membership/API/Problem-Details/ETag-Semantik |
| Contract/OpenAPI | DTOs, Enums, Fehlercodes, generierbarer Vertrag |
| Client/Gate | gemäß M3-D24; keine implizite Annahme vor Decision |

SQLite ist kein Ersatz für PostgreSQL-Race-/Constraint-Evidenz.

## 2. Gemeinsame Tenant-Matrix

Für **Wish, Plan, Place, Chapter, Collection** mindestens:

| Fall | Erwartung |
|---|---|
| aktives Mitglied, eigener Space, GET | erlaubt |
| aktives Mitglied, eigener Space, List | nur eigener Space |
| ID aus fremdem Space in eigenem Pfad | privacy-sicher 404 |
| fremde `spaceId` ohne Membership | 404/standardisierte Tenant-Antwort |
| Mutation gegen fremden Space | keine Zeilenänderung |
| Delete gegen fremden Space | keine Zeilenänderung |
| Cursor/Filter aus anderem Space | nicht wiederverwendbar / keine Fremddaten |

Die konkrete Partner-Write-Erwartung hängt von M3-D01 ab und wird nach Decision ergänzt.

## 3. Wish

### CRUD / Concurrency

- Create setzt `createdBy` aus Auth Context, nicht Request.
- Request kann `createdBy`, `spaceId`, `version` nicht überschreiben.
- Update mit aktueller Version erfolgreich.
- stale Update -> 409, keine Teiländerung.
- stale Delete -> 409, sofern Delete versioniert ist.
- ungültiger Statuspatch wird nicht als normaler Update akzeptiert, falls Transition-API beschlossen wird.

### Wish -> Plan

Pflichtfälle:

1. OPEN Wish -> Plan erfolgreich.
2. Wish + Plan in derselben DB-Transaktion sichtbar.
3. Fehler nach Plan-Insert vor Wish-Update -> kompletter Rollback.
4. zwei parallele Konvertierungen -> exakt gemäß M3-D02, niemals zwei unerlaubte Plans.
5. identischer Retry nach erfolgreichem Commit -> deterministische Idempotenz-/Conflict-Semantik.
6. stale `If-Match` -> kein Plan erzeugt.
7. fremder Space Wish -> 404.
8. Place aus fremdem Space im Conversion-Request -> 404, kein Plan.
9. Wish-Delete parallel zur Konvertierung -> genau eine fachlich zulässige Reihenfolge gewinnt.

## 4. Plan

### Status

Für jede mit M3-D04 erlaubte Kante:

- Happy Path,
- stale Version,
- doppelte Transition,
- ungültige Quell-/Zielkombination,
- Datumsvalidierung,
- Cross-Space Place,
- Partner-Write gemäß M3-D01.

Für jede verbotene Kante expliziter negativer Test.

### Completion

- `COMPLETED` setzt/validiert `experiencedOn` gemäß Decision.
- parallele Completion ist idempotent oder deterministischer Conflict.
- Completion gegen Return-to-Wish wird serialisiert.
- Completion ändert source Wish nur gemäß expliziter Decision; keine implizite Cascade.

### Return-to-Wish

Nach M3-D03 testen:

- nur zulässige nicht abgeschlossene States,
- Verhalten mit/ohne `sourceWishId`,
- keine stille Payload-Überschreibung,
- Plan-/Wish-Versionen konsistent,
- Race mit Plan-Update/Delete/Complete.

## 5. Place

### Validation

- Place ohne Koordinaten erlaubt.
- Koordinaten außerhalb erlaubter Grenzen abgewiesen.
- Paarigkeit/Null-Semantik gemäß M3-D06.
- Adresse/Description nicht in Fehler-/Audit-/Event-Logs.

### Tenant / Write

- Cross-Space CRUD negativ.
- Partner-Write gemäß M3-D01.
- keine automatische Deduplizierung zweier ähnlich benannter Places, falls M3-D07 bestätigt wird.

### Delete / Relation

- Delete gegen bestehende Relation gemäß M3-D05/D26.
- Delete vs. concurrent relation-create mit echtem PostgreSQL-Race.
- keine dangling FK-Zeile.

## 6. Content Relations

Für **jeden tatsächlich freigegebenen Relationstyp** dieselbe Basismatrix:

| Fall | Erwartung |
|---|---|
| Parent + Target gleicher Space, autorisiert | Link möglich |
| Parent fremder Space | 404 |
| Target fremder Space | 404 |
| Target unbekannt | 404 |
| Target owner-only/nicht lesbar | 404, keine Existenzauskunft |
| Duplicate Link | deterministischer Conflict/Idempotenz gemäß Contract |
| Unlink nicht vorhanden | definierte sichere Semantik |
| Target delete | Joinzeile gemäß FK/Lifecycle entfernt oder Delete blockiert |
| Parent delete | Joinzeile entfernt |
| Relation create vs target delete | kein Phantomlink |
| Relation create vs privacy revoke | kein privater Link nach Commit |

### HeartMoment Privacy Race

Pflicht-PostgreSQL-Test:

1. gemeinsamer HeartMoment ist `SHARED`;
2. Transaktion A versucht Relation zu Chapter/Place;
3. Transaktion B setzt HeartMoment `PRIVATE`;
4. nach beiden Commits darf kein gemeinsames Read Model/Relation die Existenz des privaten HeartMoments verraten.

## 7. Chapter

### CRUD

- Tenant matrix.
- `startOn/endOn` gemäß M3-D11.
- Partner-Write gemäß M3-D01.
- stale update/delete -> 409.

### Delete-Invariante

Pflichttest:

1. Chapter mit Memory, shared HeartMoment und Milestone verknüpfen.
2. Chapter löschen.
3. Joinzeilen sind entfernt.
4. Memory, HeartMoment und Milestone existieren unverändert weiter.
5. ihre Versionen werden durch Chapter-Delete nicht erhöht.
6. keine Delete-Events für Targets.

### Private Target

- Versuch, private HeartMoment-ID zu verknüpfen -> sichere 404.
- Partner kann aus Chapter-Count/Response keinen privaten Targetbestand ableiten.

## 8. Collection / CollectionItem

### Shared Ownership

Nach M3-D13:

- Ersteller-/Partneraktionen jeweils positiv/negativ,
- `createdBy` nicht manipulierbar,
- Cross-Space Parent-ID.

### Completion

- Item Completion mit aktueller Version/Parent-Version.
- stale Completion -> 409.
- paralleles Toggle -> kein Lost Update.

### Reorder

Pflichtfälle unabhängig von gewählter Strategie:

- gültiger kompletter Reorder,
- unbekannte Item-ID,
- Item aus anderer Collection,
- duplicate Item-ID im Order-Request,
- fehlende IDs, falls vollständige Liste verlangt wird,
- Reorder vs Item Delete,
- zwei parallele Reorders,
- Reorder vs Item Create,
- keine doppelten/ungültigen Positionen nach Commit.

### Parent Delete

Nach M3-D15:

- Collection delete behandelt eigene Items wie beschlossen,
- keine Auswirkungen auf Shopping oder andere Domainobjekte,
- keine orphaned Items.

## 9. PrivateNote

Pflichtmatrix:

| Actor | Operation | Erwartung |
|---|---|---|
| Owner | create/list/get/update/delete | erlaubt |
| Partner im selben Space | list | ausschließlich eigene Notes; nie Owner-Notes des Partners |
| Partner mit fremder Note-ID | get/update/delete | identisches 404 |
| Account ohne Space-Membership | alle | 404/tenant denial |
| Owner anderer Space | get via falschen Space | 404 |

Zusätzlich:

- `ownerId` nur aus Auth Context.
- Request kann Privacy nicht zu shared ändern.
- Titel/Body nicht in Domain Event.
- Titel/Body nicht in Audit/Logrepräsentation.
- stale update/delete -> 409.

## 10. GiftIdea

Wie PrivateNote plus:

- jeder Enumwert nach M3-D17 positiv getestet,
- unbekannter Status -> Validation Error,
- `url` wird gespeichert, aber **kein ausgehender HTTP-Request** durch Backend/Worker ausgelöst,
- URL/recipient/occasion/priceText nicht in Events/Logs,
- Partner erhält keine GiftIdea Counts/Existenzhinweise.

Ein Test kann einen absichtlich nicht erreichbaren/internen URL-Wert speichern und bestätigen, dass kein Netzwerkzugriff Teil der Operation ist.

## 11. PrivateCollection / PrivateCollectionItem

### Owner Isolation

- Owner CRUD/List.
- Partner sieht in seiner privaten Liste ausschließlich eigene private Collections.
- Partner-ID-Zugriff auf fremde PrivateCollection/Item -> identisches 404.
- Item kann nicht aus fremder PrivateCollection referenziert werden.
- Cross-Space negative cases.

### Reorder / Completion

Dieselbe Concurrency-Matrix wie Shared Collection, aber zusätzlich:

- kein gemeinsamer Positionsraum,
- keine IDs des Partnerbestands in Conflict-/Validation-Details,
- Parent-Owner-Bedingung Teil jeder Child-Query.

## 12. Privacy-Leak-Matrix

Für jede `OWNER_ONLY`-Domain prüfen:

- GET by ID
- List
- pagination/cursor
- Count, falls vorhanden
- Sortierung
- Fehlerdetails
- relation create/unlink
- Deep-Link/API direct navigation soweit Client vorhanden
- Events
- Audit
- Logs/Error Tracking
- Export später als Contract-Test-Merkpunkt
- Search später als M4-Merkpunkt

Negative Tests sollen nicht nur Statuscodes, sondern auch Response Body/Form vergleichen, wo Existenzleaks möglich wären.

## 13. Event-/Outbox-Tests

Für jeden event-produzierenden M3-Slice:

- Event und Domainmutation atomar.
- Rollback -> kein Event.
- Event enthält nur M3-D23-Envelope.
- JSON-Snapshot enthält keine fachlichen Titel/Texte.
- keine Adresse/lat/lon.
- keine GiftIdea URL/recipient/priceText.
- keine PrivateNote/Collection-Titel.
- Retry des Consumers erzeugt keine doppelte fachliche Wirkung.

## 14. Delete-/Cascade-Races

Pflicht-Races:

- Wish Delete vs Convert-to-Plan.
- Plan Delete vs Complete.
- Place Delete vs Relation Create.
- Chapter Delete vs Relation Create.
- Target Delete vs Chapter/Place Link.
- Collection Delete vs Item Create/Reorder.
- PrivateCollection Delete vs Item Create/Reorder.

Tests müssen echte unabhängige PostgreSQL-Transaktionen verwenden, nicht nur sequentielle Service-Aufrufe.

## 15. API-/OpenAPI-Tests

Jeder M3-API-Slice:

- generiertes OpenAPI deterministisch,
- keine ungewollten freien string enums für statusartige Felder,
- `If-Match` dokumentiert,
- 409 dokumentiert,
- privacy-sicheres 404 dokumentiert,
- unknown fields/contract rules wie Projektstandard,
- Web-/Android-Generator bleibt lauffähig, sobald Clientfläche den Vertrag konsumiert.

## 16. G3 Evidence Checklist

Die exakte Gate-Form wird M3-D24 entscheiden. Unabhängig davon sollten folgende Server-Evidenzen vorliegen:

- [ ] Wish->Plan echter HTTP/PostgreSQL-Flow inklusive Race.
- [ ] Plan lifecycle mit allen erlaubten/verbotenen Transitions.
- [ ] Place + mindestens ein freigegebener Relationstyp über echte API.
- [ ] Chapter Delete erhält alle Originaltargets.
- [ ] Collection reorder/complete concurrency.
- [ ] PrivateNote/GiftIdea/PrivateCollection owner-only negative matrix.
- [ ] Cross-Space Relation Tests.
- [ ] Private HeartMoment kann nicht über M3-Relation leaken.
- [ ] Events/Logs enthalten keine sensiblen M3-Payloads.
- [ ] OpenAPI/PostgreSQL/CI vollständig grün.
- [ ] zusätzliche Client-/Accessibility-Evidenz gemäß M3-D24.

## 17. Merge-Regel

Ein Runtime-PR, der eine neue M3-Domain oder Relation einführt, ist nicht merge-ready, wenn die zugehörige Zeile dieser Matrix weder umgesetzt noch als nachweislich nicht relevant begründet ist.
