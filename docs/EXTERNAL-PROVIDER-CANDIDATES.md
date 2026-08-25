# Externe Provider-Kandidaten

## Zweck

Diese Datei dokumentiert mögliche externe Anbieter für zukünftige SideBySide-Next-Integrationen.

**Wichtig:** Ein Eintrag in dieser Liste ist keine Freigabe zur Implementierung.

Vor jedem produktiven Adapter müssen erneut geprüft werden:

- aktuelle API-Nutzungsbedingungen
- kommerzielle Nutzbarkeit für SideBySide Cloud
- Self-Hosted-Nutzung
- Datenlizenz und Attribution
- Speicherung, Caching und Löschpflichten
- Datenschutzanforderungen
- technische Abhängigkeiten und SDK-Lizenzen

Die Prüfung wird Bestandteil des jeweiligen Feature-PRs.

## Architekturregel

Externe Anbieter werden ausschließlich über Provider-Adapter angebunden.
Der SideBySide-Core kennt keinen konkreten Anbieter.

Ein Wechsel des Providers darf keine Änderung an Domain-Modellen oder Fachlogik erzwingen.

## Produktregel: Technik bleibt unsichtbar

SideBySide richtet sich ausdrücklich auch an Menschen ohne technische Kenntnisse.
Eine externe Integration darf deshalb nicht voraussetzen, dass normale Nutzer:

- API-Keys beschaffen
- technische URLs eintragen
- Provider auswählen
- Tokens verwalten
- Serverkonfiguration verstehen

Das Backend übernimmt möglichst die komplette technische Abwicklung.

Normale Nutzer sehen ausschließlich den Nutzen:

- "Fotos verbinden"
- "Kalender verbinden"
- "Wetter für eure Pläne anzeigen"
- "Orte in der Nähe finden"

Technische Details bleiben in den Betriebs- und Administrationsbereichen.

## Pflichtdokumentation je Provider

Bevor ein Provider implementiert wird, muss zusätzlich zur Lizenzprüfung dokumentiert werden:

| Bereich | Frage |
| --- | --- |
| Nutzerwert | Was verbessert sich für ein Paar konkret? |
| Nutzeraufwand | Welche Einrichtung muss ein normales Paar durchführen? |
| Ziel | Der Nutzeraufwand soll möglichst bei 0 liegen. |
| Hoster-Aufwand | Welche Einrichtung benötigt ein Betreiber der Cloud oder Self-Hosted-Instanz? |
| Backend-Verantwortung | Welche Schritte übernimmt SideBySide automatisch? |
| Datenschutz | Welche Daten verlassen die SideBySide-Instanz? |
| Fallback | Was funktioniert ohne diesen Provider weiterhin? |
| Kostenmodell | Wer trägt eventuelle API-Kosten? |

## Betriebsmodelle

Jeder Provider muss getrennt betrachtet werden für:

### SideBySide Cloud

- SideBySide betreibt die Infrastruktur.
- API-Zugang und Kosten liegen beim Betreiber.
- Nutzer müssen keine Providerkonten anlegen.
- Datenschutz und Einwilligungen werden durch SideBySide gesteuert.

### Self-Hosted

- Betreiber einer eigenen Instanz kann eigene Provider verwenden.
- Konfiguration erfolgt durch den Hoster, nicht durch normale Nutzer.
- Bring-your-own-key ist möglich, wenn technisch und rechtlich sinnvoll.

## Aktuell interessante Kandidaten

| Bereich | Kandidat | Möglicher Adapter | Erste Einschätzung |
| --- | --- | --- | --- |
| Karten / Orte / Routing | Geoapify | MapProvider, GeocodingProvider, PlacesProvider | Kandidat für frühe Prüfung |
| Fotos Self-Hosted | Immich API | ExternalMediaProvider | sehr passend für Self-Hosted |
| Wetter | Open-Meteo | zukünftiger WeatherProvider | einfacher Kontext-Provider |
| Fotos extern | Google Photos Picker API | ExternalMediaProvider | explizite Nutzerfreigabe erforderlich |

## Bewusst nicht automatisch eingeplant

Folgende Anbieter können später interessant sein, benötigen aber eine gesonderte Prüfung:

- TMDB (Filme/Serien)
- MusicBrainz (Musikdaten)
- Edamam (Rezepte)
- Ticketmaster Discovery API (Events)

Diese Liste darf nicht als technische oder rechtliche Freigabe interpretiert werden.

## Prüfprotokoll für neue Adapter

Jeder neue externe Provider benötigt vor Merge:

1. dokumentierte Lizenz- und ToS-Prüfung
2. Entscheidung Cloud vs. Self-Hosted
3. Datenflussbeschreibung
4. Datenschutzbewertung
5. Attribution/Notice-Prüfung
6. Konfigurationskonzept (z. B. eigener API-Key bei Self-Hosted)
7. Beschreibung der Nutzererfahrung ohne technische Begriffe
