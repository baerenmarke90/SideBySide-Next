# M5 Android Delivery Plan

- **Parent issue:** #350
- **Scope:** Android only; Web is delivered separately under #295
- **Gate:** M5/G4 remains dependent on completed M4 and the full cross-platform
  evidence set
- **Binding sources:** `specification/CLEAN-ROOM-MASTER-SPEC.md`,
  `docs/ROADMAP.md`, `docs/DESIGN-PRINCIPLES.md`, `docs/DESIGN-TOKEN-POLICY.md`,
  `docs/SCREEN-TEMPLATES.md`, `docs/INFORMATION-ARCHITECTURE.md`,
  `docs/ACCESSIBILITY-QA-MATRIX.md`, `docs/CROSS-CUTTING-QUALITY.md`,
  `docs/m5/S6-CACHE-PORTABILITY-DECISIONS.md`

## Starting position

Android is still the M2-S8 thin vertical reference flow. The whole client is one
package, `de.sidebyside.next.reference`, with a single screen, a build-time
Space ID, and a Material 3 colour scheme whose values are written as literal
`Color(0x…)` constants rather than derived from the shared token set.

Product copy already lives in `res/values/strings.xml` and is read through
`stringResource`, so the resource layer exists. What is missing is a locale
strategy and product language: the default resource folder holds German, there
is no second locale and no `localeConfig`, and the copy is written in M2/G2
engineering terms: the entry screen names the milestone and the engineering
slice instead of the product. There is no spacing, radius, typography, or
elevation token layer at all, and `res/values/colors.xml` is empty while the
launcher theme repeats the background and ink values as literals.

That slice was deliberately thin and remains valid as G2 evidence. It is not a
foundation for product screens, and this plan does not treat it as one. The
reference flow keeps working until the product surfaces that replace it are
delivered; no slice removes G2 evidence before its replacement exists.

Web has meanwhile been productized through S0A-S6. Android therefore starts from
a ratified target picture rather than an open design question, which is why this
plan mirrors the Web sequence instead of inventing a second one.

## Delivery sequence

```text
S0A Design foundation + product entry (#351)
  |
  v
S0B App shell + navigation + shared states (#352)
  |
  v
S1 Identity + relationship context (#353)
  |
  +--> S2 Memories + Story (#354)
  +--> S3 Shared planning (#355)
  +--> S4 Private Area (#356)
  +--> S5 Stable M4 Android surfaces (#357)
  |
  v
S6 Android runtime: Deep Links + encrypted Read Cache + portability UI (#328)
  |
  v
M5 Android evidence -> combined M5/G4 parity and release evidence
```

S2-S5 may use controlled parallelism only after S0B and the required S1 Space
context are delivered. Two branches must not independently redefine the
destination registry, cache key policy, error mapping, generated client, or the
token layer.

S6 consumes the same M2-D17/M2-D18 decisions frozen by #303 and the Transfer
Bundle contract owned by #345. Android must not create a competing archive or
transport contract while #345 is unmerged.

## Slice contracts

### S0A — Design foundation and product entry (#351)

- a real semantic token layer derived from `design/tokens.json`, replacing the
  literal colour constants, and the Material 3 scheme built from it;
- typography, spacing, shape, and elevation as named semantic values;
- independently authored Android brand primitives;
- product entry surfaces (welcome and sign-in) in the product language, not in
  M2/G2 engineering terminology;
- product entry copy rewritten from M2/G2 engineering terms into product
  language, and a recorded decision on the locale strategy (default resource
  folder, supported locales, `localeConfig`);
- appearance behaviour for light, dark, and system, plus dynamic type,
  TalkBack names, touch targets, and contrast;
- no Domain behaviour, no navigation graph, and no new dependency.

### S0B — App shell, navigation, and shared states (#352)

- the destination registry, Bottom Navigation for compact and Navigation Rail
  for medium windows, per `docs/SCREEN-TEMPLATES.md` section 1;
- System Back with the domain behaviour required by
  `docs/INFORMATION-ARCHITECTURE.md` section 206;
- shared loading, empty, error, permission, conflict, rate-limit, and offline
  presentation;
- stable ProblemDetails mapping and a top-level error boundary;
- Deep-Link-safe destination identity prepared, without activating S6 links;
- no dead or future-contract navigation.

**Open question this slice must resolve, not defer:** the canonical route model
in `docs/INFORMATION-ARCHITECTURE.md` section 5 (`today`, `story`, `plan`,
`discover`, `more`) does not match the destinations the Web client actually
ships (`story`, `planning`, `dashboard`, `search`, `activity`, `notifications`,
`people`, `profile`). Android must not silently pick one side. S0B has to route
this through an explicit decision that either updates the binding IA document or
realigns both clients; otherwise the M5 parity gate inherits a contradiction.

### S1 — Identity and relationship (#353)

- real session handling and authorized Space context;
- supported sign-in and recovery paths, Space, Invitation, Account/Profile,
  PartnerProfile, ProfilePreference, RelatedPerson, ImportantDate;
- remove the build-time reference Space ID from normal product behaviour;
- integrate #65 for the explicit RelatedPerson delete policy.

### S2 — Memories and Story (#354)

