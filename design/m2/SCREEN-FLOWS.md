# M2 Screen Flows

**Zweck:** implementierbare End-to-End-Pfade für Web und Android  
**Stand:** 24.08.2026

## 1. Navigationsmodell

Die globale Reihenfolge bleibt unverändert:

```text
Heute · Story · Planen · Entdecken · Mehr
```

M2 lebt primär in `Story`. `Heute` darf kontextuelle Einstiege wie „Moment festhalten“ oder einen Rückblick zeigen, erzeugt aber keine zweite M2-Navigation.

### M2-Routen als Produktvertrag

| Route-ID | Ansicht | Sichtbarkeit | Compact | Expanded |
|---|---|---|---|---|
| `story` | gemeinsame Timeline | Space-Mitglieder | Seite | Liste + Detail-Pane |
| `story/search` | Suche und Filter | Space-Mitglieder | Overlay/Seite | Toolbar + Ergebnisliste |
| `memory/new` | Erinnerung erstellen | Space-Mitglieder | neue Seite | zentrierte Form Page |
| `memory/:id` | Memory-Detail | Space-Mitglieder | neue Seite | Detail-Pane |
| `heart-moment/new` | Herzmoment erstellen | Space-Mitglieder | neue Seite | zentrierte Form Page |
| `heart-moment/:id` | HeartMoment-Detail | gemäß Visibility | neue Seite | Detail-Pane |
| `private-moments` | persönliche HeartMoments | nur Owner | neue Seite unter `Mehr` | geschützter Bereich unter `Mehr` |
| `milestone/new` | Meilenstein erstellen | Space-Mitglieder | neue Seite | zentrierte Form Page |
| `milestone/:id` | Milestone-Detail | Space-Mitglieder | neue Seite | Detail-Pane |

Die technischen URL-Pfade folgen später dem Router-Konzept. Die Route-IDs beschreiben Navigation und Deep-Link-Verhalten, nicht automatisch Backend-Routen.

## 2. Einstieg „Moment festhalten“

**Einstiege:** Quick Action auf `Heute`, primäre Aktion in `Story`, Kontextaktion im leeren Story-Zustand.

```text
Moment festhalten
├── Erinnerung
├── Herzmoment
└── Meilenstein
```

- Compact: Bottom Sheet mit drei klar beschriebenen Optionen.
- Expanded: kleines Menü oder Dialog am auslösenden Element.
- Fokus kehrt beim Abbrechen zur auslösenden Aktion zurück.
- Die Auswahl wird nicht gemerkt; jeder neue Inhalt beginnt bewusst.
- „Privat“ wird nicht im Picker vorweggenommen, weil nur HeartMoment diese Wahl unterstützt.

## 3. Flow M2-A – Story ansehen, filtern und öffnen

**Ziel:** geteilte Geschichte chronologisch lesen, ohne private Inhalte anzudeuten.

1. Person öffnet `Story`.
2. Die Timeline lädt cursor-basiert und gruppiert nach Monat.
3. Filter bieten Typ, Jahr und Sortierreihenfolge; Suche ist serverseitig.
4. Auswahl einer Karte öffnet das Original.
5. Compact nutzt eine neue Seite; Expanded hält die Timeline sichtbar und öffnet ein Detail-Pane.
6. Zurück stellt Suchtext, Filter, Cursor, Auswahl und Scrollposition wieder her.

**Story enthält:** Memory, Milestone, `SHARED` HeartMoment.  
**Story enthält niemals:** `PRIVATE` HeartMoment, versteckte Attachment-Relation oder Partner-Canary.

**Karteninhalt**

- Typ und Autor,
- Titel/Textvorschau gemäß Domain,
- `happenedOn` als fachliches Datum,
- maximal eine ruhige Medienvorschau plus Anzahl,
- Kommentaranzahl nur für erlaubte Targets,
- kein redundantes „geteilt“-Badge auf jeder gemeinsamen Memory; Privacy-Hinweis dort, wo eine Wahl existiert.

## 4. Flow M2-B – Memory mit Medien erstellen

**Privacy:** immer `SPACE_SHARED`; kein versteckter Privatmodus.

1. Typ „Erinnerung“ wählen.
2. Titel, Text und fachliches Datum erfassen.
3. Null bis mehrere Medien auswählen.
4. Jede Datei erscheint sofort als lokale Kachel mit Status.
5. Validierungsfehler werden pro Datei gezeigt; andere Dateien und Texte bleiben erhalten.
6. Vor dem Speichern steht sichtbar „Mit Partner geteilt“.
7. Online speichern; Erfolg öffnet die neue Memory.
8. Story wird aktualisiert, sobald der fachliche Inhalt verfügbar ist; Medien dürfen nachvollziehbar nachziehen.

### Medienzustände im Formular

```text
selected → validating → uploading → processing → ready
                  └──────────────→ failed → retry | remove
```

| Zustand | Darstellung | Erlaubte Aktion |
|---|---|---|
| selected | Vorschau + Dateityp | entfernen |
| validating | „Datei wird geprüft …“ | abbrechen, falls technisch sicher |
| uploading | Fortschritt ohne falsche Genauigkeit | abbrechen/entfernen gemäß Contract |
| processing | „Foto wird verarbeitet …“ | Formular verlassen nur mit Hinweis |
| ready | Vorschau, Reihenfolge, Beschreibung | verschieben, entfernen |
| failed | Grund in verständlicher Kategorie | erneut versuchen oder entfernen |

