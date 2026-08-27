# Web

Der Web-Client ist langfristig Teil von M5. Für **M2-S8 / G2** wurde zuerst
ein dünner vertikaler Referenzflow geliefert, der den echten
Memory-/Bild-/Story-Vertrag Ende-zu-Ende beweist. Auf diesem validierten Pfad
liegt nun die erste produktnahe M2-Story-Oberfläche.

## Generierte API-Schicht

`src/api/generated/` entsteht aus `backend/openapi.json` und wird **nicht von
Hand bearbeitet**. Erzeugen mit `tools/openapi/generate.sh`; CI prüft, dass der
eingecheckte Stand zum Vertrag passt.

## Lokale Qualitätschecks

```bash
npm ci
npm audit --audit-level=high
npm run typecheck
npm run lint
npm run format:check
npm test
npm run build
```

Die Checks sind bewusst getrennt:

- `typecheck` prüft TypeScript-Typen;
- `lint` führt Biome-Lintregeln für handgeschriebenen Web-Code aus;
- `format:check` prüft die einheitliche Formatierung.

`npm run format` schreibt die Biome-Formatierung lokal. Der generierte
OpenAPI-Client unter `src/api/generated/` ist von Biome bewusst ausgeschlossen,
weil er aus dem Backend-Vertrag erzeugt wird.

## Aktueller M2-Web-Slice

Der Client nutzt React, TypeScript, Vite, React Router und TanStack Query gemäß
Master Spec und vorhandener Reuse-Regel.

Der Produktionsbuild liegt in einem unprivilegierten Nginx-Container.
Die vollständige Self-Hosting-Anleitung steht in `docs/SELF-HOSTING.md`.
