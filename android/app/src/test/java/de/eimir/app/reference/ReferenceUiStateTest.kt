package de.eimir.app.reference

import org.junit.Assert.assertNull
import org.junit.Test

class ReferenceUiStateTest {
    @Test
    fun defaultStateContainsNoSavedWriteResult() {
        val state = ReferenceUiState(configured = true, loggedIn = true)
        assertNull(state.lastMemoryTitle)
        assertNull(state.lastMemoryBody)
        assertNull(state.lastImageBytes)
    }
}
