# SideBySide Next - Freemium Feature Matrix

**Status:** authoritative product-tier baseline for implemented capabilities  
**Version:** 1.0  
**Audit date:** 2026-08-30  
**Audited `main` baseline:** `b10390ace37056fc6789ffe1368d20479b8fb345`  
**Owning baseline audit:** #270  
**Ongoing product strategy:** #262

## Purpose and authority

This document records the first repository-wide business/freemium classification of the SideBySide Next implementation after business-model consistency became a mandatory development invariant.

It is authoritative for the commercial/product-tier classification of capabilities that are already implemented on the audited M0-M3 baseline. It does not replace the functional, Security, Privacy, Clean-Room, or architectural requirements in the product specifications.

For capabilities that are not yet implemented, issue #262 remains the working product-decision source until a decision is promoted into this or another versioned repository document.

When sources appear to conflict:

1. Security, Privacy, Tenant Isolation, data-rights, and Clean-Room requirements cannot be weakened by monetization.
2. `specification/CLEAN-ROOM-MASTER-SPEC.md` and `specification/PRODUCT-SPEC.md` remain binding for product and technical requirements.
3. `docs/BUSINESS-MODEL.md` defines the operating/commercial model.
4. This matrix defines the current product-tier classification of implemented capabilities.
5. #262 supplies working decisions for future or still-unresolved tier boundaries.

Any later change to an existing classification must update the versioned product decision before or with the implementation that depends on it.

## Executive result

The audited M0-M3 implementation does **not** require a retroactive broad paywall retrofit.

All currently implemented major user capabilities fit one of these patterns:

- **Free/Core** - the capability is part of the meaningful baseline product;
- **Non-paywallable** - trust, Security, Privacy, Accessibility, or data-rights behavior must remain available independent of Premium;
- **Mixed, Free side currently implemented** - the existing implementation is the Free baseline and future richer extensions may be Premium.

No currently implemented M0-M3 capability is classified as a whole-feature Premium-only capability in this baseline.

This is intentional. Premium should primarily monetize richer presentation, automation, advanced organization, insights, integrations, and managed resource consumption rather than revoke the relationship history and everyday Core that users already created.

Consequences:

- no M0-M3 user data needs to become inaccessible when Premium launches;
- no blanket grandfathering is required for the audited M0-M3 capability set;
- no M0-M3 entitlement gate needs to be added merely to complete #270;
- future Premium extensions must use the centralized entitlement architecture defined through #262/M9 instead of ad-hoc feature checks;
- if a future product decision changes an existing capability from this baseline to whole-feature Premium, that change requires an explicit matrix revision and migration decision before runtime gating.

## Classification vocabulary

### Free/Core

A meaningful SideBySide baseline capability. It may have future Premium extensions, but ordinary use of the listed current capability does not require Premium.

### Premium

A capability available only under an appropriate Premium entitlement. No currently implemented M0-M3 capability is wholly classified this way by this baseline.

### Mixed

A product area with a meaningful Free baseline plus separately defined Premium extensions. The matrix states which side of the boundary is currently implemented.

### Non-paywallable

A capability or behavior that must not be monetized as an access restriction because it is required for Security, Privacy, Accessibility, account protection, deletion, or essential data portability.

### Undecided

Allowed only temporarily for a concrete unresolved product decision. None of the implemented M0-M3 capabilities needs this classification after the audit.

## Audited implementation evidence

The audit checked the current implementation rather than relying only on issue titles or roadmap claims.

The production API router on the audited baseline includes the implemented M1-M3 surfaces for authentication, invitations, attachments, Story, Memories, Milestones, HeartMoments, Comments, people, profiles, Spaces, Wishes, Places and typed Place relations, Plans, Chapters and typed Chapter relations, shared Collections, PrivateNote/GiftIdea, and PrivateCollections.

The current API does **not** register M4 Search/Dashboard/Activity/Notification/Reminder/Rule routes, M6 Question/Recap routes, M7 external product integrations, or M9 billing/entitlement routes. Those remain later-milestone work.

The current Web and Android clients provide the thin M2 reference/product evidence flow rather than complete M1-M3 client parity. Full Web/Android productization remains M5.

