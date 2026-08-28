# Security

Security is a release gate, not follow-up work. A feature is not considered
complete until its cross-tenant and privacy tests exist.

## Core invariant: tenant isolation

The tenant is called a **Space**. Every shared record carries exactly one
`space_id`.

Every access to Space data verifies four things:

1. an authenticated account,
2. active membership in exactly that Space,
3. the resource actually belongs to that Space,
4. any additional resource-level authorization that applies.

**There is no data access based solely on a resource ID.**

For

```text
GET /api/v1/spaces/{spaceId}/memories/{memoryId}
```

it is not sufficient to load the Memory and compare its `space_id` with the
path. Membership is checked first, and the resource is then queried within the
Space. The query must not load foreign rows in the first place.

## 404 instead of 403

For privacy-relevant resources, SideBySide deliberately returns **404** where
403 might be more technically precise. A 403 confirms existence. Someone
probing foreign IDs must not learn which resources exist.

## Privacy classes

Every domain assigns its data to a class. There is no implicit public class.

| Class | Meaning |
|---|---|
| `SPACE_SHARED` | both partners in the Space |
| `OWNER_ONLY` | owner only, never the partner |
| `TEMPORARY_SHARED` | shared for a limited time |
| `EPHEMERAL_CONTEXT` | short-lived, with expiry |
| `SYSTEM_METADATA` | technical, no user content |

`OWNER_ONLY` means the partner receives the content through **no** path — not
by ID, not in lists, not through search, dashboard, Story, comments,
notifications, export, or an indirect relationship.

**Hiding content in the client is not enforcement.** The filter belongs in the
query. A row that is loaded and discarded afterward is already a leak — it was
in memory, logs, or response-size behavior.

### Enforcement

The tenant guard determines whether an account belongs to a Space. The
owner/privacy authorization in `sidebyside.authorization` then determines
what the account may read and modify within that Space. Both conditions are
part of the query, not post-query checks.

Owner-/author-related domains that use this foundation inherit three columns —
`space_id`, `owner_id`, and `privacy_class` — and call `readable()`,
`require_readable()`, or `require_writable()`. They do not implement their own
visibility predicate. There is neither a universal content table nor a second
hand-written guard per domain.

Shared Space-owned resources without a domain owner are not artificially
forced into the owner model. The tenant guard remains their common foundation;
additional write rules come from the respective domain.

Currently, `SPACE_SHARED` and `OWNER_ONLY` are enforceable server-side. Only
those two values are also persistable: a class without a rule would create rows
whose protection nobody enforces. A class without a rule evaluates to `false`
in queries — an omission makes content invisible, not visible. Adding another
class therefore always requires three things together: an authorization rule,
allowing the value in the stored range, and a migration.

`SPACE_SHARED` describes visibility, not blanket write permission. For
owner-/author-related resources, `SPACE_SHARED` currently still means the
owner or author writes and the partner reads. `SpaceProfile` is the
counterexample: it belongs to the Space, has no `owner_id`, and may be changed
by either active partner. No `PrivateResourceMixin` is invented for it.

Denial is intentionally split into two cases:

| Situation | Response |
|---|---|
| not readable — foreign Space, another owner's `OWNER_ONLY`, unknown or malformed ID | 404, identical wording in every case |
| readable but not writable — owner-related shared row owned by someone else | 403 |

Returning 404 for something the caller has just been allowed to view would not
protect anything; it would be false. Returning 403 for something the caller
must not see would disclose the existence that `OWNER_ONLY` is specifically
designed to hide.

## Authentication

Android and other native clients use Bearer tokens, not a Web session cookie.

```text
Authorization: Bearer <access-token>
```

Access tokens are short-lived, on the order of 15 minutes. Refresh tokens are
persisted **only as hashes**, rotate on use, and attempted reuse must be
detectable because it indicates a copied token.

`DeviceSession` stores `refresh_token_hash`, device name, platform,
`last_used_at`, `expires_at`, and `revoked_at`. Sessions can be revoked
individually.

