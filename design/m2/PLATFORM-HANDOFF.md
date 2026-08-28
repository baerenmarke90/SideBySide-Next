# M2 Platform Handoff

**Purpose:** same Domain contract, platform-appropriate implementation  
**As of:** August 24, 2026

## 1. Shared core

Web and Android share:

- route and screen terminology,
- Privacy classes and visible copy,
- field and error semantics,
- API DTOs and Concurrency rules,
- Media lifecycle and Retry categories,
- Analytics names and data minimization,
- Story ordering, filters, and Cursor behavior,
- acceptance dataset and Privacy Canaries.

Platforms may adapt presentation and system integration, not Domain meaning or Authorization.

## 2. Window classes

| Class | Width | Navigation | Story | Detail | Create |
|---|---:|---|---|---|---|
| Compact | up to 599 px | Bottom Navigation, max five destinations | one column | new page | new page, full width |
| Medium | 600–839 px | Navigation Rail | wider list | new page or narrow Side Pane depending on space | centered form |
| Expanded | from 840 px | Sidebar | list + optional Detail Pane | 320–480 px Pane | centered form, Reading Max 720 px |

On large Web windows, text lines do not grow without limit. Content Max remains 1200 px and Reading Max remains 720 px.

## 3. Component mapping

| Task | Web | Android | Shared contract |
|---|---|---|---|
| Main navigation | Sidebar/Rail/Bottom Nav | Navigation Bar/Rail | `navigation-item` |
| Select type | Menu or Dialog | Modal Bottom Sheet | three described options |
| Choose Privacy | Radio Group / Selection Cards | Radio/Selection Controls | mandatory, not color-only |
| Story Card | semantic article/link | clickable Content Card | type, author, date, Preview |
| Detail | Side Pane or page | new Destination | neutral 404, stable Back navigation |
| Media | Grid/List with file actions | Media Tiles, System Picker | status, Retry, Remove, Reorder |
| Comment | Inline Composer | Inline/Bottom Composer | permitted Targets only |
| Error | Inline Message + optional Summary | Inline Message/Snackbar | outcome + next step |

Existing component contracts remain authoritative; M2 introduces no parallel component library.

## 4. Web-specific

- Use native Links for navigable Story Cards; opening in a new tab re-evaluates Authorization.
- Keyboard: Tab/Shift+Tab, Enter/Space, Escape, and arrow keys according to component semantics.
- Expanded List/Detail preserves selection, filters, and scroll position.
- Browser Back is a product path, not an emergency exit.
- Service Worker or Query Cache must not retain owner/Space data across Logout or Space changes.
- Do not persist signed Media URLs in persistent cache, History State, Analytics, or DOM datasets.
- Forms use appropriate Autocomplete semantics only for non-sensitive standard fields.

## 5. Android-specific

- Prefer System Photo Picker; request permission only from the intentional de-DE product action "Foto hinzufügen".
- System Back closes Sheet/Overlay first, then Detail, then Destination.
- TalkBack reads a Card as coherent content with separate clearly named actions.
- Drag-based Media ordering has Move-up/Move-down alternatives.
- App Switcher/Recents protection for private screens is documented as a Security/UX decision.
- Do not place private content or Read URLs in unencrypted Shared Preferences, general Backups, Clipboard, or Share Sheet.
- WorkManager must not simulate silent Offline Write Sync in the MVP.

## 6. Responsive Story

### Compact

- Month group above a vertical Card list.
- Search and filters as a dedicated surface or Bottom Sheet.
- Floating Action only if it obscures neither navigation nor content; otherwise use a clear Toolbar action.
- Detail replaces the list; Back restores state.

### Expanded

- Story list remains the primary surface.
- Detail Pane opens on the right with its own heading/close action.
- Search/filters live in the local Story Toolbar.
- Create Form does not displace list and Detail into three competing columns simultaneously.

## 7. Accessibility budget

These criteria block M2 Release:

| Area | Web | Android |
|---|---|---|
| Target size | at least 44 × 44 CSS px | at least 48 × 48 dp |
| Text scaling | 200% without loss of function | largest supported font/display size |
| Operation | complete keyboard operation | TalkBack, Switch Access, external keyboard |
| Focus | visible, logical, restored after overlay | stable Semantics focus and Back path |
| Contrast | WCAG 2.2 AA target according to QA contract | same semantic color pairs |
| Status | Live Region only for relevant change | polite status announcement |
| Media | description/Alt-Text contract | Content Description/Description |
| Motion | `prefers-reduced-motion` | system reduced-motion option |

Automated checks supplement but do not replace keyboard, Screen Reader, and large-font acceptance.

## 8. Product performance budgets

Budgets are internal targets measured on agreed reference devices/networks.

| Measurement | Budget | Note |
|---|---:|---|
| route shows stable structure | ≤ 150 ms after navigation | App Shell + screen frame, before network data |
| cached Story usable | ≤ 700 ms p75 | no private cache from wrong context |
| Web LCP | ≤ 2.5 s p75 | representative Mobile Web test |
| Web INP | ≤ 200 ms p75 | filter, Card, form actions |
| Web CLS | ≤ 0.10 p75 | Media reserves space |
| Android Warm Start until usable | ≤ 1.0 s p75 | agreed mid-range device |
| Android Cold Start until usable | ≤ 2.5 s p75 | no blocking on Media prefetch |
| first visible Media Preview | ≤ 1.5 s p75 | after authorized content on reference network |
| local UI response | ≤ 100 ms | selection, Privacy, remove file |
| visible loading indicator | from 300 ms | short operations do not flicker |
| Upload progress | by 500 ms at latest | status instead of invented percentages |

Budgets must not be achieved by preloading foreign or private content. Privacy filtering and Authorization take precedence over speed.

## 9. Telemetry

Allowed:

- Screen/Flow ID,
- platform and app version,
- coarse duration and error class,
- Online/Offline as technical state,
- success/abort.

Forbidden:

- content, emotion, Search text, and Comment,
- original filename, MIME details, and image characteristics,
- Resource, Attachment, Space, or partner ID in product Analytics,
- Read URLs, Tokens, or signatures,
- private/shared combinations when they enable re-identification.

## 10. Release handoff

Before merging a client flow, provide:

1. Screenshots or visual tests for Compact, Medium, and Expanded.
2. Keyboard/TalkBack recording of the core path.
3. Large-font and long-content test.
4. Offline, 401, 404, 409, 429, and 5xx evidence.
5. Privacy Canary test from the Demo Scenario.
6. Measurement against the relevant performance budgets.
7. Alignment with the published OpenAPI contract.
