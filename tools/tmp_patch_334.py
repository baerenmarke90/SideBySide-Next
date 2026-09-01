from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Expected exactly one match in {path}, found {count}: {old[:80]!r}"
        )
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


Path("web/src/client/instanceStatus.ts").write_text(
    """import { InstanceApi } from '../api/generated/apis/InstanceApi';
import type { InstanceAccessStatus } from '../api/generated/models/InstanceAccessStatus';
import { Configuration } from '../api/generated/runtime';

export type RegistrationAvailability =
  | 'available'
  | 'administrator'
  | 'maintenance'
  | 'unreachable';

export function classifyRegistrationAvailability(
  status: InstanceAccessStatus,
): RegistrationAvailability {
  if (
    status.maintenanceMode ||
    status.registrationUnavailableReason === 'maintenance'
  ) {
    return 'maintenance';
  }
  if (status.registrationAvailable) return 'available';
  if (status.registrationUnavailableReason === 'administrator') {
    return 'administrator';
  }
  return 'unreachable';
}

export async function loadRegistrationAvailability(
  apiBaseUrl: string,
  loadStatus?: () => Promise<InstanceAccessStatus>,
): Promise<RegistrationAvailability> {
  try {
    const operation =
      loadStatus ??
      (() =>
        new InstanceApi(
          new Configuration({ basePath: apiBaseUrl }),
        ).instanceStatusApiV1InstanceStatusGet());
    return classifyRegistrationAvailability(await operation());
  } catch {
    return 'unreachable';
  }
}
""",
    encoding="utf-8",
)

Path("web/src/client/instanceStatus.test.ts").write_text(
    """import {
  classifyRegistrationAvailability,
  loadRegistrationAvailability,
} from './instanceStatus';

describe('instance registration availability', () => {
  it('distinguishes available, administrator-disabled and maintenance states', () => {
    expect(
      classifyRegistrationAvailability({
        maintenanceMode: false,
        registrationAvailable: true,
        registrationUnavailableReason: null,
      }),
    ).toBe('available');
    expect(
      classifyRegistrationAvailability({
        maintenanceMode: false,
        registrationAvailable: false,
        registrationUnavailableReason: 'administrator',
      }),
    ).toBe('administrator');
    expect(
      classifyRegistrationAvailability({
        maintenanceMode: true,
        registrationAvailable: false,
        registrationUnavailableReason: 'maintenance',
      }),
    ).toBe('maintenance');
  });

  it('keeps connectivity failure distinct and fails closed for registration UI', async () => {
    await expect(
      loadRegistrationAvailability('https://sidebyside.invalid', async () => {
        throw new TypeError('network unavailable');
      }),
    ).resolves.toBe('unreachable');
  });
});
""",
    encoding="utf-8",
)

