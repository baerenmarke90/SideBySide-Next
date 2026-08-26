# M3 Collections und Private Area – verbindliche Entscheidungen

**Status:** `DECIDED` – wirksam mit Merge dieses Decision-PRs  
**Datum:** 26.08.2026  
**Tracking:** #164  
**Betrifft:** M3-D13, D14, D15, D16, D17, D18, D19, D23, D32

Dieses Dokument schliesst die blockierenden M3-Entscheidungen fuer gemeinsame Collections und die harte `OWNER_ONLY`-Private-Area. Es enthaelt keinen Runtime-Code und aendert die bestehende M3-Gate-Regel nicht.

## 1. Verbindliche Quellen

- `specification/CLEAN-ROOM-MASTER-SPEC.md`
- `specification/PRODUCT-SPEC.md`
- `docs/SECURITY.md`
- `docs/ROADMAP.md`
- `docs/m3/README.md`
- `docs/m3/DOMAIN-MODEL.md`
- M3-D01 aus #162: collaborative write fuer gemeinsame M3-Ressourcen

Source-bound:

- `Collection`/`CollectionItem` sind `SPACE_SHARED`.
- ShoppingList/ShoppingItem bleiben eigene spaetere Domains.
- `PrivateNote`, `GiftIdea`, `PrivateCollection`, `PrivateCollectionItem` sind `OWNER_ONLY`.
- Owner-only muss serverseitig gelten; Partnerzugriff darf keine Existenz leaken.
- veraenderbare Domainobjekte besitzen Optimistic Concurrency.
- `GiftIdea.status` existiert, seine Werte waren bisher nicht source-bound.

## 2. M3-D13 – Collection Ownership und Shared Writes

### Entscheidung

Gemeinsame Collections verwenden die M3-D01-Regel **collaborative write**.

Persistenz:

```text
Collection
- id
- spaceId
- title
- icon?
- createdBy
- createdAt
- updatedAt
- version

CollectionItem
- id
- collectionId
- title
- completed
- position
- createdBy
- createdAt
- updatedAt
- version
```

Regeln:

- `createdBy` wird bei Root und Item serverseitig gesetzt und bleibt unveraenderlich;
- beide aktiven Space-Mitglieder duerfen Collection-Titel/Icon aendern;
- beide duerfen Items erstellen, umbenennen, abhaken und loeschen;
- beide duerfen die gesamte Collection loeschen;
- `createdBy` ist Attribution/Audit, keine ACL;
- ShoppingList wird nicht als Spezial-Collection modelliert.

## 3. M3-D14 – Collection Concurrency, Versionierung und Reorder

### Zwei Concurrency-Grenzen

M3 trennt **Item-Inhalt** und **Aggregate-Reihenfolge**:

- `Collection.version` schuetzt Root-Felder sowie die Reihenfolge/Struktur der Itemliste;
- `CollectionItem.version` schuetzt Item-Inhalt (`title`, `completed`).

`position` ist vom Collection-Aggregat verwaltetes Ordnungsfeld. Ein Reorder braucht daher die Collection-Version, nicht N unabhaengige Item-Versionen.

### Position

- integer, nullfrei;
- kanonisch contiguous `0..n-1` pro Collection;
- Unique Constraint `(collection_id, position)`;
- Create fuegt am Ende ein und erhoeht `Collection.version`;
- Delete verdichtet die Positionen transaktional und erhoeht `Collection.version`.

Die Runtime darf die Unique-Grenze beim Umsortieren nicht durch naive sequentielle Positionsupdates verletzen. Der PostgreSQL-Slice muss deshalb entweder einen `DEFERRABLE` Unique Constraint bis zum Transaktionsende verwenden oder eine gleichwertige kollisionsfreie temporaere Renummerierung innerhalb derselben Transaktion. Sichtbar und nach Commit zulaessig ist ausschliesslich die kanonische Reihenfolge `0..n-1`.

### Atomarer Reorder

```text
PUT /api/v1/spaces/{spaceId}/collections/{collectionId}/order
If-Match: "<collection-version>"

{
  "itemIds": ["...", "...", "..."]
}
```

