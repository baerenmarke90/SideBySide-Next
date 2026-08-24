# Informationsarchitektur für SideBySide Next

**Status:** Verbindliche Grundlage für Web und App  
**Version:** 1.0  
**Gültig ab:** 24. August 2026

Dieses Dokument definiert Navigation, Benennung, Routen und die Zuordnung der
Produktfunktionen. Web und Android verwenden dieselbe fachliche Architektur,
passen ihre Navigation aber an Fenstergröße und Plattformkonventionen an.

## 1. Grundregeln

- Der gemeinsame **Space** ist der konstante Produktkontext.
- Die Hauptnavigation enthält höchstens fünf Ziele.
- Ein Inhalt hat genau einen fachlichen Hauptort; Querverweise sind Deep Links.
- Routen spiegeln Aufgaben und Inhalte, nicht technische Module.
- Private und geteilte Inhalte verwenden dieselbe Navigation, zeigen ihren
  Sichtbarkeitsstatus aber direkt am Inhalt.
- Navigation darf keine ungespeicherten Eingaben ohne Warnung verwerfen.
- Web und App verwenden dieselben Begriffe und stabilen Route-IDs.

## 2. Verbindliche Hauptnavigation

| Route-ID | Deutscher Name | Zweck |
|---|---|---|
| `today` | Heute | gemeinsamer Überblick und nächste sinnvolle Schritte |
| `story` | Story | private Timeline der gemeinsamen Erinnerungen |
| `plan` | Planen | Wünsche, konkrete Pläne und Einkauf |
| `discover` | Entdecken | kuratierte Inspiration für gemeinsame Zeit |
| `more` | Mehr | Space, Privacy, Profil und Einstellungen |

### Plattformdarstellung

- **Kompakte Fenster:** Bottom Navigation mit Icon und Textlabel.
- **Mittlere Fenster:** Navigation Rail.
- **Große Webfenster:** feste Sidebar mit Textlabel; sekundäre Ziele dürfen
  eingerückt sichtbar sein.
- Die Reihenfolge bleibt auf allen Plattformen identisch.
- Der aktuelle Bereich ist mit Farbe, Icon und Textzustand erkennbar.

## 3. Strukturbaum

```text
SideBySide Next
├── Heute
│   ├── nächster gemeinsamer Moment
│   ├── persönliche und gemeinsame Empfehlungen
│   ├── Rückblicke
│   └── offene Aufgaben und Hinweise
├── Story
│   ├── Timeline
│   ├── Erinnerung
│   │   ├── Medien
│   │   ├── Ort und Datum
│   │   ├── Sichtbarkeit
│   │   └── Bearbeitung
│   └── neue Erinnerung
├── Planen
│   ├── Wünsche
│   │   ├── privat
│   │   ├── geteilt
│   │   └── Wunschdetail
│   ├── Pläne
│   │   ├── Status
│   │   ├── Termin
│   │   ├── Checkliste
│   │   └── Medien und Notizen
│   └── Einkauf
│       ├── gemeinsame Liste
│       ├── Zuständigkeiten
│       └── Rezeptideen
├── Entdecken
│   ├── Feed
│   ├── Filter
│   ├── Empfehlung
│   └── in Wunsch oder Plan übernehmen
└── Mehr
    ├── Space und Partner
    ├── Privatsphäre und Berechtigungen
    ├── Benachrichtigungen
    ├── Profil und Präferenzen
    ├── Datenexport und Account-Löschung
    └── Hilfe, Rechtliches und App-Informationen
```

## 4. Planen als gemeinsamer Hub

`Planen` bündelt drei eng verbundene Zustände:

1. **Wunsch:** eine Idee ohne verbindlichen Termin.
2. **Plan:** eine konkretisierte Idee mit Status, Termin oder Aufgaben.
3. **Einkauf:** eine wiederkehrende gemeinsame Alltagsliste.

Wünsche und Pläne dürfen nicht als voneinander isolierte Datenwelten wirken.
Eine Umwandlung von Wunsch zu Plan ist ein sichtbarer, nachvollziehbarer
Statuswechsel. Entdecken erzeugt keine vierte Kopie eines Inhalts, sondern kann
eine Empfehlung als Wunsch oder Plan übernehmen.

### Sekundärnavigation

- Smartphone: Segmented Control oder Tabs `Wünsche | Pläne | Einkauf`.
- Web: dieselben Tabs innerhalb des Planen-Bereichs; auf großen Fenstern kann
  eine Liste mit Detail-Pane verwendet werden.
- Der zuletzt gewählte Unterbereich darf lokal wiederhergestellt werden.
- Deep Links öffnen immer den konkreten Unterbereich und Inhalt.

## 5. Routenmodell

Die folgenden Pfade sind die kanonischen Webpfade und zugleich Grundlage für
App-Deep-Links. IDs sind undurchsichtige, stabile Bezeichner.

| Aufgabe | Kanonischer Pfad |
|---|---|
| Heute öffnen | `/today` |
| Story öffnen | `/story` |
| Erinnerung öffnen | `/story/memories/:memoryId` |
| Erinnerung erstellen | `/story/memories/new` |
| Planen-Hub | `/plan` |
| Wünsche | `/plan/wishes` |
| Wunsch öffnen | `/plan/wishes/:wishId` |
| Pläne | `/plan/plans` |
| Plan öffnen | `/plan/plans/:planId` |
| Einkauf | `/plan/shopping` |
| Entdecken | `/discover` |
| Empfehlung öffnen | `/discover/:recommendationId` |
| Mehr | `/more` |
| Space und Partner | `/more/space` |
| Privacy | `/more/privacy` |
| Benachrichtigungen | `/more/notifications` |
| Profil | `/more/profile` |
| Einstellungen | `/more/settings` |
| Daten und Account | `/more/data-account` |

