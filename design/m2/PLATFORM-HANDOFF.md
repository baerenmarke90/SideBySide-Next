# M2 Platform Handoff

**Zweck:** gleicher fachlicher Vertrag, plattformgerechte Umsetzung  
**Stand:** 24.08.2026

## 1. Gemeinsamer Kern

Web und Android teilen:

- Route- und Screenbegriffe,
- Privacy-Klassen und sichtbare Texte,
- Feld- und Fehlersemantik,
- API-DTOs und Concurrency-Regeln,
- Media-Lifecycle und Retry-Kategorien,
- Analytics-Namen und Datenminimierung,
- Story-Sortierung, Filter und Cursorverhalten,
- Abnahmedatensatz und Privacy-Canaries.

Plattformen dürfen Darstellung und Systemintegration anpassen, nicht fachliche Bedeutung oder Berechtigung.

## 2. Fensterklassen

| Klasse | Breite | Navigation | Story | Detail | Create |
|---|---:|---|---|---|---|
| Compact | bis 599 px | Bottom Navigation, max. fünf Ziele | eine Spalte | neue Seite | neue Seite, volle Breite |
| Medium | 600–839 px | Navigation Rail | breitere Liste | neue Seite oder schmale Side Pane nach Platz | zentrierte Form |
| Expanded | ab 840 px | Sidebar | Liste + optionales Detail-Pane | 320–480 px Pane | zentrierte Form, Reading Max 720 px |

Bei großen Webfenstern wächst nicht die Textzeile unbegrenzt. Content Max bleibt 1200 px, Reading Max 720 px.

## 3. Komponenten-Mapping

| Aufgabe | Web | Android | gemeinsamer Contract |
|---|---|---|---|
| Hauptnavigation | Sidebar/Rail/Bottom Nav | Navigation Bar/Rail | `navigation-item` |
| Typ auswählen | Menu oder Dialog | Modal Bottom Sheet | drei beschriebene Optionen |
| Privacy wählen | Radio Group / Selection Cards | Radio/Selection Controls | verpflichtend, kein reines Farbsignal |
| Story-Karte | semantischer Artikel/Link | klickbare Content Card | Typ, Autor, Datum, Vorschau |
| Detail | Side Pane oder Seite | neue Destination | neutraler 404, stabile Zurück-Navigation |
| Medien | Grid/List mit Dateiaktionen | Media Tiles, System Picker | Status, Retry, Remove, Reorder |
| Kommentar | Inline Composer | Inline/Bottom Composer | nur erlaubte Targets |
| Fehler | Inline Message + ggf. Summary | Inline Message/Snackbar | Ergebnis + nächster Schritt |

Bestehende Komponentenverträge bleiben maßgeblich; M2 führt keinen parallelen Komponentenbaukasten ein.

## 4. Web-spezifisch

- Native Links für navigierbare Story-Karten; Öffnen in neuem Tab respektiert Berechtigung erneut.
- Tastatur: Tab/Shift+Tab, Enter/Space, Escape und Pfeiltasten gemäß Komponente.
- Expanded List/Detail bewahrt Auswahl, Filter und Scrollposition.
- Browser-Zurück ist ein Produktpfad, kein Notausgang.
- Service Worker oder Query Cache darf Owner-/Space-Daten nicht über Logout oder Space-Wechsel behalten.
- Signierte Media URLs nicht in dauerhaftem Cache, History State, Analytics oder DOM-Datensätzen persistieren.
- Formulare nutzen passende Autocomplete-Semantik nur für nicht sensible Standardfelder.

## 5. Android-spezifisch

- System Photo Picker bevorzugen; Berechtigung erst aus bewusstem „Foto hinzufügen“-Kontext.
- System-Zurück schließt zuerst Sheet/Overlay, dann Detail, dann Destination.
- TalkBack liest Karte als zusammenhängenden Inhalt mit separaten klaren Aktionen.
- Drag zur Medienreihenfolge hat Move-up/Move-down-Alternative.
- App-Switcher-/Recents-Schutz für private Screens wird als Security-/UX-Entscheidung dokumentiert.
- Private Inhalte und Read URLs nicht in unverschlüsseltem Shared Preferences, allgemeinen Backups, Clipboard oder Share Sheet.
- WorkManager darf im MVP keinen stillen Offline-Write-Sync vortäuschen.

## 6. Responsive Story

### Compact

