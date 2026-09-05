# Space and relationship offboarding lifecycle

**Version:** 1.0  
**Owner:** #518  
**Baseline:** `main` at `cf9ec3d79bd9e8cc5a1da298c7003f4e3450731c`  
**Status:** Phase-1 contract; runtime/client slices must implement this contract before #518 can close.

This document freezes the M6-B Space/relationship offboarding boundary before public destructive runtime work starts. It reuses the existing `Space`, `Membership`, Invitation, privacy-class, Transfer Bundle, MediaStore, Job/Outbox, notification and client cache/session primitives. It does not create a second relationship model, a breakup-specific export, a parallel queue, or an Account-deletion shortcut.

## 1. Non-negotiable invariants

Four concepts remain distinct:

1. **Leave a Space** ends only the caller's own active Membership.
2. **Remove a partner** is a stronger privileged/abuse-sensitive action and is not exposed to normal partner clients in V1.
3. **End/delete a Space** is a Space lifecycle action and is not synonymous with either partner leaving or with Account deletion.
4. **Delete an Account** is the global #520 lifecycle and is already independent of this contract.

Additional invariants:

- a person may leave their own active Membership without partner consent, Premium, an exit reason, or a farewell message;
- Membership history is preserved while its Space/history exists; normal self-exit is `ACTIVE -> LEFT`, never a Membership hard delete;
- `REMOVED` is not a normal partner-to-partner V1 control; it remains available to already-authoritative internal lifecycles such as Account deletion and any future explicitly audited operator/abuse policy;
- an ended Membership never grants normal Space read/write access;
- `OWNER_ONLY` is never transferred or reclassified to `SPACE_SHARED`;
- ordinary self-exit does not delete, transfer, or rewrite legitimate `SPACE_SHARED` history while another active member remains;
- a new relationship never inherits a previous relationship's Space, content, invitations, private data, or authorization history;
- Account sessions remain valid when only one Space is left; only that Space context and data are invalidated locally;
- exit, essential portability and privacy cleanup are non-paywallable.

## 2. Existing authority to reuse

The current code already provides the correct foundations:

- `relationship.require_membership(...)` resolves only `MembershipStatus.ACTIVE` and returns privacy-safe 404 for foreign or ended Memberships;
- `relationship.end_membership(...)` preserves the historical Membership row and sets `LEFT` or `REMOVED` plus server-side `ended_at`;
- `Space` remains the tenant boundary and `Membership` remains the only path from Account to Space data;
- a couple Space has at most two active partners;
- Invitation tokens are one-time hashed credentials with row-locked acceptance;
- #345 Transfer Bundles already define `SHARED` and `PERSONAL` exports with current authorization rechecks;
- privacy-aware resources already expose `space_id`, `owner_id`, and `privacy_class`;
- attachment authorization follows the current parent binding and physical deletion already uses retry-safe MediaStore cleanup;
- Jobs, Outbox, Notification/Push and Reminder paths are the existing asynchronous boundaries to harden rather than replace;
- Web and Android already have per-Space state/cache invalidation primitives and multi-Space/awaiting-Space states;
- #520 owns Account-wide deletion and already proves that ended Memberships, owner-private cleanup and stale asynchronous work can be handled without ownership transfer.

The missing work is orchestration and product semantics around *one Membership ending while the Account stays active*.

## 3. V1 command matrix

| Action | V1 | Authority / effect |
|---|---|---|
| Leave my current Space | Supported | Authenticated Account may target only its own active Membership; `ACTIVE -> LEFT` |
| Remove the other partner | Not exposed to normal clients | No unilateral partner `REMOVED` command in V1 |
| End the relationship | Represented by the caller leaving their own Membership | It does not revoke the other Account's Membership or delete their data |
| Delete the whole Space | Separate retention/destruction lifecycle | Never hidden inside the ordinary leave command |
| Delete Account | #520 | Global Account/data lifecycle; not implemented here |
| Reconnect an ended Membership | Not supported in V1 | A later explicit same-pair reconnect design may supersede this contract; until then a new relationship uses a new Space |

This intentionally favors abuse safety: one partner can always remove *their own* access, but cannot silently remove the other's access or destroy the other's shared-history copy.

## 4. Authoritative self-exit transition

V1 exposes one server-authoritative self-exit command through the normal authenticated Space API. The exact route follows repository conventions; conceptually:

```text
POST /api/v1/spaces/{spaceId}/membership/leave
```

The request accepts no Account ID, Membership ID, target partner ID, deletion mode, or free-form reason.

### 4.1 Acceptance rules

The backend must:

1. resolve the caller from the authenticated session;
2. lock the Space/Membership lifecycle boundary;
3. verify that this exact Account has a Membership in this Space;
4. if it is `ACTIVE`, transition it to `LEFT` and set `ended_at` from the server clock;
5. revoke every still-open Invitation for the Space as part of the lifecycle boundary;
6. make the loss of Space authorization durable before slower privacy/media/cache cleanup is considered complete;
7. enqueue/reuse existing cleanup work only after that fail-closed transition is durable.

A repeated request by the same former member is idempotent: it observes the existing `LEFT` state and does not create a second Membership, second cleanup lifecycle, or second user-visible side effect. A caller that never belonged to the Space still receives the normal privacy-safe not-found result.

`REMOVED` is not produced by this self-service command.

### 4.2 Concurrency boundary

The accepted transition must serialize with Space-authorized work so a mutation that started with stale authorization cannot commit a new partner-visible effect after exit has become durable.

V1 implementation must use the central Membership authority rather than endpoint-specific flags. The preferred implementation is a shared/read lock (or equivalent authorization epoch) held by normal Space transactions and an exclusive lock for the offboarding transition. At minimum, every mutating/side-effect path must revalidate the Membership under the same serialization boundary immediately before commit/provider effect.

The required observable property is:

- work authorized and completed before the exit transition may stand;
- after the `LEFT` transition commits, no new Space write, notification, provider delivery, export/import effect, signed media authorization, or background partner effect may be authorized for the former member.

Cross-Space/resource-ID probes continue to use the existing privacy-safe 404 behavior.

## 5. Data lifecycle on self-exit

### 5.1 Shared content

If another active member remains, ordinary self-exit does **not** delete or transfer `SPACE_SHARED` content.

- the surviving active member keeps their normal existing read/write rights;
- the former member loses normal read/write rights immediately;
- historical authorship remains attached to the historical Membership/Account reference required by the existing domain model;
- ownership is not silently reassigned to the remaining partner;
- shared attachment/media remains with its retained shared parent;
- content-specific delete/retention rights continue to follow each domain's normal policy.

### 5.2 The leaving Account's `OWNER_ONLY` data

V1 chooses **deletion, not an account-level private archive**.

Space-bound `OWNER_ONLY` rows owned by the leaving Account are deleted by the offboarding convergence for that Space only. This decision is deliberate:

- keeping them would create inaccessible ghost data after `require_membership(...)` stops authorizing the Space;
- transferring/reclassifying them would violate the privacy model;
- building a new account-global private archive only for offboarding would create a second storage/authorization model;
- #345 already provides the privacy-safe `PERSONAL` export for a copy the user wants to keep.

Therefore:

- the UI must explain that personal/private data belonging to this Space is removed after exit;
- the user may complete a `PERSONAL` export first, but export is never mandatory;
- cleanup filters by **both** `space_id` and `owner_id`/`OWNER_ONLY`, so private data in another active Space is untouched;
- another Account's `OWNER_ONLY` rows are never modified;
- media follows binding-aware cleanup: private/unbound media whose surviving parent disappears is purged through the existing MediaStore path, while retained shared-parent media is preserved;
- retries are idempotent and cannot reclassify private data.

This is distinct from #520: Account deletion removes the Account's private data across all Spaces; self-exit removes only that Account's private data scoped to the one exited Space.

## 6. Export behavior before exit

Reuse #345 without a special breakup archive or weaker authorization path.

Before confirmation, clients may offer:

- `SHARED` export for currently authorized shared portable data;
- `PERSONAL` export for the same shared portable data plus the caller's own `OWNER_ONLY` data.

V1 has **no post-exit download grace credential**. The user must allow an export they want to keep to finish and download it before accepting exit.

When exit is accepted:

- pending/running Transfer exports/imports owned by the leaving Account for that Space are cancelled/expired through the existing Transfer lifecycle;
- server-side artifacts that are no longer authorized enter existing retry-safe cleanup;
- a previously downloaded user copy is outside server control;
- no Membership is kept `ACTIVE` merely so an export can finish;
- no stale artifact/token can bypass the ended Membership.

The confirmation UI should say this plainly rather than silently waiting for background export completion.

## 7. Relationship-history lock and invitations

A Space belongs to one relationship history. It cannot become a container for a later partner.

Once **any** Membership in a Space has ended (`LEFT` or `REMOVED`), the Space is relationship-history locked:

- no new normal invitation may be issued for that Space;
- every still-open invitation is revoked when the first Membership ends;
- invitation acceptance must revalidate the Space lifecycle under lock and reject a stale token;
- `add_member(...)` must not reactivate an ended Membership through the ordinary invitation path;
- `add_member(...)` must not add a different Account to a Space that already contains historical ended Memberships;
- an active member who later has a new partner creates a **new Space**;
- the new partner receives no old Space ID, history, media, cache, notification, or invitation state.