The Web implementation already supports `system`, `light`, and `dark` appearance preferences. Android has a standard light/dark Material theme following the system state. Those standard accessibility/platform appearance behaviors are part of the Free baseline.

The MediaStore supports local Self-Hosted storage and an S3-compatible adapter. Current media limits are technical/security processing limits, not commercial quotas. The audited code contains no hosted Free/Premium storage-quota or billing enforcement.

## Implemented capability matrix

| Capability | Implementation baseline | Classification | Gating shape | Audit result | Rationale / future boundary |
| --- | --- | --- | --- | --- | --- |
| Account identity and normal account access | M1 backend/API | **Free/Core** | Whole feature Free | Consistent | A user must be able to enter and use the product without Premium. |
| Authentication security, session protection, recovery, email verification and supported Passkey behavior | M1 backend/API | **Non-paywallable** | Non-paywallable | Consistent | Account protection and recovery are trust/Security functions, not Premium differentiators. |
| Supported Self-Hosted auth mechanisms such as local password and OIDC | M1 backend/API | **Free/Core** | Whole feature Free within the applicable operating model | Consistent | OIDC here is an authentication mechanism, not a commercial content integration. It must not be confused with Premium integrations such as Immich/Dawarich. |
| Space creation, Membership and partner connection/invitations | M1 backend/API | **Free/Core** | Whole feature Free | Consistent | The couple/relationship context is the product entry point. |
| Tenant isolation and membership authorization | M1/core | **Non-paywallable** | Non-paywallable | Consistent | Isolation is a mandatory Security invariant. |
| SpaceProfile and basic relationship duration/context | M1 backend/API | **Free/Core** | Whole feature Free | Consistent | Basic couple context is part of the meaningful product baseline. |
| PartnerProfile and ProfilePreference | M1 backend/API | **Free/Core** | Whole feature Free | Consistent | Basic partner profile/preferences support the normal relationship product. |
| RelatedPerson basic management | M1 backend/API | **Free/Core** | Free baseline of a future Mixed area | Consistent | Storing relevant people is normal utility; future occasion automation may be Premium. |
| ImportantDate basic management | M1 backend/API | **Free/Core** | Free baseline of a future Mixed area | Consistent | Basic dates stay Free; advanced reminder/occasion workflows may be Premium. |
| Memory CRUD | M2 backend/API + thin Web/Android flow | **Free/Core** | Whole feature Free | Consistent | Memories are central SideBySide data. No artificial Memory-count limit. |
| Image attachment upload, validation, binding and normal authorized reads | M2 backend/API + thin Web/Android flow | **Free/Core** | Functional feature Free; Cloud resource quota may be Mixed | Consistent | Normal images are part of a Memory. Hosted byte consumption may later be quota-controlled without paywalling the functional right to use images. |
| Attachment Privacy/authorization and media validation | M2/core | **Non-paywallable** | Non-paywallable | Consistent | Security and Privacy protections remain identical across tiers. |
| Video attachment support | Contracted but intentionally not implemented; #88 | **Undecided for future processing tier** | Future decision | Not part of current implementation baseline | Current server fails closed. Future video storage/processing may justify Premium or fair-use compute rules, but #270 does not decide or implement them. |
| HeartMoment basic shared interaction | M2 backend/API | **Free/Core** | Whole feature Free | Consistent | Lightweight emotional interaction is part of the everyday product. |
| HeartMoment `PRIVATE` / `OWNER_ONLY` enforcement | M2 backend/API | **Non-paywallable** | Non-paywallable | Consistent | Privacy itself can never be a Premium feature. |
| Milestone CRUD | M2 backend/API | **Free/Core** | Whole feature Free | Consistent | Milestones belong to the basic shared history. |
| Comments on supported shared content | M2 backend/API | **Free/Core** | Whole feature Free | Consistent | Normal relationship interaction around shared content remains available. |
| Story / Timeline read model | M2 backend/API + thin Web/Android flow | **Free/Core** | Whole feature Free | Consistent | Users must retain normal access to their shared history. |
| Wish CRUD and normal lifecycle | M3 backend/API | **Free/Core** | Free baseline of a Mixed planning area | Consistent | Normal shared wishes remain Free; future advanced planning/automation may be Premium. |
| Plan CRUD, Wish-to-Plan conversion and normal lifecycle | M3 backend/API | **Free/Core** | Free baseline of a Mixed planning area | Consistent | Everyday planning is Core; future templates, automation, calendar sync or analytics may be Premium. |
| Place basic CRUD and optional coordinates | M3 backend/API | **Free/Core** | Free baseline of a Mixed place area | Consistent | Users can store ordinary places without Premium. Advanced map/history experiences may be Premium. |
| Typed Place-to-content relations | M3 backend/API | **Free/Core** | Whole current feature Free | Consistent | Linking a normal Place to existing Core content is part of the Free place baseline. |
| Chapter basic CRUD, content grouping and typed relations | M3 backend/API | **Mixed - current implementation is Free baseline** | Free baseline + future Premium presentation | Consistent | Basic grouping/organization remains usable. Rich covers, layouts, storytelling, export and automated curation are Premium candidates. |
| Shared Collection and CollectionItem CRUD/order/completion | M3 backend/API | **Free/Core** | Free baseline of a Mixed collection area | Consistent | Normal shared lists remain Free. Templates, recurring/reset workflows and advanced automation may be Premium. |
| PrivateNote basic CRUD | M3 backend/API | **Free/Core** | Free baseline of a Mixed private area | Consistent | A genuinely useful private area must exist without Premium. |
| PrivateNote owner-only authorization | M3/core | **Non-paywallable** | Non-paywallable | Consistent | Owner-only Privacy is mandatory independent of tier. |
| GiftIdea basic capture and lifecycle | M3 backend/API | **Free/Core** | Free baseline of a Mixed gift workflow | Consistent | Recording/managing an idea is basic utility. Occasion automation, history, templates and advanced reminder workflows may be Premium. |
| GiftIdea owner-only authorization | M3/core | **Non-paywallable** | Non-paywallable | Consistent | Privacy cannot depend on Premium. |
| PrivateCollection and PrivateCollectionItem CRUD/order/completion | M3 backend/API | **Free/Core** | Free baseline of a Mixed private-organization area | Consistent | Basic private organization remains Free; future advanced templates/automation may be Premium. |
| PrivateCollection owner-only authorization | M3/core | **Non-paywallable** | Non-paywallable | Consistent | Owner-only isolation is a Security/Privacy requirement. |
| Official Web access | thin M2 reference client currently; full parity M5 | **Free/Core** | Whole client access Free | Consistent | Premium must not be required merely to use the official Web client. |
| Official Android access | thin M2 reference client currently; full parity M5 | **Free/Core** | Whole client access Free | Consistent | Premium must not be required merely to use the official native client. |
| Standard Light/Dark/System appearance | Web and Android baseline | **Free/Core** | Whole current feature Free | Consistent | Platform expectation and accessibility-related appearance must not be Premium. Extended visual packs remain possible Premium extensions. |
| Localization/i18n behavior | client/platform baseline | **Non-paywallable** | Non-paywallable | Consistent | Correct locale behavior is product quality/accessibility, not a tier differentiator. |
| Accessibility essentials | partial/current + final M5/G4 QA pending | **Non-paywallable** | Non-paywallable | Consistent classification; completion still M5/G4 | Accessibility requirements cannot be gated by Premium. |

