# Reuse Before Build - verbindliche Entwicklungsregel

## Status

Dieses Dokument ist ein verbindlicher Governance-Nachtrag fuer SideBySide Next.

Die historische Clean-Room-Master-Spezifikation bleibt als Ausgangsspezifikation unveraendert. Fuer neue technische Entscheidungen gilt zusaetzlich diese Regel.

## Grundsatz

Bevor neue Infrastruktur, Integrationslogik oder technische Commodity-Funktionalitaet selbst implementiert wird, muss geprueft werden, ob eine geeignete bestehende Loesung existiert.

Zu pruefen sind in dieser Reihenfolge:

1. offener Standard oder Protokoll
2. Betriebssystem- oder Plattformfunktion
3. etablierte Framework-/Runtime-Funktion
4. permissiv lizenzierte Open-Source-Komponente
5. externer Provider oder API-Dienst
6. erst danach Eigenimplementierung

Eigenbau ist zulaessig, aber er muss begruendet werden, wenn eine plausible bestehende Loesung existiert.

## Wann die Pruefung Pflicht ist

Die Pruefung ist Pflicht fuer relevante Features oder Aenderungen, die mindestens einen der folgenden Bereiche betreffen:

- externe Provider oder APIs
- Uploads, Medienverarbeitung oder Wiedergabe
- Suche, Indexierung oder Caching
- Push, Notifications oder Background Jobs
- Kalender, Karten, Geocoding, Routing oder Wetter
- Storage, Backup, Restore oder Export-Infrastruktur
- Observability, Monitoring oder Hoster-Benachrichtigungen
- Web-/Android-API-Clients
- Android-/Web-Plattformfunktionen
- Auth-/OIDC-/Passkey-nahe Infrastruktur
- neue technische Services oder Daemons
- neue umfangreiche Abhaengigkeiten

Fuer rein fachliche Domainlogik ohne Commodity-Infrastruktur kann die Pruefung als nicht relevant markiert werden.

## Pflichtfragen vor Implementierungsbeginn

Bei einem relevanten Feature muessen Issue oder Pull Request nachvollziehbar beantworten:

- Gibt es einen offenen Standard fuer das Problem?
- Gibt es eine geeignete OS-/Plattform-/Framework-Funktion?
- Gibt es eine etablierte Open-Source-Komponente?
- Gibt es einen geeigneten externen Provider?
- Welche Kandidaten wurden konkret geprueft?
- Warum wird die gewaehlte Loesung bevorzugt?
- Warum ist Eigenbau erforderlich, falls selbst implementiert wird?

Bei Drittkomponenten oder Providern zusaetzlich:

- Lizenz und Nutzungsbedingungen
- kommerzielle Nutzbarkeit fuer SideBySide Cloud
- Self-Hosted-Nutzbarkeit
- Datenfluss und Datenschutz
- Speicherung, Caching, Loeschpflichten und Attribution
- Kostenmodell und Rate Limits
- Runtime-/SDK-Abhaengigkeiten
- Fallback ohne die Komponente
- Nutzeraufwand und Hoster-Aufwand

## Produktregel

Normale SideBySide-Nutzer sollen technische Integrationsdetails nicht konfigurieren muessen.

Ziel:

- keine API-Keys fuer normale Nutzer
- keine technischen Server-URLs fuer normale Nutzer
- keine Providerwahl ohne echten Produktnutzen
- keine Tokenverwaltung durch normale Nutzer
- moeglichst keine zusaetzlichen Providerkonten
- wenn Consent/OAuth erforderlich ist: ein kurzer, verstaendlicher Verbinden-Flow

Das Backend bzw. die Betriebsplattform uebernimmt die technische Abwicklung soweit wie moeglich.

## Entscheidungsregel

Eine bestehende Komponente wird nicht allein deshalb eingebaut, weil sie existiert. Sie muss gegen Eigenbau bewertet werden nach:

- fachlicher Passung
- Wartbarkeit
- Security
- Privacy
- Lizenz/ToS
- Vendor Lock-in
- Betriebsaufwand
- Kosten
- Reife und Wartungszustand
- Cloud-/Self-Hosted-Kompatibilitaet
- Nutzererlebnis

Die bevorzugte Reihenfolge ist: Standards und vorhandene Plattformfaehigkeiten zuerst, austauschbare Komponenten zweitens, proprietaere Provider nur hinter klaren Adaptern.

## Bekannte Kandidaten

Die aktuelle Kandidatenliste steht in `docs/EXTERNAL-PROVIDER-CANDIDATES.md`.

Diese Liste ist nicht abschliessend. Vor Beginn eines relevanten Features muss auch nach neuen oder inzwischen besseren Loesungen gesucht werden. Eine alte Kandidatenliste ersetzt keine aktuelle Pruefung.

## Pull-Request-Gate

Ein relevanter Pull Request ist nicht merge-ready, wenn die Reuse-Pruefung fehlt oder nur pauschal beantwortet wurde.

Akzeptabel sind:

- dokumentierte Auswahl eines bestehenden Bausteins
- dokumentierte Entscheidung fuer Eigenbau mit Begruendung
- nachvollziehbare Kennzeichnung `nicht relevant` bei rein fachlicher Aenderung

Die Pruefung wird im Pull-Request-Template abgefragt.

## Beziehung zu anderen Projektregeln

Diese Governance-Regel ergaenzt insbesondere:

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `docs/EXTERNAL-PROVIDER-CANDIDATES.md`
- `docs/ROADMAP.md`
- `CONTRIBUTING.md`

Clean-Room-, Security-, Privacy- und Tenant-Isolation-Regeln haben weiterhin Vorrang. Eine externe Komponente darf keine dieser Grenzen abschwaechen.
