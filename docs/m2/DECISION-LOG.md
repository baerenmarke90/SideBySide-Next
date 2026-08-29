# M2 Decision Log

**As of:** August 25, 2026  
**Rule:** An open question is not decided silently in code.

This log separates specification statements from implementation proposals. `PROPOSED` is not binding. `DECIDED` requires a date, decision owner, and reference to an ADR, specification, or issue.

## Status and priority

- `OPEN` – decision missing.
- `PROPOSED` – preferred option exists, approval missing.
- `DECIDED` – documented as binding.
- `BLOCKING` – decide before the first affected implementation.
- `BEFORE_CLIENTS` – decide before stable Web/Android integration.
- `LATER` – intentionally deferrable until after M2 while the boundary remains open.

## Decisions

| ID | Priority | Status | Owner | Question | Proposal / next action |
|---|---|---|---|---|---|
| M2-D01 | BLOCKING | DECIDED | Product + Domain | May the partner change or delete a Memory authored by the other person? | No. Both active partners can read shared Memories; Update/Delete remain exclusively with the immutable author. See decision below / #68. |
| M2-D02 | BLOCKING | DECIDED | Domain + API | Do Comments receive a `version` field for optimistic concurrency? | Yes. Editable Comments receive `version`; Update/Delete require the same If-Match/409 semantics as other mutable resources. See #68. |
| M2-D03 | BLOCKING | DECIDED | Domain + Data | How are multiple attachments bound: exclusive ownership, reuse, join entity, and sort order? | Exclusive binding to at most one parent; MemoryAttachment with stable `position`; no cross-space/multiple binding. See #69. |
| M2-D04 | BLOCKING | DECIDED | Security + Product | Which MIME types, file sizes, pixel limits, and video durations apply per platform? | JPEG/PNG/WebP/HEIC/HEIF ≤25 MiB/40 MP/12k px; MP4/QuickTime ≤250 MiB/180 s/4K; Memory ≤20 attachments/500 MiB. See #69. |
| M2-D05 | BLOCKING | DECIDED | Backend + Ops | Is media validation synchronous during finalize or asynchronous? Which internal states are required? | Asynchronous; `PENDING/UPLOADING/VALIDATING/READY/FAILED/DELETING/DELETE_FAILED`. See #69. |
| M2-D06 | BLOCKING | DECIDED | Security + Privacy | Is HeartMoment emotion metadata or ProtectedPayload? | ProtectedPayload. Emotion is sensitive relationship content and must not be used as analytics/event/log metadata. See #68. |
| M2-D07 | BLOCKING | DECIDED | Domain + Privacy | What happens to Comments when a HeartMoment changes from `SHARED` to `PRIVATE`? | The change is allowed only as an atomic privacy operation; existing Comments are deleted in the same DB transaction. No partner projection may remain afterward. See #68. |
| M2-D08 | BLOCKING | DECIDED | API + Data | Which Story ordering applies when `happenedOn` is missing, and which tie-breaker stabilizes cursors? | `effectiveDate = happenedOn ?? UTC_DATE(createdAt)`; key `(effectiveDate, createdAt, kindRank, id)`, full keyset pagination; cursor opaque/integrity-protected. See #70. |
| M2-D09 | BLOCKING | DECIDED | API | Exact routes, nesting, and DTO names? | Space-scoped route catalog and DTOs are frozen in `API-DESIGN.md`/`API-CONTRACT.json`. Parent Comments are nested; Update/Delete use a space-scoped Comment ID. See #70. |
| M2-D10 | BEFORE_CLIENTS | OPEN | Product + Privacy | What notification preview may a Comment show? | Generic by default; content excerpt only after explicit privacy approval. |
| M2-D11 | BLOCKING | DECIDED | Data + Privacy | Delete, retention, and cascade rules for entity, relation, blob, event, and audit? | Domain part #68 plus media part #69 decided: domain entity immediately invisible; Comments atomic; last media reference sets `DELETING`; provider cleanup async/idempotent; `DELETE_FAILED` retryable/measurable. |
| M2-D12 | BLOCKING | DECIDED | Backend + Ops | How long are incomplete/failed uploads retained? | PENDING/UPLOADING/FAILED 24 h; cleanup at least hourly; DELETE_FAILED until success/manual intervention. See #69. |
| M2-D13 | BLOCKING | DECIDED | Security + Media | Direct upload or server-side stream per local/S3 adapter? | Local: authorized server stream. S3: presigned upload ≤10 min; Read URL ≤5 min. Domain/finalize authorization remains server-controlled. See #69. |
| M2-D14 | BLOCKING | DECIDED | Privacy + Product | Are EXIF, GPS, and other embedded metadata removed? | Yes, during ingest. The validation job extracts an allowlist of technical fields into ProtectedPayload and then stores only the sanitized file. See #78. |
| M2-D15 | BLOCKING | DECIDED | Media + Product | Are thumbnailing, transcoding, and poster frames part of M2? | One derived variant each: image thumbnail and video poster frame. Transcoding is not part of M2. See #78. |
| M2-D16 | BLOCKING | DECIDED | Architecture + Security | Minimal schema for each M2 Domain Event? | Envelope: `eventId`, `eventType`, `occurredAt`, `spaceId`, `actorId`, `resourceType`, `resourceId`, `resourceVersion`; event-specific data only IDs, safe states/categories, and technical timestamps. No ProtectedPayload, filenames, URLs, or emotion. See #68. |
| M2-D17 | BEFORE_CLIENTS | OPEN | Product + Privacy | Which private data is included in personal export, shared export, or backup? | Strictly separate owner export and partner export; PRIVATE never in partner export. |
| M2-D18 | BEFORE_CLIENTS | OPEN | Client + Security | What cache/offline retention applies to private content on Web and Android? | Owner/space-bound caches, complete deletion on logout/space change, no Offline Write. |
| M2-D19 | LATER | PROPOSED | Architecture | How does E2EE remain retrofit-ready without pretending real E2EE exists today? | Keep ProtectedPayload and opaque MediaStore; key management explicitly outside M2. |
| M2-D20 | BLOCKING | DECIDED | Domain | Can an attachment be `READY` without a parent, and for how long? | Yes, owner only and at most 60 min from `readyAt`; then `DELETING`; bind-vs-cleanup serialized. See #69. |
| M2-D21 | BEFORE_CLIENTS | OPEN | Search + Privacy | Is M2 search implemented directly in Postgres or through a separate index? | Global full-text search is not required for G2 and generally belongs to M4; if needed earlier, create a new explicit gate decision. |
| M2-D22 | BLOCKING | DECIDED | Product + UX | Is the owner area for private HeartMoments part of the shared Story route or a separate view? | Separate view. `/timeline` remains a purely shared Read Model with no private variant and no `visibility` parameter; the owner area is served by the existing HeartMoment collection. See #104. |
| M2-D23 | BLOCKING | DECIDED | Security + Media | In what order are image and video processing delivered, and which parsers enter the project? | Images first with Pillow and pillow-heif; video including ffmpeg follows as a separate slice. Until then, the server rejects MP4/QuickTime fail-closed. See #85. |
| M2-D24 | BLOCKING | DECIDED | API + Security | How does the owner read a still-unbound attachment when AttachmentReadRequest requires a parent reference? | Add `parentType: "NONE"` to the union for an own unbound upload in the binding window. Owner, `READY`, and window are checked server-side. See #79. |
| M2-D25 | BLOCKING | DECIDED | Product + Domain | May the partner change or delete the other person's Milestone? | No. Both can read; Update and Delete remain with the immutable author, as with Memory (M2-D01). See #94. |