The current generic `add_member(...)` reactivation behavior is therefore not a public V1 reconnect contract and must be narrowed before the offboarding endpoint ships.

### 7.1 Reconnect

V1 does **not** reactivate an ended Space, even for the exact same former pair. If the same people reconnect, they create a new Space.

A future explicit same-pair reconnect feature may supersede this decision only through a new privacy/product contract with deliberate consent from both Accounts. It must never be inferred from an old invitation, Membership ID, or matching Account pair.

## 8. Last active member and whole-Space retention

Ordinary self-exit is not itself a whole-Space hard delete. When the final active Membership ends, the Space becomes a derived **orphaned/inactive historical context**:

```text
active_count == 0
orphaned_at = max(ended Membership.ended_at)
```

No second persisted Space-state model is required for V1; the current ServerAdmin lifecycle surfaces already derive lifecycle state from Membership rows.

### 8.1 Bounded V1 retention

A zero-active Space is inaccessible to normal users immediately and enters a **30-day offboarding retention window**. The window exists to separate the irreversible Membership-access transition from destructive whole-Space cleanup and to make the retention behavior explicit instead of indefinite.

After 30 days with still zero active Memberships:

- a normal existing Job scans/targets the orphaned Space for final shared-data/media purge;
- Space-owned `SPACE_SHARED` data and remaining Space media are removed through existing domain/MediaStore cleanup primitives;
- open Invitations are already revoked and cannot revive the Space;
- Membership rows remain only as long as required by the purge transaction/reference ordering, then the Space cascade may remove them once no retained Space history requires them;
- operational backups may still contain historical snapshots under #190's bounded operator retention, but those backups are not a live user-accessible archive.

If any future release adds explicit same-pair reconnect, it must define whether/how it can cancel this purge before the retention horizon. V1 has no such cancellation path.

The retention constant belongs to the authoritative Space-offboarding domain/configuration boundary and must not be extended by Premium/entitlement state.

## 9. Sessions, caches, offline state and drafts

Leaving one Space does **not** sign the Account out globally.

After server acceptance, Web and Android must:

- remove the exited Space from active Membership state;
- clear that Space's read cache, protected cache/media, drafts, pending uploads and pending mutation state;
- invalidate any locally cached signed/read descriptors for that Space;
- stop retrying mutations against that Space;
- ensure deep links to the old Space resolve to the existing privacy-safe unavailable state;
- if another active Space exists, select/offer an authorized active Space through the existing multi-Space path;
- otherwise enter the existing authenticated-without-active-Space / awaiting-Space state rather than logging out the Account.

If the device was offline while the Membership ended elsewhere, reconnect reconciliation must treat the server Membership list as authoritative and clear the same local state before presenting the Space as usable again.

A stale offline cache may not remain an interactive/readable normal Space after the client has learned that the Membership ended.

## 10. Notifications, reminders, jobs and provider effects

No second offboarding queue is introduced. Existing Job/Outbox/provider boundaries must revalidate current Membership immediately before side effects.

At minimum audit and cover:

- Activity/Notification projection;
- PushDelivery;
- ReminderPreference / ReminderOccurrence and rule jobs;
- Thinking-of-you and similar partner effects;
- Surprise/reveal/unlock jobs;
- recap/wrapped/book/PDF generation when present;
- Transfer export/import;
- attachment/media processing;
- notification digests and future relationship-depth jobs.

After exit:

- the former member receives no new Space-scoped push/reminder/reveal/digest;
- the surviving partner receives no stale partner effect generated from queued work that requires the former member still to be active;
- historical in-app records may remain only where their normal retention/read policy permits them and must not expose the former member's `OWNER_ONLY` data;
- stored Account/Space/resource IDs are never treated as durable authorization;
- retries converge to no-op/cancelled/expired states rather than restoring access.

No private exit reason is collected or delivered. V1 does not send a breakup/exit push merely because a Membership became `LEFT`; the surviving member sees authoritative relationship/Membership state when using the app.

## 11. Media

After `LEFT` commits:

- no new media read authorization or thumbnail/variant authorization is issued to the former member;
- already-issued bounded read/signed URLs expire under their existing TTL and are not refreshed;
- client media caches for the exited Space are invalidated when the client observes the transition;
- shared media retained for an active partner is not deleted merely because its uploader left;
- leaving-owner private/unbound media follows section 5.2 and existing retry-safe purge;
- final orphaned-Space media follows section 8 after the 30-day retention window.

No offboarding-specific storage backend is introduced.

## 12. API/client semantics

The public contract should expose a minimal accepted result containing only lifecycle state needed by clients, for example the ended Membership status and whether another active Space remains. It must not expose another Account's private state or invite a client to decide retention.