- Monatsgruppe über vertikaler Kartenliste.
- Suche und Filter als eigene Oberfläche oder Bottom Sheet.
- Floating Action nur, wenn sie keine Navigation oder Inhalte verdeckt; sonst klare Toolbar-Aktion.
- Detail ersetzt Liste, Zurück stellt Zustand wieder her.

### Expanded

- Story-Liste bleibt primäre Fläche.
- Detail-Pane öffnet rechts und erhält eigene Überschrift/Schließen-Aktion.
- Suche/Filter in der lokalen Story-Toolbar.
- Create Form verdrängt nicht gleichzeitig Liste und Detail in drei konkurrierende Spalten.

## 7. Accessibility-Budget

Diese Kriterien blockieren den M2-Release:

| Bereich | Web | Android |
|---|---|---|
| Zielgröße | mindestens 44 × 44 CSS-px | mindestens 48 × 48 dp |
| Textskalierung | 200 % ohne Funktionsverlust | größte unterstützte Schrift-/Displaygröße |
| Bedienung | vollständige Tastaturbedienung | TalkBack, Switch Access, externe Tastatur |
| Fokus | sichtbar, logisch, Rückgabe nach Overlay | stabiler Semantics-Fokus und Zurückpfad |
| Kontrast | WCAG-2.2-AA-Ziel gemäß QA-Vertrag | gleiche semantische Farbpaare |
| Status | Live Region nur für relevante Änderung | höfliche Statusankündigung |
| Medien | Beschreibung/Alt-Text-Vertrag | Content Description/Description |
| Bewegung | `prefers-reduced-motion` | Systemoption reduzierte Bewegung |

Automatisierte Checks ergänzen, ersetzen aber keine Tastatur-, Screenreader- und große-Schrift-Abnahme.

## 8. Produkt-Performancebudgets

Budgets sind interne Ziele und werden auf vereinbarten Referenzgeräten/-netzen gemessen.

| Messpunkt | Budget | Bemerkung |
|---|---:|---|
| Route zeigt stabile Struktur | ≤ 150 ms nach Navigation | App Shell + Screenrahmen, noch ohne Netzwerkdaten |
| gecachte Story nutzbar | ≤ 700 ms p75 | kein privater Cache aus falschem Kontext |
| Web LCP | ≤ 2,5 s p75 | repräsentativer Mobile-Web-Test |
| Web INP | ≤ 200 ms p75 | Filter, Karte, Formaktionen |
| Web CLS | ≤ 0,10 p75 | Medien reservieren Platz |
| Android Warm Start bis nutzbar | ≤ 1,0 s p75 | vereinbartes Mittelklassegerät |
| Android Cold Start bis nutzbar | ≤ 2,5 s p75 | kein Blockieren auf Medienvorabruf |
| erste sichtbare Medienvorschau | ≤ 1,5 s p75 | nach autorisiertem Inhalt auf Referenznetz |
| lokale UI-Reaktion | ≤ 100 ms | Auswahl, Privacy, Datei entfernen |
| sichtbarer Ladehinweis | ab 300 ms | kurze Vorgänge flackern nicht |
| Uploadfortschritt | spätestens nach 500 ms | Status statt erfundener Prozentwerte |

Budgets dürfen nicht durch Vorladen fremder oder privater Inhalte erreicht werden. Privacy-Filter und Autorisierung stehen vor Geschwindigkeit.

## 9. Telemetrie

Erlaubt:

- Screen-/Flow-ID,
- Plattform und App-Version,
- grobe Dauer- und Fehlerklasse,
- Online/Offline als technischer Zustand,
- Erfolg/Abbruch.

Verboten:

- Content, Emotion, Suchtext und Kommentar,
- Originaldateiname, MIME-Details und Bildmerkmale,
- Resource-, Attachment-, Space- oder Partner-ID in Produktanalytics,
- Read URLs, Tokens oder Signaturen,
- private/shared Kombinationen, wenn sie Re-Identifikation ermöglichen.

## 10. Release-Handoff

Vor Merge eines Client-Flows liegen vor:

1. Screenshots oder visuelle Tests für Compact, Medium und Expanded.
2. Tastatur-/TalkBack-Aufzeichnung des Kernpfads.
3. große-Schrift- und lange-Inhalte-Test.
4. Offline-, 401-, 404-, 409-, 429- und 5xx-Nachweis.
5. Privacy-Canary-Test aus dem Demo-Szenario.
6. Messung gegen relevante Performancebudgets.
7. Abgleich mit dem veröffentlichten OpenAPI-Vertrag.