Vertrag:

- Request muss **exakt** alle aktuell vorhandenen Item-IDs einmal enthalten;
- keine fremde/cross-collection ID;
- Collection `FOR UPDATE` sperren;
- aktuelle Itemmenge innerhalb derselben Transaktion revalidieren;
- alle Positionen atomar neu schreiben;
- `Collection.version` genau einmal erhoehen;
- kein sichtbarer Zwischenzustand mit doppelten/fehlenden Positionen.

### Item Update

```text
PATCH /collections/{collectionId}/items/{itemId}
If-Match: "<item-version>"
```

- Title/Completed aendern `CollectionItem.version`;
- Completion allein aendert nicht automatisch die Collection-Reihenfolge oder Root-Version.

### Item Delete

Item-Delete veraendert die Itemmenge und damit das Order-Aggregat:

- Collection `FOR UPDATE` sperren, danach Item sperren;
- `If-Match` prueft die Item-Version;
- Item loeschen;
- Positionen verdichten;
- `Collection.version` erhoehen.

Eine separate Collection-Version im Delete-Request ist nicht erforderlich: Der Collection-Lock serialisiert Delete gegen Reorder/Add/Delete. Wenn Delete zuerst committet, scheitert ein bereits mit alter Root-Version gestarteter Reorder mit `409`; wenn Reorder zuerst committet, darf der anschliessende Delete bei weiterhin aktueller Item-Version erfolgreich sein und die neue Reihenfolge erneut konsistent verdichten.

## 4. M3-D15 – Collection Delete

### Entscheidung

`CollectionItem` ist ein echtes Child des Collection-Aggregats.

```text
DELETE Collection
  -> CollectionItems mitloeschen
  -> keine anderen Domainressourcen loeschen
```

- FK `collection_items.collection_id -> collections.id` mit `ON DELETE CASCADE` ist zulaessig;
- Items werden ausserhalb ihrer Collection nicht referenziert;
- ein Collection-Delete ist versioniert (`If-Match`);
- es gibt keine versteckten Relationen zu ShoppingList oder anderen Originalressourcen.

## 5. M3-D16 – ProtectedPayload der Private Area

### PrivateNote

Protected content:

- `title`
- `body`

Strukturelle Owner-only-Metadaten:

- `pinned`
- technische IDs/Timestamps/Version

`pinned` ist nicht oeffentlich/sicher, sondern bleibt trotz struktureller Speicherung streng owner-only.

### GiftIdea

Protected content:

- `title`
- `description`
- `recipient`
- `occasion`
- `targetOn`
- `priceText`
- `url`

Strukturelle Owner-only-Metadaten:

- `status`
- `pinned`
- technische IDs/Timestamps/Version

Auch strukturelle Felder duerfen niemals Partnern, Shared Counts, Logs oder Events offenbart werden.

`url` ist ausschliesslich gespeicherter Nutzerinhalt. M3 fuehrt **keinen serverseitigen Fetch, Preview, OpenGraph-Aufruf oder Redirect-Check** aus.

### PrivateCollection

Protected content:

- Root `title`
- Root `icon`, sofern nutzerdefiniert/fachlich
- Item `title`

Strukturelle Owner-only-Metadaten:

- Item `completed`
- Item `position`
- technische IDs/Timestamps/Version

## 6. M3-D17 – GiftIdea Status

### Enum

M3 verwendet genau:

```text
IDEA
BOUGHT
GIVEN
```

Startzustand:

```text
IDEA
```

Erlaubte Transitionen:

```text
IDEA   -> BOUGHT
IDEA   -> GIVEN       # z. B. selbstgemacht, Erlebnis, kein Kauf
BOUGHT -> IDEA        # Kauf rueckgaengig / Korrektur
BOUGHT -> GIVEN
GIVEN  -> BOUGHT      # reine Statuskorrektur
```

Nicht erlaubt:

```text
GIVEN -> IDEA
```

