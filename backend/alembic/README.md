# Alembic-Code-Policy

Alembic-Migrationen sind ausführbarer Teil der Datenbank-Historie. Neue
Migrationen unterliegen deshalb derselben Ruff-Lint- und Format-Policy wie
der übrige Python-Code, bereits angewandte historische Migrationen werden
aber nicht nachträglich ausschließlich für Stiländerungen umgeschrieben.

## Historischer Bestand

Die Migrationen `0001` bis einschließlich `0007` entstanden vor Einführung
dieser Policy. Sie sind in `pyproject.toml` **einzeln und vollständig
benannt** von Ruff ausgenommen. Diese Liste ist bewusst keine Wildcard:
Eine neue Migration kann dadurch nicht versehentlich in die Ausnahme fallen.

Insbesondere bleibt `0005_auth_architecture.py` trotz abweichender
Ruff-Formatierung unverändert. Das ist eine bewusste Grandfathering-Entscheidung
für bereits angewandte Migrationen und keine allgemeine Ausnahme für Alembic.

Historische Migrationen werden nur geändert, wenn eine konkrete funktionale
Korrektur notwendig ist. Eine solche Änderung braucht ein eigenes Issue/PR
und passende Upgrade-/Downgrade-/Regressionstests; reine Stiländerungen sind
kein ausreichender Grund.

## Neue Migrationen

Alle neu angelegten Python-Migrationen sowie `alembic/env.py` müssen die
aktuelle Ruff-Policy erfüllen. Die CI prüft deshalb ausdrücklich auch den
Pfad `alembic`:

```bash
uv run --frozen ruff check src tests scripts alembic
uv run --frozen ruff format --check src tests scripts alembic
```

Schlägt eine neue Migration dabei fehl, wird sie vor dem Merge korrigiert.
Die explizite Ausschlussliste darf nicht erweitert werden, um einen neuen
Lint-/Formatfehler zu umgehen; eine Erweiterung wäre eine neue bewusste
Policy-Entscheidung und muss entsprechend begründet werden.

## Migrationssemantik

Ruff ist nur ein Codequalitäts-Gate und ersetzt keine Datenbankprüfung. Die
bestehenden CI-Prüfungen für `alembic upgrade head` und Schema-Drift bleiben
unverändert verbindlich. Funktionale Änderungen an Migrationen müssen
zusätzlich die jeweils relevanten Upgrade-/Downgrade- und
PostgreSQL-Regressionsprüfungen bestehen.