Cloud uses email verification, Magic Link, Passkey, and Recovery without
requiring a password. Self-Hosted additionally supports local password login
and OIDC so an external provider can be configured without a special-case
model.

### Target policy by deployment mode

Cloud/Managed and Self-Hosted share the same application core but do not
necessarily expose the same authentication methods. The target is a
**server-side** policy, not merely hiding buttons in the client:

| Deployment mode | Intended authentication methods |
|---|---|
| Managed/Cloud | Passkey, Magic Link, and later managed providers such as Google and Apple |
| Self-Hosted | local password, Passkey, and freely configurable OIDC; Magic Link only when mail delivery is deliberately configured |

The `SBS_DEPLOYMENT` configuration value already exists. **The route/provider
policy above is not yet fully enforced by the current runtime router.** Until
that productization hardening is implemented, a client must not treat the
deployment mode as a security boundary. Enablement must ultimately be enforced
in the backend; UI visibility is only a representation of the same server
decision.

For OIDC, the external account is identified exclusively by `(issuer,
subject)`. A freely configurable `connection_id` selects the adapter; Pocket ID
is therefore a normal OIDC connection, not a special case. A new identity may
be stored only after complete validation of discovery, signature, and claims.

### ID Token validation

An ID Token initially represents only a claim made by another server. It
becomes an identity only when five conditions are valid. None of these checks
lives in the endpoint; all providers pass through `auth.oidc`:

| Check | Against | Why |
|---|---|---|
| Signature | issuer JWKS, asymmetric algorithms only | `none` and HMAC are excluded; with `HS256`, the signing key would be the client secret |
| Issuer | configured value **and** the discovery document, which must identify itself | otherwise a document at the expected address could point to foreign endpoints |
| Audience | exclusively the `client_id` configured for this connection; additional untrusted audiences are rejected, and multiple audience values require a matching `azp` | a token for another or additional application is not valid here |
| Nonce | value generated at flow start | binds the token to exactly this request; without it, a token captured elsewhere could be replayed |
| State | server-side stored hash, redeemable exactly once | binds the return path to exactly this browser |

The discovery document is not just configuration either: `issuer` must match
the configured connection exactly, and `authorization_endpoint`,
`token_endpoint`, and `jwks_uri` are accepted only as real HTTPS URLs. A
formally reachable discovery document therefore cannot redirect subsequent
protocol traffic to plaintext endpoints.

PKCE is mandatory (`S256`). The verifier remains on the server and never
appears in the authorization URL; the client sees only the challenge.

`oidc_auth_requests` stores the state hash, nonce, and verifier for ten minutes.
The nonce and verifier are stored there in plaintext intentionally: the server
must present or compare them itself. They are not authentication credentials;
they are binding values. The maintenance job removes them once consumed or
expired.

### OIDC sign-in, linking, and invitations

An unknown OIDC identity does **not** freely create an account. Without an
existing identity, an authenticated linking flow, or a valid invitation, the
callback ends with 401.

There are two controlled ways to introduce a new OIDC identity:

1. `/auth/oidc/{connectionId}/link` binds it, after a successful OIDC callback,
   to exactly the account that is already authenticated.
2. A flow started through `/auth/oidc/{connectionId}/start` may carry an
   invitation. Only the invitation-token hash is stored. Account, OIDC identity,
   and Membership are created in the same request transaction only after
   successful OIDC validation and renewed locked validation of the invitation.

An invalid, expired, revoked, or already-used invitation token does not open an
alternative path. Concurrent callbacks for the same invitation serialize on
the invitation, so at most one new account can result. An OIDC email address
never causes an account merge: it is adopted only if the provider explicitly
confirms `email_verified=true` and the address does not already belong to
another account.

Provider error text never leaves the adapter because it may contain internal
addresses or the client secret. Externally, errors remain the stable codes
`OIDC_TOKEN_INVALID`, `OIDC_STATE_INVALID`, and `OIDC_PROVIDER_UNREACHABLE`.

