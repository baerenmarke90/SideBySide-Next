# SideBySide Partner-App Experience Standard

**Status:** Mandatory product UI standard  
**Version:** 1.1  
**Effective from:** September 2, 2026

This document is binding for every user-facing Web and Android change. It complements `DESIGN-PRINCIPLES.md`, `UX-PATTERNS.md`, `SCREEN-TEMPLATES.md`, `COMPONENT-CONTRACTS.md`, and `DESIGN-SYSTEM-DELIVERY.md`.

SideBySide is not a generic productivity tool, admin console, CRM, spreadsheet, or CRUD frontend. It is a private digital place for two people. Functional correctness is necessary but not sufficient: a client feature is incomplete when it feels like database administration with nicer colors.

## 1. Product character

Every couple-facing surface MUST feel:

- warm, private, calm, and personal;
- lively and modern without becoming noisy, trendy for its own sake, or visually cold;
- beautiful and intentionally crafted rather than assembled from generic boxes;
- emotionally aware without becoming kitschy;
- gently playful where the relationship context allows it;
- content-led rather than metadata-led;
- alive through restrained motion, feedback, and small moments of delight;
- safe and understandable when privacy or relationship data is involved.

The visual direction is **warm editorial intimacy**: soft layered surfaces, generous whitespace, meaningful typography, relationship context, tactile media, subtle gradients or glow where appropriate, carefully chosen illustrations or symbols, and motion that makes state changes feel intentional.

Modern does **not** mean sterile. Clean layouts must retain warmth through typography, spacing, imagery, surface treatment, microcopy, relationship context, and subtle movement.

## 2. The anti-admin rule

Couple-facing product surfaces MUST NOT default to admin-console or spreadsheet composition.

The following are prohibited as the primary presentation of normal relationship content unless a specific product decision justifies them:

- dense data tables;
- repeated bordered rows containing mostly labels and metadata;
- equal-sized dashboard tiles used only because data can be grouped into boxes;
- deeply nested cards;
- forms presented as uncomposed field stacks with no hierarchy or context;
- large blank grids of generic white rectangles;
- persistent technical identifiers, raw enum values, API terminology, or operational metadata;
- a screen whose dominant visual structure could be reused unchanged for invoices, inventory, or server administration.

Tables remain valid for genuinely tabular administration surfaces such as ServerAdmin when comparison across columns is the task. They are not the default for couple-facing content.

## 3. Required emotional focal point

Every primary couple-facing screen MUST have one recognizable focal point. Depending on the feature this can be:

- a memory or photo;
- the partner/relationship context;
- a meaningful next action;
- a highlighted wish, plan, question, note, or milestone;
- a small relationship message or shared moment;
- a calm empty-state composition that explains why the feature matters.

A page title followed by a uniform grid of records is not a sufficient focal point.

The first viewport SHOULD communicate the human value of the screen before secondary metadata.

## 4. Warmth, beauty, and gentle playfulness

SideBySide SHOULD feel noticeably warmer and more alive than a neutral productivity application while remaining mature and usable.

### Required characteristics

- Surfaces use soft contrast and layered depth instead of hard separators everywhere.
- Rounded shapes, spacing, media, typography, and accent surfaces SHOULD make important relationship content feel tactile and inviting.
- Small decorative details MAY appear around emotionally meaningful content when they do not compete with the task.
- Illustrations, icons, gradients, glow, confetti-like particles, floating hearts, sparkles, handwritten accents, or similar playful devices MAY be used selectively for delight moments.
- Playfulness must remain **lightweight and contextual**. It is not a permanent visual layer across every screen.
- Dense settings, privacy, consent, conflict, error, and destructive flows become calmer and more restrained rather than playful.

### Avoid

- corporate dashboard aesthetics as the default product language;
- cold monochrome layouts with no relationship context;
- exaggerated pink/red romance branding across all surfaces;
- childish illustrations or game-like decoration where intimacy, privacy, or seriousness is required;
- visual clutter created only to make a screen look less empty.

The target is **adult, affectionate, modern, warm, and lightly playful**.

## 5. Surface hierarchy

Use no more surface layers than needed. A typical screen should read as:

1. ambient canvas/background;
2. relationship or page context;
3. one primary content composition;
4. secondary/supporting content;
5. actions and transient feedback.

Prefer spacing, typography, grouping, image treatment, and subtle tonal surfaces over borders around everything.

Cards are reserved for meaningful content units. A section does not need a card merely because it has a heading.

## 6. Typography and content presentation

- Editorial/display typography is used selectively for emotionally meaningful moments, Story, memories, invitations, recaps, milestones, and other relationship-led surfaces.
- Standard UI typography remains the default for forms, settings, navigation, and dense controls.
- Content titles and user-created text outrank timestamps, statuses, IDs, and technical metadata.
- Metadata is visually quiet and grouped instead of repeated as separate rows.
- Empty states contain a human explanation and one meaningful action; they are not bare `No items` panels.
- Copy may be affectionate, warm, and lightly playful where context allows, but it must never assume a specific relationship style, gender role, sexuality, mood, or level of intimacy.

## 7. Love messages and relationship microcopy

Small relationship-oriented messages are a first-class product device. They help SideBySide feel like a shared place instead of a record-management tool.

Suitable surfaces include:

- Today/home;
- invitations and partner connection;
- HeartMoments and love notes;
- shared achievements;
- recaps and anniversaries;
- successful completion of a shared plan;
- meaningful empty states;
- occasional non-intrusive return moments.

Examples of the **type** of message, not mandatory literal copy:

