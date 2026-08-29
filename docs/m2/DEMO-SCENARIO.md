# M2 Demo & Acceptance Scenario

**Purpose:** a reproducible, entirely fictional data set for demos, visual QA, and end-to-end tests  
**As of:** August 24, 2026

All names, content, and media are synthetic. Production data or real private memories must not be used as test fixtures.

## 1. People and spaces

| Key | Person | Space | Role |
|---|---|---|---|
| `LEA` | Lea Sommer | `ALPHA` – Lea & Alex | member/author |
| `ALEX` | Alex Winter | `ALPHA` – Lea & Alex | partner/member |
| `MIRA` | Mira Berg | `BETA` – Mira & Sam | foreign member |
| `REVOKED` | Robin Test | formerly `ALPHA` | membership revoked |

Demo reference date: **August 24, 2026**.

## 2. Seed content

### Shared Memories

| Key | Author | Title | `happenedOn` | Media | Comments |
|---|---|---|---|---:|---:|
| `MEM-LAKE` | LEA | Sonnenaufgang am See | 2026-06-14 | 3 photos | 2 |
| `MEM-KITCHEN` | ALEX | Unser erster Pastateig | 2026-05-03 | 1 photo | 1 |
| `MEM-RAIN` | LEA | Spaziergang im Sommerregen | 2026-07-19 | 0 | 0 |

### HeartMoments

| Key | Author | Text | Emotion | Visibility | `happenedOn` | Attachment |
|---|---|---|---|---|---|---|
| `HM-SHARED` | ALEX | „Danke, dass du heute einfach zugehört hast.“ | APPRECIATED | SHARED | 2026-08-21 | no |
| `HM-PRIVATE` | LEA | `CANARY-PRIVATE-LEA-7421` | GRATEFUL | PRIVATE | 2026-08-22 | `private-lea-7421.jpg` |

`HM-PRIVATE` is intentionally conspicuous technically and must appear only in Lea's owner context.

### Milestones

| Key | Author | Title | `happenedOn` |
|---|---|---|---|
| `MS-GARDEN` | ALEX | Unser erster gemeinsamer Garten | 2026-04-10 |
| `MS-HOME` | LEA | Ein Jahr in unserer Wohnung | 2026-08-01 |

### Comments

| Key | Author | Target | Body |
|---|---|---|---|
| `COM-1` | ALEX | `MEM-LAKE` | „Den frühen Wecker war es wert.“ |
| `COM-2` | LEA | `MEM-LAKE` | „Nächstes Mal mit heißem Kaffee.“ |
| `COM-3` | LEA | `HM-SHARED` | „Das bedeutet mir viel.“ |

No Comment fixture references `HM-PRIVATE`.

## 3. Media fixtures

| File | Purpose | Expected result |
|---|---|---|
| `lake-01.jpg` | valid landscape image | READY |
| `lake-02.jpg` | valid portrait image | READY |
| `lake-03.jpg` | slow processing | PENDING/PROCESSING → READY |
| `pasta.webp` | valid supported format | READY, if allowlist permits it |
| `private-lea-7421.jpg` | private canary | visible only to LEA |
| `spoofed-jpg.exe` | MIME spoof | FAILED |
| `oversize-image.jpg` | size limit | FAILED |
| `broken-image.jpg` | decoder failure | FAILED |

Binary fixtures are created only after the allowlist and limits are decided. Filenames are not storage keys.

## 4. Story expectation

For LEA and ALEX, the shared Story contains the following items in descending order:

1. `HM-SHARED` – 2026-08-21
2. `MS-HOME` – 2026-08-01
3. `MEM-RAIN` – 2026-07-19
4. `MEM-LAKE` – 2026-06-14
5. `MEM-KITCHEN` – 2026-05-03
6. `MS-GARDEN` – 2026-04-10

`HM-PRIVATE` from 2026-08-22 does **not** appear. It creates no empty group, count difference, or shifted cursor.

## 5. End-to-end scenarios

### E2E-01 Read Story

1. ALEX opens Story.
2. The expected six items appear in stable order.
3. Filter “Erinnerung” shows three Memories.
4. Reset restores the timeline and scroll position.
5. DOM, network responses, cache, and analytics contain no private canary.

### E2E-02 Create Memory with media

1. LEA starts “Moment festhalten → Erinnerung”.
2. Enter title “Picknick unter den Linden”, date 2026-08-23, and two valid photos.
3. Add a third broken file; only that file shows an error.
4. Remove the broken file and save.
5. Detail opens exactly one new Memory with two media items.
6. Story shows it in the correct position; double submission does not create a duplicate.

### E2E-03 Private HeartMoment

1. LEA creates a HeartMoment with “Nur für mich”.
2. Owner-only detail shows the privacy label and no comment action.
3. ALEX tries the known ID, Story, search, comments, attachment, and export.
4. Every path returns a neutral 404 or no result.
5. Logs, events, and Push contain neither text nor filename.

### E2E-04 Shared HeartMoment

1. ALEX creates a shared HeartMoment.
2. The one-time explanation before first sharing appears.
3. The item appears in Story.
4. LEA comments.
5. ALEX receives at most one generic notification without comment text.

### E2E-05 Milestone

1. ALEX creates “Erste gemeinsame Bergtour” with a date.
2. Milestone detail and a distinct Story type appear.
3. No disabled Chapter/Recap controls are visible.

### E2E-06 Offline Read/Write

1. ALEX opens Story online, then enables airplane mode.
2. The cache shows “Offline · Stand von …”.
3. ALEX starts a Memory; submit remains “Noch nicht gespeichert”.
4. Input remains; no Story card or success event is created.
5. After an explicit retry online, exactly one Memory is created.

### E2E-07 Version conflict

1. LEA and ALEX open `MEM-LAKE` at the same version.
2. LEA saves a change.
3. ALEX receives `409` when saving his change.
4. The UI shows the current state and preserves Alex's input separately.
5. No automatic overwrite occurs.

### E2E-08 Cross-tenant and revocation

1. MIRA tries known Alpha IDs and cursors.
2. All access remains neutral and mutates nothing.
3. REVOKED tries an old token, Read URL, and cache.
4. The API rejects access; the URL's remaining validity matches the documented TTL; local cache is locked/deleted.

## 6. Visual QA variants

Capture every core screen at:

- Compact 360 px, Medium 720 px, Expanded 1440 px,
- standard and 200% Web zoom or the largest Android font,
- light/dark when Dark Theme is implemented,
- empty, normal, long content, missing media, partial failure,
- visible keyboard focus or TalkBack focus,
- Online, Offline Read, blocked Offline Write,
- privacy-safe 404.

## 7. Accessibility pass

- Read and open Story completely via keyboard/TalkBack.
- Set and remove filters without relying on visual orientation.
- Understand and select the privacy group.
- Add media, recognize errors, remove items, and change order without drag.
- Send a comment and hear its status.
- Resolve 409 without losing own input.
- Back path restores context and focus.

## 8. Analytics expectation

Allowed examples:

```text
story_opened
story_filter_applied { type_class }
memory_create_started|completed|failed { failure_class? }
attachment_upload_failed { failure_class }
heart_moment_create_started|completed|failed
milestone_create_completed
comment_send_completed|failed
```

Fixture and canary values must never appear in an analytics payload.

## 9. Definition of “demo passed”

The demo passes only when domain success, failure recovery, privacy, offline behavior, accessibility, and cross-tenant isolation are visibly demonstrated. A happy-path screenshot alone is not sufficient.
