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

Registration policy and maintenance mode are persisted as application state,
not deployment-environment feature flags. `registration_enabled` records the
operator's registration policy; the effective registration state additionally
requires maintenance mode to be off. This keeps the stored operator choice
intact when maintenance is entered and left.

Clients can read the minimal unauthenticated `GET /api/v1/instance/status`
projection. It exposes only maintenance state, effective registration
availability, and the non-sensitive reason `administrator` or `maintenance`
when registration is unavailable. Web and Android treat connectivity failure
as a separate state and fail closed for advertising new-account creation.

An authenticated ServerAdmin can use:

- `GET /api/v1/server-admin/settings`;
- `PUT /api/v1/server-admin/settings/registration`;
- `PUT /api/v1/server-admin/settings/maintenance`;
- `GET /api/v1/server-admin/activity`.

Each mutation is authorized server-side and records a narrow audit event with
the actor, setting name, previous/new boolean value, and timestamp. The audit
record contains no product content, credentials, job payloads, or other private
data.

Maintenance mode rejects ordinary product API traffic, while health,
authentication/recovery, public instance status, and ServerAdmin endpoints stay
reachable. Background workers continue to run. This boundary deliberately
lets an operator sign in and leave maintenance mode without requiring shell or
database access.

Disabling registration blocks all supported new invited-account onboarding
paths, including local-password and OIDC onboarding. Existing accounts can
still authenticate and accept invitations. Initial bootstrap remains an
explicit lockout-recovery exception so a fresh Self-Hosted instance cannot be
made permanently inaccessible before its first operator account exists.

## Business model

Core ServerAdmin operations required to run a Self-Hosted SideBySide
installation are operational administration and are not Premium-paywalled.
Hosted-service-specific capabilities must continue to use the authoritative
deployment and entitlement model rather than hardcoded client branching.