## Binding domain/privacy principles for M2

- Public domain/API language uses `visibility = SHARED | PRIVATE` where a resource supports both visibility states.
- `SPACE_SHARED` and `OWNER_ONLY` remain internal authorization/persistence classes; clients do not write `privacyClass` as a second source of truth.
- `PRIVATE` is not post-hoc UI filtering. Unauthorized rows are excluded by the authorized data query itself.
- ProtectedPayload is an architecture and leakage boundary, not a claim of real E2EE.
- Memory and Milestone are shared space content; HeartMoment may be `SHARED` or `PRIVATE`; Comment has no independent visibility and inherits parent reachability.
- Author/owner IDs are immutable after creation. Normal updates cannot transfer ownership.

## Decided entries

### M2-D01 – Memory write permissions
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Product + Domain / project decision #68  
Decision: A Memory is shared content readable by both active space partners. Update and Delete may be performed exclusively by the immutable `authorId`. The partner may change or delete neither content nor non-content fields. Future collaboration requires a new explicit domain decision and must not silently weaken this rule.  
Rationale: Shared readability is not write authority. The author rule prevents surprising changes/deletions of personal memories and provides a simple, testable ownership boundary.  
Consequences: Create sets `authorId` from Authorization Context. Read/List allow both active space members. Update/Delete require membership + authorized resource query + author check + current version. Foreign space remains 404; a visible partner Memory without write permission follows the existing 403-vs-404 convention for known shared resources. Web/Android must not offer active Edit/Delete actions to the partner.  
Tests: author CRUD; partner read/list; partner update/delete denied; foreign space 404; stale author update/delete 409; `authorId` immutable.  
References: #68, `DOMAIN-MODEL.md`, `PROJECT-CONTROL.md`.

