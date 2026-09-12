package de.sidebyside.next.story

import java.util.UUID
import org.junit.Assert.assertEquals
import org.junit.Test
import sidebyside.api.models.AuthorSummary

class AuthorPresentationTest {
    @Test
    fun formerMemberUsesClientCopy() {
        val author = AuthorSummary(
            displayName = "",
            id = UUID.randomUUID(),
            isFormerMember = true,
        )
        assertEquals(
            "Ehemaliges Mitglied",
            author.displayNameForUi("Ehemaliges Mitglied"),
        )
    }

    @Test
    fun tombstoneTextDoesNotCreateFormerMemberState() {
        val author = AuthorSummary(
            displayName = "Deleted account",
            id = UUID.randomUUID(),
            isFormerMember = false,
        )
        assertEquals(
            "Deleted account",
            author.displayNameForUi("Ehemaliges Mitglied"),
        )
    }
}