## Reconciliation with #262 working hypotheses

The audit validates the central #262 direction:

> Free lets a couple meaningfully use SideBySide; Premium monetizes richer experiences created from that data rather than the right to keep the relationship history itself.

### Confirmed from the existing implementation

- Memories, normal images, Timeline, HeartMoments, Milestones, Wishes, Plans, Places, Collections, and the basic Private Area fit the Free/Core baseline.
- Current basic Chapter behavior fits the **Free side of a Mixed Chapter model**. The current implementation does not yet contain the rich Premium presentation/curation layer proposed in #262.
- Current GiftIdea behavior is basic capture/lifecycle and therefore fits the Free side of the proposed Mixed gift workflow.
- Current RelatedPerson/ImportantDate behavior is basic management and therefore fits the Free side of the proposed Mixed occasion workflow.
- standard Light/Dark/System behavior is Free; Premium personalization means additional visual packs/layouts, not ordinary dark mode.
- current Web/Android access is Free; Premium is capability-based rather than client-based.

### Working-hypothesis wording corrected by the audit

The #262 discussion contains intentionally broad future-product wording. The factual baseline is narrower:

- current M2 Attachments implement **validated images**, not arbitrary general file storage; video remains deferred in #88;
- `HeartMoment` is implemented, but the separate `Ich denke an dich` / lightweight engagement experience belongs to M4 and must not be treated as already implemented merely because #262 discussed the concepts together;
- Search, Dashboard, Activity/Notifications, Reminders/Rules, Questions, Recaps, advanced Maps, Time Capsules, widgets, Immich, Dawarich, AI, designed yearbook PDF, animated year video, and rights-cleared music selection are **not** part of the audited M0-M3 runtime baseline.

