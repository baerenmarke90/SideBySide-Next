# M2 Screen Flows

**Purpose:** implementable end-to-end paths for Web and Android  
**As of:** August 24, 2026

## 1. Navigation model

The global order remains unchanged:

```text
Heute · Story · Planen · Entdecken · Mehr
```

M2 primarily lives in `Story`. `Heute` may provide contextual entry points such as the intentional de-DE product action "Moment festhalten" or a retrospective, but it does not create a second M2 navigation structure.

### M2 routes as product contract

| Route ID | View | Visibility | Compact | Expanded |
|---|---|---|---|---|
| `story` | shared Timeline | Space members | page | list + Detail Pane |
| `story/search` | Search and filters | Space members | Overlay/page | Toolbar + result list |
| `memory/new` | create Memory | Space members | new page | centered Form Page |
| `memory/:id` | Memory Detail | Space members | new page | Detail Pane |
| `heart-moment/new` | create HeartMoment | Space members | new page | centered Form Page |
| `heart-moment/:id` | HeartMoment Detail | according to visibility | new page | Detail Pane |
| `private-moments` | personal HeartMoments | owner only | new page under `Mehr` | protected area under `Mehr` |
| `milestone/new` | create Milestone | Space members | new page | centered Form Page |
| `milestone/:id` | Milestone Detail | Space members | new page | Detail Pane |

Technical URL paths follow the later Router concept. Route IDs describe navigation and Deep-Link behavior, not automatically Backend routes.

## 2. Entry point "Moment festhalten"

**Entry points:** Quick Action on `Heute`, primary action in `Story`, contextual action in the empty Story state.

```text
Moment festhalten
├── Erinnerung
├── Herzmoment
└── Meilenstein
```

- Compact: Bottom Sheet with three clearly described options.
- Expanded: small Menu or Dialog anchored to the triggering element.
- Focus returns to the triggering action when canceled.
- The selection is not remembered; every new item begins intentionally.
- "Privat" is not preselected in the picker because only HeartMoment supports that choice.

## 3. Flow M2-A – View, filter, and open Story

**Goal:** read the shared history chronologically without implying private content.

1. Person opens `Story`.
2. Timeline loads with Cursor Pagination and groups by month.
3. Filters provide type, year, and sort order; Search is server-side.
4. Selecting a Card opens the original resource.
5. Compact uses a new page; Expanded keeps the Timeline visible and opens a Detail Pane.
6. Back restores Search text, filters, Cursor, selection, and scroll position.

**Story contains:** Memory, Milestone, `SHARED` HeartMoment.  
**Story never contains:** `PRIVATE` HeartMoment, hidden Attachment relation, or partner Canary.

**Card content**

- type and author,
- Title/text Preview according to Domain,
- `happenedOn` as domain date,
- at most one calm Media Preview plus count,
- Comment count only for permitted Targets,
- no redundant "shared" Badge on every shared Memory; Privacy notice only where a choice exists.

## 4. Flow M2-B – Create Memory with Media

**Privacy:** always `SPACE_SHARED`; no hidden private mode.

1. Select the de-DE product type "Erinnerung".
2. Enter Title, text, and domain date.
3. Select zero to multiple Media items.
4. Each file appears immediately as a local Tile with status.
5. Validation errors are shown per file; other files and text remain intact.
6. Before saving, the intentional de-DE product copy "Mit Partner geteilt" is visible.
7. Save Online; success opens the new Memory.
8. Story updates as soon as the Domain content is available; Media may follow with transparent status.

### Media states in the form

```text
selected → validating → uploading → processing → ready
                  └──────────────→ failed → retry | remove
```

| State | Presentation | Allowed action |
|---|---|---|
| selected | Preview + file type | remove |
| validating | de-DE product copy "Datei wird geprüft …" | cancel if technically safe |
| uploading | progress without false precision | cancel/remove according to contract |
| processing | de-DE product copy "Foto wird verarbeitet …" | leave form only with notice |
| ready | Preview, order, description | move, remove |
| failed | reason in understandable category | Retry or remove |