### M2-D02 – Optimistic concurrency for Comments
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Domain + API / project decision #68  
Decision: Comments are editable entities and receive a persisted `version` field. Update and Delete require `If-Match` according to the same API convention as other mutable M1/M2 resources; stale versions deterministically produce `409 RESOURCE_VERSION_CONFLICT`. Only the immutable Comment author may change the body or delete the Comment.  
Rationale: Without versioning, Comment editing would be an isolated last-write-wins exception and break the global concurrency invariant.  
Consequences: Comment DTO exposes `version`/ETag; Create starts at version 1; every persisted change increments the version. Parent privacy/delete can atomically remove Comments as a server-side domain operation without an If-Match supplied by the Comment author.  
Tests: author update/delete; partner denied; stale update/delete 409; parent cascade despite Comment ownership; cross-space 404.  
References: #68, `DOMAIN-MODEL.md`, existing API concurrency convention.

### M2-D06 – HeartMoment emotion is ProtectedPayload
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Security + Privacy / project decision #68  
Decision: `emotion` is classified as ProtectedPayload together with HeartMoment `text`. The value may be returned through the authorized resource API to permitted clients, but is not general metadata and must not be copied into analytics, logs, notification previews, Domain Event payloads, metric labels, or search indexes outside the protected content boundary.  
Rationale: Emotion describes sensitive relationship content and can enable private inference independently of the text. The plaintext value is unnecessary for sorting, tenant isolation, or routing.  
Consequences: Persistence must respect the ProtectedPayload abstraction; future encryptability cannot depend on plaintext emotion in indexes/events. Filtering by emotion is not part of the M2 contract.  
Tests: events/logs contain no emotion; private HeartMoment remains fully owner-only; serialization returns emotion only after successful resource authorization.  
References: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D07 – HeartMoment SHARED to PRIVATE
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Domain + Privacy / project decision #68  
Decision: A `SHARED -> PRIVATE` change is an atomic domain operation. In the same DB transaction, the privacy class becomes `OWNER_ONLY` and all Comments on the HeartMoment are domain-deleted. After commit, no partner visibility may remain through Comment, Story, Activity, Notification, Cache, or Event projections. The API response reveals neither Comment count nor earlier private state to the partner after the change. `PRIVATE -> SHARED` does not restore deleted Comments.  
Rationale: Comments are shared content on a formerly shared parent. Merely hiding them would complicate retention/re-sharing semantics and could later make partner data unexpectedly visible again. Deletion is the clearest privacy boundary.  
Consequences: Before `SHARED -> PRIVATE`, the UI must warn generally that existing Comments are removed. It must not disclose another person's private data. Projections/consumers receive only safe IDs/state changes.  
Tests: change and Comment deletion atomic; rollback preserves old state completely; Story/partner GET after commit without leak; PRIVATE->SHARED resurrects nothing; race with Comment Create is serialized or rejected without inconsistency.  
References: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D11 – Domain delete/retention rules
Status: DECIDED (DOMAIN); media part below  
Date: 2026-08-25  
Decision owner: Data + Privacy / project decision #68  
Decision: Domain delete makes the resource unreadable immediately when commit succeeds. Story is a non-persisted Read Model and needs no separate deletion. Comments are dependent domain objects and are deleted atomically in the same DB transaction when their parent is deleted. Domain Events/audit may retain IDs, types, versions, actor/space reference, timestamp, and safe states required for technical traceability, but no ProtectedPayload. Physical blob deletion, orphan retention, and cleanup retry are decided separately in #69.  
Rationale: Privacy requires immediate domain invisibility while external storage I/O must not be unreliably coupled to the DB transaction.  
Consequences: Parent delete and Comment cascade are one DB transaction. Cleanup is event/job based and idempotent. Historical events must not become a shadow copy of deleted content.  
Tests: after commit 404/no list or Story row; transaction rollback restores parent+Comments; event contains no ProtectedPayload; storage cleanup failure does not make deleted domain resource visible again.  
References: #68, #69, `DOMAIN-MODEL.md`, `MEDIA-PIPELINE.md`.

