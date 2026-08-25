# Externe Provider-Kandidaten

## Zweck

Diese Datei dokumentiert mögliche externe Anbieter und technische Bausteine für zukünftige SideBySide-Next-Integrationen.

**Wichtig:** Ein Eintrag in dieser Liste ist keine Freigabe zur Implementierung.

Vor jedem produktiven Einsatz müssen erneut geprüft werden:

- aktuelle Nutzungsbedingungen
- kommerzielle Nutzbarkeit für SideBySide Cloud
- Self-Hosted-Nutzung
- Lizenz und Attribution
- Speicherung, Caching und Löschpflichten
- Datenschutzanforderungen
- technische Abhängigkeiten und SDK-Lizenzen

Die Prüfung wird Bestandteil des jeweiligen Feature-PRs.

## Architekturregel

Externe Anbieter werden ausschließlich über klare Adapter- oder Integrationsgrenzen angebunden.
Der SideBySide-Core kennt keinen konkreten Anbieter.

Ein Wechsel eines Providers darf keine Änderung an Domain-Modellen oder Fachlogik erzwingen.

## Produktregel: Technik bleibt unsichtbar

SideBySide richtet sich ausdrücklich auch an Menschen ohne technische Kenntnisse.

Normale Nutzer sollen niemals:

- API-Keys beschaffen
- technische URLs eintragen
- Provider auswählen
- Tokens verwalten
- Serverkonfiguration verstehen

Das Backend bzw. die Betriebsplattform übernimmt möglichst die komplette technische Abwicklung.

## Einordnung der Bausteine

Nicht alle Kandidaten sind externe Datenprovider. Sie werden getrennt betrachtet:

- **Externe Provider:** liefern Daten oder Dienste (z. B. Karten, Wetter, Fotos).
- **Infrastrukturbausteine:** reduzieren eigene Backend-Entwicklung (z. B. Upload, Suche, Storage, Monitoring).
- **Client-/Plattformbausteine:** nutzen bestehende Betriebssystem- oder Framework-Funktionen.

---

# Aktuell interessante externe Provider

| Bereich | Kandidat | Möglicher Adapter | Erste Einschätzung |
| --- | --- | --- | --- |
| Karten / Orte / Routing | Geoapify | MapProvider, GeocodingProvider, PlacesProvider | Kandidat für frühe Prüfung |
| Fotos Self-Hosted | Immich API | ExternalMediaProvider | sehr passend für Self-Hosted |
| Wetter | Open-Meteo | WeatherProvider | einfacher Kontext-Provider |
| Fotos extern | Google Photos Picker API | ExternalMediaProvider | explizite Nutzerfreigabe erforderlich |
| Kalender | CalDAV / iCalendar | CalendarProvider | offener Standard, geringe Abhängigkeit |
| Feiertage / Ferien | OpenHolidays | HolidayProvider | geringer Datenschutzaufwand |
| Produktdaten | Open Food Facts | ProductLookupProvider | ODbL-Prüfung erforderlich |
| Wissensdaten | Wikidata | EntertainmentProvider / DiscoveryProvider | Rate Limits beachten |
| Standort-History | Traccar | LocationHistoryProvider | nur Opt-in und M8-Kontext |

---

# Infrastrukturbausteine

| Bereich | Kandidat | Nutzen |
| --- | --- | --- |
| API-Clients | OpenAPI Generator | Web- und Android-Clients aus Vertrag erzeugen |
| Uploads | tus | robuste wiederaufnehmbare Foto-/Video-Uploads |
| Web Upload UX | Uppy | Upload-Oberfläche, Fortschritt, Fehlerbehandlung |
| Bilder | imgproxy | Thumbnails, Größen und Formate ohne eigene Pipeline |
| Videos | FFmpeg | Metadaten, Posterframes, Verarbeitung |
| Suche | PostgreSQL FTS + pg_trgm + unaccent | Suche ohne zusätzlichen Suchserver |
| Backup | restic + rclone | verschlüsselte Backups und Storage-Anbindung |
| Storage | S3-kompatible Systeme | austauschbarer MediaStore |
| Monitoring | OpenTelemetry | standardisierte Telemetrie |
| Hoster-Benachrichtigungen | Apprise | optionale Infrastrukturalarme |

---

# Client- und Plattformbausteine

| Bereich | Kandidat | Nutzen |
| --- | --- | --- |
| Android Medienauswahl | Android Photo Picker | keine eigene Galerie/Berechtigungslogik |
| Android Teilen | Android Sharesheet | Inhalte direkt aus anderen Apps übernehmen |
| Android Hintergrundjobs | WorkManager | zuverlässige Uploads und Synchronisation |
| Android lokaler Cache | Room + Paging | performante Story-Ansichten |
| Android Bilder | Coil | Bildcache und Rendering |
| Android Video | Media3 / ExoPlayer | stabiler Videoplayer |
| Web API State | TanStack Query | Cache, Retry und Server-State |
| QR/Barcode | ZXing | Einladungen und Produktflows |
| Datum/Lokalisierung | dateparser + Babel | natürliche Eingaben und Lokalisierung |

---

# Betriebsmodell

Jeder Baustein muss getrennt betrachtet werden für:

## SideBySide Cloud

- SideBySide betreibt die Infrastruktur.
- API-Zugang und Kosten liegen beim Betreiber.
- Nutzer benötigen keine technischen Providerkonten.
- Datenschutz und Einwilligungen werden durch SideBySide gesteuert.

## Self-Hosted

- Betreiber einer eigenen Instanz kann eigene Provider und Infrastruktur verwenden.
- Konfiguration erfolgt durch den Hoster, nicht durch normale Nutzer.
- Bring-your-own-key ist möglich, wenn technisch und rechtlich sinnvoll.

---

# Pflichtdokumentation vor Umsetzung

Jeder neue Provider oder technische Baustein benötigt:

1. dokumentierte Lizenz-/ToS-Prüfung
2. Entscheidung Cloud vs. Self-Hosted
3. Datenflussbeschreibung
4. Datenschutzbewertung
5. Kostenmodell
6. Abhängigkeiten und Runtime-Lizenzen
7. Beschreibung der Nutzererfahrung ohne technische Begriffe
8. Fallback-Verhalten ohne den Baustein

Diese Liste ist eine Architektur- und Prüfgrundlage, keine automatische Freigabe zur Implementierung.