- complete Memory, image Attachment, HeartMoment, Milestone, Comment, and Story
  screens;
- author- and capability-aware actions and If-Match conflicts;
- separate owner view for private HeartMoments;
- video stays unavailable while the server rejects it fail-closed.

### S3 — Shared planning (#355)

- Wish, Plan, Place, Chapter, typed Relations, shared Collection, and Item UI;
- server-authoritative transitions and exact-set reorder contracts;
- no Maps, Shopping, provider, or automation scope.

### S4 — Private Area (#356)

- PrivateNote, GiftIdea, PrivateCollection, and Item UI;
- owner- and Space-bound cache keys with complete account/Space isolation;
- no partner counts, requests, navigation state, previews, or error differences
  that disclose owner-only existence.

### S5 — Stable M4 Android surfaces (#357)

- Search, Dashboard, Activity, in-app Notifications, unread count, mark-one and
  mark-all against contracts already merged to `main`;
- Thinking-of-you, Push, Reminders, and Rules enter later scoped work only after
  their owning contracts merge;
- no mock DTOs or speculative destinations.

### S6 — Read Cache, Deep Links, and portability (#328)

Owned by #328 and bound by #303. Android may persist current-owner `OWNER_ONLY`
data only behind Room plus an Android Keystore-protected encryption key, with
the seven-day maximum age, complete clearing on logout and Account or Space
change, no Offline Write, and cache fallback only for availability failures —
never for 401, 403, 404, or 409.

## Android-specific concerns not present on Web

These have no Web counterpart and must be owned explicitly rather than
discovered late:

- **Process death and state restoration.** Saved state must survive process
  death without leaking tokens or ProtectedPayload into saved instance state.
- **Token storage.** Tokens stay in memory for S0A-S1. Any persistence needs the
  Keystore boundary frozen by #303 and its own decision.
- **Screenshot and recents exposure.** Owner-only surfaces must decide their
  `FLAG_SECURE` and recents-preview behaviour before S4.
- **Background and lifecycle.** Requests must not continue against a stale
  Account or Space after a switch.
- **Configuration change and window size classes.** Compact, medium, and
  expanded behaviour per `docs/SCREEN-TEMPLATES.md`, including foldables.
- **Release identity.** The application ID is still
  `de.sidebyside.next.reference`, versioned `0.0.1-m2-s8`. The final identity,
  versioning, and signing strategy are owned by #194 and must land before any
  distribution build.
- **Generated client gap.** The build excludes two generator-owned Passkey
  request models from the compile copy because `Map<String, Any>` has no
  concrete kotlinx.serialization serializer. #138 owns the generator fix; any
  slice that needs Passkey registration or authentication is blocked on it.
- **Dependency verification.** `android/gradle/verification-metadata.xml` is
  enforced in strict mode. Every added dependency requires verified checksums in
  the same change, which is a further reason to prefer platform capabilities.

## Reuse-before-build decision

Selected foundations:

- Jetpack Compose and Material 3 for composition, theming, and accessibility
  semantics;
- Compose `CompositionLocal` for the semantic token layer;
- Android string, plural, and configuration resources for all product copy and
  locale behaviour;
- the generated OpenAPI Kotlin models as the DTO and transport authority;
- OkHttp and kotlinx.serialization, already present and verified;
- the existing Robolectric-free unit and Compose semantics test strategy;
- Room plus Android Keystore for the bounded S6 read cache under M2-D18.

Alternatives considered for S0A: a third-party design-system or component
library, an icon dependency, a font dependency, a dependency-injection
framework, and a separate screenshot-testing harness. None is selected. S0A has
a bounded surface, Material 3 already provides the required theming and
semantics, and each option would add licence, size, maintenance, and
dependency-verification cost without closing a current gap. Navigation, image
loading, and persistence get their own reuse decisions in the slice that first
needs them, when the requirements are concrete rather than assumed.

## Business and freemium result

- official Android access and standard light, dark, and system appearance:
  Free/Core;
- accessibility, localization, account security, Privacy enforcement, cache
  isolation, and essential data portability: non-paywallable;
- basic offline read access to supported Core cached data: Free/Core;
- implemented M1-M3 capabilities keep their authoritative Free/Core or
  documented Mixed baseline;
- no Android slice may add ad-hoc Premium flags or infer entitlement in the
  client;
- M9/#262 remains the entitlement runtime boundary.

## Cross-cutting acceptance for every production screen

- localized default, loading, content, first-use empty, filtered empty,
  validation, 401, Privacy-safe 404, 409, 429, 5xx, and relevant offline states;
- semantic headings, merged and meaningful TalkBack names, visible focus, 48 dp
  targets, 200 percent font scaling, reduced motion, and screen-reader status
  announcements;
- authorization-first requests and cache keys that carry Account and Space
  context wherever data isolation requires it;
- no ProtectedPayload, token, filename, private title, or sensitive content in
  logs, crash metadata, saved instance state, or generic errors;
- generated client and API contract stay synchronized;
- representative window-size, long-text, negative and privacy, and retry and
  conflict tests;
- complete Business/Freemium, Reuse, and Cross-Cutting Quality review in the
  owning pull request.
