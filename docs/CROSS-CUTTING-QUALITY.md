# Cross-Cutting Quality Review

## Zweck

SideBySide Next behandelt Querschnittsanforderungen als Architektur- und Produktanforderungen, nicht als spaete Release-Nacharbeit.

Jeder neue Runtime-Slice, jede groessere Clientfunktion und jede Aenderung an einem produktiven Nutzerflow muss vor der Implementierung und vor dem Merge gegen die unten stehenden Bereiche geprueft werden. Nicht jeder Bereich ist fuer jede Aenderung relevant; `nicht relevant` ist zulaessig, muss aber bewusst entschieden und kurz begruendet werden.

Die Pruefung ersetzt keine bestehenden Security-, Privacy-, Reuse-, Clean-Room- oder Milestone-Gates. Sie ergaenzt sie.

## Verbindliche Pruefbereiche

### Security

Pruefen:

- neue Angriffsoberflaeche, Authentifizierung oder Autorisierung;
- Tenant-Isolation und indirekte Existenzauskuenfte;
- Abuse, Rate Limits, Replay, Idempotenz und Race Conditions;
- Eingabevalidierung, externe Inhalte, Datei- oder Netzwerkparser;
- sichere Defaults und Fail-Closed-Verhalten.

### Privacy und Datenlebenszyklus

Pruefen:

- Datenklassifizierung und Sichtbarkeit;
- Logs, Events, Analytics, Crashreports und Supportdaten;
- Retention, Delete, Export und Backup;
- Caches, Read Models, Benachrichtigungen und indirekte Beziehungen;
- Provider-/Drittanbieter-Datenfluss.

### Internationalisierung und Locale

Pruefen:

- alle nutzerseitigen Texte ueber die jeweilige Lokalisierungsschicht;
- Datum, Uhrzeit, Zahlen und Waehrung ueber aktive Locale statt fest verdrahteter Locale;
- Pluralisierung ueber locale-faehige Regeln;
- keine lokalisierten Backend-Klartexte als Clientvertrag, wenn stabile Fehlercodes moeglich sind;
- Layouts mit laengeren Texten sowie RTL-Auswirkungen, soweit der betroffene Screen dies erfordert;
- nutzergenerierte Inhalte werden nicht automatisch uebersetzt.

### Accessibility

Pruefen:

- Semantik, Name/Rolle/Wert und Screenreader-/TalkBack-Verhalten;
- Tastatur, Fokus, System Back und alternative Eingabemethoden;
- Textskalierung, Kontrast und reduzierte Bewegung;
- Fehler-, Loading-, Empty- und Conflict-Zustaende;
- relevante Anforderungen aus `docs/ACCESSIBILITY-QA-MATRIX.md`.

### Concurrency und Konsistenz

Pruefen:

- konkurrierende Writes und Lost Updates;
- `If-Match`/409, Lock-Reihenfolge und Datenbankconstraints;
- idempotente Wiederholung und Rollback-Sicherheit;
- Delete-/Transition-Races und gleiche Semantik unter Parallelitaet.

### Resilienz, Offline und Retry

Pruefen:

- Netzwerkfehler und Timeouts;
- sichere Wiederholung ohne Doppelwirkung;
- Verhalten bei partiellen Fehlern;
- Offline-Anzeige versus Offline-Write;
- keine Sync-Zusage, solange kein echter Sync existiert.

### Observability

Pruefen:

- welche Logs/Metriken/Traces fuer Betrieb und Fehlersuche erforderlich sind;
- Correlation/Request IDs bei neuen verteilten oder asynchronen Pfaden;
- niemals sensible Inhalte, Tokens, Presigned URLs oder OWNER_ONLY-Payloads in Observability;
- Fehler muessen diagnostizierbar sein, ohne Privacy-Grenzen abzuschwaechen.

### Performance und Ressourcen

Pruefen:

- Query-Anzahl, Pagination und Indexbedarf;
- Payload-, Medien-, Speicher- und CPU-Groessen;
- teure Arbeit nicht unnoetig im Requestpfad;
- Client-Recomposition/Rendering, Listen und grosse Datenmengen;
- Ressourcenlimits bei Parsern, Jobs und externen Integrationen.

### Vertrags- und Migrationsfolgen

Pruefen:

- OpenAPI-/DTO-Auswirkungen und Clientkompatibilitaet;
- DB-Migration, Rollforward und vorhandene Daten;
- Versionierung und Abwaertskompatibilitaet;
- generierte Clients und Contract-Tests;
- keine zweite Wahrheitsquelle fuer denselben Domainwert.

### Betrieb, Self-Hosted und Release

Pruefen:

- neue Konfiguration und sichere Defaults;
- Auswirkungen auf Compose, Container, Health/Readiness und Reverse Proxy;
- Upgrade-, Backup- und Restore-Folgen;
- Cloud/Self-Hosted-Paritaet auf Core-Ebene;
- neue Provider-, Secret-, Kosten- oder Supportanforderungen.

### Testing

Pruefen:

- kleinste sinnvolle Unit-/Component-Tests;
- PostgreSQL-/Integrationstests fuer Datenbank- und Concurrency-Regeln;
- Cross-Tenant-/Privacy-Negativtests;
- Contract-, E2E-, Accessibility- oder Buildtests, wenn der Scope sie beruehrt;
- Tests muessen die Regression tatsaechlich nachweisen und duerfen nicht nur den Happy Path wiederholen.

## Anwendung in Issues und Pull Requests

### Vor Implementierungsbeginn

Fuer jeden groesseren Slice oder Nutzerflow werden relevante Querschnittsbereiche bereits im Issue oder in der Slice-Dokumentation festgehalten. Offene Designfragen werden vor Runtime-Code entschieden, wenn sie die API, Persistenz, Privacy oder Clientarchitektur formen.

### Vor Merge

Der PR enthaelt eine `Cross-Cutting Quality`-Sektion. Dort wird mindestens fuer die relevanten Bereiche kurz dokumentiert, was geprueft wurde. Nicht relevante Bereiche duerfen zusammengefasst werden, solange die Entscheidung nachvollziehbar bleibt.

Ein PR ist nicht merge-ready, wenn eine erkennbare Querschnittsfolge unbehandelt bleibt oder nur auf spaeter verschoben wird, obwohl dadurch bereits jetzt ein inkompatibler Vertrag oder schwer rueckbaubare Architektur entsteht.

## Beispiel

Eine neue Datumskarte im Web koennte dokumentieren:

- Security/Privacy: keine neue Datenflaeche;
- i18n: Text ueber Translation Key, Datum ueber aktive Locale;
- Accessibility: semantische Ueberschrift und Tastaturbedienung;
- Performance: nicht relevant;
- API/Migration: nicht relevant;
- Tests: Rendering in Default-Locale und Fallback getestet.

Damit werden Querschnittsthemen frueh sichtbar, ohne jeden kleinen PR mit unnoetiger Prozesslast zu versehen.
