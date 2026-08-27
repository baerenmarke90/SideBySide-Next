# SideBySide Next Roadmap

**Status:** Menschenlesbare Orientierungs- und Priorisierungsansicht  
**Version:** 1.7  
**Stand:** 26.08.2026  
**Zeitmodell:** Phasen und Release Gates, keine zugesagten Kalendertermine

Diese Roadmap übersetzt die verbindliche Produktspezifikation in eine verständliche Reihenfolge. Sie zeigt Ziel, Abhängigkeiten und Freigabepunkte. Der tatsächliche Arbeitsstand steht im [Implementation Status](./IMPLEMENTATION-STATUS.md); die präzisierten M2-Grenzen stehen im [M2 Project Control](./m2/PROJECT-CONTROL.md), die M3-Readiness im [M3 Technical Readiness Package](./m3/README.md).

## Roadmap auf einen Blick

![Grafische Roadmap von M0 Foundation bis M9 Release und der strategischen E2EE-Spur](./assets/roadmap/roadmap-overview.svg)

**Aktuell:** M0, M1 und M2 sind für ihren vorgesehenen Umfang abgeschlossen. **G1 und G2 sind bestanden. M3 ist als nächster Milestone freigegeben; seine S0-Readiness und alle M3-D01 bis M3-D32 sind abgeschlossen.** Der verbindliche aktuelle Gate-Nachweis ist der [finale G2 Gate Review](./reviews/2026-08-26-g2-final-gate-review.md).

#59 und #60 bleiben verpflichtende Pre-Exposure-Härtungen vor öffentlicher bzw. Managed-Exposition. #25 bleibt Repository-Hardening. Diese Punkte blockieren die interne M3-Entwicklung nicht.

## Dokumentenrollen

| Dokument | beantwortet |
|---|---|
| diese Roadmap | Wohin gehen wir, in welcher Reihenfolge und warum? |
| [Implementation Status](./IMPLEMENTATION-STATUS.md) | Was ist auf `main` tatsächlich umgesetzt oder noch offen? |
| [M2 Project Control](./m2/PROJECT-CONTROL.md) | Welche M2/M5-Grenzen und G2-Kriterien galten? |
| [M3 Technical Readiness Package](./m3/README.md) | Welche M3-Entscheidungen, Gate-Regeln und Runtime-Voraussetzungen gelten? |
| [Finaler G2 Gate Review](./reviews/2026-08-26-g2-final-gate-review.md) | aktuelle Gate-Entscheidung |
| datierte ältere Reviews | historische Prüfsnapshots, die nicht umgeschrieben werden |
| GitHub Issues/PRs | Welche konkreten Arbeitspakete werden bearbeitet? |
| [Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md) | Was ist fachlich und technisch verbindlich? |

## Aktueller Snapshot

### M0 — Foundation: abgeschlossen

API-/DB-Konventionen, Migrationen, Outbox, Jobs, MediaStore-Grundlage, ProtectedPayload-Grenze, versioniertes OpenAPI, PostgreSQL-Integrationstests, Supply-Chain-Prüfungen, Secret Scan und Provenance sind für den Foundation-Umfang vorhanden.

### M1 — Identity & Relationship: abgeschlossen, G1 bestanden

Account/AuthIdentity, Sessions, Space/Membership/Tenant Guard, Invitations, Profile, RelatedPerson/ImportantDate, OIDC, Passkeys, Magic Link, E-Mail-Verifikation und Recovery sind implementiert. PR #64 hat #61 mit expliziter `preserve`-/`cascade`-Semantik ohne destruktiven Default geschlossen; der folgende Gate-Review hat G1 ausdrücklich bestanden erklärt.

### M2 — Erinnern / Story Alpha: abgeschlossen, G2 bestanden

Die blockierenden Domain-, Privacy-, Media- und API-Entscheidungen sind geschlossen. Geliefert sind:

