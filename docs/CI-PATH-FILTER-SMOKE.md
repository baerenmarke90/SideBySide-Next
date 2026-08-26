# CI Path Filter Smoke

Diese Datei existiert ausschließlich auf dem temporären Validierungsbranch für Issue #123.

Der dazugehörige Draft-PR enthält bewusst nur diese Dokumentationsänderung gegenüber `ci/docs-pr-path-filter-123`. Damit lässt sich nachweisen, dass teure Runtime-Gates bei einem echten Doku-only-PR nicht gestartet werden, während die dauerhaft erforderlichen Governance-/Security-Checks weiterlaufen.

Der aktuelle Smoke-Lauf basiert auf dem mit #150 kombinierten Stand und muss deshalb auch `Backend Integration` als übersprungenes teures Gate zeigen.

Die Datei ist nicht zur Übernahme in `main` vorgesehen.