Passkeys are stored as independent WebAuthn credentials with globally unique
credential ID, public key, signature counter, AAGUID, transports, and
discoverable/backup metadata. The private key remains in the authenticator and
is neither received nor stored by the server.

### The two ceremonies

Registration happens **only from an existing authenticated session**: a
Passkey is an additional way to access an account that already exists. Sign-in
happens **without an account reference** — the options contain no candidate
list; the authenticator chooses which discoverable credential to offer. An
endpoint that listed matching credentials for an email address would become an
account directory.

Challenge, origin, RP ID, signature, and signature counter are validated.
Every failure returns the same response (`PASSKEY_CEREMONY_INVALID`); the
specific failed check is not exposed in the response.

The challenge is stored in `webauthn_challenges` for five minutes and is
**always** consumed when completing the ceremony, even if validation fails
afterward. Otherwise the same challenge could be tried repeatedly.

The anonymous authentication start currently creates a challenge row on every
call. The still-open abuse/concurrency hardening for this write path is tracked
in GitHub issue **#59**.

A signature counter that stops increasing after previously increasing suggests
a copied authenticator and causes rejection. If a device does not count at all
and both values remain 0, that is allowed: many Passkeys behave this way, and
rejecting them would lock all of them out.

Credential IDs are globally unique, including across accounts. Registration
does not establish whether a credential is discoverable (`residentKey` is a
preference, not a guarantee); discoverability becomes observable only during
sign-in without a candidate list and is recorded there.

Email verification, Magic Link, and Account Recovery use separate tables and
separate consumption functions. Every proof is random, short-lived, revocable,
single-use, and persisted only as a hash. A token from one flow therefore
cannot be redeemed in another flow, not because a generic check rejects it but
because the other flow never searches for it. OIDC, WebAuthn, Magic Link,
email verification, and Recovery have production adapters/API flows; every
successful authentication method converges on the same `DeviceSession` output.

### The three mail flows

| Flow | Endpoints | Lifetime |
|---|---|---|
| Magic Link | `/auth/magic-link/request`, `/auth/magic-link/consume` | 15 minutes |
| Email verification | `/auth/email/verification/request` (authenticated), `/auth/email/verification/confirm` | 24 hours |
| Account Recovery | `/auth/recovery/request`, `/auth/recovery/consume` | 30 minutes |

**No account-existence disclosure.** Both `request` endpoints always return
`202` with an empty body, for a known address exactly as for an unknown one.
Rate limiting applies identically to both; otherwise the behavior difference
would itself disclose existence. A mail-server delivery failure is logged but
does not change the response.

A residual timing difference remains: a mail is handed off for a known address
but not for an unknown one. This is accepted because the endpoints are rate
limited; equalizing it would require deliberately delaying delivery.

**Only the most recently requested link is valid.** A new request invalidates
older still-open links for the same flow. Otherwise valid authentication proofs
would accumulate in a mailbox.

**Redeeming a Magic Link verifies the address.** Opening the link from the
mailbox proves possession; a second verification path would create another
opportunity to forget this relationship.

**Recovery does not establish a new authentication method.** An account without
a local password, such as an OIDC-only account, receives no link; externally,
that is indistinguishable from an unknown address. A successful reset ends
**all** existing sessions and creates exactly one new session: the one on the
current device.

**Every successful method ends in the central `DeviceSession` output.** There
is no second place where tokens are issued.

### Outgoing mail

The plaintext token exists exactly twice: in the return value of the issuance
function and in the mail message. It is neither persisted nor logged.

The development adapter that writes messages to the log is therefore not
allowed in production: `SBS_MAIL_TRANSPORT` must be `smtp` there and
`SBS_PUBLIC_BASE_URL` must start with `https://`, otherwise the application
refuses to start. Failing startup is safer than silently running an instance
that writes authentication credentials to logs.

The base address for links comes from configuration and never from a request
header. A forged `Host` header could otherwise redirect a link to a foreign
server and cause the recipient to submit the token there.

