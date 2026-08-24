# SideBySide Design System Delivery

**Status:** Verbindlicher Umsetzungsrahmen  
**Version:** 1.0  
**Stand:** 24.08.2026

Dieses Dokument macht aus Designprinzipien, Tokens und Component Contracts ein ausführbares Design-System für React/TypeScript und Kotlin/Jetpack Compose. Ziel ist semantische Parität, nicht pixelidentische Plattformen.

## 1. Zielbild

```text
design/tokens.json
        │
        ├── Web Token Adapter ─────── React Components ───── Web Catalog
        │
        └── Android Token Adapter ─── Compose Components ─── Android Catalog

docs/COMPONENT-CONTRACTS.md + design/component-manifest.json
        └────────────────── gemeinsamer Verhaltensvertrag
```

- `design/tokens.json` ist die Quelle für semantische Designwerte.
- Component Contracts sind die Quelle für Verhalten, Zustände und Accessibility.
- Plattformadapter übersetzen Einheiten und native Mechanik, nicht Bedeutung.
- OpenAPI liefert fachliche Datenmodelle; UI-Komponenten enthalten keine Domain-Autorisierung.

## 2. Paritätsstufen

| Ebene | Muss gleich sein | Darf abweichen |
|---|---|---|
| Semantik | Name, Zweck, Variante, Zustand, Privacy-Bedeutung | interne Implementierung |
| Verhalten | Ergebnis, Validierung, Fehler, Back-Verhalten | native Geste/Overlayform |
| Visuell | Farbsemantik, Typohierarchie, Abstände, Radiusfamilie | Systemfontmetriken, native Controls |
| Accessibility | Name, Rolle, Wert, Fokusziel, Zielgröße | plattformspezifische API |
| Layout | Compact/Medium/Expanded-Regeln | Pane- und Navigationsmechanik |

## 3. Logische Struktur

Die genaue Ordnerstruktur folgt dem Repository, soll aber diese Module abbilden:

```text
design/
  tokens.json
  component-manifest.json

web design system/
  generated tokens
  primitives
  components
  patterns
  icons
  catalog/examples

android design system/
  generated tokens/theme
  primitives
  components
  patterns
  icons
  catalog/examples
```

- Generierte Dateien tragen einen Header und werden nicht manuell bearbeitet.
- Domain-Screens importieren Komponenten, nicht rohe Farben/Abstände.
- Komponenten dürfen Tokens konsumieren; Tokens dürfen keine Komponente kennen.

## 4. Token-Pipeline

### Quelle

`design/tokens.json` enthält semantische Farben, Typografie, Spacing, Radius, Layout, Bewegung, Schatten und Zielgrößen.

### Web-Ausgabe

- CSS Custom Properties für Theme- und Laufzeitwerte.
- typisierte TypeScript-Namen für Komponentenlogik.
- Media Queries/Container Queries aus Breakpoint- und Motion-Tokens.
- `prefers-reduced-motion` setzt reguläre Übergänge auf `instant` oder eine sichere reduzierte Variante.

### Android-Ausgabe

- Compose `Color`, `Dp`, Shapes, Typography und Motion-Werte.
- Material-3-Theme als Adapter, ohne SideBySide-Semantik in generische Materialnamen zu verlieren.
- Window Size Classes werden auf Compact/Medium/Expanded gemappt.

### Pipeline-Gates

- JSON und Schema sind gültig.
- jeder semantische Token existiert in beiden Adaptern oder ist explizit plattformspezifisch,
- generierte Ausgabe ist reproduzierbar und im CI-Diff sauber,
- Farbkontrast-Smoketests prüfen zentrale Vorder-/Hintergrundpaare,
- rohe Hexwerte und nicht-tokenisierte Abstände werden außerhalb des Tokenmoduls verhindert oder gemeldet.

## 5. Komponentenstufen

### P0 — Foundation

- Button, IconButton, Link,
- TextField, TextArea, Checkbox, Radio, Switch,
- NavigationItem, Tabs,
- ListItem, ContentCard,
- VisibilityControl, StatusBadge, SyncIndicator,
- InlineMessage, Snackbar,
- Skeleton, EmptyState, ErrorState,
- Dialog, BottomSheet, SidePane,
- MediaTile.

### P1 — Produktpatterns

- App Shell für Bottom Bar/Rail/Sidebar,
- adaptive List-Detail-Struktur,
- Formularseite mit Fehlerzusammenfassung,
- Story Timeline Item und Monatsgruppe,
- Privacy-Auswahl HeartMoment,
- Upload Queue,
- Konfliktauflösung,
- Auth-/Invitation-Layout.

### P2 — Domain-Kompositionen

- Today-Module,
- Memory Editor und Detail,
- Wunsch-/Plan-Statusfluss,
- Settings-/Privacy-Seiten,
- Exportstatus,
- spätere Shopping- und Discover-Kompositionen hinter Feature-Verfügbarkeit.

## 6. Plattformkataloge

Beide Plattformen erhalten einen internen visuellen Katalog.

Jeder Eintrag zeigt:

- Purpose und Contract-Link,
- alle Varianten,
- Default, Hover/Pressed, Focus, Disabled, Loading, Error,
- lange Texte und Lokalisierungsbeispiel,
- große Schrift/200 % Zoom,
- Hellmodus und spätere Themes,
- Privacy- und Statusfarben mit Text,
- Compact und Expanded, falls layoutrelevant,
- Codebeispiel und verbotene Nutzung.

