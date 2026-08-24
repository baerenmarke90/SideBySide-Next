# SideBySide Next – Soll-/Ist-Vergleich zur Clean-Room Master Specification

> Datierter Review-Snapshot; keine normative Spezifikation und nicht nachträglich umschreiben.  
> Bei Widersprüchen gilt `specification/CLEAN-ROOM-MASTER-SPEC.md`. Der laufende Arbeitsstand steht in `docs/IMPLEMENTATION-STATUS.md`.

Stand: 24. August 2026  
Geprüfter Code: `main` bei Commit `c69195ca58a0c65a4bedf976c2c2d898c0b39e2c`  
Vergleichsgrundlage: „SIDEBYSIDE NEXT – CLEAN-ROOM MASTER SPECIFICATION“, 2.665 Zeilen

## Ergebnis in einem Satz

Die technische M0-Grundlage ist überwiegend vorhanden und fachlich eng an der Spezifikation ausgerichtet; der Gesamtauftrag ist aber noch nicht erfüllt, M1 ist nur teilweise umgesetzt, und die absolute Clean-Room-Regel ist laut eigener `PROVENANCE.md` formal nicht eingehalten worden.

## Milestone-Stand

| Meilenstein | Status | Bewertung |
|---|---|---|
| Übergreifende Clean-Room-Regel | ❌ nicht erfüllt | Die Implementierung liegt in einem separaten Repository, aber der implementierende Assistent war laut eigener Provenienz unmittelbar zuvor dem Classic-Quellcode ausgesetzt. |
| M0 – Clean Foundation | 🟡 weitgehend umgesetzt | Backend, PostgreSQL, Alembic, API-Grundlagen, UUIDv7, Fehlerformat, Outbox, Jobs, CI, Dokumentation und Provenienz existieren. Struktur, Provider, E2EE-Durchsetzung und CI-Mindestumfang sind nur teilweise erfüllt. |
| M1 – Identity & Relationship | 🟡 teilweise umgesetzt | Accounts, E-Mail-Modell, lokale Anmeldung, Sessions, Spaces, Memberships, Invitations, Tenant Guard und lesbares SpaceProfile sind vorhanden. Profile, Preferences, RelatedPersons, ImportantDates, Private Authorization und echte Passkey-/OIDC-Readiness fehlen. |
| M2 – Memory Core | ⏳ nur Vorarbeit | MediaStore-Interface und lokale Ablage existieren; Attachments, Upload-Lifecycle, S3, Memories, HeartMoments, Milestones, Comments, Story und Rückblicke fehlen. |
| M3–M8 | ⏳ planmäßig offen | Die fachlichen Domains und Clients sind noch nicht implementiert. Das ist beim aktuellen M0/M1-Stand keine unerwartete Abweichung. |
| M9 – Productization | 🟡 frühe Teilvorarbeit | Compose enthält API, Worker, Migration und PostgreSQL, aber keinen Web-Client, kein TLS, Backup/Restore, Cloud-Deployment, Entitlements, Observability oder Release-Härtung. |
| MX – echte E2EE | ✅ korrekt offen | Echte E2EE wurde entsprechend der Vorgabe nicht vorgezogen und wird nicht behauptet. |

## Direkte Abweichungen vom Auftrag

### 1. Absolute Clean-Room-Regel formal nicht erfüllt

Die Master-Spezifikation verbietet nicht nur Kopieren, sondern bereits das Lesen des Classic-/SharedMoments-Quellcodes durch den Implementierenden. `PROVENANCE.md` dokumentiert offen, dass dieselbe Assistentensitzung unmittelbar vor Beginn erhebliche Teile des Classic-Codes gelesen hatte und daher kein formal unexponierter Clean-Room-Implementierer war (Zeilen 32–58).

Positiv ist die ehrliche Offenlegung. Sie ändert aber nicht das Soll-/Ist-Ergebnis: Die absolute Regel aus Abschnitt 0 ist nicht erfüllt. Ohne den alten Code zu öffnen, kann dieser Review nicht feststellen, ob konkrete Teile übernommen wurden; die Prozessabweichung ist bereits durch die Provenienz belegt.

Wenn die strikte Clean-Room-Eigenschaft zwingend ist, reicht eine nachträgliche Textänderung nicht. Dann müsste eine frische, nicht exponierte Implementierung ausschließlich aus der Spezifikation entstehen. Alternativ sollte das Projekt korrekt als unabhängige Neuimplementierung mit dokumentierter Vorbefassung bezeichnet werden, nicht als formaler Clean Room.

