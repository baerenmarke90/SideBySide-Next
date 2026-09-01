package de.sidebyside.next.profile

import de.sidebyside.next.reference.ReferenceContract
import de.sidebyside.next.reference.SelectedImage
import de.sidebyside.next.reference.prepareAttachment
import java.util.UUID
import sidebyside.api.models.PartnerProfileView
import sidebyside.api.models.ProfileIdentityUpdate
import sidebyside.api.models.SessionView

/** Loads self + partner presentation identity without making avatar media public. */
suspend fun loadProfileIdentity(
    api: ReferenceContract,
    spaceId: UUID,
    session: SessionView,
): ProfileUiState {
    val accessToken = session.tokens.accessToken
    val selfId = session.account.id
    val space = api.getSpace(spaceId, accessToken)
    val self = api.getProfile(spaceId, accessToken, selfId)
    val partnerId = space.partners.firstOrNull { it.id != selfId }?.id
    val partner = partnerId?.let { api.getProfile(spaceId, accessToken, it) }

    val selfAvatar = self.profileAttachmentId?.let {
        runCatching { api.readProfileAvatar(spaceId, accessToken, selfId) }.getOrNull()
    }
    val partnerAvatar = partner?.profileAttachmentId?.let {
        runCatching { api.readProfileAvatar(spaceId, accessToken, partner.accountId) }.getOrNull()
    }

    return ProfileUiState(
        self = self,
        partner = partner,
        selfAvatarBytes = selfAvatar,
        partnerAvatarBytes = partnerAvatar,
    )
}

suspend fun updateProfileDisplayName(
    api: ReferenceContract,
    spaceId: UUID,
    session: SessionView,
    current: PartnerProfileView,
    displayName: String,
): PartnerProfileView = api.updateProfileIdentity(
    spaceId = spaceId,
    accessToken = session.tokens.accessToken,
    accountId = session.account.id,
    ifMatch = current.version,
    update = ProfileIdentityUpdate(displayName = displayName.trim()),
)

suspend fun updateProfileAvatar(
    api: ReferenceContract,
    spaceId: UUID,
    session: SessionView,
    current: PartnerProfileView,
    image: SelectedImage,
): PartnerProfileView {
    val accessToken = session.tokens.accessToken
    val prepared = prepareAttachment(
        api = api,
        spaceId = spaceId,
        accessToken = accessToken,
        image = image,
    )
    return try {
        api.updateProfileIdentity(
            spaceId = spaceId,
            accessToken = accessToken,
            accountId = session.account.id,
            ifMatch = current.version,
            update = ProfileIdentityUpdate(profileAttachmentId = prepared.attachmentId),
        )
    } catch (failure: Throwable) {
        runCatching {
            val attachment = api.getAttachment(spaceId, accessToken, prepared.attachmentId)
            api.deleteAttachment(
                spaceId = spaceId,
                accessToken = accessToken,
                attachmentId = prepared.attachmentId,
                ifMatch = attachment.version,
            )
        }
        throw failure
    }
}

suspend fun removeProfileAvatar(
    api: ReferenceContract,
    spaceId: UUID,
    session: SessionView,
    current: PartnerProfileView,
): PartnerProfileView = api.removeProfileAvatar(
    spaceId = spaceId,
    accessToken = session.tokens.accessToken,
    accountId = session.account.id,
    ifMatch = current.version,
)