These corrections do not reject the #262 Premium strategy; they prevent planned features from being mistaken for current implementation.

## Hosted versus Self-Hosted baseline

### Self-Hosted

The audited implementation is consistent with the business-model principle that Self-Hosted is a real product rather than a Cloud demo.

- LocalMediaStore is available for operator-provided local storage.
- S3-compatible MediaStore support exists as an infrastructure adapter.
- no `5 GB`, `50 GB`, Premium, billing, or other SaaS commercial storage quota is enforced in the current runtime;
- existing attachment size/type/dimension rules are technical Security/processing limits and are not commercial storage quotas;
- future Cloud quota logic must therefore remain deployment/entitlement aware and must not leak a managed SaaS quota into ordinary Self-Hosted storage.

### SideBySide Cloud / Managed

The code has relevant technical foundations such as an S3-compatible MediaStore, but the managed commercial layer is intentionally not implemented yet.

Current missing launch/productization capabilities include:

- relationship/couple-scoped managed storage accounting;
- normalized entitlement state;
- billing/license provider boundary;
- hosted Free/Premium storage quota enforcement;
- storage add-ons;
- commercial downgrade/grace handling;
- backup/restore productization;
- managed render/AI fair-use accounting where expensive Premium processing is later introduced.

These belong to #262/M9 and are not defects in the M0-M3 implementation.

### Hosted storage working values

#262 currently proposes **5 GB Cloud Free** and **50 GB Cloud Premium** per relationship/couple as working hypotheses, with optional separate storage add-ons.

Those numbers are **not finalized by this audit** and are not runtime constants. They require the cost/market validation already required by #262 before commercial launch.

The baseline rule is already firm:

- Cloud may enforce transparent managed-resource quotas;
- quota accounting should focus on durable user-originated media payloads;
- existing content is never deleted because a subscription/storage entitlement changes;
- over-quota state blocks new quota-consuming uploads rather than access to existing history;
- normal Self-Hosted storage is determined by the operator rather than a Cloud SaaS quota.

## Existing-user and migration result

The audited M0-M3 implementation creates no immediate destructive monetization migration problem because no current capability is newly classified as whole-feature Premium.

For the current baseline:

- existing Memories remain readable/editable under their normal authorization rules;
- existing images remain normal Core content; future Cloud quota state may prevent new uploads but must not hide/delete existing media;
- existing Wishes, Plans, Places, Collections, PrivateNotes, GiftIdeas and PrivateCollections remain in the Free baseline;
- existing basic Chapters remain available as the Free side of the Mixed Chapter model;
- Privacy/owner-only enforcement remains unchanged across all tiers.

If #262 later chooses to reclassify any currently implemented whole capability as Premium, implementation must stop until the matrix records:

1. the new classification and rationale;
2. existing-data read/create/edit/export behavior;
3. grace or grandfathering decision if any;
4. downgrade behavior;
5. relationship/couple entitlement ownership semantics.

## Managed-resource findings

The current implementation already creates resource surfaces that matter for a future Cloud cost model even though they are not yet commercially metered:

- durable original image media;
- generated image derivatives/thumbnails;
- PostgreSQL data growth;
- background Job/Worker processing;
- S3/object-storage requests when Cloud uses the S3 adapter;
- authentication email delivery where enabled;
- future backup/restore retention.

Later Premium candidates add materially different resource surfaces:

- video ingest/transcoding/poster generation;
- high-quality animated recap rendering;
- rights-cleared media catalog delivery;
- external provider/API calls;
- location/map processing;
- AI/inference.

