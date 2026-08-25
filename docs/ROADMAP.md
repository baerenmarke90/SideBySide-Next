# SideBySide Next Roadmap

**Status:** Menschenlesbare Orientierungs- und Priorisierungsansicht  
**Version:** 1.3  
**Stand:** 25.08.2026  
**Zeitmodell:** Phasen und Release Gates, keine zugesagten Kalendertermine

Diese Roadmap übersetzt die verbindliche Produktspezifikation in eine verständliche Reihenfolge. Sie zeigt Ziel, Abhängigkeiten und Freigabepunkte. Der tatsächliche Arbeitsstand steht ausschließlich im [Implementation Status](./IMPLEMENTATION-STATUS.md).

## Roadmap auf einen Blick

![Grafische Roadmap von M0 Foundation bis M9 Release und der strategischen E2EE-Spur](./assets/roadmap/roadmap-overview.svg)

**Aktuell:** M0 ist abgeschlossen und der vorgesehene M1-Runtimeumfang ist weitgehend umgesetzt. Gate G1 bleibt wegen der fehlenden expliziten RelatedPerson-Delete-Policy aus #61 geschlossen.

## So ist die Roadmap zu lesen

| Dokument | beantwortet |
|---|---|
| diese Roadmap | Wohin gehen wir, in welcher Reihenfolge und warum? |
| [Implementation Status](./IMPLEMENTATION-STATUS.md) | Was ist auf `main` tatsächlich umgesetzt oder noch offen? |
| [G1/M1 Follow-up Review vom 25.08.2026](./reviews/2026-08-25-g1-m1-follow-up-review.md) | Aktuelle Gate-Entscheidung und Einordnung der Restfindings |
| [G1/M1 Security Review vom 24.08.2026](./reviews/2026-08-24-g1-m1-security-review.md) | Historischer Prüfstand vor Abschluss der damaligen M1-Blocker |
| GitHub Issues/PRs | Welche konkreten Arbeitspakete werden bearbeitet? |
| [Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md) | Was ist fachlich und technisch verbindlich? |

- Ein Meilenstein ist kein Datum, sondern ein kohärenter Produkt- und Technikblock.
- Ein Release Gate ist eine prüfbare Bedingung für den nächsten Block.
- „Later“ bedeutet bewusst nach dem Core, nicht unwichtig.
- MX E2EE ist eine eigene strategische Spur und kein stilles Teilversprechen des MVP.

## Aktueller Snapshot

Der Snapshot fasst den [Implementation Status vom 25.08.2026](./IMPLEMENTATION-STATUS.md) und den [G1/M1 Follow-up Review vom 25.08.2026](./reviews/2026-08-25-g1-m1-follow-up-review.md) zusammen. Datierte Reviews bleiben unveränderliche Prüfsnapshots.

### M0 — Clean Foundation: abgeschlossen

Für den aktuellen M0-Umfang sind unter anderem umgesetzt:

- FastAPI, SQLAlchemy 2, PostgreSQL und Alembic,
- REST API v1, camelCase und einheitliches Fehlerformat,
- UUIDv7 sowie Timestamp-/Date-Konventionen,
- Transactional Outbox und PostgreSQL-Job-Queue,
- MediaStore-, Provider- und ProtectedPayload-Grundlagen,
- initiale `web/`, `android/` und `tools/`-Strukturen,
- reproduzierbare Python-Abhängigkeiten mit Lockfile,
- Dependency-/Vulnerability-Scan,
- versionierter OpenAPI-Vertrag mit Contract-Check,
- Backend-/Container-Build,
- echte PostgreSQL-Integrationstests, Secret Scan und Provenance-Prüfung.

M0 wird nicht erneut geöffnet, nur weil spätere Milestones zusätzliche Härtungen auf derselben Infrastruktur benötigen. Neue Findings werden im jeweils betroffenen Issue/Milestone verfolgt.

