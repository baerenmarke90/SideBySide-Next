# Umsetzungsstand

Stand: 27. August 2026  
Aktueller Repository-Stand: GitHub `main` ist die kanonische SHA-Quelle; dieses Living-Status-Dokument speichert bewusst keinen statischen Current-SHA.  
Aktueller Gate-Status: **G2 bestanden; M2 abgeschlossen; M3 freigegeben**

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Aktuelle Gate-Entscheidung:** [2026-08-26-g2-final-gate-review.md](reviews/2026-08-26-g2-final-gate-review.md)
- **Statusquellen und Drift-Regeln:** [STATUS-SOURCES.md](STATUS-SOURCES.md)
- **Verbindliche Entwicklungsregel:** [REUSE-BEFORE-BUILD.md](REUSE-BEFORE-BUILD.md) und [AGENTS.md](../AGENTS.md)
- **Architektur-/Betriebsentscheidungen:** datierte ADRs unter [docs/decisions](decisions)
- **M2-Steuerung:** [m2/PROJECT-CONTROL.md](m2/PROJECT-CONTROL.md)
- **M3-Readiness und Delivery:** [m3/README.md](m3/README.md) und [m3/DELIVERY-PLAN.md](m3/DELIVERY-PLAN.md)
- **Historische Reviews:** datierte Dateien unter `docs/reviews/`; sie werden nicht nachträglich geändert.
- **Dieses Dokument:** laufende Arbeits- und Fortschrittsliste.

Bei Widersprüchen gilt die Master-Spezifikation. Eine neue Gate-Entscheidung erhält immer einen neuen datierten Review.

## Arbeitsregeln

1. Nur dieses Repository bearbeiten.
2. Vor jeder Umsetzung einschlägige Spezifikation, Decision Log und aktuelle Issues lesen.
3. Ein Issue = ein klarer Scope = eigener Branch/PR.
4. Keine direkten Änderungen auf `main`, kein Rebase, kein Force Push.
5. Vor Merge aktuellen `main`, PR-HEAD, vollständigen Diff, Mergeability und CI frisch prüfen.
6. Findings außerhalb des Scopes als eigenes Issue erfassen.
7. Historische Reviews nicht umschreiben.
8. Vor Eigenbau technischer Commodity-Funktionalität die Reuse-Prüfung nach [REUSE-BEFORE-BUILD.md](REUSE-BEFORE-BUILD.md) durchführen und im Issue oder PR dokumentieren. Ein relevanter PR ohne nachvollziehbare Prüfung ist nicht merge-ready; CI erzwingt die Entscheidung.

## M0 — Foundation

**Status: abgeschlossen.**

- [x] FastAPI, SQLAlchemy 2, PostgreSQL, Alembic
- [x] REST API v1, camelCase, Problem Details
- [x] UUIDv7 und Zeit-/Datums-Konventionen
- [x] Transactional Outbox und PostgreSQL-Job-Queue
- [x] MediaStore-/Provider-Abstraktionen
- [x] ProtectedPayload-Grundabstraktion
- [x] reproduzierbare Dependencies und Lockfile
- [x] OpenAPI-Contract + Contract-Check
- [x] PostgreSQL-Integrationstests
- [x] Dependency-/Vulnerability-Scan, Container-Build, Secret Scan, Provenance

## M1 — Identity & Relationship

**Status: Runtimeumfang abgeschlossen; G1 bestanden.**

- [x] Account, AccountEmail, AuthIdentity
- [x] lokaler Passwortlogin mit Argon2
- [x] Device Sessions und rotierende Tokens
- [x] Space, Membership, zentraler Tenant Guard
- [x] race-sichere Invitations
- [x] SpaceProfile mit ETag/If-Match und 409
- [x] PartnerProfile und ProfilePreference
- [x] RelatedPerson und ImportantDate
- [x] zentrale SQL-seitige `SPACE_SHARED`-/`OWNER_ONLY`-Autorisierung
- [x] OIDC Authorization Code + PKCE/State/Nonce/Discovery/JWKS
- [x] OIDC-Invite-Onboarding ohne E-Mail-Merge
- [x] Passkey/WebAuthn Registration und Authentication
- [x] Magic Link, E-Mail-Verifikation und Recovery
- [x] Refresh-Replay-Schutz
- [x] #61: RelatedPerson-Löschung mit expliziter `preserve`-/`cascade`-Policy ohne destruktiven Default
- [x] G1 Gate Review nach #61: **BESTANDEN**

