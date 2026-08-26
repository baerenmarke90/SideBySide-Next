# SideBySide Next - Arbeitsregeln fuer Implementierungen

Diese Regeln gelten fuer AI-gestuetzte und menschliche Implementierungsarbeit in diesem Repository.

## Verbindliche Quellen

Vor relevanter Arbeit sind mindestens diese Dokumente zu beachten:

1. `specification/CLEAN-ROOM-MASTER-SPEC.md`
2. `docs/REUSE-BEFORE-BUILD.md`
3. `docs/CROSS-CUTTING-QUALITY.md`
4. `docs/EXTERNAL-PROVIDER-CANDIDATES.md`, wenn Provider, Infrastruktur oder Plattformbausteine betroffen sind
5. `docs/ROADMAP.md` und die jeweilige Milestone-/Project-Control-Dokumentation

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

## Cross-Cutting Quality

Querschnittsanforderungen sind Architektur- und Produktanforderungen und duerfen nicht pauschal auf spaetere Milestones verschoben werden.

Vor Implementierungsbeginn und vor Merge ist die Checkliste aus `docs/CROSS-CUTTING-QUALITY.md` anzuwenden. Relevanz ist mindestens fuer diese Bereiche bewusst zu entscheiden:

- Security
- Privacy und Datenlebenszyklus
- Internationalisierung und Locale
- Accessibility
- Concurrency und Konsistenz
- Resilienz, Offline und Retry
- Observability
- Performance und Ressourcen
- API-/Vertrags- und Migrationsfolgen
- Betrieb, Self-Hosted und Release
- Testing

Nicht jeder Punkt ist fuer jeden PR relevant. `nicht relevant` ist zulaessig, muss aber nachvollziehbar sein. Ein PR ist nicht merge-ready, wenn eine erkennbare Querschnittsfolge unbehandelt bleibt oder nur auf spaeter verschoben wird, obwohl dadurch bereits jetzt ein inkompatibler Vertrag oder schwer rueckbaubare Architektur entsteht.

Insbesondere gilt fuer Clientcode: nutzerseitige Texte, Datums-/Zahlenformatierung und Pluralisierung werden von Beginn an ueber die jeweilige Lokalisierungsschicht gefuehrt; Accessibility wird nicht erst bei finaler UI-Abnahme nachgeruestet.

## Nutzerregel

Normale Paare sollen keine technische Infrastruktur konfigurieren muessen. API-Keys, technische URLs, Providerwahl, Tokens und Serverdetails gehoeren in Backend oder Hoster-/Admin-Ebene.

## Keine Aufweichung bestehender Gates

Reuse oder Querschnittsentscheidungen duerfen niemals dazu fuehren, Clean-Room-, Security-, Privacy-, Tenant-Isolation-, Provenance- oder Lizenzregeln abzuschwaechen.

## Pull Requests

Ein relevanter PR ohne nachvollziehbare Reuse-Pruefung ist nicht merge-ready. Rein fachliche Aenderungen koennen die Pruefung begruendet als `nicht relevant` markieren.

Groessere Runtime-Slices, Clientfunktionen und produktive Nutzerflows dokumentieren zusaetzlich ihre relevanten Cross-Cutting-Folgen im PR. Die PR-Vorlage ist dafuer der Mindeststandard; tiefergehende Entscheidungen gehoeren in das zustaendige Issue, Decision-Dokument oder ADR.
