# SideBySide Next

Ein privater digitaler Begleiter für das gemeinsame Leben eines Paares.

SideBySide Next ist eine eigenständige Neuimplementierung. Sie wird in zwei
Betriebsformen angeboten:

- **SideBySide Cloud** — betriebener Dienst
- **SideBySide Self-Hosted** — eigene Installation

Beide teilen denselben Application Core.

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
deploy/         Docker Compose für Self-Hosted und Entwicklung
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

## Stand

Milestone M0 — technische Plattform. Siehe [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
für den Zielaufbau und [specification/PRODUCT-SPEC.md](specification/PRODUCT-SPEC.md)
für den fachlichen Umfang.

## Lizenz

Noch nicht festgelegt. Bis zu einer ausdrücklichen Entscheidung gilt für
diesen Quellcode kein Open-Source-Lizenzangebot. Pflichten aus
Drittanbieter-Lizenzen werden erfüllt und in
[docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) dokumentiert.
