# Abhängigkeiten und Assets

Jede Abhängigkeit wird mit Name, Version, Quelle und Lizenz geführt. Jedes
Asset mit Ursprung, Lizenz und Ersteller. Was hier nicht steht, gehört
nicht ins Projekt.

Stand: 2026-08-23

## Backend — Laufzeit

| Paket | Version | Quelle | Lizenz |
|---|---|---|---|
| fastapi | 0.141.1 | PyPI | MIT |
| uvicorn[standard] | 0.52.4 | PyPI | BSD-3-Clause |
| sqlalchemy | 2.0.52 | PyPI | MIT |
| alembic | 1.19.1 | PyPI | MIT |
| psycopg[binary] | 3.3.4 | PyPI | **LGPL-3.0-only** |
| pydantic | 2.13.4 | PyPI | MIT |
| pydantic-settings | 2.15.0 | PyPI | MIT |
| uuid6 | 2025.0.1 | PyPI | MIT |

## Backend — Entwicklung

| Paket | Version | Quelle | Lizenz |
|---|---|---|---|
| pytest | 9.1.1 | PyPI | MIT |
| pytest-asyncio | 1.4.0 | PyPI | Apache-2.0 |
| httpx | 0.28.1 | PyPI | BSD-3-Clause |
| httpx2 | 2.12.0 | PyPI | BSD-3-Clause |
| ruff | 0.16.4 | PyPI | MIT |
| mypy | 2.3.1 | PyPI | MIT |

## Container-Basisimages

| Image | Version | Quelle | Lizenz |
|---|---|---|---|
| python | 3.13-slim | Docker Hub | PSF-2.0 (Python), Debian-Pakete je eigene Lizenz |
| postgres | 17-alpine | Docker Hub | PostgreSQL License |

## Web und Android

Noch keine Abhängigkeiten. Die Clients beginnen mit Milestone M5.

## Zu prüfen: psycopg unter LGPL

`psycopg` steht unter **LGPL-3.0-only** und ist damit die einzige
Abhängigkeit, deren Lizenz nicht permissiv ist.

Die praktische Lage:

- Der Treiber wird als eigenständiges Paket dynamisch geladen, nicht in
  eigenen Code hineinkompiliert.
- Für den betriebenen Cloud-Dienst liegt keine Weitergabe vor; die LGPL
  greift dort typischerweise nicht.
- Für die Self-Hosted-Auslieferung als Container-Image liegt eine
  Weitergabe vor. Die LGPL verlangt dann unter anderem, dass Empfänger den
  Treiber durch eine eigene Fassung ersetzen können und dass Lizenztext
  und Quellenhinweis beiliegen.

Das ist bei einem separat installierten Python-Paket erfüllbar, aber es
ist eine bewusste Auflage und keine Formalie. Vor dem kommerziellen Start
gehört sie geprüft — gegebenenfalls durch Wechsel auf einen permissiv
lizenzierten Treiber.

Diese Einschätzung ist keine Rechtsberatung.

## Assets

Zum Zeitpunkt dieses Eintrags enthält das Repository **keine** Bild-,
Schrift-, Ton- oder Symboldateien.

Branding-Assets werden nur aufgenommen, wenn sie ausdrücklich für
SideBySide Next bereitgestellt wurden. Assets ungeklärter Herkunft werden
nicht aufgenommen — auch nicht vorläufig.

| Asset | Ursprung | Ersteller | Lizenz |
|---|---|---|---|
| — | — | — | — |

## Pflege

Eine neue Abhängigkeit wird zusammen mit ihrem Eintrag hier hinzugefügt.
Die CI prüft, dass diese Datei existiert; ihre Vollständigkeit liegt beim
Review.
