import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { InvitationsApi } from '../api/generated/apis/InvitationsApi';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import type { InvitationView } from '../api/generated/models/InvitationView';
import type { IssuedInvitationView } from '../api/generated/models/IssuedInvitationView';
import { Configuration } from '../api/generated/runtime';
import { buildInvitationLink } from '../client/invitationLink';
import { normalizeClientError } from '../client/problemDetails';
import { resolvedLocale, useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

type CopyState = 'idle' | 'copied' | 'failed';

function invitationDate(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(value);
}

export function PartnerConnectionPanel({
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
  const queryClient = useQueryClient();
  const [issuedInvitation, setIssuedInvitation] =
    useState<IssuedInvitationView | null>(null);
  const [copyState, setCopyState] = useState<CopyState>('idle');

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
  const invitationsApi = useMemo(
    () => new InvitationsApi(configuration),
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

  const partner =
    spaceQuery.data?.partners.find(
      (candidate) => candidate.id !== account.id,
    ) ?? null;
  const canInvite = Boolean(spaceQuery.data && !partner);

  const invitationsQuery = useQuery({
    queryKey: ['space-invitations', spaceId],
    queryFn: async () => {
      try {
        return await invitationsApi.listInvitationsApiV1SpacesSpaceIdInvitationsGet(
          { spaceId },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    enabled: canInvite,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      try {
        return await invitationsApi.createInvitationApiV1SpacesSpaceIdInvitationsPost(
          { spaceId },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (invitation) => {
      setIssuedInvitation(invitation);
      setCopyState('idle');
      await queryClient.invalidateQueries({
        queryKey: ['space-invitations', spaceId],
      });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: async (invitation: InvitationView) => {
      try {
        await invitationsApi.revokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDelete(
          {
            invitationId: invitation.id,
            spaceId,
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (_data, invitation) => {
      if (issuedInvitation?.id === invitation.id) {
        setIssuedInvitation(null);
        setCopyState('idle');
        createMutation.reset();
      }
      await queryClient.invalidateQueries({
        queryKey: ['space-invitations', spaceId],
      });
    },
  });

  const issuedLink = issuedInvitation
    ? buildInvitationLink(window.location.origin, issuedInvitation.token)
    : null;

  async function copyIssuedLink() {
    if (!issuedLink) return;
    try {
      if (!navigator.clipboard?.writeText)
        throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(issuedLink);
      setCopyState('copied');
    } catch {
      setCopyState('failed');
    }
  }

  function hideIssuedLink() {
    setIssuedInvitation(null);
    setCopyState('idle');
    createMutation.reset();
  }

  if (spaceQuery.isLoading) {
    return (
      <div className="page profile-page">
        <section
          className="profile-section"
          aria-labelledby="partner-connection-title"
        >
          <UiState kind="loading" title={t('partnerConnection.checking')} />
        </section>
      </div>
    );
  }

  if (spaceQuery.error) {
    return (
      <div className="page profile-page">
        <section
          className="profile-section"
          aria-labelledby="partner-connection-title"
        >
          <ProblemState
            error={spaceQuery.error}
            onRetry={() => void spaceQuery.refetch()}
          />
        </section>
      </div>
    );
  }

  if (!spaceQuery.data || partner) return null;

  const invitations = invitationsQuery.data ?? [];

  return (
    <div className="page profile-page">
      <section
        className="profile-section"
        aria-labelledby="partner-connection-title"
      >
        <div className="section-head">
          <div>
            <p className="section-kicker">{t('partnerConnection.eyebrow')}</p>
            <h2 id="partner-connection-title">
              {t('partnerConnection.title')}
            </h2>
            <p className="profile-section-intro">
              {t('partnerConnection.intro')}
            </p>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            aria-busy={createMutation.isPending}
          >
            {createMutation.isPending
              ? t('partnerConnection.creating')
              : t('partnerConnection.create')}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => void spaceQuery.refetch()}
            disabled={spaceQuery.isFetching}
          >
            {spaceQuery.isFetching
              ? t('partnerConnection.refreshing')
              : t('partnerConnection.refresh')}
          </button>
        </div>
        <p className="profile-section-intro">
          {t('partnerConnection.refreshHelp')}
        </p>

        {createMutation.error ? (
          <ProblemState error={createMutation.error} />
        ) : null}

        {issuedInvitation && issuedLink ? (
          <div className="inline-message inline-message-success" role="status">
            <strong>{t('partnerConnection.issuedTitle')}</strong>
            <span>{t('partnerConnection.issuedBody')}</span>
            <div className="field-group">
              <label htmlFor="partner-invitation-link">
                {t('partnerConnection.linkLabel')}
              </label>
              <input
                id="partner-invitation-link"
                value={issuedLink}
                readOnly
                onFocus={(event) => event.currentTarget.select()}
              />
            </div>
            <span>
              {t('partnerConnection.expiresAt', {
                date: invitationDate(issuedInvitation.expiresAt),
              })}
            </span>
            <div className="form-actions">
              <button type="button" onClick={() => void copyIssuedLink()}>
                {t('partnerConnection.copy')}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={hideIssuedLink}
              >
                {t('partnerConnection.hide')}
              </button>
            </div>
            {copyState === 'copied' ? (
              <span>{t('partnerConnection.copied')}</span>
            ) : null}
            {copyState === 'failed' ? (
              <span role="alert">{t('partnerConnection.copyFailed')}</span>
            ) : null}
          </div>
        ) : null}

        <div>
          <h3>{t('partnerConnection.openTitle')}</h3>
          <p className="profile-section-intro">
            {t('partnerConnection.openIntro')}
          </p>
        </div>

        {invitationsQuery.isLoading ? (
          <UiState kind="loading" title={t('partnerConnection.loading')} />
        ) : null}
        {invitationsQuery.error ? (
          <ProblemState
            error={invitationsQuery.error}
            onRetry={() => void invitationsQuery.refetch()}
          />
        ) : null}
        {invitationsQuery.data && invitations.length === 0 ? (
          <UiState
            kind="empty"
            title={t('partnerConnection.openEmptyTitle')}
            body={t('partnerConnection.openEmptyBody')}
          />
        ) : null}
        {invitations.length > 0 ? (
          <ul className="profile-preference-list">
            {invitations.map((invitation) => (
              <li key={invitation.id} className="profile-preference-card">
                <div>
                  <h3>{t('partnerConnection.invitationLabel')}</h3>
                  <p>
                    {t('partnerConnection.createdAt', {
                      date: invitationDate(invitation.createdAt),
                    })}
                  </p>
                  <p>
                    {t('partnerConnection.expiresAt', {
                      date: invitationDate(invitation.expiresAt),
                    })}
                  </p>
                </div>
                <div className="form-actions">
                  <button
                    type="button"
                    className="tertiary compact-action"
                    disabled={revokeMutation.isPending}
                    onClick={() => revokeMutation.mutate(invitation)}
                  >
                    {revokeMutation.isPending &&
                    revokeMutation.variables?.id === invitation.id
                      ? t('partnerConnection.revoking')
                      : t('partnerConnection.revoke')}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
        {revokeMutation.error ? (
          <ProblemState error={revokeMutation.error} />
        ) : null}
      </section>
    </div>
  );
}
