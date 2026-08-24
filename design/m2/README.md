# M2 UX-to-Engineering Handoff

**Status:** Implementierungsvorbereitung  
**Version:** 1.0  
**Stand:** 24.08.2026

Dieses Paket konkretisiert die bestehende SideBySide-Designgrundlage für **M2 – Memory Core**. Es ersetzt weder Produkt-, API- noch Security-Spezifikation, sondern verbindet sie zu implementierbaren Screens, Zuständen und Plattformregeln.

## Zielbild

M2 fühlt sich auf Web und Android wie dasselbe Produkt an:

- gemeinsame Begriffe und gleiche fachliche Ergebnisse,
- plattformgerechte Navigation und Overlays,
- sichtbare Privacy vor, während und nach dem Speichern,
- ehrliche Medien-, Sync-, Offline- und Fehlerzustände,
- keine private Information in Story, Suche, Kommentar, Push oder Partnerexport,
- ein vollständiger Kernflow ohne Maus, Touch-Präzision oder visuelle Hinweise allein.

## Dateien

- [Screen Flows](./SCREEN-FLOWS.md) – Navigation, Aufgabenpfade und Übergänge
- [Screen State Matrix](./SCREEN-STATE-MATRIX.md) – Pflichtzustände, Texte und Aktionen
- [Platform Handoff](./PLATFORM-HANDOFF.md) – Web-/Android-Adaption, Accessibility und Performance
- [Grafischer Screenflow](./m2-screenflow.svg) – kompakter Überblick für Product, Design und Engineering
- [Privacy Threat Model](../../docs/m2/PRIVACY-THREAT-MODEL.md) – Datenflüsse, Bedrohungen und Kontrollen
- [Demo Scenario](../../docs/m2/DEMO-SCENARIO.md) – reproduzierbarer End-to-End-Datensatz
- [Implementation Issues](../../docs/m2/IMPLEMENTATION-ISSUES.md) – issue-fertige Client- und QA-Pakete

## Verbindliche Grundlagen

| Thema | Quelle |
|---|---|
| Navigation und Begriffe | [Information Architecture](../../docs/INFORMATION-ARCHITECTURE.md) |
| allgemeine Interaktionen | [UX Patterns](../../docs/UX-PATTERNS.md) |
| bestehende Aufgabenpfade | [User Flows](../../docs/USER-FLOWS.md) |
| Layouttypen | [Screen Templates](../../docs/SCREEN-TEMPLATES.md) |
| Komponenten | [Component Contracts](../../docs/COMPONENT-CONTRACTS.md) |
| Privacy-Kommunikation | [Content & Privacy Guidelines](../../docs/CONTENT-PRIVACY-GUIDELINES.md) |
| Accessibility-Abnahme | [Accessibility QA Matrix](../../docs/ACCESSIBILITY-QA-MATRIX.md) |
| Design Tokens | [tokens.json](../tokens.json) |
| M2-Domain/API/Media | [M2 Technical Readiness](../../docs/m2/README.md) |

Bei Widersprüchen gilt die verbindliche Produktspezifikation beziehungsweise der zu Implementierungsbeginn veröffentlichte OpenAPI-Vertrag. Offene fachliche Punkte werden im [M2 Decision Log](../../docs/m2/DECISION-LOG.md) entschieden und nicht im Client versteckt.

## Definition of Ready für einen M2-Screen

Ein Screen ist bereit zur Umsetzung, wenn:

1. Einstieg, Erfolg und Rückweg feststehen.
2. erlaubte Rollen und Privacy-Klasse benannt sind.
3. Datenquelle und relevante API-Operation feststehen.
4. Loading, Empty, Offline, 401, 404, 409, 429 und 5xx bewertet sind.
5. Fokus-/TalkBack-Reihenfolge und große Schrift beschrieben sind.
6. Analytics keine Inhalte, Suchtexte, Dateinamen oder privaten Merkmale enthalten.
7. Web und Android denselben fachlichen Vertrag verwenden.

## Bewusste Grenzen

- Keine echte E2EE im MVP; nur E2EE-ready Daten- und Mediengrenzen.
- Offline Read ist erlaubt, Offline Write bleibt bewusst deaktiviert.
- Private HeartMoments sind ein eigener Owner-only-Pfad, kein Filter in der gemeinsamen Story.
- Chapter, Place, Recap, öffentliche Links und temporäre Freigaben sind nicht Teil dieses Pakets.
- Dieses Paket legt keine noch offenen Domainentscheidungen stillschweigend fest.
