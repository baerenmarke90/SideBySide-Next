package de.sidebyside.next.profile

import de.sidebyside.next.reference.UiMessage
import sidebyside.api.models.PartnerProfileView

data class ProfileUiState(
    val self: PartnerProfileView? = null,
    val partner: PartnerProfileView? = null,
    val selfAvatarBytes: ByteArray? = null,
    val partnerAvatarBytes: ByteArray? = null,
    val loading: Boolean = false,
    val busy: Boolean = false,
    val status: UiMessage? = null,
    val error: UiMessage? = null,
)
