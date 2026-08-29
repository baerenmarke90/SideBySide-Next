# M2 Security & Privacy Test Matrix

**Status:** binding acceptance matrix for M2  
**As of:** August 25, 2026

This matrix supplements the general security and HTTP tests with domain risks for Memories, HeartMoments, Milestones, comments, Story, and attachments. Tests must generally run through the public API; repository-only tests are insufficient for authorization.

## Test identities

| Key | Role |
|---|---|
| `A` | author and active member of Space Alpha |
| `B` | partner and active member of Space Alpha |
| `C` | active member of another Space Beta |
| `R` | former/revoked member of Space Alpha |
| `X` | authenticated but without membership |
| `ANON` | unauthenticated |

All IDs are additionally tested with random, existing foreign, and syntactically invalid values. A known UUID must never replace authorization.

## Expected disclosure behavior

- `401` only for missing or invalid authentication.
- `404` for invisible or foreign resources when `403` would disclose their existence.
- `403` only where the resource's existence is already legitimately known to the caller.
- Error text, timing, headers, and response size must not reveal private or foreign content.
- Authorization is applied server-side before projection, counting, pagination, and URL generation.

## Media abuse – binding M2 values

| ID | Case | Expectation |
|---|---|---|
| MED-01 | allowed filename extension, Magic Bytes/MIME not in allowlist | `FAILED`, no normally readable blob |
| MED-02 | declared MIME differs from server-detected type | `FAILED`, safe error code, client MIME is not trusted as truth |
| MED-03A | image >25 MiB | `FAILED` before `READY` |
| MED-03B | image >40 MP or >12,000 px edge | `FAILED` before `READY` |
| MED-03C | video >250 MiB, >180 s, or >3840×2160 | `FAILED` before `READY` |
| MED-03D | Memory >20 attachments or >500 MiB validated total size | reject binding atomically; existing relations unchanged |
| MED-04 | decompression bomb/extreme dimensions | resource limit applies, worker remains stable, `FAILED` |
| MED-05 | manipulated/broken container | parser failure isolated, `FAILED` |
| MED-06 | original name with path/Unicode control characters | never used as storage key/authorization input; absent from standard logs |
| MED-07 | duplicate/concurrent finalize | exactly one effective validation job; idempotent outcome |
| MED-08 | S3 Upload URL older than 10 min / manipulated | provider access denied; no freely selectable key |
| MED-09 | S3 Read URL older than 5 min / manipulated | access denied |
| MED-10 | Read URL after membership/privacy revocation | no new URL; already issued URL valid at most until 5-minute TTL |
| MED-11 | foreign `storageKey` in request | field not client-settable or request rejected |
| MED-12 | PENDING/UPLOADING/FAILED >24 h | hourly cleanup marks/deletes idempotently |
| MED-13 | READY unbound >60 min | `DELETING`; owner can no longer bind afterward |
| MED-14 | bind Attachment Alpha → Parent Beta | atomically return 404/reject; no leak/relation |
| MED-15 | second parent for already bound attachment | reject; exclusive binding remains unchanged |
| MED-16 | bind vs. orphan cleanup concurrently | exactly one operation wins; never a bound deleted blob |
| MED-17 | parent delete vs. finalize/bind concurrently | no relation to deleted parent; no visible orphan |
| MED-18 | provider delete timeout | domain content remains invisible; `DELETE_FAILED`, retry/metric |
| MED-19 | local/S3 adapter | identical lifecycle/authorization contract |
| MED-20 | EXIF/GPS present | location-free after `READY`; no unstripped original retrievable |
| MED-20a | vendor-specific/unknown metadata segment | does not survive ingest; allowlist is fail-closed |
| MED-20b | media cannot be sanitized safely | `FAILED`; never stored unstripped |
| MED-20c | extracted capture timestamp | ProtectedPayload; absent from every Outbox row, log, and metric |
| MED-20d | variant without parent read permission | not retrievable; privacy change also blocks variant |
| MED-20e | variant generation fails | attachment remains usable; no `FAILED`, no orphaned variant object |
| MED-21 | unknown type/GIF/RAW/WebM/MKV/document | fail-closed `FAILED` |
| MED-22 | HEIC/HEIF/JPEG/PNG/WebP within limits | validation can reach READY |
| MED-23 | MP4/QuickTime within limits | validation can reach READY |
| MED-24 | S3 Bucket/Public ACL | deployment/contract test confirms it is not public |

## Attachment authorization

For every attachment, test at least these paths:

1. Owner may manage an own unbound upload only while PENDING/UPLOADING/VALIDATING/FAILED or READY within 60 minutes.
2. Partner can never read, count, or distinguish an unbound attachment through errors.
3. After binding, read access follows the parent exclusively.
4. Owner ID alone does not bypass a later parent privacy restriction.
5. Owner-only HeartMoment leaks neither metadata nor stream/Read URL to the partner.
6. Cross-space attachment/parent combinations are rejected before relation/URL generation.
7. After the last reference/parent delete, no new Read URL is issued.
8. Storage key, bucket, and provider details do not appear in user-exposed responses.

