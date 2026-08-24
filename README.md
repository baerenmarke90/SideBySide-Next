# SideBySide Next

Ein privater digitaler Begleiter für das gemeinsame Leben eines Paares.

SideBySide Next ist eine eigenständige Neuimplementierung. Sie wird in zwei
Betriebsformen angeboten:

- **SideBySide Cloud** — betriebener Dienst
- **SideBySide Self-Hosted** — eigene Installation

Beide teilen denselben Application Core.

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


## Leitsätze

Privatsphäre ist Kernfunktion, nicht Beiwerk. Keine Werbung, kein Verkauf
persönlicher Daten, kein unnötiges Tracking. Sensible Inhalte fließen nicht
in Analytics.

Der zentrale Mandant heißt **Space** — der gemeinsame Raum eines Paares.
Jeder gemeinsame Datensatz gehört genau einem Space. Kein Zugriff erfolgt
allein anhand einer Ressourcen-ID.

## Aufbau

```
backend/        FastAPI, SQLAlchemy 2, Alembic, PostgreSQL
web/            React, TypeScript, Vite
android/        Kotlin, Jetpack Compose
compose.yaml    Docker Compose für Self-Hosted
deploy/         Docker Compose für die Entwicklungsdatenbank
docs/           Architektur, Sicherheit, Datenschutzmodell, Abhängigkeiten
specification/  Produktspezifikation als verbindliche Vorgabe
tools/          Hilfsskripte
```

## Entwicklung

PostgreSQL ist Voraussetzung. Einen SQLite-Notbehelf gibt es bewusst nicht —
das Datenmodell nutzt PostgreSQL-Eigenschaften, und ein zweiter Dialekt im
Test würde eine Sicherheit vortäuschen, die er nicht gibt.

```bash
docker compose -f deploy/docker-compose.dev.yml up -d
cd backend && pip install -e ".[dev]"
alembic upgrade head
uvicorn sidebyside.main:app --reload
```

Tests:

```bash
cd backend && pytest                    # alles
cd backend && pytest -m "not integration"   # ohne Datenbank
```

Integrationstests brauchen eine erreichbare PostgreSQL-Instanz. Ohne sie
werden sie übersprungen, nicht stillschweigend als bestanden gewertet.

## Self-Hosted

```bash
cp .env.example .env    # und ausfüllen
docker compose up -d
```

`compose.yaml` liegt bewusst im Wurzelverzeichnis: der Build-Kontext
`./backend` muss unterhalb des Verzeichnisses liegen, in dem die
Compose-Datei steht. Oberflächen wie Arcane oder Portainer legen jedes
Projekt in einem eigenen Verzeichnis ab — ein Pfad wie `../backend` zeigt
dort ins Leere. Das ganze Repository ist deshalb das Projektverzeichnis.

Der Dienst `migrate` zieht das Schema einmalig hoch, bevor `api` und
`worker` starten. Die Anwendung migriert nicht selbst; zwei startende
API-Container würden das sonst gleichzeitig tun.

## Stand

**M0 — technische Plattform.** Fehlerformat, Transactional Outbox,
Job-Warteschlange, MediaStore- und Provider-Schnittstellen, E2EE-Grenze.

**Sicherheitsgrundlage.** Account, Space, Membership, Tenant Context und
Membership Guard, dazu Geraetesitzungen mit rotierenden Tokens. Jeder
Zugriff auf Space-Daten laeuft durch `require_membership`, bevor eine
Ressource geladen wird.

Als Naechstes M1: Anmeldewege (Magic Link, Passkey, OIDC, lokales
Passwort), Invitations, Partnerprofile und Praeferenzen.

Siehe [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) für den Zielaufbau,
[docs/SECURITY.md](docs/SECURITY.md) für die Sicherheitsinvarianten und
[specification/PRODUCT-SPEC.md](specification/PRODUCT-SPEC.md) für den
fachlichen Umfang.

## Projektsteuerung

Die vollständige verbindliche Vorgabe ist die
[Clean-Room Master Specification](specification/CLEAN-ROOM-MASTER-SPEC.md).
Der [laufende Umsetzungsstand](docs/IMPLEMENTATION-STATUS.md) enthält die
aktuelle Arbeitsliste. Datierte Dateien unter [docs/reviews](docs/reviews)
sind unveränderliche Prüf-Snapshots; bei Widersprüchen gilt immer die
Master-Spezifikation.

## Lizenz

Noch nicht festgelegt. Bis zu einer ausdrücklichen Entscheidung gilt für
diesen Quellcode kein Open-Source-Lizenzangebot. Pflichten aus
Drittanbieter-Lizenzen werden erfüllt und in
[docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) dokumentiert.
