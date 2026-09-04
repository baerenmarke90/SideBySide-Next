from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one match in {path}: {count}")
    file.write_text(text.replace(old, new, 1))


contract = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceContract.kt"
replace_once(
    contract,
    "import sidebyside.api.models.AccountMembershipView\n",
    "import sidebyside.api.models.AccountDeletionAccepted\n"
    "import sidebyside.api.models.AccountDeletionRequest\n"
    "import sidebyside.api.models.AccountMembershipView\n",
)
replace_once(
    contract,
    "    suspend fun listMemberships(accessToken: String): List<AccountMembershipView>\n\n",
    "    suspend fun listMemberships(accessToken: String): List<AccountMembershipView>\n\n"
    "    /** Deletes only the Account represented by [accessToken]. */\n"
    "    suspend fun deleteOwnAccount(\n"
    "        accessToken: String,\n"
    "        request: AccountDeletionRequest,\n"
    "    ): AccountDeletionAccepted\n\n",
)

okhttp = "android/app/src/main/java/de/sidebyside/next/reference/OkHttpReferenceApi.kt"
replace_once(
    okhttp,
    "import sidebyside.api.models.AccountMembershipView\n",
    "import sidebyside.api.models.AccountDeletionAccepted\n"
    "import sidebyside.api.models.AccountDeletionRequest\n"
    "import sidebyside.api.models.AccountMembershipView\n",
)
old_memberships = '''    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =
        executeJson(
            authenticatedRequest("$baseUrl/api/v1/auth/memberships", accessToken)
                .get()
                .build(),
            ListSerializer(AccountMembershipView.serializer()),
        )

'''
new_memberships = old_memberships + '''    override suspend fun deleteOwnAccount(
        accessToken: String,
        request: AccountDeletionRequest,
    ): AccountDeletionAccepted =
        executeJson(
            authenticatedRequest("$baseUrl/api/v1/account/deletion", accessToken)
                .post(
                    SideBySideJson
                        .encodeToString(AccountDeletionRequest.serializer(), request)
                        .toRequestBody(jsonMediaType),
                )
                .build(),
            AccountDeletionAccepted.serializer(),
        )

'''
replace_once(okhttp, old_memberships, new_memberships)

view_model = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceViewModel.kt"
replace_once(
    view_model,
    "import sidebyside.api.models.AccountMembershipView\n",
    "import sidebyside.api.models.AccountDeletionRequest\n"
    "import sidebyside.api.models.AccountMembershipView\n",
)
replace_once(
    view_model,
    "    val profile: ProfileUiState = ProfileUiState(),\n    val busy: Boolean = false,\n",
    "    val profile: ProfileUiState = ProfileUiState(),\n"
    "    val accountDeletionBusy: Boolean = false,\n"
    "    val accountDeletionProblem: UiProblem? = null,\n"
    "    val busy: Boolean = false,\n",
)
replace_once(
    view_model,
    "    fun logout() {\n",
    '''    fun deleteOwnAccount() {
        if (_uiState.value.demoMode) return
        val api = contract ?: return configurationError()
        val currentSession = session ?: return
        val operationEpoch = sessionEpoch

        mutate {
            it.copy(
                accountDeletionBusy = true,
                accountDeletionProblem = null,
            )
        }
        viewModelScope.launch {
            if (!isCurrentSession(operationEpoch, currentSession)) return@launch
            runCatching {
                api.deleteOwnAccount(
                    currentSession.tokens.accessToken,
                    AccountDeletionRequest(
                        confirmation = AccountDeletionRequest.Confirmation.DELETE_ACCOUNT,
                    ),
                )
            }
                .onSuccess {
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onSuccess
                    // The server has crossed the irreversible tombstone boundary and
                    // revoked this session. Reuse the existing logout transition to
                    // invalidate in-flight work, drafts, Room/protected caches and UI state.
                    logout()
                }
                .onFailure { throwable ->
                    if (!isCurrentSession(operationEpoch, currentSession)) return@onFailure
                    mutate {
                        it.copy(
                            accountDeletionBusy = false,
                            accountDeletionProblem = problemFor(throwable),
                        )
                    }
                }
        }
    }

    fun logout() {
''',
)

activity = "android/app/src/main/java/de/sidebyside/next/reference/MainActivity.kt"
replace_once(
    activity,
    "import de.sidebyside.next.demo.DemoBanner\n",
    "import de.sidebyside.next.account.AccountSettingsContent\n"
    "import de.sidebyside.next.demo.DemoBanner\n",
)
old_profile = '''                    profileContent = {
                        ProfileSettingsContent(
                            state = state.profile,
                            onRetry = viewModel::refreshProfile,
                            onSaveDisplayName = viewModel::saveProfileDisplayName,
                            onChooseAvatar = onPickProfileAvatar,
                            onRemoveAvatar = viewModel::removeProfileAvatar,
                        )
                    },
'''
new_profile = '''                    profileContent = {
                        Column(
                            verticalArrangement = Arrangement.spacedBy(
                                SideBySideTheme.spacing.step6,
                            ),
                        ) {
                            ProfileSettingsContent(
                                state = state.profile,
                                onRetry = viewModel::refreshProfile,
                                onSaveDisplayName = viewModel::saveProfileDisplayName,
                                onChooseAvatar = onPickProfileAvatar,
                                onRemoveAvatar = viewModel::removeProfileAvatar,
                            )
                            AccountSettingsContent(
                                demoMode = state.demoMode,
                                busy = state.accountDeletionBusy,
                                problem = state.accountDeletionProblem,
                                onOpenDataExport = { navController.navigate(DATA_EXPORT_ROUTE) },
                                onDeleteAccount = viewModel::deleteOwnAccount,
                            )
                        }
                    },
'''
replace_once(activity, old_profile, new_profile)

fake = "android/app/src/test/java/de/sidebyside/next/reference/FakeReferenceContract.kt"
replace_once(
    fake,
    "import sidebyside.api.models.AccountMembershipView\n",
    "import sidebyside.api.models.AccountDeletionAccepted\n"
    "import sidebyside.api.models.AccountDeletionRequest\n"
    "import sidebyside.api.models.AccountMembershipView\n",
)
replace_once(
    fake,
    '    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =\n        notExercised("listMemberships")\n\n',
    '    override suspend fun listMemberships(accessToken: String): List<AccountMembershipView> =\n'
    '        notExercised("listMemberships")\n\n'
    '    override suspend fun deleteOwnAccount(\n'
    '        accessToken: String,\n'
    '        request: AccountDeletionRequest,\n'
    '    ): AccountDeletionAccepted = notExercised("deleteOwnAccount")\n\n',
)
