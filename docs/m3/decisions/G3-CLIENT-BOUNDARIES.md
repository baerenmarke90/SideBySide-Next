# M3 G3-, Client-, Export- und Cache-Grenzen

**Status:** `DECIDED` – wirksam mit Merge dieses Decision-PRs  
**Datum:** 26.08.2026  
**Tracking:** #165  
**Betrifft:** M3-D21, D22, D24, D25, D27, D29

Dieses Dokument legt frueh fest, welche Evidenz G3 braucht und was bewusst erst M5/G4 implementiert wird. Es enthaelt keinen Runtime- oder Client-Code und aendert die bestehende M3-Startbedingung nicht.

## 1. Verbindliche Quellen

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/ROADMAP.md`
- `docs/SECURITY.md`
- `docs/m3/README.md`
- `docs/m3/DELIVERY-PLAN.md`

Roadmap-Grenze:

- G3 prueft konsistente Wishes/Plans/Places/Chapters/Collections, vollstaendige Private-Area-Isolation und verstaendliche Delete-/409-Wirkungen.
- M5/G4 liefern vollstaendige Web-/Android-Produktisierung, Paritaet, Read Cache, Export/Import, Accessibility und Performance.

Daraus folgt: M3 muss echte Runtime-/API-/PostgreSQL-Evidenz liefern, aber keine vorgezogene vollstaendige Client-Paritaet.

## 2. M3-D24 – G3 Evidence

### Entscheidung

G3 ist ein **Domain/API/PostgreSQL-Gate**. Fuer G3 sind keine duennen Web-/Android-Referenzflows zusaetzlich verpflichtend. Client-Paritaet und systematische Accessibility bleiben M5/G4.

G3 benoetigt jedoch reale HTTP-E2E-Flows gegen den produktionsnahen FastAPI/PostgreSQL-Stack, nicht nur Unit-Tests oder Mock-Repository-Tests.

### Verbindliche G3-E2E-Flows

Mindestens diese fuenf Flows muessen auf dem finalen G3-Commit nachweisbar gruen sein:

1. **Wish -> Plan -> Complete**
   - Wish OPEN anlegen;
   - atomar zu Plan konvertieren;
   - Plan terminieren oder spontan abschliessen;
   - source Wish und Plan konsistent COMPLETED;
   - Retry/Race/Versionkonflikt mit abdecken.

2. **Place + Relation**
   - Place ohne und mit Koordinaten;
   - mindestens eine typisierte Place-Relation auf bestehenden Shared Content;
   - Cross-Space/private Target Negativpfad;
   - Place-Delete behaelt fachliche Originale.

3. **Chapter + Relation + Delete**
   - Chapter anlegen;
   - Memory/SHARED HeartMoment/Milestone verbinden;
   - deterministische abgeleitete Reihenfolge pruefen;
   - Chapter loeschen;
   - Originalinhalte bleiben lesbar.

4. **Shared Collection**
   - Collection + mehrere Items;
   - Completion;
   - atomarer Reorder;
   - stale/concurrent Reorder -> deterministischer 409;
   - Delete-Cascade nur auf Items.

5. **Private Area Owner/Partner Negativpfad**
   - Owner erstellt PrivateNote, GiftIdea und PrivateCollection mit Item;
   - Owner kann lesen/aendern;
   - Partner sieht weder GET noch LIST/Count/Item;
   - Partner-Mutation liefert privacy-sichere Nicht-Existenzsemantik;
   - Logout/Sessionwechsel erzeugt keinen serverseitigen Leak.

### Pflicht-Negativtests

G3 blockiert bei Fehlern in:

- Cross-Tenant Isolation;
- OWNER_ONLY Isolation;
- Relation zu private/non-readable Targets;
- Wish->Plan Double-Submit/halben Transaktionen;
- Relation-/Privacy-Races;
- Collection-Reorder-Konsistenz;
- Delete-Cascades auf fachliche Originale;
- Event-/Log-Leaks geschuetzter Inhalte.

### Gate-blockierende Findings

G3 kann nicht bestanden werden, wenn offen ist:

- `Critical` oder `High` Security-/Privacy-/Tenant Finding;
- **irgendein tatsaechlicher Tenant- oder OWNER_ONLY-Leak**, unabhaengig von einer sonst vergebenen Severity;
- Datenverlust/Cascade eines fachlichen Originals ausserhalb der dokumentierten Parent-Child-Semantik;
- reproduzierbarer Race, der einen ungueltigen Domainzustand erzeugt;
- fehlende reale PostgreSQL-/HTTP-Evidenz fuer einen der fuenf Pflichtflows.

Medium/Low Findings ohne Tenant-/Privacy-Leak duerfen nur mit eigenem Follow-up-Issue und ausdruecklicher Risikoannahme im G3-Review offen bleiben.

### Nachweisformat

Der finale G3-Review ist ein **neues datiertes Dokument** unter:

```text
docs/reviews/YYYY-MM-DD-g3-gate-review.md
```

Es nennt mindestens:

- finalen `main`-Commit SHA;
- relevante PRs/Issues;
- Workflow-Run-IDs;
- OpenAPI-/Backend-/PostgreSQL-Teststatus;
- die fuenf E2E-Flows mit Ergebnis;
- offene Findings mit Severity;
- explizit `G3: BESTANDEN` oder `G3: NICHT BESTANDEN`.

Historische Gate-Reviews werden nicht umgeschrieben.

## 3. G3 vs. M5/G4

### In G3 verpflichtend

- Domainmodell/Migration/API fuer M3;
- Tenant-/Owner-Autorisierung;
- Optimistic Concurrency/Races;
- reale HTTP/PostgreSQL-E2E-Evidenz;
- Privacy-/Security-Negativtests;
- OpenAPI aktuell;
- dokumentierte Delete-/409-Semantik.

### Erst M5/G4 verpflichtend

- vollstaendige Web-UI aller M3-Funktionen;
- vollstaendige Android-UI aller M3-Funktionen;
- systematische Web-/Android-Paritaet;
- Offline Read Cache;
- Export/Import-Implementierung;
- Deep Links;
- umfassende Accessibility-Abnahme;
- Client-Performance-Gate.

M3 darf spaeter kleine technische Referenzflaechen bauen, wenn sie fuer Entwicklung hilfreich sind; sie sind aber **keine G3-Pflicht** und duerfen M5 nicht als fertig darstellen.

## 4. M3-D21 – Export-Grenze

### Entscheidung

M3 implementiert **keinen Export**. Die folgende Privacy-Semantik ist jedoch fuer M5 bereits bindend.

Es gibt konzeptionell zwei Exportkontexte:

### Gemeinsamer Space-Export

Enthaelt:

- `SPACE_SHARED`-Daten des Spaces;
- gemeinsam autorisierte Attachments/Relations gemaess Exportvertrag.

Enthaelt **nie**:

- PrivateNote;
- GiftIdea;
- PrivateCollection/Items;
- private HeartMoments des Partners;
- private Counts/Manifest-Eintraege, die deren Existenz verraten.

### Persoenlicher Export

Ein authentifizierter Account darf im persoenlichen Export zusaetzlich **seine eigenen** `OWNER_ONLY`-Daten erhalten.

- eigene PrivateNote/GiftIdea/PrivateCollection duerfen enthalten sein;
- private Daten des Partners sind ausgeschlossen;
- Owner-Zuordnung muss im neutralen Transferformat erhalten bleiben;
- Manifest/Checksums duerfen fuer den Partner nicht indirekt private Ressourcen des anderen beweisen.

Die technische Bundle-/Import-Implementierung bleibt M5.

## 5. M3-D22 – Client Cache

### Entscheidung

M3 fuehrt fuer die Private Area **keinen persistenten Offline-/Read-Cache** ein. Bis M5 bleiben private Daten in technischen Referenzclients nur im Prozess-/Memory-State, soweit ein Client ueberhaupt vorhanden ist.

Fuer M5 ist folgende Namespace-Grenze verbindlich:

```text
accountId + spaceId + privacyContext
```

Fuer `OWNER_ONLY` mindestens:

```text
accountId + spaceId + ownerId
```

### Clear-/Isolation-Regeln

Private Cache-Daten muessen bei mindestens folgenden Ereignissen aus dem aktiven Clientkontext entfernt werden:

- Logout;
- Session-Revoke / erneute Authentifizierung;
- Accountwechsel;
- Space-Wechsel;
- Owner-Kontextwechsel;
- lokale Datenloeschung/Reset.

### Web

Bis zum expliziten M5-Cache-Design:

- keine Private-Area-Payloads in `localStorage`;
- keine unkontrollierte Persistenz in IndexedDB;
- keine Tokens/signed URLs als persistenter Cache-Key;
- Query-Caches muessen Account/Space/Owner sauber namespacen und bei Logout entfernt werden.

### Android

Persistenter Room-Read-Cache fuer Private Area ist M5-Scope. Vorher keine ad-hoc SharedPreferences-/Datei-Persistenz von Private Payloads.

Die endgueltige Verschluesselungs-/Retention-Strategie ist Teil des M5 Security-/Cache-Reviews.

## 6. M3-D25 – Private Area Information Architecture

### Entscheidung

Die Private Area ist ein **sekundaerer persoenlicher Bereich**, keine gemeinsame Hauptnavigation.

Kanonische Client-Idee fuer M5:

```text
Mehr / Mein Bereich
  -> Private Notizen
  -> Geschenkideen
  -> Private Listen
