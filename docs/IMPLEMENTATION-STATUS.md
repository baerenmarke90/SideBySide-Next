# Umsetzungsstand

Stand: 24. August 2026  
Ausgangspunkt: `main` bei Commit `c69195ca58a0c65a4bedf976c2c2d898c0b39e2c`

## Dokumentenrollen

- **Verbindliche Quelle:** [Clean-Room Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
- **Kompakte Produktübersicht:** [PRODUCT-SPEC.md](../specification/PRODUCT-SPEC.md)
- **Unveränderlicher Ausgangsreview:** [2026-08-24-spec-gap-review.md](reviews/2026-08-24-spec-gap-review.md)
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

## Release-Blocker vor M2

- [x] Rate-Limit-Ereignisse trotz erwarteter Auth-Fehler dauerhaft und atomar speichern.
- [x] Refresh-Replay-Widerruf trotz 401 dauerhaft und atomar speichern.
- [x] HTTP-Integrationstests mit dem echten produktiven Session-Lifecycle ergänzen.
- [x] Membership-Änderungen je Space serialisieren; Race mit zwei Einladungen testen.
- [x] Refresh-Rotation atomar machen; parallelen Refresh testen.
- [ ] Bootstrap der ersten Self-Hosted-Registrierung absichern und serialisieren.
- [x] Sicheren HTTPS-/Loopback-Standard für Self-Hosted festlegen.
- [ ] Formale Einordnung der dokumentierten Clean-Room-Vorbefassung entscheiden.

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
- [ ] Initiale Verzeichnisse `web/`, `android/` und `tools/` ergänzen
- [ ] Fehlende Provider-Interfaces ergänzen: Map, Places, Recipe, Entertainment
- [ ] Dependency-/Vulnerability-Scan aktivieren
- [ ] Reproduzierbare Abhängigkeitsauflösung mit Lock/Constraints und Hashes
- [ ] Expliziten Backend-/Container-Build in CI ergänzen
- [ ] OpenAPI-Vertrag versionieren und Contract-Tests ergänzen
- [ ] E2EE-Grenze bei ersten sensiblen Modellen und Outbox-Payloads technisch erzwingen

## M1 – Identity & Relationship

- [x] Account, AccountEmail und getrennte AuthIdentity
- [x] Lokaler Passwortlogin mit Argon2
- [x] Device Sessions und Bearer Tokens
- [x] Space, Membership und zentraler Tenant Guard
- [x] Invitations mit Hash, Ablauf, Widerruf und Einmaligkeit
- [x] SpaceProfile-Modell und lesende API
- [ ] OIDC-Modell mit Issuer/Connection-ID und eindeutigem `(issuer, subject)`
- [ ] Passkey-/WebAuthn-fähiges Credential-Modell
- [ ] Cloud-Anmeldewege: E-Mail-Verifikation, Magic Link und Recovery
- [ ] Eigene Owner-/Private-Authorization-Grundlage
- [ ] SpaceProfile-Schreib-API mit Versionskonflikt/409
- [ ] Beziehungsdauer in der fachlich richtigen Zeitzone berechnen
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

Nach Abschluss der Release-Blocker und vor Beginn von M2 einen neuen,
commitbezogenen Soll-/Ist- und Sicherheitsreview durchführen.