Der Katalog ist Entwicklungswerkzeug, keine öffentliche Produktseite.

## 7. Component API Rules

- Komponenten heißen nach Aufgabe, nicht nach Aussehen: `VisibilityControl`, nicht `PinkChip`.
- Varianten sind geschlossene Enums, keine frei kombinierbaren Style-Flags.
- Text wird als Inhalt übergeben; Komponenten erfinden keine Domain-Copy.
- Icon-only benötigt expliziten zugänglichen Namen.
- `loading` und `disabled` sind getrennte Zustände.
- Layoutkomponenten besitzen keine versteckte Navigation oder API-Abfrage.
- Domain-IDs, Tokens und private Inhalte werden nicht in Analytics-Callbacks einer Basiskomponente aufgenommen.

## 8. Beispiel eines plattformneutralen Contracts

```text
Button
  variant: primary | secondary | tertiary | destructive
  state: default | disabled | submitting
  label: required
  icon: optional
  action: exactly one callback
  accessibility: visible label is accessible name
  size: web ≥ 44 px, Android ≥ 48 dp
```

Web kann dies als natives `<button>` umsetzen; Android als Compose Button-Adapter. Ergebnis und Zustände bleiben gleich.

## 9. Adaptive Layout Delivery

- Breakpoints stammen aus Tokens.
- Navigation wechselt Bottom Bar → Rail → Sidebar ohne Änderung der Route-IDs.
- List-Detail wird ab Medium nur aktiviert, wenn Auswahl und Fokus erhalten bleiben.
- Screen-Templates werden als wiederverwendbare Layoutpatterns umgesetzt, nicht pro Domain kopiert.
- Android verwendet Window Size Classes; Web orientiert sich an verfügbarer Container-/Fensterbreite.
- Ein Größenwechsel verwirft keinen Entwurf und löst keine neue Domainaktion aus.

## 10. Testing Gates pro Komponente

### Gemeinsame Pflichtfälle

- Contract-Varianten und Zustände,
- lange Labels,
- große Schrift/Zoom,
- Hellmodus und hoher Kontrast,
- zugänglicher Name/Rolle/Wert,
- Fokus/Zurück/Schließen,
- Touch-/Klickziel,
- reduzierte Bewegung,
- visuelle Regression.

### Web zusätzlich

- native HTML-Semantik,
- Tastaturmuster nach WAI-ARIA APG, wenn kein natives Element reicht,
- Server-/Client-Rendering ohne Layoutsprung, falls später relevant,
- Browsermatrix gemäß QA-Dokument.

### Android zusätzlich

- Compose Semantics und TalkBack,
- System Back und Prozesswiederherstellung,
- unterschiedliche Schrift-/Displaygrößen,
- Compact/Medium/Expanded.

## 11. Versionierung

- Design-Tokens und Komponentenbibliotheken verwenden Semantic Versioning.
- Patch: visuelle/technische Korrektur ohne Contract-Änderung.
- Minor: additive Variante oder Komponente.
- Major: entfernte/umbenannte API oder geänderte Bedeutung.
- Deprecations besitzen Ersatz, Migrationshinweis und frühestes Entfernungsrelease.
- Produktcode importiert nur öffentliche Exports des Design-Systems.

## 12. Ownership und Entscheidungen

Für jede P0-/P1-Komponente werden benannt:

- fachlicher Owner,
- Design-Owner,
- Web- und Android-Implementierungsverantwortung,
- Accessibility-Review,
- aktueller Status im Manifest.

Neue Muster werden zuerst als Contract/Decision dokumentiert. Ein lokaler Sonderfall in einem Screen wird nicht automatisch Teil des Systems.

## 13. Lieferphasen

### Phase DS0 — Pipeline

- Token-Schema und Generatoren,
- Web- und Android-Themeadapter,
- CI-Validierung,
- leere Plattformkataloge.

### Phase DS1 — P0 Components

- Action-, Input-, Navigation-, Feedback- und Privacy-Komponenten,
- Accessibility- und Screenshottests,
- vollständige Katalogeinträge.

### Phase DS2 — App Shell und Systemzustände

- adaptive Navigation,
- Loading/Empty/Error/Offline,
- Dialog/Sheet/Pane,
- Auth-/Invitation-Grundlayout.

### Phase DS3 — Erste Domain-Flows

- Onboarding/Invitation,
- Memory/Media,
- HeartMoment-Privacy,
- Story List-Detail,
- Wunsch → Plan.

### Phase DS4 — Härtung

- visuelle Parität,
- Lokalisierungsstresstest,
- Performance,
- Dokumentation und Deprecation-Prozess.

## 14. Freigabekriterien

- Tokenadapter sind reproduzierbar.
- P0-Komponenten sind in beiden Katalogen sichtbar.
- Keine lokale Farb-/Spacing-Semantik dupliziert Tokens.
- Accessibility-Matrix ist für P0 erfüllt.
- Privacy-Zustände verwenden technische Klassen korrekt.
- Offline-MVP zeigt Read Cache, aber keinen erfundenen Write Sync.
- Web und Android bestehen dieselben Flow-Beispiele gegen denselben API-Mock.
- Manifeststatus und Dokumentation entsprechen dem ausgelieferten Stand.

## Verwandte Dokumente

- [Design-Tokens](../design/tokens.json)
- [Component Manifest](../design/component-manifest.json)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Screen-Templates](./SCREEN-TEMPLATES.md)
- [Accessibility- und QA-Matrix](./ACCESSIBILITY-QA-MATRIX.md)
