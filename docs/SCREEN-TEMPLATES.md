# SideBySide Screen Templates

**Status:** Verbindliche Produktgrundlage  
**Version:** 1.1  
**Stand:** 24.08.2026

Screen-Templates übersetzen Informationsarchitektur, UX-Patterns und Components in wiederholbare Seitenstrukturen. Sie sind keine fertigen Screens, sondern verbindliche Layout- und Verhaltensrahmen.

## 1. Fensterklassen

| Klasse | Breite | Navigation | Inhalt |
|---|---:|---|---|
| Compact | 0–599 px | Bottom Navigation | ein Haupt-Pane |
| Medium | 600–839 px | Navigation Rail | ein bis zwei Panes |
| Expanded | ab 840 px | Rail oder Sidebar | zwei bis drei Panes |

- Wechsel erfolgt nach verfügbarer Fensterbreite, nicht nach Gerätebezeichnung.
- Inhalt bleibt bei Größenänderung erhalten; Auswahl und Eingaben gehen nicht verloren.
- Hauptinhalt ist maximal 1200 px breit, Lesetext maximal 720 px.
- Außenabstand: 20 px Compact, mindestens 24 px Medium, bis 64 px Expanded.

## 2. Gemeinsame Screen-Anatomie

Jeder reguläre Screen besitzt in dieser Reihenfolge:

1. App Shell und Navigationskontext.
2. Seitentitel und optionale kurze Einordnung.
3. Primäre Aktion, passend zur Fensterklasse platziert.
4. Optional: Tabs, Filter oder lokale Navigation.
5. Hauptinhalt.
6. Persistente Statusfläche für Offline, Sync oder Fehler, falls nötig.

Auf Compact darf eine Floating Action Button-ähnliche Aktion nur verwendet werden, wenn sie eindeutig, häufig und nicht mit der Bottom Navigation verwechselt wird.

## 3. Template: Heute

**Zweck:** Gemeinsamer Tagesüberblick und schneller Einstieg.

### Compact

- Begrüßung und gemeinsamer Kontext.
- Eine hervorgehobene nächste Aktion oder Erinnerung.
- Vertikale Module: heute geplant, offene Punkte, neuer Moment.
- Primäre Aktion kontextabhängig, zum Beispiel „Moment festhalten“.

### Expanded

- Zweispaltiges Dashboard.
- Hauptspalte: Tagesverlauf und nächste Aufgaben.
- Nebenspalte: Quick Actions, Sync-/Privacy-Hinweise und kompakte Zusammenfassung.
- Keine frei konfigurierbare Widget-Wand in Version 1.

**Pflichtzustände:** erster Start, alles erledigt, offline mit lokalen Daten, teilweiser Ladefehler.

## 4. Template: Story Timeline

**Zweck:** Gemeinsame Erinnerungen chronologisch entdecken.

### Compact

- Filter/Suche als Sheet.
- Timeline als vertikale Liste.
- Detail öffnet eine neue Seite.
- „Erinnerung hinzufügen“ als sichtbare Hauptaktion.

### Expanded

- Linkes Pane: Filter und Zeiträume.
- Mittleres Pane: Timeline.
- Rechtes Pane: ausgewählte Erinnerung oder Vorschau.
- Direkte URL für jedes Detail.

**Pflichtzustände:** keine Erinnerungen, leere Filterung, Medien laden, privater Inhalt, Uploadfehler.

## 5. Template: Planen Hub

**Zweck:** Einstieg in Wünsche und Pläne; Einkauf wird später als eigene Domain ergänzt.

### Compact

- Zwei klar benannte Einstiege mit aktuellem Status; ein späterer Einkaufseinstieg
  erscheint erst bei implementierter und aktivierter Domain.
- Letzte oder dringende Inhalte unterhalb der Einstiege.
- Keine verschachtelte Kartenlandschaft.

### Expanded

- Lokale Navigation oder Segmentierung für Wünsche und Pläne; Einkauf später.
- List-Detail-Struktur für gewählten Bereich.
- Unterstützendes Pane nur bei echtem Zusatznutzen.

**Primäre Aktion:** wechselt mit aktivem Bereich, zum Beispiel „Wunsch hinzufügen“.

