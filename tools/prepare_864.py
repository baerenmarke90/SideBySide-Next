from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1))


def append_once(path: str, marker: str, addition: str) -> None:
    target = ROOT / path
    text = target.read_text()
    if marker in text:
        return
    target.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n")


# Backend bounded candidate seam.
replace_once(
    "backend/src/sidebyside/games/service.py",
    "from sidebyside.memories.models import Memory\n",
    "from sidebyside.memories.models import Memory\n"
    "from sidebyside.wishes.models import Wish, WishStatus\n",
)
replace_once(
    "backend/src/sidebyside/games/service.py",
    "\n\n@dataclass(frozen=True)\nclass MemoryCandidate:",
    "\n\nMAX_WISH_CANDIDATES = 32\n"
    "\"\"\"Maximum useful Wish candidate pool returned to one sofa-mode client.\"\"\"\n\n\n"
    "@dataclass(frozen=True)\nclass MemoryCandidate:",
)
append_once(
    "backend/src/sidebyside/games/service.py",
    "class WishCandidate:",
    '''
@dataclass(frozen=True)
class WishCandidate:
    wish_id: UUID
    created_by: UUID
    title: str


def read_wish_candidates(
    session: Session,
    context: AuthorizationContext,
    *,
    limit: int = MAX_WISH_CANDIDATES,
) -> list[WishCandidate]:
    """Return bounded OPEN Wishes eligible for #864 Wunschdetektiv.

    Normal Wish authorization remains authoritative through ``readable()``.
    ``owner_id`` is the existing stable ``createdBy`` attribution used to bind
    each round to its giver. GiftIdea is a separate OWNER_ONLY domain and is
    structurally outside this query.
    """
    if limit <= 0:
        return []

    statement = (
        readable(Wish, context)
        .where(Wish.status == WishStatus.OPEN.value)
        .order_by(Wish.created_at.desc(), Wish.id.desc())
    )
    candidates: list[WishCandidate] = []
    for wish in session.execute(statement).scalars().yield_per(100):
        title = wish.payload.title.strip()
        if not title:
            continue
        candidates.append(
            WishCandidate(
                wish_id=wish.id,
                created_by=wish.owner_id,
                title=title,
            )
        )
        if len(candidates) >= limit:
            break
    return candidates
''',
)

append_once(
    "backend/src/sidebyside/api/v1/games.py",
    "class GameWishCandidate(ApiModel):",
    '''
class GameWishCandidate(ApiModel):
    """Minimal authorized OPEN Wish context required by Wunschdetektiv."""

    wish_id: UUID
    created_by: UUID
    title: str


class GameWishCandidateSet(ApiModel):
    """Bounded Wish pool without private-derived totals."""

    items: list[GameWishCandidate]


@router.get(
    "/spaces/{spaceId}/games/wishes/candidates",
    response_model=GameWishCandidateSet,
    operation_id="getGameWishCandidates",
    responses=problem_responses(401, 403, 404),
)
def get_game_wish_candidates(
    authorization: Authorization,
    session: DbSession,
) -> GameWishCandidateSet:
    """Return Premium-authorized OPEN shared Wishes for #864."""
    ensure_capability(
        session,
        authorization.space_id,
        Capability.GAMES_COUPLE.value,
        lock_grants=False,
    )
    return GameWishCandidateSet(
        items=[
            GameWishCandidate(
                wish_id=candidate.wish_id,
                created_by=candidate.created_by,
                title=candidate.title,
            )
            for candidate in service.read_wish_candidates(session, authorization)
        ]
    )
''',
)

replace_once(
    "backend/tests/integration/test_endpoint_matrix.py",
    '    Endpoint("GET", "/api/v1/spaces/{spaceId}/games/moments/candidates"),\n',
    '    Endpoint("GET", "/api/v1/spaces/{spaceId}/games/moments/candidates"),\n'
    '    Endpoint("GET", "/api/v1/spaces/{spaceId}/games/wishes/candidates"),\n',
)

