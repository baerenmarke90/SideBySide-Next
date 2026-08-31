package de.sidebyside.next.demo

/**
 * The canonical public demo deployment.
 *
 * One place holds the address, so entering the demo never rewrites the
 * configured production or Self-Hosted endpoint and there is a single boundary
 * to change when the demo moves. Making it user-editable is deliberately out of
 * scope for this version.
 */
object DemoEndpoint {
    const val BASE_URL: String = "https://demo.sbs.ur-cloud.de"
}

/**
 * The canonical demo personas.
 *
 * The names are the server's contract for `POST /api/v1/demo/entry`; the demo
 * deployment owns the accounts and their data.
 */
enum class DemoPersona(val wireValue: String) {
    Lea("LEA"),
    Alex("ALEX"),
}
