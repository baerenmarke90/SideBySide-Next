# SideBySide Accessibility and QA Matrix

**Status:** Release Gate für Web und Android  
**Version:** 1.0  
**Stand:** 24.08.2026

SideBySide behandelt Barrierefreiheit, Privacy und adaptive Darstellung als Produktqualität. Zielstandard ist WCAG 2.2 AA für die WebApp; dieselben Prinzipien werden plattformgerecht auf Android angewendet.

## 1. Testprinzipien

- Automatisierte Prüfungen finden häufige Fehler; manuelle Bedienung bleibt verpflichtend.
- Eine Plattform darf einen Flow nicht als fertig markieren, wenn die andere fachlich abweicht.
- Kritische Pfade werden mit echten Bedienhilfen geprüft, nicht nur über Simulator-Flags.
- Testdaten sind synthetisch und enthalten keine realen privaten Inhalte.
- Privacy-, Cross-Tenant- und Accessibility-Fehler blockieren ein Release.

## 2. Verbindliche Testumgebungen

### Web

- aktuelle und vorherige stabile Version von Chrome/Chromium und Firefox,
- aktuelle stabile Version von Safari auf macOS/iOS, soweit WebApp unterstützt,
- Chromium-basiertes Edge für Windows,
- Tastatur-only,
- mindestens NVDA oder JAWS unter Windows sowie VoiceOver auf Apple-Plattformen,
- 200 % Browserzoom und Betriebssystem-Kontrastmodus.

### Android

- kleinste im Projekt tatsächlich unterstützte Android-Version,
- aktuelle stabile Android-Version,
- kleines Smartphone, großes Smartphone, Tablet-/Expanded-Fenster,
- Portrait, Landscape und Fenstergrößenänderung,
- TalkBack, große Schrift/Displaygröße, Switch Access oder vergleichbare Schaltersteuerung,
- reduzierte Bewegung und hoher Kontrast, soweit vom System bereitgestellt.

Die konkrete Versionsliste wird pro Release aus Browser-Support und Android-Buildkonfiguration erzeugt, nicht dauerhaft in diesem Dokument eingefroren.

## 3. Accessibility-Matrix

| Bereich | Web-Prüfung | Android-Prüfung | Release-Kriterium |
|---|---|---|---|
| Semantik | native Elemente, korrekte Rollen/Namen | Compose Semantics, sinnvolle Zusammenfassung | Name, Rolle, Wert und Status verständlich |
| Tastatur/Schalter | Tab, Shift+Tab, Enter, Space, Escape, Pfeiltasten | Switch Access, externe Tastatur | jede Aktion ohne Touch/Maus erreichbar |
| Fokus | sichtbar, logisch, Rückkehr nach Overlay | TalkBack-/Tastaturfokus stabil | kein Fokusverlust oder Fokusfalle |
| Überschriften | eindeutige H1, logische Ebenen | Screen-/Bereichstitel angesagt | schnelle Orientierung möglich |
| Navigation | Skip Link, Landmarks, aktive Navigation | klare Bottom-/Rail-Semantik | aktueller Ort erkennbar |
| Textskalierung | 200 % Zoom ohne Funktionsverlust | größte unterstützte Schrift/Displaygröße | kein abgeschnittener Pflichttext |
| Kontrast | WCAG 2.2 AA | gleiche semantische Farbpaare | Text/Controls erfüllen Mindestwerte |
| Farbe | Status zusätzlich mit Text/Form/Icon | Status zusätzlich mit Text/Form/Icon | keine reine Farbcodierung |
| Touch-/Klickziel | mindestens 44 × 44 CSS-px | mindestens 48 × 48 dp | Kernziel ohne Präzisionsgeste bedienbar |
| Bewegung | `prefers-reduced-motion` | Systemoption reduzierte Bewegung | kein Informationsverlust ohne Animation |
| Formulare | Label, Hint, Fehlerzuordnung, Autocomplete | Label, Fehler, passende Tastatur | Fehler auffindbar und korrigierbar |
| Medien | Alt-Text/Beschreibung, Untertitelstatus | Content Description/Description | Bedeutung ohne Bild/Ton verfügbar |
| Live-Status | angemessene Live Region | höfliche Statusankündigung | Saving/Error angekündigt, Fokus bleibt |
| Overlays | Fokusfang, Escape, Rückgabe | Zurück, Fokus, Drag nur ergänzend | vollständig schließ- und bedienbar |
| Zeitlimits | Verlängerung/Erklärung | Verlängerung/Erklärung | keine überraschende Datenlöschung |

