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

`.invalid` is deliberately non-deliverable. The initial local passwords are supplied only while the
canonical accounts are first created through `SBS_DEMO_LEA_PASSWORD` and
`SBS_DEMO_ALEX_PASSWORD`; they are never committed or printed.

Public visitors do **not** receive or enter those passwords. A demo deployment shows a persona
selection page with:

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

## Create

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

The same command is used once when bootstrapping the isolated public demo deployment. Automatic
startup/migrations still never create demo identities implicitly.

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
SBS_ALLOWED_HOSTS=["demo.sbs.example"]
SBS_CURSOR_SIGNING_KEY=<independent-random-secret-at-least-32-characters>
SBS_MAIL_TRANSPORT=none
```

Normal production hardening remains mandatory. The demo should additionally be protected by the
reverse proxy's ordinary request/rate-limit controls because it is intentionally reachable without
a personal account.

### Arcane / runtime-image bootstrap

The production/demo backend image contains the canonical demo bootstrap entrypoint. After the
isolated Arcane stack is healthy, create the demo Space once from the running API container. Keep
the initial passwords ephemeral instead of storing them permanently in the Arcane environment:

```bash
SBS_DEMO_LEA_PASSWORD="$(openssl rand -base64 32)"
SBS_DEMO_ALEX_PASSWORD="$(openssl rand -base64 32)"

docker compose -f compose.arcane.yaml exec -T \
  -e SBS_DEMO_LEA_PASSWORD="$SBS_DEMO_LEA_PASSWORD" \
  -e SBS_DEMO_ALEX_PASSWORD="$SBS_DEMO_ALEX_PASSWORD" \
  api python -m scripts.demo_space create

unset SBS_DEMO_LEA_PASSWORD SBS_DEMO_ALEX_PASSWORD
```

The generated password values are only needed for the initial account creation. Public demo users
still enter through the Lea/Alex persona selection page, and later canonical resets retain the
reserved demo Accounts and their password hashes.

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

Image bytes are generated locally with Pillow and still pass through upload registration, stream
upload, finalize, validation/sanitization, and normal binding. No Internet image or real photo is
required.

## Privacy canaries

The seed deliberately contains owner-only content for both partners. Private data must remain absent
from the other partner's Story, Search, Activity, Notifications, Dashboard, and other shared read
models.

Automated coverage verifies representative boundaries, including partner denial of private content,
Search isolation, private Activity exclusion, and Dashboard canary isolation. Do not replace these
checks with demo-only filtering exceptions.

## Freemium / entitlement behavior

The demo does not unlock, hide, or special-case product capabilities. Free/Core behavior remains the
same as for ordinary users. Future Premium scenarios must use the real capability/entitlement model
rather than a demo-only bypass.

## Practical QA loop

1. deploy/update the build under test;
2. reset the canonical demo Space;
3. enter once as Lea and once as Alex in separate browser sessions;
4. exercise the changed screen at compact, medium, and expanded widths;
5. explicitly check the opposite persona for private-canary leakage; and
6. rerun the relevant automated tests before merge.

The canonical demo complements automated tests. It does not replace negative API cases, concurrency
tests, migration checks, authorization tests, or CI/security gates.
