# Design Principles for SideBySide Next

**Status:** Mandatory foundation for Web and App  
**Version:** 1.0  
**Effective from:** August 24, 2026  
**Brand promise (de-DE):** *Gemeinsam leben. Privat verbunden.*

This document translates the SideBySide Next product idea into mandatory
design rules. It applies to product surfaces, the website, store listings,
marketing pages, and new features.

The terms **MUST**, **SHOULD**, and **MAY** describe the requirement level.
When requirements conflict, use this priority order:

1. privacy and security
2. accessibility
3. comprehensibility and usability
4. consistency
5. brand impact
6. visual novelty

## 1. Design goal

SideBySide should feel like a calm, private space for two people: warm,
personal, and high-quality, but never kitschy or overloaded.

Every surface answers these questions within a few seconds:

- Where am I?
- What is shared here and what is private?
- What is the next meaningful step?
- Which data or permissions are affected?

## 2. Ten core principles

### 2.1 Calm before stimulation

The surface MUST support the content rather than compete with it.

- Each view has at most one dominant primary action.
- Decoration supports orientation or mood; it is not an end in itself.
- Whitespace is an active part of the layout.
- Persistent animations, aggressive banners, and unnecessary badges are not allowed.

### 2.2 Privacy is a visible product state

Privacy must not be explained only in policies. It MUST be directly visible at
the point where data is created or shared.

- States use clear labels. Intentional de-DE product examples are **Nur für mich**, **Mit Partner teilen**, and **Standort aus**.
- Visibility is always represented with text and an icon, never with color alone.
- Permissions are requested only in the context where they are needed.
- Security and encryption claims may be used only when they are technically and
  operationally demonstrated in the production build.
- No E2EE claim is allowed without verified end-to-end encryption.

### 2.3 Designed for two, not for a social network

The Space and the relationship take precedence over profiles, reach, or public
self-presentation.

- Shared context is always recognizable in navigation and language.
- There are no public rankings, follower mechanics, or social pressure.
- Recommendations optimize for shared relevance rather than maximum dwell time.
- Both people receive equal control and understandable state information.

### 2.4 One clear next step

Every view MUST have an unambiguous visual hierarchy.

- The title explains the context.
- A short subtitle explains the value.
- The primary action is visually unambiguous.
- Secondary actions recede visually.
- Complex flows are split into small, reversible steps.

### 2.5 Content is the hero

Memories, wishes, plans, and shared moments are visually central.

- Cards show the relevant content first and metadata afterward.
- Real content replaces generic placeholders as early as possible.
- Images are cropped calmly and are never overloaded with text.
- Empty states explain the value and the next step, not merely the absence of data.

### 2.6 Progressive disclosure

The first level stays simple; details appear when needed.

- Rare options belong in details, menus, or a second step.
- Critical states and privacy information must not be hidden.
- Forms request only information required for the current step.
- Advanced settings retain understandable defaults.

### 2.7 Human, respectful language

Language is direct, warm, and non-judgmental.

- In de-DE product copy, prefer “ihr”, “euer”, “gemeinsam”, and concrete verbs.
- Do not use guilt mechanics, artificial urgency, or dark patterns.
- Error messages explain what happened and what the user can do next.
- Copy promises only capabilities available in the current product state.

### 2.8 Accessibility is Definition of Done

Accessibility is not a later optimization.

- The target standard is WCAG 2.2 AA.
- Body text reaches at least 4.5:1 contrast; large text and UI graphics reach 3:1.
- Color is never the only information carrier.
- Web surfaces are fully operable by keyboard.
- App surfaces support screen readers and text scaling to at least 200%.
- Touch targets are at least 48 × 48 dp; Web targets are at least 44 × 44 px.
- Reduced motion and sufficient focus indicators are supported.

### 2.9 One language across platforms

Web and App share semantics, tone, tokens, and component logic.

- The same function uses the same name and color role.
- Platform conventions take precedence over pixel-level equality.
- Android remains Android; Web remains Web.
- New one-off components are allowed only when existing patterns are insufficient.

### 2.10 Motion explains change

Motion supports orientation and feedback.

- Standard transitions last 160–220 ms.
- Larger context changes may last up to 320 ms.
- Animations use calm ease-out behavior without strong bouncing.
- Success, synchronization, and state changes are confirmed subtly.
- Decorative motion stops automatically and respects “Reduce Motion”.

## 3. Visual language

### 3.1 Color semantics

Colors are used according to meaning, not according to the preference of an
individual view.

| Token | Value | Meaning |
|---|---:|---|
| Background | `#FAF8FC` | warm, calm page background |
| Surface | `#FFFFFF` | cards, dialogs, and content surfaces |
| Ink | `#211A2B` | primary text and strong contrast |
| Muted | `#6F6878` | secondary text |
| Line | `#E6DFEC` | dividers and subtle borders |
| Brand Purple | `#7C4DFF` | product core and primary action |
| Brand Soft | `#EEE7FF` | active or highlighted surfaces |
| Shared Mint | `#36AE97` | shared, confirmed, synchronized |
| Info Blue | `#4B96E6` | system information and technical context |
| Discovery Yellow | `#E8A932` | inspiration, options, and discovery |
| Private Pink | `#F45B88` | private, restricted, or owner-only |
| Dark Background | `#1C1525` | high-quality dark hero and focus surfaces |
| Dark Surface | `#2A2135` | cards in Dark Mode |

Mandatory rules:

- Purple is the only standard color for primary actions.
- Mint means shared, synchronized, or positively confirmed.
- Pink marks privacy or restriction, not automatically an error.
- Errors and destructive actions additionally require a clear warning icon and
  unambiguous text.
- Pastel surfaces may be combined only with sufficiently dark text.
- At most two accent colors SHOULD dominate a view.

### 3.2 Typography

At most two font families are used:

- **Display:** Fraunces 600 for emotional hero titles and selected Story moments.
- **UI:** Inter 400/500/600 for navigation, content, forms, and controls.
- Fallbacks: `Georgia, serif` and
  `system-ui, -apple-system, Segoe UI, sans-serif`, respectively.

| Level | Mobile | Web | Use |
|---|---:|---:|---|
| Display | 32/38 | 44/52 | hero and special chapters |
| H1 | 28/34 | 36/44 | page titles |
| H2 | 24/30 | 28/36 | section titles |
| Title | 20/26 | 20/26 | cards and dialogs |
| Body | 16/24 | 16/24 | standard text |
| Meta | 13/18 | 13/18 | date, status, and helper text |

- Body text is never smaller than 16 px or 16 sp, respectively.
- Long-form text uses at most 70 characters per line.
- All-caps is allowed only for very short labels.
- Numbers, times, and status values use tabular figures.

### 3.3 Spacing and grid

The base unit is a 4-unit grid.

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`

- Mobile page margins: at least 20 dp.
- Web page margins: 24–64 px depending on the viewport.
- Maximum content width: 1200 px; reading text is limited to 720 px.
- Standard spacing inside a card: 20–24 px.
- Related elements are closer together than separate sections.
- Web layouts switch to one column below 768 px.

### 3.4 Shape and depth

- Standard card radius: 20 px/dp.
- Large hero surfaces and modal surfaces: 24–32 px/dp.
- Buttons: 14–16 px/dp; pills are reserved for filters and compact status values.
- Shadows remain soft and shallow; surface and line differences are preferred for boundaries.
- Avoid more than two visible depth levels per view.

### 3.5 Imagery and illustration

- Imagery is soft, tactile, calm, and slightly dreamlike.
- Suitable motifs include paths, memory objects, nature, light, and small everyday moments.
- Do not use interchangeable stock couples or over-staged romance.
- 3D objects may provide orientation and brand warmth but must not obscure UI.
- Screenshots show real, readable UI and at most one central message.
- Images have alt text; purely decorative images are hidden from assistive technology.

## 4. Component rules

### Buttons

- Each view has at most one visually dominant primary action.
- Primary: Purple surface, white text.
- Secondary: light Surface with a clear outline.
- Tertiary: text action without its own surface.
- Destructive: unambiguous warning text; never communicate destructiveness through red alone.
- Loading states retain their width and labeling context.

### Cards

A card contains information in this order:

1. context or status
2. title
3. central information
4. optional metadata
5. at most one direct primary action

Avoid nested cards.

### Navigation

- Mobile primary navigation contains at most five primary destinations.
- Web navigation remains shallow and clearly indicates the current location.
- A localized “Back” action and Close must not acquire the same meaning. For de-DE, “Zurück” is the corresponding product label.
- Deep links always lead into an understandable context.

### Privacy and sharing control

- Every shareable entity displays its current visibility state.
- Changes explain their effect before confirmation.
- Private content is not leaked into previews, notifications, or analytics.
- Location is off by default and activated only in context.

### Feedback and system states

Every asynchronous action needs a visible state:

`idle → loading → success | empty | error | offline`

- Optimistic updates are allowed only for reversible, non-critical actions.
- Saving and synchronizing are communicated as distinct states.
- Offline states explain what remains available locally.
- Errors do not remove content the user already entered.

## 5. Responsive behavior

### App

- Mobile-first with one-handed core actions.
- System bars, insets, and the keyboard are accounted for.
- Primary actions remain reachable without covering content.
- Large image surfaces load progressively with a stable placeholder.

### Web

- Viewports from 320 px through 1440+ px are supported.
- One column on mobile, up to two content zones on desktop.
- Hover may add information but is never required.
- Dialogs become bottom sheets or full-screen steps on small viewports.
- Focus order follows the visible reading order.

## 6. Content and claim rules

- Lead with value before feature names.
- Use one sentence per core message.
- Do not use rankings, prices, user counts, or security claims without a reliable source.
- The de-DE product claims “Verschlüsselt übertragen” and “Ende-zu-Ende verschlüsselt” are not interchangeable.
- Privacy copy states the concrete effect instead of relying on abstract promises.
- Copy must work in German and English without breaking the layout.

## 7. Design Definition of Done

A surface is complete only when every item is satisfied:

- [ ] The primary goal and next action are understandable within five seconds.
- [ ] Private and shared states are unambiguous.
- [ ] All default, empty, loading, error, and offline states are designed.
- [ ] Contrast, text scaling, keyboard operation, and screen-reader behavior were reviewed.
- [ ] Touch and click targets meet the minimum size.
- [ ] Responsive behavior was reviewed on small and large viewports.
- [ ] Copy is concrete, respectful, and claim-safe.
- [ ] Components and tokens come from the shared design system.
- [ ] Motion respects reduced-motion preferences.
- [ ] Screenshots and marketing representation match the actual product state.

## 8. Governance

- Design tokens are the shared source for Web and App.
- Deviations are documented and decided with Product, Design, and Engineering.
- New components require at least usage guidance, states, accessibility rules, and tokens.
- Recurring special cases are moved into the design system.
- This document is versioned and updated for every substantial brand, privacy, or navigation change.
