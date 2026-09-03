import { type FormEvent, useEffect, useMemo, useState } from 'react';
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
import { invalidateDashboard } from '../client/dashboardQueries';
import { useTranslation } from '../i18n';
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

export function RelationshipProfileSection({
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
      await invalidateDashboard(queryClient, spaceId);
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

function PreferenceDialog({
  isOpen,
  preference,
  privateNote,
  pending,
  deletePending,
  onCancel,
  onSubmit,
  onDelete,
  error,
  deleteError,
}: {
  isOpen: boolean;
  preference: ProfilePreferenceView | null;
  privateNote: boolean;
  pending: boolean;
  deletePending: boolean;
  onCancel: () => void;
  onSubmit: (draft: ProfilePreferenceDraft) => void;
  onDelete?: () => void;
  error?: unknown;
  deleteError?: unknown;
}) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

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
    <div className="preference-modal-backdrop" role="presentation">
      <div
        className="preference-modal-dialog sbs-motion-reveal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pref-dialog-heading"
      >
        <div className="preference-modal-header">
          <h3 id="pref-dialog-heading">
            {preference
              ? privateNote
                ? t('profiles.noteEditTitle')
                : t('profiles.preferenceEditTitle')
              : privateNote
                ? t('profiles.noteCreateTitle')
                : t('profiles.preferenceCreateTitle')}
          </h3>
          <button
            type="button"
            className="preference-modal-close-btn"
            onClick={onCancel}
            aria-label={t('common.cancel')}
          >
            ✕
          </button>
        </div>

        <form
          key={preference?.id ?? 'new'}
          className="form-grid"
          onSubmit={submit}
        >
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
            <label
              htmlFor={`preference-topic-${privateNote ? 'private' : 'self'}`}
            >
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
            <label
              htmlFor={`preference-value-${privateNote ? 'private' : 'self'}`}
            >
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

          {error ? <ProblemState error={error} /> : null}
          {deleteError ? <ProblemState error={deleteError} /> : null}

          <div className="preference-modal-actions">
            {preference && onDelete ? (
              <button
                type="button"
                className="tertiary compact-action preference-delete-btn"
                onClick={onDelete}
                disabled={pending || deletePending}
              >
                {deletePending ? t('profiles.deleting') : t('profiles.delete')}
              </button>
            ) : null}

            <div className="preference-modal-submit-row">
              <button
                type="button"
                className="secondary"
                onClick={onCancel}
                disabled={pending || deletePending}
              >
                {t('common.cancel')}
              </button>
              <button type="submit" disabled={pending || deletePending}>
                {pending
                  ? t('profiles.saving')
                  : preference
                    ? t('profiles.saveChanges')
                    : t('profiles.create')}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export function PreferenceManager({
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
  const [dialogOpen, setDialogOpen] = useState(false);
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
      setDialogOpen(false);
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
      setSavedMessage(t('profiles.deleted'));
      setEditing(null);
      setDialogOpen(false);
      await queryClient.invalidateQueries({
        queryKey: ['profile-preferences', spaceId],
      });
    },
  });

  const groupedCategories = useMemo(() => {
    const map = new Map<PreferenceCategory, ProfilePreferenceView[]>();
    for (const item of items) {
      const existing = map.get(item.category) ?? [];
      existing.push(item);
      map.set(item.category, existing);
    }
    return CATEGORIES.map((cat) => [cat, map.get(cat) ?? []] as const).filter(
      ([, catItems]) => catItems.length > 0,
    );
  }, [items]);

  return (
    <section
      className="layout-panel profile-section profile-preferences-panel"
      aria-labelledby={`profile-manager-${visibility}`}
    >
      <div className="profile-preferences-header">
        <div>
          <h2 id={`profile-manager-${visibility}`}>{title}</h2>
          <p className="profile-section-intro">{intro}</p>
        </div>
        <button
          type="button"
          className="secondary compact-action"
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
            saveMutation.reset();
            deleteMutation.reset();
          }}
        >
          {t('profiles.addPreferenceShort')}
        </button>
      </div>

      {savedMessage ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{savedMessage}</span>
        </div>
      ) : null}

      {items.length === 0 ? (
        <UiState kind="empty" title={emptyTitle} body={emptyBody} />
      ) : (
        <div className="profile-preferences-groups">
          {groupedCategories.map(([category, catItems]) => (
            <div key={category} className="profile-preference-category-group">
              <h3 className="profile-preference-category-heading">
                {t(`profiles.category.${category}`)}
              </h3>
              <div className="profile-preference-chips">
                {catItems.map((pref) => {
                  const sentimentIcon =
                    pref.sentiment === PreferenceSentiment.LOVE
                      ? '♥'
                      : pref.sentiment === PreferenceSentiment.LIKE
                        ? '👍'
                        : pref.sentiment === PreferenceSentiment.DISLIKE
                          ? '👎'
                          : pref.sentiment === PreferenceSentiment.AVOID
                            ? '✕'
                            : '•';
                  return (
                    <button
                      key={pref.id}
                      type="button"
                      className="profile-preference-chip sbs-motion-lift"
                      onClick={() => {
                        setEditing(pref);
                        setDialogOpen(true);
                        saveMutation.reset();
                        deleteMutation.reset();
                      }}
                    >
                      <span
                        className="profile-preference-chip-sentiment"
                        data-sentiment={pref.sentiment}
                        aria-hidden="true"
                      >
                        {sentimentIcon}
                      </span>
                      <span className="profile-preference-chip-topic">
                        {pref.topic}
                      </span>
                      <span className="profile-preference-chip-value">
                        {pref.value}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      <PreferenceDialog
        isOpen={dialogOpen}
        preference={editing}
        privateNote={privateNote}
        pending={saveMutation.isPending}
        deletePending={deleteMutation.isPending}
        onCancel={() => {
          setDialogOpen(false);
          setEditing(null);
          saveMutation.reset();
          deleteMutation.reset();
        }}
        onSubmit={(draft) => {
          setSavedMessage(null);
          saveMutation.mutate(draft);
        }}
        onDelete={
          editing
            ? () => {
                setSavedMessage(null);
                deleteMutation.mutate(editing);
              }
            : undefined
        }
        error={saveMutation.error}
        deleteError={deleteMutation.error}
      />
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

export function ProfilePreferencesSection({
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
  const profilesApi = useMemo(
    () => new ProfilesApi(configuration),
    [configuration],
  );
  const spacesApi = useMemo(
    () => new SpacesApi(configuration),
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
    <div className="profile-preferences-section">
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
  );
}

export const ProfilePage = ProfilePreferencesSection;