The first Self-Hosted account requires a one-time secret bootstrap proof.
PostgreSQL serializes competing first registrations; after the first success,
bootstrap remains permanently closed and every subsequent registration
requires an invitation. The secret value is neither persisted nor logged.

### Refresh-token family

The `DeviceSession` is also the token family: every refresh token issued from
an authentication event belongs to exactly that session. Every consumed
generation remains associated with the family as a `ConsumedRefreshToken`
hash for as long as the session is alive.

Detection is therefore not limited to the immediately previous generation. If
`T0` appears again after `T0 → T1 → T2`, it is not merely an invalid token but
evidence of a copy: the legitimate client should hold `T2`. The session is
therefore revoked permanently, even when the request itself ends with 401 and
is rolled back.

Revocation requires a real token from that family. An arbitrary unknown value
revokes nothing; otherwise anyone could terminate someone else's session.
Externally, unknown, expired, revoked, and replay-detected tokens are
indistinguishable.

The history contains hashes only and is therefore not a second source of
authentication credentials. It disappears with the session and is pruned for
ended sessions after a retention period; active sessions keep their history
because the history *is* the replay detection mechanism.

### Retention is actually executed

A retention period that exists only as a function in code is not a retention
period. The `security_retention` job regularly executes
`sessions.prune_replay_history()`, `rate_limit.prune()`,
`oidc.prune_auth_requests()`, and `passkeys.prune_challenges()` as a normal job
in the PostgreSQL queue. After completing, it schedules itself again. The
default interval is six hours, well below the shortest retention period.

There is no second scheduler and no cron process in the container. The queue is
already stored in the database and survives restarts. Scheduling happens under
an advisory lock so two workers starting at the same time do not both enqueue
the job; even a duplicate run would be harmless because the prune operations
are idempotent.

If a job gives up permanently, no future chain remains attached to it. The
worker therefore also checks periodically whether any run is scheduled and
creates one if not. A permanently absent cleanup must not fail silently.

**Operational consequence:** retention depends on a running worker process
(`python -m sidebyside.jobs.runner`, service `worker` in the Compose setup).
Running only the API retains data longer than documented.

### Two expiry times per session

For the family and its history to be genuinely finite, `DeviceSession` has two
different boundaries:

| Field | Meaning | Extended? |
|---|---|---|
| `expires_at` | sliding inactivity window | yes, on every rotation |
| `absolute_expires_at` | hard upper limit from sign-in | **no** |

The sliding window alone would not be a limit: regular refreshes could move it
forward indefinitely. A continuously used session would then run without an
upper bound and add another history row on every rotation, none of which could
ever be pruned.

The absolute boundary is fixed at sign-in. No rotation moves it. Once reached,
refreshing no longer works; a new sign-in and therefore a new family is
required. Even an access token issued shortly before the boundary expires at
that boundary, otherwise it would not be a real upper bound.

`expires_at` is never set beyond `absolute_expires_at`. Through
`refreshExpiresAt`, the client therefore receives the expiry time that actually
applies.

### Bounded rotation rate

The absolute boundary makes history growth finite, but not slow. A client with
a valid token could create many generations in a tight loop. Therefore
`/api/v1/auth/refresh` has its own budget (`rate_limit.REFRESH`, currently 20
rotations per 15 minutes). This is many times the normal rate: an access token
lives for 15 minutes, so a normal client refreshes roughly once per window.

The counter is keyed to the **`DeviceSession`**, not the token value. The token
changes on every rotation; limiting by token would reset the counter after each
successful attempt. Other sessions for the same account remain unaffected.

Unlike sign-in, **successful** attempts count here, and the counter is not
cleared after success because successful rotations are exactly what is being
limited.

The check occurs after token validation. Only someone holding the family's
current token can receive 429; unknown, old, and revoked tokens still end with
401 and are not counted. The rate limit therefore does not become an oracle
for whether a session exists.

