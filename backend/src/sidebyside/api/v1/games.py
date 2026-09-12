"""Premium-protected read seams for relationship-native games."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter

from sidebyside.api.deps import Authorization, DbSession, ensure_capability
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.entitlements.models import Capability
from sidebyside.games import service

router = APIRouter(tags=["games"])


class GameMemoryCandidate(ApiModel):
    """Minimal authorized Memory context required by `Unsere Momente`."""

    memory_id: UUID
    title: str
    effective_date: date
    image_attachment_id: UUID


class GameMemoryCandidateSet(ApiModel):
    """Bounded candidate pool without hidden/private-derived totals."""

    items: list[GameMemoryCandidate]


@router.get(
    "/spaces/{spaceId}/games/moments/candidates",
    response_model=GameMemoryCandidateSet,
    operation_id="getGameMomentCandidates",
    responses=problem_responses(401, 403, 404),
)
def get_game_moment_candidates(
    authorization: Authorization,
    session: DbSession,
) -> GameMemoryCandidateSet:
    """Return Premium-authorized shared photo Memories for the first #863 grammar.

    Normal authentication and Space membership are resolved before this route
    receives `authorization`. Commercial entitlement is then enforced on the
    server. The actual content query remains constrained by the existing
    `readable()` authorization predicate and existing attachment bindings.
    """
    ensure_capability(
        session,
        authorization.space_id,
        Capability.GAMES_COUPLE.value,
        lock_grants=False,
    )
    return GameMemoryCandidateSet(
        items=[
            GameMemoryCandidate(
                memory_id=candidate.memory_id,
                title=candidate.title,
                effective_date=candidate.effective_date,
                image_attachment_id=candidate.image_attachment_id,
            )
            for candidate in service.read_memory_candidates(session, authorization)
        ]
    )
