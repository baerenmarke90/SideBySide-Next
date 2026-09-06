from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def insert_before(path: str, anchor: str, content: str) -> None:
    replace_once(path, anchor, content + anchor)


# ---------------------------------------------------------------------------
# OkHttp adapter: reuse the current DeviceSession bearer token only to drive
# the ceremony. No recent-authentication grant/proof is returned to Android.
# ---------------------------------------------------------------------------
okhttp = "android/app/src/main/java/de/sidebyside/next/reference/OkHttpReferenceApi.kt"
replace_once(
    okhttp,
    "import kotlinx.serialization.json.JsonNull\n",
    "import kotlinx.serialization.json.JsonNull\n"
    "import kotlinx.serialization.json.JsonObject\n",
)
replace_once(
    okhttp,
    "import kotlinx.serialization.json.buildJsonObject\n",
    "import kotlinx.serialization.json.buildJsonObject\n"
    "import kotlinx.serialization.json.jsonArray\n"
    "import kotlinx.serialization.json.jsonPrimitive\n",
)
replace_once(
    okhttp,
    ") : ReferenceContract {\n",
    ") : ReferenceContract, AccountDeletionRecentAuthenticationContract {\n",
)
insert_before(
    okhttp,
    "    override suspend fun deleteOwnAccount(\n",
    '''    override suspend fun accountDeletionRecentAuthenticationCapabilities(\n        accessToken: String,\n    ): AccountDeletionRecentAuthenticationCapabilities {\n        val payload = executeJson(\n            authenticatedRequest(\n                "$baseUrl/api/v1/auth/recent-authentication/account-deletion?client=android",\n                accessToken,\n            ).get().build(),\n            JsonObject.serializer(),\n        )\n        return AccountDeletionRecentAuthenticationCapabilities(\n            localPassword = payload["localPassword"]?.jsonPrimitive?.content == "true",\n            passkey = payload["passkey"]?.jsonPrimitive?.content == "true",\n            oidcConnections = payload["oidcConnections"]\n                ?.jsonArray\n                ?.map { it.jsonPrimitive.content }\n                .orEmpty(),\n        )\n    }\n\n    override suspend fun accountDeletionRecentAuthenticationPassword(\n        accessToken: String,\n        password: String,\n    ) {\n        val body = buildJsonObject { put("password", JsonPrimitive(password)) }\n        executeEmpty(\n            authenticatedRequest(\n                "$baseUrl/api/v1/auth/recent-authentication/account-deletion/password",\n                accessToken,\n            ).post(body.toString().toRequestBody(jsonMediaType)).build(),\n        )\n    }\n\n    override suspend fun startAccountDeletionRecentAuthenticationPasskey(\n        accessToken: String,\n    ): String = executeJson(\n        authenticatedRequest(\n            "$baseUrl/api/v1/auth/recent-authentication/account-deletion/passkeys/start",\n            accessToken,\n        ).post(EMPTY_JSON_BODY.toRequestBody(jsonMediaType)).build(),\n        JsonObject.serializer(),\n    ).toString()\n\n    override suspend fun finishAccountDeletionRecentAuthenticationPasskey(\n        accessToken: String,\n        authenticationResponseJson: String,\n    ) {\n        val credential = SideBySideJson.parseToJsonElement(authenticationResponseJson)\n        val body = buildJsonObject { put("credential", credential) }\n        executeEmpty(\n            authenticatedRequest(\n                "$baseUrl/api/v1/auth/recent-authentication/account-deletion/passkeys/finish",\n                accessToken,\n            ).post(body.toString().toRequestBody(jsonMediaType)).build(),\n        )\n    }\n\n    override suspend fun startAccountDeletionRecentAuthenticationOidc(\n        accessToken: String,\n        connectionId: String,\n    ): AccountDeletionOidcStart {\n        val encodedConnection = java.net.URLEncoder\n            .encode(connectionId, Charsets.UTF_8.name())\n            .replace("+", "%20")\n        val payload = executeJson(\n            authenticatedRequest(\n                "$baseUrl/api/v1/auth/recent-authentication/account-deletion/oidc/$encodedConnection/start?client=android",\n                accessToken,\n            ).post(EMPTY_JSON_BODY.toRequestBody(jsonMediaType)).build(),\n            JsonObject.serializer(),\n        )\n        return AccountDeletionOidcStart(\n            authorizationUrl = payload.getValue("authorizationUrl").jsonPrimitive.content,\n            state = payload.getValue("state").jsonPrimitive.content,\n        )\n    }\n\n    override suspend fun finishAccountDeletionRecentAuthenticationOidc(\n        accessToken: String,\n        connectionId: String,\n        code: String,\n        state: String,\n    ) {\n        val encodedConnection = java.net.URLEncoder\n            .encode(connectionId, Charsets.UTF_8.name())\n            .replace("+", "%20")\n        val body = buildJsonObject {\n            put("code", JsonPrimitive(code))\n            put("state", JsonPrimitive(state))\n        }\n        executeEmpty(\n            authenticatedRequest(\n                "$baseUrl/api/v1/auth/recent-authentication/account-deletion/oidc/$encodedConnection/callback",\n                accessToken,\n            ).post(body.toString().toRequestBody(jsonMediaType)).build(),\n        )\n    }\n\n''',
)