**Pflichtzustände:** leerer Bereich, gemeinsame und private Einträge, Sync-Konflikt, erledigte Einträge.

## 6. Template: Einkaufsliste (spätere Domain)

**Zweck:** Schnelles gemeinsames Abhaken, auch bei schlechter Verbindung.

### Compact

- Direkteingabe am oberen Rand.
- Gruppierte Checkliste mit großen Touch-Zielen.
- Offline-Stand bleibt sichtbar; Schreiben ist im MVP ohne Verbindung nicht erlaubt.
- Zusatzinformationen öffnen ein Sheet oder eine Seite.

### Expanded

- Hauptpane: Liste und Eingabe.
- Optionales Nebenpane: ausgewähltes Rezept, Notiz oder Verlauf.
- Tastaturkürzel für Hinzufügen und Fokuswechsel.

**Pflichtzustände:** Offline-Read-Cache, Offline-Schreibversuch „Noch nicht gespeichert“, Online-Konflikt, alles erledigt, gelöschten Eintrag rückgängig machen.

## 7. Template: Entdecken

**Zweck:** Inspiration anbieten, ohne private Kernaufgaben zu überdecken.

### Compact

- Suchfeld, Themenchips und vertikaler Feed.
- Filter in einem Sheet.
- Detail öffnet eine neue Seite.

### Expanded

- Such- und Filterleiste oberhalb eines responsiven Grids.
- Optionales Detail-Pane bei schneller Vorschau; vollständiges Detail besitzt eine URL.
- Karten bleiben gleichartig und vermeiden wechselnde Interaktionslogik.

**Pflichtzustände:** personalisierte und neutrale Empfehlungen, keine Treffer, Empfehlungsfehler, blockierte externe Quelle.

## 8. Template: Settings und Privacy

**Zweck:** Beziehung, Konto, Daten, Berechtigungen und Benachrichtigungen verständlich steuern.

### Compact

- Kategorisierte Liste; jede Kategorie öffnet eine eigene Seite.
- Kritische Aktionen stehen am Ende des passenden Bereichs, nicht gesammelt als Gefahrzone ohne Kontext.

### Expanded

- Linkes Pane: Kategorien.
- Rechtes Pane: ausgewählte Einstellungen.
- Änderungen wirken entweder sofort mit Rückmeldung oder werden über eine klar sichtbare Speichern-Aktion bestätigt – nie gemischt innerhalb eines Formulars.

**Pflichtzustände:** Berechtigung abgelehnt/blockiert, Export wird erstellt, Kontoaktion ausstehend, Beziehung nicht verbunden.

## 9. Template: Erstellen/Bearbeiten

**Zweck:** Inhalte sicher und nachvollziehbar anlegen oder ändern.

### Compact

- Eigene Seite bei langen Formularen.
- Sticky Abschlussaktion nur, wenn sie Inhalt nicht verdeckt und mit Tastatur sichtbar bleibt.
- Sichtbarkeit steht nahe dem Abschluss.

### Expanded

- Formular maximal 720 px breit.
- Optionale Vorschau oder Kontextinformation im Nebenpane.
- Seitenleiste ist kein Ablageort für Pflichtfelder.

**Reihenfolge:** Titel → Hauptinhalt → Datum/Metadaten → Medien → Sichtbarkeit → Abschluss.

**Pflichtzustände:** Validierungsfehler, Upload läuft/fehlt, ungespeicherte Änderungen, Offline-Schreibversuch „Noch nicht gespeichert“, Speichern fehlgeschlagen.

## 10. Template: Auth und Einladung

**Zweck:** Sicherer, verständlicher Einstieg und Verbindung mit einer Partnerperson.

### Alle Größen

- Ein fokussierter Flow ohne reguläre Hauptnavigation.
- Nutzen und Privacy-Kontext vor sensiblen Angaben.
- Fortschritt nur bei tatsächlich mehrstufigem Ablauf.
- Einladung kann verschoben oder erneut gesendet werden.
- Einzelne Nutzung ist möglich, soweit das Produktkonzept es erlaubt.

### Expanded

