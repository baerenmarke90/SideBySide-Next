package de.sidebyside.next.place

import java.math.BigDecimal

private val LATITUDE_RANGE = BigDecimal("-90")..BigDecimal("90")
private val LONGITUDE_RANGE = BigDecimal("-180")..BigDecimal("180")

/**
 * Outcome of validating a Place's latitude/longitude text pair — the single
 * definition of "valid coordinates" this client uses, shared by the
 * create/edit form's real-time field feedback (#684) and
 * [de.sidebyside.next.reference.ReferenceViewModel]'s submit-time guard, so
 * there is exactly one coordinate-validation domain rather than two.
 *
 * Mirrors the server's authoritative contract as early feedback only: the
 * `PLACE_COORDINATE_PAIR_REQUIRED` pairing rule, decimal parsing via
 * [BigDecimal] (the contract's own decimal type — no locale normalization is
 * introduced here), and the `-90..90` / `-180..180` range. The server remains
 * authoritative; this exists to give the user feedback, and to protect their
 * draft, before a request is ever sent.
 */
sealed interface PlaceCoordinatesResult {
    /** Both blank (`latitude`/`longitude` `null`) or both present, numeric, and in range. */
    data class Valid(val latitude: BigDecimal?, val longitude: BigDecimal?) : PlaceCoordinatesResult

    /** Exactly one of the two fields is blank. */
    data object Unpaired : PlaceCoordinatesResult

    /** Both fields are non-blank but at least one is not a parseable decimal. */
    data object NotNumeric : PlaceCoordinatesResult

    /** Both fields parse, but latitude is outside `[-90, 90]` or longitude outside `[-180, 180]`. */
    data object OutOfRange : PlaceCoordinatesResult
}

fun parsePlaceCoordinates(latitude: String, longitude: String): PlaceCoordinatesResult {
    val lat = latitude.trim()
    val lng = longitude.trim()
    if (lat.isBlank() && lng.isBlank()) return PlaceCoordinatesResult.Valid(null, null)
    if (lat.isBlank() || lng.isBlank()) return PlaceCoordinatesResult.Unpaired
    val parsedLat = runCatching { BigDecimal(lat) }.getOrNull() ?: return PlaceCoordinatesResult.NotNumeric
    val parsedLng = runCatching { BigDecimal(lng) }.getOrNull() ?: return PlaceCoordinatesResult.NotNumeric
    if (parsedLat !in LATITUDE_RANGE || parsedLng !in LONGITUDE_RANGE) return PlaceCoordinatesResult.OutOfRange
    return PlaceCoordinatesResult.Valid(parsedLat, parsedLng)
}
