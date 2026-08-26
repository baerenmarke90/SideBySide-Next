"""API-Version 1.

Die Version steht im Pfad. Ein veröffentlichter Vertrag wird innerhalb
ihrer Version nicht brechend geändert; brechende Änderungen bekommen eine
neue Version, damit ältere App-Installationen weiterlaufen.
"""

from __future__ import annotations

from fastapi import APIRouter

from sidebyside.api.v1 import (
    attachments,
    auth,
    comments,
    health,
    heart_moments,
    invitations,
    memories,
    milestones,
    people,
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
