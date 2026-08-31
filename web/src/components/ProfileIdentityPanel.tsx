import { type FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import type { ProfileIdentityUpdate } from '../api/generated/models/ProfileIdentityUpdate';
import { Configuration } from '../api/generated/runtime';
import {
  type DraftUploadPhase,
  uploadMemoryDraftAttachment,
} from '../client/memoryAttachmentDraft';
import { normalizeClientError } from '../client/problemDetails';
import { createReferenceApis } from '../client/referenceFlow';
import { useProfileAvatarUrl } from '../client/useProfileAvatarUrl';
import { useTranslation } from '../i18n';
import { PersonIdentity } from './PersonIdentity';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './ProfileIdentityPanel.css';

function uploadStatusKey(phase: DraftUploadPhase | null): string | null {
  if (phase === 'uploading') return 'profileIdentity.uploadUploading';
  if (phase === 'validating') return 'profileIdentity.uploadValidating';
  return null;
}

export function ProfileIdentityPanel({
  apiBaseUrl,
  accessToken,
  account,
  spaceId,
  onDisplayNameChanged,
}: {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
  onDisplayNameChanged: (displayName: string) => void;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [uploadPhase, setUploadPhase] = useState<DraftUploadPhase | null>(null);

  const configuration = useMemo(
    () =>
      new Configuration({
        basePath: apiBaseUrl,
        headers: { Authorization: `Bearer ${accessToken}` },
      }),
    [accessToken, apiBaseUrl],
  );
  const profilesApi = useMemo(() => new ProfilesApi(configuration), [configuration]);
  const referenceApis = useMemo(
    () => createReferenceApis(apiBaseUrl, accessToken),
    [accessToken, apiBaseUrl],
  );

  const profileQuery = useQuery({
    queryKey: ['profile-identity', spaceId, account.id],
    queryFn: async () => {
      try {
        return await profilesApi.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet({
          accountId: account.id,
          spaceId,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const { avatarUrl, loadFailed: avatarLoadFailed } = useProfileAvatarUrl(
    profilesApi,
    spaceId,
    account.id,
    profileQuery.data?.profileAttachmentId,
  );

  async function updateIdentity(body: ProfileIdentityUpdate) {
    if (!profileQuery.data) throw new Error(t('profiles.loading'));
    try {
      return await profilesApi.updateProfileIdentity({
        accountId: account.id,
        spaceId,
        ifMatch: String(profileQuery.data.version),
        profileIdentityUpdate: body,
      });
    } catch (error) {
      throw await normalizeClientError(error);
    }
  }

  async function acceptUpdatedProfile(profile: Awaited<ReturnType<typeof updateIdentity>>) {
    queryClient.setQueryData(['profile-identity', spaceId, account.id], profile);
    onDisplayNameChanged(profile.displayName);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['space', spaceId] }),
      queryClient.invalidateQueries({ queryKey: ['partner-profile', spaceId] }),
    ]);
    setSaved(true);
  }

  const displayNameMutation = useMutation({
    mutationFn: async (displayName: string) => updateIdentity({ displayName }),
    onSuccess: acceptUpdatedProfile,
  });

  const avatarMutation = useMutation({
    mutationFn: async (file: File) => {
      setUploadPhase('uploading');
      let readyAttachmentId: string | null = null;
      try {
        const ready = await uploadMemoryDraftAttachment(
          referenceApis,
          apiBaseUrl,
          accessToken,
          spaceId,
          file,
          setUploadPhase,
        );
        readyAttachmentId = ready.attachmentId;
        return await updateIdentity({ profileAttachmentId: ready.attachmentId });
      } catch (error) {
        if (readyAttachmentId) {
          try {
            const attachment = await referenceApis.attachments.getAttachment({
              spaceId,
              attachmentId: readyAttachmentId,
            });
            await referenceApis.attachments.deleteAttachment({
              spaceId,
              attachmentId: readyAttachmentId,
              ifMatch: String(attachment.version),
            });
          } catch {
            // Server-side orphan cleanup remains the fallback.
          }
        }
        throw error;
      } finally {
        setUploadPhase(null);
      }
    },
    onSuccess: acceptUpdatedProfile,
  });

  const removeAvatarMutation = useMutation({
    mutationFn: async () => updateIdentity({ profileAttachmentId: null }),
    onSuccess: acceptUpdatedProfile,
  });

  function submitDisplayName(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    const form = new FormData(event.currentTarget);
    displayNameMutation.mutate(String(form.get('displayName') ?? ''));
  }

  const profile = profileQuery.data;
  const visibleName = profile?.displayName ?? account.displayName;
  const pending =
    displayNameMutation.isPending || avatarMutation.isPending || removeAvatarMutation.isPending;
  const phaseKey = uploadStatusKey(uploadPhase);

  return (
    <section className="form-card profile-identity-panel" aria-labelledby="profile-identity-title">
      <div>
        <p className="eyebrow">{t('profiles.eyebrow')}</p>
        <h2 id="profile-identity-title">{t('profileIdentity.title')}</h2>
        <p>{t('profileIdentity.intro')}</p>
      </div>

      {profileQuery.isLoading ? <UiState kind="loading" title={t('profiles.loading')} /> : null}
      {profileQuery.error ? (
        <ProblemState error={profileQuery.error} onRetry={() => void profileQuery.refetch()} />
      ) : null}

      {profile ? (
        <>
          <div className="profile-identity-preview">
            <small>{t('profileIdentity.previewLabel')}</small>
            <PersonIdentity
              displayName={visibleName}
              imageUrl={avatarUrl}
              size="large"
              imageAlt={t('profileIdentity.imageAlt', { name: visibleName })}
              fallbackAlt={t('profileIdentity.fallbackAlt', { name: visibleName })}
            />
          </div>

          {avatarLoadFailed ? (
            <p className="field-help profile-identity-status" role="status">
              {t('profileIdentity.loadAvatarFailed')}
            </p>
          ) : null}

          <form key={`name-${profile.version}`} className="form-grid" onSubmit={submitDisplayName}>
            <div className="field-group">
              <label htmlFor="profile-display-name">{t('profileIdentity.displayNameLabel')}</label>
              <input
                id="profile-display-name"
                name="displayName"
                type="text"
                defaultValue={profile.displayName}
                maxLength={120}
                autoComplete="name"
                disabled={pending}
              />
              <small>{t('profileIdentity.displayNameHelp')}</small>
            </div>
            <div className="form-actions">
              <button type="submit" disabled={pending}>
                {displayNameMutation.isPending
                  ? t('profileIdentity.savingName')
                  : t('profileIdentity.saveName')}
              </button>
            </div>
          </form>

          <div className="field-group">
            <label htmlFor="profile-avatar-file">{t('profileIdentity.avatarLabel')}</label>
            <small>{t('profileIdentity.avatarHelp')}</small>
            <input
              id="profile-avatar-file"
              className="profile-identity-file-input"
              type="file"
              accept="image/*"
              disabled={pending}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                event.currentTarget.value = '';
                if (!file) return;
                setSaved(false);
                avatarMutation.mutate(file);
              }}
            />
            <div className="profile-identity-actions">
              {phaseKey ? (
                <span role="status">{t(phaseKey)}</span>
              ) : avatarMutation.isPending ? (
                <span role="status">{t('profileIdentity.replacingAvatar')}</span>
              ) : null}
              {profile.profileAttachmentId ? (
                <button
                  type="button"
                  className="secondary"
                  disabled={pending}
                  onClick={() => {
                    setSaved(false);
                    removeAvatarMutation.mutate();
                  }}
                >
                  {removeAvatarMutation.isPending
                    ? t('profileIdentity.removingAvatar')
                    : t('profileIdentity.removeAvatar')}
                </button>
              ) : null}
            </div>
          </div>
        </>
      ) : null}

      {saved ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{t('profileIdentity.saved')}</span>
        </div>
      ) : null}
      {displayNameMutation.error ? <ProblemState error={displayNameMutation.error} /> : null}
      {avatarMutation.error ? <ProblemState error={avatarMutation.error} /> : null}
      {removeAvatarMutation.error ? <ProblemState error={removeAvatarMutation.error} /> : null}
    </section>
  );
}