Ein fehlgeschlagenes Medium verwirft nicht automatisch den Memory-Entwurf. Ob die Memory vor allen Uploads gespeichert werden darf, folgt der Media-/API-Entscheidung und wird nicht clientseitig improvisiert.

## 5. Flow M2-C – HeartMoment privat oder geteilt

1. Text und Emotion erfassen.
2. Sichtbarkeit verpflichtend wählen:
   - **Nur für mich** – der Partner sieht diesen Moment nicht.
   - **Mit Partner teilen** – der Moment erscheint im gemeinsamen Bereich.
3. Optional ein Attachment hinzufügen.
4. Vor dem ersten Teilen erklärt die UI knapp die Folge.
5. Speichern zeigt anschließend Privacy-Label und Sync-Zustand.

### Private Route

- Erfolg führt in den persönlichen Bereich `private-moments` beziehungsweise das Owner-only-Detail.
- Die gemeinsame `Story` wird nicht als Rückweg angeboten.
- Keine Kommentaraktion, keine Partner-Avatare und keine gemeinsame Aktivitätsanzeige.
- Private Inhalte dürfen nicht in allgemeiner Suche, „zuletzt geöffnet“, Push Preview oder gemeinsamem Share Sheet auftauchen.

### Geteilte Route

- Erfolg öffnet das geteilte Detail und macht den Eintrag in `Story` sichtbar.
- Kommentare sind erlaubt.
- Wechsel `SHARED → PRIVATE` ist online, versionsgeprüft und erklärt, dass bereits Gelesenes nicht rückwirkend ungesehen wird.
- Das Verhalten vorhandener Kommentare folgt `M2-D07` im Decision Log.

## 6. Flow M2-D – Milestone erfassen

1. Typ „Meilenstein“ wählen.
2. Titel, optionalen Text und fachliches Datum erfassen.
3. Klarer Hinweis auf gemeinsame Sichtbarkeit.
4. Speichern öffnet das Milestone-Detail.
5. Story zeigt den Milestone als eigenständigen Typ, nicht als dekorierte Memory.

Keine Chapter-, Place- oder Recap-Steuerung in M2. Die UI hält dafür nur strukturell Platz, zeigt aber keine deaktivierten Zukunftsfunktionen.

## 7. Flow M2-E – Kommentieren und Benachrichtigen

**Erlaubte Targets:** geteilte Memory, Milestone, geteiltes HeartMoment.

1. Person öffnet erlaubtes Detail.
2. Kommentare laden nach Domainberechtigung.
3. „Kommentar schreiben“ öffnet Inline Composer (Compact) oder festen Detailbereich (Expanded).
4. Senden zeigt genau einen optimistischen Zustand nur, wenn der API-Vertrag Idempotenz sicher trägt; sonst „Wird gesendet …“ bis Bestätigung.
5. Erfolg ergänzt den Kommentar und hält Fokus am neuen Element oder Composer gemäß Aktion.
6. Kommentar auf fremdem Inhalt erzeugt ein minimales Domain Event; Push-Vorschau bleibt generisch.

Bei `404` wird weder Target-Existenz noch Privacy-Grund erklärt. Bei Wechsel zu privat verschwindet der gemeinsame Kommentarpfad vollständig.

## 8. Flow M2-F – Offline Read und blockiertes Write

### Lesen

- Letzte autorisierte Ansicht darf mit „Offline · Stand von {Zeit}“ gezeigt werden.
- Medien ohne sicheren lokalen Cache erhalten einen neutralen Platzhalter.
- Space-Wechsel, Logout oder Session-Widerruf entfernt/sperrt Space- und Owner-gebundene Caches.

### Schreiben

- Eingaben dürfen als lokaler Entwurf im aktuellen sicheren Kontext bleiben.
- Absenden endet niemals in „Gespeichert“ oder „Synchronisiert“.
- Text: „Noch nicht gespeichert. Verbinde dich mit dem Internet und versuche es erneut.“
- Nach Wiederverbindung erfolgt Retry nur durch bewusste Aktion.
- Privacy-Wechsel ist offline nicht erlaubt.

## 9. Flow M2-G – Versionskonflikt

1. Update erhält `409`.
2. Der aktuelle Serverstand wird sicher nachgeladen.
3. UI zeigt „Dieser Inhalt wurde inzwischen geändert.“
4. Person kann aktuellen Stand ansehen und eigene Eingabe kopieren/erneut anwenden.
5. Kein automatisches Last-write-wins.
6. Bei Privacy-relevanten Konflikten wird niemals eine ältere Sichtbarkeit erneut gespeichert.

## 10. Deep Links und Rückkehr

- Deep Link prüft Auth, Membership und Ressourcensichtbarkeit vor Darstellung.
- Nicht vorhanden und nicht berechtigt teilen denselben neutralen `404`-Zustand.
- Nach Re-Authentifizierung wird nur zu einem weiterhin erlaubten Ziel zurückgekehrt.
- Expanded: geschlossener Detail-Pane stellt Fokus und Listenauswahl wieder her.
- Compact: System-Zurück kehrt zur vorherigen Filter-/Scrollposition zurück.
- Ein Deep Link auf `PRIVATE` ist nur im Owner-Kontext auflösbar.

## 11. Analytics-Grenzen

Erlaubt sind Ereignisklasse, Erfolg/Fehlerkategorie, Plattform und grobe Dauerklasse. Nicht erlaubt sind Titel, Body, Kommentar, Suchtext, Originaldateiname, Medieninhalt, Read URL, konkrete Emotion, Resource-ID oder Partnerkennung.
