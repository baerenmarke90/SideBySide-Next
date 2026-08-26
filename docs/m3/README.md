# M3 Technical Readiness Package

**Status:** Planung vor G3, keine Runtime-Freigabe  
**Stand:** 26.08.2026  
**Tracking:** #159

Dieses Paket bereitet **M3 – Shared Life / Planen & Private Area** technisch und fachlich vor. Es enthält ausschließlich Planungs- und Entscheidungsgrundlagen. Runtime-Code, Migrationen, produktiver OpenAPI-Vertrag, Web-/Android-Produktflächen und CI bleiben in diesem Slice unberührt.

## Gate-Regel

Die Planung darf vor Abschluss von G2 erfolgen. **M3-Runtime darf daraus nicht vorzeitig abgeleitet werden.**

Runtime-Arbeit beginnt erst, wenn:

1. der finale G2-Review G2 ausdrücklich als `BESTANDEN` bewertet (#145 -> #147),
2. der anschließende Status-Sync #146 M3 als freigegebenen Milestone führt,
3. alle für den konkreten Runtime-Slice relevanten `BLOCKING`-Entscheidungen in [DECISION-LOG.md](./DECISION-LOG.md) auf `DECIDED` stehen,
4. der betroffene REST-/OpenAPI-Vertrag vor Implementierung eindeutig und contract-testbar festgelegt ist.

Ein Planungs-PR darf deshalb gemergt werden, ohne M3 freizugeben. Er reduziert nur die Zahl der Fragen, die später während der Implementierung entstehen könnten.

## Verbindliche Quellen und Vorrang

Bei Widersprüchen gilt die bestehende Projekthierarchie:

1. `specification/CLEAN-ROOM-MASTER-SPEC.md`
2. `specification/PRODUCT-SPEC.md`
3. `docs/SECURITY.md`
4. veröffentlichter OpenAPI-Vertrag
5. `docs/INFORMATION-ARCHITECTURE.md`, `docs/USER-FLOWS.md`, `docs/API-UI-CONTRACTS.md`
6. dieses Readiness-Paket

Dieses Paket **schließt keine fachliche Lücke stillschweigend**. Aussagen sind entweder:

- **SOURCE-BOUND** – durch eine höher priorisierte Quelle vorgegeben,
- **DECIDED** – durch eine dokumentierte M3-Entscheidung verbindlich,
- **PROPOSED** – bevorzugter Ansatz, aber noch nicht bindend,
- **OPEN** – bewusst ungelöst.

## Scope M3

| Bereich | M3-Inhalt | Privacy-Grundlage |
|---|---|---|
| Wish | gemeinsame Wünsche, Status `OPEN/PLANNED/COMPLETED`, Autor/Ersteller, Versionierung | `SPACE_SHARED` |
| Plan | konkrete Planung, Status `IDEA/PLANNED/COMPLETED`, Zeitbezug, optionale Herkunft aus Wish | `SPACE_SHARED` |
| Place | wiederverwendbarer gemeinsamer Ort, Koordinaten optional | `SPACE_SHARED`; genaue Ortsdaten sensibel behandeln |
| Content Relations | typisierte Relationen mit referentieller Integrität | Zielressource bleibt autorisierungsbestimmend |
| Chapter | Bündel bestehender Memories, geteilter HeartMoments und Milestones | gemeinsamer Space-Inhalt |
| Collection | frei definierbare gemeinsame Listen und sortierte Items | `SPACE_SHARED` |
| PrivateNote | private persönliche Notiz | `OWNER_ONLY` |
| GiftIdea | private Geschenkidee | `OWNER_ONLY` |
| PrivateCollection | private Liste und private Items | `OWNER_ONLY` |

Die Master-/Produktspezifikation verbietet eine Universal-Tabelle für diese Fachbereiche. Shared Planning, gemeinsame Collections und Private Area bleiben deshalb eigenständige Domänenmodelle.

## Bereits durch die Spezifikation festgelegt

Folgende Grenzen gelten nicht als offene Produktentscheidung:

- Wish und Plan sind im aktuellen Core gemeinsame `SPACE_SHARED`-Inhalte.
- Private Ablage ist **keine private Variante von Wish, Plan oder Collection**, sondern besitzt eigene `OWNER_ONLY`-Modelle.
- Wish und Plan sind getrennte Domainobjekte.
- Der fachliche Ablauf führt von Wish über Plan zu `COMPLETED` und optional zu einem Chapter.
- Ein nicht abgeschlossener Plan kann grundsätzlich wieder in einen Wunschzustand zurückgeführt werden; die genaue Transaktionssemantik ist noch zu entscheiden.
- Place darf ohne Koordinaten gespeichert werden.
- Places können fachlich mit Memories, HeartMoments, Milestones, Plans und Chapters verbunden werden.
- Content Relations sollen intern nach Möglichkeit echte Foreign Keys und typisierte Relationstabellen verwenden; eine unkontrollierte `(targetType, targetId)`-Universalrelation ohne Referential Integrity ist ausgeschlossen.
- Chapter bündelt bestehende Inhalte. Das Löschen eines Chapters entfernt Relationen, **nicht** die Originalinhalte.
- Collection/CollectionItem ist die generische gemeinsame Listen-Domain.
- ShoppingList/ShoppingItem ist später eine eigene Domain und wird nicht als Collection vorgezogen.
- PrivateNote, GiftIdea, PrivateCollection und PrivateCollectionItem sind `OWNER_ONLY`; der Partner darf ihre Existenz auch nicht indirekt über ID, Suche, Dashboard, Link oder API-Manipulation erfahren.

## Inhalt des Pakets

- [Domain Model](./DOMAIN-MODEL.md) – Modelle, Lifecycle, Relationen, Ownership und Delete-Grenzen
- [API Design](./API-DESIGN.md) – vorgeschlagene REST-Fläche, Transitions, Fehler und Concurrency
- [Decision Log](./DECISION-LOG.md) – offene und bereits source-bound Entscheidungen
- [Privacy Threat Model](./PRIVACY-THREAT-MODEL.md) – Tenant-, Owner-only-, Relation- und Location-Leaks
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md) – negative Pfade, Races und Privacy-Evidenz
- [Delivery Plan](./DELIVERY-PLAN.md) – kleine vertikale Slices mit Abhängigkeiten und Gate-Regeln