# Stable Web route and routing regression.
replace_once(
    "web/src/client/routes.ts",
    "export const GAMES_MOMENTS_ROUTE = '/games/our-moments';\n",
    "export const GAMES_MOMENTS_ROUTE = '/games/our-moments';\n"
    "export const GAMES_WISH_DETECTIVE_ROUTE = '/games/wish-detective';\n",
)
replace_once(
    "web/src/client/routes.test.ts",
    "  GAMES_MOMENTS_ROUTE,\n",
    "  GAMES_MOMENTS_ROUTE,\n  GAMES_WISH_DETECTIVE_ROUTE,\n",
)
replace_once(
    "web/src/client/routes.test.ts",
    "    expect(GAMES_MOMENTS_ROUTE).toBe('/games/our-moments');\n",
    "    expect(GAMES_MOMENTS_ROUTE).toBe('/games/our-moments');\n"
    "    expect(GAMES_WISH_DETECTIVE_ROUTE).toBe('/games/wish-detective');\n",
)
replace_once(
    "web/src/client/routes.test.ts",
    "    expect(activeNavigationArea('/games/our-moments')).toBe('more');\n",
    "    expect(activeNavigationArea('/games/our-moments')).toBe('more');\n"
    "    expect(activeNavigationArea('/games/wish-detective')).toBe('more');\n",
)

# Games hub: the first two entries are now playable for entitled Spaces.
replace_once(
    "web/src/components/GamesProductArea.tsx",
    "import { GAMES_MOMENTS_ROUTE } from '../client/routes';\n",
    "import {\n"
    "  GAMES_MOMENTS_ROUTE,\n"
    "  GAMES_WISH_DETECTIVE_ROUTE,\n"
    "} from '../client/routes';\n",
)
replace_once(
    "web/src/components/GamesProductArea.tsx",
    "] as const;\n\nexport function GamesProductArea",
    "] as const;\n\n"
    "function gameRoute(entry: (typeof GAME_ENTRIES)[number]): string | null {\n"
    "  if (entry === 'moments') return GAMES_MOMENTS_ROUTE;\n"
    "  if (entry === 'wishes') return GAMES_WISH_DETECTIVE_ROUTE;\n"
    "  return null;\n"
    "}\n\n"
    "export function GamesProductArea",
)
replace_once(
    "web/src/components/GamesProductArea.tsx",
    "            {GAME_ENTRIES.map((entry, index) => {\n              const content = (",
    "            {GAME_ENTRIES.map((entry, index) => {\n"
    "              const route = gamesUnlocked ? gameRoute(entry) : null;\n"
    "              const content = (",
)
replace_once(
    "web/src/components/GamesProductArea.tsx",
    "                    {gamesUnlocked && entry === 'moments'\n                      ? t('games.status.playNow')\n                      : gamesUnlocked\n                        ? t('games.status.comingSoon')\n                        : t('games.status.premium')}",
    "                    {route\n"
    "                      ? t('games.status.playNow')\n"
    "                      : gamesUnlocked\n"
    "                        ? t('games.status.comingSoon')\n"
    "                        : t('games.status.premium')}",
)
replace_once(
    "web/src/components/GamesProductArea.tsx",
    "              return gamesUnlocked && entry === 'moments' ? (\n                <Link\n                  className=\"games-entry games-entry-link\"\n                  key={entry}\n                  to={GAMES_MOMENTS_ROUTE}\n                >",
    "              return route ? (\n"
    "                <Link\n"
    "                  className=\"games-entry games-entry-link\"\n"
    "                  key={entry}\n"
    "                  to={route}\n"
    "                >",
)

