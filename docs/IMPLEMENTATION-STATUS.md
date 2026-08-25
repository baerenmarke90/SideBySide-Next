# Umsetzungsstand

Stand: 25. August 2026  
Ausgangspunkt dieses Audits: `main` bei Commit `9b4be168cec305c8a613889d2213f133429fe158`

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Unveränderlicher Ausgangsreview:** [2026-08-24-spec-gap-review.md](reviews/2026-08-24-spec-gap-review.md)
- **Historischer G1-Snapshot:** [2026-08-24-g1-m1-security-review.md](reviews/2026-08-24-g1-m1-security-review.md)
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

Der datierte [G1/M1 Security Review vom 24.08.2026](reviews/2026-08-24-g1-m1-security-review.md) bleibt ein historischer Snapshot. Seine damaligen Blocker #7, #11, #24 und #26 sind inzwischen geschlossen; die dort beschriebenen fehlenden Auth-, Owner-/Privacy-, Profile- und Testpfade sind auf `main` vorhanden.

Der Merge von PR #57 (`9b4be168cec305c8a613889d2213f133429fe158`) hat zusätzlich OIDC-Onboarding über gültige Einladungen ergänzt. Der Merge-Commit selbst hat die vollständige CI mit PostgreSQL-Integrationstests, OpenAPI-/Migration-/Drift-Prüfung, Lint, Mypy, Supply Chain, Secret Scan und Provenance bestanden.

**G1 wird trotzdem noch nicht als bestanden markiert.** Vor der Freigabe von produktivem M2-Runtime-Code folgt ein neuer datierter Review gegen den dann aktuellen `main`. Das Audit vom 25.08.2026 hat zusätzlich folgende Härtungen bzw. Entscheidungen herausgezogen:

- [ ] #59 – anonymen Passkey-Authentication-Start gegen Challenge-Flooding absichern; PostgreSQL-Parallel-/Abuse-Test ist Pflicht.
- [ ] #60 – Rate-Limit-Schwellen bei parallelen Requests atomar/serialisiert erzwingen.
- [ ] #61 – beim Löschen einer `RelatedPerson` die Produktentscheidung „Termine erhalten“ vs. „Termine mit löschen“ privacy-sicher in API und späteren Clients umsetzen. Der heutige Cascade bleibt bis dahin dokumentiert und unverändert.
- [ ] #25 – Branch Protection/Ruleset für `main`: angelegt, aber bei diesem privaten Repository durch den aktuellen GitHub-Tarif nicht technisch erzwungen; nach einem Planwechsel Targeting und Enforcement erneut prüfen.

#59 und #60 sind Abuse-/Availability-Härtungen ohne bekannten Auth-Bypass. Der neue G1-Review entscheidet explizit, ob sie für den Beginn interner M2-Domainimplementierung blockieren oder als verpflichtende Pre-Exposure-Härtung vor Managed-/öffentlichem Betrieb geführt werden. #61 ist eine bewusste Datenintegritäts-/UX-Entscheidung; die aktuelle Privacy-Isolation wird dadurch nicht aufgehoben.

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

### Noch offene Produkt-/Betriebsgrenzen

`SBS_DEPLOYMENT` unterscheidet bereits `cloud` und `self_hosted`, wird aber noch nicht als vollständige serverseitige Auth-Routen-/Provider-Policy durchgesetzt. Ziel ist:

- **Managed/Cloud:** Passkey, Magic Link und später verwaltete Provider wie Google/Apple.
- **Self-Hosted:** lokales Passwort, Passkey und frei konfigurierbares OIDC; Mail-basierte Wege nur bei bewusster Mailkonfiguration.

Bis die Productization-Policy implementiert ist, darf das Verstecken eines Login-Buttons im Client nicht als Sicherheitsgrenze gelten. Die verbindliche Zielregel steht in [SECURITY.md](SECURITY.md).

## Spätere Meilensteine

- [ ] M2 – Attachments, Memories, HeartMoments, Milestones, Comments, Story
- [ ] M3 – Wishes, Plans, Places, Relations, Chapters, Collections, Private Area
- [ ] M4 – Reminders, Activity, Notifications, Dashboard, Search, Rules
- [ ] M5 – Export/Import, Web, Android, Read Cache und Client-Parität
- [ ] M6–M8 – Rich Features, Integrationen und Context
- [ ] M9 – Productization, Managed-/Self-Hosted-Policy und Security Hardening
- [ ] MX – echte E2EE erst als eigener späterer Security-Milestone

## Nächster Prüfpunkt

Nach Merge des Audit-Hardening-PRs einen **neuen datierten G1-Review** gegen den dann aktuellen `main` und dessen erfolgreiche CI erstellen. Der Review muss die geschlossenen Altblocker, die OIDC-Härtung dieses Audits sowie die Einordnung von #59, #60, #61 und #25 ausdrücklich bewerten. Erst danach wird G1 auf „bestanden“ gesetzt und M2-S0 freigegeben.