Resource cost may justify a transparent quota or fair-use policy. It does not justify arbitrary limits on Core text/domain objects such as a tiny number of Memories, Wishes, Plans, or Collections.

## Entitlement architecture finding

The product specification deliberately separates `FeatureConfiguration` (technical activation) from `Entitlement` (commercial eligibility), but no runtime entitlement/billing implementation exists on the audited baseline.

That is consistent with the roadmap: Entitlements/Billing belong to M9, and broad Premium gating must not be pulled forward before #262 resolves the provider-neutral capability model, relationship ownership, lifecycle, restore, downgrade, offline/Self-Hosted, and failure semantics.

Therefore:

- do not add scattered `if premium` checks to current M0-M3 code;
- do not infer Premium from client-controlled flags;
- do not couple Domain authorization to a payment provider;
- when runtime Premium arrives, application code should consume stable capability entitlements behind a provider-neutral boundary;
- Tenant/Space and OWNER_ONLY authorization always execute independently of commercial entitlement.

## Follow-up findings

### Corrective runtime issues required now

**None for the audited M0-M3 implementation.**

The audit found no existing M0-M3 capability that must immediately be removed, paywalled, quota-limited, or migrated to make the current code consistent with the accepted freemium direction.

This is a positive result, not an absence of future work.

### Existing owning work

- **#262** remains the owning product/architecture decision for future Premium capability boundaries, relationship-scoped entitlements, hosted storage hypotheses, lifecycle, downgrade, restore, licensing, billing-provider boundaries and Premium UX.
- **#88** remains the existing future work item for video upload/poster support; its eventual commercial/resource treatment must be checked against this matrix and #262 before implementation.
- **M4+ issues** must apply the mandatory business/freemium consistency check at issue/PR time. In particular, basic Search and normal access to user-created content must not accidentally become Premium merely because M4 is implemented after this baseline.
- **M9** remains the roadmap milestone for runtime Entitlements/Billing/Cloud productization. Specific implementation issues should be created when the #262 decisions are sufficiently concrete and the milestone work is ready to start.

No duplicate follow-up issue is created merely to restate work already owned by #262, #88, or the roadmap.

## Future Premium pillars retained from #262

The audit does not make these unimplemented concepts part of the current runtime. It confirms that they remain coherent Premium directions because they add value on top of the Free baseline:

1. **Relive** - advanced Recaps, rich Chapters/presentation, designed PDF/yearbook export, animated `Our Year` video and rights-cleared music choices.
2. **Personalize** - extended themes, layouts, covers and advanced widgets beyond standard Light/Dark/System behavior.
3. **Automate** - advanced reminders, Rules, recurring workflows, occasion automation and automatic recap generation while preserving a useful basic engagement layer.
4. **Connect** - Immich, Dawarich, calendar and other maintained external integrations.
5. **Understand** - advanced statistics, maps, longitudinal insights and optional privacy-conscious AI-assisted experiences.

Other strong Premium concepts retained from #262 include `Our Places` map experiences, Time Capsules, advanced Daily Question packs/history and advanced memory resurfacing.

## Change-control rule

This matrix is versioned product policy, not a one-time audit artifact.

For each future feature issue/PR:

1. identify the relevant row or add a new capability row;
2. state whether the change is Free, Premium, Mixed, or Non-paywallable;
3. identify Self-Hosted/Cloud differences and managed-resource cost when relevant;
4. identify migration/downgrade implications when an existing capability changes;
5. update this document before merge if the product-tier contract changes.

A future implementation must not silently reinterpret `implemented` as `Free`, `Cloud` as `Premium`, or `Premium` as permission to weaken Security/Privacy/data rights.

## Baseline decision summary

At the M3/G3 boundary, the commercial architecture can proceed without retroactively taking Core functionality away from users:

> **M0-M3 is the Free relationship Core. Premium should primarily be layered above it through richer presentation, automation, insights, integrations, personalization, and justified managed-resource services.**

This baseline is deliberately compatible with both operating models:

- **Self-Hosted:** operator-provided infrastructure/storage plus the applicable Free/Premium product capabilities, without artificial Cloud storage quotas;
- **SideBySide Cloud:** managed infrastructure/storage plus the applicable Free/Premium capabilities, with transparent managed-resource tiers once their values are validated.
