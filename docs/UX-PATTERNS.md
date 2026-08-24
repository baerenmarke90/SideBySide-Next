# SideBySide UX Patterns

**Status:** Verbindliche Produktgrundlage  
**Version:** 1.0  
**Stand:** 24.08.2026

Dieses Dokument legt die wiederkehrenden Interaktionsmuster für WebApp und Smartphone-App fest. Beide Oberflächen teilen dieselbe Informationsarchitektur, Semantik und Zustandslogik. Die konkrete Darstellung passt sich an Plattform, Fensterbreite und Eingabemethode an.

## 1. Grundregeln

1. **Gleiche Aufgabe, gleiche Begriffe.** Eine Funktion heißt auf allen Plattformen gleich.
2. **Plattformgerecht statt pixelgleich.** Navigation, Dialoge und Gesten dürfen sich unterscheiden, solange Bedeutung und Ergebnis gleich bleiben.
3. **Privacy ist sichtbar.** Private und geteilte Inhalte werden vor, während und nach einer Aktion eindeutig gekennzeichnet.
4. **Der aktuelle Zustand ist erkennbar.** Laden, Speichern, Synchronisieren, Offline-Betrieb und Fehler bleiben nie unsichtbar.
5. **Eine primäre Aktion pro Ansicht.** Weitere Aktionen sind visuell nachgeordnet.
6. **Keine Sackgassen.** Jeder leere oder fehlerhafte Zustand bietet einen sinnvollen nächsten Schritt.
7. **Progressive Offenlegung.** Häufige Aufgaben bleiben direkt erreichbar; seltene Optionen erscheinen kontextuell.

## 2. App Shell und Navigation

| Fensterklasse | Primärnavigation | Sekundärnavigation | Detailansicht |
|---|---|---|---|
| Compact, bis 599 px | Bottom Navigation mit maximal 5 Zielen | Tabs oder lokale Liste | neue Seite |
| Medium, 600–839 px | Navigation Rail | Tabs oder Liste | neue Seite oder zweites Pane |
| Expanded, ab 840 px | persistente Sidebar/Rail | lokale Navigation im Inhaltsbereich | zweites oder drittes Pane |

- Primärziele: **Heute, Story, Planen, Entdecken, Mehr**.
- Das aktive Ziel ist durch Form, Farbe und Text erkennbar – nicht nur durch Farbe.
- Badge-Zahlen werden nur für handlungsrelevante, aktuelle Hinweise genutzt.
- Auf Web sind alle Hauptfunktionen per Tastatur erreichbar; Fokus bleibt sichtbar.
- Zurück navigiert innerhalb des aktuellen Arbeitsflusses, nicht überraschend zum Start.

## 3. Kanonische Interaktionsmuster

| Aufgabe | Smartphone | WebApp |
|---|---|---|
| Hauptnavigation | Bottom Navigation | Rail oder Sidebar |
| Liste und Detail | getrennte Seiten | List-Detail-Layout ab Medium |
| Kurze Eingabe | Bottom Sheet oder Dialog | Dialog oder Side Pane |
| Langes Formular | eigene Seite | eigene Seite oder breites Side Pane |
| Filter | Filter-Sheet | Popover oder persistente Filterleiste |
| Kontextaktionen | Overflow-Menü; Gesten nur ergänzend | Overflow- oder Kontextmenü |
| Bestätigung | Dialog bei hohem Risiko | Dialog bei hohem Risiko |
| Rückmeldung | inline plus Snackbar bei Bedarf | inline plus Snackbar bei Bedarf |

### 3.1 Liste–Detail

- Eine Zeile oder Karte öffnet genau ein Detailobjekt.
- Auswahlzustand bleibt auf breiten Layouts sichtbar.
- Filter, Sortierung und Scrollposition bleiben beim Zurücknavigieren erhalten.
- Auf Compact ersetzt das Detail die Liste; auf Expanded bleibt die Liste sichtbar.
- Direkte Links öffnen das Zielobjekt und markieren den passenden Navigationskontext.

### 3.2 Erstellen und Bearbeiten

- Kurze Formulare: maximal fünf einfache Felder in Sheet, Dialog oder Side Pane.
- Lange, verzweigte oder medienreiche Formulare: eigene Seite.
- Pflichtfelder werden in Textform markiert; Fehler stehen direkt am betroffenen Feld.
- Änderungen werden nur automatisch gespeichert, wenn der Zustand eindeutig sichtbar und wiederherstellbar ist.
- Bei ungespeicherten Änderungen fragt die App vor dem Verlassen nach.
- Nach erfolgreichem Erstellen führt die App zum neuen Inhalt oder zurück zur aktualisierten Liste.

