# M3 Technical Readiness Package

**Status:** S0-Entscheidungen abgeschlossen; keine automatische Runtime-Freigabe  
**Stand:** 26.08.2026  
**Tracking:** #159, #162, #163, #164, #165

Dieses Paket bereitet **M3 – Shared Life / Planen & Private Area** technisch und fachlich vor. Die M3-S0-Entscheidungen sind abgeschlossen. Runtime-Code, Migrationen und produktiver OpenAPI-Vertrag werden weiterhin erst in den jeweiligen Runtime-Slices umgesetzt.

## Gate-Regel

Die Planung durfte vor Abschluss von G2 erfolgen. **Der Abschluss der M3-S0-Decisions gibt M3-Runtime nicht automatisch frei.**

Runtime-Arbeit beginnt nach der aktuell dokumentierten Projektregel erst, wenn:

1. der finale G2-Review G2 ausdruecklich als `BESTANDEN` bewertet (#147),
2. der anschliessende Status-Sync #146 M3 als freigegebenen Milestone fuehrt,
3. der betroffene REST-/OpenAPI-Vertrag fuer den jeweiligen Runtime-Slice contract-testbar konkretisiert ist.

Alle M3-D01 bis M3-D32 stehen inzwischen auf `DECIDED`; damit ist die fachliche S0-Readiness kein zusaetzlicher Blocker mehr.

## Verbindliche Quellen und Vorrang

Bei Widerspruechen gilt:

1. `specification/CLEAN-ROOM-MASTER-SPEC.md`
2. `specification/PRODUCT-SPEC.md`
3. `docs/SECURITY.md`
4. veroeffentlichter OpenAPI-Vertrag
5. `docs/INFORMATION-ARCHITECTURE.md`, `docs/USER-FLOWS.md`, `docs/API-UI-CONTRACTS.md`
6. explizit `DECIDED`e M3-Decision-Dokumente
7. uebrige Readiness-Entwuerfe in `docs/m3/`

**Wichtig:** Aeltere `OPEN`-/`PROPOSED`-Formulierungen in `DOMAIN-MODEL.md` oder `API-DESIGN.md` sind Readiness-Historie. Fuer inzwischen entschiedene Punkte gelten das aktuelle [Decision Log](./DECISION-LOG.md) und die Decision-Dokumente verbindlich.

## Scope M3

| Bereich | M3-Inhalt | Privacy-Grundlage |
|---|---|---|
| Wish | gemeinsame Wuensche und atomarer Wish->Plan-Lifecycle | `SPACE_SHARED` |
| Plan | konkrete Planung, Termine, Completion, optionaler Ursprung aus Wish | `SPACE_SHARED` |
| Place | gemeinsamer Ort, Koordinaten optional, keine Providerpflicht | `SPACE_SHARED`, Ortsdaten sensibel |
| Content Relations | typisierte Relationen mit echten FKs | Target-Autorisierung bleibt verbindlich |
| Chapter | Buendel bestehender Memories, SHARED HeartMoments und Milestones | `SPACE_SHARED` |
| Collection | gemeinsame Liste mit Items, Completion und atomarem Reorder | `SPACE_SHARED` |
| PrivateNote | private persoenliche Notiz | `OWNER_ONLY` |
| GiftIdea | private Geschenkidee | `OWNER_ONLY` |
| PrivateCollection | private Liste und Items | `OWNER_ONLY` |

Shared Planning, gemeinsame Collections und Private Area bleiben eigenstaendige Domänenmodelle. Es gibt keine Universal-Tabelle fuer alle Inhalte.

## S0-Entscheidungen

### #162 – Wish / Plan

[`decisions/WISH-PLAN-LIFECYCLE.md`](./decisions/WISH-PLAN-LIFECYCLE.md)

Festgelegt sind u. a.:

- collaborative write;
- Wish-/Plan-Statusautomaten;
- atomare, idempotente Wish->Plan-Konvertierung;
- Return-to-Wish;
- Direct Plan Create;
- Datumsinvarianten;
- Delete-/Concurrency-Matrix.

### #163 – Place / Relations / Chapters

[`decisions/PLACE-RELATIONS-CHAPTERS.md`](./decisions/PLACE-RELATIONS-CHAPTERS.md)

Festgelegt sind u. a.:

- Schutz und Praezision von Ortsdaten;
- keine automatische Place-Deduplizierung;
- typisierte Relationstabellen;
- `Plan.placeId` und `Chapter.placeId` als kanonische Single-Place-FKs;
- keine Relations auf private Targets;
- abgeleitete Chapter-Reihenfolge;
- Relation-/Delete-/Privacy-Races.

### #164 – Collections / Private Area

[`decisions/COLLECTIONS-PRIVATE-AREA.md`](./decisions/COLLECTIONS-PRIVATE-AREA.md)

Festgelegt sind u. a.:

- Shared Collection Write-/Versionierungsmodell;
- atomarer Reorder;
- Parent-Child-Delete;
- ProtectedPayload-Grenzen der Private Area;
- GiftIdea `IDEA | BOUGHT | GIVEN`;
- PrivateCollection Root-/Item-Schema;
- owner-scoped `/private/...` API;
- redigierter M3-Eventvertrag.

### #165 – G3 / Clientgrenzen

[`decisions/G3-CLIENT-BOUNDARIES.md`](./decisions/G3-CLIENT-BOUNDARIES.md)

Festgelegt sind u. a.:

- G3 als Domain/API/PostgreSQL-Gate;
- fuenf reale HTTP-E2E-Pflichtflows;
- vollstaendige Client-Paritaet/Accessibility erst M5/G4;
- Export-/Cache-Privacy-Grenzen fuer spaetere Implementierung;
- Private Area als sekundaerer `Mein Bereich`;
- Plan-Checklist/Medien bewusst spaeter;
- Multi-select nur als Clientzustand.

## Weitere Readiness-Dokumente

- [Domain Model](./DOMAIN-MODEL.md) – urspruenglicher Modell-/Risikoentwurf; bei entschiedenen Punkten gelten die Decision-Dokumente
- [API Design](./API-DESIGN.md) – urspruengliche API-Zielflaeche; konkrete Operationssemantik wird durch Decisions gebunden und spaeter in OpenAPI ueberfuehrt
- [Decision Log](./DECISION-LOG.md) – aktuelle kompakte Matrix aller M3-D01 bis D32
- [Privacy Threat Model](./PRIVACY-THREAT-MODEL.md) – Tenant-, Owner-only-, Relation- und Location-Leaks
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md) – negative Pfade, Races und Privacy-Evidenz
- [Delivery Plan](./DELIVERY-PLAN.md) – vertikale Runtime-Slices nach Gate-Freigabe

