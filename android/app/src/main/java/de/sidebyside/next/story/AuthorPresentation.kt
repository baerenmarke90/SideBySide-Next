package de.sidebyside.next.story

import sidebyside.api.models.AuthorSummary

internal fun AuthorSummary.displayNameForUi(formerMemberLabel: String): String =
    if (isFormerMember == true) formerMemberLabel else displayName
