"""API version 1.

The version is part of the path. A published contract is not changed in a
breaking way within its version; breaking changes receive a new version so
older app installations can continue to operate.
"""

from __future__ import annotations

from fastapi import APIRouter

from sidebyside.api.v1 import (
    attachments,
    auth,
    chapter_relations,
    chapters,
    collections,
    comments,
    health,
    heart_moments,
    invitations,
    memories,
    milestones,
    people,
    place_relations,
    places,
    plans,
    profiles,
    spaces,
    story,
    wishes,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(health.router)
router.include_router(invitations.router)
router.include_router(attachments.router)
router.include_router(story.router)
router.include_router(memories.router)
router.include_router(milestones.router)
router.include_router(heart_moments.router)
router.include_router(comments.router)
router.include_router(people.router)
router.include_router(profiles.router)
router.include_router(spaces.router)
router.include_router(wishes.router)
router.include_router(places.router)
router.include_router(place_relations.router)
router.include_router(plans.router)
router.include_router(chapters.router)
router.include_router(chapter_relations.router)
router.include_router(collections.router)