Fuer eine vollstaendige Ruecksetzung auf eine neue Idee wird eine neue GiftIdea oder eine bewusste zweistufige Korrektur verwendet. Es gibt kein `ARCHIVED` im M3-Kern; Delete/Pinning decken diese Basisfaelle ab.

Statusaenderung ist eine explizite versionierte Domainoperation oder streng validiertes Feldupdate; freie unbekannte Enumwerte sind unzulaessig.

## 7. M3-D18 / D32 – PrivateCollection Persistenz und Autorisierung

### Root

```text
PrivateCollection
- id
- spaceId
- ownerId
- title
- icon?
- createdAt
- updatedAt
- version
```

### Item

```text
PrivateCollectionItem
- id
- collectionId
- title
- completed
- position
- createdAt
- updatedAt
- version
```

### Entscheidung zur Owner-/Space-Persistenz

`PrivateCollectionItem` dupliziert **nicht** `ownerId` und `spaceId`.

Owner/Space werden ausschliesslich ueber den autorisierten Parent abgeleitet. Dadurch gibt es keine zwei potenziell widerspruechlichen Wahrheitsquellen.

Jeder Item-Zugriff muss deshalb query-seitig mindestens semantisch so aussehen:

```text
item
JOIN private_collection parent
  ON item.collection_id = parent.id
WHERE parent.id = :collectionId
  AND parent.space_id = :spaceId
  AND parent.owner_id = :currentAccountId
```

Ein direkter Query nur auf `item.id` ohne owner-scoped Parent ist verboten.

### Private Reorder

PrivateCollection verwendet dasselbe Concurrency-Modell wie Shared Collection:

- Root-Version schuetzt Reihenfolge/Itemmenge;
- Item-Version schuetzt Title/Completed;
- Position contiguous `0..n-1`;
- atomarer Full-List-Reorder mit derselben kollisionsfreien PostgreSQL-Strategie;
- Item-Delete sperrt Root -> Item, prueft die Item-Version, verdichtet Positionen und erhoeht die Root-Version;
- Owner-only.

### Delete

`PrivateCollectionItem` ist Parent-Child und darf bei Root-Delete per FK-Cascade geloescht werden. Keine andere Domainresource wird mitgeloescht.

## 8. M3-D19 – Private API

### Route Namespace

Private Ressourcen bleiben space-scoped, Owner wird **immer aus dem Auth Context** abgeleitet:

```text
/api/v1/spaces/{spaceId}/private/notes
/api/v1/spaces/{spaceId}/private/gift-ideas
/api/v1/spaces/{spaceId}/private/collections
```

Beispiele:

```text
GET    /private/notes
POST   /private/notes
GET    /private/notes/{noteId}
PATCH  /private/notes/{noteId}
DELETE /private/notes/{noteId}

GET    /private/gift-ideas
POST   /private/gift-ideas
GET    /private/gift-ideas/{giftIdeaId}
PATCH  /private/gift-ideas/{giftIdeaId}
DELETE /private/gift-ideas/{giftIdeaId}

GET    /private/collections
POST   /private/collections
GET    /private/collections/{collectionId}
PATCH  /private/collections/{collectionId}
DELETE /private/collections/{collectionId}
```

Child-Routen liegen unter dem autorisierten Parent.

Nicht erlaubt in Request-Bodies:

```text
ownerId
spaceId
privacyClass
```

### 404-Regel

Fuer den aktuellen Account muessen diese Faelle semantisch ununterscheidbar sein:

- unbekannte ID;
- private Resource des Partners;
- private Resource in anderem Space;
- Item unter fremdem privaten Parent.

Antwort: privacy-sicher `404` ohne bestaetigende Zusatzdetails.

### Listen, Counts und Pagination

- Listen enthalten ausschliesslich `ownerId=currentAccount`;
- Counts/Pagination-Totals werden erst **nach Owner-Filterung** gebildet;
- kein Shared Dashboard/Collection-Count erwaehnt private Ressourcen;
- M3 baut keinen globalen privaten Suchindex.

## 9. M3-D23 – Domain Events und Redaction

### Envelope

M3 friert folgenden minimalen Envelope ein:

```text
eventId
eventType
occurredAt
spaceId
actorId
resourceType
resourceId
resourceVersion
privacyClass
safeState?
```

### Shared Resources

Bei `SPACE_SHARED` darf `safeState` ausschliesslich kleine, nicht inhaltliche Enum-/Lifecycle-Werte tragen, wenn ein konkreter Consumer sie benoetigt.

### OWNER_ONLY Resources

Bei `OWNER_ONLY` gilt:

- `privacyClass=OWNER_ONLY`;
- `actorId` ist der Owner/Actor;
- `safeState` bleibt standardmaessig `null`;
- keine Status-, Pin-, Count-, Titel-, URL-, Preis-, Recipient- oder andere fachliche Information im Event;
- Consumer muessen `OWNER_ONLY` explizit behandeln und duerfen daraus keine Partnernotification, Shared Activity oder Dashboard-Sicht erzeugen.

### Niemals in Events/Logs

- Collection-/Item-Titel;
- PrivateNote title/body;
- GiftIdea-Felder inklusive `status`, `url`, `priceText`, `recipient`;
- PrivateCollection-/Item-Titel oder Completion;
- Place-Adresse/Koordinaten;
- private Counts.

## 10. Fehlercodes

Mindestens:

```text
COLLECTION_NOT_FOUND                    404
COLLECTION_ITEM_NOT_FOUND               404
COLLECTION_ORDER_CONFLICT               409
COLLECTION_ORDER_INVALID                422
PRIVATE_NOTE_NOT_FOUND                  404
GIFT_IDEA_NOT_FOUND                     404
GIFT_IDEA_STATUS_TRANSITION_INVALID     409
PRIVATE_COLLECTION_NOT_FOUND            404
PRIVATE_COLLECTION_ITEM_NOT_FOUND       404
RESOURCE_VERSION_CONFLICT               409
```

Es gibt keinen Fehlercode wie `PRIVATE_RESOURCE_OWNED_BY_PARTNER`.

## 11. Verpflichtende Tests

### Shared Collection

- beide Partner duerfen Root und Items schreiben;
- `createdBy` bleibt unveraenderlich;
- Item-Completion mit stale Version -> 409;
- Reorder mit stale Collection-Version -> 409;
- Reorder muss exakt aktuelle Itemmenge enthalten;
- paralleler Reorder -> genau einer gewinnt;
- Reorder vs. Item-Delete -> deterministischer 409/Erfolg, keine Positionsduplikate;
- Parent-Delete cascadiert nur Items;
- Cross-Tenant CRUD/Itemzugriff -> fail-closed.

### PrivateNote / GiftIdea

- Owner CRUD funktioniert;
- Partner GET/LIST/PATCH/DELETE -> privacy-sicher 404/kein Listeneintrag;
- fremde Space-ID semantisch identisch;
- Counts/Pagination leaken nichts;
- GiftIdea startet IDEA;
- alle erlaubten/verbotenen Statuskanten getestet;
- URL wird niemals serverseitig gefetcht.

### PrivateCollection

- Owner-only Root und Child;
- Item-Query ohne autorisierten Parent ist im Service/Repository nicht moeglich;
- Reorder/Delete-Concurrency wie Shared Collection;
- Parent-Delete cascadiert Child-Items;
- Partner kennt weder Parent noch Item ueber IDs/Counts/Fehler.

### Events

- Shared Events enthalten keine ProtectedPayloads;
- Private Events enthalten kein `safeState` mit fachlichen Daten;
- keine Partnernotification/Shared Activity aus OWNER_ONLY Events;
- Log-/Error-Capture-Tests redigieren private Inhalte.

## 12. Reuse-before-build

Fuer diese reine Domain-/Privacyentscheidung nicht relevant. Falls fuer spaeteres Ordering/Ranking eine technische Hilfskomponente erforderlich wird, erfolgt vor Eigenbau eine aktuelle Reuse-Pruefung. Das M3-Modell setzt fuer die Basis lediglich PostgreSQL-Transaktionen, FKs, Unique Constraints und Optimistic Concurrency voraus.
