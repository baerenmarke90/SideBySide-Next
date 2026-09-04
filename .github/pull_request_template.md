<!--
Engineering language is English for repository work.
PR titles, descriptions, review comments, commit messages, technical discussion, and engineering artifacts must be written in English.
Follow docs/ENGINEERING-LANGUAGE.md.
User-facing product copy remains governed by i18n and may be localized.
-->

## Summary

<!-- What does this PR change and why? -->

## Scope

<!-- What is intentionally in scope, and what is not? -->

## Product Design / UX

Details: `docs/DESIGN-PRINCIPLES.md`, `docs/PARTNER-APP-EXPERIENCE-STANDARD.md`, `docs/UX-PATTERNS.md`, `docs/SCREEN-TEMPLATES.md`, and `docs/DESIGN-SYSTEM-DELIVERY.md`.

Exactly one of the following options must be checked:

- [ ] User-facing UI / UX impact reviewed
- [ ] No user-facing UI / UX impact

### If user-facing UI / UX is affected

All applicable items are mandatory before merge:

- [ ] Partner-app experience standard applied
- [ ] Screen Template selected or a documented design-system gap explains why no existing template fits
- [ ] Existing design-system components and semantic tokens reused or the gap is documented
- [ ] Primary human/content focal point and dominant action are clear
- [ ] Couple-facing UI does not default to spreadsheet/admin/CRUD composition
- [ ] Result feels warm, modern, lively, beautiful, and not visually cold or sterile
- [ ] Gentle playfulness / relationship personality deliberately applied or consciously not appropriate for this context
- [ ] Love-message / relationship microcopy opportunity deliberately considered
- [ ] Compact and Expanded behavior reviewed
- [ ] Loading / Empty / Error / Offline / Success states reviewed where applicable
- [ ] Motion / feedback behavior reviewed, including reduced motion
- [ ] Privacy and relationship-state presentation reviewed where applicable
- [ ] Visual evidence attached or linked

**Design result / rationale**

<!-- Name the selected template/pattern, focal point, key hierarchy decision, warmth/playfulness decision, relationship microcopy decision, motion behavior, and any intentional exception. -->

-

**Visual evidence**

<!-- Link or attach representative screenshots/recordings. Include Compact and Expanded where applicable; include Light/Dark when theme-sensitive styling changed. -->

-

### If no user-facing UI / UX impact

**Rationale**

<!-- Explain briefly why no product UI is affected. A bare "not relevant" is insufficient. -->

-

## Business / Freemium Model Consistency

Details: `docs/BUSINESS-MODEL.md` and `docs/FREEMIUM-FEATURE-MATRIX.md`. The review itself is mandatory for every development PR.

Exactly one of the following options must be checked:

- [ ] Business/freemium impact reviewed
- [ ] No business/freemium impact

**Result / rationale**

<!-- If there is impact, summarize the decision or link to the owning product decision. If there is no impact, explain briefly why. A bare "not relevant" is insufficient. -->

-

When relevant, explicitly assess:

- [ ] Free / Premium / Mixed / non-paywallable classification
- [ ] entitlement/capability and couple/relationship ownership semantics
- [ ] Self-Hosted vs. SideBySide Cloud/Managed behavior
- [ ] managed storage / compute / provider / rendering / inference / email-push / support cost
- [ ] quotas / fair-use / retention / resource limits
- [ ] downgrade / trial / grandfathering / restore / export / existing-data behavior
- [ ] authoritative business-model or feature-matrix documentation updated or confirmed unchanged

For capabilities already classified in `docs/FREEMIUM-FEATURE-MATRIX.md`, use that versioned matrix. Until remaining future/unimplemented decisions from #262 are promoted into authoritative repository documentation, use #262 as the working source for those pending product-tier decisions.

## Reuse-before-build

Exactly one of the following options must be checked. Details: `docs/REUSE-BEFORE-BUILD.md`.

- [ ] Reuse review relevant
- [ ] Reuse review not relevant

### If relevant

**Alternatives considered**

<!-- Name concrete standards, platform/framework capabilities, open-source components, and/or providers. A generic statement such as "nothing found" is insufficient. -->

-

**Decision and rationale**

<!-- Why was this solution selected? If custom-built: why is that appropriate/necessary despite available alternatives? -->

-

**Third-party components/providers**

<!-- If no third party is involved: "not applicable". Otherwise document at least license/ToS, Cloud/Self-Hosted support, privacy/data flow, cost/rate limits, fallback, and user/hoster effort, or link to an issue/document that does. -->

-

### If not relevant

**Rationale**

<!-- For example: pure domain logic without new commodity infrastructure, provider, platform integration, or substantial dependency. -->

-

## Cross-Cutting Quality

Details: `docs/CROSS-CUTTING-QUALITY.md`.

For larger runtime slices, client features, and production user flows, document relevant cross-cutting consequences. Non-relevant areas may be summarized if the decision is traceable.

- [ ] Security / Auth / Abuse / secure defaults reviewed or not relevant
- [ ] Privacy / data lifecycle / logs / caches / events reviewed or not relevant
- [ ] i18n / locale / dates / numbers / pluralization / RTL reviewed or not relevant
- [ ] Accessibility / semantics / focus / scaling reviewed or not relevant
- [ ] Concurrency / consistency / races reviewed or not relevant
- [ ] Resilience / offline / retry behavior reviewed or not relevant
- [ ] Observability without sensitive content reviewed or not relevant
- [ ] Performance / query and resource impact reviewed or not relevant
- [ ] API / DTO / migration / compatibility impact reviewed or not relevant
- [ ] Self-Hosted / configuration / upgrade / backup / release impact reviewed or not relevant
- [ ] Appropriate test levels and negative cases reviewed

**Result / rationale**

<!-- Summarize the relevant areas and concrete decisions. Link to deeper issue/ADR documentation when applicable. -->

-

## Validation

<!-- Tests, lint, typecheck, manual checks, etc. -->

- [ ] relevant tests executed
- [ ] CI must be green before merge
- [ ] Product Design / UX result is complete and traceable
- [ ] business/freemium model consistency result is complete and traceable
- [ ] no Clean-Room, security, privacy, tenant-isolation, provenance, licensing, or engineering-language rule weakened
- [ ] no recognizable cross-cutting consequence deferred without justification
- [ ] PR title/body, review discussion, commit messages, and technical engineering prose are in English

## Notes / risks

<!-- Optional -->
