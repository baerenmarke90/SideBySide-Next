package de.sidebyside.next.profile

import org.junit.Assert.assertEquals
import org.junit.Test

class PersonIdentityTest {
    @Test
    fun multiPartNameUsesFirstAndLastInitial() {
        assertEquals("AB", personInitials("Anna Maria Beispiel"))
    }

    @Test
    fun singlePartNameUsesTwoCharacters() {
        assertEquals("李雷", personInitials("李雷"))
    }

    @Test
    fun initialsTrackTrimmedDisplayName() {
        assertEquals("ÄR", personInitials("  Änne   Reis  "))
    }

    @Test
    fun emptyNameHasDeterministicFallback() {
        assertEquals("?", personInitials("   "))
    }
}