### 2. Die vollständige Master-Spezifikation ist nicht versioniert im Repository

`specification/PRODUCT-SPEC.md` ist eine 226-zeilige Zusammenfassung. Die Vergleichsvorlage umfasst 2.665 Zeilen und enthält zahlreiche verbindliche Details, die in der Repository-Fassung fehlen: vollständige Providerliste, Upload-Lifecycle, CI-Mindestprüfungen, Security-Testmatrix, Arbeitsprozess, Location-Grenzen und viele Definition-of-Done-Punkte.

Da die Repository-Datei sich selbst als verbindliche Implementierungsquelle bezeichnet, entsteht ein Nachweis- und Driftproblem. Die exakte Master-Spezifikation sollte unverändert und versioniert abgelegt werden; zusätzlich empfiehlt sich eine Requirement-Matrix mit stabilen IDs.

### 3. Vorgesehene Anfangsstruktur ist unvollständig

Vorhanden sind `backend`, `deploy`, `docs` und `specification`. Die ausdrücklich verlangten Verzeichnisse `web`, `android` und `tools` fehlen. Dass die Clients erst in M5 gebaut werden, erklärt leere Implementierungen, nicht aber die in D1 geforderte initiale Struktur. Bei Git können Platzhalterdateien die Verzeichnisse erhalten.

### 4. CI erfüllt Abschnitt 63 nicht vollständig

Vorhanden und grün sind Formatierung, Linting, mypy, Migrationen, Schema-Drift, 175 Tests, PostgreSQL-Integrationstests, Secret Scan und Provenance.

Es fehlen dagegen:

- Dependency-/Vulnerability-Scan; GitHub Dependabot Alerts sind deaktiviert.
- expliziter Backend-/Container-Build im CI-Lauf.
- API-Contract-Tests als eigene Ebene.
- End-to-End-Tests; derzeit mangels Clients erwartbar.
- Web-/Android-Builds; derzeit mangels Clients erwartbar.

Zusätzlich sind produktive Abhängigkeiten nur mit Untergrenzen angegeben. Die exakten Versionen aus `docs/DEPENDENCIES.md` werden dadurch nicht reproduzierbar erzwungen.

## Sicherheitsanforderungen, die im Code noch nicht halten

### 5. Rate-Limiting und Refresh-Replay werden zurückgerollt

Die produktive Request-Transaktion rollt bei jeder Domain-Ausnahme zurück. Falsche Anmeldeversuche werden vor der Fehlerausnahme geschrieben und dadurch wieder entfernt. Ebenso wird der Sitzungswiderruf bei erkanntem Refresh-Replay vor einer Ausnahme gesetzt und anschließend zurückgerollt.

Die Tests erkennen dies nicht, weil der HTTP-Test die echte `get_session`-Transaktionsgrenze durch eine einfache gemeinsame Session ersetzt. Damit sind die zwingenden Anforderungen „rate limiting“ und „token replay“ aus Abschnitt 59 trotz grüner Tests nicht wirksam erfüllt.

### 6. Maximal zwei Partner sind nicht nebenläufig garantiert

`add_member()` zählt aktive Mitgliedschaften ohne Sperre auf der gemeinsamen Space-Zeile. Zwei verschiedene Einladungen können parallel angenommen werden, jeweils einen freien Platz sehen und einen dritten Partner erzeugen. Der vorhandene Race-Test prüft nur zwei Annahmen derselben Einladung.

Damit ist die zentrale Invariante aus Abschnitt 6 unter Nebenläufigkeit nicht erfüllt.

### 7. Refresh-Rotation ist nicht atomar

Zwei parallele Requests können denselben aktuellen Refresh Token lesen und jeweils neue Tokenpaare ausstellen. Der letzte Commit gewinnt. Die geforderte Rotation ist im Normalfall vorhanden, aber der sicherheitsrelevante Wettlauffall ist nicht robust.

### 8. Frische Self-Hosted-Instanz ist übernehmbar

Der erste Account darf ohne Einladung entstehen, und Compose veröffentlicht die API standardmäßig auf allen Interfaces. Es gibt kein einmaliges Bootstrap-Geheimnis und keine atomare Sperre gegen zwei parallele Erstregistrierungen. Wer die Instanz zuerst erreicht, kann sie übernehmen.

