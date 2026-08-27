# SideBySide Next

Ein privater digitaler Begleiter für das gemeinsame Leben eines Paares.

SideBySide Next ist eine eigenständige Neuimplementierung. Sie wird in zwei
Betriebsformen angeboten:

- **SideBySide Cloud** — betriebener Dienst für Nutzer, die keine eigene Infrastruktur administrieren möchten
- **SideBySide Self-Hosted** — eigene Installation für persönliche und nichtkommerzielle Nutzung

Beide teilen denselben Application Core. Die Cloud monetarisiert Betrieb,
Komfort und Service; Self-Hosted soll nicht allein zur Verkaufsförderung
künstlich um Kernfunktionen beschnitten werden. Das strategische Modell ist in
[docs/BUSINESS-MODEL.md](docs/BUSINESS-MODEL.md) dokumentiert.

## Produktvorschau

<p align="center">
  <img src="docs/assets/playstore/app-icon.png" alt="SideBySide Next App-Icon" width="112">
</p>

<p align="center">
  <img src="docs/assets/playstore/feature-graphic.png" alt="SideBySide Next – gemeinsam leben, privat verbunden" width="100%">
</p>

<p align="center">
  <strong>Erinnerungen, Wünsche, Pläne und gemeinsame Zeit – ruhig gestaltet und privacy-first gedacht.</strong>
</p>