Every generation of the family remains attributable. The rate limit does not
shorten replay history and is explicitly not a time window through which old
tokens can fall out of detection.

The still-open serialization of the general `count -> check -> record`
threshold under concurrent requests is tracked in GitHub issue **#60**. It is
not an authentication bypass, but it must be hardened before public Managed
exposure so the configured limit also holds under burst load.

## Invitations

Invitation tokens are random, have sufficient entropy, are stored **only as
hashes**, have an expiry, are revocable, and can be used exactly once.

Required tests: expired, revoked, reused, Space already full, race between two
concurrent acceptances, invalid token.

## Media

Cloud media is not public. Reads use an authorized route or a short-lived
signed URL.

Storage keys are **never** derived from user filenames:

```text
spaces/{spaceUuid}/attachments/{attachmentUuid}/original
```

Uploads validate the actual MIME type, size, allowed media type, image
dimensions, and Space association. The Content-Type claimed by the client is
not sufficient.

## Content Security Policy of the Web frontend

The production Web server delivers CSP as an HTTP header using `always`. The
policy starts fail-closed with `default-src 'none'` and allows only sources
required by the current Vite build:

| Directive | Allowance | Rationale |
|---|---|---|
| `script-src` / `style-src` | `'self'` | Vite bundle, theme bootstrap, and CSS are external files on the same origin |
| `script-src-attr` / `style-src-attr` | `'none'` | no inline handlers or styles embedded in HTML; CSSOM property assignments require no source allowance |
| `img-src` | `'self' blob:` | local assets and authorized image bytes exposed through short-lived object URLs |
| `connect-src` | `'self'` plus explicit hosting origins | API plus direct presigned uploads/reads through `fetch()` |
| `font-src` | `'self'` | no external font CDNs |
| `object-src`, `frame-src`, `media-src`, `manifest-src`, `worker-src` | `'none'` | no currently approved domain requirement; video remains fail-closed |
| `base-uri` / `frame-ancestors` | `'none'` | no base-URL rewriting and no framing |
| `form-action` | `'self'` | forms may navigate only to the same origin |

`unsafe-inline`, `unsafe-eval`, wildcards, and broad scheme sources such as
`https:` are not allowed. `blob:` applies only to `img-src`; the actual media
bytes are first loaded through authorized `fetch()` requests and therefore
fall under `connect-src`.

In the normal Self-Hosted/reverse-proxy path, Web and API use the same public
origin. With `SBS_MEDIA_STORE=s3`, Compose automatically carries the already
configured `SBS_S3_ENDPOINT` into `SBS_WEB_CSP_CONNECT_ORIGINS`. Other hosting
platforms may set a whitespace-separated list of exact HTTP(S) origins there.
The Web entrypoint normalizes this list and refuses startup for wildcards,
paths, credentials, free-form CSP expressions, or invalid ports. This value is
host/admin configuration, not a user field.

A `VITE_SBS_API_BASE_URL` whose origin differs from the Web frontend must also
have its exact origin included in `SBS_WEB_CSP_CONNECT_ORIGINS`.

An upstream reverse proxy must forward exactly this header unchanged and must
neither replace nor duplicate it. Multiple CSP policies are evaluated together
restrictively; a second policy therefore cannot add origins and can easily
break functionality. Required alternative origins are configured at the Web
container instead of being added through a broadly permissive proxy policy.

### Reuse decision

The options reviewed were the W3C CSP standard as an HTTP header, a CSP `meta`
element, application middleware, external CSP products, and custom
implementation. The selected solution uses the browser standard, the existing
Nginx `add_header`, and the template/`envsubst` functionality already included
in the unprivileged Nginx image. For the static Web server, the header is the
complete delivery boundary and also supports `frame-ancestors`; a `meta`
element is not equivalent. Backend middleware would run at the wrong hop, and
an external service would add no privacy, operational, or maintenance benefit
for a static policy. No new dependency, external data flow, license/ToS
binding, or additional user effort is introduced. The fallback is a fully
static same-origin policy without an additional connect origin.