replace_once(
    "web/src/components/GamesProductArea.test.tsx",
    "import { GAMES_MOMENTS_ROUTE } from '../client/routes';\n",
    "import {\n"
    "  GAMES_MOMENTS_ROUTE,\n"
    "  GAMES_WISH_DETECTIVE_ROUTE,\n"
    "} from '../client/routes';\n",
)
replace_once(
    "web/src/components/GamesProductArea.test.tsx",
    "  it('opens Our Moments for the centralized Games capability while later games remain unavailable', async () => {",
    "  it('opens the implemented sofa games while later games remain unavailable', async () => {",
)
replace_once(
    "web/src/components/GamesProductArea.test.tsx",
    "    expect(screen.getAllByText(games.status.comingSoon)).toHaveLength(4);\n\n"
    "    const momentsLink = screen.getByRole('link', {\n"
    "      name: new RegExp(games.entries.moments.title),\n"
    "    });\n"
    "    expect(momentsLink.textContent).toContain(games.status.playNow);\n"
    "    expect(momentsLink.getAttribute('href')).toBe(GAMES_MOMENTS_ROUTE);",
    "    expect(screen.getAllByText(games.status.comingSoon)).toHaveLength(3);\n\n"
    "    const momentsLink = screen.getByRole('link', {\n"
    "      name: new RegExp(games.entries.moments.title),\n"
    "    });\n"
    "    expect(momentsLink.textContent).toContain(games.status.playNow);\n"
    "    expect(momentsLink.getAttribute('href')).toBe(GAMES_MOMENTS_ROUTE);\n\n"
    "    const wishesLink = screen.getByRole('link', {\n"
    "      name: new RegExp(games.entries.wishes.title),\n"
    "    });\n"
    "    expect(wishesLink.textContent).toContain(games.status.playNow);\n"
    "    expect(wishesLink.getAttribute('href')).toBe(GAMES_WISH_DETECTIVE_ROUTE);",
)

# App route and stylesheet registration.
replace_once(
    "web/src/App.tsx",
    "  GAMES_MOMENTS_ROUTE,\n",
    "  GAMES_MOMENTS_ROUTE,\n  GAMES_WISH_DETECTIVE_ROUTE,\n",
)
replace_once(
    "web/src/App.tsx",
    "import { OurMomentsGamePage } from './components/OurMomentsGamePage';\n",
    "import { OurMomentsGamePage } from './components/OurMomentsGamePage';\n"
    "import { WishDetectiveGamePage } from './components/WishDetectiveGamePage';\n",
)
replace_once(
    "web/src/App.tsx",
    "          <Route\n            path={GAMES_MOMENTS_ROUTE}\n            element={\n              <OurMomentsGamePage\n                apiBaseUrl={apiBaseUrl}\n                accessToken={tokens.accessToken}\n                spaceId={spaceId}\n                currentAccountId={account.id}\n              />\n            }\n          />\n",
    "          <Route\n"
    "            path={GAMES_MOMENTS_ROUTE}\n"
    "            element={\n"
    "              <OurMomentsGamePage\n"
    "                apiBaseUrl={apiBaseUrl}\n"
    "                accessToken={tokens.accessToken}\n"
    "                spaceId={spaceId}\n"
    "                currentAccountId={account.id}\n"
    "              />\n"
    "            }\n"
    "          />\n"
    "          <Route\n"
    "            path={GAMES_WISH_DETECTIVE_ROUTE}\n"
    "            element={\n"
    "              <WishDetectiveGamePage\n"
    "                apiBaseUrl={apiBaseUrl}\n"
    "                accessToken={tokens.accessToken}\n"
    "                spaceId={spaceId}\n"
    "                currentAccountId={account.id}\n"
    "              />\n"
    "            }\n"
    "          />\n",
)
replace_once(
    "web/src/main.tsx",
    "import './components/OurMomentsGamePage.css';\n",
    "import './components/OurMomentsGamePage.css';\n"
    "import './components/WishDetectiveGamePage.css';\n",
)

print("#864 existing-file patches applied")