identity = "web/src/components/IdentityEntry.tsx"
replace_once(
    identity,
    "import type { SensitiveEntryToken } from '../client/entryToken';\n",
    "import type { SensitiveEntryToken } from '../client/entryToken';\nimport {\n  loadRegistrationAvailability,\n  type RegistrationAvailability,\n} from '../client/instanceStatus';\n",
)
replace_once(
    identity,
    "type EntryMode = 'signIn' | 'register' | 'recoveryRequest' | 'magicLinkRequest';\n",
    "type EntryMode = 'signIn' | 'register' | 'recoveryRequest' | 'magicLinkRequest';\ntype RegistrationUiState = 'checking' | RegistrationAvailability;\ntype RegistrationNoticeState = Exclude<RegistrationUiState, 'available'>;\n",
)
replace_once(
    identity,
    "  const recoveryToken =\n    entryToken?.kind === 'recovery' ? entryToken.token : null;\n  const [mode, setMode] = useState<EntryMode>('signIn');\n",
    "  const recoveryToken =\n    entryToken?.kind === 'recovery' ? entryToken.token : null;\n  const [registrationAvailability, setRegistrationAvailability] =\n    useState<RegistrationUiState>('checking');\n  const [mode, setMode] = useState<EntryMode>('signIn');\n",
)
replace_once(
    identity,
    "  useEffect(() => {\n    if (!entryToken || processedEntryToken.current === entryToken.token) return;\n",
    "  useEffect(() => {\n    if (!invitationToken) {\n      setRegistrationAvailability('available');\n      return;\n    }\n\n    let cancelled = false;\n    setRegistrationAvailability('checking');\n    void loadRegistrationAvailability(apiBaseUrl).then((availability) => {\n      if (!cancelled) setRegistrationAvailability(availability);\n    });\n    return () => {\n      cancelled = true;\n    };\n  }, [apiBaseUrl, invitationToken]);\n\n  useEffect(() => {\n    if (mode === 'register' && registrationAvailability !== 'available') {\n      setMode('signIn');\n    }\n  }, [mode, registrationAvailability]);\n\n  useEffect(() => {\n    if (!entryToken || processedEntryToken.current === entryToken.token) return;\n",
)
replace_once(
    identity,
    "  function submitRegistration(event: FormEvent<HTMLFormElement>) {\n    event.preventDefault();\n    const data = new FormData(event.currentTarget);\n",
    "  function submitRegistration(event: FormEvent<HTMLFormElement>) {\n    event.preventDefault();\n    if (registrationAvailability !== 'available') {\n      setValidationError(t('identity.registrationUnavailable'));\n      return;\n    }\n    const data = new FormData(event.currentTarget);\n",
)
replace_once(
    identity,
    "          ) : mode === 'register' && invitationToken ? (\n",
    "          ) : mode === 'register' &&\n            invitationToken &&\n            registrationAvailability === 'available' ? (\n",
)
replace_once(
    identity,
    "                  {invitationToken\n                    ? t('identity.invitationBody')\n                    : t('login.body')}\n",
    "                  {invitationToken\n                    ? registrationAvailability === 'available'\n                      ? t('identity.invitationBody')\n                      : t('identity.invitationExistingAccountBody')\n                    : t('login.body')}\n",
)
replace_once(
    identity,
    "              </div>\n              <form onSubmit={submitSignIn} className=\"form-grid login-form\">\n",
    "              </div>\n              {invitationToken && registrationAvailability !== 'available' ? (\n                <div className=\"inline-message\" role=\"status\">\n                  <strong>\n                    {t(registrationAvailabilityTitleKey(registrationAvailability))}\n                  </strong>\n                  <span>\n                    {t(registrationAvailabilityBodyKey(registrationAvailability))}\n                  </span>\n                </div>\n              ) : null}\n              <form onSubmit={submitSignIn} className=\"form-grid login-form\">\n",
)
replace_once(
    identity,
    "                {invitationToken ? (\n                  <button\n                    type=\"button\"\n                    className=\"secondary\"\n                    onClick={() => switchMode('register')}\n                  >\n                    {t('identity.createAccount')}\n                  </button>\n                ) : (\n",
    "                {invitationToken ? (\n                  registrationAvailability === 'available' ? (\n                    <button\n                      type=\"button\"\n                      className=\"secondary\"\n                      onClick={() => switchMode('register')}\n                    >\n                      {t('identity.createAccount')}\n                    </button>\n                  ) : null\n                ) : (\n",
)
replace_once(
    identity,
    "function EmailField() {\n",
    "function registrationAvailabilityTitleKey(\n  state: RegistrationNoticeState,\n):\n  | 'identity.registrationCheckingTitle'\n  | 'identity.registrationDisabledTitle'\n  | 'identity.maintenanceTitle'\n  | 'identity.registrationStatusUnavailableTitle' {\n  switch (state) {\n    case 'checking':\n      return 'identity.registrationCheckingTitle';\n    case 'administrator':\n      return 'identity.registrationDisabledTitle';\n    case 'maintenance':\n      return 'identity.maintenanceTitle';\n    case 'unreachable':\n      return 'identity.registrationStatusUnavailableTitle';\n  }\n}\n\nfunction registrationAvailabilityBodyKey(\n  state: RegistrationNoticeState,\n):\n  | 'identity.registrationCheckingBody'\n  | 'identity.registrationDisabledBody'\n  | 'identity.maintenanceBody'\n  | 'identity.registrationStatusUnavailableBody' {\n  switch (state) {\n    case 'checking':\n      return 'identity.registrationCheckingBody';\n    case 'administrator':\n      return 'identity.registrationDisabledBody';\n    case 'maintenance':\n      return 'identity.maintenanceBody';\n    case 'unreachable':\n      return 'identity.registrationStatusUnavailableBody';\n  }\n}\n\nfunction EmailField() {\n",
)

