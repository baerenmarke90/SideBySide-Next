import {
  createLocalWishDetectiveSession,
  isWishDetectiveGuessCorrect,
  selectWishDetectiveRounds,
  type WishDetectiveCandidate,
  type WishDetectiveParticipant,
  validateWishDetectiveClues,
} from './wishDetectiveSession';

const PARTICIPANTS: readonly [
  WishDetectiveParticipant,
  WishDetectiveParticipant,
] = [
  { id: 'lea', displayName: 'Lea' },
  { id: 'alex', displayName: 'Alex' },
];

function candidate(
  wishId: string,
  createdBy: string,
  title: string,
): WishDetectiveCandidate {
  return { wishId, createdBy, title };
}

const FOUR_ROUNDS: WishDetectiveCandidate[] = [
  candidate('lea-1', 'lea', 'Sterne gucken im Garten'),
  candidate('alex-1', 'alex', 'Wochenende am Meer'),
  candidate('lea-2', 'lea', 'Picknick am See'),
  candidate('alex-2', 'alex', 'Konzert in Berlin'),
];

function setValidClues(
  session: ReturnType<typeof createLocalWishDetectiveSession>,
): void {
  session.dispatch({ type: 'SET_CLUE', index: 0, value: 'Nacht' });
  session.dispatch({ type: 'SET_CLUE', index: 1, value: 'Decke' });
  session.dispatch({ type: 'SET_CLUE', index: 2, value: 'Warm' });
}

describe('selectWishDetectiveRounds', () => {
  it('builds a balanced alternating set capped at four rounds per partner', () => {
    const candidates = [
      ...Array.from({ length: 6 }, (_, index) =>
        candidate(`lea-${index}`, 'lea', `Lea ${index}`),
      ),
      ...Array.from({ length: 5 }, (_, index) =>
        candidate(`alex-${index}`, 'alex', `Alex ${index}`),
      ),
      candidate('outsider-1', 'outsider', 'Not eligible'),
    ];

    const rounds = selectWishDetectiveRounds(
      candidates,
      PARTICIPANTS,
      () => 0.5,
    );

    expect(rounds).toHaveLength(8);
    expect(rounds.every((round) => round.createdBy !== 'outsider')).toBe(true);
    for (let index = 0; index < rounds.length; index += 1) {
      expect(rounds[index].createdBy).toBe(index % 2 === 0 ? 'lea' : 'alex');
    }
  });

  it('supports a smaller 2+2 round and fails sparse below two wishes for either partner', () => {
    expect(
      selectWishDetectiveRounds(
        [
          candidate('l1', 'lea', 'L1'),
          candidate('l2', 'lea', 'L2'),
          candidate('a1', 'alex', 'A1'),
          candidate('a2', 'alex', 'A2'),
          candidate('a3', 'alex', 'A3'),
        ],
        PARTICIPANTS,
        () => 0.5,
      ),
    ).toHaveLength(4);

    expect(
      selectWishDetectiveRounds(
        [
          candidate('l1', 'lea', 'L1'),
          candidate('a1', 'alex', 'A1'),
          candidate('a2', 'alex', 'A2'),
        ],
        PARTICIPANTS,
      ),
    ).toEqual([]);
  });
});

describe('Wish Detective text rules', () => {
  it('validates one-word clues with duplicate and wish-word feedback', () => {
    expect(
      validateWishDetectiveClues(
        ['romantischer Abend', 'Nacht', 'Nacht'],
        'Sterne gucken im Garten',
      ),
    ).toEqual(['oneWord', 'duplicate', 'duplicate']);

    expect(
      validateWishDetectiveClues(
        ['Garten', 'Stern', 'Warm'],
        'Sterne gucken im Garten',
      ),
    ).toEqual(['wishWord', 'wishWord', null]);
  });

  it('accepts exact or two complete meaningful target tokens but never arbitrary substrings', () => {
    const title = 'Sterne gucken im Garten';
    expect(isWishDetectiveGuessCorrect(title, title)).toBe(true);
    expect(isWishDetectiveGuessCorrect('Sterne gucken', title)).toBe(true);
    expect(isWishDetectiveGuessCorrect('Sterne Garten', title)).toBe(true);
    expect(isWishDetectiveGuessCorrect('Sterne', title)).toBe(false);
    expect(isWishDetectiveGuessCorrect('Garten', title)).toBe(false);
    expect(isWishDetectiveGuessCorrect('tern', title)).toBe(false);
    expect(isWishDetectiveGuessCorrect('meer', 'Meer')).toBe(true);
    expect(isWishDetectiveGuessCorrect('me', 'Meer')).toBe(false);
  });
});

