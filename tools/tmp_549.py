from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one match in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if marker in text:
        return
    target.write_text(text.rstrip() + "\n\n" + content.rstrip() + "\n", encoding="utf-8", newline="\n")


# Backend API: add an authoritative read-only Space lifecycle projection.
replace_once(
    "backend/src/sidebyside/api/v1/server_admin.py",
    "from sqlalchemy import distinct, exists, func, or_, select",
    "from sqlalchemy import case, distinct, exists, func, or_, select",
)
replace_once(
    "backend/src/sidebyside/api/v1/server_admin.py",
    "from sidebyside.relationship.models import Membership, MembershipStatus",
    "from sidebyside.relationship.models import (\n"
    "    MAX_ACTIVE_PARTNERS,\n"
    "    Membership,\n"
    "    MembershipStatus,\n"
    "    Space,\n"
    ")",
)
replace_once(
    "backend/src/sidebyside/api/v1/server_admin.py",
    'VerificationFilter = Literal["all", "verified", "unverified"]\n',
    'VerificationFilter = Literal["all", "verified", "unverified"]\n'
    'SpaceStatusFilter = Literal["all", "active", "inactive", "empty", "anomaly"]\n'
    'SpaceLifecycleStatus = Literal["active", "inactive", "empty"]\n',
)
replace_once(
    "backend/src/sidebyside/api/v1/server_admin.py",
    "class ServerAdminAccountList(ApiModel):\n"
    "    items: list[ServerAdminAccountSummary]\n"
    "    total: int\n"
    "    limit: int\n"
    "    offset: int\n\n\n",
    "class ServerAdminAccountList(ApiModel):\n"
    "    items: list[ServerAdminAccountSummary]\n"
    "    total: int\n"
    "    limit: int\n"
    "    offset: int\n\n\n"
    "class ServerAdminSpaceSummary(ApiModel):\n"
    "    id: UUID\n"
    "    created_at: datetime\n"
    "    lifecycle_status: SpaceLifecycleStatus\n"
    "    membership_count: int\n"
    "    active_membership_count: int\n"
    "    historical_membership_count: int\n"
    "    left_membership_count: int\n"
    "    removed_membership_count: int\n"
    "    first_membership_at: datetime | None\n"
    "    last_membership_change_at: datetime | None\n"
    "    anomaly_codes: list[str]\n\n\n"
    "class ServerAdminSpaceDetail(ServerAdminSpaceSummary):\n"
    "    latest_membership_ended_at: datetime | None\n\n\n"
    "class ServerAdminSpaceList(ApiModel):\n"
    "    items: list[ServerAdminSpaceSummary]\n"
    "    total: int\n"
    "    limit: int\n"
    "    offset: int\n\n\n",
)