## Nicht in M3 vorziehen

- globale Volltextsuche / allgemeines Search Read Model – M4-A;
- Dashboard, Activity, Notifications, Reminders und Rules – M4;
- vollstaendige Web-/Android-Produktisierung, Paritaet, Read Cache, Export/Import, Deep Links, umfassende Accessibility/Performance – M5/G4;
- Questions, Check-in und Recaps – M6;
- Discovery-, Shopping-, Rezept-, Event- und andere Provider – M7;
- Maps-/Geocoding-Provider, Geofencing, Presence und aktiver Standortkontext – M7/M8;
- ShoppingList/ShoppingItem – eigene spaetere Domain;
- echte E2EE – MX;
- Video – Future-Backlog #88;
- Plan-Checklist und Plan-Attachments – spaeterer expliziter Scope.

`Place` in M3 bedeutet Domain + gespeicherte Ortsdaten + Relationen, nicht Adresssuche, Kartenansicht oder Geocoding.

## Definition of Ready fuer einen M3-Runtime-Slice

Ein Slice ist ready, wenn:

- [ ] G2 formal bestanden und M3 ueber #146 freigegeben ist;
- [x] relevante BLOCKING-Decisions `DECIDED` sind;
- [x] Modellfelder, Privacy-Klasse, Ersteller/Eigentuemer und Schreibrechte fachlich feststehen;
- [x] Status-/Delete-/Relation-/Concurrency-Grenzen fuer den betroffenen M3-Kern feststehen;
- [ ] produktiver Request/Response-/OpenAPI-Vertrag fuer den konkreten Slice umgesetzt bzw. eindeutig contract-testbar ist;
- [x] Cross-Tenant-/Privacy-/Race-Pflichttests vorab spezifiziert sind;
- [x] Event-Payload keine sensiblen Klartexte benoetigt;
- [ ] Reuse-before-build fuer technische Commodity-Funktionalitaet im konkreten Runtime-PR erfolgt, sofern relevant.

## G3-Ziel

G3 verlangt nach M3-Runtime mindestens:

- konsistente Wishes/Plans/Places/Chapters/Collections;
- vollstaendige Private-Area-Isolation;
- deterministische Delete-/409-/Race-Wirkungen;
- fuenf reale HTTP/PostgreSQL-E2E-Flows gemaess `G3-CLIENT-BOUNDARIES.md`;
- keine offenen High/Critical Security-/Privacy-Findings und keinen Tenant-/OWNER_ONLY-Leak.

Der finale G3-Review ist ein neuer datierter Snapshot unter `docs/reviews/` und endet explizit mit `G3: BESTANDEN` oder `G3: NICHT BESTANDEN`.