replace_once(
    "web/src/i18n/locales/de.ts",
    "    invitationBody:\n      'Melde dich mit deinem bestehenden Konto an oder erstelle über diese Einladung ein neues Konto.',\n    createAccount: 'Neues Konto erstellen',\n",
    "    invitationBody:\n      'Melde dich mit deinem bestehenden Konto an oder erstelle über diese Einladung ein neues Konto.',\n    invitationExistingAccountBody:\n      'Melde dich mit deinem bestehenden Konto an, um diese Einladung anzunehmen.',\n    createAccount: 'Neues Konto erstellen',\n    registrationCheckingTitle: 'Registrierung wird geprüft',\n    registrationCheckingBody:\n      'Die Anmeldung mit einem bestehenden Konto bleibt verfügbar. Ob ein neues Konto erstellt werden kann, wird gerade geprüft.',\n    registrationDisabledTitle: 'Neue Konten sind deaktiviert',\n    registrationDisabledBody:\n      'Der ServerAdmin hat neue Registrierungen deaktiviert. Bestehende Konten können sich weiterhin anmelden.',\n    maintenanceTitle: 'Wartungsmodus ist aktiv',\n    maintenanceBody:\n      'Während der Wartung werden keine neuen Konten erstellt. Bestehende Konten und der ServerAdmin-Zugang bleiben erreichbar.',\n    registrationStatusUnavailableTitle: 'Registrierungsstatus nicht erreichbar',\n    registrationStatusUnavailableBody:\n      'Der Serverstatus konnte nicht geprüft werden. Deshalb wird keine neue Registrierung angeboten; die Anmeldung mit einem bestehenden Konto kann weiterhin versucht werden.',\n    registrationUnavailable:\n      'Ein neues Konto kann derzeit nicht erstellt werden. Bitte nutze ein bestehendes Konto oder versuche es später erneut.',\n",
)

contract = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceContract.kt"
replace_once(
    contract,
    "import sidebyside.api.models.HeartMomentVisibilityChange\n",
    "import sidebyside.api.models.HeartMomentVisibilityChange\nimport sidebyside.api.models.InstanceAccessStatus\n",
)
replace_once(
    contract,
    "interface ReferenceContract {\n    suspend fun signIn(email: String, password: String): SessionView\n",
    "interface ReferenceContract {\n    suspend fun getInstanceStatus(): InstanceAccessStatus\n\n    suspend fun signIn(email: String, password: String): SessionView\n",
)

fake = "android/app/src/test/java/de/sidebyside/next/reference/FakeReferenceContract.kt"
replace_once(
    fake,
    "import sidebyside.api.models.HeartMomentVisibilityChange\n",
    "import sidebyside.api.models.HeartMomentVisibilityChange\nimport sidebyside.api.models.InstanceAccessStatus\n",
)
replace_once(
    fake,
    "abstract class FakeReferenceContract : ReferenceContract {\n    override suspend fun signIn(email: String, password: String): SessionView =\n",
    "abstract class FakeReferenceContract : ReferenceContract {\n    override suspend fun getInstanceStatus(): InstanceAccessStatus =\n        InstanceAccessStatus(\n            maintenanceMode = false,\n            registrationAvailable = true,\n            registrationUnavailableReason = null,\n        )\n\n    override suspend fun signIn(email: String, password: String): SessionView =\n",
)