### M1 — Identity & Relationship: Runtimeumfang weitgehend umgesetzt, G1 durch #61 blockiert

Umgesetzt sind unter anderem:

- Account/AuthIdentity, lokaler Passwortlogin und Device Sessions,
- Space, Membership, Tenant Guard und race-sichere Invitations,
- zentrale Owner-/Private-Authorization mit SQL-seitigem `SPACE_SHARED`-/`OWNER_ONLY`-Filter,
- SpaceProfile mit ETag/If-Match, 409-Concurrency und korrekter Benutzerzeitzone,
- PartnerProfile, ProfilePreference, RelatedPerson und ImportantDate,
- OIDC Authorization Code + PKCE mit State/Nonce, Discovery/JWKS, Issuer/Audience/Signaturprüfung,
- OIDC-Onboarding über eine weiterhin beim Callback gültige Einladung ohne E-Mail-Merge,
- WebAuthn-/Passkey-Registration und -Authentication,
- Magic Link, E-Mail-Verifikation und Recovery,
- Refresh-Replay über die gesamte Token-Familie,
- HTTP-/Owner-/Privacy-/Cross-Tenant-/Concurrency-Tests gegen PostgreSQL.

Die früheren G1-Tracking-Issues #7, #11, #24 und #26 sind geschlossen. Der Follow-up-Review vom 25.08.2026 hat die verbleibenden Punkte verbindlich eingeordnet:

- **#61 — G1-Blocker:** RelatedPerson-Löschen braucht eine explizite serverseitige `preserve`-/`cascade`-Policy ohne destruktiven Default. Der heutige Cascade kann auch private ImportantDates des Partners indirekt löschen.
- **#59 — Pre-Exposure:** Passkey-Authentication-Start gegen Challenge-Flooding absichern; kein Blocker für interne M2-Domainimplementierung, aber vor öffentlicher/Managed-Exposition zu schließen.
- **#60 — Pre-Exposure:** Rate-Limit-Schwellen unter Parallelität atomar erzwingen; ebenfalls vor öffentlicher/Managed-Exposition zu schließen.
- **#25 — Repository-Hardening:** Ruleset/Branch Protection bleibt tarifbedingt nicht erzwungen; kein Runtime-G1-Blocker.

### Noch offene Bedingungen vor M2

1. #61 serverseitig mit expliziter `preserve`-/`cascade`-Delete-Policy umsetzen.
2. Kein destruktiver Default; privacy-sichere Warn-/Bestätigungssemantik ohne Existenzauskunft über unsichtbare Partnertermine.
3. PostgreSQL-/HTTP-Tests für beide Policies und Cross-owner-/Tenant-Fälle grün bekommen.
4. #61 über eigenen PR mit vollständiger CI mergen.
5. Danach einen kurzen neuen datierten G1-Gate-Review gegen den aktuellen `main` erstellen und G1 ausdrücklich freigeben oder weiter blockieren.

Repository-Hardening #25 bleibt separat offen. #59 und #60 blockieren interne M2-Implementierung nicht, müssen jedoch vor öffentlicher bzw. Managed-Exposition geschlossen sein.

## Meilensteine

