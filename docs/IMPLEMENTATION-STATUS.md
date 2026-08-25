# Umsetzungsstand

Stand: 25. August 2026  
Aktueller `main`: `f20b257` (Merge von #118)  
Aktueller Gate-Status: **G1 bestanden; M2-S0 abgeschlossen; M2-Runtime läuft**

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Aktuelle Gate-Entscheidung:** [2026-08-25-g1-gate-review-after-61.md](reviews/2026-08-25-g1-gate-review-after-61.md)
- **Verbindliche Entwicklungsregel:** [REUSE-BEFORE-BUILD.md](REUSE-BEFORE-BUILD.md) und [AGENTS.md](../AGENTS.md)
- **Architektur-/Betriebsentscheidungen:** datierte ADRs unter [docs/decisions](decisions)
- **M2-Steuerung:** [m2/PROJECT-CONTROL.md](m2/PROJECT-CONTROL.md)
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

### Offene M1-/Betriebshärtungen ohne M2-Blockade

- [ ] **#59 — Pre-Exposure:** Passkey-Authentication-Start gegen Challenge-Flooding absichern.
- [ ] **#60 — Pre-Exposure:** Rate-Limit-Schwellen unter Parallelität atomar erzwingen.
- [ ] **#25 — Repository-Hardening:** Branch Protection/Ruleset technisch erzwingen, sobald GitHub-Plan/Targeting dies ermöglicht.

#59 und #60 müssen vor öffentlicher/Managed-Exposition geschlossen sein. Sie blockieren interne M2-Domainarbeit nicht.

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

Offen bleiben ausschließlich `BEFORE_CLIENTS`-Entscheidungen, die erst vor stabiler Web-/Android-Integration fällig sind: M2-D10 (Notification Preview), M2-D17 (Export/Backup), M2-D18 (Client-Cache) und M2-D21 (Suchindex). Sie blockieren keinen Backend-Slice.

M2-D22 (Owner-Ansicht) gehört nicht mehr dazu: die Frage formt die Story-Route und wurde deshalb mit #104 auf `BLOCKING` gehoben und entschieden — genau wie zuvor M2-D14 und M2-D15 in #78.

## M2 — Runtime

**Status: laufend.**

- [x] **#71 — Memory CRUD ohne Medien** (PR #77): Memory-Domain mit ProtectedPayload für Titel/Body, author-only writes bei gemeinsamer Lesbarkeit, `If-Match`/409, signierter Keyset-Cursor und `resourceVersion` im Outbox-Envelope.
- [x] **#80 — HeartMoment mit Owner-only-Privacy** (PR #84): erster Typ mit echter Nutzerentscheidung zur Sichtbarkeit; `SHARED -> PRIVATE` als eigene atomare Operation, Emotion als ProtectedPayload.
- [x] **#79 — Attachment-Lifecycle für Bilder** (PR #89): Statusautomat, LocalMediaStore, asynchrone Validierung mit Metadaten-Entfernung und Thumbnail, autorisiertes Lesen, Retention und Cleanup.
- [x] **#90 — Attachments an Memory und HeartMoment binden** (PR #93): `MemoryAttachment` mit stabiler `position`, HeartMoment mit höchstens einem Attachment, atomares Bind/Unbind gegen das Bindungsfenster aus M2-D20 und keine Cross-Space-Bindung.
- [x] **#94 — Milestone-Domain und API** (PR #95): eigenständiges Modell statt Typflag auf Memory, Autorregel nach M2-D25, `If-Match`/409 und Story-taugliche Felder.
- [x] **#97 — Comments, Outbox und Notification Hook** (PR #98): Create/List am Parent verschachtelt, Update/Delete space-scoped, enumerierte Targets `MEMORY`/`MILESTONE`/`HEART_MOMENT`, atomarer Outbox-Eintrag und idempotenter Retry.
- [x] **#87 — S3-kompatibler MediaStore-Adapter** (PR #100): presigned Upload und Read-URL mit den TTLs aus M2-D13, geprüft gegen denselben Contract-Test wie der lokale Adapter.
- [ ] **#88 — Video und Posterframes:** klärt vorher die ffmpeg-Frage. Ein Branch mit Vorarbeit existiert; ein Pull Request steht noch aus.
- [x] **#113 — Story Read Model und `/timeline`** (PR #114): abgeleitete Zeitleiste über Memory, Milestone und ausschließlich gemeinsame HeartMoments; Sortierschlüssel und Keyset-Cursor nach M2-D08, private HeartMoments nie im Ergebnis — auch nicht für ihren Owner (M2-D22). Keine Story-Tabelle.
- [ ] **S8 — dünne Web-/Android-Referenzflows:** letzter M2-Baustein vor dem G2-Nachweis. Arbeitspaket noch anzulegen.

Damit ist die M2-Domain vollständig. Für G2 fehlt allein der End-to-End-Nachweis auf Web und Android.

Video bleibt bis #88 nach M2-D23 fail-closed: M2-D04 erlaubt MP4 und QuickTime, der Server weist sie mit `ATTACHMENT_TYPE_NOT_ALLOWED` ab. Clients dürfen Video in M2 solange nicht als verfügbar anbieten.

Die Details und verbindlichen Milestone-Grenzen stehen in [M2 Project Control](m2/PROJECT-CONTROL.md).

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

Globale Volltextsuche ist nicht Teil von G2. Der Story-Mindestvertrag umfasst `type`, `year`, `order`, `cursor` und `limit`. #70 hat `q` nicht aufgenommen (M2-D08); globale Volltextsuche liegt damit in M4-A.

## M2-Runtime-Reihenfolge nach S0

1. ~~Memory CRUD ohne Medien (#71)~~ — geliefert
2. ~~Attachment Foundation / MediaStore Contract (#79)~~ — geliefert, Bilder
3. ~~HeartMoment Privacy (#80)~~ — geliefert
4. ~~Memory + mehrere Medien (#90)~~ — geliefert
5. ~~Milestone (#94)~~ — geliefert
6. ~~Comments + Outbox/Notification Hook (#97)~~ — geliefert
7. ~~Story Read Model (#113)~~ — geliefert
8. dünne Web-/Android-Referenzflows
9. G2 Review

Der S3-Adapter (#87) und der Videoslice (#88) laufen daneben und sind nicht Teil dieser Kette; #87 ist geliefert, #88 offen.

Der Memory-Slice kommt bewusst vor Media, um zuerst M2-Migrationstil, ProtectedPayload, Tenant Guard, Autorregel und Concurrency auf einer kleineren Sicherheitsfläche zu validieren.

## G2 — Story Alpha, Exit Criteria

G2 kann erst bestanden werden, wenn:

- Memory, Attachment/Media, HeartMoment, Milestone und Comment für M2 vollständig sind,
- Story niemals `OWNER_ONLY` vor Suche/Gruppierung/Pagination passieren lässt,
- Media-/Upload-Abuse, Parent-Autorisierung und relevante Races geprüft sind,
- OpenAPI, Migrationen und PostgreSQL-Integrationstests grün sind,
- mindestens ein kritischer Memory/Media/Story-Flow in Web und Android Ende-zu-Ende validiert ist,
- diese Referenzflows Privacy-/Accessibility-Abnahme ohne hohe Befunde bestehen.

Vollständige Client-Parität ist **kein** G2-Kriterium; sie gehört zu M5/G4.

## Spätere Milestones

- [ ] M3 — Wishes, Plans, Places, Chapters, Collections, Private Area
- [ ] M4 — Search/Dashboard, Activity/Notifications, Reminders/Rules
- [ ] M5 — Client Completion & Parity, Export/Import, Read Cache
- [ ] M6 — Questions, Check-in, Monats-/Jahresrückblicke
- [ ] M7 — Integrationen/Provider
- [ ] M8 — Location/Context mit explizitem Opt-in
- [ ] M9 — Productization, Managed-/Self-Hosted-Policy, Backup, Entitlements, Launch-Hardening
- [ ] MX — echte E2EE als eigener späterer Security-Milestone

## Nächster Prüfpunkt

#67 vollständig abschließen und mergen. Danach #68 und #69 als getrennte S0-Decision-Slices bearbeiten. #70 übernimmt anschließend die freigegebenen Entscheidungen in den API-Vertrag. Erst danach darf #71 als erster produktiver M2-Runtime-Slice starten.
