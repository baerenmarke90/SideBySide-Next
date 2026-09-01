"""API version 1.

The version is part of the path. A published contract is not changed in a
breaking way within its version; breaking changes receive a new version so
older app installations can continue to operate.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from sidebyside.api.deps import require_normal_operation
from sidebyside.api.v1 import (
    attachments,
    auth,
    chapter_relations,
    chapters,
    collections,
    comments,
    dashboard,
    demo,
    engagement,
    health,
    heart_moments,
    instance,
    invitations,
    memories,
    milestones,
    people,
    place_relations,
    places,
    plans,
    private_area,
    private_collections,
    profiles,
    reminders,
    rules,
    search,
    server_admin,
    session_context,
    spaces,
    story,
    transfer,
    wishes,
)

router = APIRouter()

# Health, public access state, authentication/recovery and ServerAdmin remain
# reachable while maintenance is active. Every normal product route below is
# protected by one server-side dependency instead of client-side assumptions.
router.include_router(auth.router)
router.include_router(health.router)
router.include_router(instance.router)
router.include_router(server_admin.router)

normal_router = APIRouter(dependencies=[Depends(require_normal_operation)])
normal_router.include_router(session_context.router)
normal_router.include_router(demo.router)
normal_router.include_router(invitations.router)
normal_router.include_router(attachments.router)
normal_router.include_router(story.router)
normal_router.include_router(search.router)
normal_router.include_router(dashboard.router)
normal_router.include_router(engagement.router)
normal_router.include_router(memories.router)
normal_router.include_router(milestones.router)
normal_router.include_router(heart_moments.router)
normal_router.include_router(comments.router)
normal_router.include_router(people.router)
normal_router.include_router(profiles.router)
normal_router.include_router(spaces.router)
normal_router.include_router(wishes.router)
normal_router.include_router(places.router)
normal_router.include_router(place_relations.router)
normal_router.include_router(plans.router)
normal_router.include_router(chapters.router)
normal_router.include_router(chapter_relations.router)
normal_router.include_router(collections.router)
normal_router.include_router(private_area.router)
normal_router.include_router(private_collections.router)
normal_router.include_router(reminders.router)
normal_router.include_router(rules.router)
normal_router.include_router(transfer.router)
router.include_router(normal_router)