| Phase | Menschliches Ziel | Fachlicher Umfang | Ergebnis |
|---|---|---|---|
| **M0 · Foundation** | verlässliche technische Basis | API, DB, Outbox, Jobs, MediaStore, CI, Provenance | sicher erweiterbarer Core |
| **M1 · Verbinden** | zwei Personen bilden einen privaten Space | Identity, Auth, Membership, Invitation, Profile | sicherer Account- und Beziehungsrahmen |
| **M2 · Erinnern** | gemeinsame Geschichte entsteht | Attachments, Memories, HeartMoments, Milestones, Comments, Story | erster emotionaler Kernflow |
| **M3 · Planen** | Ideen werden gemeinsame Vorhaben | Wishes, Plans, Places, Chapters, Collections, Private Area | Planung und private Ablage |
| **M4 · Begleiten** | hilfreiche, kontrollierte Aktivierung | Reminders, Activity, Notifications, Dashboard, Search, Rules | relevanter Alltag ohne unnötiges Tracking |
| **M5 · Erleben** | Web und Android sind vollständig nutzbar | Export/Import, Web, Android, Read Cache, Parität | produktfähiger Core auf beiden Clients |
| **M6 · Vertiefen** | freiwillige gemeinsame Reflexion | Questions, Check-in, Monats-/Jahresrückblicke | Rich Features nach stabilem Core |
| **M7 · Entdecken** | externe Inspiration bleibt optional | Shopping, Rezepte, Events, Unterhaltung, Medienadapter | Integrationen ohne Core-Abhängigkeit |
| **M8 · Kontext** | freiwilliger Ortskontext | Location, Karten, Geofencing, Presence | explizit aktivierbare Kontextfunktionen |
| **M9 · Veröffentlichen** | sicher betreibbares Produkt | Self-Hosted, Cloud, Backup, Entitlements, Hardening, Release | launchfähiger Betrieb |
| **MX · E2EE** | echter kryptografischer Schutz | Schlüsselmodell, Migration, Client-Crypto, Recovery | separat bewertete E2EE-Version |

## Parallele Arbeitsströme

![Roadmap mit parallelen Spuren für Produkt, Backend, Web, Android, Design-System, Security/QA und Betrieb](./assets/roadmap/roadmap-tracks.svg)

Die Spuren laufen parallel, aber nicht unabhängig. Eine Clientoberfläche darf einen Domainflow erst als fertig darstellen, wenn API, Autorisierung, Fehlerfälle, Privacy-Tests und plattformspezifische Accessibility gemeinsam erfüllt sind. Für parallele Implementierungsagenten gelten die Koordinationsregeln im [Implementation Status](./IMPLEMENTATION-STATUS.md): ein Issue-Scope pro Branch/PR und keine stillen Scope-Erweiterungen.

## Horizonte

### Now — #61 schließen und G1 freigeben

**Umfasst:** letzter Runtime-Gate-Blocker nach abgeschlossenem M1-Hauptumfang.

- RelatedPerson-Delete-API um `preserve` und `cascade` erweitern,
- destruktiven Default ausschließen,
- private Partnertermine bei `preserve` erhalten, ohne ihre Existenz oder Inhalte zu leaken,
- bestehenden Cascade als ausdrücklich gewählte Option erhalten,
- PostgreSQL-/HTTP-/Privacy-Tests für beide Policies ergänzen,
- nach grünem Merge einen neuen datierten G1-Gate-Review durchführen.

**Verlassen, wenn:** Gate G1 formell erfüllt und M2 freigegeben ist.

### Next — Der emotionale Kern

**Umfasst:** M2.

- M2-S0: blockierende Domain-, Privacy-, Media- und API-Entscheidungen aus dem Decision Log schließen,
- Memory, Attachment und Media Pipeline,
- HeartMoment mit `OWNER_ONLY`/`SPACE_SHARED`,
- Milestones und sichere Comments,
- abgeleitete Story mit Cursor-Pagination und Privacy-Filtern,
- erste vollständig paritätische End-to-End-Flows in Web und Android.

**Verlassen, wenn:** Gate G2 erfüllt ist.

### Then — Planung, Aktivierung und Client-Parität

**Umfasst:** M3 bis M5.

- Wunsch → Plan → erlebt → optional Chapter,
- Collections und eigenständige private Ablage,
- Suche, Dashboard, Reminder und kontrollierte Notifications,
- Export/Import,
- vollständige Web-/Android-Oberflächen und Android Read Cache,
- Design-System P0/P1 und Accessibility-Gates.

**Verlassen, wenn:** Gate G4 erfüllt ist.

### Later — Freiwillige Erweiterungen und Productization

