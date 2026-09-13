import { useQuery } from '@tanstack/react-query';
import {
  useEffect,
  useId,
  useMemo,
  useState,
  useSyncExternalStore,
} from 'react';
import { Link } from 'react-router-dom';
import { GamesApi } from '../api/generated/apis/GamesApi';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { PartnerView } from '../api/generated/models/PartnerView';
import { Configuration } from '../api/generated/runtime';
import { normalizeClientError } from '../client/problemDetails';
import { appRoutePath } from '../client/routes';
import {
  type ClueValidationError,
  createLocalWishDetectiveSession,
  selectWishDetectiveRounds,
  type WishDetectiveCandidate,
  type WishDetectiveParticipant,
} from '../client/wishDetectiveSession';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export interface WishDetectiveGameSetup {
  participants:
    | readonly [WishDetectiveParticipant, WishDetectiveParticipant]
    | null;
  rounds: readonly WishDetectiveCandidate[];
}

function orderParticipants(
  partners: readonly PartnerView[],
  currentAccountId: string,
): [WishDetectiveParticipant, WishDetectiveParticipant] | null {
  if (partners.length !== 2) return null;
  const current = partners.find((partner) => partner.id === currentAccountId);
  const other = partners.find((partner) => partner.id !== currentAccountId);
  if (current && other) {
    return [
      { id: current.id, displayName: current.displayName },
      { id: other.id, displayName: other.displayName },
    ];
  }
  return [
    { id: partners[0].id, displayName: partners[0].displayName },
    { id: partners[1].id, displayName: partners[1].displayName },
  ];
}

