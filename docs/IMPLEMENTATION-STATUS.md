# Umsetzungsstand

Stand: 24. August 2026  
Ausgangspunkt: `main` bei Commit `c69195ca58a0c65a4bedf976c2c2d898c0b39e2c`

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Unveränderlicher Ausgangsreview:** [2026-08-24-spec-gap-review.md](reviews/2026-08-24-spec-gap-review.md)
- **Aktueller Security-Snapshot:** [2026-08-24-g1-m1-security-review.md](reviews/2026-08-24-g1-m1-security-review.md)
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

## Release-Blocker vor M2

- [x] Rate-Limit-Ereignisse trotz erwarteter Auth-Fehler dauerhaft und atomar speichern.
- [x] Refresh-Replay-Widerruf trotz 401 dauerhaft und atomar speichern.
- [x] HTTP-Integrationstests mit dem echten produktiven Session-Lifecycle ergänzen.
- [x] Membership-Änderungen je Space serialisieren; Race mit zwei Einladungen testen.
- [x] Refresh-Rotation atomar machen; parallelen Refresh testen.
- [x] Bootstrap der ersten Self-Hosted-Registrierung absichern und serialisieren.
- [x] Sicheren HTTPS-/Loopback-Standard für Self-Hosted festlegen.
- [x] Formale Einordnung der dokumentierten Clean-Room-Vorbefassung entschieden: keine Behauptung eines strikten/formalen Clean Rooms; Fortführung als eigenständige Neuimplementierung mit dokumentierter Vorbefassung gemäß [ADR 0001](decisions/0001-clean-room-classification.md).

## Aktueller G1/M1 Security Review

Der datierte [G1/M1 Security Review vom 24.08.2026](reviews/2026-08-24-g1-m1-security-review.md) bewertet den Stand nach Abschluss der bisherigen P0-Fixes und der Auth-Persistenzarchitektur.

**Ergebnis: G1 ist noch nicht bestanden; produktive M2-Domainimplementierung bleibt gesperrt.**

Aktuelle G1-Blocker:

- [ ] #26 – OIDC-/WebAuthn-/Cloud-Auth-Flows tatsächlich implementieren.
- [ ] #11 – Owner-/Private-Authorization, SpaceProfile-Schreibpfad/409/Timezone sowie PartnerProfile, ProfilePreference, RelatedPerson und ImportantDate abschließen.
- [ ] #7 – Rollen-/Owner-/Privacy-/Tenant-Matrix für die neuen M1-Endpunkte vervollständigen.

Zusätzliche Härtung:

- [x] #24 – Refresh-Replay über die gesamte Token-Familie erkennen.
- [ ] #25 – Branch Protection/Ruleset für `main`: Ruleset angelegt, aber bei diesem privaten Repository durch den aktuellen GitHub-Tarif nicht erzwungen; zusätzlich muss das Targeting nach einem Planwechsel auf `main` geprüft werden. Kein eigenständiger G1-Codeblocker, aber offenes Repository-Hardening.

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
- [x] Fehlende Provider-Interfaces ergänzen: Map, Places, Recipe, Entertainment
- [x] Dependency-/Vulnerability-Scan aktivieren
- [x] Reproduzierbare Abhängigkeitsauflösung mit Lock/Constraints und Hashes
- [x] Expliziten Backend-/Container-Build in CI ergänzen
- [x] OpenAPI-Vertrag versionieren und Contract-Tests ergänzen
- [x] ProtectedPayload-Persistenztyp und Outbox-Payload-Allowlist technisch erzwingen

**M0 ist für den aktuellen Umfang abgeschlossen.** Weitere Security-Härtungen werden in den jeweils betroffenen Milestones und Issues verfolgt.

## M1 – Identity & Relationship

- [x] Account, AccountEmail und getrennte AuthIdentity
- [x] Lokaler Passwortlogin mit Argon2
- [x] Device Sessions und Bearer Tokens
- [x] Space, Membership und zentraler Tenant Guard
- [x] Invitations mit Hash, Ablauf, Widerruf und Einmaligkeit
- [x] SpaceProfile-Modell und lesende API
- [x] OIDC-Modell mit Issuer/Connection-ID und eindeutigem `(issuer, subject)`
- [x] Passkey-/WebAuthn-fähiges Credential-Modell
- [x] Getrennte, gehashte Einmal-Tokenmodelle für E-Mail-Verifikation, Magic Link und Recovery
- [ ] OIDC-/WebAuthn-Adapter und vollständige Cloud-Auth-API-Flows
- [x] Eigene Owner-/Private-Authorization-Grundlage (#27): zentrale, in der
      Abfrage erzwungene `SPACE_SHARED`-/`OWNER_ONLY`-Autorisierung samt
      Privacy-Testmatrix. Eine produktive `OWNER_ONLY`-Fachdomäne setzt
      darauf noch nicht auf; das gehört zu den restlichen M1-/M2-Domänen.
- [x] SpaceProfile-Schreib-API mit Versionskonflikt/409 (#28): `PUT` auf
      `relationshipStartedOn`, `showRelationshipDuration` und
      `durationDisplayMode` mit ETag und `If-Match` als Pflichtkopf.
      `SpaceProfile` bleibt `SPACE_SHARED` und trägt bewusst keine
      Owner-Einschränkung.
- [x] Beziehungsdauer in der fachlich richtigen Zeitzone berechnen (#28):
      Tagesgrenze über `Account.timezone` der lesenden Person statt
      `today_utc()`.
- [ ] PartnerProfile und ProfilePreference
- [ ] RelatedPerson und ImportantDate
- [ ] Cross-Tenant- und Privacy-Tests für jedes neue M1-Feature

## Spätere Meilensteine

- [ ] M2 – Attachments, Memories, HeartMoments, Milestones, Comments, Story
- [ ] M3 – Wishes, Plans, Places, Relations, Chapters, Collections, Private Area
- [ ] M4 – Reminders, Activity, Notifications, Dashboard, Search, Rules
- [ ] M5 – Export/Import, Web, Android, Read Cache und Client-Parität
- [ ] M6–M8 – Rich Features, Integrationen und Context
- [ ] M9 – Productization und Security Hardening
- [ ] MX – echte E2EE erst als eigener späterer Security-Milestone

## Nächster Prüfpunkt

Neuen datierten G1-Review nach Abschluss von #11, #26 und dem relevanten Rest von #7 sowie nach Umsetzung von #24 durchführen. Der nächste Review muss den dann aktuellen `main`-Commit und eine erfolgreiche CI eindeutig referenzieren. #25 bleibt als tarifbedingt blockiertes Repository-Hardening separat offen.