Error behavior:

- unauthenticated -> normal 401;
- foreign/non-member Space -> privacy-safe 404;
- already `LEFT` by the same Account -> idempotent safe result;
- `REMOVED` former Membership -> no self-service state change; safe ended-state response or repository-standard conflict, without disclosing partner/admin details;
- Demo behavior follows the normal Demo product contract; if public Demo fixtures must remain stable, the self-exit command must be disabled client-side and rejected server-side before mutation, reusing the authoritative Demo environment primitive rather than hard-coded identities.

OpenAPI remains canonical and Web/Android generated clients must be regenerated from the real API app.

## 13. Abuse and safety

- self-exit cannot be blocked by the partner;
- no joint consent is required to end one's own Membership;
- no reason field, breakup survey, farewell text, or forced partner contact is required;
- normal partners cannot remove each other in V1;
- no exit action grants new access to the other partner;
- no private-data export requires partner consent beyond current authorization;
- ServerAdmin remains an operations surface, not a relationship-content browser;
- any future forced removal needs its own authorization/audit policy and must reuse the same Membership/data cleanup semantics rather than direct SQL.

## 14. Business/freemium

All of the following are Core/non-paywallable:

- leaving one's own Space;
- the privacy cleanup caused by exit;
- essential `SHARED` / `PERSONAL` export while still authorized;
- client cache invalidation and access revocation;
- orphaned-Space retention/purge.

Premium expiry, entitlement downgrade or provider state cannot delay exit, preserve stale authorization, extend private-data retention, or make essential export a condition of leaving.

## 15. Required runtime slices

The contract is intentionally split before implementation:

1. **Backend lifecycle/API**
   - authoritative self-exit orchestration and locking;
   - scoped leaving-owner `OWNER_ONLY` cleanup;
   - invitation revocation/history lock and no implicit Membership reactivation;
   - Transfer/async/provider revalidation and orphaned-Space retention/purge;
   - OpenAPI + generated clients + tenant/race/retry tests.
2. **Web**
   - neutral consequences + optional export + explicit confirmation;
   - clear exited-Space query/cache/draft/mutation state;
   - switch to another authorized Space or awaiting-Space state;
   - offline/reconnect/deep-link handling.
3. **Android**
   - same server-authoritative journey;
   - Room/protected-cache/draft/upload invalidation;
   - multi-Space/awaiting-Space transition;
   - offline reconciliation.
4. **G5 evidence**
   - cross-Space/OWNER_ONLY negatives;
   - concurrent request/exit ordering;
   - stale invitation, export, push/reminder/job cases;
   - orphaned retention/purge;
   - Web/Android offline cache behavior.

## 16. Acceptance mapping for #518

The runtime is complete only when it proves:

- a user can leave their own active Membership without partner consent or Premium;
- Membership history uses `LEFT`/`REMOVED` rather than hard deletion during the retained Space lifecycle;
- ordinary Space access is unavailable immediately after exit;
- ordinary exit does not delete or transfer retained shared history while another active member remains;
- another Account's `OWNER_ONLY` remains invisible and untouched;
- #345 export is offered before exit without becoming a gate;
- leaving-owner Space-scoped `OWNER_ONLY` is deleted rather than stranded as ghost data;
- Account deletion, self-exit and whole-Space purge remain separate lifecycles;
- Web/Android caches, drafts and pending mutations cannot keep using the exited Space;
- Push/Reminder/Jobs/Surprise/Recap/Transfer effects revalidate current Membership;
- stale invitations cannot add/reconnect a partner into relationship-history-locked Space;
- a new partner always receives a new Space;
- V1 has no implicit reconnect of a former Membership;
- zero-active Spaces become inaccessible immediately and are purged after the bounded 30-day retention window;
- UX is neutral and non-manipulative;
- race, cross-Space, former-Membership and offline cases are negative-tested;
- Web and Android use one server-authoritative contract;
- Privacy/Security/Portability/Accessibility/Reuse/business/CI gates remain green.

## 17. Explicitly rejected alternatives

V1 rejects:

- hard-deleting the Membership at exit;
- keeping the leaving Account's Space-bound private rows indefinitely even though it can no longer authorize that Space;
- transferring private or shared ownership to the remaining partner as a cleanup shortcut;
- a post-exit export credential/grace token;
- preserving `ACTIVE` Membership merely so an export/job can finish;
- reusing an old Space for a new partner;
- implicit `add_member()` reactivation of ended Memberships through invitation acceptance;
- normal partner-to-partner removal;
- a second queue, breakup archive, storage backend or client-only authorization flag;
- entitlement-dependent exit or retention.

Any change to these frozen V1 decisions must update this document/owner before runtime silently diverges.