> Die folgenden Screens sind Produkt- und Google-Play-Mockups. Der technische
> Implementierungsstand ist im Abschnitt [Stand](#stand) dokumentiert.

### Design- und UX-Grundlagen

- [Design-Prinzipien](docs/DESIGN-PRINCIPLES.md) – visuelle Sprache, Accessibility und Privacy-first Leitlinien
- [Informationsarchitektur](docs/INFORMATION-ARCHITECTURE.md) – Navigation, Bereiche, Routen und Deep Links
- [Critical User Flows](docs/USER-FLOWS.md) – End-to-End-Abläufe für Auth, Einladung, Inhalte, Offline und Konflikte
- [UX-Patterns](docs/UX-PATTERNS.md) – plattformübergreifende Interaktions- und Zustandsmuster
- [Screen-Templates](docs/SCREEN-TEMPLATES.md) – responsive Layouts für Compact, Medium und Expanded
- [Component Contracts](docs/COMPONENT-CONTRACTS.md) – Verhalten, Varianten und Accessibility gemeinsamer Bausteine
- [API-/UI-Verträge](docs/API-UI-CONTRACTS.md) – gemeinsame DTOs, Fehler, Privacy-Klassen, Cache und Concurrency
- [Accessibility- und QA-Matrix](docs/ACCESSIBILITY-QA-MATRIX.md) – verbindliche Release Gates für Web und Android
- [Content- und Privacy-Guidelines](docs/CONTENT-PRIVACY-GUIDELINES.md) – Tonalität, Systemtexte, Notifications und Analytics-Grenzen
- [Design-System-Umsetzung](docs/DESIGN-SYSTEM-DELIVERY.md) – Token-Pipeline, Komponentenstufen und Lieferphasen
- [Design-Tokens](design/tokens.json) – Farben, Typografie, Abstände, Layout und Motion als maschinenlesbare Quelle
- [Component Manifest](design/component-manifest.json) – plattformübergreifender Implementierungsstatus

<table>
  <tr>
    <th>Gemeinsam starten</th>
    <th>Unser Heute</th>
    <th>Unsere Story</th>
    <th>Unsere Wünsche</th>
  </tr>
  <tr>
    <td><img src="docs/assets/playstore/screen-01-onboarding.png" alt="Onboarding-Mockup" width="200"></td>
    <td><img src="docs/assets/playstore/screen-02-heute.png" alt="Heute-Mockup" width="200"></td>
    <td><img src="docs/assets/playstore/screen-03-story.png" alt="Story-Mockup" width="200"></td>
    <td><img src="docs/assets/playstore/screen-04-wuensche.png" alt="Wünsche-Mockup" width="200"></td>
  </tr>
  <tr>
    <th>Gemeinsam planen</th>
    <th>Für euch entdecken</th>
    <th>Gemeinsam einkaufen</th>
    <th>Privatsphäre</th>
  </tr>
  <tr>
    <td><img src="docs/assets/playstore/screen-05-plan.png" alt="Planungs-Mockup" width="200"></td>
    <td><img src="docs/assets/playstore/screen-06-discovery.png" alt="Discovery-Mockup" width="200"></td>
    <td><img src="docs/assets/playstore/screen-07-einkauf.png" alt="Einkaufs-Mockup" width="200"></td>
    <td><img src="docs/assets/playstore/screen-08-privacy.png" alt="Privacy-Mockup" width="200"></td>
  </tr>
</table>

## Roadmap

<p align="center">
  <a href="docs/ROADMAP.md">
    <img src="docs/assets/roadmap/roadmap-overview.svg" alt="SideBySide Next Roadmap von Foundation bis Release" width="100%">
  </a>
</p>

<p align="center">
  <strong>Aktuell: G2 ist bestanden. M2 ist abgeschlossen; M3 ist als nächster Milestone freigegeben.</strong><br>
  <a href="docs/ROADMAP.md">Roadmap, parallele Arbeitsströme und Release Gates ansehen</a> ·
  <a href="docs/IMPLEMENTATION-STATUS.md">tatsächlichen Umsetzungsstand öffnen</a> ·
  <a href="docs/m3/README.md">M3 Technical Readiness Package öffnen</a>
</p>

## Leitsätze

Privatsphäre ist Kernfunktion, nicht Beiwerk. Keine Werbung, kein Verkauf
persönlicher Daten, kein unnötiges Tracking. Sensible Inhalte fließen nicht
in Analytics.

Der zentrale Mandant heißt **Space** — der gemeinsame Raum eines Paares.
Jeder gemeinsame Datensatz gehört genau einem Space. Kein Zugriff erfolgt
allein anhand einer Ressourcen-ID.

Für M2 gilt zusätzlich: `SHARED` und `PRIVATE` sind fachliche Domainwerte.
`SPACE_SHARED` und `OWNER_ONLY` sind interne Authorization-/Privacy-Klassen.
Clients schreiben `privacyClass` nicht redundant als zweite Wahrheitsquelle.

## Aufbau

```
backend/             FastAPI, SQLAlchemy 2, Alembic, PostgreSQL
web/                 React, TypeScript, Vite
android/             Kotlin, Jetpack Compose
compose.yaml         Docker Compose für vollständige Self-Hosted-Checkouts
compose.arcane.yaml  Remote-Git-Builds für Arcane/Remote-Workspaces
deploy/              Docker Compose für die Entwicklungsdatenbank
docs/                Architektur, Sicherheit, Datenschutzmodell, Abhängigkeiten
specification/       Produktspezifikation als verbindliche Vorgabe
tools/               Hilfsskripte
```

## Entwicklung

### Voraussetzungen

- **Docker** für die Entwicklungsdatenbank
- **Python 3.13** und `uv` für Backend und Tests
- **Node 22 und npm** für den Web-Client

PostgreSQL ist Voraussetzung. Einen SQLite-Notbehelf gibt es bewusst nicht —
das Datenmodell nutzt PostgreSQL-Eigenschaften, und ein zweiter Dialekt im
Test würde eine Sicherheit vortäuschen, die er nicht gibt.

### Backend

```bash
docker compose -f deploy/docker-compose.dev.yml up -d
python -m pip install uv==0.12.5
cd backend && uv sync --frozen
uv run alembic upgrade head
uv run uvicorn sidebyside.main:app --reload
```

### Web

```bash
cd web && npm ci
npm run dev
```

### Tests

Integrationstests laufen gegen eine eigene Datenbank `sidebyside_test`, die
`deploy/docker-compose.dev.yml` beim ersten Start mit anlegt. Die
Testvorrichtung legt dort ihr Schema selbst an und räumt es am Ende wieder
ab — gegen die Entwicklungsdatenbank wäre das kein Testlauf, sondern ein
Datenverlust.

```bash
export SBS_TEST_DATABASE_URL=postgresql+psycopg://sidebyside:sidebyside@localhost:5432/sidebyside_test
cd backend && uv run pytest                    # alles
cd backend && uv run pytest -m "not integration"   # ohne Datenbank
```

**Ohne `SBS_TEST_DATABASE_URL` werden alle Integrationstests übersprungen** —
auch dann, wenn die Entwicklungsdatenbank läuft und erreichbar ist. `pytest`
meldet den Lauf trotzdem grün, etwa als `353 passed, 1141 skipped`. Ein
vollständiger Lauf ist das nicht. Übersprungen heißt übersprungen und wird
nicht stillschweigend als bestanden gewertet; wer die Variable nicht setzt,
prüft nur die Unit-Ebene.

Stammt das Datenbank-Volume noch aus der Zeit vor dem Init-Skript, fehlt
`sidebyside_test`. Das Postgres-Image führt `deploy/postgres-init/` nur bei
einem leeren Datenverzeichnis aus. Einmalig nachlegen:

```bash
docker compose -f deploy/docker-compose.dev.yml exec postgres \
  createdb -U sidebyside sidebyside_test
```

Der Web-Client wird mit `cd web && npm test` geprüft.

`backend/uv.lock` ist der verbindliche, plattformübergreifende
Abhängigkeitsstand. Nach einer beabsichtigten API-Änderung wird der
versionierte Vertrag mit `uv run python scripts/openapi_contract.py write`
aktualisiert; die CI vergleicht ihn mit dem Schema der tatsächlichen App.

## Self-Hosted

Für einen vollständigen Repository-Checkout bleibt `compose.yaml` der normale
Einstieg:

```bash
cp .env.example .env    # und ausfüllen
docker compose up -d
```

Die API ist danach unter `http://127.0.0.1:8000` erreichbar. Dieser
Klartextzugang ist absichtlich auf den lokalen Rechner begrenzt. Fuer Zugriff
aus LAN oder Internet muss ein HTTPS-Reverse-Proxy vorgeschaltet werden; die
API darf dafuer nicht direkt auf allen Interfaces veroeffentlicht werden.

Verwaltungsoberflächen wie **Arcane**, deren Projekt-Workspace nicht den
vollständigen Repository-Checkout enthält, verwenden stattdessen
`compose.arcane.yaml`. Diese Variante baut `backend` und `web` direkt aus dem
konfigurierten Git-Repository und benötigt deshalb keine lokalen
`./backend`-/`./web`-Verzeichnisse im Workspace. Einrichtung, private
Repositorys und Release-Refs sind in [docs/ARCANE.md](docs/ARCANE.md)
dokumentiert.

Der Dienst `migrate` zieht das Schema einmalig hoch, bevor `api` und
`worker` starten. Die Anwendung migriert nicht selbst; zwei startende
API-Container würden das sonst gleichzeitig tun.

Der vollstaendige sichere Startablauf, Reverse-Proxy-Anforderungen und ein
Smoke-Test stehen in [docs/SELF-HOSTING.md](docs/SELF-HOSTING.md).

## Stand

**M0 — technische Plattform abgeschlossen.** Fehlerformat, Transactional
Outbox, Job-Warteschlange, MediaStore- und Provider-Schnittstellen,
ProtectedPayload-Grenze, reproduzierbare Dependencies, OpenAPI-Contract und
CI-/Supply-Chain-Prüfungen sind für den M0-Umfang vorhanden.

**M1 / G1 — abgeschlossen und bestanden.** Account, Space, Membership,
Tenant Context, Owner-/Privacy-Guard und Geraetesitzungen mit rotierenden
Tokens sind implementiert. Lokales Passwort, OIDC mit PKCE/State/Nonce,
OIDC-Einladungs-Onboarding, Passkeys, Magic Link, E-Mail-Verifikation,
Recovery, Invitations, SpaceProfile, PartnerProfile/ProfilePreference sowie
RelatedPerson/ImportantDate sind im Backend vorhanden und durch
PostgreSQL-/Privacy-/Tenant-Tests abgesichert. #61 wurde mit einer expliziten
`preserve`-/`cascade`-Delete-Policy ohne destruktiven Default geschlossen.

Der [G1 Gate Review nach Abschluss von #61](docs/reviews/2026-08-25-g1-gate-review-after-61.md)
setzt G1 auf **BESTANDEN**. #59 und #60 bleiben verpflichtende
Pre-Exposure-Härtungen vor öffentlichem/Managed-Betrieb; #25 bleibt
Repository-Hardening.

**M2 / G2 — abgeschlossen und bestanden.** Memory CRUD, HeartMoment mit
Owner-only-Privacy, Bild-Attachments samt sicherem Ingest und Bindung,
Milestone, Comments, S3-kompatibler MediaStore, Story Read Model sowie die
dünnen Web-/Android-Referenzflows sind geliefert. Der reale kritische
Memory/Media/Story-Flow wurde gegen API, Worker, PostgreSQL und LocalMediaStore
auf beiden Clientpfaden nachgewiesen.

Der [finale G2 Gate Review](docs/reviews/2026-08-26-g2-final-gate-review.md)
setzt G2 ausdrücklich auf **BESTANDEN**. Die manuelle Accessibility-Abnahme
wurde dabei nicht als bestanden behauptet; sie bleibt Teil der späteren
Client-/Release-QA in M5/G4.

**M3 — freigegeben.** Die S0-Readiness und alle M3-D01 bis M3-D32 sind
`DECIDED`. Runtime-Slices dürfen nach dem
[M3 Technical Readiness Package](docs/m3/README.md) und dem
[M3 Delivery Plan](docs/m3/DELIVERY-PLAN.md) beginnen, sobald der jeweilige
produktive REST-/OpenAPI-Vertrag contract-testbar konkretisiert ist.

Siehe [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) für den Zielaufbau,
[docs/SECURITY.md](docs/SECURITY.md) für die Sicherheitsinvarianten,
[docs/m3/README.md](docs/m3/README.md) für das M3-Readiness-Paket und
[specification/PRODUCT-SPEC.md](specification/PRODUCT-SPEC.md) für den
fachlichen Umfang.

## Projektsteuerung

Die vollständige verbindliche Vorgabe ist die
[Clean-Room Master Specification](specification/CLEAN-ROOM-MASTER-SPEC.md).
Der [laufende Umsetzungsstand](docs/IMPLEMENTATION-STATUS.md) enthält die
aktuelle Arbeitsliste. Datierte Dateien unter [docs/reviews](docs/reviews)
sind unveränderliche Prüf-Snapshots; bei Widersprüchen gilt immer die
Master-Spezifikation.

Parallele Implementierungsarbeit wird über klar abgegrenzte GitHub Issues,
eigene Branches und Pull Requests koordiniert. Solange Branch Protection bei
diesem privaten Repository tarifbedingt nicht technisch erzwungen werden
kann, gilt die PR-/CI-Pflicht als Projektregel.

## Lizenz

Der eigene SideBySide-Next-Quellcode wird unter der **PolyForm Noncommercial
License 1.0.0** bereitgestellt. Nichtkommerzielle Nutzung, Änderung und
Weitergabe sind im Rahmen dieser Lizenz erlaubt. Für kommerzielle Nutzung ist
eine separate kommerzielle Lizenz des Rechteinhabers erforderlich.

- [LICENSE](LICENSE) — PolyForm Noncommercial License 1.0.0
- [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md) — kommerzielle Lizenzierung
- [CONTRIBUTING.md](CONTRIBUTING.md) und [CLA.md](CLA.md) — Beiträge und Rechte an Contributions
- [TRADEMARKS.md](TRADEMARKS.md) — Name, Logo und Branding
- [docs/BUSINESS-MODEL.md](docs/BUSINESS-MODEL.md) — Self-Hosted, SideBySide Cloud und Produktprinzipien

SideBySide Next ist damit **source-available**, nicht Open Source im engeren
OSI-Sinn, da kommerzielle Nutzung nicht allgemein freigegeben wird.
Drittanbieter-Abhängigkeiten bleiben unter ihren jeweiligen Lizenzen; die
Pflichten sind in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) dokumentiert.
