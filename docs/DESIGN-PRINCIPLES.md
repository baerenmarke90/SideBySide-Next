# Design-Prinzipien für SideBySide Next

**Status:** Verbindliche Grundlage für Web und App  
**Version:** 1.0  
**Gültig ab:** 24. August 2026  
**Markenversprechen:** *Gemeinsam leben. Privat verbunden.*

Dieses Dokument übersetzt die Produktidee von SideBySide Next in verbindliche
Gestaltungsregeln. Es gilt für Produktoberflächen, Website, Store-Auftritt,
Marketingseiten und neue Funktionen.

Die Begriffe **MUSS**, **SOLLTE** und **KANN** beschreiben die Verbindlichkeit.
Bei Konflikten gilt diese Reihenfolge:

1. Datenschutz und Sicherheit
2. Barrierefreiheit
3. Verständlichkeit und Nutzbarkeit
4. Konsistenz
5. Markenwirkung
6. visuelle Neuheit

## 1. Gestaltungsziel

SideBySide soll sich wie ein ruhiger, privater Raum für zwei Menschen anfühlen:
warm, persönlich und hochwertig, aber niemals kitschig oder überladen.

Jede Oberfläche beantwortet innerhalb weniger Sekunden:

- Wo bin ich?
- Was ist hier gemeinsam und was ist privat?
- Was ist der nächste sinnvolle Schritt?
- Welche Daten oder Berechtigungen sind betroffen?

## 2. Zehn Kernprinzipien

### 2.1 Ruhe vor Reiz

Die Oberfläche MUSS den Inhalt tragen, nicht mit ihm konkurrieren.

- Pro Ansicht gibt es höchstens eine dominante Primäraktion.
- Dekoration unterstützt Orientierung oder Stimmung; sie ist kein Selbstzweck.
- Leerraum ist ein aktiver Bestandteil des Layouts.
- Dauerhafte Animationen, aggressive Banner und unnötige Badges sind unzulässig.

### 2.2 Privacy ist ein sichtbarer Produktzustand

Privatsphäre darf nicht nur in Richtlinien erklärt werden. Sie MUSS direkt an
der Stelle erkennbar sein, an der Daten entstehen oder geteilt werden.

- Zustände heißen klar: **Nur für mich**, **Mit Partner teilen**, **Standort aus**.
- Sichtbarkeit wird immer mit Text und Icon dargestellt, nie nur mit Farbe.
- Berechtigungen werden erst im Nutzungskontext angefragt.
- Sicherheits- und Verschlüsselungsversprechen dürfen nur verwendet werden,
  wenn sie im produktiven Build technisch und operativ belegt sind.
- Kein E2EE-Claim ohne verifizierte Ende-zu-Ende-Verschlüsselung.

### 2.3 Für zwei gedacht, nicht für ein soziales Netzwerk

Der Space und die Beziehung stehen vor Profil, Reichweite oder öffentlicher
Selbstdarstellung.

- Gemeinsamer Kontext ist in Navigation und Sprache stets erkennbar.
- Es gibt keine öffentlichen Rankings, Follower-Mechaniken oder sozialen Druck.
- Empfehlungen optimieren auf gemeinsame Relevanz statt maximale Verweildauer.
- Beide Personen erhalten gleichwertige Kontrolle und nachvollziehbare Zustände.

### 2.4 Ein klarer nächster Schritt

Jede Ansicht MUSS eine eindeutige visuelle Hierarchie besitzen.

- Titel erklärt den Kontext.
- Eine kurze Unterzeile erklärt den Nutzen.
- Die Primäraktion ist visuell eindeutig.
- Sekundäraktionen treten zurück.
- Komplexe Abläufe werden in kleine, reversible Schritte zerlegt.

### 2.5 Inhalt ist der Held

Erinnerungen, Wünsche, Pläne und gemeinsame Momente stehen visuell im Zentrum.

- Karten zeigen zuerst den relevanten Inhalt, danach Metadaten.
- Reale Inhalte ersetzen generische Platzhalter so früh wie möglich.
- Bilder werden ruhig beschnitten und nie mit Text überladen.
- Empty States erklären Nutzen und nächsten Schritt, nicht nur das Fehlen von Daten.