okhttp = "android/app/src/main/java/de/sidebyside/next/reference/OkHttpReferenceApi.kt"
replace_once(
    okhttp,
    "import sidebyside.api.models.HeartMomentVisibilityChange\n",
    "import sidebyside.api.models.HeartMomentVisibilityChange\nimport sidebyside.api.models.InstanceAccessStatus\n",
)
replace_once(
    okhttp,
    "    override suspend fun signIn(email: String, password: String): SessionView {\n",
    "    override suspend fun getInstanceStatus(): InstanceAccessStatus =\n        executeJson(\n            Request.Builder()\n                .url(\"$baseUrl/api/v1/instance/status\")\n                .get()\n                .build(),\n            InstanceAccessStatus.serializer(),\n        )\n\n    override suspend fun signIn(email: String, password: String): SessionView {\n",
)

view_model = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceViewModel.kt"
replace_once(
    view_model,
    "import sidebyside.api.models.HeartMomentVisibilityChange\n",
    "import sidebyside.api.models.HeartMomentVisibilityChange\nimport sidebyside.api.models.InstanceAccessStatus\n",
)
replace_once(
    view_model,
    "enum class DraftUploadState {\n    UPLOADING,\n    VALIDATING,\n    READY,\n    FAILED,\n}\n\ndata class DraftImageUiItem(\n",
    "enum class DraftUploadState {\n    UPLOADING,\n    VALIDATING,\n    READY,\n    FAILED,\n}\n\nenum class InstanceAvailability {\n    CHECKING,\n    AVAILABLE,\n    REGISTRATION_DISABLED,\n    MAINTENANCE,\n    UNREACHABLE,\n}\n\ninternal fun instanceAvailabilityOf(status: InstanceAccessStatus): InstanceAvailability = when {\n    status.maintenanceMode ||\n        status.registrationUnavailableReason == InstanceAccessStatus.RegistrationUnavailableReason.maintenance ->\n        InstanceAvailability.MAINTENANCE\n    status.registrationAvailable -> InstanceAvailability.AVAILABLE\n    status.registrationUnavailableReason == InstanceAccessStatus.RegistrationUnavailableReason.administrator ->\n        InstanceAvailability.REGISTRATION_DISABLED\n    else -> InstanceAvailability.UNREACHABLE\n}\n\ndata class DraftImageUiItem(\n",
)
replace_once(
    view_model,
    "data class ReferenceUiState(\n    val configured: Boolean = false,\n    val loggedIn: Boolean = false,\n",
    "data class ReferenceUiState(\n    val configured: Boolean = false,\n    val instanceAvailability: InstanceAvailability = InstanceAvailability.CHECKING,\n    val loggedIn: Boolean = false,\n",
)
replace_once(
    view_model,
    "    private val _uiState = MutableStateFlow(ReferenceUiState(configured = config.isConfigured))\n    val uiState: StateFlow<ReferenceUiState> = _uiState.asStateFlow()\n\n",
    "    private val _uiState = MutableStateFlow(ReferenceUiState(configured = config.isConfigured))\n    val uiState: StateFlow<ReferenceUiState> = _uiState.asStateFlow()\n\n    init {\n        if (config.isConfigured) refreshInstanceAvailability()\n    }\n\n    fun refreshInstanceAvailability() {\n        val api = contract ?: return\n        if (!config.isConfigured) return\n        mutate { it.copy(instanceAvailability = InstanceAvailability.CHECKING) }\n        viewModelScope.launch {\n            val availability = runCatching { api.getInstanceStatus() }\n                .fold(\n                    onSuccess = ::instanceAvailabilityOf,\n                    onFailure = { InstanceAvailability.UNREACHABLE },\n                )\n            mutate { it.copy(instanceAvailability = availability) }\n        }\n    }\n\n",
)
replace_once(
    view_model,
    "        _uiState.value = ReferenceUiState(\n            configured = config.isConfigured,\n            status = message(R.string.demo_left),\n        )\n    }\n",
    "        _uiState.value = ReferenceUiState(\n            configured = config.isConfigured,\n            status = message(R.string.demo_left),\n        )\n        refreshInstanceAvailability()\n    }\n",
)
replace_once(
    view_model,
    "        _uiState.value = ReferenceUiState(\n            configured = config.isConfigured,\n            status = message(R.string.ref_status_logged_out),\n        )\n    }\n",
    "        _uiState.value = ReferenceUiState(\n            configured = config.isConfigured,\n            status = message(R.string.ref_status_logged_out),\n        )\n        refreshInstanceAvailability()\n    }\n",
)