Das widerspricht der Priorität „Sicherheit / Tenant Isolation“ und dem Ziel einer privaten Self-Hosted-Paarinstanz.

### 9. HTTPS-Zielarchitektur wird im Self-Hosted-Setup nicht geliefert

Die Spezifikation zeichnet HTTPS als verbindliche Client-Verbindung. Das aktuelle Compose-Setup veröffentlicht Uvicorn direkt über HTTP und liefert weder TLS-Reverse-Proxy noch eine deutliche Loopback-/TLS-Grenze. Für eine externe oder LAN-Nutzung ist der Self-Hosted-Abschnitt daher noch kein sicheres Produktsetup.

## M0 im Detail

| Vorgabe | Status | Ist-Zustand |
|---|---|---|
| Separates Projekt/Repository | ✅ | Eigenes privates Repository und eigener Quellbaum. |
| Strikter Clean Room | ❌ | Vorbefassung der implementierenden Sitzung dokumentiert. |
| Repository-Struktur | 🟡 | `web`, `android`, `tools` fehlen. |
| FastAPI / SQLAlchemy 2 / PostgreSQL / Alembic | ✅ | Entsprechend umgesetzt, kein SQLite-Fallback. |
| `/api/v1`, JSON, camelCase | ✅ | Zentrale API-Basis und Alias-Generator vorhanden. |
| OpenAPI als Vertrag | 🟡 | Laufzeit-OpenAPI in Nicht-Produktion vorhanden; kein versioniertes Schema und keine Contract-Tests. |
| Problem-Details-Fehlerformat | ✅ | Einheitliches Format und stabile Codes vorhanden. |
| UUIDv7 / UTC / DATE | ✅ | Grundkonventionen umgesetzt. |
| Optimistic Concurrency | 🟡 | VersionMixin existiert nur am SpaceProfile; keine Update-API, kein If-Match und keine Abbildung eines ORM-Versionskonflikts auf 409. |
| Transactional Outbox | ✅ Foundation | Modell, atomisches Record und Claiming vorhanden; noch keine Zustellpipeline. |
| PostgreSQL Job Queue | ✅ Foundation | SKIP LOCKED, Lease, Retry und Worker vorhanden. Lange Jobs können nach Lease-Ablauf allerdings doppelt laufen. |
| MediaStore-Abstraktion | 🟡 | `LocalMediaStore` vorhanden; S3, Upload-Finalisierung und Attachment-Lifecycle fehlen planmäßig bis M2. |
| Provider Interfaces | 🟡 | Geocoding, Discovery, ExternalMedia und LocationHistory vorhanden. Map, Places, Recipe und Entertainment fehlen. |
| E2EE-ready Payload Boundary | 🟡 | ProtectedPayload-Abstraktion vorhanden, aber noch keine echte persistierte sensible Domain und keine technische Erzwingung, dass Outbox-Payloads keine sensiblen Inhalte enthalten. |
| CI und Tests | 🟡 | Sehr gute Backend-CI, aber ohne Dependency Scan und expliziten Build. |
| Provenienz / Dependencies / Lizenz | ✅ dokumentiert | Pflichtdokumente, AI-Unterstützung und fehlende Source-Lizenz werden transparent benannt. |

## M1 im Detail