space_helpers = r'''
def _space_aggregate_subquery() -> Any:
    return (
        select(
            Membership.space_id.label("space_id"),
            func.count(Membership.id).label("membership_count"),
            func.sum(
                case(
                    (Membership.status == MembershipStatus.ACTIVE.value, 1),
                    else_=0,
                )
            ).label("active_membership_count"),
            func.sum(
                case(
                    (Membership.status == MembershipStatus.LEFT.value, 1),
                    else_=0,
                )
            ).label("left_membership_count"),
            func.sum(
                case(
                    (Membership.status == MembershipStatus.REMOVED.value, 1),
                    else_=0,
                )
            ).label("removed_membership_count"),
            func.min(func.coalesce(Membership.joined_at, Membership.created_at)).label(
                "first_membership_at"
            ),
            func.max(
                func.coalesce(
                    Membership.ended_at,
                    Membership.joined_at,
                    Membership.created_at,
                )
            ).label("last_membership_change_at"),
            func.max(Membership.ended_at).label("latest_membership_ended_at"),
        )
        .group_by(Membership.space_id)
        .subquery()
    )


def _space_projection(aggregate: Any) -> tuple[Any, ...]:
    return (
        Space.id.label("id"),
        Space.created_at.label("created_at"),
        func.coalesce(aggregate.c.membership_count, 0).label("membership_count"),
        func.coalesce(aggregate.c.active_membership_count, 0).label(
            "active_membership_count"
        ),
        func.coalesce(aggregate.c.left_membership_count, 0).label(
            "left_membership_count"
        ),
        func.coalesce(aggregate.c.removed_membership_count, 0).label(
            "removed_membership_count"
        ),
        aggregate.c.first_membership_at,
        aggregate.c.last_membership_change_at,
        aggregate.c.latest_membership_ended_at,
    )


def _space_lifecycle_status(
    *, active_membership_count: int, membership_count: int
) -> SpaceLifecycleStatus:
    if active_membership_count > 0:
        return "active"
    if membership_count > 0:
        return "inactive"
    return "empty"


def _space_anomaly_codes(*, active_membership_count: int, membership_count: int) -> list[str]:
    codes: list[str] = []
    if membership_count == 0:
        codes.append("no_memberships")
    if active_membership_count > MAX_ACTIVE_PARTNERS:
        codes.append("too_many_active_memberships")
    return codes


def _space_summary_from_row(row: Any) -> ServerAdminSpaceSummary:
    values = row._mapping
    membership_count = int(values["membership_count"] or 0)
    active_membership_count = int(values["active_membership_count"] or 0)
    return ServerAdminSpaceSummary(
        id=values["id"],
        created_at=values["created_at"],
        lifecycle_status=_space_lifecycle_status(
            active_membership_count=active_membership_count,
            membership_count=membership_count,
        ),
        membership_count=membership_count,
        active_membership_count=active_membership_count,
        historical_membership_count=max(0, membership_count - active_membership_count),
        left_membership_count=int(values["left_membership_count"] or 0),
        removed_membership_count=int(values["removed_membership_count"] or 0),
        first_membership_at=values["first_membership_at"],
        last_membership_change_at=values["last_membership_change_at"],
        anomaly_codes=_space_anomaly_codes(
            active_membership_count=active_membership_count,
            membership_count=membership_count,
        ),
    )


def _space_detail_from_row(row: Any) -> ServerAdminSpaceDetail:
    summary = _space_summary_from_row(row)
    return ServerAdminSpaceDetail(
        **summary.model_dump(),
        latest_membership_ended_at=row._mapping["latest_membership_ended_at"],
    )


def _parse_space_id(space_id: str) -> UUID:
    parsed = parse_id(space_id)
    if parsed is None:
        raise NotFoundError("Space not found.", "SERVER_ADMIN_SPACE_NOT_FOUND")
    return parsed


'''
replace_once(
    "backend/src/sidebyside/api/v1/server_admin.py",
    "def _parse_account_id(account_id: str) -> UUID:\n",
    space_helpers + "def _parse_account_id(account_id: str) -> UUID:\n",
)