- Formular bleibt in einer schmalen Lesespalte.
- Eine optionale Illustration unterstützt Atmosphäre, trägt aber keine notwendigen Informationen.

**Pflichtzustände:** Link abgelaufen, Konto existiert, falsche Person, Einladung ausstehend, Verbindung erfolgreich.

## 11. Template: Detailansicht

**Zweck:** Ein Objekt lesen, bearbeiten, teilen oder verwalten.

### Compact

- Titel, Sichtbarkeit und wichtigste Meta-Information vor dem Inhalt.
- Sekundäraktionen im Overflow; Bearbeiten bleibt sichtbar, wenn häufig.
- Zurück führt zur vorherigen Liste mit erhaltenem Kontext.

### Expanded

- Kann als zweites oder drittes Pane erscheinen.
- Direkte URL und Browser-Zurück bleiben korrekt.
- Bei sehr umfangreichem Inhalt wechselt das Detail auf eine vollständige Seite.

**Pflichtzustände:** nicht gefunden, keine Berechtigung, veraltet, Konflikt, gelöscht.

## 12. Template: Systemzustände

### Empty

- Titel benennt den Zustand.
- Ein Satz erklärt Nutzen oder Ursache.
- Eine primäre Aktion führt zum nächsten sinnvollen Schritt.
- Illustration ist optional und rein unterstützend.

### Error

- Vorhandene Inhalte bleiben sichtbar, wenn möglich.
- Fehlermeldung erklärt Auswirkung und nächsten Schritt.
- Retry erscheint nur, wenn technisch sinnvoll.
- Support-/Diagnosecode ist kopierbar, aber visuell nachgeordnet.

### Offline

- Globaler Status erscheint kompakt in der Shell.
- Betroffene Schreibaktionen erklären, dass sie nicht gespeichert wurden. Ein
  sicherer Formularentwurf darf erhalten bleiben, ist aber kein Domainobjekt.
- Wiederverbinden aktualisiert den Read-Cache; ein erneuter Schreibversuch erfolgt
  im MVP bewusst und nicht über eine lokale Outbox.

### No Permission

- Erklärt fehlende Berechtigung und Alternative.
- Führt bei dauerhaft blockierter Systemberechtigung zu den passenden Systemeinstellungen.
- Kein wiederholtes automatisches Öffnen der Systemabfrage.

## 13. Responsives Verhalten

- Reihenfolge folgt Bedeutung, nicht der Desktop-Position.
- Zwei Panes werden auf Compact zu zwei navigierbaren Seiten.
- Unterstützende Inhalte folgen auf Compact nach dem Hauptinhalt oder öffnen kontextuell.
- Tabellen werden zu Listen/Details, wenn horizontales Scrollen die Kernaufgabe behindert.
- Aktionen bleiben in allen Größen semantisch gleich benannt.
- Layoutänderungen verschieben Fokus nicht unerwartet.
- Bei Bildschirmdrehung oder Fensteränderung bleiben Entwurf, Auswahl und Scrollkontext erhalten.

## 14. Abnahmecheck pro Screen

- Seitentitel und Navigationskontext sind eindeutig.
- Es gibt höchstens eine visuell dominante Aktion.
- Compact, Medium und Expanded sind festgelegt.
- Browser-Zurück, App-Zurück und Deep Link funktionieren.
- Loading, Empty, Error, Offline und Success sind gestaltet.
- Privacy-, Permission- und Sync-Zustände sind sichtbar.
- Tastatur, Fokus, Screenreader und 200 % Textzoom sind geprüft.
- Touch-Ziele und Kontrast erfüllen die gemeinsamen Vorgaben.
- Analyse erfasst nur notwendige, nicht sensible Ereignisse.

## Verwandte Dokumente

- [Design-Prinzipien](./DESIGN-PRINCIPLES.md)
- [Informationsarchitektur](./INFORMATION-ARCHITECTURE.md)
- [UX Patterns](./UX-PATTERNS.md)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Design-Tokens](../design/tokens.json)
- [Critical User Flows](./USER-FLOWS.md)
- [Accessibility- und QA-Matrix](./ACCESSIBILITY-QA-MATRIX.md)
