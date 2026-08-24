# M2 Screen State Matrix

**Zweck:** verbindliche UI-Zustände vor Implementierungsbeginn  
**Stand:** 24.08.2026

## 1. Globale Zustandsreihenfolge

Jede datenbasierte M2-Ansicht bewertet mindestens:

```text
initial → loading → content
                 ├→ empty:first-use
                 ├→ empty:filter
                 ├→ partial
                 ├→ offline:cached
                 └→ error {validation | 401 | 404 | 409 | 429 | 5xx}
```

Privacy-Filter läuft vor jedem sichtbaren Zustand. Ein leerer Screen darf deshalb nicht verraten, dass private oder fremde Treffer existieren.

## 2. Gemeinsame Texte und Aktionen

| Zustand | Primärtext | Primäre Aktion | Erhaltener Kontext |
|---|---|---|---|
| loading | kein technischer Text nötig; strukturelles Skeleton | keine | Route, Filter, Auswahl |
| empty:first-use | „Eure Story beginnt hier“ | „Erinnerung hinzufügen“ | Navigation |
| empty:filter | „Keine passenden gemeinsamen Momente“ | „Filter zurücksetzen“ | Suchfeld nur lokal, nie Telemetrie |
| partial | „Einige Inhalte konnten nicht geladen werden.“ | „Erneut versuchen“ | bereits sichere Inhalte |
| offline:cached | „Offline · Stand von {Zeit}“ | „Erneut verbinden“ optional | Cache + Scrollposition |
| offline:write | „Noch nicht gespeichert.“ | „Erneut versuchen“ nach Verbindung | kompletter sicherer Entwurf |
| validation | konkrete Feld-/Dateimeldung | „Fehler korrigieren“ implizit | alle Eingaben |
| 401 | „Deine Sitzung ist abgelaufen.“ | „Erneut anmelden“ | nur erlaubtes Rückkehrziel |
| 404 | „Dieser Inhalt ist nicht verfügbar.“ | „Zur Story“ | keine Existenz-/Privacy-Details |
| 409 | „Dieser Inhalt wurde inzwischen geändert.“ | „Aktuellen Stand ansehen“ | eigene Eingabe separat |
| 429 | „Das waren viele Versuche.“ | zeitgesteuerter Retry | Eingabe ohne Auto-Spam |
| 5xx | „Das hat gerade nicht geklappt.“ | „Erneut versuchen“ | sichere Ansicht/Entwurf |

## 3. Matrix pro Screen

| Screen | Loading | Empty | Partial/Offline | kritische Fehler | Erfolg |
|---|---|---|---|---|---|
| Story Timeline | Monats-Skeleton, keine alten Fremddaten | Erstnutzung oder Filter getrennt | sichere Karten + Statusleiste | 401, privacy-safe 404, 5xx | stabile Timeline, Fokus auf Überschrift |
| Story Search | Feld sofort bedienbar, Ergebnisse Skeleton | keine Treffer ohne private Counts | letzter autorisierter Ergebnisstand klar markiert | ungültiger Cursor neutral, 429 | Filterzahl und Ergebnisse konsistent |
| Memory Detail | Struktur für Text/Medien/Kommentare | nicht anwendbar | Text darf laden, Medien einzeln fehlschlagen | 404, 409 bei Edit | Autor/Datum/Medien korrekt |
| Memory Form | vorhandener Editstand Skeleton | neuer Entwurf | Offline-Entwurf ohne Erfolgssignal | Feldfehler, 409, Uploadfehler | Detail öffnet; Story aktualisiert |
| Media Queue | je Datei eigener Status | „Foto hinzufügen“ bleibt optional | einzelne Fehler blockieren nicht alles | Typ/Größe/Dimension/Timeout | `ready` mit Reihenfolge |
| HeartMoment Form | keine Default-Privacy vortäuschen | Sichtbarkeit bleibt Pflichtfeld | Offline speichern blockiert | Privacy-Wechsel 409/Offline | Owner- oder Shared-Ziel korrekt |
| Private Moments | owner-gebundener Skeleton | ruhiger persönlicher Empty State | Cache eindeutig persönlich und offline | Partner sieht neutral 404 | nur Owner-Inhalt |
| Milestone Form/Detail | Standard-Form-/Detail-Skeleton | neuer Entwurf | Text bleibt bei Netzfehler | Validation, 409, 404 | eigener Story-Typ |
| Comments | Kommentar-Skeleton nach Parent | „Noch keine Kommentare“ nur auf erlaubtem Target | bestehende Kommentare bleiben, Retry separat | Target 404/private, Sendefehler | neuer Kommentar genau einmal |

## 4. Story Timeline im Detail

### Initial und Loading

- App Shell und Seitentitel erscheinen sofort.
- Skeleton entspricht Karte und Monatsgruppe, enthält aber keine zufälligen Namen, Bilder oder Datumswerte.
- Bereits sichtbarer sicherer Cache wird nicht durch leeres Skeleton ersetzt; er erhält einen Refresh-Zustand.
- Screenreader erhält einmal „Story wird geladen“, nicht pro Skeleton-Karte.

### Empty: Erstnutzung

```text
Eure Story beginnt hier
Haltet einen gemeinsamen Moment fest, wenn es für euch passt.
[Erinnerung hinzufügen]
```