space_endpoints = r'''
@router.get(
    "/spaces",
    response_model=ServerAdminSpaceList,
    responses=problem_responses(401, 403, 422),
)
def list_server_admin_spaces(
    _: CurrentServerAdmin,
    session: DbSession,
    query: Annotated[str | None, Query(max_length=64)] = None,
    space_status: Annotated[SpaceStatusFilter, Query(alias="status")] = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ServerAdminSpaceList:
    """Return lifecycle metadata for Spaces without relationship content."""
    aggregate = _space_aggregate_subquery()
    membership_count = func.coalesce(aggregate.c.membership_count, 0)
    active_membership_count = func.coalesce(aggregate.c.active_membership_count, 0)
    conditions: list[Any] = []

    if query is not None and query.strip():
        parsed = parse_id(query.strip())
        if parsed is None:
            return ServerAdminSpaceList(items=[], total=0, limit=limit, offset=offset)
        conditions.append(Space.id == parsed)

    if space_status == "active":
        conditions.append(active_membership_count > 0)
    elif space_status == "inactive":
        conditions.extend((active_membership_count == 0, membership_count > 0))
    elif space_status == "empty":
        conditions.append(membership_count == 0)
    elif space_status == "anomaly":
        conditions.append(
            or_(
                membership_count == 0,
                active_membership_count > MAX_ACTIVE_PARTNERS,
            )
        )

    count_statement = select(func.count()).select_from(Space).outerjoin(
        aggregate, aggregate.c.space_id == Space.id
    )
    if conditions:
        count_statement = count_statement.where(*conditions)
    total = session.execute(count_statement).scalar_one()

    statement = (
        select(*_space_projection(aggregate))
        .select_from(Space)
        .outerjoin(aggregate, aggregate.c.space_id == Space.id)
    )
    if conditions:
        statement = statement.where(*conditions)
    statement = statement.order_by(Space.created_at.desc()).limit(limit).offset(offset)
    rows = session.execute(statement).all()
    return ServerAdminSpaceList(
        items=[_space_summary_from_row(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/spaces/{space_id}",
    response_model=ServerAdminSpaceDetail,
    responses=problem_responses(401, 403, 404),
)
def get_server_admin_space(
    _: CurrentServerAdmin,
    session: DbSession,
    space_id: Annotated[str, Path(max_length=64)],
) -> ServerAdminSpaceDetail:
    """Return one Space's privacy-safe lifecycle projection."""
    parsed = _parse_space_id(space_id)
    aggregate = _space_aggregate_subquery()
    statement = (
        select(*_space_projection(aggregate))
        .select_from(Space)
        .outerjoin(aggregate, aggregate.c.space_id == Space.id)
        .where(Space.id == parsed)
    )
    row = session.execute(statement).one_or_none()
    if row is None:
        raise NotFoundError("Space not found.", "SERVER_ADMIN_SPACE_NOT_FOUND")
    return _space_detail_from_row(row)


'''
replace_once(
    "backend/src/sidebyside/api/v1/server_admin.py",
    '@router.get(\n    "/accounts",\n',
    space_endpoints + '@router.get(\n    "/accounts",\n',
)

