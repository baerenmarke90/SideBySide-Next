# M2 Technical Readiness Package

**Status:** Implementierungsvorbereitung, kein Ersatz für OpenAPI oder Master-Spezifikation  
**Version:** 1.0  
**Stand:** 24.08.2026

Dieses Paket bereitet **M2 – Memory Core** technisch vor, ohne in die laufenden Foundation-Issues #5–#11 einzugreifen. Es enthält ausschließlich neue Planungsdateien. Runtime-Code, Auth/Session, Transport, CI, Projektgerüste, OpenAPI und Profile bleiben unberührt.

## Ziel

Nach Abschluss der M0-/M1-Gates soll M2 ohne erneute Grundsatzarbeit in überprüfbaren vertikalen Slices umgesetzt werden können:

```text
Memory + Media + HeartMoment + Milestone + Comment
                         │
                         └── Story Read Model
```

## Inhalt

- [Domain Model](./DOMAIN-MODEL.md) – Entitäten, Invarianten, Privacy und Events
- [API Design](./API-DESIGN.md) – Operationen, DTOs, Fehler und Concurrency als OpenAPI-Vorlage
- [Media Pipeline](./MEDIA-PIPELINE.md) – Upload, Validierung, Storage und autorisierter Abruf
- [Security Test Matrix](./SECURITY-TEST-MATRIX.md) – Tenant-, Owner-only-, Media- und Leak-Tests
- [Delivery Plan](./DELIVERY-PLAN.md) – vertikale Slices und issue-fertige Arbeitspakete
- [Decision Log](./DECISION-LOG.md) – vor Codebeginn zu klärende M2-Entscheidungen
- [Grafische Architektur](./m2-architecture.svg) – menschenlesbarer Überblick

## Verbindliche Quellen

1. [Clean-Room Master Specification](../../specification/CLEAN-ROOM-MASTER-SPEC.md), insbesondere Abschnitte 14–21.
2. [Produktspezifikation](../../specification/PRODUCT-SPEC.md).
3. [Security-Invarianten](../SECURITY.md).
4. [Architektur](../ARCHITECTURE.md).
5. Der zu M2-Zeitpunkt versionierte OpenAPI-Vertrag.

Bei Widersprüchen gilt die höherstehende Quelle. Dieses Paket darf keine fachliche Lücke stillschweigend entscheiden.

## Scope M2

| Domain | M2-Inhalt |
|---|---|
| Memory | CRUD, Autor, fachliches Datum, mehrere Medien, Kommentare, Story |
| HeartMoment | Text, Emotion, `SHARED`/`PRIVATE`, optionales Attachment, Story nur wenn geteilt |
| Milestone | eigenes Modell, CRUD, Story, später Chapter/Recap |
| Attachment | MediaStore-Abstraktion, Upload-Lifecycle, Validierung, sichere Lese-URL/Route |
| Comment | kontrollierte Targets, nur geteilte Inhalte, Notification-Event |
| Story | abgeleitetes Read Model, Filter, Suche, Sortierung, Cursor-Pagination |

## Nicht in M2

- echte Ende-zu-Ende-Verschlüsselung,
- Offline Write Sync,
- Chapter-/Place-Implementierung,
- Jahresrückblick,
- öffentliche Share Links,
- KI-Bildanalyse oder automatische Inhaltsanalyse,
- Shopping, Discovery, Location und weitere Providerintegrationen,
- frei polymorphe Kommentare auf beliebige Tabellen.

## Startbedingungen

M2-Implementierung beginnt erst, wenn:

- die offenen Foundation-/M1-Sicherheitsgates geschlossen sind,
- Owner-only-Autorisierung serverseitig vorhanden ist,
- der OpenAPI-Vertrag versioniert und contract-testbar ist,
- ProtectedPayload-Grenzen bei sensiblen Modellen technisch erzwungen werden können,
- Web-/Android-Grundgerüste für die geplanten Client-Slices vorhanden sind,
- Entscheidungen mit Priorität `BLOCKING` im Decision Log geklärt sind.

## Definition of Ready

- [ ] jedes Modell besitzt bestätigte Felder, Privacy-Klasse und Schreibrechte,
- [ ] jede Operation besitzt Request, Response, Fehlercodes und Concurrency-Regel,
- [ ] Story-Filterung schließt private Inhalte serverseitig aus,
- [ ] Media-Limits und Allowlist sind entschieden,
- [ ] Attachment-Lifecycle und Orphan-Cleanup sind spezifiziert,
- [ ] Domain Events enthalten keine unnötigen Klartext-Payloads,
- [ ] Tenant-/Owner-only-/Media-Testmatrix ist akzeptiert,
- [ ] Delivery-Slices besitzen eindeutige Abhängigkeiten,
- [ ] keine M2-Aussage verspricht vorhandene E2EE.

## Arbeitsregel

Ein Slice gilt erst als fertig, wenn Domainmodell, Migration, Service, Autorisierung, API/OpenAPI, Fehlercodes, Unit-/Integration-/Cross-Tenant-Tests, Privacy-Tests, Exportwirkung, Clientverhalten und Dokumentation gemeinsam erfüllt sind. Ein einzelner funktionierender Endpoint oder Screen reicht nicht.