1. #71 — Memory CRUD ohne Medien: **geliefert**.
2. #80 — HeartMoment mit Owner-only-Privacy: **geliefert**.
3. #79 — Attachment-Lifecycle für Bilder: **geliefert**. Video ist nicht Teil von M2/G2 und als zukünftige Entwicklung in #88 vorgemerkt.
4. #90 — Attachments an Memory und HeartMoment binden: **geliefert**.
5. #94 — Milestone-Domain und API: **geliefert**.
6. #97 — Comments, Outbox und Notification Hook: **geliefert**.
7. #87 — S3-kompatibler MediaStore-Adapter: **geliefert**.
8. #113 — Story Read Model und `/timeline`: **geliefert**.
9. S8 — dünne Web-/Android-Referenzflows: **geliefert**.
10. Realer Web-/Android-Memory/Media/Story-E2E gegen API, Worker, PostgreSQL und LocalMediaStore: **nachgewiesen**.

Der [finale G2 Gate Review](./reviews/2026-08-26-g2-final-gate-review.md) bewertet den Stand ausdrücklich mit **G2: BESTANDEN**. Die manuelle Accessibility-Abnahme wurde dabei nicht als bestanden gewertet; sie bleibt Teil der finalen Client-/Release-QA in M5/G4.

Future-Backlog: #88 hält Video-Uploads und Posterframes für eine spätere Neubewertung fest. Der Prototyp #109 wurde wegen eines Produktions-Images von rund 755 MiB und des zusätzlichen ffmpeg-Betriebs-, Supply-Chain- und Security-Aufwands bewusst ohne Merge geschlossen; `main` bleibt für Video fail-closed.

### M3 — Planen & Private Area: freigegeben

Das [M3 Technical Readiness Package](./m3/README.md) ist vorbereitet; M3-D01 bis M3-D32 stehen auf `DECIDED`. Damit ist die fachliche S0-Readiness abgeschlossen. Runtime-Slices dürfen gemäß [M3 Delivery Plan](./m3/DELIVERY-PLAN.md) beginnen, sobald der produktive REST-/OpenAPI-Vertrag des jeweiligen Slices contract-testbar konkretisiert ist und die normalen Reuse-/PR-/CI-Regeln erfüllt sind.

Der erste geplante Runtime-Slice ist **M3-S1 — Wish Foundation**.

## Milestones

| Phase | Menschliches Ziel | Fachlicher Umfang | Ergebnis |
|---|---|---|---|
| **M0 · Foundation** | verlässliche technische Basis | API, DB, Outbox, Jobs, MediaStore, CI, Provenance | sicher erweiterbarer Core |
| **M1 · Verbinden** | zwei Personen bilden einen privaten Space | Identity, Auth, Membership, Invitation, Profile | sicherer Account- und Beziehungsrahmen |
| **M2 · Erinnern / Story Alpha** | gemeinsame Geschichte funktioniert als erster vertikaler Kern | Attachments, Memories, HeartMoments, Milestones, Comments, Story plus minimale Web-/Android-Referenzflows | Domain/API vollständig und kritischer E2E-Flow technisch bewiesen |
| **M3 · Planen & Private Area** | Ideen werden gemeinsame Vorhaben | Wishes, Plans, Places, Chapters, Collections, Private Area | Planung und private Ablage mit eigener Privacy-Grenze |
| **M4 · Begleiten** | hilfreiche, kontrollierte Aktivierung | Search/Dashboard, Activity/Notifications, Reminders/Rules | Read Models und Aktivierung ohne unnötiges Tracking |
| **M5 · Client Completion & Parity** | Web und Android sind vollständig nutzbar | vollständige Clientintegration, Export/Import, Read Cache, Deep Links, Accessibility, Performance, Parität | produktfähiger Core auf beiden Clients |
| **M6 · Vertiefen** | freiwillige gemeinsame Reflexion | Questions, Check-in, Monats-/Jahresrückblicke | Rich Features nach stabilem Core |
| **M7 · Entdecken** | externe Inspiration bleibt optional | Shopping, Rezepte, Events, Unterhaltung, Provideradapter | Integrationen ohne Core-Abhängigkeit |
| **M8 · Kontext** | freiwilliger Ortskontext | Location, Karten, Geofencing, Presence | explizit aktivierbare Kontextfunktionen |
| **M9 · Veröffentlichen** | sicher betreibbares Produkt | Self-Hosted, Cloud, Backup, Entitlements, Hardening, Release | launchfähiger Betrieb |
| **MX · E2EE** | echter kryptografischer Schutz | Schlüsselmodell, Migration, Client-Crypto, Recovery | separat bewertete E2EE-Version |

