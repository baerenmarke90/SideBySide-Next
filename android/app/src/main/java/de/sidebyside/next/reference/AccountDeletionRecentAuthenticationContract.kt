package de.sidebyside.next.reference

data class AccountDeletionRecentAuthenticationCapabilities(
    val localPassword: Boolean,
    val passkey: Boolean,
    val oidcConnections: List<String>,
)

data class AccountDeletionOidcStart(
    val authorizationUrl: String,
    val state: String,
)

data class AccountDeletionOidcPending(
    val connectionId: String,
    val authorizationUrl: String,
    val state: String,
)

/**
 * Platform-neutral high-risk authentication calls used by Account deletion.
 *
 * No method returns a bearer step-up proof. Success only creates the
 * server-side grant bound to the current DeviceSession.
 */
interface AccountDeletionRecentAuthenticationContract {
    suspend fun accountDeletionRecentAuthenticationCapabilities(
        accessToken: String,
    ): AccountDeletionRecentAuthenticationCapabilities

    suspend fun accountDeletionRecentAuthenticationPassword(
        accessToken: String,
        password: String,
    )

    /** Returns the WebAuthn request-options JSON understood by Credential Manager. */
    suspend fun startAccountDeletionRecentAuthenticationPasskey(
        accessToken: String,
    ): String

    /** [authenticationResponseJson] is Credential Manager's WebAuthn assertion JSON. */
    suspend fun finishAccountDeletionRecentAuthenticationPasskey(
        accessToken: String,
        authenticationResponseJson: String,
    )

    /** Starts OIDC using only the server-configured Android callback URI. */
    suspend fun startAccountDeletionRecentAuthenticationOidc(
        accessToken: String,
        connectionId: String,
    ): AccountDeletionOidcStart

    suspend fun finishAccountDeletionRecentAuthenticationOidc(
        accessToken: String,
        connectionId: String,
        code: String,
        state: String,
    )
}
