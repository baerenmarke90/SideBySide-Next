# Web

Der vollstaendige React-/TypeScript-Client wird in M5 fertiggestellt. M2-S8
enthaelt bewusst nur einen duennen vertikalen Referenzflow fuer den G2-Nachweis:
authentifizierter Zugriff -> Memory -> Bild-Attachment -> `/timeline` ->
minimal dargestellte Story.

Der Client nutzt ausschliesslich die versionierte REST-/OpenAPI-Schnittstelle
des Backends; Fach-, Privacy- und Autorisierungsregeln bleiben im Application
Core. Es gibt insbesondere keine clientseitige private Story-Variante.

## Generierte API-Schicht

`src/api/generated/` entsteht aus `backend/openapi.json` und wird **nicht von
Hand bearbeitet**. Erzeugen mit `tools/openapi/generate.sh`; CI prueft, dass
der eingecheckte Stand zum Vertrag passt.

Der Ordner enthaelt DTOs und Endpunktaufrufe. UI, State und die kleine
S8-Orchestrierung liegen daneben. Es werden keine konkurrierenden API-DTOs
angelegt.

## S8 lokal ausfuehren

Voraussetzung ist eine laufende SideBySide-API auf `127.0.0.1:8000` sowie ein
vorhandener Paar-Space. Technische Instanzwerte werden vom Betreiber gesetzt,
nicht vom Paar in der UI:

```bash
cd web
cp .env.example .env
# VITE_SBS_SPACE_ID in .env setzen
npm install
npm run dev
```

Im Entwicklungsmodus leitet Vite `/api` an die lokale API weiter. Fuer einen
Same-Origin-Betrieb bleibt `VITE_SBS_API_BASE_URL` leer; bei anderer
Deployment-Topologie kann der Betreiber eine API-Basis setzen.

Der Referenzflow speichert Access-/Refresh-Tokens nicht persistent. Abmelden
leert Query- und Session-State. Ein persistenter Read-/Offline-Cache wird hier
bewusst nicht eingefuehrt, damit M2-D18 nicht stillschweigend entschieden wird.

Video wird nicht angeboten; #88 bleibt ausserhalb von M2/G2.
