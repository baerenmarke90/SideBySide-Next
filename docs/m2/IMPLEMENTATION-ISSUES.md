# M2 Client & QA Implementation Issues

**Status:** Vorlagen, noch keine angelegten GitHub-Issues  
**Stand:** 24.08.2026

Diese Pakete ergänzen den [M2 Delivery Plan](./DELIVERY-PLAN.md). Sie starten erst, wenn das jeweilige Backend-/OpenAPI-Inkrement stabil ist. Ein Issue entspricht einem Branch und einem Pull Request.

## Gemeinsame PR-Grenzen

- keine Änderung an Auth-/Tenant-Grundlagen im Feature-PR,
- keine clientseitige Erfindung fehlender API-Felder,
- keine parallelen Web-/Android-Begriffe oder Privacy-Regeln,
- kein Content in Analytics, Logs oder Push Preview,
- Pflichtzustände und Demo-Fixtures im selben PR wie der Screen,
- visuelle, Accessibility- und Privacy-Nachweise vor Merge.

## C1 – Gemeinsame M2 Client Contracts

**Titel:** `[M2][Clients] Gemeinsame Route-, DTO- und Fehlerverträge integrieren`

**Abhängigkeiten:** veröffentlichter M2-OpenAPI-Vertrag, M2-Domainentscheidungen.  
**Scope:** Route-IDs, typisierte DTOs, Error Mapping, Query Keys, Privacy-/Space-gebundene Cache Keys, Test Doubles.

**Akzeptanz**

- Web und Android erzeugen/verwenden denselben Vertrag.
- 401, 404, 409, 429 und 5xx werden semantisch unterschieden.
- Cache Keys enthalten Owner-/Space-Kontext, keine Contentwerte.
- PRIVATE ist kein rein visueller Filter.
- Contract- und Fixture-Tests laufen reproduzierbar.

**Nicht enthalten:** fertige Screens, eigenes Backendmodell.

## C2 – Story Timeline & Search Web

**Titel:** `[M2][Web] Story Timeline, Suche und Detail-Pane liefern`

**Abhängigkeiten:** Story Query API, C1.  
**Scope:** Compact/Medium/Expanded, Monatsgruppen, Filter, Cursor, Suche, Detail-Pane, Back/Deep Link.

**Akzeptanz**

- Memory, Milestone und Shared HeartMoment erscheinen; PRIVATE niemals.
- Filter/Scroll/Auswahl werden bei Rückkehr wiederhergestellt.
- Cursor-Retry erzeugt keine Duplikate.
- Tastatur, 200 % Zoom und privacy-sicheres 404 bestehen.
- Web-Performancebudgets sind gemessen.

## C3 – Story Timeline Android

**Titel:** `[M2][Android] Story Timeline, Suche und Detailnavigation liefern`

**Abhängigkeiten:** Story Query API, C1.  
**Scope:** Navigation Destination, Monatsgruppen, Filter Sheet, Cursor, Deep Link, Offline Read Cache.

**Akzeptanz**

- TalkBack/Switch Access/Zurückpfad vollständig.
- größte Schrift schneidet keine Pflichttexte ab.
- Cache ist Owner-/Space-gebunden und nach Logout/Wechsel gesperrt.
- PRIVATE Canary fehlt in UI, Cache und Netzwerkprojektion.
- Start-/Scroll-Performancebudgets sind gemessen.

## C4 – Memory Creator & Media Queue Web

**Titel:** `[M2][Web] Memory-Formular mit sicherer Medienwarteschlange liefern`

**Abhängigkeiten:** Memory CRUD, Attachment Lifecycle, C1.  
**Scope:** Create/Edit, `happenedOn`, mehrere Medien, Reihenfolge, Status, Retry/Remove, Shared-Hinweis.

**Akzeptanz**

- alle Media-Status sichtbar und pro Datei behandelbar,
- ungültige Datei zerstört weder Text noch gültige Medien,
- Reorder ohne Drag möglich,
- Offline Write bleibt ungespeichert,
- Doppelabsenden erzeugt kein Duplikat,
- 409 bewahrt eigene Eingabe.

## C5 – Memory Creator & Media Queue Android

**Titel:** `[M2][Android] Memory-Formular mit Photo Picker und Medienstatus liefern`

**Abhängigkeiten:** Memory CRUD, Attachment Lifecycle, C1.  
**Scope:** System Photo Picker, Form, Medienkacheln, Retry/Remove/Reorder, Prozess-/Netzstatus.

**Akzeptanz**

- keine Berechtigung beim App-Start,
- TalkBack nennt Datei, Status und Aktion,
- keine Read URL oder private Datei in Share Sheet/Clipboard/Backup,
- WorkManager erzeugt keinen Offline Write Sync,
- Entwurf bleibt im sicheren aktuellen Kontext erhalten.

## C6 – HeartMoment Privacy Flow Web & Android

**Titel:** `[M2][Privacy] HeartMoment Owner-only und Shared UX auf beiden Clients liefern`