screen = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceFlowScreen.kt"
replace_once(
    screen,
    "    if (!state.loggedIn) {\n        EntryScreen(\n            onSignIn = onLogin,\n            busy = state.busy,\n            signInEnabled = state.configured,\n            notice = if (state.configured) null else stringResource(R.string.ref_not_configured),\n            onEnterDemo = onEnterDemo,\n            modifier = modifier.fillMaxSize(),\n        )\n        return\n    }\n",
    "    if (!state.loggedIn) {\n        val entryNotice = when {\n            !state.configured -> stringResource(R.string.ref_not_configured)\n            state.instanceAvailability == InstanceAvailability.MAINTENANCE ->\n                stringResource(R.string.ref_maintenance_mode)\n            state.instanceAvailability == InstanceAvailability.REGISTRATION_DISABLED ->\n                stringResource(R.string.ref_registration_disabled)\n            state.instanceAvailability == InstanceAvailability.UNREACHABLE ->\n                stringResource(R.string.ref_instance_status_unreachable)\n            else -> null\n        }\n        EntryScreen(\n            onSignIn = onLogin,\n            busy = state.busy,\n            signInEnabled = state.configured,\n            notice = entryNotice,\n            onEnterDemo = onEnterDemo,\n            modifier = modifier.fillMaxSize(),\n        )\n        return\n    }\n",
)

replace_once(
    "android/app/src/main/res/values/strings.xml",
    "    <string name=\"ref_not_configured\">Der M2-Referenzflow ist operatorseitig noch nicht konfiguriert.</string>\n",
    "    <string name=\"ref_not_configured\">Der M2-Referenzflow ist operatorseitig noch nicht konfiguriert.</string>\n    <string name=\"ref_maintenance_mode\">Wartungsmodus aktiv. Bestehende Konten können sich weiterhin anmelden; neue Konten werden derzeit nicht erstellt.</string>\n    <string name=\"ref_registration_disabled\">Neue Konten sind auf diesem Server deaktiviert. Bestehende Konten können sich weiterhin anmelden.</string>\n    <string name=\"ref_instance_status_unreachable\">Der Serverstatus konnte nicht geprüft werden. Die Anmeldung kann weiterhin versucht werden; eine neue Registrierung wird nicht angeboten.</string>\n",
)

