"""Privacy-boundary regression tests for account-scoped Transfer data."""

from uuid import uuid4

import pytest

from sidebyside.core.errors import ErrorCode
from sidebyside.transfer import service
from sidebyside.transfer.archive import TransferArchiveError
from sidebyside.transfer.models import TransferScope


@pytest.mark.parametrize("table_name", ["rule_preferences", "reminder_preferences"])
def test_shared_import_rejects_account_scoped_configuration(table_name: str) -> None:
    member_id = uuid4()
    tables = {
        table_name: [
            {
                "id": str(uuid4()),
                "accountId": str(member_id),
            }
        ]
    }

    with pytest.raises(TransferArchiveError) as exc_info:
        service._validate_ids_and_privacy(  # noqa: SLF001
            TransferScope.SHARED,
            None,
            tables,
            {member_id},
        )

    assert exc_info.value.code == ErrorCode.TRANSFER_PRIVACY_SCOPE_INVALID


@pytest.mark.parametrize("table_name", ["rule_preferences", "reminder_preferences"])
def test_personal_import_rejects_partner_account_scoped_configuration(table_name: str) -> None:
    requester_id = uuid4()
    partner_id = uuid4()
    tables = {
        table_name: [
            {
                "id": str(uuid4()),
                "accountId": str(partner_id),
            }
        ]
    }

    with pytest.raises(TransferArchiveError) as exc_info:
        service._validate_ids_and_privacy(  # noqa: SLF001
            TransferScope.PERSONAL,
            requester_id,
            tables,
            {requester_id, partner_id},
        )

    assert exc_info.value.code == ErrorCode.TRANSFER_PRIVACY_SCOPE_INVALID
