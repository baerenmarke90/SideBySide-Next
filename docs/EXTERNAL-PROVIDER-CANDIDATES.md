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