### 2.6 Progressive Offenlegung

Die erste Ebene bleibt einfach; Details erscheinen bei Bedarf.

- Seltene Optionen gehören in Details, Menüs oder einen zweiten Schritt.
- Kritische Zustände und Privacy-Informationen dürfen nicht versteckt werden.
- Formulare fragen nur Informationen ab, die für den aktuellen Schritt nötig sind.
- Erweiterte Einstellungen behalten verständliche Standardwerte.

### 2.7 Menschliche, respektvolle Sprache

Die Sprache ist direkt, warm und nicht wertend.

- Bevorzugt werden „ihr“, „euer“, „gemeinsam“ und konkrete Verben.
- Keine Schuldmechaniken, künstliche Dringlichkeit oder Dark Patterns.
- Fehlertexte erklären, was passiert ist und wie es weitergeht.
- Texte versprechen nur Funktionen, die im aktuellen Produktstand verfügbar sind.

### 2.8 Barrierefreiheit ist Definition of Done

Barrierefreiheit ist keine spätere Optimierung.

- Zielstandard ist WCAG 2.2 AA.
- Fließtext erreicht mindestens 4,5:1 Kontrast; große Schrift und UI-Grafiken 3:1.
- Farbe ist nie der einzige Informationsträger.
- Weboberflächen sind vollständig per Tastatur bedienbar.
- App-Oberflächen unterstützen Screenreader und Textskalierung bis mindestens 200 %.
- Touch-Ziele sind mindestens 48 × 48 dp; Web-Ziele mindestens 44 × 44 px.
- Reduzierte Bewegung und ausreichende Fokusindikatoren werden unterstützt.

### 2.9 Eine Sprache über alle Plattformen

Web und App teilen Semantik, Tonalität, Tokens und Komponentenlogik.

- Die gleiche Funktion trägt denselben Namen und dieselbe Farbrolle.
- Plattformkonventionen haben Vorrang vor pixelgenauer Gleichheit.
- Android bleibt Android; Web bleibt Web.
- Neue Einzelkomponenten sind nur zulässig, wenn bestehende Muster nicht ausreichen.

### 2.10 Bewegung erklärt Veränderung

Motion dient Orientierung und Feedback.

- Standardübergänge dauern 160–220 ms.
- Größere Kontextwechsel dürfen bis 320 ms dauern.
- Animationen verwenden ruhiges Ease-out ohne starkes Springen.
- Erfolg, Synchronisation und Zustandswechsel werden subtil bestätigt.
- Dekorative Bewegung stoppt automatisch und respektiert „Reduce Motion“.

## 3. Visuelle Sprache

### 3.1 Farbsemantik

Farben werden nach Bedeutung eingesetzt, nicht nach Geschmack der einzelnen
Ansicht.

| Token | Wert | Bedeutung |
|---|---:|---|
| Background | `#FAF8FC` | warmer, ruhiger Seitenhintergrund |
| Surface | `#FFFFFF` | Karten, Dialoge und Inhaltsflächen |
| Ink | `#211A2B` | Haupttext und starke Kontraste |
| Muted | `#6F6878` | Sekundärtext |
| Line | `#E6DFEC` | Trennlinien und ruhige Umrandungen |
| Brand Purple | `#7C4DFF` | Produktkern und Primäraktion |
| Brand Soft | `#EEE7FF` | aktive oder hervorgehobene Flächen |
| Shared Mint | `#36AE97` | gemeinsam, bestätigt, synchron |
| Info Blue | `#4B96E6` | Systeminformation und Technik |
| Discovery Yellow | `#E8A932` | Inspiration, Optionen und Entdecken |
| Private Pink | `#F45B88` | privat, eingeschränkt oder owner-only |
| Dark Background | `#1C1525` | hochwertige dunkle Hero- und Fokusflächen |
| Dark Surface | `#2A2135` | Karten im Dark Mode |

Verbindliche Regeln:

- Purple ist die einzige Standardfarbe für Primäraktionen.
- Mint bedeutet geteilt, synchron oder positiv bestätigt.
- Pink kennzeichnet Privacy oder Einschränkung, nicht automatisch einen Fehler.
- Fehler und destruktive Aktionen benötigen zusätzlich ein klares Warnsymbol und
  eindeutigen Text.
- Pastellflächen dürfen nur mit ausreichend dunklem Text kombiniert werden.
- Pro Ansicht SOLLTEN höchstens zwei Akzentfarben dominieren.

### 3.2 Typografie

Maximal zwei Schriftfamilien werden verwendet:

- **Display:** Fraunces 600 für emotionale Hero-Titel und ausgewählte Story-Momente.
- **UI:** Inter 400/500/600 für Navigation, Inhalte, Formulare und Bedienelemente.
- Fallbacks: `Georgia, serif` beziehungsweise
  `system-ui, -apple-system, Segoe UI, sans-serif`.

| Ebene | Mobile | Web | Verwendung |
|---|---:|---:|---|
| Display | 32/38 | 44/52 | Hero und besondere Kapitel |
| H1 | 28/34 | 36/44 | Seitentitel |
| H2 | 24/30 | 28/36 | Abschnittstitel |
| Title | 20/26 | 20/26 | Karten und Dialoge |
| Body | 16/24 | 16/24 | Standardtext |
| Meta | 13/18 | 13/18 | Datum, Status und Hilfstext |

- Body-Text wird nie kleiner als 16 px beziehungsweise 16 sp.
- Lange Texte erhalten höchstens 70 Zeichen pro Zeile.
- Versalien sind nur für sehr kurze Labels zulässig.
- Zahlen, Uhrzeiten und Statuswerte verwenden tabellarische Ziffern.

### 3.3 Abstand und Raster

