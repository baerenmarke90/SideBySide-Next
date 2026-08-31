# Canonical Demo & Manual Test Space

Issue: #304  
Status: development/QA facility; required before Go Live

The canonical demo Space turns the scenario in `docs/m2/DEMO-SCENARIO.md` into a repeatable,
fictional dataset that can be used for manual Web/Android QA, screenshots, demonstrations,
and automated privacy/regression coverage.

It is **not** a production feature, an authentication bypass, a separate domain implementation,
or a database dump.

## Identities

The reserved demo identities are:

| Person | Local demo address |
|---|---|
| Lea Sommer | `demo-lea@sidebyside.invalid` |
| Alex Winter | `demo-alex@sidebyside.invalid` |

`.invalid` is deliberately non-deliverable. Passwords are never stored in the repository and are
never printed by the command. For initial creation they must be supplied explicitly through
`SBS_DEMO_LEA_PASSWORD` and `SBS_DEMO_ALEX_PASSWORD`.

The demo implementation refuses to operate when `SBS_ENVIRONMENT=production`.

## Create

Run migrations first, then execute from `backend/` in a development or test environment:

```bash
export SBS_DEMO_LEA_PASSWORD='choose-a-local-demo-password'
export SBS_DEMO_ALEX_PASSWORD='choose-a-different-local-demo-password'
uv run python -m scripts.demo_space create
```

Creation is idempotent. If the verified reserved accounts already share their one canonical demo
Space, the command returns that Space and does not duplicate data.

For a deterministic acceptance run, pin the scenario reference date:

```bash
uv run python -m scripts.demo_space create --reference-date 2026-08-24
```

Without `--reference-date`, the local current day becomes the reference date. Dates in the seed
are derived from that reference so a freshly reset Space continues to contain recent memories,
past milestones, open/completed work, and upcoming plans rather than permanently aging fixture
dates.

## Reset

Reset keeps the two reserved demo Accounts and their local credentials, removes only the verified
canonical demo Space, and recreates its content:

```bash
uv run python -m scripts.demo_space reset
```

A deterministic reset is also possible:

```bash
uv run python -m scripts.demo_space reset --reference-date 2026-08-24
```

The reset fails closed if:

- either reserved demo Account is missing;
- only one reserved Account exists;
- a reserved address belongs to an Account with an unexpected display name;
- the two reserved Accounts do not share exactly one active Space;
- either reserved Account also belongs to another active Space; or
- generated demo media cannot be purged safely.

The command never accepts an arbitrary Space ID to delete.

## Seed coverage

The canonical dataset is created through normal domain services and currently includes:

- relationship start and duration settings;
- shared self-profile preferences for Lea and Alex;
- private partner notes for both owners;
- shared and owner-only RelatedPerson / ImportantDate examples;
- three Memories, including Memories with and without images;
- generated, repository-owned JPEG demo media processed through the normal attachment pipeline;
- one shared and one owner-only HeartMoment;
- the private HeartMoment canary `CANARY-PRIVATE-LEA-7421`;
- two Milestones;
- comments that produce normal recipient notifications;
- Wishes in OPEN, PLANNED, and COMPLETED states;
- Plans in IDEA, PLANNED, and COMPLETED states, including upcoming schedules;
- Places with and without coordinates;
- Chapters, including a Place-linked chapter;
- a shared Collection with completed/open items;
- independent PrivateNote, GiftIdea, and PrivateCollection content for both demo Accounts;
- Search-visible shared/private material; and
- Activity and in-app Notification projections generated from the normal transactional outbox.

The image bytes are generated locally with Pillow. No Internet image, real photo, external asset,
or redistributable binary fixture is required. The images still pass through upload registration,
stream upload, finalize, validation/sanitization, and normal Memory/HeartMoment binding.

## Privacy canaries

The seed deliberately contains owner-only content for both partners. Private data must remain
absent from the other partner's shared Story, Search, Activity, Notifications, Dashboard, and
other shared read models.

The integration suite in `backend/tests/integration/test_demo_space.py` verifies representative
boundaries, including partner denial of the private HeartMoment, Search isolation, no private
Activity target, and no private canary in the partner Dashboard.

Do not replace these tests with a demo-only filtering exception. The point of the seed is to
exercise the production privacy model.

## Media lifecycle during reset

Reset first detaches Memory media through normal Memory attachment replacement, removes the seeded
attached HeartMoment through its domain service, and then purges the now-unbound demo attachments
from the configured media provider. Only after that cleanup succeeds is the verified demo Space
deleted and recreated.

This prevents repeated manual QA resets from accumulating orphaned demo media.

## Freemium / entitlement behavior

The demo does not unlock, hide, or special-case capabilities. It uses the same domain and
entitlement behavior as ordinary users. A future Premium demo scenario must use the real
capability/entitlement model; it must not add a demo-only bypass.

## Manual QA workflow

A practical development loop is:

1. merge/update the application build under test;
2. run `scripts.demo_space reset`;
3. sign in as Lea and Alex in separate sessions;
4. exercise the changed screen at compact, medium, and expanded widths;
5. explicitly check the opposite partner for private-canary leakage; and
6. rerun the relevant automated tests before merge.

The canonical seed complements automated tests. It does not replace API negative cases,
concurrency tests, migration checks, authorization tests, or CI gates.

## Web layout note

The demo implementation does not modify Web components or CSS. It can therefore be developed in
parallel with #348. Once the Web layout change is on `main`, reset the demo Space and perform the
visual verification against that merged layout.
