# F1 visual foundations — implementation and proof

**Owner:** [#957](https://github.com/baerenmarke90/eimir/issues/957), child of #955.  
**Authority:** [Product Reference v1](product-reference-v1.md), D1/D2/D7; [system direction](design-system-direction.md).  
**Status:** preflight recorded before UI implementation on 2026-09-15; evidence and delivered API are completed below with implementation.

## Live baseline and overlap

Start from `f1d3496d091c1823ad618748686f2c5eea068a50` (`origin/main`, merged #959). #955 and #957 were read with all comments; both had no comments. #953 and the identity migration are complete. The original checkout remains untouched; work uses `codex/957-visual-foundations` in an isolated worktree.

The live open-PR inventory has 18 entries: #763, #762, #339, #317, #234, #233, #232, #207, #157, #156, #142, #141, #140, #139, #136, #135, #133 and #132. Their `updatedAt` values match the file-level inventory reviewed for #959. No open design/token implementation competes with F1. #317 targets an older feature branch and touches App/Space context/localization; F1 does not alter that flow. Dependency PRs touching Android build configuration (#142/#141/#140/#139), Gradle (#207), Web manifests (#156/#136/#135/#133/#132), containers or workflows are not adopted here. Preserve their dependency versions and review any overlapping build-file hunks again before merge.

## Product Design Preflight and Mobile Interaction Contract

**User-facing UI / UX impact reviewed.** The full bounded Mobile Interaction Contract is recorded in #957. This implementation binds it to concrete consumers before UI code:

- Web: `web/e2e/fixtures/product-reference-foundations.html`, `.tsx` and `.css`, exercised by `web/e2e/tests/product-reference-foundations.spec.ts`. Vite serves the internal fixture in development; the production entry/router does not import it. Check the production build excludes it.
- Android: `android/app/src/debug/java/de/eimir/app/design/VisualRolesProofActivity.kt`, debug-only manifest/resources and `VisualRolesProofTest.kt`. Explicit developer launch only; no production navigation or release Activity. Copy the approved photo into generated debug assets, never release assets.
- Production consumers: Web `shell.css` and `product-reflow.css` consume the responsive gutter; existing Android `EimirTheme.spacing.pageMargin` consumers inherit the responsive adapter. The approximately 28 native consumers include some all-direction padding, so review their vertical spacing consequence as well.
- Templates: Story Timeline/Detail View for photo and text, Settings and Privacy for compact utility selection. This fixture creates no new Screen Template.
- Composition: a large photo and meaningful short title; a separate authored text memory with no photo hole; a small utility group. Photo/words → supporting audience/context → utility. One selected sample opens its own reading detail; Close/Back returns to the sample. Utility has real fixture selection/status behavior, not dead controls.
- Overlay: browser-native modal dialog and Compose Material 3 ModalBottomSheet demonstrate the raised role with a visible Close action. F1 does not introduce a reusable sheet lifecycle or change production navigation; F2 owns those mechanics.
- States: stable media loading; failed media retaining caption and retry; successful retry; text-only/absent-image composition; explicitly simulated cached/offline information and visible announced fixture completion. No domain save/sync promise.
- Privacy: synthetic text and the existing approved cabin photo only; shared/private meaning includes text/semantics. No accounts, real IDs, credentials, API, analytics or persisted fixture data.
- Mobile: 320 reflow plus 360/390/430 widths; 16-unit gutters below 390, 20 from 390 through Compact. Reading and targets grow with text; Web minimum 44, native 48. No autofocus or IME. Expanded adds reading/media room within a bounded measure, without a tile wall or permanent management controls.
- Warmth comes from the approved image, authored words, selective Literata and varied spacing. Utility remains Instrument Sans. No love-message banner or decorative delight animation is appropriate in this foundation proof.
- Motion uses existing fast/standard/emphasized durations and platform mechanics; reduced motion preserves content, status, focus and every action without nonessential translation/scale/shimmer.
- Acceptance includes actual interaction, focus/Back/return, contrast and layout measurements, Light/Dark screenshots, long labels, 200% text and reduced motion. Native host tests supplement device/emulator evidence, never substitute for it.

## Role and consumer decisions

| Purpose | Existing source / selected delivery | Constraint |
| --- | --- | --- |
| Bare page, reading, bounded content | `background`, `surface`, `surfaceSubtle`; semantic HTML/Compose layout | No universal Card component or mandatory border/shadow |
| Meaningful tint | Existing shared/private surfaces plus explicit audience text | No tint-only privacy signal |
| Elevated sheet | `surfaceRaised`, existing scrim/overlay depth and `radius.sheet` | Only a transient interaction layer |
| Photograph | Existing approved image; `radius.large`; no extra card padding | Caption below; full view contains complete image; failed differs from absent |
| Personal/content title | Existing heading2/heading3 metrics with existing display family | Selective Literata; long prose uses body, not display |
| Utility, reading, support | Existing heading2/heading3, body and bodySmall; UI family; `textSecondary` | Essential small text does not use failing Light `textMuted` |
| Links/selected text | Strong coral in Light, existing bright coral in Dark | Filled actions keep strong coral + onAccent in both themes |
| Radius and motion | Existing JSON scale via additive purpose roles | Legacy Web aliases have different values; no blanket consumer rewrite |
| Page gutter | Existing 16/20 spacing; one new narrow-gutter alias and 390 threshold | JSON owns values; both viewport/container and native adapters agree |

The Web adapter is currently manual and drift-tested; native generation omits layout/motion. A bounded deterministic adapter extension may emit the F1 values from JSON using existing Node/Gradle APIs. This is a mapping of the current token source, not a replacement token framework. Existing aliases remain compatible until their consumers migrate. Do not add duplicate palette/supporting-text values or one token per fixture margin.

## Current reuse review

Reviewed on 2026-09-15 before implementation:

- Standards/platform: [CSS media queries](https://www.w3.org/TR/mediaqueries-3/) express width-dependent spacing; [reduced-motion guidance](https://www.w3.org/WAI/WCAG21/Techniques/css/C39.html) preserves understandable changes without movement. [HTML dialog](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element) provides top-layer modality and background inertness for the controlled Web sample.
- Framework/native: [Compose window information](https://developer.android.com/reference/kotlin/androidx/compose/ui/platform/WindowInfo) supplies available window dimensions; [Material 3 sheets](https://developer.android.com/develop/ui/compose/components/bottom-sheets) supply established native overlay behavior. Reuse existing EimirTheme, fonts, Image/Text/Material controls and bounded image decoding.
- Existing Web: reuse MemoryPreview/VisibilityBadge/UiState where their actual behavior fits; keep recovery honest. Domain editors are too coupled to authorization/forms for this visual proof. Do not turn that rejection into a new shared overlay framework.
- Established OSS considered: [Style Dictionary](https://styledictionary.com/getting-started/installation/) is a general token transformation option. The existing JSON/Gradle boundary and a small deterministic Node mapping need no new package, configuration ecosystem or migration. Existing React, Playwright, axe, Compose and Robolectric remain at locked versions.
- External providers: none solve a missing requirement. Existing self-hosted fonts and checked-in approved demo media avoid image/font CDN requests, new accounts, keys, costs, rate limits or deletion obligations. `docs/EXTERNAL-PROVIDER-CANDIDATES.md` was reviewed; a media pipeline/provider is out of scope.

No new runtime dependency or service is selected. Existing React (MIT), AndroidX/Material, Playwright/Robolectric (Apache-2.0), axe (MPL-2.0) and OFL fonts keep their documented provenance/licensing. They support the same Cloud/Self-Hosted build with no new user/hoster configuration. Failure falls back to readable text and explicit retry. Existing build infrastructure owns dependency installation; no new production storage/cache/data transfer results.

Photo provenance: `backend/demo_assets/manifest.json`, `memory-cabin`, creator Darkmoon_Art, CC0 1.0 Universal, SHA-256 `6c734e84d199e3d2e38d9d51064ce5bdd741def0b842fe4fb5dbb20d8c0f7f8f`. Reuse these approved local bytes; no third-party image download or duplicate source asset is needed.

## Business/Freemium Model Consistency

**No business/freemium impact:** official clients, standard appearance and Memory/Timeline remain Free/Core under the versioned matrix; accessibility/i18n remain non-paywallable. This is the baseline design system, not Premium bespoke themes/covers. Space entitlements, ownership, quotas, storage, compute, provider costs, retention, downgrade/trial/grandfathering/restore/export and existing data are unchanged. Cloud and Self-Hosted receive the same behavior.

## Cross-cutting review

- Security/privacy: debug/test proof only, approved fixtures; no new production route, authentication, authorization, persistence, logs, analytics, or data lifecycle. Verify release/build exclusion.
- Accessibility/i18n: localized fixture resources, semantic headings and named controls, text plus privacy meaning, visible focus/Back/Close, contrast, large text/reflow and minimum targets. No automatic keyboard. Platform and RTL-aware padding semantics.
- Concurrency/resilience: no domain mutations. Ignore stale image completions/unmounts using existing lifecycle; stable pending/error/retry states preserve text. Offline fixture explains available read-only content.
- Performance: bounded single existing image, stable aspect ratio, bounded decoding, no new derivative/processing infrastructure or decorative loops. Responsive spacing responds to window changes without resetting sample state.
- Contracts/operations: additive token/adapter roles with reproducible generation; preserve legacy consumers and dependency versions. No API/DTO/database migration, backend runtime or deployment change.
- Validation: adapter/token contrast and drift tests, Web/native component behavior, production build exclusion, visual/reflow/large-text checks and relevant CI. Record real evidence and remaining limitations rather than checking unperformed gates.

## Delivery and evidence

Pending implementation and validation. F1 does not complete a reference-screen redesign, #955 or final product audit #946. Merge requires Product Owner approval.
