package de.sidebyside.next.profile

import de.sidebyside.next.reference.UiMessage
import de.sidebyside.next.shell.UiProblem
import sidebyside.api.models.PartnerProfileView
import sidebyside.api.models.ProfilePreferenceView

data class ProfileUiState(
    val self: PartnerProfileView? = null,
    val partner: PartnerProfileView? = null,
    val selfAvatarBytes: ByteArray? = null,
    val partnerAvatarBytes: ByteArray? = null,
    val loading: Boolean = false,
    val busy: Boolean = false,
    val status: UiMessage? = null,
    val error: UiMessage? = null,
    /**
     * Every ProfilePreference visible to this account: SELF_PROFILE rows are
     * already embedded on [self] and [partner]; this flat list is read for
     * the PRIVATE_PARTNER_NOTE rows, which are not attached to either.
     */
    val preferences: List<ProfilePreferenceView> = emptyList(),
    val preferencesBusy: Boolean = false,
    val preferencesProblem: UiProblem? = null,
)
