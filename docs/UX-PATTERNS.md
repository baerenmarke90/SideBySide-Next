# SideBySide UX Patterns

**Status:** Binding product foundation  
**Version:** 1.1  
**As of:** August 24, 2026

This document defines recurring interaction patterns for the WebApp and
smartphone app. Both surfaces share the same information architecture,
semantics, and state logic. Concrete presentation adapts to platform, window
width, and input method.

## 1. Core rules

1. **Same task, same terminology.** A feature uses the same product term on all
   platforms.
2. **Platform-appropriate, not pixel-identical.** Navigation, dialogs, and
   gestures may differ as long as meaning and result remain equivalent.
3. **Privacy is visible.** Private and shared content is clearly identified
   before, during, and after an action.
4. **Current state is observable.** Loading, saving, synchronization, offline
   state, and errors are never hidden.
5. **One primary action per view.** Additional actions are visually secondary.
6. **No dead ends.** Every empty or error state provides a meaningful next step.
7. **Progressive disclosure.** Frequent tasks remain directly accessible;
   uncommon options appear contextually.

## 2. App Shell and navigation

| Window class | Primary navigation | Secondary navigation | Detail view |
|---|---|---|---|
| Compact, up to 599 px | Bottom Navigation with at most 5 destinations | Tabs or local list | new page |
| Medium, 600–839 px | Navigation Rail | Tabs or list | new page or second pane |
| Expanded, from 840 px | persistent Sidebar/Rail | local navigation in content area | second or third pane |

- Primary destinations are the intentional de-DE product labels **Heute, Story,
  Planen, Entdecken, Mehr**. `Entdecken` depends on the M7 Discover domain: its
  position is reserved and it is not rendered before that domain exists, so the
  primary navigation carries four destinations until then. See
  `decisions/0003-primary-navigation-and-route-model.md`.
- Search and Activity are not primary destinations. Search is a global utility
  in the app bar; Activity lives underneath `Heute`.
- The active destination is identifiable through shape, color, and text state,
  never through color alone.
- Badge counts are used only for current, actionable information.
- On Web, every primary function is keyboard-accessible and focus remains
  visible.
- Back navigation stays inside the current workflow rather than unexpectedly
  returning to the start.

## 3. Canonical interaction patterns

| Task | Smartphone | WebApp |
|---|---|---|
| Primary navigation | Bottom Navigation | Rail or Sidebar |
| List and detail | separate pages | List-Detail layout from Medium upward |
| Short input | Bottom Sheet or Dialog | Dialog or Side Pane |
| Long form | dedicated page | dedicated page or wide Side Pane |
| Filters | Filter Sheet | Popover or persistent filter bar |
| Context actions | Overflow menu; gestures supplementary only | Overflow or context menu |
| Confirmation | Dialog for high-risk actions | Dialog for high-risk actions |
| Feedback | inline plus Snackbar when useful | inline plus Snackbar when useful |

### 3.1 List–Detail

- One row or card opens exactly one detail object.
- Selection state remains visible on wide layouts.
- Filters, sorting, and scroll position are preserved when navigating back.
- On Compact, detail replaces the list; on Expanded, the list remains visible.
- Direct links open the target object and activate the appropriate navigation
  context.

### 3.2 Create and edit

- Short forms: at most five simple fields in a Sheet, Dialog, or Side Pane.
- Long, branching, or media-heavy forms: dedicated page.
- Required fields are marked textually; errors appear next to the affected
  field.
- Changes are autosaved only when the state is unambiguous, visible, and
  recoverable.
- If unsaved changes exist, the app asks before leaving.
- After successful creation, the app navigates to the new content or back to
  the refreshed list.

### 3.3 Dialog, Bottom Sheet, Side Pane, or page

| Pattern | Use for | Do not use for |
|---|---|---|
| Dialog | irreversible decision, short confirmation | multi-step forms |
| Bottom Sheet | mobile selection, short contextual action | critical long-form text |
| Side Pane | Web detail, preview, short edit | central full-screen task on Compact |
| dedicated page | focused, complex, or shareable task | single yes/no question |

### 3.4 Search, filters, and sorting

- Search starts only after meaningful input or a short delay; in-flight requests
  are replaced.
- Active filters are visible as removable chips.
- The intentional de-DE label **„Zurücksetzen“** appears only when at least one
  filter is active.
- Result count and empty-search state explain the outcome.
- Sorting changes no data and remains clearly distinct from filtering.
- Search terms, filters, and sorting remain available throughout a session.

## 4. States for every data-driven view

Every data-driven component and screen supports these states:

| State | Presentation | Primary response |
|---|---|---|
| Initial | stable base structure | no action yet |
| Loading | Skeleton matching expected content | wait for content |
| Content | actual content | perform core task |
| Empty | explain cause and value | create or discover content |
| Error | understandable cause where known | retry |
| Offline | last authorized read cache plus timestamp/age | read; clearly block writes |
| Syncing | subtle persistent status | continue working |
| Conflict | explain differences and consequences | consciously choose a version |