# Backend integration coverage and endpoint completeness.
replace_once(
    "backend/tests/integration/test_server_admin.py",
    "from sidebyside.jobs.models import Job, JobStatus\n",
    "from sidebyside.jobs.models import Job, JobStatus\n"
    "from sidebyside.relationship import service as relationship\n"
    "from sidebyside.relationship.models import Space\n",
)
replace_once(
    "backend/tests/integration/test_server_admin.py",
    '    response = client.get("/api/v1/server-admin/overview")\n\n    assert response.status_code == 401\n',
    '    response = client.get("/api/v1/server-admin/overview")\n'
    '    spaces = client.get("/api/v1/server-admin/spaces")\n\n'
    '    assert response.status_code == 401\n'
    '    assert spaces.status_code == 401\n',
)
replace_once(
    "backend/tests/integration/test_server_admin.py",
    '    overview = client.get("/api/v1/server-admin/overview", headers=auth(token))\n\n'
    '    assert capability.status_code == 200\n',
    '    overview = client.get("/api/v1/server-admin/overview", headers=auth(token))\n'
    '    spaces = client.get("/api/v1/server-admin/spaces", headers=auth(token))\n\n'
    '    assert capability.status_code == 200\n',
)
replace_once(
    "backend/tests/integration/test_server_admin.py",
    '    assert overview.status_code == 403\n'
    '    assert overview.json()["code"] == "SERVER_ADMIN_REQUIRED"\n',
    '    assert overview.status_code == 403\n'
    '    assert overview.json()["code"] == "SERVER_ADMIN_REQUIRED"\n'
    '    assert spaces.status_code == 403\n'
    '    assert spaces.json()["code"] == "SERVER_ADMIN_REQUIRED"\n',
)
space_test = r'''

def test_space_directory_exposes_only_lifecycle_metadata(
    client,
    session,
    server_admin_allowlist,
) -> None:  # type: ignore[no-untyped-def]
    _, token = _admin(session)

    active_owner = make_account(session, "Active owner")
    active_space = make_space(session, active_owner)

    inactive_owner = make_account(session, "Inactive owner")
    inactive_space = make_space(session, inactive_owner)
    membership = relationship.require_membership(session, inactive_owner, inactive_space.id)
    relationship.end_membership(membership)

    empty_space = Space()
    session.add(empty_space)
    session.flush()

    response = client.get(
        "/api/v1/server-admin/spaces?status=all&limit=50",
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    by_id = {item["id"]: item for item in payload["items"]}
    assert str(active_space.id) in by_id
    assert str(inactive_space.id) in by_id
    assert str(empty_space.id) in by_id

    expected_fields = {
        "id",
        "createdAt",
        "lifecycleStatus",
        "membershipCount",
        "activeMembershipCount",
        "historicalMembershipCount",
        "leftMembershipCount",
        "removedMembershipCount",
        "firstMembershipAt",
        "lastMembershipChangeAt",
        "anomalyCodes",
    }
    assert set(by_id[str(active_space.id)]) == expected_fields
    assert by_id[str(active_space.id)]["lifecycleStatus"] == "active"
    assert by_id[str(active_space.id)]["activeMembershipCount"] == 1
    assert by_id[str(active_space.id)]["historicalMembershipCount"] == 0

    inactive = by_id[str(inactive_space.id)]
    assert inactive["lifecycleStatus"] == "inactive"
    assert inactive["activeMembershipCount"] == 0
    assert inactive["historicalMembershipCount"] == 1
    assert inactive["leftMembershipCount"] == 1
    assert inactive["removedMembershipCount"] == 0

    empty = by_id[str(empty_space.id)]
    assert empty["lifecycleStatus"] == "empty"
    assert empty["membershipCount"] == 0
    assert empty["anomalyCodes"] == ["no_memberships"]

    inactive_filter = client.get(
        "/api/v1/server-admin/spaces?status=inactive",
        headers=auth(token),
    )
    assert inactive_filter.status_code == 200
    assert {item["id"] for item in inactive_filter.json()["items"]} == {
        str(inactive_space.id)
    }

    anomaly_filter = client.get(
        "/api/v1/server-admin/spaces?status=anomaly",
        headers=auth(token),
    )
    assert anomaly_filter.status_code == 200
    assert {item["id"] for item in anomaly_filter.json()["items"]} == {
        str(empty_space.id)
    }

    by_exact_id = client.get(
        f"/api/v1/server-admin/spaces?query={inactive_space.id}",
        headers=auth(token),
    )
    assert by_exact_id.status_code == 200
    assert by_exact_id.json()["total"] == 1
    assert by_exact_id.json()["items"][0]["id"] == str(inactive_space.id)

    invalid_id = client.get(
        "/api/v1/server-admin/spaces?query=not-a-space-id",
        headers=auth(token),
    )
    assert invalid_id.status_code == 200
    assert invalid_id.json()["total"] == 0
    assert invalid_id.json()["items"] == []

    detail = client.get(
        f"/api/v1/server-admin/spaces/{inactive_space.id}",
        headers=auth(token),
    )
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert set(detail_payload) == expected_fields | {"latestMembershipEndedAt"}
    assert detail_payload["latestMembershipEndedAt"] is not None
    serialized = detail.text.lower()
    for forbidden in (
        "displayname",
        "email",
        "relationshipstartedon",
        "memory",
        "owner_only",
        "media",
    ):
        assert forbidden not in serialized


'''
replace_once(
    "backend/tests/integration/test_server_admin.py",
    "def test_server_admin_can_suspend_account_and_sessions_are_revoked(\n",
    space_test + "def test_server_admin_can_suspend_account_and_sessions_are_revoked(\n",
)
replace_once(
    "backend/tests/integration/test_endpoint_matrix.py",
    '    ("GET", "/api/v1/server-admin/overview"),\n',
    '    ("GET", "/api/v1/server-admin/overview"),\n'
    '    ("GET", "/api/v1/server-admin/spaces"),\n'
    '    ("GET", "/api/v1/server-admin/spaces/{spaceId}"),\n',
)