## Präzisierte Milestone-Grenzen

### M2 vs. M5

M2 ist **nicht backend-only**. M2 enthält dünne Web-/Android-Referenzflows, um den kritischen Memory/Media/Story-Flow Ende-zu-Ende zu beweisen. M2 verspricht aber keine vollständige Client-Parität.

M5 ist die vollständige Client-Produktisierung: vollständige Screens und Navigation, Deep Links, Read Cache, Export/Import, systematische Web-/Android-Parität, Accessibility, Performance und Release-Hardening.

### M4 interne Slices

M4 wird intern in drei getrennte Risikoklassen geschnitten:

- **M4-A:** Search + Dashboard Read Models,
- **M4-B:** Activity + Notifications,
- **M4-C:** Reminders + Rules.

Diese Aufteilung ist eine Delivery-Grenze, keine fachliche Scope-Erweiterung.

### Privacy-Sprache

- `SHARED` / `PRIVATE` sind öffentliche fachliche Domainwerte.
- `SPACE_SHARED` / `OWNER_ONLY` sind interne Authorization-/Privacy-Klassen.
- Clients schreiben `privacyClass` nicht redundant als zweite Wahrheitsquelle.

## M2 Lieferfolge

```text
S0 Readiness
   │
   ├── Memory CRUD ohne Medien
   │        │
   │        ├──────────────┐
   │        │              │
   │   Attachment      HeartMoment
   │        │              │
   │        └── Memory+Media
   │
   ├── Milestone
   ├── Comments + Outbox
   └── Story Read Model
              │
              ▼
      Thin Web/Android E2E
              │
              ▼
             G2 ✓
```

Diese Lieferfolge ist abgeschlossen. Sie validierte zuerst M2-Migrationstil, ProtectedPayload, Tenant Guard, Autorregel und Concurrency auf einer kleineren Sicherheitsfläche und führte anschließend bis zum realen Client-E2E-Nachweis.

## Search-Abgrenzung

Globale Volltextsuche war kein G2-Bestandteil. Der Story-Mindestvertrag umfasst `type`, `year`, `order`, `cursor` und `limit`; globale Volltextsuche liegt in M4-A.

## Abhängigkeiten

```mermaid
flowchart LR
  M0[M0 Foundation] --> M1[M1 Identity & Relationship]
  M1 --> M2[M2 Memories & Story]
  M2 --> M3[M3 Planning & Private Area]
  M2 --> M4[M4 Engagement]
  M3 --> M5[M5 Client Completion & Parity]
  M4 --> M5
  M5 --> M6[M6 Rich Features]
  M5 --> M7[M7 Integrations]
  M7 --> M8[M8 Context]
  M6 --> M9[M9 Productization]
  M8 --> M9
  M0 -. ProtectedPayload boundary .-> MX[MX E2EE]
  M5 -. mature clients .-> MX
```

## Release Gates

### G0 — Foundation prüfbar

**Bestanden.**

### G1 — Sicherer Paar-Space

- Auth- und Recovery-Wege,
- race-sichere Invitations,
- Tenant Guard und Owner-only-Autorisierung,
- Profile/SpaceProfile mit Versionskonflikten,
- Cross-Tenant-, Session- und Privacy-Tests.