- A spinner alone does not replace a stable loading state.
- Existing content remains visible during background refresh.
- Critical errors are inline; a Snackbar alone is insufficient.
- Success feedback disappears automatically when no further action is needed.

## 5. Saving, synchronization, and undo

- Safe reversible changes may be represented optimistically.
- If saving fails, the local draft is preserved.
- Intentional de-DE synchronization copy is **„Wird gespeichert“**,
  **„Gespeichert“**, or **„Aktion nötig“**.
- Android supports offline reading in the MVP, but no offline writes and no local
  Outbox. A write attempt ends with **„Noch nicht gespeichert“**; a secure form
  draft may be retained.
- Deletions should be recoverable through de-DE **„Rückgängig“** where feasible.
- Conflicts are never overwritten silently.
- Timestamps are supplementary; understandable state comes first.

## 6. Privacy and sharing

- Every object has a domain privacy class. The UI maps `OWNER_ONLY` to the
  intentional de-DE label **„Nur für mich“** and `SPACE_SHARED` to
  **„Für uns beide“**.
- A privacy choice appears only in domains supporting multiple classes; Memory,
  Wish, and Plan remain `SPACE_SHARED` in the current Core.
- Visibility state appears near the title, form completion area, or primary
  action.
- Where selection is allowed, the most data-minimizing permitted class is the
  default unless the product specification defines otherwise.
- Before first sharing, the UI explains recipient, content, and effect.
- Changing private content to shared is a deliberate action and receives clear
  confirmation in the result.
- Changing back to private explains whether already synchronized copies or
  notifications are affected.
- Security and encryption claims are shown only when technically substantiated.

## 7. Permissions

- System permissions are requested **just in time**, immediately after an
  understandable user action.
- Before the system prompt, the app explains value and alternatives.
- Denial blocks only the affected feature, not the entire app.
- Settings provide an understandable path to change permissions later.
- Camera, photos, location, contacts, and notifications are justified
  separately.

## 8. Destructive and sensitive actions

- Destructive actions are named in text and visually distinct.
- Confirmation is required when data is not directly recoverable or another
  person is affected.
- The confirmation names the concrete object and consequence; de-DE example:
  **„Erinnerung endgültig löschen“**.
- Swipe gestures are shortcuts only; the same action remains available through
  a visible menu.
- Sign out, disconnect relationship, and delete account are separate actions
  with different risk levels.

## 9. Media upload

Media passes through `selected → preparing → uploading → processing → ready` or
`failed`.

- Before upload, preview, file type, and removal are available.
- Progress is shown per media item.
- A failure affects only that item and offers the de-DE action
  **„Erneut versuchen“**.
- Cancellation and reselection remain possible before final save.
- Alt text or a description is available for semantically relevant images.
- Metadata and location information follow the documented privacy rule.

## 10. Notifications

- Push previews contain no sensitive content by default.
- Users choose event type, channel, and preview level.
- Every notification leads to one concrete destination.
- Grouping prevents a stream of separate notifications for the same activity.
- In-app notices do not replace system-level error presentation.

## 11. Motion and feedback

- Animation explains hierarchy, causality, or movement between places.
- Standard duration: 120–280 ms; no normal transition lasts longer than 320 ms.
- `prefers-reduced-motion` and the platform reduced-motion setting are
  respected.
- No content is readable only during an animation.
- Haptic feedback supplements a visible state change and never replaces it.

## 12. Accessibility

- Touch targets are at least 48 × 48 dp in the app and 44 × 44 CSS px on Web.
- Text and essential symbols meet at least WCAG 2.2 AA.
- Focus order follows visual and semantic order.
- Web components use native HTML elements before adding ARIA roles.
- Every icon button has an accessible name.
- Information is never conveyed through color, position, motion, or haptics
  alone.
- Dynamic status messages are announced to assistive technologies without
  moving focus unnecessarily.

## 13. Anti-patterns

- Cards nested inside cards without real hierarchy.
- Multiple equally strong primary actions.
- Icon-only treatment for uncommon or critical actions.
- Delete available only through swipe.
- Critical errors shown only as transient Snackbars.
- Disabled buttons without explanation of missing prerequisites.
- Horizontal scrolling used as hidden primary navigation.
- Different terminology for the same feature on Web and Mobile.
- Privacy claims not backed by technology and operations.
- Desktop layout merely compressed onto a smartphone.

## 14. Acceptance criteria

A new flow is ready for implementation only when:

- Compact and Expanded behavior are described,
- Loading, Empty, Error, Offline, and Success are covered,
- privacy and permission consequences are resolved,
- keyboard, focus, screen reader, and large-text behavior are considered,
- one primary action and a clear way back exist,
- destructive actions are reversible or consciously confirmed,
- analytics events contain no sensitive content data.

## Related documents

- [Design Principles](./DESIGN-PRINCIPLES.md)
- [Information Architecture](./INFORMATION-ARCHITECTURE.md)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Screen Templates](./SCREEN-TEMPLATES.md)
- [Design Tokens](../design/tokens.json)
- [Critical User Flows](./USER-FLOWS.md)
- [API/UI Contracts](./API-UI-CONTRACTS.md)