describe('local Wish Detective session', () => {
  it('keeps all clues editable until explicit handoff and removes the secret during handoff and guessing', () => {
    const session = createLocalWishDetectiveSession();
    session.start(FOUR_ROUNDS, PARTICIPANTS);

    setValidClues(session);
    expect(session.getSnapshot().phase).toBe('clue');
    expect(session.getSnapshot().currentWish?.title).toBe(
      'Sterne gucken im Garten',
    );

    session.dispatch({ type: 'SET_CLUE', index: 1, value: 'Kissen' });
    expect(session.getSnapshot().clues[1]).toBe('Kissen');
    expect(session.getSnapshot().phase).toBe('clue');

    session.dispatch({ type: 'START_HANDOFF' });
    expect(session.getSnapshot().phase).toBe('handoff');
    expect(session.getSnapshot().currentWish).toBeNull();

    session.dispatch({ type: 'CONFIRM_HANDOFF' });
    expect(session.getSnapshot().phase).toBe('guess');
    expect(session.getSnapshot().currentWish).toBeNull();
  });

  it('awards a correct point to the guesser and reveals the real wish only after resolution', () => {
    const session = createLocalWishDetectiveSession();
    session.start(FOUR_ROUNDS, PARTICIPANTS);
    setValidClues(session);
    session.dispatch({ type: 'START_HANDOFF' });
    session.dispatch({ type: 'CONFIRM_HANDOFF' });
    session.dispatch({ type: 'SUBMIT_GUESS', guess: 'Sterne gucken' });

    const snapshot = session.getSnapshot();
    expect(snapshot.phase).toBe('reveal');
    expect(snapshot.reveal?.result).toBe('correct');
    expect(snapshot.currentWish?.title).toBe('Sterne gucken im Garten');
    expect(snapshot.scores).toEqual([0, 1]);
    expect(snapshot.correctGuesses).toBe(1);
    expect(snapshot.roundsPlayed).toBe(1);
  });

  it('advances progress for incorrect and passed rounds independently from score and alternates giver', () => {
    const session = createLocalWishDetectiveSession();
    session.start(FOUR_ROUNDS, PARTICIPANTS);
    setValidClues(session);
    session.dispatch({ type: 'START_HANDOFF' });
    session.dispatch({ type: 'CONFIRM_HANDOFF' });
    session.dispatch({ type: 'SUBMIT_GUESS', guess: 'Falsch geraten' });

    expect(session.getSnapshot().roundsPlayed).toBe(1);
    expect(session.getSnapshot().scores).toEqual([0, 0]);
    session.dispatch({ type: 'CONTINUE' });
    expect(session.getSnapshot().giverIndex).toBe(1);
    expect(session.getSnapshot().guesserIndex).toBe(0);

    setValidClues(session);
    session.dispatch({ type: 'START_HANDOFF' });
    session.dispatch({ type: 'CONFIRM_HANDOFF' });
    session.dispatch({ type: 'PASS' });
    expect(session.getSnapshot().reveal?.result).toBe('passed');
    expect(session.getSnapshot().roundsPlayed).toBe(2);
    expect(session.getSnapshot().scores).toEqual([0, 0]);
  });

  it('finishes every selected round and restart works from completion', () => {
    const session = createLocalWishDetectiveSession();
    session.start(FOUR_ROUNDS, PARTICIPANTS);

    for (let index = 0; index < FOUR_ROUNDS.length; index += 1) {
      setValidClues(session);
      session.dispatch({ type: 'START_HANDOFF' });
      session.dispatch({ type: 'CONFIRM_HANDOFF' });
      session.dispatch({ type: 'PASS' });
      session.dispatch({ type: 'CONTINUE' });
    }

    expect(session.getSnapshot().phase).toBe('finished');
    expect(session.getSnapshot().roundsPlayed).toBe(4);

    session.restart();
    const restarted = session.getSnapshot();
    expect(restarted.phase).toBe('clue');
    expect(restarted.currentRoundIndex).toBe(0);
    expect(restarted.roundsPlayed).toBe(0);
    expect(restarted.scores).toEqual([0, 0]);
  });

  it('emits immutable observable snapshot references', () => {
    const session = createLocalWishDetectiveSession();
    session.start(FOUR_ROUNDS, PARTICIPANTS);
    const before = session.getSnapshot();
    const cluesBefore = before.clues;

    session.dispatch({ type: 'SET_CLUE', index: 0, value: 'Nacht' });
    const after = session.getSnapshot();

    expect(after).not.toBe(before);
    expect(after.clues).not.toBe(cluesBefore);
    expect(before.clues[0]).toBe('');
    expect(after.clues[0]).toBe('Nacht');
  });
});
