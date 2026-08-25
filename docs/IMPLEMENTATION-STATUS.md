# Umsetzungsstand

Stand: 25. August 2026  
Aktueller `main`: `76f5f086e1228662c22147590d5e85eac70e6fb4`  
Aktueller Gate-Status: **G1 bestanden; M2-S0 freigegeben und aktiv**

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Aktuelle Gate-Entscheidung:** [2026-08-25-g1-gate-review-after-61.md](reviews/2026-08-25-g1-gate-review-after-61.md)
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

## M2-S0 — Readiness & Vertragsentscheidungen

**Status: aktiv. Runtime-Code noch gesperrt, bis die für den jeweiligen Slice relevanten BLOCKING-Decisions geschlossen sind.**

### Aktuelle Issue-Kette

- [ ] **#67 — Planning:** G1-Status, Roadmap und Milestone-Grenzen synchronisieren.
- [ ] **#68 — Domain/Privacy:** Memory-, Comment- und Privacy-Entscheidungen schließen.
- [ ] **#69 — Media:** Attachment-Lifecycle, Limits, Validation und Retention entscheiden.
- [ ] **#70 — API:** Routen, DTOs, Concurrency, Pagination und Story-Sortierung festlegen.
- [ ] **#71 — erster Runtime-Slice:** Memory CRUD ohne Medien; blockiert durch #67/#68/#70.

Nach Merge von #67 können #68 und #69 parallel bearbeitet werden. #70 übernimmt die freigegebenen Entscheidungen in den versionierten Contract. #71 startet erst, wenn seine relevanten S0-Abhängigkeiten erfüllt sind.

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

Globale Volltextsuche ist nicht automatisch Teil von G2. Der Story-Mindestvertrag beginnt mit `type`, `year`, `order`, `cursor` und `limit`; `q` wird nur nach explizitem Privacy-/Index-Review in #70 in M2 aufgenommen, sonst M4-A.

## Geplante M2-Runtime-Reihenfolge nach S0

1. Memory CRUD ohne Medien (#71)
2. Attachment Foundation / MediaStore Contract
3. HeartMoment Privacy
4. Memory + mehrere Medien
5. Milestone
6. Comments + Outbox/Notification Hook
7. Story Read Model
8. dünne Web-/Android-Referenzflows
9. G2 Review

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
