package de.eimir.app.story

import eimir.api.models.AuthorSummary

internal fun AuthorSummary.displayNameForUi(formerMemberLabel: String): String =
    if (isFormerMember == true) formerMemberLabel else displayName
