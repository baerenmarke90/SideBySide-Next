package de.sidebyside.next.i18n

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import de.sidebyside.next.reference.R
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.xmlpull.v1.XmlPullParser

/**
 * The set of languages this app is written in.
 *
 * It is declared in two places that have to agree: `locales_config.xml`, which
 * tells Android what the app supports, and `localeFilters` in the Gradle build,
 * which decides what is actually packaged. If they drift apart, the app claims
 * a language whose strings are not in the package — or ships translations for a
 * language it does not claim.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SupportedLocalesTest {
    private val context: Context get() = ApplicationProvider.getApplicationContext()

    @Test
    fun declaresExactlyTheLanguagesTheProductIsWrittenIn() {
        // German only, deliberately. A second locale is a product decision, and
        // adding it means adding a `values-xx` folder, this entry, and the same
        // tag in `localeFilters` — all three, or the interface mixes languages.
        assertEquals(listOf("de"), declaredLocales())
    }

    @Test
    @Config(qualifiers = "fr-rFR")
    fun theProductCopyStaysGermanOnADeviceInAnotherLanguage() {
        // Nothing resolves to another language, because nothing else is
        // packaged. Before the locale set was declared, roughly eighty library
        // translations were, and a device set to one of them read a screen half
        // in German and half in that language.
        assertEquals("Anmelden", context.getString(R.string.entry_sign_in))
    }

    private fun declaredLocales(): List<String> {
        val locales = mutableListOf<String>()
        val parser = context.resources.getXml(R.xml.locales_config)
        while (parser.next() != XmlPullParser.END_DOCUMENT) {
            if (parser.eventType == XmlPullParser.START_TAG && parser.name == "locale") {
                locales += parser.getAttributeValue(ANDROID_NAMESPACE, "name")
            }
        }
        return locales
    }

    private companion object {
        const val ANDROID_NAMESPACE = "http://schemas.android.com/apk/res/android"
    }
}