**Umfasst:** M6 bis M9.

- Fragen, Check-in und Rückblicke,
- Shopping, Discovery und Providerintegrationen,
- optionale Location-/Context-Funktionen,
- serverseitige Managed-/Self-Hosted-Auth-Policy,
- verwaltete Login-Provider wie Google/Apple,
- Self-Hosted- und Cloud-Härtung einschließlich #59/#60,
- Backup, Entitlements, Releasebetrieb und Supportfähigkeit.

**Verlassen, wenn:** Gate G5 erfüllt ist.

### Strategic — Echte Ende-zu-Ende-Verschlüsselung

**Umfasst:** MX.

- formales Threat Model und Schlüssel-/Recovery-Produktentscheidung,
- Client-seitige Kryptografie in Web und Android,
- Migration bestehender ProtectedPayload-Daten,
- Auswirkungen auf Suche, Dashboard, Regeln, Notifications und Export,
- unabhängiges Security Review vor jeder E2EE-Aussage.

MX startet erst mit eigenem Scope und Gate. Bis dahin wird E2EE weder versprochen noch grafisch als MVP-Eigenschaft dargestellt.

## Abhängigkeiten

```mermaid
flowchart LR
  M0[M0 Foundation] --> M1[M1 Identity & Relationship]
  M1 --> M2[M2 Memories & Story]
  M2 --> M3[M3 Planning & Private Area]
  M2 --> M4[M4 Engagement & Search]
  M3 --> M5[M5 Clients & Parity]
  M4 --> M5
  M5 --> M6[M6 Rich Features]
  M5 --> M7[M7 Integrations]
  M7 --> M8[M8 Context]
  M6 --> M9[M9 Productization]
  M8 --> M9
  M0 -. ProtectedPayload boundary .-> MX[MX E2EE]
  M5 -. mature clients .-> MX
```

Kritische Reihenfolge:

1. Tenant Isolation und Auth vor sensiblen Inhaltsdomänen.
2. Owner-only-Grundlage vor privaten Inhalten.
3. Media Security vor produktiver Attachment-Nutzung.
4. Memory/Story vor Rückblicken und Discovery-Personalisierung.
5. stabile API und Contract-Tests vor vollständiger Client-Parität.
6. Core-Parität vor Shopping, Location und weiteren Integrationen.

## Release Gates

### G0 — Foundation prüfbar

- API-/DB-Konventionen und Migrationen stabil,
- CI, Integrationstests, Secret Scan und reproduzierbarer Build,
- versioniertes OpenAPI mit Contract-Tests,
- Outbox/Jobs/MediaStore und ProtectedPayload-Grenze abgesichert.

**Aktueller Stand:** bestanden für den M0-Umfang.

### G1 — Sicherer Paar-Space

- Auth- und Recovery-Wege für den jeweiligen Betriebsmodus,
- Invitation atomar, einmalig, widerrufbar und race-sicher,
- Tenant Guard und Owner-only-Autorisierung,
- Profile/SpaceProfile mit Versionskonflikten,
- Cross-Tenant-, Session- und Privacy-Tests grün.

**Aktueller Stand:** **nicht bestanden.** Der Follow-up-Review vom 25.08.2026 bestätigt die früheren Runtime-Kriterien als umgesetzt, identifiziert aber #61 als verbleibenden G1-Blocker: Eine geteilte `RelatedPerson` kann aktuell über den impliziten Cascade auch einen privaten Termin des Partners löschen. G1 wird erst nach expliziter `preserve`-/`cascade`-Policy, grünen Privacy-/PostgreSQL-Tests und erneutem datiertem Gate-Review freigegeben.

### G2 — Story Alpha

- Memory, Media, HeartMoment, Milestone und Comment vollständig,
- Story enthält niemals `OWNER_ONLY`,
- Upload-Missbrauch und signierte URLs geprüft,
- Web und Android bestehen die ersten kritischen Flows,
- Accessibility- und Content-Review ohne hohe Befunde.

