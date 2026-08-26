## Zusammenfassung

<!-- Was aendert dieser PR und warum? -->

## Scope

<!-- Was gehoert bewusst in diesen PR, was nicht? -->

## Reuse-before-build

Mindestens eine der folgenden Optionen muss angekreuzt werden. Details: `docs/REUSE-BEFORE-BUILD.md`.

- [ ] Reuse review relevant
- [ ] Reuse review not relevant

### Falls relevant

**Gepruefte Alternativen**

<!-- Konkrete Standards, Plattform-/Framework-Funktionen, Open-Source-Komponenten und/oder Provider nennen. Eine pauschale Aussage wie "nichts gefunden" reicht nicht. -->

- 

**Entscheidung und Begruendung**

<!-- Warum wurde diese Loesung gewaehlt? Falls Eigenbau: warum ist er trotz vorhandener Alternativen sinnvoll/notwendig? -->

- 

**Drittkomponenten/Provider**

<!-- Falls keine Drittkomponente betroffen ist: "nicht zutreffend". Sonst mindestens Lizenz/ToS, Cloud/Self-Hosted, Privacy/Datenfluss, Kosten/Rate-Limits, Fallback und Nutzer-/Hoster-Aufwand dokumentieren oder auf ein Issue/Dokument verweisen. -->

- 

### Falls nicht relevant

**Begruendung**

<!-- Zum Beispiel: reine Domainlogik ohne neue Commodity-Infrastruktur, Provider, Plattformintegration oder wesentliche Dependency. -->

- 

## Cross-Cutting Quality

Details und Beispiele: `docs/CROSS-CUTTING-QUALITY.md`.

Bei groesseren Runtime-Slices, Clientfunktionen und produktiven Nutzerflows relevante Folgen kurz dokumentieren. Nicht relevante Punkte duerfen zusammengefasst werden.

- [ ] Security / Auth / Abuse / sichere Defaults geprueft oder nicht relevant
- [ ] Privacy / Datenlebenszyklus / Logs / Caches / Events geprueft oder nicht relevant
- [ ] i18n / Locale / Datum / Zahlen / Pluralisierung / RTL geprueft oder nicht relevant
- [ ] Accessibility / Semantik / Fokus / Skalierung geprueft oder nicht relevant
- [ ] Concurrency / Idempotenz / 409 / Races geprueft oder nicht relevant
- [ ] Resilienz / Offline / Retry / partielle Fehler geprueft oder nicht relevant
- [ ] Observability ohne sensible Inhalte geprueft oder nicht relevant
- [ ] Performance / Query- und Ressourcenfolgen geprueft oder nicht relevant
- [ ] OpenAPI / DTO / Migration / Kompatibilitaet geprueft oder nicht relevant
- [ ] Self-Hosted / Konfiguration / Upgrade / Backup / Release geprueft oder nicht relevant
- [ ] passende Testebenen und Negativfaelle geprueft

**Ergebnis / Begruendung**

<!-- Relevante Punkte konkret nennen. Beispiel: "i18n relevant: neue UI-Texte ueber Translation Keys; Accessibility: Semantics-Test ergaenzt; Betrieb: nicht betroffen." -->

- 

## Validierung

<!-- Tests, Lint, Typecheck, manuelle Checks etc. -->

- [ ] relevante Tests ausgefuehrt
- [ ] CI muss vor Merge gruen sein
- [ ] keine Clean-Room-, Security-, Privacy- oder Tenant-Isolation-Regel abgeschwaecht
- [ ] keine erkennbare Querschnittsfolge unbegruendet auf spaeter verschoben

## Hinweise / Risiken

<!-- Optional -->