### M2-D16 – Minimal M2 Domain Event schema
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Architecture + Security / project decision #68  
Decision: Every M2 Domain Event uses at least the envelope `eventId`, `eventType`, `occurredAt`, `spaceId`, `actorId`, `resourceType`, `resourceId`, `resourceVersion`. Event-specific payload may contain only additional IDs, technical timestamps, and states/categories explicitly classified as safe. Forbidden are ProtectedPayload fields, Comment body, Memory/Milestone title and body, HeartMoment text/emotion, original filenames, storage keys, download URLs, and unnecessary personal metadata. Delete events may contain the last known resource ID/version and `deletedAt`, but not deleted content.  
Rationale: Consumers need stable routing/invalidation data, not sensitive content. A small envelope reduces leakage in Outbox, logs, retries, and observability and preserves future encryption options.  
Consequences: Notification/Activity consumers load required presentation under their own authorization or use generic text; they must not expect a sensitive snapshot in the event. A `PRIVATE` HeartMoment creates no partner-directed Activity/Notification.  
Tests: schema/contract test per event type; negative tests for forbidden keys/values; private events create no partner projection; Outbox and logs contain no ProtectedPayload.  
References: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D03 – Attachment binding
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Domain + Data / project decision #69  
Decision: An attachment belongs to exactly one space and owner and may be bound to at most one domain resource in M2. Memory uses an explicit `MemoryAttachment` relation with unique zero-based `position`; HeartMoment has at most one attachment. Reuse of the same attachment record across multiple parents and cross-space binding are forbidden.  
Rationale: Exclusive binding keeps parent authorization and cleanup unambiguous and avoids many-to-many privacy races.  
Consequences: Binding requires owner + writable parent in the same space + READY within the binding window and is atomic.  
References: #69, `MEDIA-PIPELINE.md`.

### M2-D04 – Media allowlist and limits
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Security + Product / project decision #69  
Decision: JPEG/PNG/WebP/HEIC/HEIF images up to 25 MiB, 40 MP, and 12,000 px/edge. MP4/QuickTime video up to 250 MiB, 180 seconds, and 3840×2160. Memory at most 20 attachments and 500 MiB; HeartMoment at most one. All other types fail closed.  
Rationale: A small allowlist covers common smartphone media while limiting parser, storage, and DoS risk.  
Consequences: The server checks actual bytes/MIME/size/dimensions/duration; client values are UX only.  
References: #69, `MEDIA-PIPELINE.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D05 – Asynchronous validation and states
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Backend + Ops / project decision #69  
Decision: `finalizeUpload` atomically sets `VALIDATING` and enqueues an idempotent job. Internal states are `PENDING`, `UPLOADING`, `VALIDATING`, `READY`, `FAILED`, `DELETING`, `DELETE_FAILED`.  
Rationale: Media parsers and provider I/O do not belong in a long HTTP/DB transaction; the same contract works for local and S3.  
Consequences: Clients do not treat Finalize as upload success and observe status; concurrent Finalize is serialized.  
References: #69, `MEDIA-PIPELINE.md`.

