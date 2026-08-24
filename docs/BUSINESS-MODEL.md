# SideBySide Next – Produkt- und Geschäftsmodell

## Ziel

SideBySide Next soll zwei Dinge miteinander verbinden:

1. technisch versierte Privatnutzer können die Anwendung selbst betreiben;
2. Privatnutzer, die keinen eigenen Server administrieren möchten, können den offiziell betriebenen SideBySide-Cloud-Dienst nutzen.

Die Monetarisierung der Cloud basiert auf Betrieb, Komfort und Service – nicht darauf, den Self-Hosted-Build künstlich funktional zu verschlechtern.

## Betriebsmodelle

### SideBySide Self-Hosted

SideBySide Self-Hosted richtet sich an Privatnutzer, die SideBySide Next selbst installieren und betreiben möchten.

Für persönliche und sonstige nichtkommerzielle Nutzung gelten die Bedingungen der [PolyForm Noncommercial License 1.0.0](../LICENSE).

Self-Hosted-Nutzer übernehmen insbesondere selbst:

- Installation und Aktualisierung;
- Server- und Datenbankbetrieb;
- TLS, Domain und Reverse Proxy;
- Backups und Wiederherstellung;
- Monitoring und Verfügbarkeit;
- E-Mail- und Push-Infrastruktur, soweit diese Funktionen eine externe Infrastruktur benötigen;
- Speicher- und Betriebskosten.

Self-Hosted soll den gemeinsamen Application Core verwenden und nicht allein zur Verkaufsförderung der Cloud künstlich um Kernfunktionen beschnitten werden. Unterschiede dürfen sich aus der Betriebsform ergeben, zum Beispiel durch verwaltete Infrastruktur, verfügbare Integrationen, Speicher- oder Serviceleistungen.

### SideBySide Cloud

SideBySide Cloud ist der offiziell betriebene Managed Service für Nutzer, die SideBySide verwenden möchten, ohne selbst Infrastruktur zu administrieren.

Die Nutzer bezahlen dabei insbesondere für den Betrieb und die damit verbundenen Leistungen, zum Beispiel:

- bereitgestellte und gewartete Infrastruktur;
- automatische Updates und Migrationen;
- Backups und Wiederherstellungsprozesse;
- Monitoring und Verfügbarkeit;
- Sicherheitswartung;
- verwalteten Speicher;
- E-Mail-, Push- und vergleichbare Betriebsdienste;
- eine direkt nutzbare Web- und App-Erfahrung ohne eigene Serveradministration.

Die Cloud darf in unterschiedlichen Tarifen angeboten werden, beispielsweise anhand von Speicher, Serviceumfang oder zusätzlichen verwalteten Leistungen. Konkrete Preise und Limits werden erst nach einer Kosten- und Marktbetrachtung verbindlich festgelegt.

## Offizielle Apps und Clients

Offizielle Web-, Android- und gegebenenfalls weitere Clients sind Teil des SideBySide-Produktes.

Der kommerzielle Nutzen der offiziellen Cloud entsteht nicht dadurch, Self-Hosted-Nutzer technisch aus den offiziellen Clients auszuschließen, sondern durch den komfortablen, fertig betriebenen Dienst. Wo es technisch und sicherheitlich sinnvoll ist, sollen die offiziellen Clients daher sowohl mit SideBySide Cloud als auch mit kompatiblen Self-Hosted-Instanzen funktionieren können.

App-Store-Veröffentlichung, Signierung, Updatekanäle, Push-Infrastruktur und andere vom Projektbetreiber bereitgestellte Distributions- oder Plattformdienste können separat an den offiziellen Betrieb gebunden sein, sofern dies technisch, sicherheitlich oder wirtschaftlich erforderlich ist.

## Kommerzielle Nutzung durch Dritte

Die Veröffentlichung des Quellcodes erteilt keine allgemeine Erlaubnis zur kommerziellen Nutzung.

Dritte benötigen eine separate kommerzielle Lizenz insbesondere für:

- einen kostenpflichtigen SideBySide-Hosting- oder SaaS-Dienst;
- die Integration in ein kommerzielles Produkt;
- White-Label- oder OEM-Angebote;
- kommerzielle Weitergabe oder Vermarktung.

Die maßgebliche Projektpolicy steht in [COMMERCIAL-LICENSE.md](../COMMERCIAL-LICENSE.md).

## Beiträge aus der Community

Community-Forks und Pull Requests sind ausdrücklich erwünscht. Änderungen können nach Review in den Hauptzweig übernommen werden, wenn sie fachlich, technisch und strategisch zum Projekt passen.

Die Entscheidung über die Aufnahme eines Beitrags liegt bei den Maintainers. Für Beiträge gelten [CONTRIBUTING.md](../CONTRIBUTING.md) und das [Contributor License Agreement](../CLA.md), damit akzeptierte Contributions sowohl im nichtkommerziellen Modell als auch bei einer späteren kommerziellen Lizenzierung rechtssicher weiterverwendet werden können.

## Produktprinzipien

Das Geschäftsmodell folgt diesen Grundsätzen:

- **Self-Hosting bleibt ein echtes Produkt.** Es dient nicht nur als Demo für die Cloud.
- **Die Cloud verkauft Bequemlichkeit und Betrieb.** Der Mehrwert besteht in einem verwalteten Dienst.
- **Ein gemeinsamer Application Core.** Cloud und Self-Hosted sollen nicht unnötig auseinanderentwickelt werden.
- **Keine künstliche Verschlechterung.** Kernfunktionen werden nicht allein zur Monetarisierung aus Self-Hosted entfernt.
- **Kommerzielle Nutzung bleibt kontrolliert.** Dritte benötigen dafür eine separate Lizenz.
- **Community-Beiträge können zurückfließen.** Die Maintainers entscheiden über die Aufnahme in `main`.
- **Datenschutz bleibt Produktmerkmal.** Monetarisierung soll nicht auf Werbung, Verkauf persönlicher Daten oder unnötigem Tracking beruhen.

## Positionierung

Die spätere Kommunikation kann das Modell sinngemäß so erklären:

> SideBySide Next kannst du für persönliche, nichtkommerzielle Nutzung selbst hosten. Wenn du keinen eigenen Server betreiben, keine Updates einspielen und keine Backups verwalten möchtest, kannst du stattdessen SideBySide Cloud als fertig betriebenen Dienst nutzen.

## Noch nicht festgelegt

Dieses Dokument legt die strategische Produktstruktur fest, aber bewusst noch keine endgültigen Preise, Speichergrenzen, SLA-Zusagen oder Tarifnamen. Diese Punkte werden vor dem kommerziellen Start anhand der tatsächlichen Infrastrukturkosten, Zahlungsgebühren, App-Store-Kosten, Supportaufwände und Marktpositionierung festgelegt.
