package de.eimir.app.profile

import de.eimir.app.reference.UiMessage
import de.eimir.app.shell.UiProblem
import eimir.api.models.PartnerProfileView
import eimir.api.models.ProfilePreferenceView

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
