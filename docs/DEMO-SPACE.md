# Canonical Demo & Manual Test Space

Issue: #304  
Status: development/QA and public product-demo facility; required before Go Live

The canonical demo Space turns the scenario in `docs/m2/DEMO-SCENARIO.md` into a repeatable,
fictional dataset for manual Web/Android QA, screenshots, demonstrations, privacy regression
coverage, and a permanently reachable public demo deployment.

It is not a database dump or a parallel domain implementation. Seeded product data still uses the
normal domain, media, privacy, outbox, reminder, and entitlement paths.

## Identities

The reserved demo identities are:

| Person | Reserved address |
|---|---|
| Lea Sommer | `demo-lea@sidebyside.invalid` |
| Alex Winter | `demo-alex@sidebyside.invalid` |

`.invalid` is deliberately non-deliverable. For manual development/QA creation, initial local
passwords are supplied only while the canonical accounts are first created through
`SBS_DEMO_LEA_PASSWORD` and `SBS_DEMO_ALEX_PASSWORD`; they are never committed or printed.

The dedicated public demo does not require an operator to provide or persist these seed passwords.
Its Compose bootstrap creates high-entropy ephemeral initial values in process memory when the
reserved Accounts do not exist yet. Those values are neither printed nor written to deployment
configuration and are not used for public entry.

Public visitors do **not** receive or enter passwords. A demo deployment shows a persona selection
page with:

- the Lea persona action (`demo.joinLea`); and
- the Alex persona action (`demo.joinAlex`).

The selected persona receives a rate-limited, one-time authentication proof. That proof is then
consumed through the ordinary magic-link session path. The deployment-only entry endpoint is
intentionally excluded from the product OpenAPI contract so generated Android/Web API clients do
not treat public-demo entry as a normal authentication capability.

## Environments

`SBS_ENVIRONMENT` has three operational meanings relevant here:

- `development`: local development and QA;
- `demo`: isolated public demo deployment;
- `production`: ordinary production deployment.

`demo` receives the same public-runtime hardening as `production`: HTTPS public URL, explicit
allowed hosts, a real cursor signing key, and no logging mail transport are required.

`SBS_ENVIRONMENT=demo` requires:

```env
SBS_DEMO_MODE=true
```

Conversely, the ordinary `production` environment rejects `SBS_DEMO_MODE=true`. This prevents the
main production instance from accidentally becoming the public demo.

## Manual create for development / QA

Run migrations first. For local development/QA, execute from `backend/`:

```bash
export SBS_DEMO_LEA_PASSWORD='choose-a-local-demo-password'
export SBS_DEMO_ALEX_PASSWORD='choose-a-different-local-demo-password'
uv run python -m scripts.demo_space create
```

Creation is idempotent. If the verified reserved accounts already share their canonical Space, the
command returns that Space instead of duplicating data.

For deterministic acceptance runs:

```bash
uv run python -m scripts.demo_space create --reference-date 2026-08-24
```

Without `--reference-date`, the current local date becomes the reference date. The scenario derives
recent memories, future plans, past milestones, and mixed open/completed states from it.

The explicit `create` command intentionally remains available for development and QA. Public demo
Compose deployments use the automatic `ensure` path described below instead.

## Permanent public demo deployment

Run the demo as a **separate stack/database/media store/domain**, for example
`https://demo.sbs.example`. Never reuse the production database or media volume.

A representative demo environment is:

```env
SBS_ENVIRONMENT=demo
SBS_DEMO_MODE=true
SBS_DEMO_MODE_RESET_TIMER=true
SBS_DEMO_MODE_RESET_INTERVAL=6h

SBS_PUBLIC_BASE_URL=https://demo.sbs.example
SBS_ALLOWED_HOSTS=["demo.sbs.example","localhost","127.0.0.1"]
SBS_CURSOR_SIGNING_KEY=<independent-random-secret-at-least-32-characters>
SBS_MAIL_TRANSPORT=none
```

Normal production hardening remains mandatory. The demo should additionally be protected by the
reverse proxy's ordinary request/rate-limit controls because it is intentionally reachable without
a personal account.

### Automatic Compose bootstrap

Both supported Compose stacks contain a one-shot `demo-init` service. Startup order is:

```text
postgres -> migrate -> demo-init -> api / worker -> web
```

`demo-init` runs `python -m scripts.demo_space ensure` after successful migrations.

- on `SBS_ENVIRONMENT=demo` with `SBS_DEMO_MODE=true`, it creates the canonical Lea/Alex Space if it
  is missing;