# ---------------------------------------------------------------------------
# ViewModel: session/token stay here. Platform UI receives only request options
# or authorization URL/state, never the bearer or a step-up credential.
# ---------------------------------------------------------------------------
view_model = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceViewModel.kt"
replace_once(
    view_model,
    "    val accountDeletionBusy: Boolean = false,\n"
    "    val accountDeletionProblem: UiProblem? = null,\n",
    "    val accountDeletionBusy: Boolean = false,\n"
    "    val accountDeletionProblem: UiProblem? = null,\n"
    "    val accountDeletionRecentAuthenticationCapabilities: AccountDeletionRecentAuthenticationCapabilities? = null,\n"
    "    val accountDeletionRecentAuthenticationBusy: Boolean = false,\n"
    "    val accountDeletionRecentAuthenticationProblem: UiProblem? = null,\n"
    "    val accountDeletionRecentAuthenticationComplete: Boolean = false,\n"
    "    val accountDeletionPasskeyRequest: String? = null,\n"
    "    val accountDeletionOidcPending: AccountDeletionOidcPending? = null,\n",
)
insert_before(
    view_model,
    "    fun deleteOwnAccount() {\n",
    '''    fun resetAccountDeletionRecentAuthentication() {\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationCapabilities = null,\n                accountDeletionRecentAuthenticationBusy = false,\n                accountDeletionRecentAuthenticationProblem = null,\n                accountDeletionRecentAuthenticationComplete = false,\n                accountDeletionPasskeyRequest = null,\n                accountDeletionOidcPending = null,\n            )\n        }\n    }\n\n    fun loadAccountDeletionRecentAuthentication() {\n        val api = contract as? AccountDeletionRecentAuthenticationContract ?: return configurationError()\n        val currentSession = session ?: return\n        val operationEpoch = sessionEpoch\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = true,\n                accountDeletionRecentAuthenticationProblem = null,\n                accountDeletionRecentAuthenticationComplete = false,\n            )\n        }\n        viewModelScope.launch {\n            runCatching {\n                api.accountDeletionRecentAuthenticationCapabilities(currentSession.tokens.accessToken)\n            }.onSuccess { capabilities ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess\n                mutate {\n                    it.copy(\n                        accountDeletionRecentAuthenticationCapabilities = capabilities,\n                        accountDeletionRecentAuthenticationBusy = false,\n                    )\n                }\n            }.onFailure { throwable ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure\n                failAccountDeletionRecentAuthentication(throwable)\n            }\n        }\n    }\n\n    fun authenticateAccountDeletionPassword(password: String) {\n        val api = contract as? AccountDeletionRecentAuthenticationContract ?: return configurationError()\n        val currentSession = session ?: return\n        val operationEpoch = sessionEpoch\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = true,\n                accountDeletionRecentAuthenticationProblem = null,\n            )\n        }\n        viewModelScope.launch {\n            runCatching {\n                api.accountDeletionRecentAuthenticationPassword(currentSession.tokens.accessToken, password)\n            }.onSuccess {\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess\n                mutate {\n                    it.copy(\n                        accountDeletionRecentAuthenticationBusy = false,\n                        accountDeletionRecentAuthenticationComplete = true,\n                    )\n                }\n            }.onFailure { throwable ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure\n                failAccountDeletionRecentAuthentication(throwable)\n            }\n        }\n    }\n\n    fun startAccountDeletionPasskey() {\n        val api = contract as? AccountDeletionRecentAuthenticationContract ?: return configurationError()\n        val currentSession = session ?: return\n        val operationEpoch = sessionEpoch\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = true,\n                accountDeletionRecentAuthenticationProblem = null,\n                accountDeletionPasskeyRequest = null,\n            )\n        }\n        viewModelScope.launch {\n            runCatching {\n                api.startAccountDeletionRecentAuthenticationPasskey(currentSession.tokens.accessToken)\n            }.onSuccess { requestJson ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess\n                mutate {\n                    it.copy(\n                        accountDeletionRecentAuthenticationBusy = false,\n                        accountDeletionPasskeyRequest = requestJson,\n                    )\n                }\n            }.onFailure { throwable ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure\n                failAccountDeletionRecentAuthentication(throwable)\n            }\n        }\n    }\n\n    fun finishAccountDeletionPasskey(authenticationResponseJson: String) {\n        val api = contract as? AccountDeletionRecentAuthenticationContract ?: return configurationError()\n        val currentSession = session ?: return\n        val operationEpoch = sessionEpoch\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = true,\n                accountDeletionRecentAuthenticationProblem = null,\n                accountDeletionPasskeyRequest = null,\n            )\n        }\n        viewModelScope.launch {\n            runCatching {\n                api.finishAccountDeletionRecentAuthenticationPasskey(\n                    currentSession.tokens.accessToken,\n                    authenticationResponseJson,\n                )\n            }.onSuccess {\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess\n                mutate {\n                    it.copy(\n                        accountDeletionRecentAuthenticationBusy = false,\n                        accountDeletionRecentAuthenticationComplete = true,\n                    )\n                }\n            }.onFailure { throwable ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure\n                failAccountDeletionRecentAuthentication(throwable)\n            }\n        }\n    }\n\n    fun startAccountDeletionOidc(connectionId: String) {\n        val api = contract as? AccountDeletionRecentAuthenticationContract ?: return configurationError()\n        val currentSession = session ?: return\n        val operationEpoch = sessionEpoch\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = true,\n                accountDeletionRecentAuthenticationProblem = null,\n                accountDeletionOidcPending = null,\n            )\n        }\n        viewModelScope.launch {\n            runCatching {\n                api.startAccountDeletionRecentAuthenticationOidc(\n                    currentSession.tokens.accessToken,\n                    connectionId,\n                )\n            }.onSuccess { started ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess\n                mutate {\n                    it.copy(\n                        accountDeletionRecentAuthenticationBusy = false,\n                        accountDeletionOidcPending = AccountDeletionOidcPending(\n                            connectionId = connectionId,\n                            authorizationUrl = started.authorizationUrl,\n                            state = started.state,\n                        ),\n                    )\n                }\n            }.onFailure { throwable ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure\n                failAccountDeletionRecentAuthentication(throwable)\n            }\n        }\n    }\n\n    fun finishAccountDeletionOidc(code: String, state: String) {\n        val pending = _uiState.value.accountDeletionOidcPending ?: return\n        if (pending.state != state) {\n            failAccountDeletionRecentAuthentication(IllegalArgumentException("OIDC state mismatch"))\n            return\n        }\n        val api = contract as? AccountDeletionRecentAuthenticationContract ?: return configurationError()\n        val currentSession = session ?: return\n        val operationEpoch = sessionEpoch\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = true,\n                accountDeletionRecentAuthenticationProblem = null,\n            )\n        }\n        viewModelScope.launch {\n            runCatching {\n                api.finishAccountDeletionRecentAuthenticationOidc(\n                    currentSession.tokens.accessToken,\n                    pending.connectionId,\n                    code,\n                    state,\n                )\n            }.onSuccess {\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess\n                mutate {\n                    it.copy(\n                        accountDeletionRecentAuthenticationBusy = false,\n                        accountDeletionRecentAuthenticationComplete = true,\n                        accountDeletionOidcPending = null,\n                    )\n                }\n            }.onFailure { throwable ->\n                if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure\n                failAccountDeletionRecentAuthentication(throwable)\n            }\n        }\n    }\n\n    fun failAccountDeletionRecentAuthentication(throwable: Throwable) {\n        mutate {\n            it.copy(\n                accountDeletionRecentAuthenticationBusy = false,\n                accountDeletionRecentAuthenticationProblem = problemFor(throwable),\n                accountDeletionPasskeyRequest = null,\n                accountDeletionOidcPending = null,\n            )\n        }\n    }\n\n''',
)

