package de.sidebyside.next.reference

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

val SideBySideJson: Json = Json {
    ignoreUnknownKeys = false
    explicitNulls = false
    encodeDefaults = true
    serializersModule = SerializersModule {
        contextual(UUID::class, UuidSerializer)
        contextual(LocalDate::class, LocalDateSerializer)
        contextual(OffsetDateTime::class, OffsetDateTimeSerializer)
    }
}
