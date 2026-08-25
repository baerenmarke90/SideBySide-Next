# SideBySide Next - Arbeitsregeln fuer Implementierungen

Diese Regeln gelten fuer AI-gestuetzte und menschliche Implementierungsarbeit in diesem Repository.

## Verbindliche Quellen

Vor relevanter Arbeit sind mindestens diese Dokumente zu beachten:

1. `specification/CLEAN-ROOM-MASTER-SPEC.md`
2. `docs/REUSE-BEFORE-BUILD.md`
3. `docs/EXTERNAL-PROVIDER-CANDIDATES.md`, wenn Provider, Infrastruktur oder Plattformbausteine betroffen sind
4. `docs/ROADMAP.md` und die jeweilige Milestone-/Project-Control-Dokumentation

## Reuse before build

Vor Eigenimplementierung technischer Commodity-Funktionalitaet muss eine aktuelle Reuse-Pruefung erfolgen.

Pruefe insbesondere:

- offene Standards/Protokolle
- OS-/Plattformfunktionen
- Framework-/Runtime-Funktionen
- etablierte Open-Source-Komponenten
- externe Provider/APIs

Die konkrete Checkliste und Entscheidungsregeln stehen in `docs/REUSE-BEFORE-BUILD.md`.

### Pflicht vor Implementierungsbeginn

Wenn die Aenderung relevant ist, muss im Issue oder PR dokumentiert sein:

- welche Alternativen geprueft wurden
- welche Loesung gewaehlt wurde
- warum sie passt
- warum gegebenenfalls Eigenbau notwendig ist
- bei Drittkomponenten: Lizenz/ToS, Cloud/Self-Hosted, Privacy, Kosten, Fallback und Nutzeraufwand

`docs/EXTERNAL-PROVIDER-CANDIDATES.md` ist eine Startliste, ersetzt aber keine aktuelle Suche nach besseren oder neueren Optionen.

## Nutzerregel

Normale Paare sollen keine technische Infrastruktur konfigurieren muessen. API-Keys, technische URLs, Providerwahl, Tokens und Serverdetails gehoeren in Backend oder Hoster-/Admin-Ebene.

## Keine Aufweichung bestehender Gates

Reuse darf niemals dazu fuehren, Clean-Room-, Security-, Privacy-, Tenant-Isolation-, Provenance- oder Lizenzregeln abzuschwaechen.

## Pull Requests

Ein relevanter PR ohne nachvollziehbare Reuse-Pruefung ist nicht merge-ready. Rein fachliche Aenderungen koennen die Pruefung begruendet als `nicht relevant` markieren.
