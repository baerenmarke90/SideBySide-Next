# SideBySide Next - Freemium Feature Matrix

**Status:** authoritative product-tier and roadmap baseline  
**Version:** 1.1  
**Audit date:** 2026-09-01  
**Audited `main` baseline:** `1b5a46f`  
**Strategic decision:** #262 (Finalized)  
**Entitlement architecture:** [ADR 0006](m6/ADR-0006-ENTITLEMENT-ARCHITECTURE.md)

## Purpose and authority

This document records the authoritative repository-wide business/freemium classification for all current (M0–M3) and planned (M4–M8) capabilities of SideBySide Next following the resolution of issue #262.

It defines the commercial boundaries, entitlement ownership semantics, downgrade guarantees, and licensing rules across both the **SideBySide Self-Hosted** and **SideBySide Cloud** operating models.

When sources appear to conflict:

1. Security, Privacy, Tenant Isolation, data rights, and Clean-Room requirements cannot be weakened by monetization.
2. `specification/CLEAN-ROOM-MASTER-SPEC.md` and `specification/PRODUCT-SPEC.md` remain binding for product and technical requirements.
3. `docs/BUSINESS-MODEL.md` defines the operating and commercial model.
4. This matrix defines the authoritative product-tier classification.
5. `docs/m6/ADR-0006-ENTITLEMENT-ARCHITECTURE.md` defines the technical entitlement and licensing architecture.

Any future change to an existing classification requires an explicit, versioned matrix revision before runtime gating changes are implemented.

---

## Executive summary & commercial pillars

SideBySide Next adheres strictly to a genuine **freemium model**:

> **Free lets a couple meaningfully use SideBySide as their complete relationship home. Premium enriches that foundation through advanced presentation, automation, longitudinal insights, third-party integrations, and managed cloud resources — without ever holding existing shared history hostage.**

### Core principles