### Abgeschlossene M1-/Repository-Härtungen

- [x] **#59 — Pre-Exposure:** Passkey-Authentication-Start gegen Challenge-Flooding abgesichert.
- [x] **#60 — Pre-Exposure:** Rate-Limit-Schwellen werden unter Parallelität atomar erzwungen.
- [x] **#25 — Repository-Hardening:** aktives Ruleset für `main` erzwingt Pull Request, Merge Commit, aktuelle Pflichtchecks, keine Force Pushes und keine Branch-Löschung.

Damit sind die zuvor im Living Status als offen geführten Pre-Exposure-/Repository-Härtungen abgeschlossen. GitHub bleibt für den jeweiligen Issue-Zustand die operative Quelle.

### Betrieb: Self-Hosted-Startpfad

- [x] **#110 — Startpfad und Migration entkoppelt** (PR #111): `alembic upgrade head` hängt nicht mehr an Cursor-Signing-Key, SMTP und öffentlicher Adresse; Compose trennt Migrations- von Runtime-Konfiguration; CI fährt den realen Startpfad statt ihn nur zu parsen.
- [x] **#115 — Netzwerk- und Portbereitschaft gehärtet** (PR #118): ein belegter API-Port und ein fehlender Netzwerkpfad hinterlassen die Instanz nicht mehr als scheinbar funktionsfähig; eigener Deployment-Guard in CI.

Zwei Betriebszusagen daraus sind verbindlich und stehen in [ADR 0002](decisions/0002-self-hosted-first-start-mode.md):

- Der mitgelieferte Compose-Stack startet als **klar markierter lokaler Testbetrieb**. Echter Betrieb verlangt `SBS_ENVIRONMENT=production` in `.env`; die Anwendung meldet ihren Betriebsmodus bei jedem Start.
- Ein SMTP-Zugang ist **keine Startvoraussetzung**. `SBS_MAIL_TRANSPORT=none` ist in Produktion zulässig; die mailabhängigen Anmeldewege antworten dann `503 MAIL_TRANSPORT_UNAVAILABLE`, Anmeldung läuft über Passwort, Passkey und OIDC. `log` bleibt in Produktion verboten.

## M2-S0 — Readiness & Vertragsentscheidungen

**Status: abgeschlossen.** Alle `BLOCKING`-Entscheidungen im [Decision Log](m2/DECISION-LOG.md) sind `DECIDED`.

- [x] **#67 — Planning:** G1-Status, Roadmap und Milestone-Grenzen synchronisiert.
- [x] **#68 — Domain/Privacy:** Memory-, Comment- und Privacy-Entscheidungen geschlossen.
- [x] **#69 — Media:** Attachment-Lifecycle, Limits, Validation und Retention entschieden.
- [x] **#70 — API:** Routen, DTOs, Concurrency, Pagination und Story-Sortierung festgelegt.
- [x] **#78 — Media-Metadaten:** EXIF-/GPS-Strippen beim Ingest und Variantenumfang entschieden (M2-D14/D15).

Offen bleiben ausschließlich `BEFORE_CLIENTS`-Entscheidungen, die vor stabiler Vollintegration relevant werden: M2-D10 (Notification Preview), M2-D17 (Export/Backup), M2-D18 (Client-Cache) und M2-D21 (Suchindex). Sie blockierten G2 nicht und werden in den zuständigen späteren Milestones behandelt.