| Vorgabe | Status | Ist-Zustand |
|---|---|---|
| Account / AccountEmail | ✅ Modell | Vorhanden; `profileAttachmentId` fehlt noch. |
| AuthIdentity getrennt | ✅ | Geheimnisse liegen nicht am Account. |
| Lokaler Passwortlogin | ✅ mit Sicherheitsfehler | Argon2, Dummy-Hash und Sitzungen vorhanden; Rate-Limit-Transaktion ist fehlerhaft. |
| Cloud Magic Link / E-Mail-Verifikation / Recovery | ❌ | Noch nicht implementiert. |
| Passkey-fähige Architektur | 🟡 schwach vorbereitet | Nur Provider-Enum; Credential-ID, Public Key, Counter und weitere WebAuthn-Daten haben noch kein tragfähiges Modell. |
| OIDC-ready | 🟡 unzureichend | Nur `provider = OIDC` plus `subject`. OIDC-`sub` ist nur zusammen mit dem Issuer eindeutig; Issuer/Connection-ID fehlt. Mehrere Provider einschließlich Pocket ID lassen sich nicht sauber unterscheiden. |
| DeviceSession / Bearer Token | ✅ mit Race-Lücke | Gehashte Tokens, 15-Minuten-Access-Token, Rotation und Widerruf vorhanden; paralleler Refresh ist nicht atomar. |
| Space / Membership / Tenant Guard | ✅ mit Race-Lücke | Zentrale Prüfung und 404-Isolation sind gut umgesetzt; die Zwei-Partner-Grenze ist nicht atomar. |
| Invitations | ✅ mit Testlücke | Hash, Ablauf, Widerruf und Einmaligkeit vorhanden; Race-Test deckt nicht zwei verschiedene Einladungen ab. |
| Private Authorization | ❌ | Es gibt noch keine Owner-only-Domain und keinen eigenen Owner-Guard. |
| SpaceProfile | 🟡 | Modell und GET-Ausgabe vorhanden; keine Schreib-API. Die sichtbare Dauer verwendet UTC statt der Benutzer-/Space-Zeitzone. |
| PartnerProfile / ProfilePreference | ❌ | Nicht implementiert. |
| RelatedPerson / ImportantDate | ❌ | Nicht implementiert. |

## Anforderungen, die aktuell korrekt bewusst offen sind

Die folgenden großen Lücken sind beim angegebenen Entwicklungsstand keine Fehlentwicklung:

- Memories, HeartMoments, Milestones, Comments und Attachments gehören zu M2.
- Wishes, Plans, Places, Chapters, Collections und private Ablage gehören zu M3.
- Reminders, Notifications, Dashboard, Search und Rules gehören zu M4.
- Web, Android, Export/Import und Offline-Read-Cache gehören zu M5.
- Fragen, Jahresrückblick, Integrationen, Context und Location gehören zu M6–M8.
- Echte E2EE gehört ausdrücklich in MX und darf jetzt noch fehlen.
- AI und öffentliche Share Links sind korrekt nicht vorhanden.

## Besonders gute Übereinstimmungen

- Modularer Monolith statt Microservices.
- PostgreSQL ohne SQLite-Scheinabsicherung.
- Space/Membership als zentrale Mandantengrenze.
- Membership-Prüfung vor dem Laden von Space-Daten und 404 statt 403.
- Opaque Tokens nur gehasht; Passwörter mit Argon2.
- Separate Account- und Auth-Modelle.
- UUIDv7, TIMESTAMPTZ und DATE-Grundkonventionen.
- Transactional-Outbox- und SKIP-LOCKED-Job-Foundation.
- Keine generische Universal-Domain-Tabelle.
- Keine Werbung, Tracking-SDKs, AI oder öffentliche Freigabelinks.
- E2EE wird ehrlich als noch nicht implementiert bezeichnet.
- Pflichtdokumente, Dependency-Lizenzen, Assets und fehlende eigene Lizenz sind transparent dokumentiert.
- CI führt echte PostgreSQL-Integrationstests aus und verhindert stilles Überspringen.

## Empfohlene Reihenfolge zur Spezifikationskonformität

1. Entscheiden, ob formaler Clean Room zwingend bleibt. Falls ja, neue unexponierte Implementierung; andernfalls Provenienzbezeichnung präzisieren.
2. Master-Spezifikation unverändert versionieren und eine Requirement-Traceability-Matrix anlegen.
3. Rate-Limit-/Replay-Transaktionen, Bootstrap, Membership-Race und Refresh-Race beheben.
4. CI um Dependency Scan und reproduzierbaren Backend-/Container-Build ergänzen; Dependabot oder Renovate aktivieren.
5. M1 sauber abschließen: OIDC-/Passkey-Modell, Private Authorization, Profile, Preferences, RelatedPersons, ImportantDates und SpaceProfile-Update.
6. Erst danach M2-Inhaltsdomänen beginnen, damit sie auf tatsächlich tragfähigen Sicherheitsinvarianten aufbauen.

## Gesamturteil

Der Code ist keine Umsetzung der gesamten Master-Spezifikation, sondern eine gute Backend-Grundlage zwischen M0 und frühem M1. Die fachliche Richtung stimmt weitgehend. Die wichtigsten Abweichungen liegen an Prozessnachweis, Transaktionsgrenzen und Nebenläufigkeit – genau in den Bereichen, die die Master-Spezifikation höher priorisiert als Funktionsumfang. Vor M2 sollten diese Punkte als Release-Blocker behandelt werden.