### 3.3 Dialog, Bottom Sheet, Side Pane oder Seite

| Muster | Verwenden für | Nicht verwenden für |
|---|---|---|
| Dialog | irreversible Entscheidung, kurze Bestätigung | mehrstufige Formulare |
| Bottom Sheet | mobile Auswahl, kurze kontextuelle Aktion | kritische Langtexte |
| Side Pane | Web-Details, Vorschau, kurze Bearbeitung | zentrale Vollbildaufgabe auf Compact |
| eigene Seite | fokussierte, komplexe oder teilbare Aufgabe | einzelne Ja/Nein-Frage |

### 3.4 Suche, Filter und Sortierung

- Suche startet erst nach sinnvoller Eingabe oder kurzer Verzögerung; laufende Anfragen werden ersetzt.
- Aktive Filter sind als entfernbare Chips sichtbar.
- „Zurücksetzen“ erscheint nur, wenn mindestens ein Filter aktiv ist.
- Trefferzahl und leerer Suchzustand erklären das Ergebnis.
- Sortierung verändert keine Daten und ist klar von Filtern getrennt.
- Suchbegriffe, Filter und Sortierung bleiben während einer Sitzung erhalten.

## 4. Zustände jeder datenbasierten Ansicht

Jede datenbasierte Komponente und jeder Screen unterstützt diese Zustände:

| Zustand | Darstellung | Primäre Reaktion |
|---|---|---|
| Initial | stabile Grundstruktur | noch keine Aktion |
| Loading | Skeleton in erwarteter Form | Inhalt abwarten |
| Content | echte Inhalte | Kernaufgabe ausführen |
| Empty | Ursache und Nutzen erklären | Inhalt anlegen oder entdecken |
| Error | verständliche Ursache, soweit bekannt | erneut versuchen |
| Offline | lokale Inhalte plus Status | offline weiterarbeiten oder erneut verbinden |
| Syncing | dezenter, persistenter Status | weiterarbeiten |
| Conflict | Unterschiede und Folgen erklären | Version bewusst auswählen |

- Ein Spinner allein ersetzt keine stabile Ladeansicht.
- Vorhandene Inhalte bleiben bei Hintergrundaktualisierung sichtbar.
- Kritische Fehler stehen inline; eine Snackbar allein reicht nicht.
- Erfolgsrückmeldungen verschwinden automatisch, solange keine weitere Handlung nötig ist.

## 5. Speichern, Synchronisieren und Rückgängig

- Sichere, reversible Änderungen dürfen optimistisch dargestellt werden.
- Bei fehlgeschlagenem Speichern wird der lokale Entwurf erhalten.
- Synchronisationsstatus lautet klar: **Wird gespeichert**, **Gespeichert**, **Offline gespeichert**, **Aktion nötig**.
- Löschungen sind nach Möglichkeit über „Rückgängig“ wiederherstellbar.
- Konflikte werden niemals still überschrieben.
- Zeitstempel dienen nur als Zusatz; der verständliche Status steht zuerst.

## 6. Privacy und Teilen

- Jedes teilbare Objekt besitzt den Zustand `private` oder `shared`.
- Der Sichtbarkeitsstatus steht nahe Titel, Formularabschluss oder Hauptaktion.
- Die Voreinstellung ist der datensparsamere Zustand, sofern der Produktkontext nichts anderes zwingend verlangt.
- Vor dem ersten Teilen werden Empfänger, Inhalt und Wirkung erklärt.
- Ein Wechsel von privat zu geteilt ist eine bewusste Aktion und erhält eine klare Bestätigung im Ergebnis.
- Ein Wechsel zurück zu privat erklärt, ob bereits synchronisierte Kopien oder Benachrichtigungen betroffen sind.
- Sicherheits- und Verschlüsselungsaussagen werden nur angezeigt, wenn sie technisch belegt sind.

## 7. Berechtigungen

- Systemberechtigungen werden **just in time** angefragt, unmittelbar nach einer verständlichen Nutzeraktion.
- Vor der Systemabfrage erklärt die App Nutzen und Alternative.
- Ablehnen blockiert nur die betroffene Funktion, nicht die gesamte App.
- Einstellungen bieten einen nachvollziehbaren Weg, Berechtigungen später zu ändern.
- Kamera, Fotos, Standort, Kontakte und Benachrichtigungen werden getrennt begründet.

## 8. Destruktive und sensible Aktionen

