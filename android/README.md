# Android

Hier entsteht ab Milestone M5 der native Kotlin-/Jetpack-Compose-Client.
M0 versioniert nur den vorgesehenen Modulplatz und zieht keine spätere
Produktfunktion vor.

Android spricht über die versionierte REST-/OpenAPI-Schnittstelle mit dem
gemeinsamen Application Core und erhält keine eigene Fachlogik-Kopie.

## Generierte API-Modelle

`api/generated/` enthält die Kotlin-Datenklassen aus `backend/openapi.json`
und wird **nicht von Hand bearbeitet**. Erzeugen mit
`tools/openapi/generate.sh`; CI prüft den eingecheckten Stand gegen den
Vertrag.

Bewusst nur Modelle: ein generierter Service-Layer würde Retrofit oder Ktor
als Runtime-Abhängigkeit festlegen. Diese Wahl trifft, wer den Client baut.

Eine bekannte Einschränkung betrifft `StoryItem`; sie steht in
[`tools/openapi/README.md`](../tools/openapi/README.md) und in #119; sie muss
vor der ersten Nutzung von `/timeline` gelöst sein.