### Deep-Link-Regeln

- Jeder Detailinhalt besitzt einen teilbaren internen Deep Link.
- Ein Deep Link prüft Authentifizierung und Space-Mitgliedschaft, bevor Daten
  geladen werden.
- Nicht berechtigte Inhalte werden nicht als vorhandene Ressource bestätigt.
- Nach Login oder Einladung wird zum ursprünglich angeforderten Ziel
  zurückgekehrt.
- Gelöschte Inhalte erhalten einen verständlichen Zustand statt einer
  generischen leeren Seite.

## 6. Screen- und Pane-Verhalten

| Inhalt | Kompakt | Mittel | Erweitert |
|---|---|---|---|
| Story | Liste oder Detail | Liste oder Detail | Timeline + Detail |
| Wünsche | Liste oder Detail | Liste oder Detail | Liste + Detail |
| Pläne | Liste oder Detail | Liste oder Detail | Liste + Detail + optionale Unterstützung |
| Einkauf | eine Liste | Liste + optionale Rezeptkarte | Liste + Rezept-/Detail-Pane |
| Entdecken | Feed + Detail-Screen | Feed + Detail | Grid/Feed + Detail-Pane |
| Einstellungen | gestapelte Seiten | Seite mit Kategorien | Kategorien + Einstellungsdetail |

Das Detail ersetzt auf kleinen Fenstern die Liste. Auf großen Fenstern bleibt
die Liste sichtbar und der ausgewählte Inhalt erscheint daneben. Der
Zurück-Zustand muss beim Wechsel zwischen Fenstergrößen erhalten bleiben.

## 7. Benennung und Sprache

### Verbindliche Begriffe

| Fachbegriff | UI-Name | Nicht verwenden |
|---|---|---|
| gemeinsamer Mandant | Space | Workspace, Tenant |
| Beziehungspartner | Partner | Kontakt, Nutzer 2 |
| Erinnerung | Erinnerung | Post, Beitrag |
| Wunsch | Wunsch | Bookmark, Favorite |
| konkreter gemeinsamer Vorgang | Plan | Projekt, Task-Liste |
| Sichtbarkeit nur für Eigentümer | Nur für mich | Owner-only |
| Sichtbarkeit im Space | Mit Partner teilen | Public, freigeben für alle |

- Technische Begriffe bleiben aus der Endnutzeroberfläche fern.
- Buttons verwenden Verben: `Speichern`, `Teilen`, `Planen`, `Entfernen`.
- Navigationslabels verwenden Substantive oder etablierte Produktnamen.
- Deutsch und Englisch müssen ohne abweichende Navigationsstruktur funktionieren.

## 8. Rollen und Sichtbarkeit

Navigation ist nicht gleich Berechtigung. Ein sichtbarer Navigationsbereich
garantiert keinen Zugriff auf jedes Objekt darin.

### Sichtbarkeitswerte

| Wert | Bedeutung | UI-Label |
|---|---|---|
| `private` | nur die erstellende Person | Nur für mich |
| `shared` | beide aktiven Space-Mitglieder | Mit Partner teilen |

Weitere Sichtbarkeitsstufen werden erst eingeführt, wenn das Produkt tatsächlich
mehr als zwei Space-Mitglieder unterstützt. `public` ist kein zulässiger Wert.

## 9. URL-, Verlauf- und Zurück-Verhalten

- Auswahl, Filter und relevante Tabs werden im URL- oder Navigationszustand
  abgebildet, wenn sie einen wiederherstellbaren Kontext darstellen.
- Modale Kurzinteraktionen erzeugen nur dann einen Verlaufseintrag, wenn sie
  per Deep Link geöffnet werden können.
- Android System Back und Browser Back verhalten sich fachlich gleich.
- Schließen beendet einen Dialog; Zurück navigiert im Verlauf.
- Ein Wechsel der Hauptnavigation erzeugt keinen gestapelten Detailverlauf.

## 10. Offene Produktentscheidungen

Vor M1 müssen diese Punkte entschieden werden:

- Ist `private` oder `shared` der Standard für neue Wünsche?
- Welche Inhalte erscheinen in Benachrichtigungsvorschauen?
- Darf eine Empfehlung direkt als Plan übernommen werden oder zunächst nur als Wunsch?
- Welche Filter werden zwischen Sitzungen gespeichert?
- Wie werden Inhalte dargestellt, wenn eine Partnerschaft beendet wurde?

## 11. Akzeptanzkriterien

- [ ] Jede Funktion ist genau einem Hauptbereich zugeordnet.
- [ ] Web und App verwenden identische Route-IDs und Labels.
- [ ] Bottom Bar, Rail und Sidebar besitzen dieselbe Reihenfolge.
- [ ] Detailrouten sind deep-link-fähig.
- [ ] Auth-, Membership- und Löschzustände sind definiert.
- [ ] Zurück-Verhalten funktioniert bei Ein- und Mehrfensterlayouts.
- [ ] Navigation bleibt mit Tastatur, Screenreader und Textskalierung bedienbar.

## Verwandte Dokumente

- [Design-Prinzipien](DESIGN-PRINCIPLES.md)
- [UX-Patterns](UX-PATTERNS.md)
- [Component Contracts](COMPONENT-CONTRACTS.md)
- [Screen-Templates](SCREEN-TEMPLATES.md)
