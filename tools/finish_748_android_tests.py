from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# Mask the local password while the platform step-up UI is displayed.
content = "android/app/src/main/java/de/sidebyside/next/account/AccountSettingsContent.kt"
replace_once(
    content,
    "import androidx.compose.ui.semantics.semantics\n",
    "import androidx.compose.ui.semantics.semantics\n"
    "import androidx.compose.ui.text.input.PasswordVisualTransformation\n",
)
replace_once(
    content,
    "                singleLine = true,\n"
    "                enabled = !busy,\n"
    "                modifier = Modifier.fillMaxWidth(),\n"
    "            )\n"
    "            Button(\n"
    "                onClick = onPassword,\n",
    "                singleLine = true,\n"
    "                enabled = !busy,\n"
    "                visualTransformation = PasswordVisualTransformation(),\n"
    "                modifier = Modifier.fillMaxWidth(),\n"
    "            )\n"
    "            Button(\n"
    "                onClick = onPassword,\n",
)

# Update the Compose journey test. The final destructive confirmation must not
# exist until a server-authorized recent-authentication method succeeds.
test_path = "android/app/src/test/java/de/sidebyside/next/account/AccountSettingsContentTest.kt"
replace_once(
    test_path,
    "import androidx.compose.ui.test.performTextInput\n",
    "import androidx.compose.runtime.getValue\n"
    "import androidx.compose.runtime.mutableStateOf\n"
    "import androidx.compose.runtime.remember\n"
    "import androidx.compose.runtime.setValue\n"
    "import androidx.compose.ui.test.performTextInput\n",
)
replace_once(
    test_path,
    "import de.sidebyside.next.design.SideBySideTheme\n",
    "import de.sidebyside.next.design.SideBySideTheme\n"
    "import de.sidebyside.next.reference.AccountDeletionRecentAuthenticationCapabilities\n",
)
old_test = '''    @Test
    fun exactTypedConfirmationUnlocksTheFinalDestructiveAction() {
        var deletes = 0
        render(onDeleteAccount = { deletes += 1 })

        deletionAction().performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_continue))
            .performClick()

        val finalAction = composeRule.onNodeWithText(
            context.getString(R.string.account_delete_confirm_action),
        )
        finalAction.assertIsNotEnabled()

        composeRule.onNode(hasSetTextAction()).performTextInput("WRONG")
        finalAction.assertIsNotEnabled()

        composeRule.onNode(hasSetTextAction()).performTextClearance()
        composeRule.onNode(hasSetTextAction()).performTextInput(
            context.getString(R.string.account_delete_confirmation_phrase),
        )
        finalAction.performScrollTo().assertIsEnabled().performClick()

        assertEquals(1, deletes)
    }
'''
new_test = '''    @Test
    fun recentAuthenticationPrecedesExactTypedConfirmationAndDeletion() {
        var deletes = 0
        var passwordAttempts = 0
        render(
            onDeleteAccount = { deletes += 1 },
            onRecentAuthenticationPassword = {
                passwordAttempts += 1
                true
            },
        )

        deletionAction().performClick()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_continue))
            .performClick()

        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_reauth_title))
            .assertExists()
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_confirm_action))
            .assertDoesNotExist()

        composeRule.onNode(hasSetTextAction()).performTextInput("secret")
        composeRule
            .onNodeWithText(context.getString(R.string.account_delete_reauth_password_action))
            .performClick()
        composeRule.waitForIdle()
        assertEquals(1, passwordAttempts)

        val finalAction = composeRule.onNodeWithText(
            context.getString(R.string.account_delete_confirm_action),
        )
        finalAction.assertIsNotEnabled()

        composeRule.onNode(hasSetTextAction()).performTextInput("WRONG")
        finalAction.assertIsNotEnabled()

        composeRule.onNode(hasSetTextAction()).performTextClearance()
        composeRule.onNode(hasSetTextAction()).performTextInput(
            context.getString(R.string.account_delete_confirmation_phrase),
        )
        finalAction.performScrollTo().assertIsEnabled().performClick()

        assertEquals(1, deletes)
    }
'''
replace_once(test_path, old_test, new_test)
old_render = '''    private fun render(
        demoMode: Boolean = false,
        onOpenDataExport: () -> Unit = {},
        onDeleteAccount: () -> Unit = {},
    ) {
        composeRule.setContent {
            SideBySideTheme {
                AccountSettingsContent(
                    demoMode = demoMode,
                    busy = false,
                    problem = null,
                    onOpenDataExport = onOpenDataExport,
                    onDeleteAccount = onDeleteAccount,
                )
            }
        }
    }
'''
new_render = '''    private fun render(
        demoMode: Boolean = false,
        onOpenDataExport: () -> Unit = {},
        onDeleteAccount: () -> Unit = {},
        onRecentAuthenticationPassword: (String) -> Boolean = { true },
    ) {
        composeRule.setContent {
            var recentAuthenticationComplete by remember { mutableStateOf(false) }
            SideBySideTheme {
                AccountSettingsContent(
                    demoMode = demoMode,
                    busy = false,
                    problem = null,
                    recentAuthenticationCapabilities =
                        AccountDeletionRecentAuthenticationCapabilities(
                            localPassword = true,
                            passkey = false,
                            oidcConnections = emptyList(),
                        ),
                    recentAuthenticationBusy = false,
                    recentAuthenticationProblem = null,
                    recentAuthenticationComplete = recentAuthenticationComplete,
                    onLoadRecentAuthentication = {},
                    onRecentAuthenticationPassword = { password ->
                        recentAuthenticationComplete = onRecentAuthenticationPassword(password)
                    },
                    onRecentAuthenticationPasskey = {},
                    onRecentAuthenticationOidc = {},
                    onResetRecentAuthentication = { recentAuthenticationComplete = false },
                    onOpenDataExport = onOpenDataExport,
                    onDeleteAccount = onDeleteAccount,
                )
            }
        }
    }
'''
replace_once(test_path, old_render, new_render)

