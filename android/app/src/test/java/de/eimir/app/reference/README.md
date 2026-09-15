# M2-S8 Android Tests

This test source set intentionally covers the G2 reference slice only:

- generated `StoryItem` discriminator deserialization,
- Memory/Image/Story flow orchestration,
- STREAM vs. signed media authorization headers,
- Compose semantics and large system font scale,
- operator-only configuration boundaries.

It does not establish a persistent cache, offline write behavior, full navigation, or M5 client parity.
