# Finaler G2 Gate Review — Story Alpha

**Datum:** 26.08.2026  
**Gate:** G2 — Story Alpha  
**Geprüfter `main`:** `ffead7ef5e00b57012d705d2abb53d257c34611a`  
**Ergebnis:** **G2: BESTANDEN**

> Dieser Review ist ein neuer datierter Gate-Snapshot. Der frühere Review `2026-08-26-g2-gate-review-after-s8.md` bleibt unverändert als historischer Nachweis des damaligen, noch unvollständigen Gate-Stands erhalten.

## 1. Anlass und geänderte Gate-Grenze

Der frühere G2-Review bewertete das Gate als nicht bestanden, weil zwei Nachweise fehlten:

1. ein realer Web-/Android-End-to-End-Lauf gegen API, PostgreSQL und MediaStore;
2. eine manuelle Accessibility-Abnahme der dünnen S8-Referenzflows.

Punkt 1 ist inzwischen über #144 und den versionierten `G2 Client E2E`-Workflow reproduzierbar geschlossen.

Für Punkt 2 wurde die Projektsteuerung am 26.08.2026 bewusst geändert: Manuelle Accessibility-Prüfungen mit Screenreader/NVDA/VoiceOver, TalkBack, 200-%-Browserzoom, größter Android-Schrift/Displaygröße und vollständiger manueller Fokus-/Bedienhilfen-Abnahme sind **kein G2-Blocker mehr**. Sie werden in die finale Client-/Release-QA verschoben, wenn Web und Android funktional vollständig sind. #145 wurde deshalb ohne Erfolgsbehauptung als `not planned` geschlossen; der vorbereitende Draft-PR #153 wurde ungemergt geschlossen.

Diese Änderung bedeutet ausdrücklich **nicht**, dass Accessibility als bestanden gilt. Sie verschiebt nur den Zeitpunkt der manuellen Abnahme.

Unverändert G2-relevant bleiben:

- Security und serverseitige Authorization;
- Privacy und Tenant-Isolation;
- Race-/Concurrency- und Datenintegritätsverhalten;
- OpenAPI-/Migrations-/PostgreSQL-Nachweise;
- reale Client-End-to-End-Evidenz;
- aktuelle CI-, Supply-Chain-, Secret-Scan- und Deployment-Gates.

## 2. Prüfstand

Der geprüfte `main` ist:

```text
ffead7ef5e00b57012d705d2abb53d257c34611a
```

Dieser Commit ist der Merge von PR #169. Der darin enthaltene Runtime-/Self-Hosting-Stand wurde auf dessen exaktem PR-Head

```text
2c78bfd94bd7cc03aced0cfecdde4e92d68ce9ca
```

vollständig durch die relevanten Workflows geprüft. Der Merge-Commit selbst fügt gegenüber diesem Head keine eigenständige Runtime-Änderung hinzu; er verbindet ihn mit dem zuvor gemergten M3-S0-Dokumentationsstand.

Der vorliegende G2-Review wird in einem getrennten, rein dokumentarischen PR erstellt. Vor dessen Merge müssen die Repository-Gates auf dessen exaktem Head erneut grün sein.

## 3. Technische G2-Evidenz

### 3.1 M2-Domain und versionierter API-Vertrag

Für den G2-Scope sind geliefert:

- Memory CRUD;
- Bild-Attachment-Lifecycle und Parent-Bindung;
- HeartMoment mit `OWNER_ONLY`-Grenze;
- Milestone;
- Comments einschließlich Race-/Cascade-Semantik;
- Story Read Model und `/timeline`;
- generator-owned Web-/Android-Vertragsmodelle und dünne Referenzclients.

Video bleibt bewusst außerhalb von M2/G2 und fail-closed; #88 ist Future-Backlog.

**Bewertung:** erfüllt.

### 3.2 Story-Privacy, Tenant-Isolation und Authorization

Die bestehende PostgreSQL-/HTTP-Integrationstestfläche prüft insbesondere:

- `OWNER_ONLY`/private HeartMoments erscheinen nicht in der gemeinsamen Story, auch nicht für ihren Owner;
- `SHARED -> PRIVATE` entfernt sie aus der Story, ohne die getrennte Owner-Sicht aufzuweichen;
- Cross-Space-Zugriffe liefern keine fremden Daten;
- Attachment-Lesbarkeit folgt der Parent-Autorisierung;
- Cross-Space- und Mehrfachbindungen werden verhindert;
- Tenant-/Private-Authorization-Suites bleiben Teil der ausführbaren Integrationstestfläche.