### M2-D11 – Media delete/cleanup extension
Status: DECIDED (MEDIA)  
Date: 2026-08-25  
Decision owner: Data + Privacy / project decision #69  
Decision: When the last allowed parent reference is removed or an orphan becomes due, the DB atomically marks the attachment `DELETING`. Provider deletion happens outside the domain transaction through an idempotent job. Failures produce `DELETE_FAILED` with repeated retry/alerting; they never make domain content visible again.  
Rationale: External storage I/O must not be unreliably coupled to the DB transaction.  
Consequences: Cleanup is observable; metadata is finally removed/terminalized only after successful provider cleanup.  
References: #69, #68, `MEDIA-PIPELINE.md`.

### M2-D12 – Upload retention
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Backend + Ops / project decision #69  
Decision: PENDING without completion, UPLOADING without Finalize, and FAILED become cleanup-eligible after 24 hours. Cleanup runs at least hourly. `DELETE_FAILED` has no automatic forgetting period and remains visible/measured until success or manual intervention.  
Rationale: 24 hours tolerates mobile interruption while preventing permanent orphans.  
Consequences: Retention uses server-side timestamps, never client time.  
References: #69, `MEDIA-PIPELINE.md`.

### M2-D13 – Upload/read transport
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Security + Media / project decision #69  
Decision: LocalMediaStore accepts uploads through an authorized server-side streaming route. S3MediaStore may use presigned Upload URLs with a maximum TTL of 10 minutes. Reads: local streams server-side after authorization; S3 returns a signed URL only after parent authorization with a maximum TTL of 5 minutes. Bucket/storage remain private.  
Rationale: Adapters may optimize transport but not bypass domain authorization or Finalize.  
Consequences: Do not log/persist URLs or signatures; residual validity after permission revocation is limited to at most 5 minutes for S3 and documented as a trade-off.  
References: #69, `MEDIA-PIPELINE.md`.

### M2-D20 – READY without parent
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Domain / project decision #69  
Decision: A READY attachment may remain unbound for at most 60 minutes from `readyAt` and is manageable only by its owner during that time. It then becomes cleanup-eligible. Binding and cleanup are serialized through state checking/row lock.  
Rationale: A short window decouples upload from parent mutation without creating durably readable orphans.  
Consequences: After successful binding, lifetime follows the parent; there is no partner access merely because the attachment is READY.  
References: #69, `MEDIA-PIPELINE.md`.

### M2-D08 – Story sorting and cursor
Status: DECIDED  
Date: 2026-08-25  
Decision owner: API + Data / project decision #70  
Decision: Story uses `effectiveDate = happenedOn ?? UTC_DATE(createdAt)` and the full keyset key `(effectiveDate, createdAt, kindRank, id)`. `kindRank` is `MEMORY=1`, `HEART_MOMENT=2`, `MILESTONE=3`. ASC/DESC apply the same direction to the entire tuple. The cursor is opaque, versioned, integrity-protected, and bound to space and `type`/`year`/`order`.  
Rationale: A complete unique key prevents tie duplicates/gaps without offset pagination and remains deterministic for heterogeneous Story unions.  
Consequences: `q` remains M4. Privacy/tenant filters run before sorting. A manipulated or context-foreign cursor returns `400 INVALID_CURSOR` without foreign metadata. No historical snapshot is promised when a sort field changes concurrently; clients refresh.  
Tests: identical effectiveDate/createdAt across all kinds; ASC/DESC; cursor with changed space/filter/order; PRIVATE HeartMoment never in union; no tie duplicates/gaps on unchanged data.  
References: #70, `API-DESIGN.md`, `API-CONTRACT.json`.

