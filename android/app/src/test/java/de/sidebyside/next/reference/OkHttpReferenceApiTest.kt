package de.sidebyside.next.reference

import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.MediaType
import sidebyside.api.models.ReadDescriptor
import sidebyside.api.models.UploadDescriptor

class OkHttpReferenceApiTest {
    @Test
    fun bearerTokenOnlyTravelsOnAuthenticatedStreamDescriptors() = runTest {
        val requests = mutableListOf<Request>()
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                requests += request
                val isRead = request.url.encodedPath.contains("read")
                val body = if (isRead) byteArrayOf(1, 2, 3) else byteArrayOf()
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(if (isRead) 200 else 204)
                    .message("OK")
                    .body(body.toResponseBody("image/jpeg".toMediaType()))
                    .build()
            }
            .build()
        val api = OkHttpReferenceApi("https://api.example.invalid", client)
        val image = SelectedImage(byteArrayOf(4, 5), "test.jpg", "image/jpeg")
        val attachment = AttachmentDetail(
            createdAt = OffsetDateTime.parse("2026-08-26T08:00:00Z"),
            durationSeconds = null,
            hasThumbnail = false,
            height = null,
            id = UUID.fromString("00000000-0000-0000-0000-000000000030"),
            mediaType = MediaType.IMAGE,
            mimeType = "image/jpeg",
            propertySize = 2,
            status = "UPLOADING",
            version = 1,
            width = null,
        )

        api.uploadAttachmentBytes(
            "secret",
            UploadDescriptor(
                attachment = attachment,
                method = UploadDescriptor.Method.STREAM,
                requiredHeaders = mapOf("Content-Type" to "image/jpeg"),
                uploadUrl = "/stream",
            ),
            image,
        )
        api.uploadAttachmentBytes(
            "secret",
            UploadDescriptor(
                attachment = attachment,
                method = UploadDescriptor.Method.SIGNED_UPLOAD,
                requiredHeaders = emptyMap(),
                uploadUrl = "https://storage.example.invalid/signed",
            ),
            image,
        )
        api.readImageBytes(
            "secret",
            ReadDescriptor(ReadDescriptor.Method.STREAM, "/read-stream"),
        )
        api.readImageBytes(
            "secret",
            ReadDescriptor(ReadDescriptor.Method.SIGNED_URL, "https://storage.example.invalid/read-signed"),
        )

        assertEquals("Bearer secret", requests[0].header("Authorization"))
        assertNull(requests[1].header("Authorization"))
        assertEquals("Bearer secret", requests[2].header("Authorization"))
        assertNull(requests[3].header("Authorization"))
        assertEquals("https://api.example.invalid/stream", requests[0].url.toString())
        assertEquals("https://storage.example.invalid/signed", requests[1].url.toString())
    }
}
