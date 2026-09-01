package de.sidebyside.next.contract

import de.sidebyside.next.reference.SideBySideJson
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Test
import sidebyside.api.models.PasskeyAuthenticationRequest
import sidebyside.api.models.PasskeyRegistrationRequest

/**
 * The two models that could not be compiled at all.
 *
 * Their `credential` is a free-form object in the contract, which the generator
 * mapped to `Map<String, Any>` — a type kotlinx.serialization cannot serialize,
 * so both files were excluded from the Android build and Passkey work was
 * blocked. They now carry `JsonElement`, and compiling is only half the claim:
 * these tests are the other half.
 */
class PasskeyRequestSerializationTest {
    @Test
    fun carriesANestedCredentialThroughSerializationUnchanged() {
        // A WebAuthn credential is nested and not flat, which is why the
        // contract leaves it free-form in the first place.
        val credential = mapOf(
            "id" to JsonPrimitive("credential-id"),
            "type" to JsonPrimitive("public-key"),
            "response" to buildJsonObject {
                put("clientDataJSON", JsonPrimitive("eyJ0eXAiOiJ3ZWJhdXRobi5nZXQifQ"))
                put("signature", JsonPrimitive("MEUCIQD"))
            },
        )

        val request = PasskeyAuthenticationRequest(
            credential = credential,
            deviceName = "Pixel",
            platform = "android",
        )
        val encoded = SideBySideJson.encodeToString(
            PasskeyAuthenticationRequest.serializer(),
            request,
        )
        val decoded = SideBySideJson.decodeFromString(
            PasskeyAuthenticationRequest.serializer(),
            encoded,
        )

        assertEquals(request, decoded)
        assertEquals(
            "MEUCIQD",
            (decoded.credential.getValue("response") as JsonObject)["signature"]
                ?.jsonPrimitive?.content,
        )
    }

    @Test
    fun writesTheCredentialAsAnObjectRatherThanAsAString() {
        // A credential encoded as a quoted string would be accepted by the
        // client and refused by the server, which is the kind of failure a
        // compile check cannot see.
        val request = PasskeyRegistrationRequest(
            credential = mapOf("id" to JsonPrimitive("credential-id")),
            name = "Pixel",
        )

        val encoded = SideBySideJson.parseToJsonElement(
            SideBySideJson.encodeToString(PasskeyRegistrationRequest.serializer(), request),
        )

        assertEquals(
            "credential-id",
            encoded.jsonObject.getValue("credential").jsonObject
                .getValue("id").jsonPrimitive.content,
        )
    }
}
