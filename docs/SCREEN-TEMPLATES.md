# SideBySide Screen Templates

**Status:** Binding product foundation  
**Version:** 1.1  
**As of:** August 24, 2026

Screen Templates translate Information Architecture, UX Patterns, and Components into repeatable page structures. They are not finished screens, but binding layout and behavior frameworks.

## 1. Window classes

| Class | Width | Navigation | Content |
|---|---:|---|---|
| Compact | 0–599 px | Bottom Navigation | one primary pane |
| Medium | 600–839 px | Navigation Rail | one to two panes |
| Expanded | from 840 px | Rail or Sidebar | two to three panes |

- Switching is based on available window width, not device category.
- Content is preserved across resize; selection and input are not lost.
- Primary content is at most 1200 px wide; reading text is at most 720 px wide.
- Outer spacing: 20 px on Compact, at least 24 px on Medium, up to 64 px on Expanded.

## 2. Shared screen anatomy

Every regular screen contains, in this order:

1. App Shell and navigation context.
2. Page title and optional short orientation text.
3. Primary action, placed appropriately for the window class.
4. Optional Tabs, filters, or local navigation.
5. Main content.
6. Persistent status surface for Offline, Sync, or errors where required.

On Compact, a Floating Action Button-like action is used only when it is unambiguous, frequent, and cannot be confused with Bottom Navigation.

## 3. Template: Today

**Purpose:** Shared daily overview and fast entry point.

### Compact

- Greeting and shared context.
- One highlighted next action or Memory.
- Vertical modules: planned today, open items, new moment.
- Contextual primary action, for example the intentional de-DE label **„Moment festhalten“**.

### Expanded

- Two-column Dashboard.
- Main column: day flow and next tasks.
- Secondary column: Quick Actions, Sync/Privacy notices, and compact summary.
- No freely configurable widget wall in version 1.

**Required states:** first launch, everything completed, offline with local data, partial loading failure.

## 4. Template: Story Timeline

**Purpose:** Explore shared Memories chronologically.

### Compact

- Filter/search in a Sheet.
- Timeline as a vertical list.
- Detail opens as a new page.
- Intentional de-DE primary action **„Erinnerung hinzufügen“**.

### Expanded

- Left pane: filters and time ranges.
- Middle pane: Timeline.
- Right pane: selected Memory or preview.
- Direct URL for every detail.

**Required states:** no Memories, empty filtered result, media loading, private content, upload failure.

## 5. Template: Plan Hub

**Purpose:** Entry point for Wishes and Plans; Shopping is added later as its own domain.

### Compact

- Two clearly named entry points with current state; a later Shopping entry appears only when the domain is implemented and enabled.
- Recent or urgent content below the entry points.
- No nested card landscape.

### Expanded

- Local navigation or segmentation for Wishes and Plans; Shopping later.
- List-Detail structure for the selected area.
- Supporting pane only when it provides real additional value.

**Primary action:** changes with the active area, for example the intentional de-DE label **„Wunsch hinzufügen“**.

**Required states:** empty area, shared and private entries, Sync conflict, completed entries.

## 6. Template: Shopping List (later domain)

**Purpose:** Fast shared checking-off, including under poor connectivity.

### Compact

- Direct input at the top.
- Grouped Checklist with large touch targets.
- Offline state remains visible; writes are not allowed in the MVP without connectivity.
- Additional information opens a Sheet or page.

### Expanded

- Main pane: list and input.
- Optional secondary pane: selected Recipe, note, or history.
- Keyboard shortcuts for adding and focus movement.

**Required states:** Offline read cache, offline write attempt with **„Noch nicht gespeichert“**, online conflict, everything completed, undo deleted entry.

## 7. Template: Discover

**Purpose:** Offer inspiration without overshadowing private core tasks.

### Compact

- Search field, topic chips, and vertical Feed.
- Filters in a Sheet.
- Detail opens as a new page.

### Expanded

- Search and filter bar above a responsive Grid.
- Optional Detail Pane for quick preview; full detail has its own URL.
- Cards remain consistent and avoid changing interaction logic.

**Required states:** personalized and neutral recommendations, no results, recommendation failure, blocked external source.

## 8. Template: Settings and Privacy