# Web: a real Spaces section now that the backend projection exists.
spaces_component = r'''import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { ServerAdminApi } from '../api/generated/apis/ServerAdminApi';
import type { ServerAdminSpaceDetail } from '../api/generated/models/ServerAdminSpaceDetail';
import { resolvedLocale, useTranslation } from '../i18n';

const PAGE_SIZE = 25;

type SpaceFilter = 'all' | 'active' | 'inactive' | 'empty' | 'anomaly';

function formatDate(value: Date | null): string {
  if (!value) return '–';
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(value);
}

function lifecycleLabel(status: string, t: (key: string) => string): string {
  switch (status) {
    case 'active':
      return t('serverAdmin.spaces.lifecycle.active');
    case 'inactive':
      return t('serverAdmin.spaces.lifecycle.inactive');
    case 'empty':
      return t('serverAdmin.spaces.lifecycle.empty');
    default:
      return status;
  }
}

function anomalyLabel(code: string, t: (key: string) => string): string {
  switch (code) {
    case 'no_memberships':
      return t('serverAdmin.spaces.anomalies.noMemberships');
    case 'too_many_active_memberships':
      return t('serverAdmin.spaces.anomalies.tooManyActive');
    default:
      return code;
  }
}

function SpaceDetail({ space }: { space: ServerAdminSpaceDetail }) {
  const { t } = useTranslation();
  return (
    <section
      className="server-admin-panel server-admin-panel-wide"
      aria-labelledby="server-space-detail-title"
    >
      <div className="server-admin-account-detail-heading">
        <div>
          <p className="eyebrow">{t('serverAdmin.spaces.detail.eyebrow')}</p>
          <h2 id="server-space-detail-title">
            {t('serverAdmin.spaces.detail.title')}
          </h2>
          <p className="server-admin-muted server-admin-actor-id">{space.id}</p>
        </div>
        <span
          className={`server-admin-badge ${space.anomalyCodes.length > 0 ? 'is-warning' : 'is-ok'}`}
        >
          {lifecycleLabel(space.lifecycleStatus, t)}
        </span>
      </div>

      <dl className="server-admin-metrics server-admin-account-detail-metrics">
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.createdAt')}</dt>
          <dd>{formatDate(space.createdAt)}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.memberships')}</dt>
          <dd>{space.membershipCount}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.activeMemberships')}</dt>
          <dd>{space.activeMembershipCount}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.historicalMemberships')}</dt>
          <dd>{space.historicalMembershipCount}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.leftMemberships')}</dt>
          <dd>{space.leftMembershipCount}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.removedMemberships')}</dt>
          <dd>{space.removedMembershipCount}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.firstMembership')}</dt>
          <dd>{formatDate(space.firstMembershipAt)}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.lastLifecycleChange')}</dt>
          <dd>{formatDate(space.lastMembershipChangeAt)}</dd>
        </div>
        <div className="server-admin-metric">
          <dt>{t('serverAdmin.spaces.latestEndedMembership')}</dt>
          <dd>{formatDate(space.latestMembershipEndedAt)}</dd>
        </div>
      </dl>

      {space.anomalyCodes.length > 0 ? (
        <div className="server-admin-warning-panel">
          <strong>{t('serverAdmin.spaces.anomalies.title')}</strong>
          <ul>
            {space.anomalyCodes.map((code) => (
              <li key={code}>{anomalyLabel(code, t)}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <p className="server-admin-muted">{t('serverAdmin.spaces.detail.privacy')}</p>
    </section>
  );
}

export function ServerAdminSpacesPanel({ api }: { api: ServerAdminApi }) {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<SpaceFilter>('all');
  const [offset, setOffset] = useState(0);
  const [selectedSpaceId, setSelectedSpaceId] = useState<string | null>(null);

  const request = useMemo(
    () => ({
      query: search.trim() || undefined,
      status,
      limit: PAGE_SIZE,
      offset,
    }),
    [offset, search, status],
  );
  const spacesQuery = useQuery({
    queryKey: ['server-admin', 'spaces', request],
    queryFn: () =>
      api.listServerAdminSpacesApiV1ServerAdminSpacesGet(request),
    retry: false,
  });
  const detailQuery = useQuery({
    queryKey: ['server-admin', 'space', selectedSpaceId],
    queryFn: () =>
      api.getServerAdminSpaceApiV1ServerAdminSpacesSpaceIdGet({
        spaceId: selectedSpaceId as string,
      }),
    enabled: selectedSpaceId !== null,
    retry: false,
  });

  const total = spacesQuery.data?.total ?? 0;
  const canPrevious = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  return (
    <>
      <section
        className="server-admin-panel server-admin-panel-wide"
        aria-labelledby="server-spaces-title"
      >
        <div className="server-admin-panel-heading">
          <div>
            <h2 id="server-spaces-title">{t('serverAdmin.spaces.title')}</h2>
            <p className="server-admin-muted">{t('serverAdmin.spaces.body')}</p>
          </div>
          <span className="server-admin-count">
            {total} {t('serverAdmin.spaces.totalSuffix')}
          </span>
        </div>

        <div className="server-admin-account-filters">
          <label>
            {t('serverAdmin.spaces.search')}
            <input
              type="search"
              value={search}
              placeholder={t('serverAdmin.spaces.searchPlaceholder')}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            {t('serverAdmin.spaces.status.label')}
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as SpaceFilter);
                setOffset(0);
              }}
            >
              <option value="all">{t('serverAdmin.spaces.status.all')}</option>
              <option value="active">{t('serverAdmin.spaces.status.active')}</option>
              <option value="inactive">
                {t('serverAdmin.spaces.status.inactive')}
              </option>
              <option value="empty">{t('serverAdmin.spaces.status.empty')}</option>
              <option value="anomaly">
                {t('serverAdmin.spaces.status.anomaly')}
              </option>
            </select>
          </label>
        </div>

        {spacesQuery.isPending ? (
          <p className="server-admin-muted">{t('serverAdmin.spaces.loading')}</p>
        ) : spacesQuery.error ? (
          <p className="status status-error" role="alert">
            {t('serverAdmin.spaces.error')}
          </p>
        ) : spacesQuery.data?.items.length === 0 ? (
          <p className="server-admin-muted">{t('serverAdmin.spaces.empty')}</p>
        ) : (
          <div className="server-admin-table-scroll">
            <table className="server-admin-table">
              <thead>
                <tr>
                  <th scope="col">{t('serverAdmin.spaces.spaceId')}</th>
                  <th scope="col">{t('serverAdmin.spaces.lifecycleLabel')}</th>
                  <th scope="col">{t('serverAdmin.spaces.activeMemberships')}</th>
                  <th scope="col">{t('serverAdmin.spaces.historicalMemberships')}</th>
                  <th scope="col">{t('serverAdmin.spaces.lastLifecycleChange')}</th>
                  <th scope="col">{t('serverAdmin.spaces.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {spacesQuery.data?.items.map((space) => (
                  <tr key={space.id}>
                    <td className="server-admin-actor-id">{space.id}</td>
                    <td>
                      <span
                        className={`server-admin-badge ${space.anomalyCodes.length > 0 ? 'is-warning' : 'is-ok'}`}
                      >
                        {lifecycleLabel(space.lifecycleStatus, t)}
                      </span>
                    </td>
                    <td>{space.activeMembershipCount}</td>
                    <td>{space.historicalMembershipCount}</td>
                    <td>{formatDate(space.lastMembershipChangeAt)}</td>
                    <td>
                      <button
                        type="button"
                        className="text-button"
                        onClick={() => setSelectedSpaceId(space.id)}
                      >
                        {t('serverAdmin.spaces.open')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="server-admin-pagination">
          <button
            type="button"
            className="secondary-button"
            disabled={!canPrevious}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            {t('serverAdmin.spaces.previous')}
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={!canNext}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            {t('serverAdmin.spaces.next')}
          </button>
        </div>
      </section>

      {selectedSpaceId !== null ? (
        detailQuery.isPending ? (
          <section className="server-admin-panel server-admin-panel-wide">
            <p className="server-admin-muted">
              {t('serverAdmin.spaces.detail.loading')}
            </p>
          </section>
        ) : detailQuery.error ? (
          <section className="server-admin-panel server-admin-panel-wide">
            <p className="status status-error" role="alert">
              {t('serverAdmin.spaces.detail.error')}
            </p>
            <button type="button" onClick={() => setSelectedSpaceId(null)}>
              {t('serverAdmin.spaces.detail.close')}
            </button>
          </section>
        ) : detailQuery.data ? (
          <>
            <SpaceDetail space={detailQuery.data} />
            <button
              type="button"
              className="secondary-button"
              onClick={() => setSelectedSpaceId(null)}
            >
              {t('serverAdmin.spaces.detail.close')}
            </button>
          </>
        ) : null
      ) : null}
    </>
  );
}
'''
(ROOT / "web/src/components/ServerAdminSpacesPanel.tsx").write_text(
    spaces_component, encoding="utf-8", newline="\n"
)