A failed Media item does not automatically discard the Memory draft. Whether the Memory may be saved before all Uploads finish follows the Media/API decision and is not improvised client-side.

## 5. Flow M2-C – HeartMoment private or shared

1. Enter text and emotion.
2. Select visibility explicitly:
   - **Nur für mich** — the partner does not see this moment.
   - **Mit Partner teilen** — the moment appears in the shared area.
3. Optionally add an Attachment.
4. Before the first share, the UI briefly explains the consequence.
5. After saving, show the Privacy label and Sync state.

### Private route

- Success leads to the personal `private-moments` area or owner-only Detail.
- The shared `Story` is not offered as the return path.
- No Comment action, partner Avatars, or shared Activity indicator.
- Private content must not appear in global Search, recently opened, Push Preview, or shared Share Sheet.

### Shared route

- Success opens Shared Detail and makes the item visible in `Story`.
- Comments are permitted.
- Transition `SHARED → PRIVATE` is Online, version-checked, and explains that already-read content cannot be made unread retroactively.
- Existing Comment behavior follows `M2-D07` in the Decision Log.

## 6. Flow M2-D – Create Milestone

1. Select the de-DE product type "Meilenstein".
2. Enter Title, optional text, and domain date.
3. Show a clear notice of shared visibility.
4. Save opens Milestone Detail.
5. Story shows the Milestone as a dedicated type, not a decorated Memory.

No Chapter, Place, or Recap controls in M2. The UI may reserve structural space for them but does not show disabled future features.

## 7. Flow M2-E – Comment and notify

**Permitted Targets:** shared Memory, Milestone, shared HeartMoment.

1. Person opens an allowed Detail.
2. Comments load after Domain Authorization.
3. The de-DE product action "Kommentar schreiben" opens an Inline Composer (Compact) or fixed Detail area (Expanded).
4. Sending shows exactly one optimistic state only if the API contract safely supports Idempotency; otherwise show "Wird gesendet …" until confirmation.
5. Success appends the Comment and keeps focus on the new item or Composer according to the action.
6. Comment on another person's content creates a minimal Domain Event; Push Preview remains generic.

For `404`, neither Target existence nor Privacy reason is explained. When content becomes private, the shared Comment path disappears completely.

## 8. Flow M2-F – Offline Read and blocked Write

### Read

- The last authorized view may be shown with the de-DE status copy "Offline · Stand von {Zeit}".
- Media without a secure local cache uses a neutral placeholder.
- Space switch, Logout, or Session revocation removes/locks Space- and owner-bound caches.

### Write

- Input may remain as a local draft in the current secure context.
- Submit never ends in "Gespeichert" or "Synchronisiert" while Offline.
- Product copy: "Noch nicht gespeichert. Verbinde dich mit dem Internet und versuche es erneut."
- After reconnection, Retry occurs only through an intentional action.
- Privacy transitions are not allowed Offline.

## 9. Flow M2-G – Version conflict

1. Update receives `409`.
2. The current server state is safely reloaded.
3. UI shows the de-DE product copy "Dieser Inhalt wurde inzwischen geändert."
4. Person can inspect the current state and copy/reapply local input.
5. No automatic last-write-wins.
6. For Privacy-relevant conflicts, an older visibility value is never resaved automatically.

## 10. Deep Links and return behavior

- Deep Link checks Auth, Membership, and resource visibility before presentation.
- Not found and unauthorized share the same neutral `404` state.
- After Re-Authentication, return only to a still-permitted destination.
- Expanded: closing Detail Pane restores focus and list selection.
- Compact: System Back returns to the previous filter/scroll position.
- A Deep Link to `PRIVATE` resolves only in owner context.

## 11. Analytics boundaries

Allowed: Event class, success/error category, platform, and coarse duration class. Forbidden: Title, Body, Comment, Search text, original filename, Media content, Read URL, concrete emotion, Resource ID, or partner identifier.
