package de.sidebyside.next.place

import java.math.BigDecimal
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Pins the single coordinate-validation predicate (#684) shared by the
 * create/edit form's real-time field feedback and the ViewModel's
 * submit-time guard: both blank is valid, exactly one set is invalid,
 * non-numeric values are invalid, and the server's `-90..90` / `-180..180`
 * range is enforced client-side as early feedback.
 */
class PlaceCoordinatesTest {
    @Test
    fun bothBlankIsValidWithNoCoordinates() {
        assertEquals(PlaceCoordinatesResult.Valid(null, null), parsePlaceCoordinates("", ""))
    }

    @Test
    fun latitudeSetLongitudeBlankIsUnpaired() {
        assertEquals(PlaceCoordinatesResult.Unpaired, parsePlaceCoordinates("52.5", ""))
    }

    @Test
    fun longitudeSetLatitudeBlankIsUnpaired() {
        assertEquals(PlaceCoordinatesResult.Unpaired, parsePlaceCoordinates("", "13.4"))
    }

    @Test
    fun nonNumericValuesAreRejected() {
        assertEquals(PlaceCoordinatesResult.NotNumeric, parsePlaceCoordinates("abc", "def"))
    }

    @Test
    fun nonNumericLatitudeAloneIsRejected() {
        assertEquals(PlaceCoordinatesResult.NotNumeric, parsePlaceCoordinates("abc", "13.4"))
    }

    @Test
    fun latitudeBelowMinimumIsOutOfRange() {
        assertEquals(PlaceCoordinatesResult.OutOfRange, parsePlaceCoordinates("-91", "13.4"))
    }

    @Test
    fun latitudeAboveMaximumIsOutOfRange() {
        assertEquals(PlaceCoordinatesResult.OutOfRange, parsePlaceCoordinates("91", "13.4"))
    }

    @Test
    fun longitudeBelowMinimumIsOutOfRange() {
        assertEquals(PlaceCoordinatesResult.OutOfRange, parsePlaceCoordinates("52.5", "-181"))
    }

    @Test
    fun longitudeAboveMaximumIsOutOfRange() {
        assertEquals(PlaceCoordinatesResult.OutOfRange, parsePlaceCoordinates("52.5", "181"))
    }

    @Test
    fun validNegativeValuesAreAccepted() {
        assertEquals(
            PlaceCoordinatesResult.Valid(BigDecimal("-33.5"), BigDecimal("-70.6")),
            parsePlaceCoordinates("-33.5", "-70.6"),
        )
    }

    @Test
    fun boundaryValuesAreAccepted() {
        assertEquals(
            PlaceCoordinatesResult.Valid(BigDecimal("-90"), BigDecimal("-180")),
            parsePlaceCoordinates("-90", "-180"),
        )
        assertEquals(
            PlaceCoordinatesResult.Valid(BigDecimal("90"), BigDecimal("180")),
            parsePlaceCoordinates("90", "180"),
        )
    }
}
