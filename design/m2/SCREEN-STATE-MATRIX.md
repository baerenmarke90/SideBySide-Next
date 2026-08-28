# M2 Screen State Matrix

**Purpose:** binding UI states before implementation begins  
**As of:** August 24, 2026

## 1. Global state sequence

Every data-driven M2 view evaluates at least:

```text
initial → loading → content
                 ├→ empty:first-use
                 ├→ empty:filter
                 ├→ partial
                 ├→ offline:cached
                 └→ error {validation | 401 | 404 | 409 | 429 | 5xx}
```

Privacy filtering runs before every visible state. An empty screen therefore must not reveal that private or foreign results exist.

## 2. Shared copy and actions

The strings in this table are intentional de-DE product copy and remain localized.

| State | Primary copy | Primary action | Preserved context |
|---|---|---|---|
| loading | no technical copy required; structural Skeleton | none | route, filters, selection |
| empty:first-use | „Eure Story beginnt hier“ | „Erinnerung hinzufügen“ | navigation |
| empty:filter | „Keine passenden gemeinsamen Momente“ | „Filter zurücksetzen“ | Search field local only, never Telemetry |
| partial | „Einige Inhalte konnten nicht geladen werden.“ | „Erneut versuchen“ | already safe content |
| offline:cached | „Offline · Stand von {Zeit}“ | optional „Erneut verbinden“ | cache + scroll position |
| offline:write | „Noch nicht gespeichert.“ | „Erneut versuchen“ after reconnect | complete secure draft |
| validation | concrete field/file message | implicit „Fehler korrigieren“ | all input |
| 401 | „Deine Sitzung ist abgelaufen.“ | „Erneut anmelden“ | permitted return target only |
| 404 | „Dieser Inhalt ist nicht verfügbar.“ | „Zur Story“ | no existence/Privacy details |
| 409 | „Dieser Inhalt wurde inzwischen geändert.“ | „Aktuellen Stand ansehen“ | local input separately |
| 429 | „Das waren viele Versuche.“ | timed Retry | input without automatic spam |
| 5xx | „Das hat gerade nicht geklappt.“ | „Erneut versuchen“ | safe view/draft |

## 3. Matrix per screen

| Screen | Loading | Empty | Partial/Offline | Critical errors | Success |
|---|---|---|---|---|---|
| Story Timeline | month Skeleton, no stale foreign data | first use and filters separated | safe Cards + status bar | 401, Privacy-safe 404, 5xx | stable Timeline, focus on heading |
| Story Search | field immediately usable, result Skeleton | no results without private Counts | latest authorized result state clearly marked | invalid Cursor neutral, 429 | filter count and results consistent |
| Memory Detail | structure for text/Media/Comments | not applicable | text may load while individual Media fail | 404, 409 on Edit | author/date/Media correct |
| Memory Form | existing Edit state Skeleton | new draft | Offline draft without success signal | field errors, 409, Upload failures | Detail opens; Story updates |
| Media Queue | per-file state | intentional de-DE product action „Foto hinzufügen“ remains optional | individual failures do not block everything | type/size/dimension/timeout | `ready` with ordering |
| HeartMoment Form | do not imply default Privacy | visibility remains mandatory | Offline save blocked | Privacy transition 409/Offline | owner or Shared destination correct |
| Private Moments | owner-bound Skeleton | calm personal Empty State | cache clearly personal and Offline | partner sees neutral 404 | owner content only |
| Milestone Form/Detail | standard Form/Detail Skeleton | new draft | text remains on network failure | Validation, 409, 404 | dedicated Story type |
| Comments | Comment Skeleton after parent | „Noch keine Kommentare“ only on permitted Target | existing Comments remain, Retry separate | Target 404/private, send failure | new Comment exactly once |

## 4. Story Timeline in detail

### Initial and Loading

- App Shell and page title appear immediately.
- Skeleton matches Card and month group but contains no random names, images, or dates.
- Already visible safe cache is not replaced by an empty Skeleton; it receives a Refresh state.
- Screen Reader announces the intentional de-DE status copy „Story wird geladen“ once, not once per Skeleton Card.

