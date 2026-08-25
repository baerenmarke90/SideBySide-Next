# Umsetzungsstand

Stand: 25. August 2026  
Aktueller G1-Prüfstand: `main` bei Commit `6bc2cc955da04933e0957be2f19ce14d29e59755`

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Unveränderlicher Ausgangsreview:** [2026-08-24-spec-gap-review.md](reviews/2026-08-24-spec-gap-review.md)
- **Historischer G1-Snapshot:** [2026-08-24-g1-m1-security-review.md](reviews/2026-08-24-g1-m1-security-review.md)
- **Aktueller G1-Follow-up-Review:** [2026-08-25-g1-m1-follow-up-review.md](reviews/2026-08-25-g1-m1-follow-up-review.md)
- **Dieses Dokument:** laufende, kurze Arbeits- und Fortschrittsliste

Bei Widersprüchen gilt die Master-Spezifikation. Datierte Dateien unter
`docs/reviews/` werden nicht nachträglich korrigiert; ein neuer Prüfstand
bekommt eine neue Datei.

## Arbeitsregeln für die Weiterentwicklung

1. Keine Vorgänger-Repositories öffnen, durchsuchen oder als Vorlage verwenden.
2. Vor jeder Umsetzung die einschlägigen Abschnitte der Master-Spezifikation lesen.
3. Sicherheits- und Tenant-Invarianten vor neuen Inhaltsdomänen stabilisieren.
4. Nach jedem Block Tests, Lint, Typprüfung, `git diff --check` und `git status` prüfen.
5. Nur dieses Statusdokument fortschreiben; historische Reviews unverändert lassen.

### Parallele Arbeit mit mehreren Implementierungsagenten

- GitHub Issues sind die verbindliche Einheit für Arbeitsumfang und Abnahme.
- Ein Agent bearbeitet einen klar abgegrenzten Issue-Scope auf einer eigenen Branch/PR.
- Zwei Agenten sollen nicht gleichzeitig denselben Issue oder dieselben Kern-Dateien verändern.
- Vor Merge/Übergabe wird gegen den aktuellen `main` abgeglichen; Konflikte werden nicht durch Force Push aufgelöst.
- Direkte Pushes auf `main` werden organisatorisch vermieden, solange GitHub sie für dieses private Repository tarifbedingt nicht technisch blockieren kann.
- Neue Findings werden als eigenes Issue erfasst, statt den Scope eines laufenden Issues still zu erweitern.

## G1/M1 – aktueller Stand

Der [G1/M1 Follow-up Security Review vom 25.08.2026](reviews/2026-08-25-g1-m1-follow-up-review.md) prüft `main` bei `6bc2cc955da04933e0957be2f19ce14d29e59755`. Die früheren Blocker #7, #11, #24 und #26 sind geschlossen. Auth-/Recovery-Flows, zentrale Owner-/Privacy-Autorisierung, M1-Profile und die PostgreSQL-/HTTP-Testmatrix sind vorhanden; die OIDC-Härtung aus PR #62 ist enthalten und CI-grün.

**G1 ist noch nicht bestanden.** Der verbleibende Runtime-Gate-Blocker ist #61: Beim Löschen einer geteilten `RelatedPerson` kann der bestehende Datenbank-Cascade heute auch einen `OWNER_ONLY`-Termin des Partners löschen. Die beschlossene Produktregel verlangt stattdessen eine explizite serverseitige Auswahl zwischen `preserve` und `cascade`, keinen destruktiven Default und eine privacy-sichere Warn-/Bestätigungssemantik.

Offene Punkte sind damit verbindlich eingeordnet:

- [ ] **#61 – G1-Blocker:** RelatedPerson-Delete-Policy `preserve`/`cascade` serverseitig und atomar umsetzen; Cross-owner-/Privacy-/PostgreSQL-Tests sind Pflicht.
- [ ] **#59 – Pre-Exposure:** anonymen Passkey-Authentication-Start gegen Challenge-Flooding absichern; PostgreSQL-Parallel-/Abuse-Test ist Pflicht. Kein Blocker für interne M2-Domainimplementierung, aber vor öffentlicher/Managed-Exposition zu schließen.
- [ ] **#60 – Pre-Exposure:** Rate-Limit-Schwellen bei parallelen Requests atomar/serialisiert erzwingen. Kein Blocker für interne M2-Domainimplementierung, aber vor öffentlicher/Managed-Exposition zu schließen.
- [ ] **#25 – Repository-Hardening:** Branch Protection/Ruleset für `main` bleibt tarifbedingt nicht technisch erzwungen; kein Runtime-G1-Blocker.

Bis #61 geschlossen und in einem neuen datierten Gate-Review positiv bewertet ist, bleibt produktiver M2-Runtime-Code gesperrt.

## Bereits geschlossene Foundation-/M1-Sicherheitsarbeit

- [x] Rate-Limit-Ereignisse trotz erwarteter Auth-Fehler dauerhaft speichern.
- [x] Refresh-Replay-Widerruf trotz 401 dauerhaft und atomar speichern.
- [x] HTTP-Integrationstests mit dem echten produktiven Session-Lifecycle ergänzen (#7).
- [x] Membership-Änderungen je Space serialisieren; Race mit zwei Einladungen testen.
- [x] Refresh-Rotation atomar machen; parallelen Refresh testen.
- [x] Bootstrap der ersten Self-Hosted-Registrierung absichern und serialisieren.
- [x] Sicheren HTTPS-/Loopback-Standard für Self-Hosted festlegen.
- [x] Refresh-Replay über die gesamte Token-Familie erkennen (#24).
- [x] OIDC-, WebAuthn-/Passkey-, Magic-Link-, E-Mail-Verifikations- und Recovery-Flows implementieren (#26).
- [x] Owner-/Private-Authorization, Profile und zugehörige Privacy-/Tenant-Matrix vervollständigen (#11/#7).
- [x] OIDC-Discovery-Endpunkte auf HTTPS begrenzen und zusätzliche nicht vertrauenswürdige Audiences/inkonsistentes `azp` ablehnen (PR #62).
- [x] Formale Einordnung der dokumentierten Clean-Room-Vorbefassung entschieden: keine Behauptung eines strikten/formalen Clean Rooms; Fortführung als eigenständige Neuimplementierung mit dokumentierter Vorbefassung gemäß [ADR 0001](decisions/0001-clean-room-classification.md).

## M0 – Clean Foundation

- [x] Separates Repository und eigener Quellbaum
- [x] FastAPI, SQLAlchemy 2, PostgreSQL und Alembic
- [x] REST API unter `/api/v1`, camelCase und einheitliches Fehlerformat
- [x] UUIDv7 sowie TIMESTAMPTZ-/DATE-Konventionen
- [x] Transactional-Outbox-Foundation
- [x] PostgreSQL-Job-Queue mit Worker
- [x] LocalMediaStore und MediaStore-Abstraktion
- [x] ProtectedPayload-Grundabstraktion
- [x] Dokumentation, Provenienz und Dependency-Verzeichnis
- [x] Backend-CI mit echten PostgreSQL-Integrationstests und Secret Scan
- [x] Initiale Verzeichnisse `web/`, `android/` und `tools/` ergänzen
- [x] Provider-Interfaces: Map, Places, Recipe, Entertainment
- [x] Dependency-/Vulnerability-Scan
- [x] Reproduzierbare Abhängigkeitsauflösung mit Lock/Constraints und Hashes
- [x] Backend-/Container-Build in CI
- [x] OpenAPI-Vertrag versioniert und Contract-Tests
- [x] ProtectedPayload-Persistenztyp und Outbox-Payload-Allowlist technisch erzwungen

**M0 ist für den aktuellen Umfang abgeschlossen.** Weitere Security-Härtungen werden in den jeweils betroffenen Milestones und Issues verfolgt.

## M1 – Identity & Relationship

- [x] Account, AccountEmail und getrennte AuthIdentity
- [x] Lokaler Passwortlogin mit Argon2
- [x] Device Sessions und Bearer Tokens
- [x] Space, Membership und zentraler Tenant Guard
- [x] Invitations mit Hash, Ablauf, Widerruf, Einmaligkeit und Race-Schutz
- [x] SpaceProfile-Modell sowie Lese-/Schreib-API mit ETag/If-Match und 409
- [x] Beziehungsdauer in der Zeitzone des lesenden Accounts
- [x] OIDC-Modell mit Issuer/Connection-ID und eindeutigem `(issuer, subject)`
- [x] OIDC Authorization Code + PKCE, Discovery/JWKS, State, Nonce, Issuer, Audience und Signaturprüfung
- [x] OIDC-Onboarding mit gültiger Einladung; Einladung nur gehasht, Account/Identität/Membership atomar, kein E-Mail-Merge
- [x] Passkey/WebAuthn Registration und Authentication mit realer Signatur-/Origin-/RP-ID-/Counter-Prüfung
- [x] Getrennte, gehashte Einmal-Tokenmodelle und API-Flows für E-Mail-Verifikation, Magic Link und Recovery
- [x] Zentrale Owner-/Private-Authorization mit SQL-seitigem `SPACE_SHARED`-/`OWNER_ONLY`-Filter
- [x] PartnerProfile und ProfilePreference inklusive `PRIVATE_PARTNER_NOTE`
- [x] RelatedPerson und ImportantDate inklusive Privacy-/Owner-/Cross-Tenant-Regeln
- [x] Rollen-/Owner-/Privacy-/Tenant-Matrix für die M1-Endpunkte
- [ ] RelatedPerson-Delete-Policy aus #61: explizites `preserve`/`cascade` ohne destruktiven Default

### Noch offene Produkt-/Betriebsgrenzen

`SBS_DEPLOYMENT` unterscheidet bereits `cloud` und `self_hosted`, wird aber noch nicht als vollständige serverseitige Auth-Routen-/Provider-Policy durchgesetzt. Ziel ist:

- **Managed/Cloud:** Passkey, Magic Link und später verwaltete Provider wie Google/Apple.
- **Self-Hosted:** lokales Passwort, Passkey und frei konfigurierbares OIDC; Mail-basierte Wege nur bei bewusster Mailkonfiguration.

Bis die Productization-Policy implementiert ist, darf das Verstecken eines Login-Buttons im Client nicht als Sicherheitsgrenze gelten. Die verbindliche Zielregel steht in [SECURITY.md](SECURITY.md). Die Roadmap ordnet diese Durchsetzung G5/Productization zu; öffentliche Managed-Exposition setzt zusätzlich die Schließung von #59 und #60 voraus.

## Spätere Meilensteine

- [ ] M2 – Attachments, Memories, HeartMoments, Milestones, Comments, Story
- [ ] M3 – Wishes, Plans, Places, Relations, Chapters, Collections, Private Area
- [ ] M4 – Reminders, Activity, Notifications, Dashboard, Search, Rules
- [ ] M5 – Export/Import, Web, Android, Read Cache und Client-Parität
- [ ] M6–M8 – Rich Features, Integrationen und Context
- [ ] M9 – Productization, Managed-/Self-Hosted-Policy und Security Hardening
- [ ] MX – echte E2EE erst als eigener späterer Security-Milestone

## Nächster Prüfpunkt

#61 implementieren und über einen eigenen Branch/PR mit PostgreSQL-/HTTP-/Privacy-Tests verifizieren. Nach dessen Merge einen kurzen neuen datierten G1-Gate-Review gegen den dann aktuellen `main` und dessen erfolgreiche CI erstellen. Erst eine positive Entscheidung dieses Reviews setzt G1 auf „bestanden“ und gibt M2-S0 bzw. produktiven M2-Runtime-Code frei.
