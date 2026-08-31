# ADR 0003 – Primary Navigation and Route Model

**Status:** Accepted
**Date:** August 31, 2026
**Owning issue:** #360
**Affects:** #295 (Web), #350 (Android), #328 and #346 (Deep Links), #344, #352

## Context

`docs/INFORMATION-ARCHITECTURE.md` section 2 declared five mandatory primary
destinations and section 5 a canonical route model. `docs/UX-PATTERNS.md`
repeated the same five product labels, and `docs/SCREEN-TEMPLATES.md` carries a
template for one of them.

The delivered Web client ships a different set. Only `story` matches:

| IA route | Purpose | Backend | Web client |
|---|---|---|---|
| `today` — Heute | shared overview and next actions | `/spaces/{id}/dashboard` | `dashboard`, labelled *Übersicht* |
| `story` — Story | shared timeline | present | `story` |
| `plan` — Planen | wishes and plans | present | `planning`, labelled *Planen* |
| `discover` — Entdecken | curated inspiration | **none** | not shipped |
| `more` — Mehr | Space, privacy, profile, settings | present | dissolved into five flat destinations |

Three findings shaped this decision.

**Discover has no Core.** `docs/ROADMAP.md` places Discover in **M7**, together
with Shopping, Recipes, Events and Provider adapters. The backend exposes no
endpoint for it. The Web client was therefore right not to build it: the M5 Web
slice contract forbids dead or future-contract navigation. The contradiction
here is in the Information Architecture, which listed an M7 area as mandatory
primary navigation from the start.

**Two divergences are naming only.** `today` versus `dashboard` describes the
same purpose against the same endpoint, and `plan` versus `planning` differs
only in the path — the Web label is already *Planen*.

**The substantive divergence is `more`.** The Web client dissolved that area
into `search`, `activity`, `notifications`, `people` and `profile`, reaching
eight primary destinations. That breaks a core rule of the Information
Architecture — "primary navigation contains no more than five destinations" —
rather than only its route table.

Related: the desktop navigation grouping introduced by #340 labels a Web sidebar
group *Entdecken* while holding Search, Activity and Notifications. That name is
reserved for the M7 area and must not be used for anything else.

## Decision

Keep the five-area product intent of the Information Architecture. Correct the
document where the clients are right, and correct the clients where the document
is right.

### 1. Primary navigation

Four destinations until M7, five from M7:

| Route ID | de-DE | Path | Availability |
|---|---|---|---|
| `today` | Heute | `/today` | now |
| `story` | Story | `/story` | now |
| `plan` | Planen | `/plan` | now |
| `discover` | Entdecken | `/discover` | **M7**, feature-gated |
| `more` | Mehr | `/more` | now |

`discover` keeps its reserved identity and its position in the order, and is not
rendered before its domain exists. A reserved route is not dead navigation; a
visible empty area would be.

### 2. Naming is unified on the document

`dashboard` becomes `today`, `planning` becomes `plan`. The user-facing label
for `today` is **Heute**, not *Übersicht*: the area answers what is relevant
now, and the Information Architecture, UX Patterns and the App all use that
term.

### 3. `more` is restored as an area

Everything that is not a primary task moves underneath it:

| Path | Content |
|---|---|
| `/more` | area overview |
| `/more/space` | Space and partner, invitations |
| `/more/people` | related people and important dates |
| `/more/private` | the owner-only area |
| `/more/notifications` | in-app notifications |
| `/more/profile` | profile, preferences, appearance |

This closes #344: the owner-only area becomes a named destination under `Mehr`
instead of being reachable only from within Profile.

### 4. Search and Activity are not primary destinations

Neither appears in the Information Architecture structure tree, and adding them
would break the five-destination rule again.

- **Search** is a global utility, not an area. It belongs in the app bar on Web
  and behind the search affordance on Android, at `/search`.
- **Activity** answers "what happened between us", which is what `Heute` is
  for. It becomes `/today/activity` rather than a peer of Story and Planen.

### 5. Old paths redirect

`/dashboard`, `/planning`, `/people`, `/profile`, `/activity`,
`/notifications` and the current private-area paths keep working as permanent
redirects to their new locations. Deep Links that have already been shared must
not break, and #328 and #346 build their Deep Link registry on the new model.

## Consequences

- `docs/INFORMATION-ARCHITECTURE.md`, `docs/UX-PATTERNS.md` and
  `docs/SCREEN-TEMPLATES.md` are updated with this ADR to mark Discover as an
  M7 area and to record the sub-routes of `Mehr`.
- The Web client needs a routing change with redirects and a navigation
  regrouping. That is implementation and is owned by its own issue, not by
  #360.
- The Web sidebar group currently labelled *Entdecken* is renamed; the label
  stays reserved for the M7 area.
- Android S0B (#352) is unblocked and builds its destination registry against
  this model directly, so no Android route is ever migrated.
- The M5 parity gate can compare both clients against one model.

## Alternatives considered

**Rewrite the route table to match the shipped Web client.** Cheapest, and
rejected: it would delete *Heute* and *Entdecken* as product concepts, abandon
the five-destination rule, and let three binding documents follow the
implementation rather than guide it.

**Rebuild the Web client exactly as documented.** Rejected: it would require a
visible *Entdecken* area with no Core behind it until M7, which the Web slice
contract forbids, and it treats the document as correct on a point where the
client's judgement was better.