- creation is idempotent, so ordinary redeploys do not duplicate or replace an existing demo Space;
- initial Account passwords are generated ephemerally inside the process and are never printed or
  stored in `.env`/Arcane;
- on development and ordinary production deployments, `ensure` exits successfully without creating
  demo data;
- API and worker start only after this one-shot step has completed successfully;
- migrations themselves still never seed product data.

This removes the previous manual post-deployment bootstrap command for a public demo instance.
Manual `create` remains available for local development/QA and explicit troubleshooting.

## Demo-instance banner

When `SBS_DEMO_MODE=true`, the Web build renders a visible notice above the entire demo UI. It states
that the deployment is a demo and that visitor changes are temporary.

The banner uses the same deployment values as the reset worker:

```env
SBS_DEMO_MODE_RESET_TIMER=true
SBS_DEMO_MODE_RESET_INTERVAL=6h
```

With the example above, the UI states that the demo is reset automatically every **6 hours**. The
compact interval syntax is formatted into user-facing German text (`30m` -> `30 Minuten`, `1h` ->
`1 Stunde`, `1d` -> `1 Tag`). If the reset timer is disabled, the banner says so rather than claiming
a reset cadence that is not active.

The interval is a Web build input as well as a backend runtime setting. Changing the reset timer or
interval therefore requires rebuilding/redeploying the Web image so the displayed notice remains in
sync with the worker configuration.

## Link from the main login

The normal/main Web build can advertise the isolated demo without enabling demo mode itself:

```env
SBS_ENVIRONMENT=production
SBS_DEMO_MODE=false
SBS_DEMO_PUBLIC_URL=https://demo.sbs.example
```

`SBS_DEMO_PUBLIC_URL` is a Web build input. When present, the login screen shows the configured demo
launch action (`demo.launch`) and links to the separate demo deployment. Changing the value therefore
requires rebuilding the Web image.

On the demo deployment, `SBS_DEMO_MODE=true` replaces the normal unauthenticated entry screen with
the Lea/Alex selection page.

## Manual reset

Reset keeps the two reserved demo Accounts and their local seed credentials, removes only the
verified canonical demo Space, and recreates its product data:

```bash
uv run python -m scripts.demo_space reset
```

A deterministic reset is also possible:

```bash
uv run python -m scripts.demo_space reset --reference-date 2026-08-24
```

The reset refuses ambiguous/partial reserved-account state, a demo Account in another active Space,
or unsafe media cleanup. It never accepts an arbitrary Space ID.

## Automatic reset timer

The public demo can reset itself through the existing durable PostgreSQL job queue:

```env
SBS_DEMO_MODE_RESET_TIMER=true
SBS_DEMO_MODE_RESET_INTERVAL=6h
```

Supported interval syntax is `m`, `h`, or `d`, for example `30m`, `6h`, or `1d`. Values below `5m`
or above `7d` are rejected.

The timer is independent from `SBS_DEMO_MODE`: demo mode may be enabled while automatic reset is
disabled. The timer itself requires demo mode.

After a successful automatic reset, public-demo authentication artifacts for Lea and Alex are
expired/removed, including device sessions, one-time authentication tokens, passkeys, and linked
non-local identities. Existing visitors therefore re-enter through the persona selection page
instead of carrying authentication state indefinitely across resets.

Automatic resets use the same complete canonical wrapper as initial creation: presentation cleanup
and stable Reminder examples are restored before the reset is considered complete.

## Seed coverage

The canonical dataset is created through normal domain services and currently includes:

- relationship start and duration settings;
- shared self-profile preferences for Lea and Alex;
- private partner notes for both owners;
- shared and owner-only RelatedPerson / ImportantDate examples;
- Memories with and without generated images;
- shared and owner-only HeartMoments;
- Milestones and Comments;
- Wishes in OPEN, PLANNED, and COMPLETED states;
- Plans in IDEA, PLANNED, and COMPLETED states, including scheduled examples;
- Places with and without coordinates;
- Chapters, including Place-linked content;
- shared Collections/items;
- independent PrivateNote, GiftIdea, and PrivateCollection content for both Accounts;
- Search-visible shared/private material;
- Activity and in-app Notification projections;
- generated M4-C Reminder examples for ImportantDate, birthday, relationship anniversary, and
  planned Plan rules;
- one manual Reminder plus recipient-specific mute/rule-preference examples.

The canonical demo ships a hash-pinned set of curated real stock photos under
`backend/demo_assets/`. They are imported locally through upload registration, normal MediaStore
storage, finalize, validation/sanitization, thumbnailing, and normal binding. Runtime bootstrap and
reset never download media from a stock provider or hotlink an external CDN.

