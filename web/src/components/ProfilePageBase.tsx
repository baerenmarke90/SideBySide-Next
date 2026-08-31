import { type FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { DurationDisplayMode } from '../api/generated/models/DurationDisplayMode';
import { PreferenceCategory } from '../api/generated/models/PreferenceCategory';
import { PreferenceSentiment } from '../api/generated/models/PreferenceSentiment';
import type { ProfilePreferenceView } from '../api/generated/models/ProfilePreferenceView';
import { ProfileVisibility } from '../api/generated/models/ProfileVisibility';
import type { SpaceProfileView } from '../api/generated/models/SpaceProfileView';
import { Configuration } from '../api/generated/runtime';
import {
  type ProfilePreferenceDraft,
  profilePreferenceCreateFromDraft,
  profilePreferenceUpdateFromDraft,
} from '../client/profilePreferenceDraft';
import { normalizeClientError } from '../client/problemDetails';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

const CATEGORIES = Object.values(PreferenceCategory);
const SENTIMENTS = Object.values(PreferenceSentiment);

type PreferenceVisibility =
  | typeof ProfileVisibility.SELF_PROFILE
  | typeof ProfileVisibility.PRIVATE_PARTNER_NOTE;

function relationshipDateInput(value: Date | null | undefined): string {
  if (!value) return '';
  return value.toISOString().slice(0, 10);
}

function relationshipDuration(
  profile: SpaceProfileView,
  t: (key: string, values?: Record<string, unknown>) => string,
): string {
  if (!profile.showRelationshipDuration || !profile.relationshipStartedOn) {
    return t('profiles.relationshipNotAvailable');
  }

  if (
    profile.durationDisplayMode === DurationDisplayMode.DAYS &&
    profile.relationshipDays !== null &&
    profile.relationshipDays !== undefined
  ) {
    return t('profiles.relationshipDays', { days: profile.relationshipDays });
  }

  if (
    profile.relationshipYears !== null &&
    profile.relationshipYears !== undefined &&
    profile.relationshipMonths !== null &&
    profile.relationshipMonths !== undefined
  ) {
    return t('profiles.relationshipYearsMonths', {
      years: profile.relationshipYears,
      months: profile.relationshipMonths,
    });
  }

  return t('profiles.relationshipNotAvailable');
}

function RelationshipProfileSection({
  spacesApi,
  spaceId,
}: {
  spacesApi: SpacesApi;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);

  const profileQuery = useQuery({
    queryKey: ['space-profile', spaceId],
    queryFn: async () => {
      try {
        return await spacesApi.getSpaceProfileApiV1SpacesSpaceIdProfileGet({
          spaceId,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: async ({
      relationshipStartedOn,
      showRelationshipDuration,
      durationDisplayMode,
    }: {
      relationshipStartedOn: Date | null;
      showRelationshipDuration: boolean;
      durationDisplayMode: SpaceProfileView['durationDisplayMode'];
    }) => {
      if (!profileQuery.data) return null;
      try {
        return await spacesApi.updateSpaceProfileApiV1SpacesSpaceIdProfilePut({
          spaceId,
          ifMatch: String(profileQuery.data.version),
          spaceProfileUpdate: {
            relationshipStartedOn,
            showRelationshipDuration,
            durationDisplayMode:
              durationDisplayMode ?? DurationDisplayMode.YEARS_MONTHS,
          },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (profile) => {
      setSaved(true);
      if (profile) {
        queryClient.setQueryData(['space-profile', spaceId], profile);
      } else {
        await queryClient.invalidateQueries({
          queryKey: ['space-profile', spaceId],
        });
      }
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    const form = new FormData(event.currentTarget);
    const start = String(form.get('relationshipStartedOn') || '');
    mutation.mutate({
      relationshipStartedOn: start ? new Date(`${start}T00:00:00.000Z`) : null,
      showRelationshipDuration: form.get('showRelationshipDuration') === 'on',
      durationDisplayMode: String(
        form.get('durationDisplayMode'),
      ) as SpaceProfileView['durationDisplayMode'],
    });
  }

  return (
    <section
      className="layout-panel profile-section"
      aria-labelledby="relationship-profile-title"
    >
      <h2 id="relationship-profile-title">{t('profiles.relationshipTitle')}</h2>

      {profileQuery.isLoading ? (
        <UiState kind="loading" title={t('profiles.loading')} />
      ) : null}
      {profileQuery.error ? (
        <ProblemState
          error={profileQuery.error}
          onRetry={() => void profileQuery.refetch()}
        />
      ) : null}
      {profileQuery.data ? (
        <form
          key={profileQuery.data.version}
          className="form-grid"
          onSubmit={submit}
        >
          <div className="field-group">
            <label htmlFor="relationship-started-on">
              {t('profiles.relationshipStartLabel')}
            </label>
            <input
              id="relationship-started-on"
              name="relationshipStartedOn"
              type="date"
              defaultValue={relationshipDateInput(
                profileQuery.data.relationshipStartedOn,
              )}
            />
          </div>

          <label className="choice-row" htmlFor="show-relationship-duration">
            <input
              id="show-relationship-duration"
              name="showRelationshipDuration"
              type="checkbox"
              defaultChecked={profileQuery.data.showRelationshipDuration}
            />
            <span>
              <strong>{t('profiles.relationshipDurationLabel')}</strong>
              <small>{t('profiles.relationshipDurationHelp')}</small>
            </span>
          </label>

          <div className="field-group">
            <label htmlFor="relationship-duration-mode">
              {t('profiles.relationshipModeLabel')}
            </label>
            <select
              id="relationship-duration-mode"
              name="durationDisplayMode"
              defaultValue={
                profileQuery.data.durationDisplayMode ??
                DurationDisplayMode.YEARS_MONTHS
              }
            >
              <option value={DurationDisplayMode.YEARS_MONTHS}>
                {t('profiles.relationshipModeYearsMonths')}
              </option>
              <option value={DurationDisplayMode.DAYS}>
                {t('profiles.relationshipModeDays')}
              </option>
            </select>
          </div>

          <p className="profile-duration" role="status">
            {t('profiles.relationshipCurrent', {
              duration: relationshipDuration(profileQuery.data, t),
            })}
          </p>

          <div className="form-actions">
            <button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? t('profiles.relationshipSaving')
                : t('profiles.relationshipSave')}
            </button>
          </div>
        </form>
      ) : null}

      {saved ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{t('profiles.relationshipSaved')}</span>
        </div>
      ) : null}
      {mutation.error ? <ProblemState error={mutation.error} /> : null}
    </section>
  );
}

function PreferenceForm({
  preference,
  privateNote,
  pending,
  onCancel,
  onSubmit,
}: {
  preference: ProfilePreferenceView | null;
  privateNote: boolean;
  pending: boolean;
  onCancel: () => void;
  onSubmit: (draft: ProfilePreferenceDraft) => void;
}) {
  const { t } = useTranslation();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    onSubmit({
      category: String(
        form.get('category'),
      ) as ProfilePreferenceDraft['category'],
      sentiment: String(
        form.get('sentiment'),
      ) as ProfilePreferenceDraft['sentiment'],
      topic: String(form.get('topic') || ''),
      value: String(form.get('value') || ''),
    });
  }

  return (
    <form
      key={preference?.id ?? 'new'}
      className="profile-preference-form form-grid"
      onSubmit={submit}
    >
      <h3>
        {preference
          ? privateNote
            ? t('profiles.noteEditTitle')
            : t('profiles.preferenceEditTitle')
          : privateNote
            ? t('profiles.noteCreateTitle')
            : t('profiles.preferenceCreateTitle')}
      </h3>

      <div className="field-group">
        <label
          htmlFor={`preference-category-${privateNote ? 'private' : 'self'}`}
        >
          {t('profiles.categoryLabel')}
        </label>
        <select
          id={`preference-category-${privateNote ? 'private' : 'self'}`}
          name="category"
          defaultValue={preference?.category ?? PreferenceCategory.OTHER}
        >
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {t(`profiles.category.${category}`)}
            </option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label
          htmlFor={`preference-sentiment-${privateNote ? 'private' : 'self'}`}
        >
          {t('profiles.sentimentLabel')}
        </label>
        <select
          id={`preference-sentiment-${privateNote ? 'private' : 'self'}`}
          name="sentiment"
          defaultValue={preference?.sentiment ?? PreferenceSentiment.LIKE}
        >
          {SENTIMENTS.map((sentiment) => (
            <option key={sentiment} value={sentiment}>
              {t(`profiles.sentiment.${sentiment}`)}
            </option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label htmlFor={`preference-topic-${privateNote ? 'private' : 'self'}`}>
          {t('profiles.topicLabel')}
        </label>
        <input
          id={`preference-topic-${privateNote ? 'private' : 'self'}`}
          name="topic"
          required
          maxLength={120}
          defaultValue={preference?.topic ?? ''}
          placeholder={
            privateNote
              ? t('profiles.noteTopicPlaceholder')
              : t('profiles.topicPlaceholder')
          }
        />
      </div>

      <div className="field-group">
        <label htmlFor={`preference-value-${privateNote ? 'private' : 'self'}`}>
          {t('profiles.valueLabel')}
        </label>
        <textarea
          id={`preference-value-${privateNote ? 'private' : 'self'}`}
          name="value"
          required
          rows={3}
          maxLength={500}
          defaultValue={preference?.value ?? ''}
          placeholder={
            privateNote
              ? t('profiles.noteValuePlaceholder')
              : t('profiles.valuePlaceholder')
          }
        />
      </div>

      <div className="form-actions">
        {preference ? (
          <button type="button" className="secondary" onClick={onCancel}>
            {t('common.cancel')}
          </button>
        ) : null}
        <button type="submit" disabled={pending}>
          {pending
            ? t('profiles.saving')
            : preference
              ? t('profiles.saveChanges')
              : t('profiles.create')}
        </button>
      </div>
    </form>
  );
}

function PreferenceManager({
  profilesApi,
  spaceId,
  accountId,
  visibility,
  items,
  title,
  intro,
  emptyTitle,
  emptyBody,
}: {
  profilesApi: ProfilesApi;
  spaceId: string;
  accountId: string;
  visibility: PreferenceVisibility;
  items: ProfilePreferenceView[];
  title: string;
  intro: string;
  emptyTitle: string;
  emptyBody: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<ProfilePreferenceView | null>(null);
  const [deleteTarget, setDeleteTarget] =
    useState<ProfilePreferenceView | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const privateNote = visibility === ProfileVisibility.PRIVATE_PARTNER_NOTE;

  const saveMutation = useMutation({
    mutationFn: async (draft: ProfilePreferenceDraft) => {
      try {
        if (editing) {
          return await profilesApi.updateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPut(
            {
              preferenceId: editing.id,
              spaceId,
              ifMatch: String(editing.version),
              profilePreferenceUpdate: profilePreferenceUpdateFromDraft(draft),
            },
          );
        }
        return await profilesApi.createProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPost(
          {
            spaceId,
            profilePreferenceCreate: profilePreferenceCreateFromDraft(
              draft,
              accountId,
              visibility,
            ),
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setSavedMessage(editing ? t('profiles.updated') : t('profiles.created'));
      setEditing(null);
      await queryClient.invalidateQueries({
        queryKey: ['profile-preferences', spaceId],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (target: ProfilePreferenceView) => {
      try {
        await profilesApi.deleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDelete(
          {
            preferenceId: target.id,
            spaceId,
            ifMatch: String(target.version),
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setDeleteTarget(null);
      setSavedMessage(t('profiles.deleted'));
      await queryClient.invalidateQueries({
        queryKey: ['profile-preferences', spaceId],
      });
    },
  });

  return (
    <section
      className="layout-panel profile-section"
      aria-labelledby={`profile-manager-${visibility}`}
    >
      <div className="section-head">
        <div>
          <h2 id={`profile-manager-${visibility}`}>{title}</h2>
          <p className="profile-section-intro">{intro}</p>
        </div>
      </div>

      {savedMessage ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{savedMessage}</span>
        </div>
      ) : null}

      <PreferenceForm
        preference={editing}
        privateNote={privateNote}
        pending={saveMutation.isPending}
        onCancel={() => {
          setEditing(null);
          saveMutation.reset();
        }}
        onSubmit={(draft) => {
          setSavedMessage(null);
          saveMutation.mutate(draft);
        }}
      />
      {saveMutation.error ? <ProblemState error={saveMutation.error} /> : null}

      {items.length === 0 ? (
        <UiState kind="empty" title={emptyTitle} body={emptyBody} />
      ) : (
        <ul className="profile-preference-list">
          {items.map((preference) => {
            const confirmingDelete = deleteTarget?.id === preference.id;
            return (
              <li key={preference.id} className="profile-preference-card">
                <div>
                  <div className="profile-preference-meta">
                    <span>{t(`profiles.category.${preference.category}`)}</span>
                    <span>
                      {t(`profiles.sentiment.${preference.sentiment}`)}
                    </span>
                  </div>
                  <h3>{preference.topic}</h3>
                  <p>{preference.value}</p>
                </div>

                {!confirmingDelete ? (
                  <div className="form-actions">
                    <button
                      type="button"
                      className="secondary compact-action"
                      onClick={() => {
                        setEditing(preference);
                        setDeleteTarget(null);
                        saveMutation.reset();
                      }}
                    >
                      {t('profiles.edit')}
                    </button>
                    <button
                      type="button"
                      className="tertiary compact-action"
                      onClick={() => {
                        setDeleteTarget(preference);
                        deleteMutation.reset();
                      }}
                    >
                      {t('profiles.delete')}
                    </button>
                  </div>
                ) : (
                  <div className="inline-delete-confirmation" role="alert">
                    <strong>{t('profiles.deleteQuestion')}</strong>
                    <span>{t('profiles.deleteBody')}</span>
                    {deleteMutation.error ? (
                      <ProblemState error={deleteMutation.error} />
                    ) : null}
                    <div className="form-actions">
                      <button
                        type="button"
                        className="secondary compact-action"
                        disabled={deleteMutation.isPending}
                        onClick={() => {
                          setDeleteTarget(null);
                          deleteMutation.reset();
                        }}
                      >
                        {t('common.cancel')}
                      </button>
                      <button
                        type="button"
                        className="danger compact-action"
                        disabled={deleteMutation.isPending}
                        onClick={() => deleteMutation.mutate(preference)}
                      >
                        {deleteMutation.isPending
                          ? t('profiles.deleting')
                          : t('profiles.deleteConfirm')}
                      </button>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function PartnerProfileSection({
  profilesApi,
  spaceId,
  partnerId,
  partnerName,
}: {
  profilesApi: ProfilesApi;
  spaceId: string;
  partnerId: string;
  partnerName: string;
}) {
  const { t } = useTranslation();
  const partnerQuery = useQuery({
    queryKey: ['partner-profile', spaceId, partnerId],
    queryFn: async () => {
      try {
        return await profilesApi.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet(
          { accountId: partnerId, spaceId },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  return (
    <section
      className="layout-panel profile-section"
      aria-labelledby="partner-profile-title"
    >
      <h2 id="partner-profile-title">
        {t('profiles.partnerTitle', { name: partnerName })}
      </h2>
      <p className="profile-section-intro">{t('profiles.partnerIntro')}</p>

      {partnerQuery.isLoading ? (
        <UiState kind="loading" title={t('profiles.loading')} />
      ) : null}
      {partnerQuery.error ? (
        <ProblemState
          error={partnerQuery.error}
          onRetry={() => void partnerQuery.refetch()}
        />
      ) : null}
      {partnerQuery.data?.preferences.length === 0 ? (
        <UiState
          kind="empty"
          title={t('profiles.partnerEmpty', { name: partnerName })}
        />
      ) : null}
      {partnerQuery.data?.preferences.length ? (
        <ul className="profile-preference-list">
          {partnerQuery.data.preferences.map((preference) => (
            <li key={preference.id} className="profile-preference-card">
              <div className="profile-preference-meta">
                <span>{t(`profiles.category.${preference.category}`)}</span>
                <span>{t(`profiles.sentiment.${preference.sentiment}`)}</span>
              </div>
              <h3>{preference.topic}</h3>
              <p>{preference.value}</p>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

export function ProfilePage({
  apiBaseUrl,
  accessToken,
  account,
  spaceId,
}: {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const configuration = useMemo(
    () =>
      new Configuration({
        basePath: apiBaseUrl,
        headers: { Authorization: `Bearer ${accessToken}` },
      }),
    [accessToken, apiBaseUrl],
  );
  const spacesApi = useMemo(
    () => new SpacesApi(configuration),
    [configuration],
  );
  const profilesApi = useMemo(
    () => new ProfilesApi(configuration),
    [configuration],
  );

  const spaceQuery = useQuery({
    queryKey: ['space', spaceId],
    queryFn: async () => {
      try {
        return await spacesApi.getSpaceApiV1SpacesSpaceIdGet({ spaceId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const preferencesQuery = useQuery({
    queryKey: ['profile-preferences', spaceId],
    queryFn: async () => {
      try {
        return await profilesApi.listProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGet(
          { spaceId },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const partner =
    spaceQuery.data?.partners.find(
      (candidate) => candidate.id !== account.id,
    ) ?? null;
  const selfPreferences =
    preferencesQuery.data?.filter(
      (preference) =>
        preference.accountId === account.id &&
        preference.visibility === ProfileVisibility.SELF_PROFILE,
    ) ?? [];
  const privatePartnerNotes = partner
    ? (preferencesQuery.data?.filter(
        (preference) =>
          preference.accountId === partner.id &&
          preference.visibility === ProfileVisibility.PRIVATE_PARTNER_NOTE,
      ) ?? [])
    : [];

  return (
    <div className="page profile-page">
      <PageHeader
        eyebrow={t('profiles.eyebrow')}
        title={t('profiles.title')}
        description={t('profiles.intro')}
      />

      <div className="layout-split layout-split-lead-rail">
        <aside
          className="layout-rail layout-rail-sticky"
          aria-label={t('profiles.settingsRailAria')}
        >
          <section
            className="layout-panel profile-section"
            aria-labelledby="account-profile-title"
          >
            <h2 id="account-profile-title">{t('profiles.accountTitle')}</h2>
            <dl className="profile-account-list">
              <div>
                <dt>{t('profiles.accountName')}</dt>
                <dd>{account.displayName}</dd>
              </div>
            </dl>
          </section>

          <RelationshipProfileSection spacesApi={spacesApi} spaceId={spaceId} />
        </aside>

        <div className="layout-main">
          {preferencesQuery.isLoading ? (
            <UiState kind="loading" title={t('profiles.preferencesLoading')} />
          ) : null}
          {preferencesQuery.error ? (
            <ProblemState
              error={preferencesQuery.error}
              onRetry={() => void preferencesQuery.refetch()}
            />
          ) : null}
          {preferencesQuery.data ? (
            <PreferenceManager
              profilesApi={profilesApi}
              spaceId={spaceId}
              accountId={account.id}
              visibility={ProfileVisibility.SELF_PROFILE}
              items={selfPreferences}
              title={t('profiles.selfTitle')}
              intro={t('profiles.selfIntro')}
              emptyTitle={t('profiles.emptySelfTitle')}
              emptyBody={t('profiles.emptySelfBody')}
            />
          ) : null}

          {spaceQuery.isLoading ? (
            <UiState kind="loading" title={t('profiles.loading')} />
          ) : null}
          {spaceQuery.error ? (
            <ProblemState
              error={spaceQuery.error}
              onRetry={() => void spaceQuery.refetch()}
            />
          ) : null}
          {spaceQuery.data && !partner ? (
            <UiState
              kind="empty"
              title={t('profiles.noPartnerTitle')}
              body={t('profiles.noPartnerBody')}
            />
          ) : null}
          {partner ? (
            <>
              <PartnerProfileSection
                profilesApi={profilesApi}
                spaceId={spaceId}
                partnerId={partner.id}
                partnerName={partner.displayName}
              />
              {preferencesQuery.data ? (
                <PreferenceManager
                  profilesApi={profilesApi}
                  spaceId={spaceId}
                  accountId={partner.id}
                  visibility={ProfileVisibility.PRIVATE_PARTNER_NOTE}
                  items={privatePartnerNotes}
                  title={t('profiles.privateTitle', {
                    name: partner.displayName,
                  })}
                  intro={t('profiles.privateIntro')}
                  emptyTitle={t('profiles.emptyPrivateTitle')}
                  emptyBody={t('profiles.emptyPrivateBody')}
                />
              ) : null}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
