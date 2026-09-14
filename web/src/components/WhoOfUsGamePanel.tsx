import { useQuery } from '@tanstack/react-query';
import { useEffect, useState, useSyncExternalStore } from 'react';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import { Configuration } from '../api/generated/runtime';
import { normalizeClientError } from '../client/problemDetails';
import {
  createLocalWhoOfUsSession,
  selectWhoOfUsQuestions,
  type WhoOfUsParticipant,
  type WhoOfUsQuestionId,
} from '../client/whoOfUsSession';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

async function loadDefaultParticipants({
  apiBaseUrl,
  accessToken,
  spaceId,
}: {
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
}): Promise<readonly [WhoOfUsParticipant, WhoOfUsParticipant] | null> {
  const spacesApi = new SpacesApi(
    new Configuration({
      basePath: apiBaseUrl,
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  );
  const space = await spacesApi.getSpaceApiV1SpacesSpaceIdGet({ spaceId });
  if (space.partners.length !== 2) return null;
  return [
    { id: space.partners[0].id, displayName: space.partners[0].displayName },
    { id: space.partners[1].id, displayName: space.partners[1].displayName },
  ];
}

function questionKey(questionId: WhoOfUsQuestionId): string {
  return `games.whoOfUs.questions.${questionId}`;
}

function WhoOfUsSessionView({
  participants,
  onExit,
}: {
  participants: readonly [WhoOfUsParticipant, WhoOfUsParticipant];
  onExit: () => void;
}) {
  const { t } = useTranslation();
  const [questions] = useState(() => selectWhoOfUsQuestions());
  const [session] = useState(() => {
    const next = createLocalWhoOfUsSession();
    next.start(questions, participants);
    return next;
  });
  const snapshot = useSyncExternalStore(
    session.subscribe,
    session.getSnapshot,
    session.getSnapshot,
  );

  useEffect(() => () => session.dispose(), [session]);

  const participant = (id: string | null): WhoOfUsParticipant | null =>
    id ? participants.find((candidate) => candidate.id === id) ?? null : null;
  const responder = participant(snapshot.responderId);
  const roundLabel = t('games.whoOfUs.round', {
    current: Math.min(snapshot.currentRoundIndex + 1, snapshot.totalRounds),
    total: snapshot.totalRounds,
  });

  if (snapshot.phase === 'finished') {
    const differentCount = snapshot.roundsPlayed - snapshot.agreementCount;
    return (
      <section
        className="who-of-us-card who-of-us-finish sbs-motion-reveal"
        aria-labelledby="who-of-us-finish-title"
      >
        <p className="eyebrow">{t('games.whoOfUs.finishEyebrow')}</p>
        <h2 id="who-of-us-finish-title">{t('games.whoOfUs.finishTitle')}</h2>
        <p className="who-of-us-finish-count">
          {t('games.whoOfUs.finishAgreement', {
            count: snapshot.agreementCount,
            total: snapshot.roundsPlayed,
          })}
        </p>
        <p>
          {t('games.whoOfUs.finishDifferent', { count: differentCount })}
        </p>
        <div className="who-of-us-actions">
          <button type="button" onClick={() => session.restart()}>
            {t('games.whoOfUs.restart')}
          </button>
          <button type="button" className="secondary-button" onClick={onExit}>
            {t('games.whoOfUs.backToGames')}
          </button>
        </div>
      </section>
    );
  }

  if (snapshot.phase === 'handoff') {
    const [, secondResponder] =
      snapshot.currentRoundIndex % 2 === 0
        ? participants
        : [participants[1], participants[0]];
    const firstResponder =
      snapshot.currentRoundIndex % 2 === 0 ? participants[0] : participants[1];
    return (
      <section
        className="who-of-us-card who-of-us-handoff sbs-motion-reveal"
        aria-labelledby="who-of-us-handoff-title"
      >
        <p className="eyebrow">{t('games.whoOfUs.handoffEyebrow')}</p>
        <h2 id="who-of-us-handoff-title">
          {t('games.whoOfUs.handoffTitle', {
            name: secondResponder.displayName,
          })}
        </h2>
        <p>
          {t('games.whoOfUs.handoffBody', {
            name: firstResponder.displayName,
          })}
        </p>
        <button
          type="button"
          className="who-of-us-primary-action"
          onClick={() => session.dispatch({ type: 'CONFIRM_HANDOFF' })}
        >
          {t('games.whoOfUs.handoffConfirm', {
            name: secondResponder.displayName,
          })}
        </button>
      </section>
    );
  }

  if (snapshot.phase === 'reveal' && snapshot.reveal) {
    const firstResponder = participant(snapshot.reveal.firstResponderId);
    const firstChoice = participant(snapshot.reveal.firstAnswerPartnerId);
    const secondResponder = participant(snapshot.reveal.secondResponderId);
    const secondChoice = participant(snapshot.reveal.secondAnswerPartnerId);
    if (!firstResponder || !firstChoice || !secondResponder || !secondChoice) {
      return null;
    }
    return (
      <section
        className="who-of-us-card who-of-us-reveal sbs-motion-reveal"
        aria-live="polite"
        aria-labelledby="who-of-us-reveal-title"
      >
        <p className="eyebrow">{t('games.whoOfUs.revealEyebrow')}</p>
        <h2 id="who-of-us-reveal-title">
          {snapshot.reveal.matches
            ? t('games.whoOfUs.sameTitle')
            : t('games.whoOfUs.differentTitle')}
        </h2>
        <p className="who-of-us-question-repeat">
          {t(questionKey(snapshot.reveal.questionId))}
        </p>
        <dl className="who-of-us-reveal-answers">
          <div>
            <dt>{firstResponder.displayName}</dt>
            <dd>{firstChoice.displayName}</dd>
          </div>
          <div>
            <dt>{secondResponder.displayName}</dt>
            <dd>{secondChoice.displayName}</dd>
          </div>
        </dl>
        <p>
          {snapshot.reveal.matches
            ? t('games.whoOfUs.sameBody', { name: firstChoice.displayName })
            : t('games.whoOfUs.differentBody')}
        </p>
        <button
          type="button"
          className="who-of-us-primary-action"
          onClick={() => session.dispatch({ type: 'CONTINUE' })}
        >
          {t('games.whoOfUs.continue')}
        </button>
      </section>
    );
  }

  if (!snapshot.currentQuestionId || !responder) return null;

  return (
    <div className="who-of-us-session">
      <div className="who-of-us-meta" aria-live="polite">
        <span>{roundLabel}</span>
        <span>
          {t('games.whoOfUs.agreementCount', {
            count: snapshot.agreementCount,
          })}
        </span>
      </div>
      <section
        className="who-of-us-card who-of-us-question sbs-motion-reveal"
        aria-labelledby="who-of-us-question-title"
      >
        <p className="eyebrow">
          {snapshot.phase === 'firstAnswer'
            ? t('games.whoOfUs.firstResponder', {
                name: responder.displayName,
              })
            : t('games.whoOfUs.secondResponder', {
                name: responder.displayName,
              })}
        </p>
        <h2 id="who-of-us-question-title">
          {t(questionKey(snapshot.currentQuestionId))}
        </h2>
        <p>{t('games.whoOfUs.choosePrompt')}</p>
        <div
          className="who-of-us-choices"
          aria-label={t('games.whoOfUs.choicesAria')}
        >
          {participants.map((choice) => (
            <button
              type="button"
              className="who-of-us-choice"
              key={choice.id}
              aria-label={t('games.whoOfUs.choiceAria', {
                responder: responder.displayName,
                choice: choice.displayName,
              })}
              onClick={() =>
                session.dispatch({ type: 'ANSWER', partnerId: choice.id })
              }
            >
              <span className="who-of-us-choice-initial" aria-hidden="true">
                {choice.displayName.trim().slice(0, 1).toLocaleUpperCase()}
              </span>
              <span>{choice.displayName}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

export function WhoOfUsGamePanel({
  apiBaseUrl,
  accessToken,
  spaceId,
  onExit,
  loadParticipants,
}: {
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  onExit: () => void;
  loadParticipants?: () => Promise<
    readonly [WhoOfUsParticipant, WhoOfUsParticipant] | null
  >;
}) {
  const { t } = useTranslation();
  const participantsQuery = useQuery({
    queryKey: ['games', 'who-of-us', 'participants', spaceId],
    queryFn: async () => {
      try {
        return loadParticipants
          ? await loadParticipants()
          : await loadDefaultParticipants({ apiBaseUrl, accessToken, spaceId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
    gcTime: 0,
  });

  return (
    <div className="who-of-us-game">
      <PageHeader
        before={
          <button type="button" className="back-link" onClick={onExit}>
            {t('games.whoOfUs.back')}
          </button>
        }
        eyebrow={t('games.entries.perspective.role')}
        title={t('games.entries.perspective.title')}
        description={t('games.whoOfUs.intro')}
        className="who-of-us-heading"
      />

      {participantsQuery.isPending ? (
        <UiState
          kind="loading"
          title={t('games.whoOfUs.loadingTitle')}
          body={t('games.whoOfUs.loadingBody')}
        />
      ) : participantsQuery.error ? (
        <ProblemState
          error={participantsQuery.error}
          onRetry={() => void participantsQuery.refetch()}
        />
      ) : !participantsQuery.data ? (
        <UiState
          kind="empty"
          title={t('games.whoOfUs.coupleRequiredTitle')}
          body={t('games.whoOfUs.coupleRequiredBody')}
        />
      ) : (
        <WhoOfUsSessionView
          participants={participantsQuery.data}
          onExit={onExit}
        />
      )}
    </div>
  );
}