### M2-D09 – Routes, nesting, and DTO names
Status: DECIDED  
Date: 2026-08-25  
Decision owner: API / project decision #70  
Decision: M2 remains completely under `/api/v1/spaces/{spaceId}`. Memories, HeartMoments, Milestones, and Attachments have their own collections. Comment Create/List are nested under the parent; Comment Update/Delete use `/comments/{commentId}` within the space. Story remains `/timeline`. Privacy changes for HeartMoment use an explicit `/visibility` mutation. DTO/operationId names are frozen in `API-DESIGN.md` and machine-readably in `API-CONTRACT.json`.  
Rationale: Parent nesting for Comment Create/List eliminates freely selectable target IDs/types from the body; space scoping matches the existing Tenant Guard. A dedicated privacy endpoint makes destructive SHARED->PRIVATE semantics explicit.  
Consequences: Clients write neither `privacyClass` nor storage internals. All mutations of existing resources use If-Match. `backend/openapi.json` is updated by the existing generator only when runtime slices are implemented; the manifest is not a second production OpenAPI contract.  
Tests: unique operationIds/method-path pairs; all paths space-scoped; If-Match matrix; no `privacyClass` write fields; Attachment descriptor without storage keys/bucket/provider.  
References: #70, `API-DESIGN.md`, `API-CONTRACT.json`, `backend/tests/test_m2_api_contract_manifest.py`.

### M2-D14 – EXIF/metadata removal during ingest
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Privacy + Product / project decision #78  
Decision: Embedded metadata is removed during ingest. Before stripping, the existing validation job extracts a closed allowlist of technical fields into ProtectedPayload: capture time, orientation, width, height, and for video duration. Everything else — GPS/location, device and serial numbers, software, author and copyright fields, comment/description fields, container thumbnails, and unknown segments — is discarded. Only the sanitized file is stored; uploaded original bytes are not retained durably. The allowlist is fail-closed: an unlisted field is removed, not retained.  
Rationale: A blacklist of known location fields is not exhaustive — containers can transport location in vendor-specific and newly introduced segments. Only an allowlist matches M2's existing fail-closed line for MIME and format validation. Stripping during ingest leaves exactly one stored object, so export, backup, and every future read path do not have to decide again which copy may leave the system. Extracting before stripping preserves useful domain data: capture time remains available as a proposal source for `happenedOn`.  
Consequences: The validation step from M2-D05 rewrites the object; `READY` is set only after successful stripping. Media that cannot be sanitized safely fails closed to `FAILED` and is not stored unstripped. The extracted allowlist is ProtectedPayload and is not projected into events, logs, metrics, or indexes. A future “download original with metadata” feature does not exist and requires a new decision. M2-D17 (Export) may assume that media objects contain no location metadata.  
Tests: image with GPS tag is location-free after `READY`; vendor segment containing location is removed as well; unknown metadata segment does not survive ingest; capture time exists as ProtectedPayload and appears in no Outbox row; unsanitizable media ends `FAILED` instead of `READY`; video retains duration and loses location.  
References: #78, `MEDIA-PIPELINE.md`, `PRIVACY-THREAT-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D15 – Scope of derived media variants
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Media + Product / project decision #78  
Decision: M2 creates at most one derived variant per attachment: a reduced thumbnail for images and one poster frame for video. Video transcoding, multiple resolution levels, audio extraction, and adaptive streaming are not part of M2. Variants are created server-side in the same validation job after M2-D14 has been applied, and contain no embedded metadata themselves.  
Rationale: M2 allows images up to 25 MiB and 40 MP. A Story timeline serving originals would miss every client budget and turn each list view into bandwidth amplification through the authorized read route — a misuse issue as well as a performance issue. The poster frame adds little extra work because validation for duration and resolution already requires a server-side media probe. Transcoding, by contrast, would add a large dependency with attack surface and long job runtimes to the first media slice and conflict with the goal of keeping S1 a manageable security surface.  
Consequences: The storage key receives controlled server-side variant suffixes under the existing pattern; clients cannot select variant keys. A variant has no separate authorization and follows its attachment and parent exactly. Cleanup removes variants with the attachment; an orphaned variant is a cleanup failure, not an allowed state. Failed variant generation does not set the attachment to `FAILED`; it serves the attachment without a variant — a missing thumbnail is a presentation issue, not a security failure. Video without a poster frame is presented neutrally by the client.  
Tests: thumbnail and poster frame exist after `READY` and contain no metadata; variant cannot be read without parent read permission; parent privacy change also blocks variant; Delete removes original and variants; failed variant generation leaves attachment usable; no client-selectable variant key.  
References: #78, `MEDIA-PIPELINE.md`, `DELIVERY-PLAN.md`.

