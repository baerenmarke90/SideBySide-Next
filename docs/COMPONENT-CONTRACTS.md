# SideBySide Component Contracts

**Status:** Verbindliche Produktgrundlage  
**Version:** 1.1  
**Stand:** 24.08.2026

Component Contracts beschreiben Verhalten und Bedeutung gemeinsamer UI-Bausteine unabhängig vom technischen Framework. WebApp und Smartphone-App dürfen unterschiedliche Implementierungen besitzen, müssen aber dieselben Verträge erfüllen.

## 1. Aufbau eines Contracts

Jede Komponente dokumentiert:

1. **Purpose** – welches Problem sie löst.
2. **Anatomy** – verpflichtende und optionale Bestandteile.
3. **Variants** – bewusst unterstützte Varianten.
4. **States** – sichtbare und interaktive Zustände.
5. **Behavior** – Eingabe, Ausgabe und Übergänge.
6. **Accessibility** – Name, Rolle, Fokus und Bedienung.
7. **Content** – Regeln für Beschriftung und Fehlermeldungen.
8. **Analytics** – erlaubte Ereignisse ohne sensible Inhaltsdaten.

Neue visuelle Varianten werden nur ergänzt, wenn sie eine neue Bedeutung oder Interaktion ausdrücken.

## 2. Gemeinsame Zustandsmodelle

```text
LoadState       = idle | loading | content | empty | error | offline
SyncState       = local_draft | submitting | synced | failed | conflict
PrivacyClass    = SPACE_SHARED | OWNER_ONLY | TEMPORARY_SHARED | EPHEMERAL_CONTEXT | SYSTEM_METADATA
PermissionState = unknown | explaining | requesting | granted | denied | blocked
ActionState     = idle | submitting | success | error
```

- `LoadState` beschreibt das Laden einer Ansicht.
- `SyncState` beschreibt die Persistenz eines bereits sichtbaren Inhalts.
- `PrivacyClass` beschreibt die fachliche Zugriffsklasse. UI-Kürzel wie `private`
  und `shared` sind keine API-Werte.
- Zustände werden nicht zu einem unklaren Boolean wie `isLoading` verdichtet, wenn mehrere Übergänge möglich sind.
- Fehlermeldungen besitzen einen stabilen Fehlercode für Technik und eine verständliche Nachricht für Menschen.

## 3. Action Components

### 3.1 Button

**Purpose:** Löst eine klar benannte Aktion aus.

**Varianten:**

- `primary` – wichtigste Aktion der Ansicht, in der Regel einmal pro Bereich.
- `secondary` – wichtige Alternative.
- `tertiary` – leichte, kontextuelle Aktion.
- `destructive` – potenziell irreversible Aktion.

**Zustände:** `default`, `hover`, `focus`, `pressed`, `disabled`, `submitting`, `success`, `error`.

**Contract:**

- Beschriftung beginnt möglichst mit einem Verb: „Erinnerung speichern“.
- Ein Button ändert seine Breite beim Ladezustand nicht.
- `submitting` verhindert Doppelauslösung und zeigt eine textlich verständliche Aktivität.
- `disabled` ersetzt keine Validierungs- oder Berechtigungserklärung.
- Mindestziel: 48 dp in der App, 44 CSS-px im Web.
- Der zugängliche Name entspricht der sichtbaren Beschriftung oder erweitert sie sinnvoll.

### 3.2 Icon Button

- Nur für gelernte, häufige Aktionen wie Schließen, Zurück, Suchen oder Overflow.
- Besitzt immer Tooltip auf Web und einen zugänglichen Namen auf allen Plattformen.
- Kritische oder seltene Aktionen erhalten zusätzlich Text.
- Badge, Icon und Status verändern die Bedienfläche nicht.

### 3.3 Link

- Navigiert zu einem Ziel; ein Button verändert Zustand oder löst eine Aktion aus.
- Links sind an Textstil, Unterstreichung im Kontext oder zusätzlichem Merkmal erkennbar.
- Externe Ziele und Downloads werden angekündigt, wenn das Verhalten sonst überrascht.

## 4. Input Components

### 4.1 Text Field und Text Area

**Anatomy:** Label, Eingabe, optionale Hilfestellung, Zeichenzähler, Status und Fehlermeldung.

- Das Label bleibt sichtbar; Placeholder ersetzt kein Label.
- Validierung erfolgt spätestens beim Verlassen des Feldes und erneut beim Absenden.
- Fehler erklärt Problem und Korrektur direkt am Feld.
- Eingabetyp, Autocomplete und virtuelle Tastatur passen zum Inhalt.
- Text Area wächst bis zu einer definierten Maximalhöhe und bleibt danach scrollbar.
- Sensible Inhalte werden nicht ohne Zweck protokolliert oder vorausgefüllt.

### 4.2 Auswahlfelder