Private Inhalte werden damit nicht durch Clientfilter abgesichert, sondern serverseitig vor Projektion bzw. Auslieferung.

**Bewertung:** erfüllt.

### 3.3 Media-, Race- und Datenintegritäts-Gates

Die Integrationstests decken unter anderem ab:

- Upload -> Finalize -> `READY` -> Bindung -> autorisiertes Lesen;
- MIME-/Magic-Byte-, Größen- und Typprüfung;
- fail-closed bei ungültigen/nicht erlaubten Medien;
- idempotentes Finalize;
- Parent-gebundene Media-Autorisierung;
- konkurrierende Bindungen;
- Comment-/Privacy-/Delete-Races über echte PostgreSQL-Transaktionen;
- Migrationen und vollständige PostgreSQL-Integration.

**Bewertung:** erfüllt.

### 3.4 Aktuelle Repository-CI

Auf dem in `main` enthaltenen PR-Head `2c78bfd94bd7cc03aced0cfecdde4e92d68ce9ca` lief **CI Run #431** (`32999927122`) vollständig erfolgreich.

Der Run belegte unter anderem:

- **Backend:** sichere Self-Hosted-Konfiguration, Lint, Formatierung, Typprüfung, OpenAPI-Vertrag und Tests;
- **Backend Integration:** Migrationen, Migrationsvollständigkeit und tatsächlich ausgeführte PostgreSQL-Integrationstests;
- **API Clients:** generierter Client-Code stimmt mit dem veröffentlichten Vertrag überein;
- **Secret Scan:** erfolgreich;
- **Supply Chain:** Lockfile, Dependency-/Vulnerability-Scan sowie reproduzierbare Backend-/Web-Produktionsbuilds;
- **Provenance:** erfolgreich;
- **Self-Hosted Start:** Stackstart, Migration, Healthchecks, wiederholbare Migration und Production-Konfigurationsschutz erfolgreich.

Zusätzlich war der **Self-Hosted Deployment Guard #128** erfolgreich. Der aktuelle Reuse-Review für PR #169 wurde nach Korrektur der PR-Metadaten ebenfalls erfolgreich abgeschlossen; ein vorheriger Reuse-Review-Fehllauf wurde damit ersetzt und ist kein aktueller technischer Befund.

**Bewertung:** erfüllt.

### 3.5 Echter Web-/Android-End-to-End-Nachweis

**G2 Client E2E Run #14** (`32999926869`) lief auf demselben PR-Head erfolgreich und startete einen realen isolierten SideBySide-Stack mit:

- API;
- Worker;
- PostgreSQL;
- LocalMediaStore.

Der Workflow bootstrappt einen synthetischen Account und dessen echten Space. Danach:

1. verwendet Web den produktiven S8-/OpenAPI-Pfad gegen diesen Stack;
2. führt Web den E2E tatsächlich aus und nicht nur einen Mock-/Skip-Pfad;
3. verwendet Android `OkHttpReferenceApi` gegen denselben realen Stack;
4. führt Android den E2E tatsächlich aus und nicht nur eine Fake-Implementierung;
5. wird der isolierte Teststack anschließend wieder abgebaut.

Damit ist die frühere Nachweislücke aus #143/#144 geschlossen: Client -> HTTP -> API -> PostgreSQL -> MediaStore -> Story/Read wird auf beiden Plattformen gegen reale Infrastruktur ausgeführt.

**Bewertung:** erfüllt.

## 4. Offene Punkte außerhalb des G2-Gates

Die offenen Issues wurden gegen den G2-Scope abgegrenzt:

- **#59** Passkey-Challenge-Flooding: P1-/Pre-Exposure-Härtung vor öffentlicher bzw. Managed-Exposition, kein aktueller Auth-Bypass und kein M2-G2-Blocker;
- **#60** atomare Rate-Limit-Schwellen: P1-/Pre-Exposure-Härtung vor öffentlicher bzw. Managed-Exposition, kein M2-G2-Blocker;
- **#121** leere `SBS_DATABASE_URL`: Konfigurations-/Fehlermeldungs-Härtung, kein offener M2-Datenintegritäts- oder Privacy-Blocker;
- **#138** Android-Passkey-Generator: Tooling-Follow-up außerhalb des M2-S8-Referenzflows;
- **#25** Branch Protection: Repository-Hardening; bis zur technischen Erzwingung gelten PR + CI als verbindliche Projektregel;
- **#88** Video: Future-Backlog, ausdrücklich außerhalb von M2/G2.