## 4. Flow-Matrix

| Kritischer Flow | Tastatur/TalkBack | große Schrift | Offline/Netzwerk | Privacy/Security | Deep Link/Zurück |
|---|---:|---:|---:|---:|---:|
| Anmeldung/Passkey/Magic Link | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Space erstellen | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Einladung annehmen | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Erinnerung + Medien | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Herzmoment privat/geteilt | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Wunsch → Plan | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Story-Suche und Detail | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| 409-Konflikt | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |
| Export/Kontoaktion | Pflicht | Pflicht | Pflicht | Pflicht | Pflicht |

## 5. Zustandsmatrix pro datenbasierter Ansicht

Jeder Screen wird mindestens in diesen Zuständen visuell und funktional geprüft:

| Zustand | Erwartung |
|---|---|
| Initial | keine zufälligen alten Inhalte oder Layoutsprünge |
| Loading | strukturelles Skeleton, verständliche Semantik |
| Content | Kernaufgabe vollständig bedienbar |
| Empty – Erstnutzung | Nutzen und passende Startaktion |
| Empty – Filter/Suche | Filtergrund und Zurücksetzen |
| Validation Error | Eingabe bleibt, Fokus/Fehlerzusammenfassung funktioniert |
| 401 | Re-Authentifizierung mit erhaltenem Ziel |
| 404 | neutral, keine Existenz fremder Inhalte verraten |
| 409 | keine stille Überschreibung, bewusste Entscheidung |
| 429 | Wartezeit und begrenzter Retry |
| 5xx | vorhandene Daten bleiben, Retry möglich |
| Offline Cache | Stand und Read-only klar sichtbar |
| Offline Write | „Noch nicht gespeichert“, kein Sync-Versprechen |

## 6. Responsive QA

Mindestens diese Breiten werden pro Template geprüft:

- 320 px: engster realistischer Compact-Fall,
- 599 px: obere Compact-Grenze,
- 600 px und 839 px: Medium-Grenzen,
- 840 px: Beginn Expanded,
- 1280 px und 1440 px: typische Desktopbreiten.

Zusätzlich:

- lange deutsche Texte und mindestens eine Sprache mit längeren Labels,
- 200 % Textzoom ohne horizontales Scrollen der Kernaufgabe,
- Wechsel zwischen Ein- und Mehrpane ohne Verlust von Auswahl, Entwurf oder Fokus,
- Soft Keyboard verdeckt keine Pflichtfelder oder Abschlussaktionen,
- sichere Bereiche, Display Cutouts und Systemleisten werden berücksichtigt.

## 7. Formulare

- Jedes Feld besitzt dauerhaft sichtbares Label.
- Pflicht/optional wird textlich oder systematisch erklärt.
- Fehler erscheint am Feld und bei langen Formularen zusätzlich in einer fokussierbaren Zusammenfassung.
- Fokus springt beim Absenden zum ersten fehlerhaften Feld oder zur Fehlerzusammenfassung.
- Fehler verschwindet erst, wenn Ursache korrigiert oder erneut validiert wurde.
- Autocomplete, Eingabetyp und Passwortmanager funktionieren.
- Copy/Paste wird nicht ohne Sicherheitsgrund blockiert.
- Deaktivierte Aktionen erklären fehlende Voraussetzungen.
- Ungespeicherte Eingaben überleben harmlose Layoutwechsel und Netzwerkfehler.

## 8. Navigation und Overlays