**Abhängigkeiten:** HeartMoment API/Policy, Attachment Parent Auth, `M2-D06`, `M2-D07`.  
**Scope:** Pflichtauswahl, Erst-Share-Erklärung, Owner-Bereich, Shared Detail, Visibility-Wechsel, Cache-/Deep-Link-Regeln.

**Akzeptanz**

- keine vorausgewählte Sichtbarkeit ohne dokumentierte Entscheidung,
- PRIVATE hat keine Kommentar-/Story-/Partneraktion,
- Partner-Deep-Link und alle indirekten Pfade sind neutral,
- Wechsel benötigt Online + aktuelle Version,
- Canary fehlt in Story, Suche, Cache, Analytics, Log, Push und Export,
- Privacy-Gruppe ist mit Tastatur/TalkBack vollständig verständlich.

## C7 – Milestone Web & Android

**Titel:** `[M2][Clients] Eigenständigen Milestone-Flow integrieren`

**Abhängigkeiten:** Milestone CRUD, C1.  
**Scope:** Create/Edit/Detail, Story Card, Datum, Concurrency.

**Akzeptanz**

- Milestone ist kein Memory-Typflag im Client,
- eigener Story-Typ und verständliche Semantik,
- keine deaktivierten Chapter-/Recap-Zukunftscontrols,
- 404/409/Offline/Accessibility auf beiden Plattformen geprüft.

## C8 – Comments & Privacy-safe Notification UX

**Titel:** `[M2][Clients] Kommentare und sichere Notification-Vorschau integrieren`

**Abhängigkeiten:** Comment API, Outbox/Notification Hook, Preview-Entscheidung.  
**Scope:** List/Composer/Edit/Delete gemäß Contract, Sendestatus, Retry, Deep Link aus Notification.

**Akzeptanz**

- Composer nur auf erlaubten Shared Targets,
- Sendestatus erzeugt genau einen Kommentar,
- Parent-404 bleibt neutral,
- Push Preview enthält keinen Kommentar-/Titeltext ohne explizite Freigabe,
- Notification Deep Link autorisiert erneut,
- Screenreaderstatus und Fokus nach Senden korrekt.

## C9 – System States, Offline & Conflict

**Titel:** `[M2][Clients] M2-Systemzustände, Offline Read und 409-Konflikt vereinheitlichen`

**Abhängigkeiten:** C1 und mindestens ein integrierter M2-Flow.  
**Scope:** Skeleton, Empty, Partial, Offline Cache, Offline Write Block, 401/404/409/429/5xx, Entwurfserhalt.

**Akzeptanz**

- State Matrix für jeden M2-Screen als visuelle Tests vorhanden,
- kein Zustand leakt private Counts oder Existenz,
- Offline Write zeigt nie Erfolg,
- 409 hat keinen automatischen Last-write-wins,
- Fokus und Eingabe bleiben stabil.

## C10 – M2 Accessibility & Performance Gate

**Titel:** `[M2][QA] Accessibility- und Performancebudgets für Web und Android abnehmen`

**Abhängigkeiten:** C2–C9.  
**Scope:** Tastatur, TalkBack, Switch Access, große Schrift, Kontrast, Motion, Fokus, Referenzmessungen.

**Akzeptanz**

- alle Kernflows aus `DEMO-SCENARIO.md` durchlaufen,
- keine kritische WCAG-/TalkBack-Barriere offen,
- Touch-/Klickziele entsprechen Tokens,
- Performancebudgets dokumentiert; Abweichungen haben Owner und Entscheidung,
- Privacy-Autorisierung wird nicht zugunsten von Performance umgangen.

## C11 – M2 Privacy Abuse & Release Sign-off

**Titel:** `[M2][Security] Client-, Cache- und Notification-Leaks vor Release ausschließen`

**Abhängigkeiten:** Backend-Security-Suite, C2–C10.  
**Scope:** Canary-Suche in DOM/Cache/Logs/Events/Push/Export, Cross-Tenant, Revocation, Read URLs, Recents.

**Akzeptanz**

- alle `TM-01` bis `TM-18` relevanten Clientpfade bewertet,
- Private Canary nur im Owner-Kontext,
- Logout/Space-Wechsel löscht/sperrt Caches,
- Deep Links und Notifications autorisieren erneut,
- offene hohe/kritische Risiken blockieren Release,
- Ergebnis ist als Security-/Privacy-Abnahme dokumentiert.

## Empfohlene Reihenfolge

```text
C1
├── C2 ── C4 ──┐
├── C3 ── C5 ──┤
├── C6 ────────┤
├── C7 ────────┤── C9 ── C10 ── C11
└── C8 ────────┘
```

C2/C3 und C4/C5 können plattformweise parallel laufen, teilen aber Contract, Fixtures, Copy und Abnahmekriterien. C6 bleibt ein gemeinsames Privacy-Paket, damit sich Web und Android nicht semantisch auseinanderentwickeln.
