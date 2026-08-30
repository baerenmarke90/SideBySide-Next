# Web client

The React web client is an authoritative M5 client surface. It uses the generated OpenAPI client, React Router, TanStack Query, i18next, and browser platform capabilities. It does not duplicate backend authorization, privacy, or validation rules.

## M5 Web S2 story products

M5 Web S2 completes the product surfaces for Memories, HeartMoments, and Milestones:

- Memory create, detail, edit, delete, media gallery, comments, and deep links.
- HeartMoment create, detail, edit, delete, visibility changes, optional image attachment, comments for shared HeartMoments, and deep links.
- Milestone create, detail, edit, delete, comments, and deep links.
- Story cards link directly to the corresponding detail route.
- Image galleries provide a fullscreen viewer, keyboard navigation, touch swipe navigation, and an item counter. The renderer is video-capable for server-supported READY video attachments, but the current backend intentionally remains fail-closed for video upload until the dedicated video scope is implemented.
- Memory and HeartMoment attachment drafts upload immediately after selection, show a local preview and upload progress, and can be cancelled before binding the attachment to domain content.

Routes:

- `/memory/new`
- `/memory/:memoryId`
- `/memory/:memoryId/edit`
- `/heart-moment/new`
- `/heart-moment/:heartMomentId`
- `/heart-moment/:heartMomentId/edit`
- `/milestone/new`
- `/milestone/:milestoneId`
- `/milestone/:milestoneId/edit`

## Read cache and privacy

Product detail reads use IndexedDB as a last-known-good read cache. The cache is scoped by account, space, domain kind, and resource id. A successful authorized network read refreshes the cache.

Cache fallback is deliberately limited to transport/offline failures and temporary server failures. Authentication, permission, and not-found responses never fall back to cached protected content. This preserves fail-closed authorization semantics, including privacy-sensitive resources that deliberately use `404` instead of `403` to avoid existence disclosure.

Cached detail views are read-only. The client does not queue or synchronize offline writes. Comments are not loaded from the product cache. The cache is cleared on logout.

## Concurrency and mutations

All updates, deletes, visibility changes, comment deletes, and attachment binding operations continue to use the version returned by the API through `If-Match`. Client-side optimistic presentation is rolled back when the mutation fails; the server remains authoritative.

HeartMoment visibility is not part of the content update payload. The UI uses the dedicated visibility operation and only the API-defined `SHARED` and `PRIVATE` values. Private HeartMoments do not request or render shared comments.

## Reuse review

M5 Web S2 reuses existing capabilities instead of introducing parallel infrastructure:

- generated OpenAPI clients for all domain and comment operations;
- the existing attachment upload/finalize/READY lifecycle;
- IndexedDB for durable local reads;
- `AbortController` plus `XMLHttpRequest.upload` for cancellable upload progress;
- native image/video elements, keyboard events, and touch events for the gallery;
- React Router for deep links and TanStack Query for remote state and optimistic rollback.

No new runtime dependency or provider service is introduced.

## Business and freemium classification

This slice does not change product classification. Memory CRUD, normal image attachments, HeartMoments, Milestones, comments, Story, and web access remain Free/Core. Privacy and accessibility behavior are non-paywallable. Cloud and self-hosted deployments use the same client behavior and API contract.

## Accessibility

Interactive gallery thumbnails are buttons with accessible names. The fullscreen viewer is an `aria-modal` dialog, exposes a live counter, supports Escape and arrow keys, and keeps 44+ pixel navigation controls. Forms use explicit labels, status/error regions use existing shared UI-state components, and upload progress uses the native `progress` element. The S2 regression suite includes semantic route/render smoke coverage and the `SBS-M5-Web-S2-SCOPE` acceptance marker.
