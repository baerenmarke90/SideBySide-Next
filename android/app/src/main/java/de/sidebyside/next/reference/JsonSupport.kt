package de.sidebyside.next.reference

import java.math.BigDecimal
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.serialization.KSerializer
import kotlinx.serialization.SerializationException
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.JsonEncoder
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.modules.SerializersModule
import kotlinx.serialization.modules.contextual

private object UuidSerializer : KSerializer<UUID> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("UUID", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: UUID) = encoder.encodeString(value.toString())

    override fun deserialize(decoder: Decoder): UUID = try {
        UUID.fromString(decoder.decodeString())
    } catch (exception: IllegalArgumentException) {
        throw SerializationException("Invalid UUID", exception)
    }
}

private object LocalDateSerializer : KSerializer<LocalDate> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("LocalDate", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: LocalDate) = encoder.encodeString(value.toString())

    override fun deserialize(decoder: Decoder): LocalDate = try {
        LocalDate.parse(decoder.decodeString())
    } catch (exception: RuntimeException) {
        throw SerializationException("Invalid LocalDate", exception)
    }
}

private object OffsetDateTimeSerializer : KSerializer<OffsetDateTime> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("OffsetDateTime", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: OffsetDateTime) = encoder.encodeString(value.toString())

    override fun deserialize(decoder: Decoder): OffsetDateTime = try {
        OffsetDateTime.parse(decoder.decodeString())
    } catch (exception: RuntimeException) {
        throw SerializationException("Invalid OffsetDateTime", exception)
    }
}

/**
 * Round-trips as a JSON number, not a string — the contract types Place
 * coordinates as `number` — while still avoiding the precision loss a
 * `Double` would risk. Found the hard way: no `BigDecimal` serializer was
 * registered at all until Place needed one, so every response carrying a
 * coordinate failed to decode.
 */
private object BigDecimalSerializer : KSerializer<BigDecimal> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("BigDecimal", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: BigDecimal) {
        val jsonEncoder = encoder as? JsonEncoder
            ?: throw SerializationException("BigDecimal requires the JSON format.")
        jsonEncoder.encodeJsonElement(JsonPrimitive(value))
    }

    override fun deserialize(decoder: Decoder): BigDecimal {
        val jsonDecoder = decoder as? JsonDecoder
            ?: throw SerializationException("BigDecimal requires the JSON format.")
        return try {
            BigDecimal(jsonDecoder.decodeJsonElement().jsonPrimitive.content)
        } catch (exception: NumberFormatException) {
            throw SerializationException("Invalid BigDecimal", exception)
        }
    }
}

val SideBySideJson: Json = Json {
    ignoreUnknownKeys = false
    explicitNulls = false
    encodeDefaults = true
    serializersModule = SerializersModule {
        contextual(UUID::class, UuidSerializer)
        contextual(LocalDate::class, LocalDateSerializer)
        contextual(OffsetDateTime::class, OffsetDateTimeSerializer)
        contextual(BigDecimal::class, BigDecimalSerializer)
    }
}