## Curated demo media

The repository carries the canonical media set in:

```text
backend/demo_assets/manifest.json
backend/demo_assets/images/
backend/demo_assets/README.md
```

The current set contains twelve real Pixabay stock photos. Each concrete source page was checked individually. The selected files were published before **2019-01-09**; Pixabay's current terms identify content published before that date as CC0 content. The manifest records the real asset id, creator, source publication date, source-page URL, `CC0 1.0 Universal`, the Pixabay terms as the licensing basis, the date of the license check, SHA-256, MIME type, German alt text, and intended usage. Source URLs are provenance only and are never used as media URLs.

Do not infer redistribution permission merely from the provider name. Current provider licenses may restrict standalone redistribution. A maintainer adding an image must check the concrete source page and applicable terms, commit the approved bytes locally, compute the exact hash, update all provenance fields, and run:

```bash
uv run python -m scripts.demo_space validate-assets
```

`validate-assets` does not open the database. Creation and reset run the same complete asset preflight before any demo mutation: manifest schema, required provenance, provider/source URL, local file existence, exact directory membership, SHA-256, decodable image type, MIME agreement, alt text, and the historical Pixabay CC0 cutoff used by this curated set. A failure aborts before accounts are created or existing demo media is purged.

The runtime image copies `demo_assets` explicitly and validates it during image build. There are no stock-site downloads at container startup. Seeding calls the existing attachment service (`create_upload` -> `open_upload` -> `complete_upload` -> `finalize_upload` -> validation) so normal size/type checks, image sanitization, thumbnails, MediaStore, and database bindings remain authoritative. No parallel demo storage exists.

Reset first validates the local catalog, then detaches all demo bindings and purges every attachment provider object before replacing the verified demo Space. The same local asset ids are re-imported in the same deterministic order, so repeated resets do not accumulate duplicate or orphaned media.

The five album-like demo themes (`Unser Sommer`, `Kleine Alltagsmomente`, `Unterwegs am Wochenende`, `Kochabende`, `Draußen unterwegs`) use the existing Chapter model. SideBySide currently has no separate Album product model, and this demo change intentionally does not add a DB column, API, or Web feature solely to simulate one.

### Maintainer flow for a new image

1. Inspect the concrete Pexels/Pixabay source page and its applicable redistribution terms.
2. Avoid identifiable people, logos, trademarks, and other third-party rights unless reviewed separately.
3. Download the approved image once into `backend/demo_assets/images/`; never add a runtime CDN URL.
4. Record real provider/asset/creator/license metadata and meaningful `alt_text_de`/`usage_context` values.
5. Compute SHA-256 over the exact committed file and update `manifest.json`.
6. Run `uv run python -m scripts.demo_space validate-assets` plus demo unit/integration tests.
7. Build the backend image to prove the packaged runtime contains exactly the validated set.

## Privacy canaries and presentation cleanup

The seed deliberately uses unmistakable owner-only canary tokens while its privacy fixtures are
assembled. They allow automated tests to detect leakage into the partner's Story, Search, Activity,
Notifications, Dashboard, and other shared read models.

Those tokens are **not product copy**. Before the completed canonical demo dataset is returned to
public callers, the presentation-normalization step replaces them with natural fictional values
such as private notes, dates, gift ideas, and private-list titles. The privacy class and ownership do
not change. Automated coverage verifies both properties: the internal tokens are absent from the
completed public demo data, and the natural private content still remains owner-only.

Do not solve presentation problems by weakening privacy tests or adding demo-only filtering
exceptions.

## Freemium / entitlement behavior

The demo does not unlock, hide, or special-case product capabilities. Free/Core behavior remains the
same as for ordinary users. Curated media, richer seed content, and reset behavior add no entitlement,
paywall, storage-tier, billing, or Premium capability change. Future Premium scenarios must use the real
capability/entitlement model rather than a demo-only bypass.

## Practical QA loop

1. deploy/update the build under test; the public demo is ensured automatically;
2. reset the canonical demo Space when a fresh reference state is needed;
3. enter once as Lea and once as Alex in separate browser sessions;
4. exercise the changed screen at compact, medium, and expanded widths;
5. explicitly check the opposite persona for owner-only leakage; and
6. rerun the relevant automated tests before merge.

The canonical demo complements automated tests. It does not replace negative API cases, concurrency
tests, migration checks, authorization tests, or CI/security gates.
