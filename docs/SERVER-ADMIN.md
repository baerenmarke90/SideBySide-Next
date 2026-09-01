# Server Administration

## Purpose

ServerAdmin is an instance-wide operational capability for administering a
SideBySide installation. It is separate from partner-facing Space membership
and does not grant access to private product content.

The Web administration surface uses the dedicated `/server-admin` route. The
backend remains authoritative: hiding or showing the route in a client is only
presentation assistance and does not replace endpoint authorization.

## Operator-managed authorization

ServerAdmin identities are configured in the deployment environment:

```dotenv
SBS_SERVER_ADMIN_EMAILS=["operator@example.com"]
```

The value is a JSON array. Multiple operators may be configured. Addresses are
normalized to lower case and duplicates are ignored.

An authenticated account receives ServerAdmin only when at least one of its
stored `AccountEmail` rows:

1. is verified; and
2. exactly matches an address in `SBS_SERVER_ADMIN_EMAILS`.

The safe default is:

```dotenv
SBS_SERVER_ADMIN_EMAILS=[]
```

which grants ServerAdmin to nobody. Space roles, Space ownership, the first
bootstrap registration, and unverified email addresses do not implicitly grant
ServerAdmin.

The API process loads this setting from its environment. After changing the
allowlist, recreate/restart the API process through the normal deployment
workflow so the new configuration is loaded.

## Deployment plumbing

The setting is passed through both supported Self-Hosted Compose paths:

- `compose.yaml` for a complete repository checkout;
- `compose.arcane.yaml` for the remote-source Arcane workflow.

`.env.example` and `deploy/persistent-development.env.example` both document the
setting. Development, Demo, and Production installations manage their own
allowlists and must not share environment files as a convenience.

## Authorization contract

The authenticated client may read `/api/v1/auth/capabilities` to decide whether
to present the ServerAdmin entry point. This response is not an authorization
source.

Every `/api/v1/server-admin/...` endpoint independently requires the
server-side ServerAdmin guard. An ordinary authenticated account receives a
stable forbidden response even if it manually navigates to the route or calls
the API directly.

## Operational overview

`GET /api/v1/server-admin/overview` exposes a privacy-safe application-level
projection including available signals for:

- API/database state;
- deployment and environment;
- build revision and API process start time;
- safe public/runtime configuration state;
- aggregate Account and active-Space counts;
- coarse recent Account-registration counts;
- READY media object count and aggregate stored bytes;
- background-job state and recent failed-job technical metadata.

Where no authoritative runtime primitive exists yet, the API reports that the
signal is not available instead of fabricating health. In particular, the
current worker model has no heartbeat primitive and the media adapters do not
expose a generic health probe.

The overview does not expose:

- passwords, tokens, private keys, DSNs, provider credentials, or secrets;
- private Memories, Notes, messages, media content, or other product payloads;
- background-job payloads;
- raw background-job exception text;
- shell, SQL, filesystem, or container execution capabilities.

## Registration and maintenance controls

Runtime registration policy and maintenance mode are owned by Issue #334. Their
persistent state, public status semantics, privileged mutations, audit events,
and recovery/lockout behavior must be implemented there and then surfaced by
the ServerAdmin dashboard. The dashboard must not introduce temporary
client-only switches or environment-only substitutes for those runtime
settings.

## Business model

Core ServerAdmin operations required to run a Self-Hosted SideBySide
installation are operational administration and are not Premium-paywalled.
Hosted-service-specific capabilities must continue to use the authoritative
deployment and entitlement model rather than hardcoded client branching.
