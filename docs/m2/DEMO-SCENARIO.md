# M2 Demo & Acceptance Scenario

**Zweck:** ein reproduzierbarer, rein fiktiver Datensatz für Demo, visuelle QA und End-to-End-Tests  
**Stand:** 24.08.2026

Alle Namen, Inhalte und Medien sind synthetisch. Produktivdaten oder echte private Erinnerungen dürfen nicht als Testfixture verwendet werden.

## 1. Personen und Spaces

| Kürzel | Person | Space | Rolle |
|---|---|---|---|
| `LEA` | Lea Sommer | `ALPHA` – Lea & Alex | Mitglied/Autor |
| `ALEX` | Alex Winter | `ALPHA` – Lea & Alex | Partner/Mitglied |
| `MIRA` | Mira Berg | `BETA` – Mira & Sam | Fremdmitglied |
| `REVOKED` | Robin Test | ehemals `ALPHA` | Mitgliedschaft widerrufen |

Referenzdatum der Demo: **24.08.2026**.

## 2. Seed-Inhalte

### Geteilte Memories

| Key | Autor | Titel | `happenedOn` | Medien | Kommentare |
|---|---|---|---|---:|---:|
| `MEM-LAKE` | LEA | Sonnenaufgang am See | 14.06.2026 | 3 Fotos | 2 |
| `MEM-KITCHEN` | ALEX | Unser erster Pastateig | 03.05.2026 | 1 Foto | 1 |
| `MEM-RAIN` | LEA | Spaziergang im Sommerregen | 19.07.2026 | 0 | 0 |

### HeartMoments

| Key | Autor | Text | Emotion | Visibility | `happenedOn` | Attachment |
|---|---|---|---|---|---|---|
| `HM-SHARED` | ALEX | „Danke, dass du heute einfach zugehört hast.“ | APPRECIATED | SHARED | 21.08.2026 | nein |
| `HM-PRIVATE` | LEA | `CANARY-PRIVATE-LEA-7421` | GRATEFUL | PRIVATE | 22.08.2026 | `private-lea-7421.jpg` |

`HM-PRIVATE` ist absichtlich technisch auffällig und darf ausschließlich in Leas Owner-Kontext erscheinen.

### Milestones

| Key | Autor | Titel | `happenedOn` |
|---|---|---|---|
| `MS-GARDEN` | ALEX | Unser erster gemeinsamer Garten | 10.04.2026 |
| `MS-HOME` | LEA | Ein Jahr in unserer Wohnung | 01.08.2026 |

### Comments

| Key | Autor | Target | Body |
|---|---|---|---|
| `COM-1` | ALEX | `MEM-LAKE` | „Den frühen Wecker war es wert.“ |
| `COM-2` | LEA | `MEM-LAKE` | „Nächstes Mal mit heißem Kaffee.“ |
| `COM-3` | LEA | `HM-SHARED` | „Das bedeutet mir viel.“ |

Keine Comment-Fixture referenziert `HM-PRIVATE`.

## 3. Medienfixtures

| Datei | Zweck | erwartetes Ergebnis |
|---|---|---|
| `lake-01.jpg` | gültiges Querformat | READY |
| `lake-02.jpg` | gültiges Hochformat | READY |
| `lake-03.jpg` | langsame Verarbeitung | PENDING/PROCESSING → READY |
| `pasta.webp` | gültiges unterstütztes Format | READY, sofern Allowlist entschieden |
| `private-lea-7421.jpg` | Private Canary | nur LEA sichtbar |
| `spoofed-jpg.exe` | MIME-Spoof | FAILED |
| `oversize-image.jpg` | Größenlimit | FAILED |
| `broken-image.jpg` | Decoderfehler | FAILED |

Binäre Fixtures werden erst nach Festlegung der Allowlist und Limits erzeugt. Dateinamen sind kein Storage Key.

## 4. Story-Erwartung

Für LEA und ALEX enthält die gemeinsame Story, absteigend sortiert:

1. `HM-SHARED` – 21.08.2026
2. `MS-HOME` – 01.08.2026
3. `MEM-RAIN` – 19.07.2026
4. `MEM-LAKE` – 14.06.2026
5. `MEM-KITCHEN` – 03.05.2026
6. `MS-GARDEN` – 10.04.2026

`HM-PRIVATE` vom 22.08.2026 erscheint **nicht**. Es erzeugt keine leere Gruppe, keinen Count-Unterschied und keinen verschobenen Cursor.

## 5. End-to-End-Szenarien

### E2E-01 Story lesen

1. ALEX öffnet Story.
2. Erwartete sechs Items erscheinen in stabiler Reihenfolge.
3. Filter „Erinnerung“ zeigt drei Memories.
4. Zurücksetzen stellt Timeline und Scrollposition wieder her.
5. DOM, Netzwerkantworten, Cache und Analytics enthalten keine Private Canary.