### G3 — Gemeinsamer Alltag

- Wünsche/Pläne/Places/Chapters/Collections fachlich konsistent,
- private Ablage vollständig isoliert,
- 409-Konflikte und Delete-Wirkungen verständlich,
- Suche und Dashboard privacy-sicher vorbereitet.

### G4 — Core Release Candidate

- Web und Android fachlich gleichwertig,
- Android Offline Read Cache ohne vorgetäuschten Write Sync,
- Export/Import versioniert und getestet,
- Design-System P0/P1 auf beiden Plattformen verifiziert,
- Performance-, Accessibility-, Privacy- und Security-Gates bestanden.

### G5 — Launchfähig

- Cloud und Self-Hosted dokumentiert, update- und backupfähig,
- serverseitige Auth-/Provider-Policy je Betriebsform durchgesetzt,
- #59 und #60 vor öffentlicher/Managed-Exposition geschlossen,
- Retention, vollständige Löschung und Supportprozesse geklärt,
- Entitlements/Billing-Adapter ohne Domainkopplung,
- Monitoring ohne sensible Inhalte,
- Release-, Incident- und Recovery-Prozess getestet.

## Was bewusst nicht vorgezogen wird

- Shopping, Event Discovery und Providerintegrationen vor stabilem Core,
- Offline Write Sync im MVP,
- öffentliche Share Links,
- KI-Funktionen,
- Partnerentfernung,
- Location/Geofencing ohne separaten Opt-in- und Privacy-Flow,
- E2EE-Marketing vor echter Implementierung und Review.

## Roadmap-Risiken

| Risiko | Schutzmaßnahme |
|---|---|
| Features beginnen vor offenen Security-Gates | Gate G1 blockiert M2-Freigabe |
| Parallele Agenten überschreiben denselben Scope | ein Issue pro Branch/PR, klarer Owner und Abgleich gegen aktuellen `main` |
| Web und Android driften auseinander | gemeinsamer OpenAPI-Vertrag, Component Contracts und Paritäts-DoD |
| Design-System wird zur Dokumentation ohne Code | Manifest, Tokenadapter, Plattformkataloge und CI-Gates |
| spätere Integrationen dominieren den Core | Provideradapter und klare M7/M8-Grenze |
| Privacy-Sprache übertreibt den Stand | Content Guidelines und unabhängiges Security Review |
| Roadmap wird mit Status verwechselt | Implementation Status bleibt einzige operative Wahrheit |

## Pflege

- Der Current-Marker wird nach jedem abgeschlossenen Gate aktualisiert.
- Meilensteine ändern sich nur bei einer fachlichen Entscheidung in der Spezifikation.
- Offene Aufgaben werden nicht in dieser Datei gepflegt, sondern im Implementation Status und in Issues.
- Ein Roadmap-Update nennt Grund und Auswirkung, nicht nur eine neue Reihenfolge.
- Grafiken und Text werden gemeinsam geändert, wenn sich die dargestellte Phase ändert, damit keine widersprüchlichen Ansichten entstehen.

## Verwandte Dokumente

- [Implementation Status](./IMPLEMENTATION-STATUS.md)
- [G1/M1 Follow-up Security Review vom 25.08.2026](./reviews/2026-08-25-g1-m1-follow-up-review.md)
- [Historischer G1/M1 Security Review vom 24.08.2026](./reviews/2026-08-24-g1-m1-security-review.md)
- [Produktspezifikation](../specification/PRODUCT-SPEC.md)
- [Critical User Flows](./USER-FLOWS.md)
- [API-/UI-Verträge](./API-UI-CONTRACTS.md)
- [Design-System-Umsetzung](./DESIGN-SYSTEM-DELIVERY.md)
- [Accessibility- und QA-Matrix](./ACCESSIBILITY-QA-MATRIX.md)