# ---------------------------------------------------------------------------
# Android platform bridge.
# ---------------------------------------------------------------------------
gradle = "android/app/build.gradle.kts"
replace_once(
    gradle,
    '    implementation("androidx.navigation:navigation-compose:2.10.0")\n',
    '    implementation("androidx.navigation:navigation-compose:2.10.0")\n'
    '    implementation("androidx.credentials:credentials:1.6.0")\n',
)

manifest = "android/app/src/main/AndroidManifest.xml"
replace_once(
    manifest,
    '        <activity\n            android:name=".MainActivity"\n            android:exported="true">\n',
    '        <activity\n            android:name=".MainActivity"\n            android:exported="true"\n'
    '            android:launchMode="singleTop">\n',
)
replace_once(
    manifest,
    '                <category android:name="android.intent.category.LAUNCHER" />\n'
    '            </intent-filter>\n',
    '                <category android:name="android.intent.category.LAUNCHER" />\n'
    '            </intent-filter>\n'
    '            <intent-filter>\n'
    '                <action android:name="android.intent.action.VIEW" />\n'
    '                <category android:name="android.intent.category.DEFAULT" />\n'
    '                <category android:name="android.intent.category.BROWSABLE" />\n'
    '                <data\n'
    '                    android:scheme="de.sidebyside.app"\n'
    '                    android:host="recent-authentication"\n'
    '                    android:path="/oidc" />\n'
    '            </intent-filter>\n',
)

