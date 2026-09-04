"""Create and reset the canonical SideBySide demo space.

The demo is a development/QA facility, not a second domain implementation.
Every seeded resource is created through the same service boundary as normal
application traffic. The only destructive shortcut is deleting the already
verified demo Space during reset; media is detached and purged first so reset
does not leave provider objects behind.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.attachments import binding as attachment_binding
from sidebyside.attachments import service as attachment_service
from sidebyside.attachments.models import Attachment
from sidebyside.auth import passwords
from sidebyside.authorization import AuthorizationContext, ContentVisibility
from sidebyside.chapters import service as chapter_service
from sidebyside.collections import service as collection_service
from sidebyside.comments import service as comment_service
from sidebyside.comments.models import CommentTarget
from sidebyside.config import Environment
from sidebyside.demo.assets import (
    DemoAssetCatalog,
    import_demo_asset,
    load_and_validate_assets,
)
from sidebyside.demo.story import CHAPTERS, MEMORIES
from sidebyside.engagement import service as engagement_service
from sidebyside.gift_ideas import service as gift_idea_service
from sidebyside.heart_moments import service as heart_moment_service
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment
from sidebyside.identity import service as identity_service
from sidebyside.identity.models import Account
from sidebyside.memories import service as memory_service
from sidebyside.memories.models import Memory
from sidebyside.milestones import service as milestone_service
from sidebyside.people import service as people_service
from sidebyside.people.models import DateRepeat, ImportantDateType, PersonRelationship
from sidebyside.places import service as place_service
from sidebyside.plans import service as plan_service
from sidebyside.private_collections import service as private_collection_service
from sidebyside.private_notes import service as private_note_service
from sidebyside.profiles import service as profile_service
from sidebyside.profiles.models import (
    PreferenceCategory,
    PreferenceSentiment,
    ProfileVisibility,
)
from sidebyside.relationship import profile as relationship_profile
from sidebyside.relationship import service as relationship_service
from sidebyside.relationship.models import DurationDisplayMode, Membership, MembershipStatus, Space
from sidebyside.wishes import service as wish_service

LEA_EMAIL = "demo-lea@sidebyside.invalid"
ALEX_EMAIL = "demo-alex@sidebyside.invalid"
LEA_NAME = "Lea Sommer"
ALEX_NAME = "Alex Winter"
PRIVATE_CANARY_LEA = "CANARY-PRIVATE-LEA-7421"
PRIVATE_CANARY_ALEX = "CANARY-PRIVATE-ALEX-9134"


@dataclass(frozen=True)
class DemoSeedResult:
    """Stable identifiers returned by create/reset without exposing credentials."""

    lea_id: UUID
    alex_id: UUID
    space_id: UUID
    reference_date: date
    created: bool


def _ensure_allowed(environment: Environment) -> None:
    if environment is Environment.PRODUCTION:
        raise RuntimeError("Canonical demo data must never be created in production.")


def _active_space_ids(session: Session, account: Account) -> set[UUID]:
    return set(
        session.execute(
            select(Membership.space_id).where(
                Membership.account_id == account.id,
                Membership.status == MembershipStatus.ACTIVE.value,
            )
        ).scalars()
    )


def _validate_demo_account(account: Account, *, expected_name: str, email: str) -> None:
    if account.display_name != expected_name:
        raise RuntimeError(f"Refusing demo operation: {email} exists with a non-demo display name.")


def _existing_accounts(session: Session) -> tuple[Account | None, Account | None]:
    lea = identity_service.find_by_email(session, LEA_EMAIL)
    alex = identity_service.find_by_email(session, ALEX_EMAIL)
    if lea is not None:
        _validate_demo_account(lea, expected_name=LEA_NAME, email=LEA_EMAIL)
    if alex is not None:
        _validate_demo_account(alex, expected_name=ALEX_NAME, email=ALEX_EMAIL)
    if (lea is None) != (alex is None):
        raise RuntimeError(
            "Refusing demo operation: only one reserved demo account exists. "
            "Resolve the partial state explicitly before retrying."
        )
    return lea, alex


def _shared_demo_space(
    session: Session,
    lea: Account,
    alex: Account,
    *,
    required: bool,
) -> Space | None:
    lea_spaces = _active_space_ids(session, lea)
    alex_spaces = _active_space_ids(session, alex)
    shared = lea_spaces & alex_spaces

    if len(shared) > 1:
        raise RuntimeError("Refusing demo operation: demo accounts share multiple active Spaces.")
    if shared:
        space_id = next(iter(shared))
        if lea_spaces != {space_id} or alex_spaces != {space_id}:
            raise RuntimeError(
                "Refusing demo operation: a reserved demo account also belongs to "
                "another active Space."
            )
        space = session.get(Space, space_id)
        if space is None:
            raise RuntimeError("Demo membership references a missing Space.")
        return space

    if lea_spaces or alex_spaces:
        raise RuntimeError(
            "Refusing demo operation: reserved demo accounts are active in different Spaces."
        )
    if required:
        raise RuntimeError("Canonical demo Space does not exist; run the create command first.")
    return None


def _create_accounts(
    session: Session,
    *,
    lea_password: str,
    alex_password: str,
) -> tuple[Account, Account]:
    # Validate both before writing either account so bad input cannot create a
    # partial reserved identity even inside a manually managed transaction.
    passwords.validate(lea_password)
    passwords.validate(alex_password)
    lea = identity_service.create_account(
        session,
        display_name=LEA_NAME,
        email=LEA_EMAIL,
        password_hash=passwords.hash_password(lea_password),
    )
    alex = identity_service.create_account(
        session,
        display_name=ALEX_NAME,
        email=ALEX_EMAIL,
        password_hash=passwords.hash_password(alex_password),
    )
    return lea, alex


def _new_space(session: Session, lea: Account, alex: Account) -> Space:
    space = relationship_service.create_space(session, lea)
    relationship_service.add_member(session, space.id, alex)
    return space


def _context(account: Account, space: Space) -> AuthorizationContext:
    return AuthorizationContext(account_id=account.id, space_id=space.id)


def _instant(day: date, hour: int) -> datetime:
    return datetime.combine(day, time(hour=hour, tzinfo=UTC))


def _seed_relationship(
    session: Session,
    space: Space,
    *,
    reference_date: date,
) -> None:
    profile = relationship_profile.load(session, space.id)
    if profile is None:
        raise RuntimeError("Fresh demo Space has no SpaceProfile.")
    relationship_profile.update(
        session,
        space.id,
        expected_version=profile.version,
        relationship_started_on=reference_date - timedelta(days=3 * 365 + 83),
        show_relationship_duration=True,
        duration_display_mode=DurationDisplayMode.YEARS_MONTHS,
        today=reference_date,
    )


def _seed_profiles(
    session: Session,
    lea: Account,
    alex: Account,
    lea_context: AuthorizationContext,
    alex_context: AuthorizationContext,
) -> None:
    profile_service.create_preference(
        session,
        lea_context,
        account_id=lea.id,
        visibility=ProfileVisibility.SELF_PROFILE,
        category=PreferenceCategory.FOOD,
        topic="Lieblingsessen",
        sentiment=PreferenceSentiment.LOVE,
        value="Pasta mit viel Parmesan",
    )
    profile_service.create_preference(
        session,
        lea_context,
        account_id=lea.id,
        visibility=ProfileVisibility.SELF_PROFILE,
        category=PreferenceCategory.ACTIVITIES,
        topic="Sonntag",
        sentiment=PreferenceSentiment.LIKE,
        value="Lange Spaziergänge und Kaffee danach",
    )
    profile_service.create_preference(
        session,
        alex_context,
        account_id=alex.id,
        visibility=ProfileVisibility.SELF_PROFILE,
        category=PreferenceCategory.MUSIC,
        topic="Unterwegs",
        sentiment=PreferenceSentiment.LOVE,
        value="Indie und ruhige elektronische Musik",
    )
    profile_service.create_preference(
        session,
        alex_context,
        account_id=alex.id,
        visibility=ProfileVisibility.SELF_PROFILE,
        category=PreferenceCategory.TRAVEL,
        topic="Kurzurlaub",
        sentiment=PreferenceSentiment.LIKE,
        value="Kleine Städte, Seen und gutes Frühstück",
    )
    profile_service.create_preference(
        session,
        lea_context,
        account_id=alex.id,
        visibility=ProfileVisibility.PRIVATE_PARTNER_NOTE,
        category=PreferenceCategory.OTHER,
        topic="Überraschung",
        sentiment=PreferenceSentiment.LOVE,
        value=f"{PRIVATE_CANARY_LEA} - Alex freut sich über handgeschriebene Karten.",
    )
    profile_service.create_preference(
        session,
        alex_context,
        account_id=lea.id,
        visibility=ProfileVisibility.PRIVATE_PARTNER_NOTE,
        category=PreferenceCategory.OTHER,
        topic="Überraschung",
        sentiment=PreferenceSentiment.LOVE,
        value=f"{PRIVATE_CANARY_ALEX} - Lea mag Frühstück als kleine Überraschung.",
    )


def _seed_people(
    session: Session,
    lea_context: AuthorizationContext,
    alex_context: AuthorizationContext,
    *,
    reference_date: date,
) -> None:
    shared_friend = people_service.create_person(
        session,
        lea_context,
        display_name="Mara",
        relationship=PersonRelationship.FRIEND,
        birthday=date(reference_date.year - 31, 5, 12),
        birthday_year_known=True,
        visibility=ContentVisibility.SHARED,
    )
    lea_private = people_service.create_person(
        session,
        lea_context,
        display_name=f"{PRIVATE_CANARY_LEA} Person",
        relationship=PersonRelationship.OTHER,
        birthday=None,
        birthday_year_known=False,
        visibility=ContentVisibility.PRIVATE,
    )
    alex_private = people_service.create_person(
        session,
        alex_context,
        display_name=f"{PRIVATE_CANARY_ALEX} Person",
        relationship=PersonRelationship.OTHER,
        birthday=None,
        birthday_year_known=False,
        visibility=ContentVisibility.PRIVATE,
    )
    people_service.create_date(
        session,
        lea_context,
        label="Mara hat Geburtstag",
        date_type=ImportantDateType.BIRTHDAY,
        day=date(reference_date.year, 10, 18),
        repeats=DateRepeat.ANNUALLY,
        visibility=ContentVisibility.SHARED,
        related_person_id=shared_friend.id,
    )
    people_service.create_date(
        session,
        lea_context,
        label=f"{PRIVATE_CANARY_LEA} privater Termin",
        date_type=ImportantDateType.CUSTOM,
        day=reference_date + timedelta(days=9),
        repeats=DateRepeat.NONE,
        visibility=ContentVisibility.PRIVATE,
        related_person_id=lea_private.id,
    )
    people_service.create_date(
        session,
        alex_context,
        label=f"{PRIVATE_CANARY_ALEX} privater Termin",
        date_type=ImportantDateType.CUSTOM,
        day=reference_date + timedelta(days=12),
        repeats=DateRepeat.NONE,
        visibility=ContentVisibility.PRIVATE,
        related_person_id=alex_private.id,
    )


def _seed_story(
    session: Session,
    lea_context: AuthorizationContext,
    alex_context: AuthorizationContext,
    *,
    assets: DemoAssetCatalog,
    reference_date: date,
) -> None:
    contexts = {"lea": lea_context, "alex": alex_context}
    memories: dict[str, Memory] = {}
    for story in MEMORIES:
        context = contexts[story.owner]
        memory = memory_service.create_memory(
            session,
            context,
            title=story.title,
            body=story.body,
            happened_on=reference_date - timedelta(days=story.days_ago),
        )
        memories[story.key] = memory
        attachments = [
            import_demo_asset(session, context, assets.require(asset_id))
            for asset_id in story.asset_ids
        ]
        memory_service.replace_attachments(
            session,
            context,
            memory.id,
            expected_version=memory.version,
            entries=[(attachment.id, index) for index, attachment in enumerate(attachments)],
        )

    shared_heart = heart_moment_service.create_heart_moment(
        session,
        alex_context,
        text="Danke, dass du heute einfach zugehört hast.",
        emotion=HeartEmotion.APPRECIATED,
        visibility=ContentVisibility.SHARED,
        happened_on=reference_date - timedelta(days=3),
    )
    private_image = import_demo_asset(session, lea_context, assets.require("private-flowers"))
    heart_moment_service.create_heart_moment(
        session,
        lea_context,
        text=PRIVATE_CANARY_LEA,
        emotion=HeartEmotion.GRATEFUL,
        visibility=ContentVisibility.PRIVATE,
        happened_on=reference_date - timedelta(days=2),
        attachment_id=private_image.id,
    )

    milestone_service.create_milestone(
        session,
        alex_context,
        title="Unser erster gemeinsamer Garten",
        body="Die ersten Kräuter haben tatsächlich überlebt.",
        happened_on=reference_date - timedelta(days=136),
    )
    milestone_service.create_milestone(
        session,
        lea_context,
        title="Ein Jahr in unserer Wohnung",
        body="Noch immer unser liebster Ort für einen ruhigen Sonntag.",
        happened_on=reference_date - timedelta(days=23),
    )
    milestone_service.create_milestone(
        session,
        alex_context,
        title="Drei Jahre wir",
        body="Kein großes Programm, nur unser Lieblingsessen und ein langer Spaziergang.",
        happened_on=reference_date - timedelta(days=83),
    )

    comment_service.create_comment(
        session,
        lea_context,
        target_type=CommentTarget.MEMORY,
        target_id=memories["lake-walk"].id,
        body="Nächstes Mal nehmen wir wieder Kaffee mit.",
    )
    comment_service.create_comment(
        session,
        alex_context,
        target_type=CommentTarget.MEMORY,
        target_id=memories["ravioli-evening"].id,
        body="Die krummen waren trotzdem die besten.",
    )
    comment_service.create_comment(
        session,
        lea_context,
        target_type=CommentTarget.MEMORY,
        target_id=memories["trier-weekend"].id,
        body="Da müssen wir nochmal hin, aber diesmal zwei Nächte.",
    )
    comment_service.create_comment(
        session,
        lea_context,
        target_type=CommentTarget.HEART_MOMENT,
        target_id=shared_heart.id,
        body="Das bedeutet mir viel.",
    )


def _seed_planning(
    session: Session,
    lea_context: AuthorizationContext,
    alex_context: AuthorizationContext,
    *,
    reference_date: date,
) -> None:
    cafe = place_service.create_place(
        session,
        lea_context,
        name="Café am Markt",
        description="Unser Treffpunkt für Kaffee und ein langes Frühstück.",
        address=None,
        latitude=None,
        longitude=None,
    )
    lake = place_service.create_place(
        session,
        alex_context,
        name="Waldsee",
        description="Ruhige Runde am Wasser für Spaziergänge und Picknick.",
        address=None,
        latitude=None,
        longitude=None,
    )

    wish_service.create_wish(session, lea_context, title="Zusammen einen Töpferkurs machen")
    planned_wish = wish_service.create_wish(session, alex_context, title="Herbstwanderung")
    planned = plan_service.convert_wish_to_plan(
        session,
        alex_context,
        planned_wish.id,
        expected_version=planned_wish.version,
        title=None,
        description="Wenn die Blätter bunt werden, einen ganzen Tag für den Wald freihalten.",
        place_id=lake.id,
    ).plan
    plan_service.schedule_plan(
        session,
        alex_context,
        planned.id,
        expected_version=planned.version,
        planned_start=_instant(reference_date + timedelta(days=18), 10),
        planned_end=_instant(reference_date + timedelta(days=18), 17),
    )

    completed_wish = wish_service.create_wish(
        session, lea_context, title="Gemeinsamer Tagesausflug"
    )
    completed = plan_service.convert_wish_to_plan(
        session,
        lea_context,
        completed_wish.id,
        expected_version=completed_wish.version,
        title=None,
        description="Morgens los und erst unterwegs entscheiden, wo wir landen.",
        place_id=lake.id,
    ).plan
    plan_service.complete_plan(
        session,
        lea_context,
        completed.id,
        expected_version=completed.version,
        experienced_on=reference_date - timedelta(days=43),
    )

    plan_service.create_plan(
        session,
        alex_context,
        title="Wellness-Wochenende",
        description="Eine Nacht, Sauna und das Handy möglichst lange in der Tasche lassen.",
        place_id=None,
    )
    plan_service.create_plan(
        session,
        lea_context,
        title="Neues Rezept ausprobieren",
        description="Etwas kochen, das wir beide noch nie gemacht haben.",
        place_id=None,
    )
    concert = plan_service.create_plan(
        session,
        alex_context,
        title="Konzert im Herbst",
        description="Tickets liegen schon bereit.",
        place_id=None,
    )
    plan_service.schedule_plan(
        session,
        alex_context,
        concert.id,
        expected_version=concert.version,
        planned_start=_instant(reference_date + timedelta(days=34), 19),
        planned_end=_instant(reference_date + timedelta(days=34), 23),
    )
    flea_market = plan_service.create_plan(
        session,
        lea_context,
        title="Flohmarkt am Samstag",
        description="Früh los, danach Kaffee und schauen, was wir finden.",
        place_id=cafe.id,
    )
    plan_service.schedule_plan(
        session,
        lea_context,
        flea_market.id,
        expected_version=flea_market.version,
        planned_start=_instant(reference_date + timedelta(days=11), 9),
        planned_end=_instant(reference_date + timedelta(days=11), 13),
    )

    places = {"cafe": cafe, "lake": lake}
    for chapter in CHAPTERS:
        place = places.get(chapter.place) if chapter.place is not None else None
        chapter_service.create_chapter(
            session,
            lea_context if chapter.title in {"Unser Sommer", "Kochabende"} else alex_context,
            title=chapter.title,
            description=chapter.description,
            start_on=reference_date - timedelta(days=chapter.start_days_ago),
            end_on=(
                reference_date - timedelta(days=chapter.end_days_ago)
                if chapter.end_days_ago is not None
                else None
            ),
            place_id=place.id if place is not None else None,
        )

    shared_collection = collection_service.create_collection(
        session,
        lea_context,
        title="Filme für einen Regentag",
    )
    collection_service.create_item(
        session,
        alex_context,
        shared_collection.id,
        title="Den alten Lieblingsfilm nochmal sehen",
        completed=True,
    )
    collection_service.create_item(
        session,
        lea_context,
        shared_collection.id,
        title="Eine neue Komödie aussuchen",
        completed=False,
    )
    recipes = collection_service.create_collection(
        session,
        alex_context,
        title="Rezepte für lange Abende",
    )
    collection_service.create_item(
        session,
        lea_context,
        recipes.id,
        title="Ravioli mit neuer Füllung",
        completed=False,
    )
    collection_service.create_item(
        session,
        alex_context,
        recipes.id,
        title="Ofengemüse mit Feta",
        completed=True,
    )


def _seed_private_area(
    session: Session,
    lea_context: AuthorizationContext,
    alex_context: AuthorizationContext,
    *,
    reference_date: date,
) -> None:
    private_note_service.create_note(
        session,
        lea_context,
        title="Idee für Alex",
        body=f"{PRIVATE_CANARY_LEA} - Den alten Fotostreifen rahmen lassen.",
        pinned=True,
    )
    private_note_service.create_note(
        session,
        alex_context,
        title="Idee für Lea",
        body=f"{PRIVATE_CANARY_ALEX} - Frühstück und Spaziergang vorbereiten.",
        pinned=False,
    )
    private_note_service.create_note(
        session,
        lea_context,
        title="Für den nächsten freien Sonntag",
        body="Kaffee holen, Handy zu Hause lassen und eine große Runde am See drehen.",
        pinned=False,
    )
    private_note_service.create_note(
        session,
        alex_context,
        title="Kleine Überraschung",
        body="Die Blumen vom Markt mitbringen, wenn Lea einen langen Tag hatte.",
        pinned=True,
    )

    gift_idea_service.create_idea(
        session,
        lea_context,
        title="Kleines Fotobuch",
        description=f"{PRIVATE_CANARY_LEA} - mit den Bildern vom See.",
        recipient=ALEX_NAME,
        occasion="Einfach so",
        target_on=reference_date + timedelta(days=45),
        price_text="ca. 25 €",
        url=None,
        pinned=True,
    )
    gift_idea_service.create_idea(
        session,
        alex_context,
        title="Keramikbecher",
        description=f"{PRIVATE_CANARY_ALEX} - passend zum Sonntagskaffee.",
        recipient=LEA_NAME,
        occasion=None,
        target_on=None,
        price_text=None,
        url=None,
        pinned=False,
    )
    gift_idea_service.create_idea(
        session,
        lea_context,
        title="Konzertposter rahmen",
        description="Eine schöne Erinnerung an unseren Konzertabend.",
        recipient=ALEX_NAME,
        occasion=None,
        target_on=None,
        price_text="ca. 20 €",
        url=None,
        pinned=False,
    )
    gift_idea_service.create_idea(
        session,
        alex_context,
        title="Frühstückskorb",
        description="Croissants, Marmelade und der Kaffee, den Lea am liebsten mag.",
        recipient=LEA_NAME,
        occasion="Freier Sonntag",
        target_on=reference_date + timedelta(days=26),
        price_text="ca. 30 €",
        url=None,
        pinned=True,
    )

    lea_collection = private_collection_service.create_collection(
        session,
        lea_context,
        title=f"{PRIVATE_CANARY_LEA} Überraschungen",
    )
    private_collection_service.create_item(
        session,
        lea_context,
        lea_collection.id,
        title="Fotobuch bestellen",
        completed=False,
    )
    private_collection_service.create_item(
        session,
        lea_context,
        lea_collection.id,
        title="Rahmen fürs Konzertposter aussuchen",
        completed=False,
    )
    alex_collection = private_collection_service.create_collection(
        session,
        alex_context,
        title=f"{PRIVATE_CANARY_ALEX} Überraschungen",
    )
    private_collection_service.create_item(
        session,
        alex_context,
        alex_collection.id,
        title="Tisch fürs Frühstück vorbereiten",
        completed=True,
    )
    private_collection_service.create_item(
        session,
        alex_context,
        alex_collection.id,
        title="Blumen auf dem Markt holen",
        completed=False,
    )


def _project_engagement(session: Session) -> None:
    # Drain the finite batch produced by the seed. A cap protects the demo
    # command from looping forever if a future projector starts producing new
    # unprocessed events recursively.
    for _ in range(20):
        if engagement_service.project_pending(session, limit=100) == 0:
            return
    raise RuntimeError("Demo outbox projection did not drain after 20 batches.")


def _seed(
    session: Session,
    lea: Account,
    alex: Account,
    space: Space,
    *,
    assets: DemoAssetCatalog,
    reference_date: date,
) -> None:
    lea_context = _context(lea, space)
    alex_context = _context(alex, space)
    _seed_relationship(session, space, reference_date=reference_date)
    _seed_profiles(session, lea, alex, lea_context, alex_context)
    _seed_people(
        session,
        lea_context,
        alex_context,
        reference_date=reference_date,
    )
    _seed_story(
        session,
        lea_context,
        alex_context,
        assets=assets,
        reference_date=reference_date,
    )
    _seed_planning(
        session,
        lea_context,
        alex_context,
        reference_date=reference_date,
    )
    _seed_private_area(
        session,
        lea_context,
        alex_context,
        reference_date=reference_date,
    )
    _project_engagement(session)


def create_demo_space(
    session: Session,
    *,
    environment: Environment,
    lea_password: str,
    alex_password: str,
    reference_date: date,
) -> DemoSeedResult:
    """Create the canonical demo dataset once; repeat calls are idempotent."""
    _ensure_allowed(environment)
    assets = load_and_validate_assets()
    lea, alex = _existing_accounts(session)
    if lea is None or alex is None:
        lea, alex = _create_accounts(
            session,
            lea_password=lea_password,
            alex_password=alex_password,
        )

    existing = _shared_demo_space(session, lea, alex, required=False)
    if existing is not None:
        return DemoSeedResult(
            lea_id=lea.id,
            alex_id=alex.id,
            space_id=existing.id,
            reference_date=reference_date,
            created=False,
        )

    space = _new_space(session, lea, alex)
    _seed(session, lea, alex, space, assets=assets, reference_date=reference_date)
    return DemoSeedResult(
        lea_id=lea.id,
        alex_id=alex.id,
        space_id=space.id,
        reference_date=reference_date,
        created=True,
    )


def _detach_and_purge_media(
    session: Session,
    space: Space,
    lea: Account,
    alex: Account,
) -> None:
    contexts = {
        lea.id: _context(lea, space),
        alex.id: _context(alex, space),
    }

    memories = list(session.execute(select(Memory).where(Memory.space_id == space.id)).scalars())
    for memory in memories:
        if not attachment_binding.attachments_of_memory(session, memory.id):
            continue
        context = contexts.get(memory.owner_id)
        if context is None:
            raise RuntimeError("Demo Space contains a Memory owned by a non-demo account.")
        memory_service.replace_attachments(
            session,
            context,
            memory.id,
            expected_version=memory.version,
            entries=[],
        )

    heart_moments = list(
        session.execute(
            select(HeartMoment).where(
                HeartMoment.space_id == space.id,
                HeartMoment.attachment_id.is_not(None),
            )
        ).scalars()
    )
    for heart_moment in heart_moments:
        context = contexts.get(heart_moment.owner_id)
        if context is None:
            raise RuntimeError("Demo Space contains a HeartMoment owned by a non-demo account.")
        heart_moment_service.delete_heart_moment(
            session,
            context,
            heart_moment.id,
            expected_version=heart_moment.version,
        )

    attachments = list(
        session.execute(select(Attachment).where(Attachment.space_id == space.id)).scalars()
    )
    for attachment in attachments:
        attachment_service.mark_for_deletion(session, attachment)
        if not attachment_service.purge(session, attachment):
            raise RuntimeError(f"Could not purge demo attachment {attachment.id}; reset aborted.")
    session.flush()


def reset_demo_space(
    session: Session,
    *,
    environment: Environment,
    reference_date: date,
) -> DemoSeedResult:
    """Replace only the verified canonical demo Space with a fresh scenario."""
    _ensure_allowed(environment)
    assets = load_and_validate_assets()
    lea, alex = _existing_accounts(session)
    if lea is None or alex is None:
        raise RuntimeError("Canonical demo accounts do not exist; run create first.")
    space = _shared_demo_space(session, lea, alex, required=True)
    assert space is not None

    _detach_and_purge_media(session, space, lea, alex)
    session.delete(space)
    session.flush()

    replacement = _new_space(session, lea, alex)
    _seed(session, lea, alex, replacement, assets=assets, reference_date=reference_date)
    return DemoSeedResult(
        lea_id=lea.id,
        alex_id=alex.id,
        space_id=replacement.id,
        reference_date=reference_date,
        created=True,
    )