- Destruktive Aktionen sind textlich benannt und visuell eindeutig.
- Eine Bestätigung ist erforderlich, wenn Daten nicht direkt wiederherstellbar sind oder andere Personen betroffen sind.
- Die Bestätigung benennt konkretes Objekt und Folge, zum Beispiel „Erinnerung endgültig löschen“.
- Swipe-Gesten sind nur Abkürzungen; dieselbe Aktion ist über ein sichtbares Menü verfügbar.
- Abmelden, Beziehung trennen und Konto löschen sind getrennte Aktionen mit unterschiedlicher Risikostufe.

## 9. Medien-Upload

Medien durchlaufen die Zustände `selected → preparing → uploading → processing → ready` oder `failed`.

- Vor dem Upload sind Vorschau, Dateityp und Entfernen möglich.
- Fortschritt wird pro Medium angezeigt.
- Ein Fehler betrifft nur das jeweilige Medium und bietet „Erneut versuchen“.
- Abbruch und erneute Auswahl sind jederzeit vor dem finalen Speichern möglich.
- Alt-Text oder eine Beschreibung ist für inhaltlich relevante Bilder verfügbar.
- Metadaten und Standortinformationen werden nach dokumentierter Privacy-Regel behandelt.

## 10. Benachrichtigungen

- Push-Vorschauen enthalten standardmäßig keine sensiblen Inhalte.
- Nutzer:innen wählen Ereignistyp, Kanal und Vorschaugrad.
- Jede Benachrichtigung führt zu einem konkreten Ziel.
- Gruppierung verhindert eine Folge einzelner Hinweise für denselben Vorgang.
- In-App-Hinweise ersetzen keine systemische Fehleranzeige.

## 11. Bewegung und Feedback

- Animation erklärt Hierarchie, Ursache oder Ortswechsel.
- Standarddauer: 120–280 ms; kein regulärer Übergang dauert länger als 320 ms.
- `prefers-reduced-motion` und die Systemeinstellung für reduzierte Bewegung werden respektiert.
- Kein Inhalt ist nur während einer Animation lesbar.
- Haptisches Feedback ergänzt eine sichtbare Zustandsänderung, ersetzt sie aber nicht.

## 12. Barrierefreiheit

- Touch-Ziele sind mindestens 48 × 48 dp in der App und 44 × 44 CSS-px im Web.
- Text und wesentliche Symbole erfüllen mindestens WCAG 2.2 AA.
- Fokusreihenfolge folgt der visuellen und semantischen Reihenfolge.
- Web-Komponenten nutzen native HTML-Elemente, bevor ARIA-Rollen ergänzt werden.
- Jeder Icon-Button besitzt einen zugänglichen Namen.
- Informationen werden nie ausschließlich über Farbe, Position, Bewegung oder Haptik vermittelt.
- Dynamische Statusmeldungen sind für Assistenztechnologien angekündigt, ohne den Fokus unnötig zu verschieben.

## 13. Anti-Patterns

- Karten in Karten ohne echte Hierarchie.
- Mehrere gleich starke Hauptaktionen.
- Icon-only für seltene oder kritische Aktionen.
- Löschen ausschließlich per Swipe.
- Kritische Fehler nur als kurzlebige Snackbar.
- Deaktivierte Buttons ohne Erklärung für fehlende Voraussetzungen.
- Horizontales Scrollen als versteckte Hauptnavigation.
- Unterschiedliche Begriffe für dieselbe Funktion auf Web und Mobile.
- Privacy-Versprechen, die nicht durch Technik und Betrieb abgesichert sind.
- Desktop-Layout, das auf dem Smartphone nur zusammengestaucht wird.

## 14. Abnahmekriterien

Ein neuer Flow ist erst bereit für Umsetzung, wenn:

- Compact- und Expanded-Verhalten beschrieben sind,
- Loading, Empty, Error, Offline und Success berücksichtigt sind,
- Privacy- und Berechtigungsfolgen geklärt sind,
- Tastatur, Fokus, Screenreader und große Schrift mitgedacht sind,
- eine primäre Aktion und ein klarer Rückweg existieren,
- destruktive Aktionen reversibel oder bewusst bestätigt sind,
- Analyseereignisse keine sensiblen Inhaltsdaten übertragen.

## Verwandte Dokumente

- [Design-Prinzipien](./DESIGN-PRINCIPLES.md)
- [Informationsarchitektur](./INFORMATION-ARCHITECTURE.md)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Screen-Templates](./SCREEN-TEMPLATES.md)
- [Design-Tokens](../design/tokens.json)