```

Routen koennen intern unter einem klaren persoenlichen Namespace liegen, z. B.:

```text
/private/notes
/private/gift-ideas
/private/collections
```

Regeln:

- die UI bezeichnet diesen Bereich als persoenlich/nur fuer den aktuellen Nutzer;
- gemeinsame Space-Flachen zeigen keine privaten Counts/Badges;
- ein Deep Link auf private Resource autorisiert serverseitig erneut;
- Ausblenden im Client ist niemals die Security-Grenze;
- ein Partner darf aus Navigation, Badges oder Fehlern nicht erkennen, wie viele private Ressourcen existieren.

Die genaue visuelle Navigation/Label-Politur bleibt M5, die Sicherheits- und IA-Grenze ist hiermit entschieden.

## 7. M3-D27 – Plan Richness

### Entscheidung

**Checklist, Plan-Medien und weitere strukturierte Plan-Notizen werden nicht in M3 vorgezogen.**

M3-Plan bleibt beim source-bound Kern:

```text
title
description?
status
plannedStart?
plannedEnd?
experiencedOn?
placeId?
```

Damit gilt:

- keine versteckte Checklist als `Collection`;
- keine `PlanChecklistItem`-Tabelle in M3;
- keine Plan-Attachment-Relation in M3;
- `description` ist der einzige allgemeine Freitext im Plan-Kern;
- eine spaetere Richness-Erweiterung braucht eigenen Scope, Datenmodell, API-, Privacy-, Media- und Reuse-Review.

M3-D27 ist damit als **bewusst spaeter** entschieden und blockiert keinen M3-Runtime-Slice.

## 8. M3-D29 – Collection Multi-select

### Entscheidung

„Mehrfachauswahl“ ist in M3 **reiner Client-Interaktionszustand**, keine persistierte Domainsemantik.

- keine `selected`-Spalte;
- keine Selection-Tabelle;
- Selection verschwindet beim Verlassen/Reload nach Clientkonvention;
- Batch-Aktionen duerfen spaeter mehrere normale Domainoperationen oder einen expliziten Batch-Endpunkt verwenden;
- der Server speichert nur fachliche Endzustaende wie `completed`, nicht UI-Selektion.

Damit entsteht kein zusaetzlicher Sync-/Privacy-Zustand nur fuer eine UI-Interaktion.

## 9. G3-Vorbereitung fuer M4

G3 verlangt nur, dass M4-Read-Model-Grenzen **vorbereitet** sind:

- M3-Events transportieren keine ProtectedPayloads;
- OWNER_ONLY Events koennen nicht versehentlich in Shared Activity/Dashboard gelangen;
- globale Volltextsuche bleibt M4-A;
- M3 baut keinen privaten Suchindex als Vorgriff;
- IDs/Status/Privacy-Klassen reichen fuer spaetere kontrollierte Read Models, soweit fachlich benoetigt.

## 10. Reuse-before-build

Fuer diese reine Gate-/Clientgrenzen-Entscheidung nicht relevant. Spaetere Export-, Cache-, Deep-Link- oder Clienttechnik muss im jeweiligen Implementierungs-PR erneut auf vorhandene Libraries/Plattformmechanismen und Security-Eigenschaften geprueft werden.