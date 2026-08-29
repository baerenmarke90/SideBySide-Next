# Information Architecture for SideBySide Next

**Status:** Binding foundation for Web and App  
**Version:** 1.1  
**Effective from:** August 24, 2026

This document defines navigation, naming, routes, and product-function
assignment. Web and Android use the same domain architecture while adapting
navigation to window size and platform conventions.

## 1. Core rules

- The shared **Space** is the constant product context.
- Primary navigation contains no more than five destinations.
- A piece of content has exactly one domain home; cross-references are Deep
  Links.
- Routes represent tasks and content, not technical modules.
- Privacy classes do not change primary navigation; where a domain supports
  multiple classes, the status is shown directly on the content.
- Navigation must not discard unsaved input without warning.
- Web and App use the same terminology and stable route IDs.

## 2. Mandatory primary navigation

| Route ID | de-DE product name | Purpose |
|---|---|---|
| `today` | Heute | shared overview and next meaningful actions |
| `story` | Story | non-public shared timeline of memories |
| `plan` | Planen | wishes and concrete plans; shopping later |
| `discover` | Entdecken | curated inspiration for shared time |
| `more` | Mehr | Space, privacy, profile, and settings |

### Platform representation

- **Compact windows:** Bottom Navigation with icon and text label.
- **Medium windows:** Navigation Rail.
- **Large Web windows:** fixed sidebar with text labels; secondary targets may
  appear indented.
- Order remains identical on all platforms.
- Current area is recognizable through color, icon, and text state.

## 3. Structure tree

```text
SideBySide Next
├── Heute
│   ├── next shared moment
│   ├── personal and shared recommendations
│   ├── recaps
│   └── open tasks and notices
├── Story
│   ├── Timeline
│   ├── Erinnerung
│   │   ├── media
│   │   ├── place and date
│   │   ├── status "Geteilt"
│   │   └── editing
│   └── new memory
├── Planen
│   ├── Wünsche
│   │   ├── open
│   │   ├── planned
│   │   ├── completed
│   │   └── wish detail
│   ├── Pläne
│   │   ├── status
│   │   ├── date
│   │   ├── checklist
│   │   └── media and notes
│   └── Einkauf (later, feature-controlled)
├── Entdecken
│   ├── feed
│   ├── filters
│   ├── recommendation
│   └── convert into wish or plan
└── Mehr
    ├── Space and partner
    ├── privacy and permissions
    ├── notifications
    ├── profile and preferences
    ├── data export and account deletion
    └── help, legal, and app information
```

## 4. Planen as shared hub

`Planen` combines two closely related states in Core and keeps a future area
architecturally open:

1. **Wish:** an idea without a binding date.
2. **Plan:** a concretized idea with status, date, or tasks.
3. **Shopping (later):** an independent shopping domain, not a generic
   collection.

Wishes and plans must not appear as isolated data worlds. Converting a wish
into a plan is a visible, understandable state transition. Discover does not
create a fourth copy of content; it can adopt a recommendation as a wish or
plan.

### Secondary navigation

- Smartphone: initially segmented control or tabs **Wünsche | Pläne**; Shopping
  is added only with an implemented and enabled shopping domain.
- Web: same tabs inside the Planen area; large windows may use list plus detail
  pane.
- The last selected sub-area may be restored locally.
- Deep Links always open the concrete sub-area and content.

## 5. Route model

The following paths are canonical Web paths and the foundation for App Deep
Links. IDs are opaque, stable identifiers.

| Task | Canonical path |
|---|---|
| Open Heute | `/today` |
| Open Story | `/story` |
| Open memory | `/story/memories/:memoryId` |
| Create memory | `/story/memories/new` |
| Planen hub | `/plan` |
| Wishes | `/plan/wishes` |
| Open wish | `/plan/wishes/:wishId` |
| Plans | `/plan/plans` |
| Open plan | `/plan/plans/:planId` |
| Shopping reserved for later domain | `/plan/shopping` |
| Discover | `/discover` |
| Open recommendation | `/discover/:recommendationId` |
| More | `/more` |
| Space and partner | `/more/space` |
| Privacy | `/more/privacy` |
| Notifications | `/more/notifications` |
| Profile | `/more/profile` |
| Settings | `/more/settings` |
| Data and account | `/more/data-account` |