1. **Couple/Space-level entitlement ownership:** SideBySide is a shared couple product. A commercial purchase by either partner applies to the entire shared Space. Both partners immediately benefit from Premium capabilities within that Space.
2. **Strict non-destructive downgrade:** Downgrading or license expiry **never deletes or hides user data**. All existing memories, chapters, photos, and answers remain 100% readable and exportable. Only the creation of new Premium-tier items or regeneration of heavy artifacts is paused.
3. **Self-Hosted independence:** The Self-Hosted build is a complete, first-class product under the [PolyForm Noncommercial License 1.0.0](../LICENSE). It functions fully offline without any forced phone-home connection. Optional commercial Self-Hosted licenses use cryptographically signed offline tokens.
4. **No micro-limits on core data:** There are no artificial paywalls on the number of memories, wishes, plans, places, notes, or list items. Cloud storage limits apply transparently to durable media byte volume, not domain entity counts.
5. **Privacy and trust are non-paywallable:** Security, authentication, passkeys, owner-only private entries (`PrivateNote`, `GiftIdea`), account deletion (#520), space offboarding (#518), and accessibility features can never be gated behind Premium.

---

## Classification vocabulary

### Free/Core
A core capability available to all users without payment. Standard use of the capability is unlimited by entity count.

### Premium
An advanced capability accessible only under an active Premium entitlement (e.g. printable book generation, annual video recaps, deep analytical mirrors, external tool integrations).

### Mixed
A capability with a functional Free baseline and clearly demarcated Premium extensions. The boundary between the Free baseline and Premium extension is explicitly defined in this matrix.

### Non-paywallable
Capabilities essential for Security, Privacy, Accessibility, Tenant Isolation, account protection, deletion, or fundamental data portability. These must never be paywalled.

---

## Authoritative feature & capability matrix (M0–M8)

| Capability / Surface | Milestone | Classification | Gating boundary | Operating model impact | Strategic rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Account identity & registration** | M1 | **Free/Core** | Whole feature Free | Identical across Cloud and Self-Hosted | Every user must be able to create an account and access the product. |
| **Authentication security, Passkeys & Session protection** | M1 | **Non-paywallable** | Non-paywallable | Identical | Account protection and authentication security are fundamental trust requirements. |
| **Self-Hosted authentication mechanisms (Password, OIDC)** | M1 | **Free/Core** | Whole feature Free | Self-Hosted specific | Authentication standards are infrastructure mechanisms, not commercial content integrations. |
| **Space creation, Membership & Partner invitations** | M1 | **Free/Core** | Whole feature Free | Identical | The couple Space is the core product entry point. |
| **Tenant isolation & Authorization boundary** | M1 | **Non-paywallable** | Non-paywallable | Identical | Isolation between tenants is a non-negotiable security invariant. |
| **SpaceProfile & Relationship context** | M1 | **Free/Core** | Whole feature Free | Identical | Basic couple anniversary and relationship context are core baseline. |
| **PartnerProfile & ProfilePreferences** | M1 | **Free/Core** | Whole feature Free | Identical | Managing personal and shared preferences is part of the basic product. |
| **RelatedPerson & ImportantDate management** | M1, M5 | **Mixed** | **Free:** Basic CRUD & standard date tracking.<br>**Premium:** Multi-condition occasion automation & recurring reminders. | Identical | Storing friends/family is basic utility; automated complex workflows are Premium. |
| **Memory CRUD & Timeline history** | M2, M5 | **Free/Core** | Whole feature Free (no count limit) | Identical | Memories are the emotional heart of SideBySide. |
| **Image attachment upload & storage** | M2, M5 | **Free/Core** | Functional feature Free | **Self-Hosted:** Unmetered (operator storage).<br>**Cloud:** Subject to Space storage quota. | Image uploading is core to memories; Cloud storage has operational byte costs. |
| **Cloud storage quota** | M2, M6 | **Mixed** | **Free:** 5 GB per Space.<br>**Premium:** 50 GB per Space (expandable via add-ons). | Cloud only (Self-Hosted is unmetered) | Protects Cloud infrastructure from runaway hosting and bandwidth costs. |
| **Media privacy & attachment validation** | M2 | **Non-paywallable** | Non-paywallable | Identical | Security checks and media validation must execute identically for all users. |
| **HeartMoments & Shared emotional reactions** | M2, M5 | **Free/Core** | Whole feature Free | Identical | Everyday emotional connection must remain frictionless. |
| **HeartMoment `PRIVATE` / `OWNER_ONLY` enforcement** | M2 | **Non-paywallable** | Non-paywallable | Identical | Partner privacy can never depend on commercial tier. |
| **Milestone tracking** | M2, M5 | **Free/Core** | Whole feature Free | Identical | Shared couple milestones belong to the core baseline history. |
| **Comments on shared entries** | M2, M5 | **Free/Core** | Whole feature Free | Identical | In-app communication around shared memories is basic functionality. |
| **Wish & Plan lifecycle** | M3, M5 | **Free/Core** | Whole feature Free | Identical | Shared bucket list and couple planning are everyday core tools. |
| **Place CRUD & Coordinates** | M3, M5 | **Mixed** | **Free:** Place CRUD, pin locations, content links.<br>**Premium:** Interactive journey routes, clustering, heatmaps. | Identical | Storing places is basic utility; advanced geospatial analytics are Premium. |
| **Chapters & Story grouping** | M3, M5 | **Mixed** | **Free:** Chapter CRUD, grouping, typed relations.<br>**Premium:** Bespoke magazine layouts, custom covers, narrative export. | Identical | Grouping content is organizational; high-end curation & design are Premium. |
| **Shared Collections & Checklists** | M3, M5 | **Free/Core** | Whole feature Free | Identical | Packing lists and shared couple checklists are core utility. |
| **Private Area (Notes & Gift Ideas)** | M3, M5 | **Free/Core** | Whole feature Free | Identical | A safe private individual space is necessary for authentic relationship use. |
| **Private Area owner-only isolation** | M3 | **Non-paywallable** | Non-paywallable | Identical | Strict cryptographic/authorization boundary for individual entries. |
| **Search & Multi-criteria filtering** | M4 | **Free/Core** | Whole feature Free | Identical | Users must always be able to search and locate their own history. |
| **Zero-Decision Dashboard & Activity** | M4, M7 | **Free/Core** | Whole feature Free | Identical | The primary daily landing experience is part of the core product. |
| **Lightweight engagement ("Thinking of you")** | M4 | **Free/Core** | Whole feature Free | Identical | Spontaneous emotional pings belong to everyday core interactions. |
| **Notification Policy, Digest & Quiet Hours** | M4, M5 | **Free/Core** | Whole feature Free | Identical | Respecting partner attention and preventing notification fatigue is core quality. |
| **Automation Rules & Custom Triggers** | M4, M7 | **Mixed** | **Free:** Standard date alerts & digests.<br>**Premium:** Multi-step rules, custom triggers, automated recaps. | Identical | Advanced automation consumes background compute resources. |
| **Official Web & Android client access** | M5 | **Free/Core** | Whole client access Free | Identical | Accessing the application via official native clients is never paywalled. |
| **Standard Light/Dark/System appearance** | M5 | **Free/Core** | Whole feature Free | Identical | Standard platform accessibility and dark mode are basic expectations. |
| **Bespoke Themes, Covers & UI Personalization** | M5, M7 | **Premium** | Premium only | Identical | Artistic color palettes, custom card styles, and bespoke widgets. |
| **Accessibility essentials & i18n localization** | M1–M5 | **Non-paywallable** | Non-paywallable | Identical | Inclusive accessibility and locale support are baseline engineering standards. |
| **Short Audio / Voice Notes** | M7 | **Free/Core** | Whole feature Free (storage applies in Cloud) | Identical | Voice snippets add emotional intimacy to memories (#512). |
| **Daily Questions & Shared Answers** | M7 | **Mixed** | **Free:** Daily questions & basic answer history.<br>**Premium:** 5-Year Reflection Mirror (#516), deep category packs, cross-year comparison. | Identical | Daily bonding is free; long-term analytical mirroring is Premium. |
| **Printable PDF Chronicle / Yearbook** | M7 | **Premium** | Premium only (#517) | Identical | Computationally intensive high-resolution book rendering artifact. |
| **Annual Video Montage & Relive** | M7 | **Premium** | Premium only | Identical | Heavy video transcoding and licensed music catalog delivery. |
| **Surprise Mode (Timed-reveal Vault)** | M7 | **Premium** | Premium only (#514) | Identical | Specialized emotional reveal vault for anniversaries and gifts. |
| **Server Admin & System Health Dashboard** | M6 | **Free/Core** | Whole feature Free | Self-Hosted / Operator focused | System operators must be able to administer instances without paywalls. |
| **Backup, Restore & Instance Migration** | M6 | **Free/Core** | Whole feature Free | Self-Hosted focused | Data ownership and recovery are foundational for Self-Hosted users. |
| **Account Deletion & Space Offboarding** | M6 | **Non-paywallable** | Non-paywallable (#518, #520) | Identical | GDPR compliance and data sovereignty can never be gated. |
| **Observability, Structured Logging & Redaction** | M6 | **Non-paywallable** | Non-paywallable (#189) | Identical | Operational diagnostics and privacy scrubbing are core infrastructure. |
| **External Integrations (Immich, Dawarich, CalSync)** | M8 | **Premium** | Premium only | Identical | Maintained third-party platform integrations and sync pipelines. |

---

## Entitlement ownership & couple semantics

SideBySide is explicitly modeled around the couple unit. Commercial entitlements reflect this reality:

```text
[ Purchaser Account (Anna) ] ----( purchases )----> [ Space Entitlement Grant ]
                                                            |
                       +------------------------------------+------------------------------------+
                       |                                                                         |
                       v                                                                         v
             [ Member A (Anna) ]                                                       [ Member B (Ben) ]
             Full Premium in Space                                                     Full Premium in Space
```

1. **Space-Level Entitlement Scope:** The entitlement is bound to the `SpaceId`. Any active member authorized in that Space inherits the active Premium capabilities.
2. **Purchaser Sponsorship:** The purchasing account (`AccountId`) is recorded as the billing owner/sponsor for invoice, renewal, and store restore purposes.
3. **No Cross-Space Leakage:** If a user is a member of multiple spaces (e.g. testing or migration), Premium does not leak to unrelated spaces.
4. **Relationship Dissolution / Offboarding (#518):** If a partner leaves a Space or the Space is deleted, the Space entitlement expires with the Space. The purchasing partner may re-bind their active subscription to a new Space via "Restore Purchase", but the abandoned Space immediately drops back to Free.
5. **No Privacy Override:** An entitlement grant never gives a partner access to `OWNER_ONLY` items (`PrivateNote`, `GiftIdea`, private HeartMoments) created by the other partner.

---

## Subscription & license lifecycle state machine

Commercial entitlement states follow a strict, deterministic state machine:

```text
       +---------------------------------------------+
       |                                             |
       v                                             |
  [ ACTIVE ] <-----( payment / grant / key )---------+
       |                                             |
       +--( payment failure / renewal pending )-----> [ GRACE_PERIOD (14 days) ]
       |                                                    |
       +--( period end / expired / offline timeout )-------> [ EXPIRED ]
       |                                                    |
       +--( refund / chargeback / revoked key )------------> [ REVOKED ]
```

### Lifecycle states

* **`ACTIVE`:** Paid subscription, valid offline license key, or active trial. Full capability set is available.
* **`TRIAL`:** Time-limited introductory period (e.g. 14 days) providing full Premium capabilities. Reverts to Free upon expiry if not converted to a paid plan.
* **`GRACE_PERIOD`:** 14-day transitional window following a payment failure or renewal delay. All Premium capabilities remain fully active to avoid abrupt couple disruption, accompanied by an informative, non-intrusive renewal banner.
* **`EXPIRED`:** Subscription term ended without renewal, or grace period elapsed. Space seamlessly transitions to Free/Core without data loss.
* **`REVOKED`:** Immediate termination due to refund, payment chargeback, or explicit license invalidation. Immediately reverts to Free/Core.
* **`GRANDFATHERED`:** Promotional, lifetime, or legacy administrator grants that do not require recurring billing.

---

## Non-destructive downgrade & data retention contract

The most critical commercial guarantee of SideBySide Next is **Zero Data Loss on Downgrade**:

1. **Read & Export Invariant:** All content created during a Premium subscription remains **100% accessible, viewable, and exportable** forever.
   * Chapters with bespoke layouts remain viewable in their rich presentation.
   * High-resolution photo galleries and audio notes remain playable and downloadable.
   * Past yearly recaps and generated PDF books remain readable and downloadable.
   * 5-Year Reflection histories and past question answers remain readable.
2. **Create / Edit / Regenerate Boundary:**
   * *Create:* New items requiring Premium capabilities cannot be created while expired.
   * *Edit:* Basic text/date fields of existing items can still be updated; re-rendering complex Premium artifacts (e.g. re-generating high-res yearbook PDFs) requires active Premium.
   * *Uploads:* If Cloud storage exceeds the 5 GB Free quota upon downgrade, existing media is **never deleted**, but new uploads are paused until storage is reduced or Premium is restored.

---

## Self-Hosted licensing & offline resilience

1. **PolyForm Noncommercial 1.0.0 Baseline:** Self-Hosted instances are 100% free for personal/noncommercial use with full access to all Free/Core capabilities.
2. **Zero Phone-Home Requirement for Core:** A healthy Self-Hosted instance never connects to external license servers for normal operation. It remains fully functional in air-gapped, local-only, or offline environments.
3. **Offline Signed License Keys for Commercial / Premium:**
   * Self-Hosted Premium features use asymmetric cryptographic license keys (Ed25519 signatures).
   * The license payload contains `instance_id`, `holder`, `capabilities`, and `valid_until`.
   * The server validates the signature locally using an embedded public key without requiring any outbound network connection.
   * Clock-tampering protection uses monotonically tracked database event timestamps.

---

## Multi-channel purchase reconciliation & restore

The application abstracts all billing providers behind a unified, provider-neutral capability model:

```text
[ Google Play Billing ] ----\
[ Cloud Web / Stripe ]  -----\
[ Offline License Key ] ------+---> [ Normalized Entitlement Adapter ] ---> [ Capability Core ]
[ Admin / Grandfather ] -----/
```

* **One-Tap Restore:** Both Web and Android clients provide a transparent "Restore Purchases" action in Settings.
* **Idempotent Reconciliation:** Replaying purchase receipts or re-entering license keys is fully idempotent and updates the Space entitlement record without duplicate billing or state corruption.
* **Store Independence:** Store-specific identifiers (SKUs, product IDs, receipt tokens) remain strictly isolated inside provider adapters and never leak into Domain models or general database schemas.

---

## Paywall UX principles

Monetization presentation in official clients must respect the emotional nature of the product:

* **No Modal Spam:** Locked features are marked with a subtle, elegant badge (e.g. `✨ Premium`). Tapping a locked feature opens an informative preview sheet explaining the added value.
* **No Fake Urgency:** No countdown timers, artificial scarcity, or manipulative dark patterns.
* **Transparent Pricing:** Prices and terms are presented clearly up front before entering store purchase flows.
* **Reassurance of Data Safety:** Any downgrade or paywall screen explicitly reassures users that their existing memories and shared data are safe and will never be deleted.