M2-D22 (Owner-Ansicht) gehört nicht mehr dazu: die Frage formt die Story-Route und wurde deshalb mit #104 auf `BLOCKING` gehoben und entschieden — genau wie zuvor M2-D14 und M2-D15 in #78.

## M2 — Runtime und G2

**Status: abgeschlossen; G2 bestanden.**

- [x] **#71 — Memory CRUD ohne Medien** (PR #77): Memory-Domain mit ProtectedPayload für Titel/Body, author-only writes bei gemeinsamer Lesbarkeit, `If-Match`/409, signierter Keyset-Cursor und `resourceVersion` im Outbox-Envelope.
- [x] **#80 — HeartMoment mit Owner-only-Privacy** (PR #84): erster Typ mit echter Nutzerentscheidung zur Sichtbarkeit; `SHARED -> PRIVATE` als eigene atomare Operation, Emotion als ProtectedPayload.
- [x] **#79 — Attachment-Lifecycle für Bilder** (PR #89): Statusautomat, LocalMediaStore, asynchrone Validierung mit Metadaten-Entfernung und Thumbnail, autorisiertes Lesen, Retention und Cleanup.
- [x] **#90 — Attachments an Memory und HeartMoment binden** (PR #93): `MemoryAttachment` mit stabiler `position`, HeartMoment mit höchstens einem Attachment, atomares Bind/Unbind gegen das Bindungsfenster aus M2-D20 und keine Cross-Space-Bindung.
- [x] **#94 — Milestone-Domain und API** (PR #95): eigenständiges Modell statt Typflag auf Memory, Autorregel nach M2-D25, `If-Match`/409 und Story-taugliche Felder.
- [x] **#97 — Comments, Outbox und Notification Hook** (PR #98): Create/List am Parent verschachtelt, Update/Delete space-scoped, enumerierte Targets `MEMORY`/`MILESTONE`/`HEART_MOMENT`, atomarer Outbox-Eintrag und idempotenter Retry.
- [x] **#87 — S3-kompatibler MediaStore-Adapter** (PR #100): presigned Upload und Read-URL mit den TTLs aus M2-D13, geprüft gegen denselben Contract-Test wie der lokale Adapter.
- [x] **#113 — Story Read Model und `/timeline`** (PR #114): abgeleitete Zeitleiste über Memory, Milestone und ausschließlich gemeinsame HeartMoments; Sortierschlüssel und Keyset-Cursor nach M2-D08, private HeartMoments nie im Ergebnis — auch nicht für ihren Owner (M2-D22). Keine Story-Tabelle.
- [x] **S8 — dünne Web-/Android-Referenzflows:** Web und Android liefern den kritischen Memory/Media/Story-Referenzpfad.
- [x] **#144 — realer G2-Client-E2E-Nachweis:** Web und Android laufen gegen denselben realen SideBySide-Stack aus API, Worker, PostgreSQL und LocalMediaStore.
- [x] **#147 / PR #170 — finaler G2 Gate Review:** **G2: BESTANDEN**.

### Future-Backlog außerhalb von M2/G2

- [ ] **#88 — Video-Uploads und Posterframes:** zukünftige Entwicklung, nicht jetzt implementieren. Der Prototyp #109 wurde wegen eines Produktions-Images von rund 755 MiB sowie des zusätzlichen ffmpeg-Betriebs-, Supply-Chain- und Security-Aufwands bewusst ohne Merge geschlossen.

Video bleibt bis zu einer neuen Produktentscheidung fail-closed: M2-D04 erlaubt MP4 und QuickTime im Zielvertrag, der aktuelle Server weist sie mit `ATTACHMENT_TYPE_NOT_ALLOWED` ab. Clients dürfen Video nicht als verfügbar anbieten.

Die historische M2-Steuerung und verbindlichen Milestone-Grenzen stehen in [M2 Project Control](m2/PROJECT-CONTROL.md). Die aktuelle Gate-Entscheidung steht im [finalen G2 Gate Review](reviews/2026-08-26-g2-final-gate-review.md).