replace_once(
    "web/src/components/ServerAdminPage.tsx",
    "import { ServerAdminAccountsPanel } from './ServerAdminAccountsPanel';\n",
    "import { ServerAdminAccountsPanel } from './ServerAdminAccountsPanel';\n"
    "import { ServerAdminSpacesPanel } from './ServerAdminSpacesPanel';\n",
)
replace_once(
    "web/src/components/ServerAdminPage.tsx",
    "  'accounts',\n  'jobs',\n",
    "  'accounts',\n  'spaces',\n  'jobs',\n",
)
replace_once(
    "web/src/components/ServerAdminPage.tsx",
    "    { id: 'accounts', label: t('serverAdmin.navigation.accounts') },\n"
    "    { id: 'jobs', label: t('serverAdmin.navigation.jobs') },\n",
    "    { id: 'accounts', label: t('serverAdmin.navigation.accounts') },\n"
    "    { id: 'spaces', label: t('serverAdmin.navigation.spaces') },\n"
    "    { id: 'jobs', label: t('serverAdmin.navigation.jobs') },\n",
)
replace_once(
    "web/src/components/ServerAdminPage.tsx",
    "    if (section === 'accounts') {\n"
    "      void queryClient.invalidateQueries({\n"
    "        queryKey: ['server-admin', 'accounts'],\n"
    "      });\n"
    "      void queryClient.invalidateQueries({\n"
    "        queryKey: ['server-admin', 'action-activity'],\n"
    "      });\n"
    "    }\n",
    "    if (section === 'accounts') {\n"
    "      void queryClient.invalidateQueries({\n"
    "        queryKey: ['server-admin', 'accounts'],\n"
    "      });\n"
    "      void queryClient.invalidateQueries({\n"
    "        queryKey: ['server-admin', 'action-activity'],\n"
    "      });\n"
    "      return;\n"
    "    }\n"
    "    if (section === 'spaces') {\n"
    "      void queryClient.invalidateQueries({\n"
    "        queryKey: ['server-admin', 'spaces'],\n"
    "      });\n"
    "      void queryClient.invalidateQueries({\n"
    "        queryKey: ['server-admin', 'space'],\n"
    "      });\n"
    "    }\n",
)
replace_once(
    "web/src/components/ServerAdminPage.tsx",
    "            {section === 'activity' ? (\n",
    "            {section === 'spaces' ? (\n"
    "              <ServerAdminSpacesPanel api={apis.serverAdmin} />\n"
    "            ) : null}\n\n"
    "            {section === 'activity' ? (\n",
)
replace_once(
    "web/src/components/ServerAdminNavigation.test.tsx",
    "    expect(resolveServerAdminSection('accounts')).toBe('accounts');\n"
    "    expect(resolveServerAdminSection('jobs')).toBe('jobs');\n",
    "    expect(resolveServerAdminSection('accounts')).toBe('accounts');\n"
    "    expect(resolveServerAdminSection('spaces')).toBe('spaces');\n"
    "    expect(resolveServerAdminSection('jobs')).toBe('jobs');\n",
)
replace_once(
    "web/src/components/ServerAdminNavigation.test.tsx",
    "    expect(html.match(/server-admin-section-link/g)).toHaveLength(6);\n",
    "    expect(html.match(/server-admin-section-link/g)).toHaveLength(7);\n",
)
replace_once(
    "web/src/components/ServerAdminNavigation.test.tsx",
    '    expect(html).toContain(\'href="/server-admin?section=accounts"\');\n'
    '    expect(html).toContain(\'href="/server-admin?section=jobs"\');\n',
    '    expect(html).toContain(\'href="/server-admin?section=accounts"\');\n'
    '    expect(html).toContain(\'href="/server-admin?section=spaces"\');\n'
    '    expect(html).toContain(\'href="/server-admin?section=jobs"\');\n',
)
replace_once(
    "web/src/i18n/locales/serverAdmin.ts",
    "    accounts: 'Benutzer',\n    jobs: 'Jobs & Betrieb',\n",
    "    accounts: 'Benutzer',\n    spaces: 'Spaces',\n    jobs: 'Jobs & Betrieb',\n",
)
spaces_i18n = r'''  spaces: {
    title: 'Space-Lifecycle',
    body: 'Zeigt ausschließlich technische Membership- und Lifecycle-Metadaten. Beziehungsinhalte, Profile und Medien bleiben unsichtbar.',
    totalSuffix: 'Spaces',
    search: 'Space suchen',
    searchPlaceholder: 'Exakte Space-ID',
    loading: 'Spaces werden geladen …',
    error: 'Die Space-Lifecycle-Daten konnten nicht geladen werden.',
    empty: 'Keine passenden Spaces gefunden.',
    spaceId: 'Space-ID',
    lifecycleLabel: 'Lifecycle',
    memberships: 'Memberships gesamt',
    activeMemberships: 'Aktive Memberships',
    historicalMemberships: 'Historische Memberships',
    leftMemberships: 'Verlassen',
    removedMemberships: 'Entfernt',
    createdAt: 'Space erstellt',
    firstMembership: 'Erste Membership',
    lastLifecycleChange: 'Letzte Lifecycle-Änderung',
    latestEndedMembership: 'Letzte beendete Membership',
    actions: 'Details',
    open: 'Öffnen',
    previous: 'Zurück',
    next: 'Weiter',
    status: {
      label: 'Status',
      all: 'Alle',
      active: 'Aktiv',
      inactive: 'Historisch / inaktiv',
      empty: 'Ohne Membership',
      anomaly: 'Auffällig',
    },
    lifecycle: {
      active: 'Aktiv',
      inactive: 'Historisch / inaktiv',
      empty: 'Ohne Membership',
    },
    anomalies: {
      title: 'Lifecycle-Hinweis',
      noMemberships: 'Dieser Space besitzt keine Membership-Zeilen.',
      tooManyActive: 'Dieser Space besitzt mehr aktive Memberships als das Domain-Maximum erlaubt.',
    },
    detail: {
      eyebrow: 'Privacy-safe Operator-Metadaten',
      title: 'Space-Details',
      loading: 'Space-Details werden geladen …',
      error: 'Die Space-Details konnten nicht geladen werden.',
      close: 'Details schließen',
      privacy: 'Diese Ansicht enthält keine Namen, E-Mail-Adressen, Beziehungsdaten, Memories, Nachrichten, Medien oder OWNER_ONLY-Metadaten.',
    },
  },
'''
replace_once(
    "web/src/i18n/locales/serverAdmin.ts",
    "  activity: {\n",
    spaces_i18n + "  activity: {\n",
)

append_once(
    "docs/SERVER-ADMIN.md",
    "## Space lifecycle directory",
    """## Space lifecycle directory

`GET /api/v1/server-admin/spaces` and `GET /api/v1/server-admin/spaces/{spaceId}`
expose a deliberately narrow, read-only lifecycle projection derived from `Space` and
`Membership` state. The projection contains IDs, creation/lifecycle timestamps,
Membership status counts and coarse anomaly codes only.

It does **not** expose Account identity correlation, Space profile/relationship dates,
Memories, Notes, messages, media, OWNER_ONLY state or behavioral/engagement analytics.
Space termination, partner removal and reactivation remain outside this operator surface
until the authoritative lifecycle decisions in #518 are complete.
""",
)

print("#549 source patch applied")
