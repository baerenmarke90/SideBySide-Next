# Statusquellen und Drift-Regeln

## Zweck

Dieses Dokument legt fest, welche Projektdateien den laufenden Stand beschreiben und welche bewusst unveraenderliche historische Snapshots sind.

## Living Status

Diese Dateien werden als laufende Statusquellen gepflegt und vom automatisierten Drift-Guard geprueft:

- `docs/IMPLEMENTATION-STATUS.md` — tatsaechlich gelieferter und noch offener Arbeitsstand;
- `docs/ROADMAP.md` — aktuelle Milestone-/Gate-Orientierung und Priorisierung.

Fuer diese Dateien gelten folgende Regeln:

1. GitHub ist die kanonische Quelle fuer den aktuellen `main`-Commit sowie Issue-/PR-Zustaende.
2. Ein statisch eingetragener angeblich aktueller `main`-SHA ist verboten. Er waere nach dem naechsten Merge zwangsläufig veraltet.
3. Ein GitHub-Issue darf nur als offene Markdown-Task (`- [ ] ... #123`) gefuehrt werden, solange GitHub das Issue tatsaechlich als `open` meldet.
4. Bei Gate-/Milestone-Merges werden die fachlichen Current-Marker und der naechste Runtime-/Pruefpunkt aktualisiert.
5. GitHub-Issues und Pull Requests bleiben die operative Quelle fuer einzelne Arbeitspakete; Living-Status-Dokumente sind keine zweite Issue-Datenbank.

## Historische Snapshots

Datierte Reviews unter `docs/reviews/` sind historische Nachweise. Sie werden nach ihrer Erstellung nicht umgeschrieben, auch wenn darin ein damaliger `main`-SHA, offene Findings oder damalige Issue-Zustaende stehen.

Dasselbe gilt fuer ausdruecklich datierte Entscheidungs- oder Gate-Snapshots, sofern ihre Dokumentenrolle sie als historischen Nachweis ausweist.

Der Drift-Guard scannt solche Dateien deshalb absichtlich nicht.

## Automatisierter Guard

`tools/ci/status_drift.py` prueft die Living-Status-Dateien.

Lokal ohne Netzwerk:

```bash
python3 tools/ci/test_status_drift.py
python3 tools/ci/status_drift.py
```

Im Pull Request laeuft zusaetzlich der Online-Abgleich explizit als offen gefuehrter Issues gegen die GitHub API. Er ist in den bereits verpflichtenden `Reuse Review`-Statuscheck integriert:

```bash
python3 tools/ci/status_drift.py --online
```

Der Online-Check verwendet ausschließlich `contents: read` und `issues: read`. Er schreibt keine GitHub-Daten und benoetigt keinen externen Bot oder Provider.

## Pflegeverantwortung

Der PR, der einen Gate-, Milestone- oder Slice-Status veraendert, aktualisiert die betroffenen Living-Status-Dateien im selben Arbeitszusammenhang oder dokumentiert nachvollziehbar, warum dort keine Aenderung erforderlich ist.

Historische Reviews bleiben davon unberuehrt. Eine neue Gate-Entscheidung wird als neuer datierter Review angelegt.
