# Web

Der Web-Client ist langfristig Teil von M5. Für **M2-S8 / G2** existiert hier
bewusst vorher nur ein dünner vertikaler Referenzflow. Er beweist den echten
Memory-/Bild-/Story-Vertrag auf Web, ohne vollständige Navigation, Offline-
Cache oder Client-Parität vorwegzunehmen.

Der Client nutzt ausschließlich die versionierte REST-/OpenAPI-Schnittstelle
des Backends; Fach-, Privacy- und Autorisierungsregeln bleiben im Application
Core.

## Generierte API-Schicht

`src/api/generated/` entsteht aus `backend/openapi.json` und wird **nicht von
Hand bearbeitet**. Erzeugen mit `tools/openapi/generate.sh`; CI prüft, dass der
eingecheckte Stand zum Vertrag passt.

Der Ordner enthält ausschließlich DTOs und Endpunktaufrufe. UI, State und
Flow-Orchestrierung liegen daneben.

## M2-S8 Referenzflow

Der S8-Web-Slice verwendet React, TypeScript, Vite, React Router und TanStack
Query gemäß Master Spec. Er führt genau einen kritischen Flow aus:

1. Anmeldung über den veröffentlichten Auth-Vertrag,
2. Memory über `MemoriesApi`,
3. Bild-Upload über `AttachmentsApi` und den gelieferten `UploadDescriptor`,
4. Finalize + READY-Prüfung + Bindung an die Memory,
5. `/timeline` über `StoryApi`,
6. Verarbeitung der generierten `StoryItem`-Union über `kind`,
7. autorisierter Bildabruf und minimale Darstellung.

### Konfiguration

Technische Werte sind Betreiberkonfiguration und werden normalen Nutzern nicht
als Eingabefelder gezeigt:

- `VITE_SBS_API_BASE_URL` – API-Basis; ohne Wert wird Same-Origin verwendet.
- `VITE_SBS_SPACE_ID` – der Referenz-Space für diesen dünnen G2-Nachweis.

Access- und Refresh-Token bleiben ausschließlich im flüchtigen React-State.
Logout leert State und TanStack-Query-Cache; S8 führt keine persistente
Offline-/Read-Cache-Policy ein.

### Lokal am Quellcode

```bash
npm ci
npm audit --audit-level=high
npm run lint
npm test
npm run build
```

### Self-Hosted-PoC

Der Produktionsbuild liegt in einem unprivilegierten Nginx-Container. Im
lokalen Compose-Test liefert er die statischen Dateien auf
`http://127.0.0.1:${WEB_PORT:-8080}` aus und leitet `/api/` intern an den
API-Service weiter. Dadurch bleibt der Browser same-origin und es ist keine
pauschale CORS-Freigabe nötig.

Der Referenzflow benötigt noch eine bekannte Space-UUID:

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

Video, vollständige Navigation, Offline Write Sync, Room/Paging-Äquivalente,
Export/Import, Deep Links, globale Suche und M3+-Funktionen bleiben außerhalb
von S8.
