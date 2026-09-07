# Phase A1 — Shell/navigation rescue from #784

## Audit and scope decision (2026-09-07)

Live baseline: `main` at `a216c7a29c90fe80c3ca6c326243cf898e483200`;
#779 is merged into that baseline. Read-only source: #784 at
`62c9651f2c5245beb391a97a9eb5ca98f1f53dcd`, open, no submitted reviews
or inline review comments. Its engineering-language/reuse gates fail on a
hardcoded German browser-test assertion; browser failures also involve Today
composition and Planning zoom. None is automatically imported into A1.

- **KEEP:** horizontal primary header navigation, removal of the permanent
  sidebar, global header Quick Create, existing Search/Notifications/Profile,
  route identities and compact bottom navigation.
- **REDUCE:** integrate the shell presentation in `shell.css`; retain the
  existing 840px switch instead of introducing 960px plus transition overrides.
  Update existing component and browser behavior coverage.
- **DROP:** `AppShellB2.css` as a second override architecture,
  `AppShellB2.test.ts` source-string/CSS-regex tests, special B2 visual workflow,
  unrelated formatting churn, and the 88rem domain-content expansion.
- **DEFER:** every `TodayPage*` change, keepsake fallback/hierarchy, Planning
  horizon, Activity recomposition, Today translations and Today E2E changes.

Other open Web PRs: #317 changes App/Space selection and locale resources;
#763 changes artifact action versions; #762 and dependency PRs change build
inputs. No A1 runtime-file overlap except the deliberately read-only #784.
The Lists/Planning and Profile/Settings eimir branches have no remaining diff
against current main. The original workspace's Android edit is outside this
isolated checkout and outside this rescue.

## Product design before implementation

Owner: shared App Shell anatomy in Screen Templates §2 and Navigation Item in
Component Contracts §5.1. The user's explicit A1 direction replaces the older
Web sidebar prescription; destination IDs and the existing 840px breakpoint
remain stable. This is a shared shell change, not a Today template change.

Reuse Brand, PrimaryNavigationLinks/NavLink, DestinationIcon, QuickCreateMenu,
HeaderNotificationsMenu, HeaderProfileMenu, and existing semantic theme tokens.
Page content is the focal point; navigation is quiet horizontal orientation,
with an active underline and a compact global create trigger. Instrument Sans
remains the control typeface. Extra relationship copy/delight is unnecessary
in persistent chrome; existing eimir identity and content provide warmth.
Compact/Medium retain bottom navigation and the reachable create sheet.
Expanded uses header navigation and a bounded create popover. Long labels,
resize, keyboard focus, 200% reflow, Light/Dark and reduced motion need browser
verification. Existing hover/selection feedback uses motion tokens and the
reduced-motion fallback. Loading/Empty/Error/Offline/Success and private-area
presentation continue through existing components without new data semantics.

## Reuse and business review before implementation

Reuse review not relevant to new commodity infrastructure: this is composition
of existing product components and CSS, with no new dependency, provider or
platform integration. Alternatives were direct integration, #784's additional
CSS layer, or a replacement navigation library. Direct integration is smallest
and retains established route, accessibility and menu behavior. No third-party
license/ToS, configuration, data flow or cost is added.

**No business/freemium impact:** existing Free/Core navigation and creation
entry points retain their destinations and capability boundaries. No change to
Space ownership, Premium eligibility, Cloud/Self-Hosted parity, managed costs,
quotas, retention, downgrade, restore, export or existing data; the authoritative
feature matrix needs no change.

## Cross-cutting quality and validation plan

Relevant: semantic navigation/current destination, visible keyboard focus,
menu focus/close behavior, localized labels and long-copy reflow, touch targets,
responsive overflow, themes and reduced motion. Use existing component tests
and Playwright/axe with runtime screenshots; replace source-only responsive
assertions with browser checks rather than removing the behavior contract.

No new security/auth/privacy/cache/server-authority/API/migration, concurrency,
retry, observability or operational behavior. No additional network queries or
resources. Existing offline notices and authorized utility components stay in
place. Run Web tests, lint, format, typecheck/build, engineering-language audit
and browser QA. Diagnose failures against the same current-main baseline;
keep unrelated pre-existing defects outside the rescue. Stop after A1.