- a short reminder that something belongs to both partners;
- a small thank-you or appreciation prompt;
- a celebratory line after a shared milestone;
- a gentle invitation to leave the partner a note;
- a small contextual message such as “Für euch”, “Ein kleiner Moment für euch” or equivalent localized language.

Rules:

- Love messages MUST be localization-driven and context-sensitive.
- They SHOULD be short enough to feel spontaneous rather than like marketing copy.
- They MUST NOT guilt users into engagement or imply relationship problems.
- They MUST NOT become repetitive banners on every screen.
- Sensitive features must not expose private content through decorative previews or notifications.
- User-created messages outrank generated/system relationship copy whenever both compete for attention.

## 8. Motion is part of the feature

Motion is a product behavior, not optional polish added after implementation.

Every new or materially changed client feature MUST define the relevant motion/feedback behavior and reduced-motion fallback.

### Standard motion language

- **Micro feedback:** 120-180 ms for press, selection, icon, and compact state feedback.
- **Component transition:** 160-240 ms for cards, sheets, expansion, filtering, reordering, and local state changes.
- **Context transition:** 220-320 ms for page/pane changes and larger hierarchy changes.
- Use calm ease-out/ease-in-out curves from design tokens. Avoid aggressive bounce, elastic motion, or constant animation.
- Elements may use subtle opacity plus 4-12 px translation or small scale changes when this clarifies causality.
- Drag-and-drop MUST visibly lift, move, settle, and confirm state; disappearing and reappearing in another list is insufficient.
- Hover, press, selection, successful save, completed actions, and newly revealed relationship content SHOULD feel responsive rather than switching abruptly.

### Emotional micro-interactions

Features such as `Thinking of you`, invitations, love notes, HeartMoments, shared achievements, recaps, and relationship milestones MAY use a short one-shot delight animation. It MUST:

- be non-blocking;
- end automatically;
- preserve the visible result after the animation;
- avoid repeated attention-seeking loops;
- respect reduced-motion settings;
- never communicate essential information through motion alone.

Appropriate examples include a subtle heart pulse, tiny particles, soft glow, short card lift, gentle reveal, or restrained celebratory motion. These effects SHOULD feel charming and intentional, not like a mobile game reward loop.

Haptics may supplement visible feedback on supported mobile devices but never replace it.

## 9. Feature composition requirements

Before implementing a new user-facing feature, the issue or PR MUST identify:

1. the owning Screen Template or explain why no existing template fits;
2. the existing design-system components/patterns that will be reused;
3. the primary emotional or content focal point;
4. the primary action and visual hierarchy;
5. how the feature stays warm, modern, lively, and appropriate to a partner app;
6. whether relationship microcopy, playful detail, or a delight moment is appropriate;
7. Compact and Expanded behavior;
8. Loading, Empty, Error, Offline, and Success behavior where applicable;
9. motion/feedback behavior, including reduced motion;
10. privacy/relationship-state presentation where applicable.

`Functionality first, design later` is not an acceptable delivery strategy for product UI. The first mergeable implementation must already use the shared product language.

## 10. Responsive composition

Responsive behavior is composition, not shrinking.

### Compact

- one dominant task at a time;
- strong content focus;
- bottom sheets/pages instead of dense multi-column controls;
- important actions remain reachable with one hand;
- horizontal scrolling is not used to hide primary navigation or core content.

### Expanded

- use width to add context, richer media, list-detail behavior, or supporting content;
- do not fill available width with more equal boxes merely because space exists;
- reading text stays bounded;
- side rails contain supporting information, not required form fields dumped out of the main flow.

## 11. Visual evidence is required

A PR that changes couple-facing Web or Android UI MUST include visual evidence for review.

Minimum evidence:

- at least one representative Compact state;
- at least one representative Expanded/Web state when the feature exists on Web;
- Light and Dark when theme-sensitive styling changed;
- any important interaction state that cannot be understood from a static default screenshot.

Evidence may be screenshots, a short recording, or stable visual-test output. A textual statement that the UI was reviewed is not sufficient by itself.

## 12. Review questions

A couple-facing surface is not merge-ready if any answer below is `no`:

- Does this look and feel like a private partner app rather than generic business software?
- Does it feel warm, modern, beautiful, and alive rather than cold or sterile?
- Is the human content more prominent than the data model?
- Is there one clear focal point and one dominant next action?
- Is there an appropriate amount of gentle playfulness or relationship personality for this context?
- If a small love message or delight moment would improve the experience, has it been considered deliberately?
- Could at least one generic box/border be removed without losing hierarchy?
- Are privacy and shared context visible where they matter?
- Does the layout intentionally adapt between Compact and Expanded?
- Does interaction have appropriate subtle motion or feedback?
- Does reduced motion remain fully understandable?
- Are design-system tokens/components reused instead of local visual inventions?
- Is visual evidence available for review?

## 13. Exceptions

Administration, diagnostics, migration, and operational tools may legitimately use denser information design. An exception MUST be explicit in the PR and MUST not leak that visual language into couple-facing product surfaces.

Accessibility, privacy, security, comprehensibility, and platform conventions always take precedence over decorative treatment.

## Related documents

- [Design Principles](./DESIGN-PRINCIPLES.md)
- [UX Patterns](./UX-PATTERNS.md)
- [Screen Templates](./SCREEN-TEMPLATES.md)
- [Component Contracts](./COMPONENT-CONTRACTS.md)
- [Design System Delivery](./DESIGN-SYSTEM-DELIVERY.md)
- [Design Tokens](../design/tokens.json)