- Skip Link führt auf Web direkt zum Hauptinhalt.
- Hauptnavigation besitzt konsistente Reihenfolge und aktiven Status.
- Browser-Zurück und Android System Back schließen zuerst kontextuelle Overlays oder navigieren im erwarteten Verlauf.
- Dialogfokus startet sinnvoll, bleibt im Dialog und kehrt zum Auslöser zurück.
- Bottom Sheets sind nicht ausschließlich per Drag bedienbar.
- Mehrpane-Auswahl ist für Assistenztechnologien als Auswahl erkennbar.
- Deep Links landen nach Authentifizierung wieder am Ziel.

## 9. Privacy- und Security-QA

Für jede `OWNER_ONLY`-Domäne wird getrennt getestet:

- Liste und Detail,
- Suche und Trefferzahl,
- Dashboard und Story,
- Benachrichtigung und Vorschau,
- Export,
- Beziehungen und Kommentare,
- Attachments und signierte URLs,
- Update und Delete,
- Android Read-Cache,
- Web Query-/Browsercache,
- Logs, Analytics und Crashreporting.

Tenant-Matrix:

```text
Account A / Space A / Mitglied     → erlaubt
Account B / Space A / Partner      → erlaubt für SPACE_SHARED
Account B / Space A / Partner      → niemals für OWNER_ONLY von A
Account C / Space B                → niemals Zugriff auf Space A
Anonym                              → niemals Zugriff
```

## 10. Medien-QA

- tatsächlicher MIME-Type, Größe und Bilddimensionen werden serverseitig geprüft,
- ungültige, zu große und manipulierte Dateien liefern sichere Fehler,
- Fortschritt, Abbruch, Retry und Teilerfolg sind bedienbar,
- abgelaufene signierte URL wird erneuert, ohne Öffentlichkeit herzustellen,
- Alt-Text/Beschreibung kann erfasst und bearbeitet werden,
- Videos zeigen Dauer und Untertitelstatus,
- Dateiname und Metadaten erscheinen nicht ungewollt in Analytics oder Storage-Pfaden.

## 11. Automatisierte Gates

### Web

- Lint und Typecheck,
- Komponententests für Rolle, Name, Tastatur und Fokus,
- automatisierte Accessibility-Prüfung der P0-Komponenten und kritischen Screens,
- visuelle Regression für Compact und Expanded,
- Routertests für Deep Link und Zurück,
- Contract-Tests gegen OpenAPI-Beispiele.

### Android

- Compile/Lint und Unit-Tests,
- Compose-Semantics-Tests für P0-Komponenten,
- Navigation-/Back-Tests,
- Screenshottests für zentrale Größen und Schriftstufen,
- Room-Cache- und Logout-Isolationstests,
- Contract-Tests gegen dieselben API-Beispiele.

Automatisierung ersetzt nicht die manuelle Prüfung mit Screenreader/TalkBack und realer Tastatur/Schaltersteuerung.

## 12. Severity und Freigabe

| Stufe | Beispiel | Wirkung |
|---|---|---|
| Blocker | fremder/private Inhalt sichtbar, Login nicht bedienbar | Release stoppen |
| Kritisch | Kernflow nicht per Tastatur/TalkBack möglich | Release stoppen |
| Hoch | Fokusverlust, Text abgeschnitten, destruktive Aktion unklar | vor Release beheben |
| Mittel | inkonsistente Ansage oder unnötiger Fokusweg | zeitnah beheben |
| Niedrig | kleine nicht blockierende visuelle Abweichung | geplant beheben |

## 13. Definition of Done

- Alle Pflichtzellen der Flow-Matrix sind geprüft.
- Keine Blocker-, kritischen oder hohen Befunde sind offen.
- Automatisierte Gates laufen reproduzierbar in CI.
- Manuelle Ergebnisse nennen Plattform, Version, Bedienhilfe und Testdatum.
- Privacy-Tests decken indirekte Lecks und Caches ab.
- Bekannte mittlere/niedrige Befunde besitzen Owner und Zieltermin.

## Referenzen

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/patterns/)
- [Android Accessibility](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility)
- [User Flows](./USER-FLOWS.md)
- [Screen-Templates](./SCREEN-TEMPLATES.md)
