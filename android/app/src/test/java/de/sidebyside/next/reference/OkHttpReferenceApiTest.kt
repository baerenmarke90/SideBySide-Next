package de.sidebyside.next.reference

import java.time.OffsetDateTime
import java.util.UUID
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.encodeToString
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import okhttp3.ResponseBody.Companion.toResponseBody
import okio.Buffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import sidebyside.api.models.AttachmentDetail
import sidebyside.api.models.MediaType
import sidebyside.api.models.PartnerProfileView
import sidebyside.api.models.ProfileIdentityUpdate
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

    @Test
    fun profileIdentityPatchCarriesAccountVersionAndGeneratedBody() = runTest {
        val requests = mutableListOf<Request>()
        val responseProfile = profile(version = 8, displayName = "Änne")
        val client = jsonClient(requests, responseProfile)
        val api = OkHttpReferenceApi("https://api.example.invalid", client)
        val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000011")
        val accountId = responseProfile.accountId

        val result = api.updateProfileIdentity(
            spaceId = spaceId,
            accessToken = "secret",
            accountId = accountId,
            ifMatch = 7,
            update = ProfileIdentityUpdate(displayName = "Änne"),
        )

        val request = requests.single()
        val body = requestBody(request)
        assertEquals("PATCH", request.method)
        assertEquals("Bearer secret", request.header("Authorization"))
        assertEquals("7", request.header("If-Match"))
        assertEquals(
            "/api/v1/spaces/$spaceId/profiles/$accountId",
            request.url.encodedPath,
        )
        assertTrue(body.contains("\"displayName\":\"Änne\""))
        assertFalse(body.contains("profileAttachmentId"))
        assertEquals(8, result.version)
    }

    @Test
    fun avatarRemovalSendsExplicitJsonNull() = runTest {
        val requests = mutableListOf<Request>()
        val responseProfile = profile(version = 4)
        val client = jsonClient(requests, responseProfile)
        val api = OkHttpReferenceApi("https://api.example.invalid", client)
        val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000012")

        api.removeProfileAvatar(
            spaceId = spaceId,
            accessToken = "secret",
            accountId = responseProfile.accountId,
            ifMatch = 3,
        )

        val request = requests.single()
        assertEquals("PATCH", request.method)
        assertEquals("3", request.header("If-Match"))
        assertEquals("{\"profileAttachmentId\":null}", requestBody(request))
    }

    @Test
    fun profileAvatarReadUsesAuthenticatedStableRoute() = runTest {
        val requests = mutableListOf<Request>()
        val avatar = byteArrayOf(8, 6, 7)
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                requests += request
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(avatar.toResponseBody("image/jpeg".toMediaType()))
                    .build()
            }
            .build()
        val api = OkHttpReferenceApi("https://api.example.invalid", client)
        val spaceId = UUID.fromString("00000000-0000-0000-0000-000000000013")
        val accountId = UUID.fromString("00000000-0000-0000-0000-000000000014")

        val result = api.readProfileAvatar(spaceId, "secret", accountId)

        assertTrue(result.contentEquals(avatar))
        assertEquals("Bearer secret", requests.single().header("Authorization"))
        assertEquals(
            "/api/v1/spaces/$spaceId/profiles/$accountId/avatar/content",
            requests.single().url.encodedPath,
        )
    }

    private fun jsonClient(
        requests: MutableList<Request>,
        responseProfile: PartnerProfileView,
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val request = chain.request()
            requests += request
            Response.Builder()
                .request(request)
                .protocol(Protocol.HTTP_1_1)
                .code(200)
                .message("OK")
                .body(
                    SideBySideJson
                        .encodeToString(PartnerProfileView.serializer(), responseProfile)
                        .toResponseBody("application/json".toMediaType()),
                )
                .build()
        }
        .build()

    private fun profile(
        version: Int,
        displayName: String = "Anna",
    ): PartnerProfileView = PartnerProfileView(
        accountId = UUID.fromString("00000000-0000-0000-0000-000000000021"),
        createdAt = OffsetDateTime.parse("2026-08-31T08:00:00Z"),
        displayName = displayName,
        id = UUID.fromString("00000000-0000-0000-0000-000000000022"),
        preferences = emptyList(),
        profileAttachmentId = null,
        updatedAt = OffsetDateTime.parse("2026-08-31T08:00:00Z"),
        version = version,
    )

    private fun requestBody(request: Request): String = Buffer().use { buffer ->
        request.body?.writeTo(buffer)
        buffer.readUtf8()
    }
}