## Nicht in M3 vorziehen

M3 darf nicht zum Sammelmilestone werden. Ausdrücklich außerhalb dieses Pakets bzw. der M3-Runtime liegen:

- globale Volltextsuche und Search Read Model – M4-A,
- Dashboard, Activity, Notifications, Reminders und Rules – M4,
- vollständige Web-/Android-Produktisierung, systematische Parität, Read Cache, Export/Import und umfassende Deep-Link-/Offline-Härtung – M5,
- Questions, Check-in und Recaps – M6,
- Discovery-, Shopping-, Rezept-, Event- und andere externe Provider – M7,
- Maps-/Geocoding-Provider, Geofencing, Presence und aktiver Standortkontext – M7/M8,
- ShoppingList/ShoppingItem – spätere eigene Domain,
- echte E2EE – MX,
- Video – Future-Backlog #88.

`Place` in M3 bedeutet daher **Domain + gespeicherte Ortsdaten + Relationen**. Es bedeutet nicht, dass M3 bereits Adresssuche, Kartenansicht, Geocoding oder Standortprovider integrieren muss.

## Definition of Ready für einen M3-Runtime-Slice

Ein Slice ist erst ready, wenn:

- [ ] G2 formal bestanden und M3 über #146 freigegeben ist,
- [ ] relevante `BLOCKING`-Decisions `DECIDED` sind,
- [ ] Modellfelder, Privacy-Klasse, Ersteller/Eigentümer und Schreibrechte feststehen,
- [ ] Statusübergänge und ungültige Übergänge feststehen,
- [ ] Delete-/Cascade-/Relation-Auswirkungen feststehen,
- [ ] Request/Response, Fehlercodes und `If-Match`-/409-Verhalten feststehen,
- [ ] Cross-Tenant- und Privacy-negativtests spezifiziert sind,
- [ ] relevante Races/Idempotenzfälle spezifiziert sind,
- [ ] Event-Payload keine sensiblen Klartexte benötigt,
- [ ] Reuse-before-build für technische Commodity-Funktionalität durchgeführt ist, sofern relevant,
- [ ] keine spätere M4/M5/M7/M8-Funktion als versteckte Voraussetzung eingebaut wird.

## Definition of Done für Runtime

Die projektweite DoD bleibt bestehen: Datenmodell, Migration, Domain Service, Autorisierung, API/OpenAPI, Validierung, Fehlercodes, Unit-/PostgreSQL-Integrationstests, Cross-Tenant-/Privacy-Tests, Concurrency, Dokumentation sowie die für den Milestone vereinbarte Client-/Gate-Evidenz gehören zusammen.

Ein Endpoint allein ist ebenso wenig fertig wie ein UI-Screen ohne serverseitige Privacy-Grenze.

## Offene Kernfragen

Die wichtigsten Risiken vor Codebeginn sind nicht CRUD, sondern Semantik:

1. Wer darf gemeinsame Wish/Plan/Place/Chapter/Collection-Inhalte ändern oder löschen?
2. Wie wird Wish -> Plan atomar, idempotent und race-sicher modelliert?
3. Was bedeutet die Rückführung eines Plans zu Wish für Identitäten, Historie und Status?
4. Welche Datums-/Statuskombinationen sind bei Plan gültig?
5. Welche Relationstabellen werden in M3 tatsächlich ausgeliefert und wie reagieren sie auf Delete/Privacy-Wechsel?
6. Welche Reihenfolge und Concurrency gilt für Chapter- und Collection-Items/Relationen?
7. Wie werden genaue Ortsdaten klassifiziert, geloggt und später exportiert/gecached?
8. Welche Statuswerte besitzt GiftIdea? Die Master-Spezifikation nennt ein Feld `status`, aber keinen Enum.
9. Welche minimale Client-Evidenz verlangt G3, ohne M5 vorwegzunehmen?

Diese Fragen sind im Decision Log explizit erfasst; kein Runtime-PR darf sie nebenbei beantworten.