strings = "android/app/src/main/res/values/strings.xml"
insert_before(
    strings,
    '    <string name="account_delete_confirmation_title">',
    '    <string name="account_delete_reauth_title">Identität bestätigen</string>\n'
    '    <string name="account_delete_reauth_intro">Bestätige deine Identität erneut. Welche Methode verfügbar ist, entscheidet der Server für dieses Konto und diese Sitzung.</string>\n'
    '    <string name="account_delete_reauth_loading">Verfügbare Anmeldemethoden werden geladen …</string>\n'
    '    <string name="account_delete_reauth_password_label">Aktuelles Passwort</string>\n'
    '    <string name="account_delete_reauth_password_action">Mit Passwort bestätigen</string>\n'
    '    <string name="account_delete_reauth_passkey_action">Mit Passkey bestätigen</string>\n'
    '    <string name="account_delete_reauth_oidc_action">Mit %1$s erneut anmelden</string>\n'
    '    <string name="account_delete_reauth_unavailable">Für dieses Konto ist auf Android aktuell keine Methode zur erneuten Identitätsbestätigung verfügbar. Die Kontolöschung bleibt gesperrt.</string>\n'
    '    <string name="account_delete_reauth_pending">Identität wird bestätigt …</string>\n',
)

activity = "android/app/src/main/java/de/sidebyside/next/reference/MainActivity.kt"
replace_once(
    activity,
    "import android.content.Context\n",
    "import android.content.Context\nimport android.content.Intent\nimport android.net.Uri\n",
)
replace_once(
    activity,
    "import androidx.activity.result.contract.ActivityResultContracts\n",
    "import androidx.activity.result.contract.ActivityResultContracts\n"
    "import androidx.credentials.CredentialManager\n"
    "import androidx.credentials.GetCredentialRequest\n"
    "import androidx.credentials.GetPublicKeyCredentialOption\n"
    "import androidx.credentials.PublicKeyCredential\n",
)
replace_once(
    activity,
    "class MainActivity : ComponentActivity() {\n"
    "    override fun onCreate(savedInstanceState: Bundle?) {\n",
    "class MainActivity : ComponentActivity() {\n"
    "    private val oidcCallback = mutableStateOf<Uri?>(null)\n\n"
    "    override fun onCreate(savedInstanceState: Bundle?) {\n",
)
replace_once(
    activity,
    "        super.onCreate(savedInstanceState)\n"
    "        setContent {\n"
    "            SideBySideTheme {\n"
    "                ReferenceFlowRoute()\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "}\n",
    "        super.onCreate(savedInstanceState)\n"
    "        oidcCallback.value = intent?.data?.takeIf(::isRecentAuthenticationOidcCallback)\n"
    "        setContent {\n"
    "            SideBySideTheme {\n"
    "                ReferenceFlowRoute(\n"
    "                    oidcCallback = oidcCallback.value,\n"
    "                    onOidcCallbackConsumed = { oidcCallback.value = null },\n"
    "                )\n"
    "            }\n"
    "        }\n"
    "    }\n\n"
    "    override fun onNewIntent(intent: Intent) {\n"
    "        super.onNewIntent(intent)\n"
    "        setIntent(intent)\n"
    "        oidcCallback.value = intent.data?.takeIf(::isRecentAuthenticationOidcCallback)\n"
    "    }\n\n"
    "    private fun isRecentAuthenticationOidcCallback(uri: Uri): Boolean =\n"
    "        uri.scheme == \"de.sidebyside.app\" &&\n"
    "            uri.host == \"recent-authentication\" &&\n"
    "            uri.path == \"/oidc\"\n"
    "}\n",
)
replace_once(
    activity,
    "private fun ReferenceFlowRoute(\n"
    "    referenceViewModel: ReferenceViewModel = viewModel(factory = referenceViewModelFactory(LocalContext.current)),\n"
    ") {\n",
    "private fun ReferenceFlowRoute(\n"
    "    oidcCallback: Uri? = null,\n"
    "    onOidcCallbackConsumed: () -> Unit = {},\n"
    "    referenceViewModel: ReferenceViewModel = viewModel(factory = referenceViewModelFactory(LocalContext.current)),\n"
    ") {\n",
)
replace_once(
    activity,
    "    val context = LocalContext.current\n"
    "    val scope = rememberCoroutineScope()\n",
    "    val context = LocalContext.current\n"
    "    val scope = rememberCoroutineScope()\n"
    "    val credentialManager = remember(context) { CredentialManager.create(context) }\n",
)
insert_before(
    activity,
    "    val signOut = {\n",
    '''    LaunchedEffect(state.accountDeletionPasskeyRequest) {\n        val requestJson = state.accountDeletionPasskeyRequest ?: return@LaunchedEffect\n        runCatching {\n            val result = credentialManager.getCredential(\n                context = context,\n                request = GetCredentialRequest(\n                    credentialOptions = listOf(\n                        GetPublicKeyCredentialOption(requestJson = requestJson),\n                    ),\n                ),\n            )\n            val credential = result.credential as? PublicKeyCredential\n                ?: error("Credential Manager returned a non-passkey credential")\n            credential.authenticationResponseJson\n        }.onSuccess(referenceViewModel::finishAccountDeletionPasskey)\n            .onFailure(referenceViewModel::failAccountDeletionRecentAuthentication)\n    }\n\n    LaunchedEffect(state.accountDeletionOidcPending?.authorizationUrl) {\n        state.accountDeletionOidcPending?.authorizationUrl?.let { authorizationUrl ->\n            runCatching {\n                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(authorizationUrl)))\n            }.onFailure(referenceViewModel::failAccountDeletionRecentAuthentication)\n        }\n    }\n\n    LaunchedEffect(oidcCallback) {\n        val callback = oidcCallback ?: return@LaunchedEffect\n        val code = callback.getQueryParameter("code")\n        val stateParameter = callback.getQueryParameter("state")\n        if (code != null && stateParameter != null) {\n            referenceViewModel.finishAccountDeletionOidc(code, stateParameter)\n        } else {\n            referenceViewModel.failAccountDeletionRecentAuthentication(\n                IllegalArgumentException("OIDC recent authentication did not return code and state"),\n            )\n        }\n        onOidcCallbackConsumed()\n    }\n\n''',
)
replace_once(
    activity,
    "                            AccountSettingsContent(\n"
    "                                demoMode = state.demoMode,\n"
    "                                busy = state.accountDeletionBusy,\n"
    "                                problem = state.accountDeletionProblem,\n"
    "                                onOpenDataExport = { navController.navigate(DATA_EXPORT_ROUTE) },\n"
    "                                onDeleteAccount = viewModel::deleteOwnAccount,\n"
    "                            )\n",
    "                            AccountSettingsContent(\n"
    "                                demoMode = state.demoMode,\n"
    "                                busy = state.accountDeletionBusy,\n"
    "                                problem = state.accountDeletionProblem,\n"
    "                                recentAuthenticationCapabilities =\n"
    "                                    state.accountDeletionRecentAuthenticationCapabilities,\n"
    "                                recentAuthenticationBusy = state.accountDeletionRecentAuthenticationBusy,\n"
    "                                recentAuthenticationProblem = state.accountDeletionRecentAuthenticationProblem,\n"
    "                                recentAuthenticationComplete = state.accountDeletionRecentAuthenticationComplete,\n"
    "                                onLoadRecentAuthentication = viewModel::loadAccountDeletionRecentAuthentication,\n"
    "                                onRecentAuthenticationPassword = viewModel::authenticateAccountDeletionPassword,\n"
    "                                onRecentAuthenticationPasskey = viewModel::startAccountDeletionPasskey,\n"
    "                                onRecentAuthenticationOidc = viewModel::startAccountDeletionOidc,\n"
    "                                onResetRecentAuthentication = viewModel::resetAccountDeletionRecentAuthentication,\n"
    "                                onOpenDataExport = { navController.navigate(DATA_EXPORT_ROUTE) },\n"
    "                                onDeleteAccount = viewModel::deleteOwnAccount,\n"
    "                            )\n",
)