### Deep-Link rules

- Every detail item has a shareable internal Deep Link.
- A Deep Link validates authentication and Space membership before loading data.
- Unauthorized content is not confirmed as an existing resource.
- After login or invitation, the user returns to the originally requested
  destination.
- Deleted content receives an understandable state instead of a generic empty
  page.

## 6. Screen and pane behavior

| Content | Compact | Medium | Expanded |
|---|---|---|---|
| Story | list or detail | list or detail | timeline + detail |
| Wishes | list or detail | list or detail | list + detail |
| Plans | list or detail | list or detail | list + detail + optional support |
| Shopping, later | one list | list + optional recipe card | list + recipe/detail pane |
| Discover | feed + detail screen | feed + detail | grid/feed + detail pane |
| Settings | stacked pages | categorized page | categories + setting detail |

On small windows, detail replaces the list. On large windows, the list remains
visible and selected content appears beside it. Back state must survive window
size changes.

## 7. Naming and language

### Binding terms

| Domain term | UI name | Do not use |
|---|---|---|
| shared tenant | Space | Workspace, Tenant |
| relationship partner | Partner | Contact, User 2 |
| memory | Erinnerung | Post, Beitrag |
| wish | Wunsch | Bookmark, Favorite |
| concrete shared activity | Plan | Project, Task List |
| owner-only visibility | Nur für mich | Owner-only |
| Space visibility | Mit Partner teilen | Public, share with everyone |

- Technical terms remain outside end-user UI.
- Buttons use verbs: `Speichern`, `Teilen`, `Planen`, `Entfernen`.
- Navigation labels use nouns or established product names.
- German and English must work without different navigation structures.

## 8. Roles and visibility

Navigation is not permission. A visible area does not guarantee access to every
object within it.

### Privacy classes

| API value | Meaning | UI label |
|---|---|---|
| `OWNER_ONLY` | owner only | Nur für mich |
| `SPACE_SHARED` | both active Space members | Geteilt / Mit Partner teilen |
| `TEMPORARY_SHARED` | limited-time sharing | only after domain implementation |
| `EPHEMERAL_CONTEXT` | short-lived context with expiry | context-dependent |
| `SYSTEM_METADATA` | technical metadata | no regular UI label |

The UI may use `private` and `shared` as internal presentation states but sends
the domain API values. Not every domain supports selection: Memory, Wish, and
Plan are `SPACE_SHARED` in the current Core; HeartMoment may use `OWNER_ONLY`
or `SPACE_SHARED`. `public` is not a valid value.

## 9. URL, history, and back behavior

- Selection, filters, and relevant tabs are represented in URL or navigation
  state when they describe a restorable context.
- Short modal interactions create history entries only when they can be opened
  by Deep Link.
- Android System Back and Browser Back have the same domain behavior.
- Close ends a dialog; Back navigates history.
- Switching primary navigation does not create stacked detail history.

## 10. Open product decisions

Before M1, decide:

- Which content appears in notification previews?
- Can a recommendation become a plan directly, or only a wish first?
- Which filters persist between sessions?
- Which retention periods apply before Cloud launch for account and Space
  deletion?
- How is future partner removal represented? It is not part of MVP.

## 11. Acceptance criteria

- [ ] Every feature belongs to exactly one primary area.
- [ ] Web and App use identical route IDs and labels.
- [ ] Bottom Bar, Rail, and Sidebar use the same order.
- [ ] Detail routes support Deep Links.
- [ ] Authentication, membership, and deletion states are defined.
- [ ] Back behavior works across single- and multi-window layouts.
- [ ] Navigation remains operable with keyboard, screen reader, and text scaling.

## Related documents

- [Design Principles](DESIGN-PRINCIPLES.md)
- [UX Patterns](UX-PATTERNS.md)
- [Component Contracts](COMPONENT-CONTRACTS.md)
- [Screen Templates](SCREEN-TEMPLATES.md)
- [Critical User Flows](USER-FLOWS.md)
- [API/UI Contracts](API-UI-CONTRACTS.md)