- Checkbox: mehrere unabhängige Optionen.
- Radio Group: genau eine Option aus einer überschaubaren Menge.
- Switch: sofort wirksamer An/Aus-Zustand; nicht zum Absenden eines Formulars.
- Select/Combobox: größere oder durchsuchbare Optionsmenge.
- Segmented Control: zwei bis vier gleichartige Ansichten oder Modi, keine langfristige Navigation.

### 4.3 Date, Time und Duration

- Plattformnative Auswahl ist zulässig, wenn Ergebnisformat und Validierung gleich bleiben.
- Zeitzone und ganztägige Ereignisse werden explizit behandelt.
- Menschlich lesbare Zusammenfassung erscheint vor dem Speichern.

## 5. Navigation Components

### 5.1 Navigation Item

**Anatomy:** Icon, sichtbares Label, optionaler Badge, aktiver Indikator.

- Status: `default`, `hover`, `focus`, `active`, `disabled`.
- Aktivität ist nicht nur farblich erkennbar.
- Reihenfolge und Bezeichnung sind auf allen Plattformen stabil.
- Ein Item führt zu einem Ort, nicht zu einer einmaligen Aktion.

### 5.2 Tabs

- Wechseln gleichrangige Inhalte innerhalb eines Bereichs.
- Die aktive Registerkarte ist programmatisch erkennbar.
- Pfeiltastenbedienung folgt dem nativen Plattformmuster.
- Tabs werden nicht über mehrere Zeilen umgebrochen; bei Platzmangel wird das Informationsmodell vereinfacht.

### 5.3 Breadcrumbs

- Nur auf Web und nur ab mindestens drei nachvollziehbaren Hierarchieebenen.
- Sie ergänzen die Hauptnavigation und ersetzen keinen Seitentitel.

## 6. Content Components

### 6.1 List Item

**Anatomy:** Titel, optionale Meta-Zeile, Leading Visual, Trailing Status oder Aktion.

- Die gesamte Zeile darf ein einziges Ziel öffnen.
- Zusätzliche Aktionen sind getrennt fokussierbar und verständlich benannt.
- Titel wird auf zwei Zeilen begrenzt; vollständiger Inhalt bleibt im Detail verfügbar.
- Auswahl-, ungelesen- und Sync-Zustand sind unterscheidbar.

### 6.2 Content Card

- Eine Karte fasst ein Objekt oder eine Handlung zusammen, nicht bloß Dekoration.
- Verschachtelte Karten sind nicht erlaubt.
- Klickbare Karten besitzen sichtbaren Fokus und genau ein Hauptziel.
- Sekundäraktionen stehen in einem klar abgegrenzten Bereich.
- Kartenradius, Innenabstand und Schatten stammen ausschließlich aus Tokens.

### 6.3 Timeline Item

- Zeigt Zeitpunkt, Urheber:in, Inhaltstyp, Sichtbarkeit und Sync-Zustand.
- Die visuelle Linie ist dekorativ; semantische Reihenfolge bleibt im Dokumentfluss.
- Mehrere Ereignisse am selben Tag können gruppiert werden, ohne einzelne Ziele zu verlieren.

### 6.4 Checklist Row

- Checkbox und Text bilden eine gemeinsame verständliche Bedienung.
- Erledigte Einträge bleiben lesbar und können wieder geöffnet werden.
- Gleichzeitige Online-Änderungen verwenden `version`; Konflikte überschreiben nichts still.
- Löschen ist über Menü und optional ergänzend über Geste erreichbar.

## 7. Privacy und Status Components

### 7.1 Visibility Control

**MVP-Auswahlwerte, wenn die Domain sie unterstützt:** `OWNER_ONLY`, `SPACE_SHARED`.

- Zeigt Icon und Text: „Nur für mich“ oder „Geteilt“.
- Im Anzeigezustand als Chip/Status, im Formular als echte Auswahlkomponente.
- Ein Wechsel erklärt Empfänger und Wirkung.
- Pink markiert privaten/geschützten Kontext, Grün geteilten Kontext; Text bleibt verpflichtend.
- Memory, Wish und Plan zeigen nur ihren Status; sie bieten im aktuellen Core
  keinen Wechsel der Privacy-Klasse. HeartMoment darf beide MVP-Werte anbieten.

### 7.2 Status Badge

- Unterstützte Kategorien: `info`, `success`, `warning`, `error`, `private`, `shared`.
- Badges enthalten maximal zwei kurze Wörter oder eine Zahl.
- Status ist nicht allein durch Farbe vermittelt.
- Badges sind nicht klickbar; interaktive Filterchips sind eine eigene Komponente.

### 7.3 Sync Indicator