async function loadDefaultSetup({
  apiBaseUrl,
  accessToken,
  spaceId,
  currentAccountId,
}: {
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  currentAccountId: string;
}): Promise<WishDetectiveGameSetup> {
  const configuration = new Configuration({
    basePath: apiBaseUrl,
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const gamesApi = new GamesApi(configuration);
  const spacesApi = new SpacesApi(configuration);
  const [candidateSet, space] = await Promise.all([
    gamesApi.getGameWishCandidates({ spaceId }),
    spacesApi.getSpaceApiV1SpacesSpaceIdGet({ spaceId }),
  ]);
  const participants = orderParticipants(space.partners, currentAccountId);
  if (!participants) return { participants: null, rounds: [] };

  const candidates: WishDetectiveCandidate[] = candidateSet.items.map(
    (candidate) => ({
      wishId: candidate.wishId,
      createdBy: candidate.createdBy,
      title: candidate.title,
    }),
  );
  return {
    participants,
    rounds: selectWishDetectiveRounds(candidates, participants),
  };
}

function clueErrorKey(error: ClueValidationError): string {
  return `games.wishDetective.errors.${error}`;
}

function WishDetectiveSessionView({
  setup,
}: {
  setup: WishDetectiveGameSetup & {
    participants: readonly [WishDetectiveParticipant, WishDetectiveParticipant];
  };
}) {
  const { t } = useTranslation();
  const clueGroupId = useId();
  const [guess, setGuess] = useState('');
  const [validationAttempted, setValidationAttempted] = useState(false);
  const session = useMemo(() => {
    const next = createLocalWishDetectiveSession();
    next.start(setup.rounds, setup.participants);
    return next;
  }, [setup]);

  useEffect(() => () => session.dispose(), [session]);

  const snapshot = useSyncExternalStore(
    session.subscribe,
    session.getSnapshot,
    session.getSnapshot,
  );
  const participants = snapshot.participants;
  if (!participants) return null;

  const giver = participants[snapshot.giverIndex];
  const guesser = participants[snapshot.guesserIndex];
  const roundLabel = t('games.wishDetective.round', {
    current: Math.min(snapshot.currentRoundIndex + 1, snapshot.totalRounds),
    total: snapshot.totalRounds,
  });

  if (snapshot.phase === 'finished') {
    return (
      <section
        className="wish-detective-finish sbs-motion-reveal"
        aria-labelledby="wish-detective-finish-title"
      >
        <p className="eyebrow">{t('games.wishDetective.finishEyebrow')}</p>
        <h2 id="wish-detective-finish-title">
          {t('games.wishDetective.finishTitle')}
        </h2>
        <p>
          {t('games.wishDetective.finishBody', {
            correct: snapshot.correctGuesses,
            total: snapshot.totalRounds,
          })}
        </p>
        <p className="wish-detective-finish-score">
          {participants[0].displayName} {snapshot.scores[0]} ·{' '}
          {participants[1].displayName} {snapshot.scores[1]}
        </p>
        <div className="wish-detective-actions">
          <button
            type="button"
            onClick={() => {
              setGuess('');
              setValidationAttempted(false);
              session.restart();
            }}
          >
            {t('games.wishDetective.restart')}
          </button>
          <Link
            className="button-link secondary-link"
            to={appRoutePath('games')}
          >
            {t('games.wishDetective.backToGames')}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <div className="wish-detective-session">
      <section className="wish-detective-meta" aria-live="polite">
        <span>{roundLabel}</span>
        <span className="wish-detective-score">
          {participants[0].displayName} <strong>{snapshot.scores[0]}</strong>
          <span aria-hidden="true"> · </span>
          {participants[1].displayName} <strong>{snapshot.scores[1]}</strong>
        </span>
      </section>

      {snapshot.phase === 'clue' && snapshot.currentWish ? (
        <section
          className="wish-detective-card wish-detective-clue sbs-motion-reveal"
          aria-labelledby="wish-detective-clue-title"
        >
          <p className="eyebrow">
            {t('games.wishDetective.clueEyebrow', {
              name: giver.displayName,
            })}
          </p>
          <h2 id="wish-detective-clue-title">{snapshot.currentWish.title}</h2>
          <p className="wish-detective-private-note">
            {t('games.wishDetective.cluePrivate')}
          </p>

          <fieldset
            className="wish-detective-clues"
            aria-describedby={`${clueGroupId}-help`}
          >
            <legend>{t('games.wishDetective.cluesLegend')}</legend>
            <p id={`${clueGroupId}-help`} className="field-help">
              {t('games.wishDetective.cluesHelp')}
            </p>
            {snapshot.clues.map((value, index) => {
              const clueIndex = index as 0 | 1 | 2;
              const error = snapshot.clueErrors[clueIndex];
              const showError = Boolean(
                error && (validationAttempted || value.trim()),
              );
              const inputId = `${clueGroupId}-clue-${index}`;
              const errorId = `${inputId}-error`;
              return (
                <div className="wish-detective-clue-field" key={inputId}>
                  <label htmlFor={inputId}>
                    {t('games.wishDetective.clueLabel', {
                      index: index + 1,
                    })}
                  </label>
                  <input
                    id={inputId}
                    value={value}
                    maxLength={40}
                    autoComplete="off"
                    aria-invalid={showError || undefined}
                    aria-describedby={showError ? errorId : undefined}
                    onChange={(event) =>
                      session.dispatch({
                        type: 'SET_CLUE',
                        index: clueIndex,
                        value: event.currentTarget.value,
                      })
                    }
                  />
                  {showError && error ? (
                    <p id={errorId} className="field-error" role="alert">
                      {t(clueErrorKey(error))}
                    </p>
                  ) : null}
                </div>
              );
            })}
          </fieldset>

          <button
            type="button"
            className="wish-detective-primary-action"
            onClick={() => {
              setValidationAttempted(true);
              session.dispatch({ type: 'START_HANDOFF' });
            }}
          >
            {t('games.wishDetective.startHandoff')}
          </button>
        </section>
      ) : null}

      {snapshot.phase === 'handoff' ? (
        <section
          className="wish-detective-card wish-detective-handoff sbs-motion-reveal"
          aria-labelledby="wish-detective-handoff-title"
        >
          <p className="eyebrow">{t('games.wishDetective.handoffEyebrow')}</p>
          <h2 id="wish-detective-handoff-title">
            {t('games.wishDetective.handoffTitle', {
              name: guesser.displayName,
            })}
          </h2>
          <p>{t('games.wishDetective.handoffBody')}</p>
          <button
            type="button"
            className="wish-detective-primary-action"
            onClick={() => {
              setGuess('');
              session.dispatch({ type: 'CONFIRM_HANDOFF' });
            }}
          >
            {t('games.wishDetective.handoffConfirm', {
              name: guesser.displayName,
            })}
          </button>
        </section>
      ) : null}

      {snapshot.phase === 'guess' ? (
        <section
          className="wish-detective-card wish-detective-guess sbs-motion-reveal"
          aria-labelledby="wish-detective-guess-title"
        >
          <p className="eyebrow">
            {t('games.wishDetective.guessEyebrow', {
              name: guesser.displayName,
            })}
          </p>
          <h2 id="wish-detective-guess-title">
            {t('games.wishDetective.guessTitle')}
          </h2>
          <div
            className="wish-detective-clue-chips"
            role="group"
            aria-label={t('games.wishDetective.cluesAria')}
          >
            {snapshot.clues.map((clue) => (
              <span key={clue}>{clue}</span>
            ))}
          </div>
          <label htmlFor="wish-detective-guess-input">
            {t('games.wishDetective.guessLabel', { name: giver.displayName })}
          </label>
          <input
            id="wish-detective-guess-input"
            value={guess}
            autoComplete="off"
            onChange={(event) => setGuess(event.currentTarget.value)}
          />
          <div className="wish-detective-actions">
            <button
              type="button"
              disabled={!guess.trim()}
              onClick={() => session.dispatch({ type: 'SUBMIT_GUESS', guess })}
            >
              {t('games.wishDetective.submitGuess')}
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => session.dispatch({ type: 'PASS' })}
            >
              {t('games.wishDetective.pass')}
            </button>
          </div>
        </section>
      ) : null}

      {snapshot.phase === 'reveal' &&
      snapshot.currentWish &&
      snapshot.reveal ? (
        <section
          className={`wish-detective-card wish-detective-reveal wish-detective-reveal-${snapshot.reveal.result} sbs-motion-reveal`}
          aria-live="polite"
          aria-labelledby="wish-detective-reveal-title"
        >
          <p className="eyebrow">{t('games.wishDetective.revealEyebrow')}</p>
          <h2 id="wish-detective-reveal-title">
            {snapshot.reveal.result === 'correct'
              ? t('games.wishDetective.correctTitle', {
                  name: guesser.displayName,
                })
              : snapshot.reveal.result === 'incorrect'
                ? t('games.wishDetective.incorrectTitle')
                : t('games.wishDetective.passedTitle')}
          </h2>
          <p className="wish-detective-revealed-wish">
            {snapshot.currentWish.title}
          </p>
          <button
            type="button"
            className="wish-detective-primary-action"
            onClick={() => {
              setGuess('');
              setValidationAttempted(false);
              session.dispatch({ type: 'CONTINUE' });
            }}
          >
            {t('games.wishDetective.continue')}
          </button>
        </section>
      ) : null}
    </div>
  );
}

export function WishDetectiveGamePage({
  apiBaseUrl,
  accessToken,
  spaceId,
  currentAccountId,
  loadSetup,
}: {
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  currentAccountId: string;
  loadSetup?: () => Promise<WishDetectiveGameSetup>;
}) {
  const { t } = useTranslation();
  const setupQuery = useQuery({
    queryKey: ['games', 'wish-detective', 'setup', spaceId],
    queryFn: async () => {
      try {
        return loadSetup
          ? await loadSetup()
          : await loadDefaultSetup({
              apiBaseUrl,
              accessToken,
              spaceId,
              currentAccountId,
            });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
    gcTime: 0,
  });

  return (
    <div className="page wish-detective-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('games')}>
            {t('games.wishDetective.back')}
          </Link>
        }
        eyebrow={t('games.entries.wishes.role')}
        title={t('games.entries.wishes.title')}
        description={t('games.wishDetective.intro')}
        className="wish-detective-heading"
      />

      {setupQuery.isPending ? (
        <UiState
          kind="loading"
          title={t('games.wishDetective.loadingTitle')}
          body={t('games.wishDetective.loadingBody')}
        />
      ) : setupQuery.error ? (
        <ProblemState
          error={setupQuery.error}
          onRetry={() => void setupQuery.refetch()}
        />
      ) : !setupQuery.data.participants ? (
        <UiState
          kind="empty"
          title={t('games.wishDetective.coupleRequiredTitle')}
          body={t('games.wishDetective.coupleRequiredBody')}
        />
      ) : setupQuery.data.rounds.length < 4 ? (
        <section
          className="wish-detective-sparse"
          aria-labelledby="wish-detective-sparse-title"
        >
          <p className="eyebrow">{t('games.wishDetective.sparseEyebrow')}</p>
          <h2 id="wish-detective-sparse-title">
            {t('games.wishDetective.sparseTitle')}
          </h2>
          <p>{t('games.wishDetective.sparseBody')}</p>
          <Link className="button-link" to="/plan#wish-title">
            {t('games.wishDetective.sparseAction')}
          </Link>
        </section>
      ) : (
        <WishDetectiveSessionView
          setup={{
            participants: setupQuery.data.participants,
            rounds: setupQuery.data.rounds,
          }}
        />
      )}
    </div>
  );
}