### M2-D23 – Media-processing order and parsers
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Security + Media / project decision #85  
Decision: Media processing is delivered in two steps. The first slice handles images only — JPEG, PNG, WebP, HEIC, and HEIF — completely: validation, metadata removal under M2-D14, and thumbnail under M2-D15. `Pillow` and `pillow-heif` enter the project for this; HEIC/HEIF is in the D04 allowlist and cannot be supported without libheif. Video and poster frames follow in a separate slice together with ffmpeg. Until that slice is delivered, the server rejects MP4 and QuickTime fail-closed even though M2-D04 allows them.  
Rationale: Parsing untrusted media is the riskiest code surface in the product. Adding image and video parsers at once creates the entire attack surface in one step and makes the first media slice too large for careful review. The questions also differ in nature: Pillow is a library decision, while ffmpeg is an operational decision affecting container images and self-hosted installation — and a system binary is invisible to the existing `uv audit` gate, so it needs its own evidence path.  
Consequences: M2-D04 remains unchanged as a contract; the gap between allowed contract and current server response is explicitly documented and not a silent difference. Until then, video upload ends with `ATTACHMENT_TYPE_NOT_ALLOWED`, not a server error or hanging `PENDING`. Clients must not offer video as available in M2. Before implementation, the video slice must resolve the ffmpeg question including image size, CVE tracking, and transcoding resource limits. The inventory entry for `Pillow` and `pillow-heif` is created in #79 together with declaration because the dependency gate treats a documented row without a declaration as an error.  
Tests: video MIME is rejected while the video slice is absent; rejection uses a stable error code and leaves no object in the store; HEIC/HEIF reaches `READY`; all allowed image formats complete stripping and thumbnailing.  
References: #85, #79, `MEDIA-PIPELINE.md`, `DELIVERY-PLAN.md`.

### M2-D24 – Read access to unbound attachments
Status: DECIDED  
Date: 2026-08-25  
Decision owner: API + Security / project decision #79  
Decision: `AttachmentReadRequest` is extended additively with `{ parentType: "NONE" }`. It denotes the owner's own still-unbound upload within the M2-D20 binding window. Existing `MEMORY` and `HEART_MOMENT` variants remain valid unchanged. `NONE` is invalid for an already bound attachment; only parent reachability applies there.  
Rationale: Section 8 of the media pipeline already allows the case — a `READY` attachment without a parent is visible to its owner within the window. The request contract frozen in #70 simply could not express it because it was a closed union over two parent types. Without the variant, the owner could not view a just-uploaded image and the first media slice could prove only the absence, not the authorized read path.  
Consequences: The variant is not an authorization shortcut. The server requires owner identity, state `READY`, and an unexpired binding window; afterward readability again follows the parent exclusively. A partner never obtains access with `NONE`, even to an unbound attachment in the same space. After the window expires, the attachment becomes `DELETING` anyway. The extension is backward-compatible: existing clients continue to send a parent reference.  
Tests: owner reads own unbound upload; partner receives 404; `NONE` on a bound attachment is rejected; expired window returns 404; `NONE` on foreign or non-`READY` attachment returns 404.  
References: #79, `API-DESIGN.md`, `API-CONTRACT.json`, `MEDIA-PIPELINE.md`.

