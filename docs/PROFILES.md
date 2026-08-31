# Partner Profiles and Preferences

## Scope

The M1 Profiles Domain strictly separates two technically different kinds of information:

- `SELF_PROFILE`: An Account describes itself to the active partner in the same Space. These rows are `SPACE_SHARED`.
- `PRIVATE_PARTNER_NOTE`: An Account privately remembers something about the other active partner. These rows are `OWNER_ONLY`.

There is no `PUBLIC` visibility and the request cannot freely set `privacyClass`. The API derives the Privacy class server-side from the Domain `visibility`.

### Account presentation identity

`Account.display_name` is the authoritative current presentation name for an authenticated person. It is not an authentication identifier and changing it does not change the Account ID, email address, OIDC issuer/subject, Passkey credentials, password identity, or active sessions.

Display names are normalized in the identity service: surrounding whitespace is removed, at least one visible non-control character is required, Unicode content is preserved, and names longer than 120 characters are rejected rather than silently truncated. Local registration and later profile edits use the same rule. An unusable external OIDC display-name claim falls back to the neutral `Partner` name instead of making an otherwise verified identity unusable.

Person/author projections use the **current Account presentation identity** unless a domain explicitly documents a historical snapshot field. A stored historical event remains historical content, but an ordinary author label/avatar is not a second authoritative copy of the old display name.

## Persistence

`partner_profiles` is the visible profile aggregate root of an Account in a Space. At most one row exists per `(space_id, owner_id)` and the database enforces `SPACE_SHARED`.

`profile_preferences` stores structured preferences. Metadata such as category, topic, sentiment, ownership, and visibility remain separate from the protected `value`. The value is stored in a `ProtectedPayloadJSON` column with `crypto_version = 0`; this is plaintext and **not E2EE**. The separation keeps the later migration to client-side sealed payloads possible.

The database additionally enforces:

- `SELF_PROFILE` => `account_id == owner_id`, `SPACE_SHARED`, visible `partner_profile` exists.
- `PRIVATE_PARTNER_NOTE` => `account_id != owner_id`, `OWNER_ONLY`, no connection to visible `partner_profile`.

Therefore a private partner note cannot become part of the visible partner profile through faulty serialization.

### Avatar media binding

Profile avatars reuse the existing Attachment/MediaStore lifecycle. `account_profile_attachments` is a one-to-one attachment-parent relation: one Account has at most one current avatar and one Attachment can belong to at most one Account profile. It is a media binding only, not a second Account/Profile aggregate.

The relation stores only stable IDs. No temporary or signed provider URL becomes profile state. Upload validation, sanitization, thumbnail generation, storage keys, retention and physical cleanup remain owned by the existing attachment pipeline.

The central attachment binding resolver reports profile media as `ACCOUNT_PROFILE`. This means avatar attachments participate in the same cross-parent exclusivity rule as Memory and HeartMoment media and are no longer considered unbound once attached to a profile. Normal replacement/removal detaches the old relation before that attachment enters the existing deletion lifecycle. Because every Attachment is Space-scoped, deleting its Space cascades the Attachment and avatar binding together; the profile then deterministically falls back to its no-image representation instead of blocking Space deletion.

The visible profile contract exposes only the stable nullable `profileAttachmentId`. The authenticated owner can set another READY image Attachment that they own in the currently authorized Space, or send an explicit `null` to remove the current avatar. Replacement/removal uses the existing `DELETING` and media-cleanup lifecycle; the Profile domain never deletes provider objects synchronously and never creates avatar-specific storage keys.

Avatar bytes are served only through the authorized profile-avatar route. The caller first proves that the Account has a readable profile in the caller's current Space. The server then resolves exactly that Account's current avatar binding; the caller cannot supply an arbitrary Attachment ID. The route prefers the existing thumbnail when available, otherwise serves the sanitized original, and returns `private, no-store` cache semantics. It never turns the avatar into a public unauthenticated URL or profile-stored signed URL.

Avatar presentation identity is Account-global while the backing Attachment remains Space-scoped. If the same Account is an active member of another Space, that Space may render the same current avatar after its own profile/membership authorization succeeds. This exception applies only to the exact current Account-profile binding and does not make any other Attachment from the source Space readable.

## Authorization

Every endpoint begins with the existing Tenant Context. Lists and detail access then use the central Owner/Privacy Guard. The filter condition is part of the SQL query; invisible rows are not loaded first and discarded afterward.

For `SPACE_SHARED`:

- both active partners may read,
- only the owner may write or delete.

For `OWNER_ONLY`:

- only the owner may read, write or delete,
- for the affected partner and Cross-Tenant caller the resource is indistinguishable from a missing resource (`404`).

The visible endpoint:

`GET /api/v1/spaces/{spaceId}/profiles/{accountId}`

always filters to `SELF_PROFILE`. The owner's own private notes about this person therefore cannot accidentally appear in this profile view.

`PATCH /api/v1/spaces/{spaceId}/profiles/{accountId}` is self-write only. Omitted identity fields remain unchanged. `displayName` is normalized and validated only by the authoritative identity-domain rule; changing it does not change authentication identity or sessions. An explicit `profileAttachmentId: null` removes the avatar, while a non-null ID must pass the existing READY/owner/current-Space/image validation.

`GET /api/v1/spaces/{spaceId}/profiles/{accountId}/avatar/content` requires an authenticated caller with readable current-Space profile access and returns `404` for a missing/invisible/non-ready current avatar. It does not accept an Attachment ID and therefore cannot be used as a cross-tenant media guessing oracle.

## API

- `GET /api/v1/spaces/{spaceId}/profiles/{accountId}`
- `PATCH /api/v1/spaces/{spaceId}/profiles/{accountId}`
- `GET /api/v1/spaces/{spaceId}/profiles/{accountId}/avatar/content`
- `GET /api/v1/spaces/{spaceId}/profile-preferences`
- `POST /api/v1/spaces/{spaceId}/profile-preferences`
- `GET /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}`
- `PUT /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}`
- `DELETE /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}`

ProfilePreference changes and deletes use ETag/`If-Match`. Stale versions return `409 VERSION_CONFLICT` instead of a silent Lost Update.

## Stable enums

Categories:

`FOOD`, `DRINK`, `FLOWERS`, `MOVIES`, `SERIES`, `MUSIC`, `HOBBIES`, `ACTIVITIES`, `TRAVEL`, `RESTAURANTS`, `COLORS`, `OTHER`.

Sentiments:

`LOVE`, `LIKE`, `NEUTRAL`, `DISLIKE`, `AVOID`.

Visibility:

`SELF_PROFILE`, `PRIVATE_PARTNER_NOTE`.

Unknown values are rejected by the API and additionally excluded through database constraints.