**Aktueller Stand: BESTANDEN.** Der datierte [G1 Gate Review nach Abschluss von #61](./reviews/2026-08-25-g1-gate-review-after-61.md) bleibt der historische G1-Nachweis.

### G2 — Story Alpha

**Aktueller Stand: BESTANDEN.** Der [finale G2 Gate Review](./reviews/2026-08-26-g2-final-gate-review.md) ist die aktuelle Gate-Entscheidung.

Nachgewiesen sind insbesondere:

- vollständige M2-Domain/API für Memory, Bild-Attachments, HeartMoment, Milestone, Comments und Story,
- serverseitiger Ausschluss von `OWNER_ONLY` vor Story-Projektion/Pagination,
- Media-/Upload-Abuse, Parent-Autorisierung, Tenant- und Race-/Datenintegritätspfade,
- OpenAPI, Migrationen und PostgreSQL-Integration,
- realer kritischer Memory/Media/Story-Flow in Web und Android gegen denselben SideBySide-Stack,
- aktuelle CI-, Secret-Scan-, Supply-Chain- und Deployment-Gates.

Die manuelle Accessibility-Abnahme ist bewusst **kein G2-Blocker mehr** und wird in M5/G4 als finale Client-/Release-QA durchgeführt. Vollständige Client-Parität bleibt ebenfalls M5/G4.

### G3 — Gemeinsamer Alltag

- Wishes/Plans/Places/Chapters/Collections konsistent,
- Private Area vollständig isoliert,
- Delete-/409-Wirkungen verständlich,
- M4-Read-Model-Grenzen vorbereitet.

### G4 — Core Release Candidate

- Web und Android fachlich gleichwertig,
- Offline Read Cache ohne vorgetäuschten Write Sync,
- Export/Import versioniert und getestet,
- Design-System und Accessibility verifiziert,
- Performance-, Privacy- und Security-Gates bestanden.

### G5 — Launchfähig

- Cloud und Self-Hosted dokumentiert, update- und backupfähig,
- serverseitige Auth-/Provider-Policy je Betriebsform durchgesetzt,
- #59 und #60 vor öffentlicher/Managed-Exposition geschlossen,
- Retention, vollständige Löschung und Supportprozesse geklärt,
- Entitlements/Billing ohne Domainkopplung,
- Monitoring ohne sensible Inhalte,
- Release-, Incident- und Recovery-Prozess getestet.

## Was bewusst nicht vorgezogen wird

- globale Volltextsuche vor geklärter M4-Privacy-/Indexstrategie,
- Shopping, Event Discovery und Providerintegrationen vor stabilem Core,
- Offline Write Sync im MVP,
- öffentliche Share Links,
- KI-Funktionen,
- Location/Geofencing ohne separaten Opt-in- und Privacy-Flow,
- E2EE-Marketing vor echter Implementierung und Review.

## Roadmap-Risiken

| Risiko | Schutzmaßnahme |
|---|---|
| Runtime beginnt vor geklärtem Vertrag | relevante M3-Decisions + contract-testbarer OpenAPI-Vertrag vor jedem Runtime-Slice |
| Web und Android driften auseinander | gemeinsamer OpenAPI-Vertrag und M5-Paritätsgate |
| Privacy-Klassen werden Client-Domain | klare Trennung `SHARED/PRIVATE` vs. `SPACE_SHARED/OWNER_ONLY` |
| Media erzeugt indirekte Leaks | Parent-Autorisierung, Adapter-Contract und Abuse-/Race-Tests |
| Repository-Gates können umgangen werden | PR-/CI-Pflicht als Projektregel bis #25 technisch erzwingbar ist |
| öffentlicher Betrieb erfolgt zu früh | #59/#60 und G5 bleiben Pre-Exposure-Pflicht |

## Pflege

- Datierte Reviews werden nie nachträglich umgeschrieben.
- Der Current-Marker wird nach jedem abgeschlossenen Gate aktualisiert.
- Offene Aufgaben stehen im Implementation Status und in GitHub Issues.
- Roadmap-Updates nennen Grund und Auswirkung, nicht nur eine neue Reihenfolge.

## Verwandte Dokumente

- [Implementation Status](./IMPLEMENTATION-STATUS.md)
- [M2 Project Control](./m2/PROJECT-CONTROL.md)
- [M3 Technical Readiness Package](./m3/README.md)
- [M3 Decision Log](./m3/DECISION-LOG.md)
- [M3 Delivery Plan](./m3/DELIVERY-PLAN.md)
- [Finaler G2 Gate Review](./reviews/2026-08-26-g2-final-gate-review.md)
- [Produktspezifikation](../specification/PRODUCT-SPEC.md)
- [Master Specification](../specification/CLEAN-ROOM-MASTER-SPEC.md)
