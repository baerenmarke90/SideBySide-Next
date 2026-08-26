# Web

Hier entsteht ab Milestone M5 der React-/TypeScript-Client. M0 versioniert
nur diese Grenze: Noch keine UI-Abhängigkeiten, kein Build und keine
vorgezogenen Produktfunktionen.

Der Client nutzt ausschließlich die versionierte REST-/OpenAPI-Schnittstelle
des Backends; Fach- und Autorisierungsregeln bleiben im Application Core.

## Generierte API-Schicht

`src/api/generated/` entsteht aus `backend/openapi.json` und wird **nicht von
Hand bearbeitet**. Erzeugen mit `tools/openapi/generate.sh`; CI prüft, dass
der eingecheckte Stand zum Vertrag passt.

Der Ordner enthält ausschließlich DTOs und Endpunktaufrufe. UI, State und
Fachlogik gehören daneben, nicht hinein.
