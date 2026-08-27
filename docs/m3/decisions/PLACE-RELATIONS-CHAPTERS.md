# M3 Place-, Relations- und Chapter-Semantik

**Status:** `DECIDED` – wirksam mit Merge dieses Decision-PRs  
**Datum:** 26.08.2026  
**Tracking:** #163  
**Betrifft:** M3-D06, D07, D08, D09, D10, D11, D12, D26, D28, D31

Dieses Dokument schliesst die blockierenden M3-Entscheidungen fuer Places, typisierte Content Relations und Chapters. Es enthaelt ausschliesslich Domain-, Persistenz-, API-, Privacy-, Concurrency- und Testentscheidungen. Es gibt **keinen M3-Runtime-Code frei**; die bestehende G2-/Status-Sync-Gate-Regel bleibt unveraendert.

## 1. Verbindliche Quellen

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/SECURITY.md`
- `docs/ROADMAP.md`
- `docs/m3/README.md`
- `docs/m3/DOMAIN-MODEL.md`
- `docs/m3/API-DESIGN.md`
- `docs/m3/SECURITY-TEST-MATRIX.md`
- M3-D01 aus #162: collaborative write fuer gemeinsame M3-Planungsressourcen

Source-bound bleiben insbesondere:

- Place ist `SPACE_SHARED` und darf ohne Koordinaten existieren.
- Place kann mit Memories, HeartMoments, Milestones, Plans und Chapters verbunden werden.
- Relationen muessen echte referentielle Integritaet besitzen; keine unkontrollierte `(targetType,targetId)`-Universalrelation.
- Chapter buendelt Memories, geteilte HeartMoments und Milestones.
- Chapter-Delete entfernt Relationen, niemals Originalinhalte.
- `OWNER_ONLY` darf nicht indirekt ueber Relations, Counts, Fehler oder Sortierluecken leaken.
- genaue Ortsdaten duerfen nicht in Logs, Analytics, Events oder Metriklabels gelangen.

## 2. M3-D06 / D28 – Place Privacy, Feldklassifizierung und Location Leakage

### Entscheidung

Place bleibt ein **gemeinsames `SPACE_SHARED`-Objekt**. Beide aktiven Space-Mitglieder duerfen den fachlichen Inhalt lesen. Es gibt in M3 keine per-Place Sichtbarkeitsstufe.

Als **geschuetzter fachlicher Inhalt** gelten:

- `name`
- `description`
- `address`
- `latitude`
- `longitude`

Diese Felder gehoeren zur ProtectedPayload-/E2EE-Readiness-Grenze. In Version 1 duerfen `latitude`/`longitude` fuer saubere Validierung und spaetere Provider-/Map-Erweiterbarkeit als typisierte DB-Spalten vorliegen; ihre Klassifizierung bleibt trotzdem `sensitive protected content`. Die technische Spaltenform macht sie nicht zu Telemetrie- oder Eventdaten.

Technische Metadaten ausserhalb der ProtectedPayload-Grenze:

- `id`
- `spaceId`
- `createdBy`
- `createdAt`
- `updatedAt`
- `version`

### Koordinateninvarianten

- beide Koordinaten gesetzt oder beide `NULL`;
- Latitude: `-90 <= latitude <= 90`;
- Longitude: `-180 <= longitude <= 180`;
- Persistenzpraezision fuer M3: maximal 6 Nachkommastellen;
- kein automatisches Runden fuer API-Responses ausser auf diese Persistenzpraezision;
- ein Place ohne Koordinaten ist voll gueltig;
- Address darf ohne Koordinaten und Koordinaten duerfen ohne Address gespeichert werden.

### Ausgabe / Privacy

Ein aktiver Partner im selben Space erhaelt die gespeicherten exakten Place-Werte. Nichtmitglieder oder IDs aus anderen Spaces erhalten keine unterscheidbare Existenzinformation.

Verboten sind insbesondere:

- Koordinaten in Application Logs;
- Koordinaten/Adresse in Error Context;
- Koordinaten/Adresse in Domain Events;
- Koordinaten/Adresse in Analytics oder Metriklabels;
- automatische Geocoding-/Reverse-Geocoding-Aufrufe;
- serverseitige Provider-IDs oder Karten-Metadaten in M3.

Maps, Geocoding, aktuelle Position und Providerdaten bleiben M7/M8 bzw. spaeterem explizitem Provider-Scope vorbehalten.

## 3. M3-D07 – Place Identity und Deduplizierung

### Entscheidung

**Keine automatische oder implizite Deduplizierung.**

- jeder Create-Request erzeugt einen neuen Place;
- Name, Adresse und Koordinaten sind keine Unique Keys;
- gleiche oder nahezu gleiche Koordinaten werden nicht automatisch zusammengefuehrt;
- kein fuzzy matching im Write Path;
- eine spaetere explizite Merge-/Duplicate-UX ist eigener Scope.

Begruendung: Orte mit gleichem Namen oder gleicher Adresse koennen fachlich bewusst getrennt sein; automatische Zusammenfuehrung waere datenveraendernd und privacy-riskant.

## 4. M3-D08 / D31 – Kanonische Relationflaeche

### Entscheidung

M3 verwendet **typisierte Relationen und direkte FKs**, keine generische Relationstabelle.

### 4.1 Direkte Single-Place-FKs

Fuer Plans und Chapters gilt genau eine kanonische Wahrheit:

```text
Plan.placeId?    -> places.id
Chapter.placeId? -> places.id
```

Daher gibt es in M3 **keine** zusaetzlichen Tabellen `place_plans` oder `place_chapters`.

Semantik:

- ein Plan hat hoechstens einen primaeren Place;
- ein Chapter hat hoechstens einen primaeren Place;
- `placeId` ist nullable;
- Place-Delete setzt diese FKs auf `NULL` (`ON DELETE SET NULL` oder aequivalente transaktionale Semantik);
- Plan/Chapter bleiben nach Place-Delete bestehen.

Damit ist M3-D31 entschieden: `Chapter.placeId` ist kanonisch, `place_chapters` wird nicht parallel eingefuehrt.

### 4.2 Place-Relations zu bestehendem Content

M3 liefert folgende typisierten n:m-Relationen:

```text
place_memories
place_heart_moments
place_milestones
```

Je Tabelle mindestens:

```text
- place_id      FK places.id
- target_id     FK auf konkreten Zieltyp
- created_by
- created_at
UNIQUE(place_id, target_id)
```

- Place-Delete entfernt nur die Join-Zeilen;
- Target-Delete entfernt nur die betroffenen Join-Zeilen;
- Originalressourcen werden nie mitgeloescht.

Bei `place_heart_moments` sind ausschliesslich `SHARED` HeartMoments zulaessig.

### 4.3 Chapter-Relations

M3 liefert:

```text
chapter_memories
chapter_heart_moments
chapter_milestones
```

Je Tabelle mindestens:

```text
- chapter_id    FK chapters.id
- target_id     FK auf konkreten Zieltyp
- created_by
- created_at
UNIQUE(chapter_id, target_id)
```

Ein Ziel darf in mehreren Chapters vorkommen; es gibt **keinen** globalen Unique Constraint auf `target_id`.

### 4.4 Externe API

Die externe API ist **typisiert**, nicht polymorph.

Beispielhafte Form:

```text
PUT    /api/v1/spaces/{spaceId}/places/{placeId}/memories/{memoryId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/memories/{memoryId}

PUT    /api/v1/spaces/{spaceId}/places/{placeId}/heart-moments/{heartMomentId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/heart-moments/{heartMomentId}

PUT    /api/v1/spaces/{spaceId}/places/{placeId}/milestones/{milestoneId}
DELETE /api/v1/spaces/{spaceId}/places/{placeId}/milestones/{milestoneId}

PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/memories/{memoryId}

PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/heart-moments/{heartMomentId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/heart-moments/{heartMomentId}

PUT    /api/v1/spaces/{spaceId}/chapters/{chapterId}/milestones/{milestoneId}
DELETE /api/v1/spaces/{spaceId}/chapters/{chapterId}/milestones/{milestoneId}
```

Plan-/Chapter-Place wird ueber deren normales versioniertes Update bzw. die dafuer definierte Resource-Operation gesetzt; dafuer wird kein zusaetzlicher generischer Relation Service eingefuehrt.

## 5. M3-D09 – Relation Privacy

### Entscheidung

Eine gemeinsame Relation darf nur auf ein Target zeigen, das fuer beide gemeinsamen Space-Mitglieder als gemeinsamer Inhalt zulaessig ist.

Insbesondere:

- private HeartMoments duerfen nicht an Place oder Chapter gebunden werden;
- `OWNER_ONLY` Targets sind fuer Shared Relations generell verboten;
- unbekannte, fremde, cross-space oder nicht lesbare Targets werden beim Create identisch als privacy-sicher `404` behandelt;
- Listen/Counts enthalten private Targets nicht;
- ein Fehler darf nicht unterscheiden, ob ein Target existiert, privat ist oder in einem anderen Space liegt.

### Privacy-Wechsel HeartMoment

Beim Wechsel `SHARED -> PRIVATE` werden in **derselben DB-Transaktion** zuerst bzw. zusammen mit dem Sichtbarkeitswechsel alle Shared-Relationen entfernt:

```text
place_heart_moments
chapter_heart_moments
```

Der Commit darf keinen Zustand sichtbar machen, in dem ein privater HeartMoment noch ueber Shared Relations beweisbar ist.

Beim spaeteren Wechsel `PRIVATE -> SHARED` werden alte Relationen **nicht automatisch rekonstruiert**.

## 6. M3-D10 – Chapter Ordering

### Entscheidung

Chapter-Inhalte erhalten in M3 **keine manuell persistierte Reihenfolge**.

Die Darstellung wird deterministisch aus den verknuepften Originalressourcen abgeleitet:

1. fachliches Ereignisdatum (`happenedOn`) aufsteigend;
2. falls kein fachliches Datum vorhanden: `createdAt`;
3. stabiler Tie-Breaker: Resource-Type und UUID.

Folgen:

- keine `position`-Spalte in Chapter-Relationstabellen;
- kein Chapter-Reorder-Endpunkt in M3;
- Relationtabellen bleiben einfach und voll referentiell;
- eine spaetere kuratierte manuelle Reihenfolge ist eigener Decision-/Migration-Scope.

## 7. M3-D11 – Chapter Dates

### Entscheidung

`startOn` und `endOn` sind unabhaengig optional.

Gueltig:

- beide `NULL`;
- nur `startOn`;
- nur `endOn`;
- beide gesetzt, wenn `endOn >= startOn`.

Die Datumsgrenzen werden nicht automatisch aus verknuepften Inhalten berechnet und werden durch Relations-Aenderungen nicht stillschweigend angepasst.

## 8. M3-D12 – Chapter Delete

Source-bound und unveraendert:

```text
DELETE Chapter
  -> Chapter selbst loeschen
  -> chapter_memories / chapter_heart_moments / chapter_milestones entfernen
  -> Memory / HeartMoment / Milestone erhalten
  -> Place erhalten
```

Wenn das Chapter eine `placeId`-Referenz besitzt, wird lediglich das Chapter geloescht; der Place bleibt bestehen.

## 9. Place Delete

Place-Delete ist erlaubt und besitzt folgende Semantik:

| Beziehung | Folge |
|---|---|
| `place_memories` | Join-Zeilen loeschen |
| `place_heart_moments` | Join-Zeilen loeschen |
| `place_milestones` | Join-Zeilen loeschen |
| `Plan.placeId` | auf `NULL` setzen |
| `Chapter.placeId` | auf `NULL` setzen |
| Memory/HeartMoment/Milestone | Original bleibt bestehen |
| Plan/Chapter | Original bleibt bestehen |

Es gibt keine Place-Cascade auf fachliche Originalressourcen.

## 10. M3-D26 – Concurrency und Relation Races

### Grundregel

Kein Relation-Create arbeitet nach unsicherem `check-then-insert` ohne Locks/Constraints.

### Relation Create

Transaktionale Reihenfolge fuer Join-Relations:

```text
1. Membership pruefen
2. Parent space-scoped laden und FOR UPDATE sperren
3. Target space-scoped laden und FOR UPDATE sperren
4. Target-Privacy erneut pruefen
5. UNIQUE-/FK-gesicherten Join einfuegen
6. sichere Outbox-/Audit-Metadaten schreiben
7. Commit
```

Doppeltes `PUT` derselben Relation ist idempotent und darf denselben Endzustand liefern, ohne zweite Join-Zeile.

### Parent Delete vs. Relation Create

- wer den Parent-Lock zuerst erhaelt, gewinnt;
- Delete entfernt Parent + Join-Zeilen;
- ein wartender Create revalidiert nach dem Lock und liefert 404/Conflict ohne verwaiste Relation.

### Target Delete vs. Relation Create

- Target-Delete sperrt das Target;
- Relation Create sperrt Parent, danach Target;
- gewinnt Delete zuerst, sieht Create nach Revalidation kein Target mehr;
- gewinnt Create zuerst, wartet Delete bis Commit und entfernt danach Target + Join-Zeile gemaess FK-Semantik.

### HeartMoment SHARED -> PRIVATE vs. Relation Create

Privacy-Wechsel sperrt den HeartMoment und entfernt dessen Shared-Join-Zeilen in derselben Transaktion. Er sperrt dabei **keine Relation-Parents nachtraeglich**, damit keine umgekehrte Parent->Target-Lockreihenfolge entsteht.

Relation Create sperrt Parent -> Target. Nach Target-Lock wird `SHARED` erneut geprueft. Ergebnis ist immer entweder:

- Shared + Relation vorhanden, oder
- Private + Relation nicht vorhanden.

Ein Zustand `Private + Relation vorhanden` ist unzulaessig.

### Direct FK Updates

`Plan.placeId` und `Chapter.placeId` verwenden normale Resource-Version/`If-Match`-Semantik und same-space Place-Revalidation innerhalb derselben Transaktion.

## 11. Fehlercodes

Mindestens:

```text
PLACE_NOT_FOUND                    404
CHAPTER_NOT_FOUND                  404
MEMORY_NOT_FOUND                   404
HEART_MOMENT_NOT_FOUND             404
MILESTONE_NOT_FOUND                404
RELATION_TARGET_NOT_FOUND          404
RELATION_ALREADY_EXISTS            200/204 idempotent, kein Fehler erforderlich
RESOURCE_VERSION_CONFLICT          409
CHAPTER_DATE_RANGE_INVALID         422
PLACE_COORDINATE_PAIR_REQUIRED     422
PLACE_LATITUDE_INVALID             422
PLACE_LONGITUDE_INVALID            422
```

Es wird **kein** eigener Cross-Space-/Private-Target-Fehlercode eingefuehrt.

## 12. Verpflichtende Tests

### Place

- Place ohne Koordinaten ist gueltig;
- nur Latitude oder nur Longitude -> 422;
- Grenzwerte fuer Latitude/Longitude;
- keine automatische Deduplizierung;
- beide Partner duerfen gemaess M3-D01 schreiben;
- Cross-Tenant CRUD fail-closed;
- Place-Delete entfernt Relations, setzt Plan/Chapter FK auf NULL und behaelt Originale.

### Relations

Fuer jeden freigegebenen Relationstyp:

- Happy Path;
- idempotentes doppeltes PUT;
- same-space FK;
- Cross-Space Target -> 404;
- geloeschtes Target -> 404;
- Parent Delete vs. Create Race;
- Target Delete vs. Create Race;
- keine fachliche Original-Cascade.

Zusaetzlich HeartMoment:

- PRIVATE Target -> 404;
- SHARED -> PRIVATE entfernt Place-/Chapter-Relations atomar;
- Race Relation Create vs. Privacy-Wechsel laesst keinen Leakzustand zu;
- PRIVATE -> SHARED rekonstruiert keine alten Relations.

### Chapter

- Datumsvarianten: leer/start-only/end-only/beide;
- `endOn < startOn` -> 422;
- mehrere Chapters duerfen dasselbe Target referenzieren;
- abgeleitete Sortierung ist stabil;
- Chapter-Delete behaelt alle Originaltargets;
- `Chapter.placeId` ist einzige Chapter/Place-Wahrheit.

## 13. Reuse-before-build

Fuer diese reine Domain-/Privacyentscheidung nicht relevant. Spaetere Maps-, Geocoding-, Provider- oder Ranking-Funktionen muessen vor Eigenbau erneut nach `docs/REUSE-BEFORE-BUILD.md` und `docs/EXTERNAL-PROVIDER-CANDIDATES.md` geprueft werden.