## IDOR and tenant isolation

| ID | Attack | Expectation |
|---|---|---|
| TEN-01 | `C` reads/changes/deletes Alpha entity by UUID | `404`, no mutation |
| TEN-02 | `A` sets `spaceId=Beta` in body, query, or route | reject request, no implicit rewriting |
| TEN-03 | Comment from Alpha references target in Beta | atomically reject, no event |
| TEN-04 | bind Attachment from Alpha to parent in Beta | atomically reject |
| TEN-05 | use cursor from Alpha for Beta | neutral error or empty result according to contract, no data |
| TEN-06 | reuse signed URL/read token across spaces | deny access or permit only the exactly bound key within TTL |
| TEN-07 | revoked member requests new media read | deny; no new signed URL |
| TEN-08 | casing, encoding, and duplicate parameters | canonical and fail-closed |

## Concurrency and transactions

- Two updates with the same version: exactly one wins; the other receives `409`.
- Update concurrent with delete: no reappearance, consistent failure behavior.
- Parent delete concurrent with attachment finalize/bind: no visible orphan and no relation to deleted parent.
- Comment create concurrent with target privatization or delete: transaction prevents an unauthorized comment.
- Duplicate create with idempotency key: one domain entity and at most one Outbox event.
- Domain change plus Outbox: either both commit or both roll back.
- Two finalize requests: exactly one validation job / terminally consistent state.
- Binding concurrent with READY-orphan cleanup: status/row lock prevents binding to a deleted blob.
- Removing last reference concurrent with Read Descriptor: no new authorization after domain delete.

## Owner-only: required paths

For a `PRIVATE` HeartMoment by `A`, `B` must receive exactly no signal through any of these paths:

1. Direct read and update/delete attempt.
2. Lists, later search/filter, and autocomplete.
3. Story, month groups, counts, and cursor.
4. Dashboard, Activity Feed, Recap, and “zuletzt geändert”.
5. Comment target resolution and comment lists.
6. Attachment metadata, file retrieval, preview image, and signed URL.
7. Domain events, notifications, Push Preview, and badge count.
8. Partner export, shared backup, and diagnostic output.
9. Cache keys, ETags, logs, traces, metrics, and analytics properties.
10. Error behavior for a known ID and indirect relation IDs.

A test data set contains clearly recognizable canary values in text, emotion, filename, and attachment metadata. No canary may appear outside the owner context.

## Logging, telemetry, and events

- No titles, bodies, comments, original files, original filenames, Read/Upload URLs, or private emotions in standard logs.
- IDs are logged only as operationally necessary; no tokens, signatures, or storage credentials.
- Error tracking receives sanitized payloads and no complete request bodies/provider responses.
- Domain events contain minimal references instead of protected content.
- Metrics have bounded cardinality and no user text/filenames as labels.
- Media metrics capture at least state age/count for PENDING, FAILED, READY-unbound, DELETE_FAILED, plus cleanup success/failure.

## Adapter contract tests

Every `MediaStore` implementation must pass the same domain-level test catalog:

- `createUpload` creates non-guessable, space-bound server-side keys.
- Local Upload streams through the server with authorization; S3 Upload Descriptor expires after ≤10 min.
- `finalizeUpload` is idempotent and does not transition directly to READY without validation.
- `open`/`createReadUrl` cannot be reached without immediately preceding domain authorization.
- S3 Read URL expires after ≤5 min; bucket remains private.
- `delete` is idempotent and deletes only the exactly addressed blob.
- Partial failures do not misleadingly change domain state.
- A future encrypted blob can be stored/transferred; M2 does not claim that server-side validation with real E2EE is already solved.

## Retention/job tests

- Cleanup clock uses server-side timestamps, not client time.
- PENDING/FAILED at 23:59 h remain; >24 h become due.
- READY-unbound at 59 min remains bindable; >60 min becomes due.
- Repeated cleanup is idempotent.
- Provider failure causes no domain rollback and no reappearance.
- `DELETE_FAILED` remains visible to operations/metrics and is retried.
- Cleanup logs contain attachment ID/state/adapter/attempt, but no URLs/filenames/content.

## Story/pagination

Global full-text search `q` is not required for G2 according to M2-S0 project control and is generally M4. Story privacy is still enforced before sorting, counting, and cursor construction. Sorting/cursor behavior is decided authoritatively in #70/D08.

## Client and cache checks

| Area | Web | Android |
|---|---|---|
| Logout / space change | fully clear query and media caches | clear local projections and image cache |
| PRIVATE data | never in shared browser/service-worker cache | owner-bound, not in backup/Share Sheet |
| Offline | last authorized view according to later cache contract | last authorized view according to later cache contract |
| Offline Write | disabled or clearly blocked | disabled or clearly blocked |
| Read URL | never persist durably | never persist durably |

## Acceptance criterion

M2 is not security-complete while a required path is missing, a cross-tenant test exists only at repository level, or a private HeartMoment can become indirectly visible. Media runtime is additionally blocked until the #69 values are implemented reproducibly in the API, adapter contract tests, and PostgreSQL integration tests.