test = "android/app/src/test/java/de/sidebyside/next/reference/ReferenceViewModelTest.kt"
replace_once(
    test,
    "import sidebyside.api.models.MemoryDetail\n",
    "import sidebyside.api.models.InstanceAccessStatus\nimport sidebyside.api.models.MemoryDetail\n",
)
replace_once(
    test,
    "import org.junit.Assert.assertNull\n",
    "import org.junit.Assert.assertNull\nimport org.junit.Assert.assertTrue\n",
)
replace_once(
    test,
    "    private fun session(): SessionView {\n",
    "    @Test\n    fun instanceStatusDistinguishesRegistrationPolicyAndMaintenance() = runTest(dispatcher) {\n        val disabled = ReferenceViewModel(\n            config = ReferenceConfig(apiBaseUrl = \"https://sidebyside.invalid\"),\n            api = instanceStatusApi(\n                InstanceAccessStatus(\n                    maintenanceMode = false,\n                    registrationAvailable = false,\n                    registrationUnavailableReason =\n                        InstanceAccessStatus.RegistrationUnavailableReason.administrator,\n                ),\n            ),\n        )\n        val maintenance = ReferenceViewModel(\n            config = ReferenceConfig(apiBaseUrl = \"https://sidebyside.invalid\"),\n            api = instanceStatusApi(\n                InstanceAccessStatus(\n                    maintenanceMode = true,\n                    registrationAvailable = false,\n                    registrationUnavailableReason =\n                        InstanceAccessStatus.RegistrationUnavailableReason.maintenance,\n                ),\n            ),\n        )\n        advanceUntilIdle()\n\n        assertEquals(\n            InstanceAvailability.REGISTRATION_DISABLED,\n            disabled.uiState.value.instanceAvailability,\n        )\n        assertEquals(\n            InstanceAvailability.MAINTENANCE,\n            maintenance.uiState.value.instanceAvailability,\n        )\n        assertTrue(disabled.uiState.value.configured)\n        assertTrue(maintenance.uiState.value.configured)\n    }\n\n    @Test\n    fun instanceStatusKeepsConnectivityFailureDistinct() = runTest(dispatcher) {\n        val api = object : FakeReferenceContract() {\n            override suspend fun getInstanceStatus(): InstanceAccessStatus =\n                throw java.io.IOException(\"network unavailable\")\n        }\n        val viewModel = ReferenceViewModel(\n            config = ReferenceConfig(apiBaseUrl = \"https://sidebyside.invalid\"),\n            api = api,\n        )\n        advanceUntilIdle()\n\n        assertEquals(InstanceAvailability.UNREACHABLE, viewModel.uiState.value.instanceAvailability)\n        assertTrue(viewModel.uiState.value.configured)\n    }\n\n    private fun instanceStatusApi(status: InstanceAccessStatus): FakeReferenceContract =\n        object : FakeReferenceContract() {\n            override suspend fun getInstanceStatus(): InstanceAccessStatus = status\n        }\n\n    private fun session(): SessionView {\n",
)

replace_once(
    "docs/SERVER-ADMIN.md",
    "## Registration and maintenance controls\n\nRuntime registration policy and maintenance mode are owned by Issue #334. Their\npersistent state, public status semantics, privileged mutations, audit events,\nand recovery/lockout behavior must be implemented there and then surfaced by\nthe ServerAdmin dashboard. The dashboard must not introduce temporary\nclient-only switches or environment-only substitutes for those runtime\nsettings.\n",
    "## Registration and maintenance controls\n\nRegistration policy and maintenance mode are persisted as application state,\nnot deployment-environment feature flags. `registration_enabled` records the\noperator's registration policy; the effective registration state additionally\nrequires maintenance mode to be off. This keeps the stored operator choice\nintact when maintenance is entered and left.\n\nClients can read the minimal unauthenticated `GET /api/v1/instance/status`\nprojection. It exposes only maintenance state, effective registration\navailability, and the non-sensitive reason `administrator` or `maintenance`\nwhen registration is unavailable. Web and Android treat connectivity failure\nas a separate state and fail closed for advertising new-account creation.\n\nAn authenticated ServerAdmin can use:\n\n- `GET /api/v1/server-admin/settings`;\n- `PUT /api/v1/server-admin/settings/registration`;\n- `PUT /api/v1/server-admin/settings/maintenance`;\n- `GET /api/v1/server-admin/activity`.\n\nEach mutation is authorized server-side and records a narrow audit event with\nthe actor, setting name, previous/new boolean value, and timestamp. The audit\nrecord contains no product content, credentials, job payloads, or other private\ndata.\n\nMaintenance mode rejects ordinary product API traffic, while health,\nauthentication/recovery, public instance status, and ServerAdmin endpoints stay\nreachable. Background workers continue to run. This boundary deliberately\nlets an operator sign in and leave maintenance mode without requiring shell or\ndatabase access.\n\nDisabling registration blocks all supported new invited-account onboarding\npaths, including local-password and OIDC onboarding. Existing accounts can\nstill authenticate and accept invitations. Initial bootstrap remains an\nexplicit lockout-recovery exception so a fresh Self-Hosted instance cannot be\nmade permanently inaccessible before its first operator account exists.\n",
)