## Mandatory test cases

- cross-tenant / IDOR,
- private-resource leak,
- malformed IDs,
- invitation abuse,
- token replay,
- refresh rotation,
- revoked sessions,
- rate limiting,
- concurrent and reused Self-Hosted bootstrap,
- upload abuse and malicious media,
- XSS, CSRF in browser flows, SQL injection,
- signed-URL expiry,
- backup authorization,
- privacy leaks in search.

### Where they are enforced

The list above defines the requirements. The table below records where each
requirement is proven. It is updated when a gap is closed, not merely when a
test is created.

| Invariant | Evidence |
|---|---|
| Every Space endpoint rejects anonymous access, foreign access, and malformed IDs consistently | `test_endpoint_matrix.py` |
| The published contract is completely covered by this matrix | `test_endpoint_matrix.py::test_the_contract_is_complete_covered` |
| No write access without `If-Match` | `test_endpoint_matrix.py::test_without_if_match_is_not_geschrieben` |
| Private resources remain invisible to the partner — detail, list, filter, error response | `test_private_authorization.py`, `test_related_persons.py`, `test_partner_profiles.py` |
| Failed attempts remain counted durably even when the request is rejected | `test_auth_flows.py::TestProduktiveTransaktionsgrenze` |
| Refresh replay permanently revokes the family across generations | `test_auth_flows.py`, `test_sessions.py::TestReplay` |
| Concurrent refresh has exactly one winner | `test_auth_flows.py::test_parallele_refresh_rotation_hat_exactly_a_sieger` |
| Successful rotations are themselves limited | `test_sessions.py::TestRotationsflut` |
| Two concurrent invitation acceptances cannot grow a Space beyond two partners | `test_invitations.py::TestRace` |
| Concurrent bootstrap creates exactly one initial owner | `test_auth_flows.py::test_paralleler_bootstrap_hat_exactly_a_owner` |
| Security-relevant integration tests actually run in CI and are not silently skipped | CI step **Integration tests actually ran** |
| The production Web server serves exactly the restrictive CSP; arbitrary origins fail before startup | `web/scripts/check_csp_header.sh`, `web/scripts/test_csp_config.sh`, CI step **CSP origins are narrowly and fail-closed configurable** |

The rows covering uploads, signed URLs, backups, and search remain open because
the corresponding features do not yet exist. They are implemented with their
domain, not before it.

### Tenant matrix

| Access | Expected |
|---|---|
| Account A on Space A (member) | allowed |
| Account B on Space A (member) | allowed |
| Account C on Space B accessing Space A | never |
| anonymous | never |

### Private isolation

For every `OWNER_ONLY` domain, test separately through: list, search, dashboard,
timeline, notifications, export, relationships, attachments, update, and
delete.

## Logging

Allowed: `request_id`, `account_id`, `space_id`, route, duration, status, error
code.

Never logged: passwords; Bearer, refresh, Magic Link, verification, or Recovery
tokens; OIDC tokens; WebAuthn challenges; contents of Memories, HeartMoments,
answers, private notes, and gift ideas; sensitive preference values; precise
locations. Error tracking is sanitized in the same way.

## End-to-end encryption

**Not yet implemented.** The architecture is prepared for it; see
[ARCHITECTURE.md](ARCHITECTURE.md).

The claim that even the operator cannot read content may be used **only** after
actual implementation and an external audit. Stage 1 is not E2EE and must not
be called E2EE.

Stage 1 enforces technical separation only: sensitive domain content is bound
as a concrete `ProtectedPayload` class to a designated JSONB column; raw
dictionaries are rejected. With `crypto_version = 0`, this content still
exists as server-readable plaintext. There are no keys, no client-side
sealing, and no protection from the server operator yet.

Outbox payloads are separately restricted to explicitly allowed,
non-sensitive metadata. Free-text fields and `ProtectedPayload` objects are
rejected both by domain validation and by direct ORM binding.