- Verwendet die Texte „Wird gespeichert“, „Gespeichert“ oder „Aktion nötig“.
- Für einen fehlgeschlagenen Offline-Schreibversuch gilt separat: „Noch nicht gespeichert“.
- `synced` darf nach kurzer Zeit visuell zurücktreten.
- `failed` und `conflict` bleiben sichtbar, bis sie gelöst oder bewusst verworfen wurden.

## 8. Overlay Components

### 8.1 Dialog

- Besitzt Titel, verständlichen Inhalt, primäre und optionale sekundäre Aktion.
- Fokus startet auf dem ersten sinnvollen Element, bleibt im Dialog und kehrt danach zum Auslöser zurück.
- Escape/Zurück schließt nur, wenn dadurch keine kritischen Änderungen verloren gehen.
- Destruktive Bestätigungen benennen Objekt und Folge.

### 8.2 Bottom Sheet

- Wird auf Compact für kurze Auswahl oder kontextuelle Aktion verwendet.
- Besitzt eine klare Überschrift und eine sichtbare Schließmöglichkeit.
- Drag-to-dismiss ist nur ergänzend; Tastatur und Screenreader bleiben vollständig unterstützt.
- Lange, komplexe Flows wechseln auf eine eigene Seite.

### 8.3 Side Pane

- Wird ab Medium für Details, Vorschau oder kurze Bearbeitung genutzt.
- Breite folgt Layout-Tokens; Inhalt besitzt eine eigene scrollbare Region.
- Schließen stellt Fokus und Listenauswahl wieder her.

## 9. Feedback Components

### 9.1 Inline Message

- Erste Wahl für anhaltende Fehler, Warnungen und blockierende Informationen.
- Steht nahe dem betroffenen Inhalt und bietet bei Bedarf eine konkrete Aktion.
- Meldung besteht aus Problem, Auswirkung und nächstem Schritt.

### 9.2 Snackbar

- Für kurze, nicht kritische Bestätigung oder reversible Aktion.
- Maximal eine Aktion, zum Beispiel „Rückgängig“.
- Kritische Fehler und notwendige Entscheidungen werden nicht ausschließlich hier angezeigt.
- Dauer berücksichtigt Leselänge und Bedienhilfen.

### 9.3 Skeleton, Empty State und Error State

- Skeleton entspricht der Form des erwarteten Inhalts und animiert dezent.
- Empty State unterscheidet Erstnutzung, leere Suche und fehlende Berechtigung.
- Error State erhält „Erneut versuchen“, wenn Wiederholung sinnvoll ist.
- Bestehende Inhalte werden bei Hintergrundfehlern nicht entfernt.

## 10. Media Components

### 10.1 Media Tile

- Zeigt Vorschau, Typ, Uploadstatus, Sichtbarkeit und alternative Beschreibung.
- Fehler und Retry gelten pro Datei.
- Crop und Bearbeitung verändern nie unbemerkt das Original.
- Videos besitzen Posterframe, Dauer und Untertitelstatus.

### 10.2 Avatar Pair

- Zwei Personen werden gleichwertig dargestellt; keine Person ist visuell standardmäßig dominant.
- Initialen oder neutrale Platzhalter sind bei fehlendem Foto verfügbar.
- Status oder Rolle wird als Text ergänzt, wenn relevant.

## 11. Analytics Contract

Erlaubt sind Ereignisse wie:

```text
screen_viewed
primary_action_started
primary_action_completed
primary_action_failed
permission_explained
permission_result
sync_conflict_opened
```

Nicht erlaubt sind Freitext, Suchtext, Nachrichtentexte, Bildinhalte, exakte private Datumsangaben, direkte Resource-IDs oder andere sensible Nutzinhalte. Technische/pseudonymisierte Referenzen werden nur bei dokumentiertem Zweck und nicht als Inhaltsmerkmal übertragen.

## 12. Definition of Done

Eine gemeinsame Komponente ist bereit, wenn:

- Contract, Varianten und Zustände dokumentiert sind,
- Design-Tokens statt lokaler Werte verwendet werden,
- Web-Tastaturbedienung und Fokus geprüft sind,
- Screenreader-Name, Rolle und Status korrekt sind,
- große Schrift und Textzoom funktionieren,
- Compact und Expanded geprüft sind,
- Error, Disabled, Loading und Offline nicht fehlen,
- Privacy- und Analytics-Folgen geklärt sind,
- visuelle Regressionen automatisiert oder reproduzierbar prüfbar sind.

## Verwandte Dokumente

- [Design-Prinzipien](./DESIGN-PRINCIPLES.md)
- [Informationsarchitektur](./INFORMATION-ARCHITECTURE.md)
- [UX Patterns](./UX-PATTERNS.md)
- [Screen-Templates](./SCREEN-TEMPLATES.md)
- [Design-Tokens](../design/tokens.json)
- [API-/UI-Verträge](./API-UI-CONTRACTS.md)
- [Design-System-Umsetzung](./DESIGN-SYSTEM-DELIVERY.md)