# Exercise ViewModel session binding for the password step-up. The fake only
# implements the narrow recent-authentication contract in addition to the
# existing ReferenceContract test surface.
vm_test = "android/app/src/test/java/de/sidebyside/next/reference/AccountDeletionTest.kt"
insert_anchor = '''    @Test
    fun rejectedDeletionKeepsTheSessionAndSurfacesTheProblem() = runTest(dispatcher) {
'''
new_vm_test = '''    @Test
    fun recentAuthenticationUsesTheCurrentSessionAndUnlocksOnlyAfterSuccess() =
        runTest(dispatcher) {
            val api = DeletionApi()
            val model = model(api)

            model.signIn("someone@example.test", "secret")
            advanceUntilIdle()

            model.loadAccountDeletionRecentAuthentication()
            advanceUntilIdle()
            assertTrue(model.uiState.value.accountDeletionRecentAuthenticationCapabilities?.localPassword == true)
            assertEquals(listOf("access"), api.recentAuthenticationCapabilityTokens)
            assertFalse(model.uiState.value.accountDeletionRecentAuthenticationComplete)

            model.authenticateAccountDeletionPassword("fresh-secret")
            advanceUntilIdle()

            assertEquals(listOf("access" to "fresh-secret"), api.recentAuthenticationPasswords)
            assertTrue(model.uiState.value.accountDeletionRecentAuthenticationComplete)
        }

'''
replace_once(vm_test, insert_anchor, new_vm_test + insert_anchor)
replace_once(
    vm_test,
    ") : FakeReferenceContract() {\n",
    ") : FakeReferenceContract(), AccountDeletionRecentAuthenticationContract {\n",
)
replace_once(
    vm_test,
    "    val deletionTokens = mutableListOf<String>()\n"
    "    val deletionRequests = mutableListOf<AccountDeletionRequest>()\n",
    "    val deletionTokens = mutableListOf<String>()\n"
    "    val deletionRequests = mutableListOf<AccountDeletionRequest>()\n"
    "    val recentAuthenticationCapabilityTokens = mutableListOf<String>()\n"
    "    val recentAuthenticationPasswords = mutableListOf<Pair<String, String>>()\n",
)
recent_methods = '''    override suspend fun accountDeletionRecentAuthenticationCapabilities(
        accessToken: String,
    ): AccountDeletionRecentAuthenticationCapabilities {
        recentAuthenticationCapabilityTokens += accessToken
        return AccountDeletionRecentAuthenticationCapabilities(
            localPassword = true,
            passkey = false,
            oidcConnections = emptyList(),
        )
    }

    override suspend fun accountDeletionRecentAuthenticationPassword(
        accessToken: String,
        password: String,
    ) {
        recentAuthenticationPasswords += accessToken to password
    }

    override suspend fun startAccountDeletionRecentAuthenticationPasskey(
        accessToken: String,
    ): String = error("not used")

    override suspend fun finishAccountDeletionRecentAuthenticationPasskey(
        accessToken: String,
        authenticationResponseJson: String,
    ) = error("not used")

    override suspend fun startAccountDeletionRecentAuthenticationOidc(
        accessToken: String,
        connectionId: String,
    ): AccountDeletionOidcStart = error("not used")

    override suspend fun finishAccountDeletionRecentAuthenticationOidc(
        accessToken: String,
        connectionId: String,
        code: String,
        state: String,
    ) = error("not used")

'''
replace_once(
    vm_test,
    "    override suspend fun deleteOwnAccount(\n",
    recent_methods + "    override suspend fun deleteOwnAccount(\n",
)
