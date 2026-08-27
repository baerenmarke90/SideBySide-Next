# Web

Der Web-Client ist langfristig Teil von M5. Für **M2-S8 / G2** wurde zuerst
ein dünner vertikaler Referenzflow geliefert, der den echten
Memory-/Bild-/Story-Vertrag Ende-zu-Ende beweist. Auf diesem validierten Pfad
liegt nun die erste **produktnahe M2-Story-Oberfläche**: Anmeldung, gemeinsame
Story und das Erstellen einer Memory mit Bild verwenden bereits die
verbindlichen Design-Tokens und Screen-Verträge.

Das ist weiterhin **keine vollständige M5-Client-Parität**. Vollständige
Navigation, Detailscreens, Deep Links, Offline-Read-Cache, Export/Import und
M3+-Funktionen werden durch diesen Slice nicht vorgezogen.

Der Client nutzt ausschließlich die versionierte REST-/OpenAPI-Schnittstelle
des Backends; Fach-, Privacy- und Autorisierungsregeln bleiben im Application
Core.

## Generierte API-Schicht

`src/api/generated/` entsteht aus `backend/openapi.json` und wird **nicht von
Hand bearbeitet**. Erzeugen mit `tools/openapi/generate.sh`; CI prüft, dass der
eingecheckte Stand zum Vertrag passt.

Der Ordner enthält ausschließlich DTOs und Endpunktaufrufe. UI, State und
Flow-Orchestrierung liegen daneben.

## Aktueller M2-Web-Slice

Der Web-Slice verwendet React, TypeScript, Vite, React Router und TanStack
Query gemäß Master Spec und vorhandener Reuse-Regel. Es kommt keine neue
UI-Library hinzu.

Der kritische Flow bleibt unverändert:

1. Anmeldung über den veröffentlichten Auth-Vertrag,
2. Memory über `MemoriesApi`,
3. Bild-Upload über `AttachmentsApi` und den gelieferten `UploadDescriptor`,
4. Finalize + READY-Prüfung + Bindung an die Memory,
5. `/timeline` über `StoryApi`,
6. Verarbeitung der generierten `StoryItem`-Union über `kind`,
7. autorisierter Bildabruf als Teil des E2E-Nachweises.

Die produktnahe Oberfläche ergänzt darauf:

- eine nutzerorientierte Anmeldung ohne M2-/G2-Techniksprache,
- eine eigene Route `/story`,
- die Erstellen-Route `/memory/new`,
- monatsweise gruppierte Story-Karten für Memory, HeartMoment und Milestone,
- sichtbare gemeinsame Sichtbarkeit beim Erstellen einer Memory,
- Lade-, Leer-, Erfolgs- und Fehlerzustände,
- responsive Darstellung auf Compact, Medium und Expanded,
- Design-Tokens und 44-CSS-px-Zielgrößen aus dem Plattform-Handoff.

### Konfiguration

Technische Werte sind Betreiberkonfiguration und werden normalen Nutzern nicht
als Eingabefelder gezeigt:

- `VITE_SBS_API_BASE_URL` – API-Basis; ohne Wert wird Same-Origin verwendet.
- `VITE_SBS_SPACE_ID` – der Referenz-Space für den aktuellen M2-Web-Slice.

Access- und Refresh-Token bleiben ausschließlich im flüchtigen React-State.
Logout leert State und TanStack-Query-Cache; M2 führt keine persistente
Offline-/Read-Cache-Policy ein.

### Lokal am Quellcode

```bash
npm ci
npm audit --audit-level=high
npm run typecheck
npm run lint
npm run format:check
npm test
npm run build
```

`typecheck`, `lint` und `format:check` sind getrennte Gates. Biome lintet und
prüft die Formatierung des handgeschriebenen Web-Codes; der generierte
OpenAPI-Client unter `src/api/generated/` bleibt dabei ausgeschlossen.
`npm run format` schreibt die Biome-Formatierung lokal.

### Self-Hosted

Der Produktionsbuild liegt in einem unprivilegierten Nginx-Container. Im
lokalen Compose-Test liefert er die statischen Dateien auf
`http://127.0.0.1:${WEB_PORT:-8080}` aus und leitet `/api/` intern an den
API-Service weiter. Dadurch bleibt der Browser same-origin und es ist keine
pauschale CORS-Freigabe nötig.

Der aktuelle M2-Web-Slice benötigt noch eine bekannte Space-UUID:

```dotenv
SBS_WEB_SPACE_ID=00000000-0000-0000-0000-000000000000
```

Da Vite diesen Betreiberwert beim Build einbettet, ist nach einer Änderung
`docker compose up -d --build web` erforderlich. Die UUID ist kein Secret;
Access- und Refresh-Token bleiben weiterhin ausschließlich im flüchtigen
Browser-State.

Im öffentlichen Betrieb darf `/api/` nicht durch den Web-Container
geschleift werden. Der TLS-Reverse-Proxy routet `/api/` direkt zum
API-Host-Port und alle übrigen Pfade zum Web-Host-Port. Die vollständige
Anleitung steht in `docs/SELF-HOSTING.md`.

## Bewusste M2-Grenze

Die globale Produktnavigation `Heute · Story · Planen · Entdecken · Mehr` wird
nicht als Sammlung toter Links vorgetäuscht. Dieser Slice produktisiert zuerst
die tatsächlich implementierte Story-Fläche. Die vollständige Navigation und
systematische Feature-Parität bleiben M5.

Video, Offline Write Sync, Export/Import, globale Suche und M3+-Funktionen
bleiben ebenfalls außerhalb dieses Slices.