### Empty: first use

Intentional de-DE product copy:

```text
Eure Story beginnt hier
Haltet einen gemeinsamen Moment fest, wenn es für euch passt.
[Erinnerung hinzufügen]
```

No artificial urgency, partner blame, or private alternative appears in the shared Story.

### Empty: Search/filter

- Active filters remain visible.
- Search text is not copied into Analytics or error reports.
- Do not show copy such as „3 private Treffer ausgeblendet“.
- Reset preserves Story context and correctly resets Cursor/scroll.

### Partial

- Failed Media shows a placeholder per Card.
- Failure on a Cursor page does not remove already loaded Cards.
- Retry reloads only the affected section and creates no duplicates.

## 5. Forms

### Required structure

1. unambiguous page title,
2. Domain fields,
3. Privacy status or mandatory selection,
4. optional Media,
5. one primary Save action,
6. secondary Cancel with draft warning only when changes exist.

### Validation

- Error appears directly at the field and in a focusable Summary when multiple errors exist.
- The first invalid area receives focus after Submit.
- Value, selection, Media ordering, and local draft are preserved.
- No error message names internal fields, tables, or Storage identifiers.

### Saving

- Action is protected against double submit.
- The intentional de-DE status „Wird gespeichert …“ is announced politely; focus remains stable.
- Timeout is not success. The UI resolves Idempotency/status before creating again.
- Leaving during an active Upload follows the Media decision; no silent background promise is made.

## 6. Media states

The user-facing strings below remain intentional de-DE product copy.

| Error class | User copy | Next action | Telemetry |
|---|---|---|---|
| type not allowed | „Dieses Dateiformat wird nicht unterstützt.“ | choose another file | `unsupported_type` |
| too large | „Diese Datei ist zu groß.“ | choose another file | `size_limit` |
| dimension/processing | „Dieses Bild konnte nicht verarbeitet werden.“ | Retry or remove | `processing_failed` |
| network | „Upload unterbrochen.“ | Retry | `network` |
| Authorization | neutral parent/Session state | sign in/back | no file details |
| Storage/server | „Upload gerade nicht möglich.“ | Retry later | `service_unavailable` |

Filename, MIME details, pixel values, and Read URLs do not belong in standard Telemetry. Technical details may appear only in sanitized diagnostics.

## 7. HeartMoment Privacy states

The quoted strings are intentional de-DE product copy.

| State | Visible elements | Forbidden elements |
|---|---|---|
| selection open | both options equally understandable | preselected Privacy without product decision |
| PRIVATE saved | „Nur für mich“, owner context | Comment, partner Activity, Story Link |
| SHARED saved | „Mit Partner geteilt“, Story/Comment access | ambiguous lock without text |
| PRIVATE → SHARED | confirmation of new visibility | silent switch |
| SHARED → PRIVATE | notice of future invisibility and limits of withdrawal | promise to erase already-read content |
| partner Deep Link to PRIVATE | neutral 404 state | „privat“, author name, date, Attachment |

## 8. Accessibility acceptance per state

- Name, role, value, and status are programmatically determinable.
- Status changes are announced once and politely.
- Focus remains stable during Loading/Refresh and does not jump to the page start.
- Error Summary and field errors are linked.
- Privacy selection is operable as a group with two complete Labels.
- Media Tiles include file type, status, and action in the accessible name.
- Reordering is possible without Drag.
- 200% Web zoom and the largest supported Android font do not clip required text.
- Color is always supplemented by text, Icon, or shape.
- Reduced Motion loses no status information.

## 9. Visual test datasets

Every screen is tested with:

- 0, 1, 2, and 20 Story items,
- very short and very long Title/text,
- a date with a long German month name to exercise de-DE localization,
- 0, 1, and multiple Media items in mixed states,
- long display names and missing Avatar,
- no Comment, one Comment, and a longer list,
- PRIVATE Canary that must not appear in any Shared view.