### M2-D25 – Milestone write permissions
Status: DECIDED  
Date: 2026-08-25  
Decision owner: Product + Domain / project decision #94  
Decision: A Milestone is shared content readable by both active space partners. Update and Delete may be performed exclusively by the immutable `authorId` — the same rule as Memory under M2-D01. Shared readability does not grant write authority.  
Rationale: The domain model explicitly left this question open and, until resolved, prohibited deriving partner write permission from shared readability. The decisive factor was reversibility: opening collaborative editing later is additive and endangers no existing content; closing it later would remove functionality from couples who had relied on it. It also keeps authorization on one already-tested rule; otherwise Milestone would be the first resource whose read and write boundaries differ.  
Consequences: `authorization.rules` needs no new rule class — `SPACE_SHARED` remains readable by the space and writable only by the owner. Create sets `authorId` from Authorization Context; the partner's `capabilities` contains neither Edit nor Delete. Future collaborative editing requires a new explicit decision and a dedicated rule in the table, not an endpoint exception.  
Tests: author CRUD; partner read/list; partner update/delete denied with 403; foreign space 404; stale `If-Match` 409; `authorId` immutable.  
References: #94, `DOMAIN-MODEL.md`, `authorization/rules.py`.

### M2-D22 – Owner view for private HeartMoments
Status: DECIDED  
Priority: raised from `BEFORE_CLIENTS` to `BLOCKING`  
Date: 2026-08-25  
Decision owner: Product + UX / project decision #104  
Decision: The owner area for private HeartMoments is a separate view and not part of the shared Story route. `GET /spaces/{spaceId}/timeline` returns shared content only; there is no `PRIVATE` variant of the Story union, no `visibility` parameter, no owner mode, and no count of private entries. The owner area is served by the existing collection `GET /spaces/{spaceId}/heart-moments?visibility=PRIVATE`. M2 adds no new route for it. The rejected alternative was to extend `/timeline` with an owner mode that additionally mixes in the caller's private HeartMoments.  
Rationale: Both options can be implemented correctly — the difference is how often the privacy question must be re-answered later. A Story route with owner mode would have two result sets under one `operationId`, and every later Story property would need to account for it individually: month groups, counters, cursor binding, client cache, prefetch, export, and M4 Read Models. Each would be another opportunity to lose the mode; a missing mode would not look like an error, but like a plausible row in the shared history. A separate view makes the boundary visible at the route itself and lets Story remain what M2-D11 already defines: a derived Read Model over shared content. The separate variant is also already proven — `list_heart_moments` filters `visibility` only after `readable()` and therefore returns the partner an empty page instead of foreign private rows. The decision is reversible as well: offering a combined view later is additive, while enriching an established shared route with private content later would remove assumptions and create a migration problem for client caches.  
Consequences: The Story union in `API-DESIGN.md` remains unchanged with `MEMORY`, `HEART_MOMENT` (only `SHARED`), and `MILESTONE`. `/timeline` accepts no `visibility` parameter; supplying one is a request error, not a silently ignored filter. Cursor binding from M2-D08 needs no owner dimension because the result set does not depend on a mode. The privacy filter remains part of the authorized query and is not modeled as a Story parameter. Web and Android present the owner area as a separate, clearly marked view rather than a filter chip in Story; switching there is a navigation step, not a list option. M2-D18 therefore treats the owner cache as a separate cache alongside the Story cache. M4-A Read Models and M4-B Activity inherit this boundary and must not reintroduce private HeartMoments through a shared projection. The separation of owner and partner export under M2-D17 remains unaffected.  
Tests: `/timeline` contains no owner's private HeartMoment; `/timeline` with `visibility` parameter is rejected rather than filtered; `SHARED -> PRIVATE` removes the item for both sides from `/timeline` and leaves it in the owner list; `heart-moments?visibility=PRIVATE` returns an empty page to the partner; a Story cursor cannot be rewritten to address private rows.  
References: #104, #70, `API-DESIGN.md`, `API-CONTRACT.json`, `DELIVERY-PLAN.md`.

## Decision format

When approved, update the table row and add an entry below:

```text
### M2-Dxx – Short title
Status: DECIDED
Date: YYYY-MM-DD
Decision owner: Role/Name
Decision: ...
Rationale: ...
Consequences: ...
References: ADR / Spec / Issue / PR
```

## Definition of “decision-ready”

A decision is complete only when:

1. the chosen option and consciously rejected alternative are clear,
2. privacy, security, and data-migration consequences are named,
3. API, Web, Android, and operational consequences are considered,
4. tests and acceptance criteria can be derived from it,
5. a binding source is linked.