**Purpose:** Manage relationship, Account, data, permissions, and notifications understandably.

### Compact

- Categorized list; every category opens its own page.
- Critical actions appear at the end of the relevant area rather than in an isolated danger zone without context.

### Expanded

- Left pane: categories.
- Right pane: selected settings.
- Changes either apply immediately with feedback or are confirmed through one clearly visible Save action — never both patterns mixed within one form.

**Required states:** permission denied/blocked, export being generated, account action pending, relationship not connected.

## 9. Template: Create/Edit

**Purpose:** Create or modify content safely and transparently.

### Compact

- Dedicated page for long forms.
- Sticky completion action only when it does not obscure content and remains visible with the keyboard.
- Visibility appears near completion.

### Expanded

- Form width at most 720 px.
- Optional preview or contextual information in a secondary pane.
- Sidebar is not a dumping ground for required fields.

**Order:** title → main content → date/metadata → media → visibility → completion.

**Required states:** validation error, upload running/missing, unsaved changes, offline write attempt with **„Noch nicht gespeichert“**, save failure.

## 10. Template: Authentication and Invitation

**Purpose:** Secure, understandable entry and connection with a partner.

### All sizes

- One focused flow without regular primary navigation.
- Value and Privacy context before sensitive input.
- Progress indicator only when the flow is genuinely multi-step.
- Invitation can be deferred or resent.
- Individual use remains possible where the product concept allows it.

### Expanded

- Form remains in a narrow reading column.
- Optional illustration may support atmosphere but carries no required information.

**Required states:** link expired, Account exists, wrong person, Invitation pending, connection successful.

## 11. Template: Detail View

**Purpose:** Read, edit, share, or manage one object.

### Compact

- Title, visibility, and most important metadata appear before the content.
- Secondary actions live in Overflow; Edit remains visible when frequent.
- Back returns to the prior list with context preserved.

### Expanded

- May appear as second or third pane.
- Direct URL and Browser Back remain correct.
- Very extensive content switches to a full page.

**Required states:** not found, no permission, stale, conflict, deleted.

## 12. Template: System states

### Empty

- Title names the state.
- One sentence explains value or cause.
- One primary action leads to the next meaningful step.
- Illustration is optional and purely supportive.

### Error

- Existing content remains visible where possible.
- Error message explains impact and next step.
- Retry appears only when technically meaningful.
- Support/diagnostic code is copyable but visually secondary.

### Offline

- Global status appears compactly in the Shell.
- Affected write actions explain that they were not saved. A safe form draft may be retained but is not a domain object.
- Reconnecting refreshes the read cache; another write attempt in the MVP happens deliberately and not through a local Outbox.

### No Permission

- Explains the missing permission and alternative.
- If a system permission is permanently blocked, links to the appropriate system settings.
- No repeated automatic reopening of the system permission prompt.

## 13. Responsive behavior

- Order follows meaning, not desktop position.
- Two panes become two navigable pages on Compact.
- Supporting content follows the main content on Compact or opens contextually.
- Tables become Lists/Details when horizontal scrolling would obstruct the core task.
- Actions keep the same semantic naming at all sizes.
- Layout changes do not move focus unexpectedly.
- Draft, selection, and scroll context remain across orientation or window changes.

## 14. Acceptance checklist per screen

- Page title and navigation context are unambiguous.
- At most one visually dominant action exists.
- Compact, Medium, and Expanded behavior are defined.
- Browser Back, App Back, and Deep Link behavior work.
- Loading, Empty, Error, Offline, and Success are designed.
- Privacy, Permission, and Sync states are visible.
- Keyboard, focus, screen reader, and 200% text zoom are verified.
- Touch targets and contrast meet the shared requirements.
- Analytics capture only necessary non-sensitive events.

## Related documents

- [Design Principles](./DESIGN-PRINCIPLES.md)
- [Information Architecture](./INFORMATION-ARCHITECTURE.md)
- [UX Patterns](./UX-PATTERNS.md)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Design Tokens](../design/tokens.json)
- [Critical User Flows](./USER-FLOWS.md)
- [Accessibility and QA Matrix](./ACCESSIBILITY-QA-MATRIX.md)