Grundmaß ist ein 4er-Raster.

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`

- Mobile Seitenränder: mindestens 20 dp.
- Web Seitenränder: 24–64 px je nach Viewport.
- Maximale Inhaltsbreite: 1200 px; Lesetext maximal 720 px.
- Standardabstand innerhalb einer Card: 20–24 px.
- Zusammengehörige Elemente stehen enger als getrennte Abschnitte.
- Weblayouts wechseln unter 768 px auf eine Spalte.

### 3.4 Formen und Tiefe

- Standardradius Cards: 20 px/dp.
- Große Hero-Flächen und Modal-Surfaces: 24–32 px/dp.
- Buttons: 14–16 px/dp; Pills nur für Filter und kompakte Statuswerte.
- Schatten bleiben weich und flach; Grenzen werden bevorzugt über Fläche und Linie erzeugt.
- Mehr als zwei sichtbare Tiefenebenen pro Ansicht sind zu vermeiden.

### 3.5 Bildwelt und Illustration

- Die Bildwelt ist weich, taktil, ruhig und leicht verträumt.
- Geeignet sind Wege, Erinnerungsobjekte, Natur, Licht und kleine Alltagsmomente.
- Keine austauschbaren Stock-Paare oder überinszenierte Romantik.
- 3D-Objekte dürfen Orientierung und Markenwärme erzeugen, aber keine UI verdecken.
- Screenshots zeigen echte, lesbare UI und höchstens eine zentrale Aussage.
- Bilder erhalten Alt-Texte; rein dekorative Bilder werden für Assistenztechnik ausgeblendet.

## 4. Komponentenregeln

### Buttons

- Pro Ansicht maximal eine visuell dominante Primäraktion.
- Primär: Purple-Fläche, weißer Text.
- Sekundär: helle Surface mit klarer Kontur.
- Tertiär: Textaktion ohne eigene Fläche.
- Destruktiv: eindeutiger Warntext; niemals ausschließlich durch Rot kommunizieren.
- Loading-Zustände behalten Breite und Beschriftungskontext bei.

### Cards

Eine Card enthält in dieser Reihenfolge:

1. Kontext oder Status
2. Titel
3. zentrale Information
4. optionale Metadaten
5. höchstens eine direkte Hauptaktion

Verschachtelte Cards sind zu vermeiden.

### Navigation

- Mobile Hauptnavigation umfasst höchstens fünf primäre Ziele.
- Webnavigation bleibt flach und zeigt den aktuellen Ort eindeutig.
- „Zurück“ und Schließen dürfen nicht dieselbe Bedeutung erhalten.
- Tiefe Links führen immer in einen verständlichen Kontext.

### Privacy- und Sharing-Control

- Jede teilbare Entität zeigt ihren aktuellen Sichtbarkeitsstatus.
- Änderungen erklären vor Bestätigung ihre Wirkung.
- Private Inhalte werden nicht in Vorschauen, Benachrichtigungen oder Analytics geleakt.
- Standort ist standardmäßig aus und wird nur kontextbezogen aktiviert.

### Feedback und Systemzustände

Jede asynchrone Aktion braucht einen sichtbaren Zustand:

`idle → loading → success | empty | error | offline`

- Optimistische Updates sind nur für reversible, unkritische Aktionen erlaubt.
- Speichern und Synchronisieren werden unterscheidbar kommuniziert.
- Offline-Zustände erklären, was lokal verfügbar bleibt.
- Fehler entfernen keine bereits eingegebenen Inhalte.

## 5. Responsive Verhalten

### App

- Mobile-first und einhändige Kernaktionen.
- Systemleisten, Insets und Tastatur werden berücksichtigt.
- Primäraktionen bleiben erreichbar, ohne Inhalte zu verdecken.
- Große Bildflächen laden abgestuft und mit stabilem Platzhalter.

### Web

- 320 px bis 1440+ px werden unterstützt.
- Eine Spalte auf Mobile, bis zu zwei Inhaltszonen auf Desktop.
- Hover ergänzt Information, ist aber nie Voraussetzung.
- Dialoge werden auf kleinen Viewports zu Bottom Sheets oder Vollbildschritten.
- Fokusreihenfolge folgt der sichtbaren Leserichtung.

## 6. Content- und Claim-Regeln

- Nutzen vor Feature-Namen.
- Ein Satz pro Kernaussage.
- Keine Rankings, Preise, Nutzerzahlen oder Sicherheitsclaims ohne belastbare Quelle.
- „Verschlüsselt übertragen“ und „Ende-zu-Ende verschlüsselt“ sind nicht austauschbar.
- Privacy-Texte nennen konkrete Wirkung statt abstrakter Versprechen.
- Texte müssen auf Deutsch und Englisch ohne Layoutbruch funktionieren.

## 7. Design-Definition-of-Done

Eine Oberfläche ist erst fertig, wenn alle Punkte erfüllt sind:

- [ ] Primärziel und nächste Aktion sind in fünf Sekunden verständlich.
- [ ] Private und geteilte Zustände sind eindeutig.
- [ ] Alle Standard-, Leer-, Lade-, Fehler- und Offline-Zustände sind gestaltet.
- [ ] Kontraste, Textskalierung, Tastatur und Screenreader wurden geprüft.
- [ ] Touch- und Klickziele erfüllen die Mindestgröße.
- [ ] Responsive Verhalten wurde auf kleinen und großen Viewports geprüft.
- [ ] Texte sind konkret, respektvoll und claim-sicher.
- [ ] Komponenten und Tokens stammen aus dem gemeinsamen Designsystem.
- [ ] Motion respektiert reduzierte Bewegung.
- [ ] Screenshots und Marketingdarstellung entsprechen dem realen Produktstand.

## 8. Governance

- Design-Tokens sind die gemeinsame Quelle für Web und App.
- Abweichungen werden dokumentiert und mit Produkt, Design und Engineering entschieden.
- Neue Komponenten benötigen mindestens Nutzung, Zustände, Accessibility-Regeln und Tokens.
- Wiederkehrende Sonderlösungen werden in das Designsystem überführt.
- Dieses Dokument wird bei jeder wesentlichen Marken-, Privacy- oder Navigationsänderung
  versioniert aktualisiert.