Aus den aktuell offenen Issues ergibt sich damit kein offener Blocker-/kritischer/hoher Security-, Privacy- oder Datenintegritätsbefund **im M2-G2-Scope**.

## 5. Accessibility bleibt offene Abschluss-QA

Nicht als G2-Evidenz behauptet und nicht durchgeführt sind insbesondere:

- Screenreader/NVDA/VoiceOver;
- TalkBack;
- 200-%-Browserzoom;
- größte Android-Schrift/Displaygröße;
- vollständige manuelle Fokus-/Bedienhilfen-Abnahme.

Diese Punkte bleiben verpflichtende spätere Client-/Release-QA. Automatisierte Semantics-/DOM-Checks bleiben sinnvoller Regressionsschutz, ersetzen diese spätere manuelle Abnahme aber nicht.

## 6. Gate-Matrix

| G2-Kriterium | Ergebnis | Evidenz |
|---|---|---|
| M2-Domain/API für Story Alpha vollständig | **erfüllt** | gemergte M2-Slices + versionierter Vertrag |
| `OWNER_ONLY` vor Story-Projektion/Pagination ausgeschlossen | **erfüllt** | Story-/Privacy-Integrationstests |
| Media-Abuse und Parent-Autorisierung | **erfüllt** | Attachment-/Binding-Integrationstests |
| Cross-Tenant-/Race-/Datenintegritätspfade | **erfüllt** | PostgreSQL-/HTTP-Integrationstestfläche |
| OpenAPI und generierte Clients konsistent | **erfüllt** | CI #431 / API Clients |
| Migrationen + PostgreSQL-Integration grün | **erfüllt** | CI #431 / Backend Integration |
| Web realer Memory/Media/Story-E2E | **erfüllt** | G2 Client E2E #14 |
| Android realer Memory/Media/Story-E2E | **erfüllt** | G2 Client E2E #14 |
| Secret Scan / Supply Chain / Provenance / Self-Hosted Gates | **erfüllt** | CI #431 + Deployment Guard #128 |
| keine offene hohe/kritische M2-Security-/Privacy-/Datenintegritätslücke | **erfüllt** | offene Issues gegen G2-Scope geprüft |
| manuelle Accessibility-Abnahme | **nicht Teil von G2** | verpflichtend in finaler Client-/Release-QA |
| vollständige Client-Parität | **nicht Teil von G2** | M5 / späteres Release-Gate |

## 7. Gate-Entscheidung

**G2: BESTANDEN.**

Die technische Story-Alpha-Grenze ist auf dem geprüften Stand belastbar nachgewiesen:

- Domain/API und Privacy-Grenzen sind implementiert;
- PostgreSQL-/HTTP-Integration, OpenAPI und Clients sind grün;
- Web und Android durchlaufen den kritischen Memory/Media/Story-Pfad gegen einen realen SideBySide-Stack;
- die aktuellen Security-, Supply-Chain- und Deployment-Gates sind grün;
- es besteht kein offener G2-blockierender Security-/Privacy-/Datenintegritätsbefund.

Die Entscheidung behauptet **keine abgeschlossene Accessibility-Abnahme**. Diese bleibt bewusst für die finale Client-/Release-QA offen.

## 8. Folge

Nach Merge dieses Reviews ist **#146** der nächste verpflichtende Schritt. Dort werden die aktiven Statusquellen (`README.md`, `docs/ROADMAP.md`, `docs/IMPLEMENTATION-STATUS.md`, `docs/m2/PROJECT-CONTROL.md`) auf denselben finalen Gate-Stand synchronisiert.

Erst nach diesem Status-Sync wird M3-Runtime als freigegeben geführt. Das M3-S0-Readiness-/Decision-Paket ist bereits vollständig vorbereitet.

Öffentliche bzw. Managed-Exposition bleibt unabhängig davon bis zur vorgesehenen Pre-Exposure-/Release-Härtung, insbesondere #59/#60, gesperrt.