### E2E-02 Memory mit Medien erstellen

1. LEA startet „Moment festhalten → Erinnerung“.
2. Titel „Picknick unter den Linden“, Datum 23.08.2026 und zwei gültige Fotos erfassen.
3. Eine dritte defekte Datei hinzufügen; nur diese zeigt Fehler.
4. Defekte Datei entfernen, speichern.
5. Detail öffnet genau eine neue Memory mit zwei Medien.
6. Story zeigt sie an korrekter Position; doppeltes Absenden erzeugt kein Duplikat.

### E2E-03 Private HeartMoment

1. LEA erstellt einen HeartMoment mit „Nur für mich“.
2. Owner-only-Detail zeigt Privacy-Label und keine Kommentaraktion.
3. ALEX versucht bekannte ID, Story, Suche, Kommentare, Attachment und Export.
4. Alle Pfade zeigen neutral 404 oder enthalten keinen Treffer.
5. Logs, Events und Push enthalten weder Text noch Dateiname.

### E2E-04 Shared HeartMoment

1. ALEX erstellt einen geteilten HeartMoment.
2. Einmalige Erklärung vor erstem Teilen erscheint.
3. Eintrag erscheint in Story.
4. LEA kommentiert.
5. ALEX erhält höchstens eine generische Notification ohne Kommentartext.

### E2E-05 Milestone

1. ALEX erstellt „Erste gemeinsame Bergtour“ mit Datum.
2. Milestone-Detail und eigener Story-Typ erscheinen.
3. Keine deaktivierten Chapter-/Recap-Steuerungen sind sichtbar.

### E2E-06 Offline Read/Write

1. ALEX öffnet Story online, dann aktiviert er Flugmodus.
2. Cache zeigt „Offline · Stand von …“.
3. ALEX beginnt eine Memory, Absenden bleibt „Noch nicht gespeichert“.
4. Eingabe bleibt erhalten; keine Story-Karte und kein Success-Event entsteht.
5. Nach bewusster Wiederholung online wird genau eine Memory erzeugt.

### E2E-07 Versionskonflikt

1. LEA und ALEX öffnen `MEM-LAKE` mit gleicher Version.
2. LEA speichert eine Änderung.
3. ALEX erhält bei seiner Änderung `409`.
4. UI zeigt aktuellen Stand und bewahrt Alex’ Eingabe separat.
5. Kein automatisches Überschreiben.

### E2E-08 Cross-Tenant und Revocation

1. MIRA versucht bekannte Alpha-IDs und Cursor.
2. Alle Zugriffe bleiben neutral und mutieren nichts.
3. REVOKED versucht alten Token, Read URL und Cache.
4. API verweigert; URL-Restfenster entspricht dokumentierter TTL; lokaler Cache ist gesperrt/gelöscht.

## 6. Visuelle QA-Varianten

Jeder Kernscreen wird aufgenommen mit:

- Compact 360 px, Medium 720 px, Expanded 1440 px,
- Standard- und 200-%-Webzoom beziehungsweise größte Android-Schrift,
- hell/dunkel, sofern Dark Theme implementiert ist,
- leer, normal, lange Inhalte, fehlendes Medium, Teilfehler,
- Tastaturfokus beziehungsweise TalkBack-Fokus sichtbar,
- Online, Offline Read, Offline Write blockiert,
- privacy-sicherem 404.

## 7. Accessibility-Durchlauf

- Story vollständig per Tastatur/TalkBack lesen und öffnen.
- Filter setzen und entfernen, ohne visuelle Orientierung vorauszusetzen.
- Privacy-Gruppe verstehen und auswählen.
- Medien hinzufügen, Fehler erkennen, entfernen und Reihenfolge ohne Drag ändern.
- Kommentar senden und Status hören.
- 409 lösen, ohne eigene Eingabe zu verlieren.
- Zurückpfad stellt Kontext und Fokus wieder her.

## 8. Analytics-Erwartung

Erlaubte Beispiele:

```text
story_opened
story_filter_applied { type_class }
memory_create_started|completed|failed { failure_class? }
attachment_upload_failed { failure_class }
heart_moment_create_started|completed|failed
milestone_create_completed
comment_send_completed|failed
```

Fixture- und Canary-Werte dürfen in keinem Analytics-Payload erscheinen.

## 9. Definition „Demo bestanden“

Die Demo gilt nur als bestanden, wenn fachlicher Erfolg, Fehlerrückweg, Privacy, Offline-Verhalten, Accessibility und Cross-Tenant-Isolation sichtbar nachgewiesen sind. Ein reiner Happy-Path-Screenshot reicht nicht.