Keine künstliche Dringlichkeit, keine Partnerbeschuldigung und keine private Alternative in der gemeinsamen Story.

### Empty: Suche/Filter

- Aktive Filter bleiben sichtbar.
- Suchtext wird nicht in Analytics oder Fehlerberichte übernommen.
- Kein Text wie „3 private Treffer ausgeblendet“.
- Zurücksetzen bewahrt den Story-Kontext und setzt Cursor/Scroll korrekt zurück.

### Partial

- Fehlerhafte Medien zeigen Platzhalter pro Karte.
- Fehler einer Cursor-Seite entfernt bereits geladene Karten nicht.
- Retry lädt nur den betroffenen Abschnitt und erzeugt keine Duplikate.

## 5. Formulare

### Pflichtstruktur

1. eindeutiger Seitentitel,
2. fachliche Felder,
3. Privacy-Status beziehungsweise Pflichtauswahl,
4. optionale Medien,
5. eine primäre Speichern-Aktion,
6. sekundäres Abbrechen mit Entwurfswarnung nur bei Änderungen.

### Validierung

- Fehler steht direkt am Feld und in einer fokussierbaren Zusammenfassung bei mehreren Fehlern.
- Der erste fehlerhafte Bereich erhält Fokus nach Absenden.
- Wert, Auswahl, Medienreihenfolge und lokaler Entwurf bleiben erhalten.
- Keine Fehlermeldung nennt interne Feld-, Tabellen- oder Storage-Namen.

### Saving

- Aktion wird gegen Doppelabsenden geschützt.
- Status „Wird gespeichert …“ wird höflich angekündigt; Fokus bleibt stabil.
- Timeout ist kein Erfolg. Die UI klärt über Idempotenz/Statusabfrage, bevor erneut erzeugt wird.
- Verlassen während laufendem Upload folgt der Media-Entscheidung; kein stilles Hintergrundversprechen.

## 6. Medienzustände

| Fehlerklasse | Nutzertext | nächste Aktion | Telemetrie |
|---|---|---|---|
| Typ nicht erlaubt | „Dieses Dateiformat wird nicht unterstützt.“ | andere Datei wählen | `unsupported_type` |
| zu groß | „Diese Datei ist zu groß.“ | andere Datei wählen | `size_limit` |
| Dimension/Verarbeitung | „Dieses Bild konnte nicht verarbeitet werden.“ | Retry oder entfernen | `processing_failed` |
| Netzwerk | „Upload unterbrochen.“ | Retry | `network` |
| Autorisierung | neutraler Parent-/Session-Zustand | anmelden/zurück | keine Dateiinfos |
| Storage/Server | „Upload gerade nicht möglich.“ | später erneut | `service_unavailable` |

Dateiname, MIME-Details, Pixelwerte und Read URLs gehören nicht in Standardtelemetrie. Technische Details dürfen nur in bereinigter Diagnose erscheinen.

## 7. HeartMoment Privacy-Zustände

| Zustand | sichtbare Elemente | verbotene Elemente |
|---|---|---|
| Auswahl offen | beide Optionen gleich verständlich | vorausgewählte Privacy ohne Produktentscheidung |
| PRIVATE gespeichert | „Nur für mich“, Owner-Kontext | Kommentar, Partneraktivität, Story-Link |
| SHARED gespeichert | „Mit Partner geteilt“, Story-/Kommentarzugang | missverständliches Schloss ohne Text |
| PRIVATE → SHARED | Bestätigung der neuen Sichtbarkeit | stilles Umschalten |
| SHARED → PRIVATE | Hinweis auf zukünftige Unsichtbarkeit und Grenze des Zurücknehmens | Versprechen, bereits Gelesenes zu löschen |
| Partner-Deep-Link auf PRIVATE | neutraler 404-Zustand | „privat“, Autorname, Datum, Attachment |

## 8. Accessibility-Abnahme pro Zustand

- Name, Rolle, Wert und Status sind programmatisch erkennbar.
- Statusänderungen werden einmalig und höflich angekündigt.
- Fokus bleibt bei Loading/Refresh stabil und springt nicht an Seitenanfang.
- Fehlerzusammenfassung und Feldfehler sind miteinander verknüpft.
- Privacy-Auswahl ist als Gruppe mit zwei vollständigen Labels bedienbar.
- Medienkacheln haben Dateityp, Status und Aktion im zugänglichen Namen.
- Reihenfolgeänderung ist ohne Drag möglich.
- 200 % Web-Zoom und größte unterstützte Android-Schrift schneiden keine Pflichttexte ab.
- Farbe wird immer durch Text, Icon oder Form ergänzt.
- reduzierte Bewegung verliert keine Statusinformation.

## 9. Visuelle Testdatensätze

Jeder Screen wird mit folgenden Datenmengen geprüft:

- 0, 1, 2 und 20 Story Items,
- sehr kurzer und sehr langer Titel/Text,
- Datum mit langer deutscher Monatsbezeichnung,
- 0, 1 und mehrere Medien, gemischte Zustände,
- lange Anzeigenamen und fehlender Avatar,
- kein Kommentar, ein Kommentar, längere Liste,
- PRIVATE Canary, die in keiner Shared-Ansicht erscheinen darf.