### Verbindliche M2/M5-Grenze

M2 ist **Domain + API + minimale vertikale Web-/Android-Referenzflows**. Diese Referenzflows dienen dem technischen E2E-Nachweis des kritischen Memory/Media/Story-Kerns und bedeuten keine vollständige Client-Parität.

M5 ist **Client Completion & Parity**: vollständige Clientintegration, Deep Links, Read Cache, Export/Import, systematische Web-/Android-Parität, Accessibility und Performance.

### Privacy-Begriffe

- `SHARED` / `PRIVATE`: öffentliche fachliche Domainwerte.
- `SPACE_SHARED` / `OWNER_ONLY`: interne Authorization-/Privacy-Klassen.
- Clients schreiben `privacyClass` nicht redundant.

### M4-Abgrenzung

M4 wird intern in drei Delivery-Slices geteilt:

- M4-A Search + Dashboard Read Models
- M4-B Activity + Notifications
- M4-C Reminders + Rules

Globale Volltextsuche war nicht Teil von G2. Der Story-Mindestvertrag umfasst `type`, `year`, `order`, `cursor` und `limit`; globale Volltextsuche liegt in M4-A.

## M2-Runtime-Reihenfolge nach S0

1. ~~Memory CRUD ohne Medien (#71)~~ — geliefert
2. ~~Attachment Foundation / MediaStore Contract (#79)~~ — geliefert, Bilder
3. ~~HeartMoment Privacy (#80)~~ — geliefert
4. ~~Memory + mehrere Medien (#90)~~ — geliefert
5. ~~Milestone (#94)~~ — geliefert
6. ~~Comments + Outbox/Notification Hook (#97)~~ — geliefert
7. ~~Story Read Model (#113)~~ — geliefert
8. ~~dünne Web-/Android-Referenzflows~~ — geliefert
9. ~~G2 Review~~ — **BESTANDEN**

Der S3-Adapter (#87) lief daneben und ist geliefert. Video (#88) ist nicht Teil dieser Kette oder von M2/G2, sondern Future-Backlog.

## G2 — Story Alpha

**Status: BESTANDEN.** Verbindliche Entscheidungsquelle ist der [finale G2 Gate Review](reviews/2026-08-26-g2-final-gate-review.md).

Nachgewiesen sind M2-Domain/API, Story-Privacy, Media-/Parent-Autorisierung, Cross-Tenant-/Race-/Datenintegrität, OpenAPI, Migrationen, PostgreSQL-Integration sowie ein realer kritischer Memory/Media/Story-Flow in Web und Android gegen denselben SideBySide-Stack.

Die manuelle Accessibility-Abnahme wurde bewusst aus G2 in die finale Client-/Release-QA verschoben. Sie gilt **nicht** als bestanden und bleibt Bestandteil von M5/G4. Vollständige Client-Parität ist ebenfalls M5/G4.

## M3 — Planen & Private Area

**Status: freigegeben.** Das [M3 Technical Readiness Package](m3/README.md) ist vorbereitet; alle M3-D01 bis M3-D32 stehen auf `DECIDED`.

Die Runtime-Reihenfolge folgt dem [M3 Delivery Plan](m3/DELIVERY-PLAN.md). Ein konkreter Slice startet erst, wenn sein produktiver Request/Response-/OpenAPI-Vertrag eindeutig contract-testbar ist und Reuse-before-build sowie die normalen PR-/CI-Gates erfüllt sind.

- [x] **M3-S1 — Wish Foundation:** Wish-Domain mit ProtectedPayload für den Titel, collaborative write nach M3-D01, `status` ausschließlich serverseitig, `If-Match`/409, Statusfilter über einen space- und filtergebundenen Cursor sowie redigierte `WISH_*`-Events. Die Wish->Plan-Operation und die planabhängigen Zeilen der Delete-Matrix folgen in S2.
- [x] **M3-S2 — Plan + Wish->Plan:** Plan-Domain mit Direct Create nach M3-D30, Statusautomat `IDEA | PLANNED | COMPLETED` mit Datumsinvarianten als Service- **und** DB-Constraints, `sourceWishId` mit `UNIQUE` und zusammengesetztem Same-Space-Fremdschlüssel, atomare und idempotente Wish->Plan-Konvertierung, `return-to-wish`, `schedule`/`unschedule`/`complete` sowie die kanonische Lock-Reihenfolge `Wish -> Plan` mit echten PostgreSQL-Race- und Rollback-Tests. Die Wish-Delete-Matrix aus M3-D05 ist damit vollständig.
- [x] **M3-S3 — Place Foundation:** Place-Domain mit Name, Beschreibung und Adresse hinter der ProtectedPayload-Grenze, Koordinaten als typisierte `NUMERIC`-Spalten mit Paar-, Bereichs- und Genauigkeitsinvarianten in Dienst **und** Schema, CRUD/List ohne Deduplizierung, kein Geocoding- oder Maps-Provider. `Plan.placeId` ist nachgezogen (kanonisch und einspaltig, mit zusammengesetztem Same-Space-Fremdschlüssel). Place-Delete löst zugeordnete Plans versioniert und lässt sie bestehen. Zusätzlich: gebundene DB-Parameter erscheinen nicht mehr in Fehlermeldungen und damit nicht mehr im Anwendungslog.
- [x] **M3-S4 — typisierte Content Relations:** `place_memories`, `place_heart_moments` und `place_milestones` mit echten zusammengesetzten Fremdschlüsseln über `(id, space_id)`, Primärschlüssel `(place_id, target_id)` und typisierten REST-Routen statt freier `(targetType,targetId)`-Polymorphie. Same-Space ist eine Schemaeigenschaft, keine Dienstregel: beide Fremdschlüssel teilen sich dieselbe `space_id`-Spalte. Unbekanntes, gelöschtes, fremdes und privates Ziel enden ununterscheidbar in `RELATION_TARGET_NOT_FOUND`. Der Privacy-Wechsel `SHARED -> PRIVATE` entfernt die Relationen in derselben Transaktion; darunter liegt ein Schema-Riegel, der den Zustand „privat mit gemeinsamer Relation" unformulierbar macht. Lock-Reihenfolge `Place -> Target` mit PostgreSQL-Race-Tests gegen Parent-Delete, Target-Delete und Privacy-Wechsel.
- [ ] **M3-S5 — Chapter:** nächster Runtime-Slice. Bringt `Chapter.placeId` und die drei `chapter_*`-Relationen nach.
- [ ] M3-S6+ — Collections und Private Area gemäß Delivery Plan.

## Spätere Milestones

- [ ] M4 — Search/Dashboard, Activity/Notifications, Reminders/Rules
- [ ] M5 — Client Completion & Parity, Export/Import, Read Cache, finale Accessibility-QA
- [ ] M6 — Questions, Check-in, Monats-/Jahresrückblicke
- [ ] M7 — Integrationen/Provider
- [ ] M8 — Location/Context mit explizitem Opt-in
- [ ] M9 — Productization, Managed-/Self-Hosted-Policy, Backup, Entitlements, Launch-Hardening
- [ ] MX — echte E2EE als eigener späterer Security-Milestone

## Nächster Prüfpunkt

M3-S5 **Chapter** nach dem [M3 Delivery Plan](m3/DELIVERY-PLAN.md). Der Slice bringt das Chapter-Modell mit `startOn`/`endOn` nach M3-D11, die abgeleitete chronologische Darstellung nach M3-D10 sowie `Chapter.placeId` und die drei `chapter_*`-Relationen — letztere auf derselben Join-Form, die S4 für Places geliefert hat.

Chapter-Delete entfernt nach M3-D12 ausschließlich das Chapter und seine Relationen; kein Memory, HeartMoment oder Milestone darf dabei verschwinden.
