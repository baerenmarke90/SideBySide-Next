"""ServerAdmin-only operational read models.

The dashboard reports SideBySide application state only. It deliberately has
no shell, filesystem, container, SQL-console, or private-content inspection
surface.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from sidebyside.api.deps import CurrentServerAdmin, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.api.v1.health import build_revision
from sidebyside.attachments.models import Attachment, AttachmentStatus
from sidebyside.config import get_settings
from sidebyside.core.clock import now
from sidebyside.identity.models import Account
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.relationship.models import Membership, MembershipStatus

router = APIRouter(prefix="/server-admin", tags=["server-admin"])
_PROCESS_STARTED_AT = now()


class ServerAdminFailedJob(ApiModel):
    """Safe queue metadata without payload or raw exception text."""

    id: UUID
    kind: str
    attempts: int
    max_attempts: int
    finished_at: datetime | None


class ServerAdminOverview(ApiModel):
    """Privacy-safe operational projection for one SideBySide installation."""

    application_status: str
    database_status: str
    worker_status: str
    media_status: str
    deployment: str
    environment: str
    build_revision: str
    process_started_at: datetime
    public_base_url: str
    media_store: str
    mail_transport: str
    oidc_connection_count: int
    demo_mode: bool
    database_provider: str
    account_count: int
    active_space_count: int
    accounts_last_24h: int
    accounts_last_7d: int
    media_object_count: int
    media_stored_bytes: int
    jobs_pending: int
    jobs_running: int
    jobs_failed: int
    last_successful_job_at: datetime | None
    recent_failed_jobs: list[ServerAdminFailedJob]


def _job_count(session: Session, status: JobStatus) -> int:
    return session.execute(
        select(func.count()).select_from(Job).where(Job.status == status.value)
    ).scalar_one()


@router.get(
    "/overview",
    response_model=ServerAdminOverview,
    responses=problem_responses(401, 403),
)
def get_server_admin_overview(
    _: CurrentServerAdmin,
    session: DbSession,
) -> ServerAdminOverview:
    """Return safe operational state for an authorized ServerAdmin."""
    settings = get_settings()
    current_time = now()

    account_count = session.execute(
        select(func.count()).select_from(Account)
    ).scalar_one()
    active_space_count = session.execute(
        select(func.count(distinct(Membership.space_id))).where(
            Membership.status == MembershipStatus.ACTIVE.value
        )
    ).scalar_one()
    accounts_last_24h = session.execute(
        select(func.count())
        .select_from(Account)
        .where(Account.created_at >= current_time - timedelta(hours=24))
    ).scalar_one()
    accounts_last_7d = session.execute(
        select(func.count())
        .select_from(Account)
        .where(Account.created_at >= current_time - timedelta(days=7))
    ).scalar_one()

    media_object_count = session.execute(
        select(func.count()).select_from(Attachment).where(
            Attachment.status == AttachmentStatus.READY.value
        )
    ).scalar_one()
    media_stored_bytes = session.execute(
        select(func.coalesce(func.sum(Attachment.size), 0)).where(
            Attachment.status == AttachmentStatus.READY.value
        )
    ).scalar_one()

    last_successful_job_at = session.execute(
        select(func.max(Job.finished_at)).where(Job.status == JobStatus.SUCCEEDED.value)
    ).scalar_one()
    failed_jobs = (
        session.execute(
            select(Job)
            .where(Job.status == JobStatus.FAILED.value)
            .order_by(Job.finished_at.desc().nullslast(), Job.created_at.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )

    return ServerAdminOverview(
        application_status="ok",
        database_status="ok",
        worker_status="no_heartbeat_signal",
        media_status="not_probed",
        deployment=settings.deployment.value,
        environment=settings.environment.value,
        build_revision=build_revision(),
        process_started_at=_PROCESS_STARTED_AT,
        public_base_url=settings.public_base_url,
        media_store=settings.media_store.value,
        mail_transport=settings.mail_transport.value,
        oidc_connection_count=len(settings.oidc_connections),
        demo_mode=settings.demo_mode,
        database_provider="postgresql",
        account_count=account_count,
        active_space_count=active_space_count,
        accounts_last_24h=accounts_last_24h,
        accounts_last_7d=accounts_last_7d,
        media_object_count=media_object_count,
        media_stored_bytes=int(media_stored_bytes),
        jobs_pending=_job_count(session, JobStatus.PENDING),
        jobs_running=_job_count(session, JobStatus.RUNNING),
        jobs_failed=_job_count(session, JobStatus.FAILED),
        last_successful_job_at=last_successful_job_at,
        recent_failed_jobs=[
            ServerAdminFailedJob(
                id=job.id,
                kind=job.kind,
                attempts=job.attempts,
                max_attempts=job.max_attempts,
                finished_at=job.finished_at,
            )
            for job in failed_jobs
        ],
    )
