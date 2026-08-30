import { type FormEvent, useEffect, useRef, useState } from 'react';
import type { SessionView } from '../api/generated/models/SessionView';
import type { SensitiveEntryToken } from '../client/entryToken';
import {
  completePasswordRecovery,
  confirmEmailAddress,
  consumeMagicLink,
  registerFromInvitation,
  requestMagicLink,
  requestPasswordRecovery,
  signInAndJoinInvitation,
} from '../client/identityFlow';
import { useTranslation } from '../i18n';
import { Brand } from './Brand';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

type EntryMode = 'signIn' | 'register' | 'recoveryRequest' | 'magicLinkRequest';
type PendingAction =
  | 'signIn'
  | 'register'
  | 'recoveryRequest'
  | 'recovery'
  | 'magicLinkRequest'
  | 'magicLinkConsume'
  | 'verification';

export function IdentityEntry({
  apiBaseUrl,
  entryToken,
  onSession,
}: {
  apiBaseUrl: string;
  entryToken: SensitiveEntryToken | null;
  onSession: (session: SessionView) => void;
}) {
  const { t } = useTranslation();
  const invitationToken =
    entryToken?.kind === 'invitation' ? entryToken.token : null;
  const recoveryToken =
    entryToken?.kind === 'recovery' ? entryToken.token : null;
  const [mode, setMode] = useState<EntryMode>('signIn');
  const [recoveryRequested, setRecoveryRequested] = useState(false);
  const [magicLinkRequested, setMagicLinkRequested] = useState(false);
  const [verificationDismissed, setVerificationDismissed] = useState(false);
  const [verificationSucceeded, setVerificationSucceeded] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [activeError, setActiveError] = useState<unknown>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(
    null,
  );
  const processedEntryToken = useRef<string | null>(null);

  async function runAction<T>(
    action: PendingAction,
    operation: () => Promise<T>,
    onSuccess: (result: T) => void,
  ): Promise<void> {
    setActiveError(null);
    setPendingAction(action);
    try {
      const result = await operation();
      setPendingAction(null);
      onSuccess(result);
    } catch (error) {
      setActiveError(error);
      setPendingAction(null);
    }
  }

  useEffect(() => {
    if (!entryToken || processedEntryToken.current === entryToken.token) return;

    if (entryToken.kind === 'magicLink') {
      const token = entryToken.token;
      processedEntryToken.current = token;
      setActiveError(null);
      setPendingAction('magicLinkConsume');
      void consumeMagicLink(apiBaseUrl, token)
        .then((session) => {
          setPendingAction(null);
          onSession(session);
        })
        .catch((error: unknown) => {
          setActiveError(error);
          setPendingAction(null);
        });
    } else if (entryToken.kind === 'emailVerification') {
      const token = entryToken.token;
      processedEntryToken.current = token;
      setActiveError(null);
      setVerificationSucceeded(false);
      setPendingAction('verification');
      void confirmEmailAddress(apiBaseUrl, token)
        .then(() => {
          setVerificationSucceeded(true);
          setPendingAction(null);
        })
        .catch((error: unknown) => {
          setActiveError(error);
          setPendingAction(null);
        });
    }
  }, [apiBaseUrl, entryToken, onSession]);

  function switchMode(nextMode: EntryMode) {
    setActiveError(null);
    setValidationError(null);
    setMode(nextMode);
  }

  function requireMatchingPasswords(data: FormData): string | null {
    const password = String(data.get('password'));
    const confirmation = String(data.get('passwordConfirmation'));
    if (password !== confirmation) {
      setValidationError(t('identity.passwordMismatch'));
      return null;
    }
    setValidationError(null);
    return password;
  }

  function submitSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const email = String(data.get('email'));
    const password = String(data.get('password'));
    void runAction(
      'signIn',
      () =>
        signInAndJoinInvitation(apiBaseUrl, email, password, invitationToken),
      onSession,
    );
  }

  function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const password = requireMatchingPasswords(data);
    if (!password) return;
    if (!invitationToken) {
      setActiveError(new Error(t('identity.invitationMissing')));
      return;
    }
    const displayName = String(data.get('displayName'));
    const email = String(data.get('email'));
    void runAction(
      'register',
      () =>
        registerFromInvitation(
          apiBaseUrl,
          displayName,
          email,
          password,
          invitationToken,
        ),
      onSession,
    );
  }

  function submitRecoveryRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const email = String(data.get('email'));
    void runAction(
      'recoveryRequest',
      () => requestPasswordRecovery(apiBaseUrl, email),
      () => setRecoveryRequested(true),
    );
  }

  function submitRecovery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const password = requireMatchingPasswords(data);
    if (!password) return;
    if (!recoveryToken) {
      setActiveError(new Error(t('identity.recoveryMissing')));
      return;
    }
    void runAction(
      'recovery',
      () => completePasswordRecovery(apiBaseUrl, recoveryToken, password),
      onSession,
    );
  }

  function submitMagicLinkRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const email = String(data.get('email'));
    void runAction(
      'magicLinkRequest',
      () => requestMagicLink(apiBaseUrl, email),
      () => setMagicLinkRequested(true),
    );
  }

  const showsVerification =
    entryToken?.kind === 'emailVerification' && !verificationDismissed;

  return (
    <main className="login-shell">
      <section className="login-intro" aria-labelledby="welcome-heading">
        <Brand
          inverse
          suffix={<span className="brand-suffix">{t('brand.suffix')}</span>}
        />
        <div className="login-intro-content">
          <h1 id="welcome-heading">{t('login.introHeading')}</h1>
          <p>{t('login.introBody')}</p>
        </div>
        <div className="entry-illustration" aria-hidden="true">
          <span className="entry-orbit entry-orbit-large" />
          <span className="entry-orbit entry-orbit-small" />
          <span className="entry-illustration-heart">♡</span>
        </div>
      </section>

      <div className="login-panel">
        <section className="login-card" aria-label={t('identity.entryAria')}>
          {entryToken?.kind === 'magicLink' ? (
            <UiState
              kind={activeError ? 'error' : 'loading'}
              title={
                activeError
                  ? t('identity.magicLinkFailedTitle')
                  : t('identity.magicLinkOpening')
              }
              body={activeError ? t('identity.magicLinkFailedBody') : undefined}
            />
          ) : showsVerification ? (
            verificationSucceeded ? (
              <>
                <div
                  className="inline-message inline-message-success"
                  role="status"
                >
                  <strong>{t('identity.verificationCompleteTitle')}</strong>
                  <span>{t('identity.verificationCompleteBody')}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setVerificationDismissed(true)}
                >
                  {t('identity.backToSignIn')}
                </button>
              </>
            ) : (
              <UiState
                kind={activeError ? 'error' : 'loading'}
                title={
                  activeError
                    ? t('identity.verificationFailedTitle')
                    : t('identity.verificationOpening')
                }
                body={
                  activeError ? t('identity.verificationFailedBody') : undefined
                }
              />
            )
          ) : recoveryToken ? (
            <>
              <div>
                <p className="eyebrow">{t('identity.recoveryEyebrow')}</p>
                <h2 id="identity-entry-heading">
                  {t('identity.recoveryTitle')}
                </h2>
                <p className="muted">{t('identity.recoveryBody')}</p>
              </div>
              <form onSubmit={submitRecovery} className="form-grid login-form">
                <PasswordFields />
                <button
                  type="submit"
                  disabled={pendingAction === 'recovery'}
                  aria-busy={pendingAction === 'recovery'}
                >
                  {pendingAction === 'recovery'
                    ? t('identity.recoverySaving')
                    : t('identity.recoverySave')}
                </button>
              </form>
            </>
          ) : mode === 'register' && invitationToken ? (
            <>
              <div>
                <p className="eyebrow">{t('identity.invitationEyebrow')}</p>
                <h2 id="identity-entry-heading">
                  {t('identity.registerTitle')}
                </h2>
                <p className="muted">{t('identity.registerBody')}</p>
              </div>
              <form
                onSubmit={submitRegistration}
                className="form-grid login-form"
              >
                <div className="field-group">
                  <label htmlFor="display-name">
                    {t('identity.displayName')}
                  </label>
                  <input
                    id="display-name"
                    name="displayName"
                    autoComplete="name"
                    required
                  />
                </div>
                <EmailField />
                <PasswordFields />
                <button
                  type="submit"
                  disabled={pendingAction === 'register'}
                  aria-busy={pendingAction === 'register'}
                >
                  {pendingAction === 'register'
                    ? t('identity.registerPending')
                    : t('identity.registerSubmit')}
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => switchMode('signIn')}
                >
                  {t('identity.haveAccount')}
                </button>
              </form>
            </>
          ) : mode === 'recoveryRequest' ? (
            <>
              <div>
                <p className="eyebrow">
                  {t('identity.recoveryRequestEyebrow')}
                </p>
                <h2 id="identity-entry-heading">
                  {t('identity.recoveryRequestTitle')}
                </h2>
                <p className="muted">{t('identity.recoveryRequestBody')}</p>
              </div>
              {recoveryRequested ? (
                <NeutralMailResult />
              ) : (
                <form
                  onSubmit={submitRecoveryRequest}
                  className="form-grid login-form"
                >
                  <EmailField />
                  <button
                    type="submit"
                    disabled={pendingAction === 'recoveryRequest'}
                    aria-busy={pendingAction === 'recoveryRequest'}
                  >
                    {pendingAction === 'recoveryRequest'
                      ? t('identity.recoveryRequestPending')
                      : t('identity.recoveryRequestSubmit')}
                  </button>
                </form>
              )}
              <BackToSignIn
                onClick={() => {
                  setRecoveryRequested(false);
                  switchMode('signIn');
                }}
              />
            </>
          ) : mode === 'magicLinkRequest' ? (
            <>
              <div>
                <p className="eyebrow">{t('identity.magicLinkEyebrow')}</p>
                <h2 id="identity-entry-heading">
                  {t('identity.magicLinkTitle')}
                </h2>
                <p className="muted">{t('identity.magicLinkBody')}</p>
              </div>
              {magicLinkRequested ? (
                <NeutralMailResult />
              ) : (
                <form
                  onSubmit={submitMagicLinkRequest}
                  className="form-grid login-form"
                >
                  <EmailField />
                  <button
                    type="submit"
                    disabled={pendingAction === 'magicLinkRequest'}
                    aria-busy={pendingAction === 'magicLinkRequest'}
                  >
                    {pendingAction === 'magicLinkRequest'
                      ? t('identity.magicLinkRequestPending')
                      : t('identity.magicLinkRequestSubmit')}
                  </button>
                </form>
              )}
              <BackToSignIn
                onClick={() => {
                  setMagicLinkRequested(false);
                  switchMode('signIn');
                }}
              />
            </>
          ) : (
            <>
              <div>
                <p className="eyebrow">
                  {invitationToken
                    ? t('identity.invitationEyebrow')
                    : t('login.eyebrow')}
                </p>
                <h2 id="identity-entry-heading">
                  {invitationToken
                    ? t('identity.invitationTitle')
                    : t('login.heading')}
                </h2>
                <p className="muted">
                  {invitationToken
                    ? t('identity.invitationBody')
                    : t('login.body')}
                </p>
              </div>
              <form onSubmit={submitSignIn} className="form-grid login-form">
                <EmailField />
                <div className="field-group">
                  <label htmlFor="password">{t('login.password')}</label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={pendingAction === 'signIn'}
                  aria-busy={pendingAction === 'signIn'}
                >
                  {pendingAction === 'signIn'
                    ? t('login.pending')
                    : t('login.submit')}
                </button>
                {invitationToken ? (
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => switchMode('register')}
                  >
                    {t('identity.createAccount')}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => switchMode('magicLinkRequest')}
                  >
                    {t('identity.useMagicLink')}
                  </button>
                )}
                <button
                  type="button"
                  className="tertiary"
                  onClick={() => switchMode('recoveryRequest')}
                >
                  {t('identity.forgotPassword')}
                </button>
              </form>
            </>
          )}

          {validationError ? (
            <p className="status status-error" role="alert">
              {validationError}
            </p>
          ) : null}
          {activeError &&
          entryToken?.kind !== 'magicLink' &&
          entryToken?.kind !== 'emailVerification' ? (
            <ProblemState error={activeError} />
          ) : null}
          <p className="login-assurance">{t('login.assurance')}</p>
        </section>
      </div>
    </main>
  );
}

function EmailField() {
  const { t } = useTranslation();
  return (
    <div className="field-group">
      <label htmlFor="email">{t('login.email')}</label>
      <input
        id="email"
        name="email"
        type="email"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        required
      />
    </div>
  );
}

function PasswordFields() {
  const { t } = useTranslation();
  return (
    <>
      <div className="field-group">
        <label htmlFor="new-password">{t('identity.newPassword')}</label>
        <input
          id="new-password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
        />
      </div>
      <div className="field-group">
        <label htmlFor="password-confirmation">
          {t('identity.passwordConfirmation')}
        </label>
        <input
          id="password-confirmation"
          name="passwordConfirmation"
          type="password"
          autoComplete="new-password"
          required
        />
      </div>
    </>
  );
}

function NeutralMailResult() {
  const { t } = useTranslation();
  return (
    <div className="inline-message inline-message-success" role="status">
      <strong>{t('identity.mailRequestedTitle')}</strong>
      <span>{t('identity.mailRequestedBody')}</span>
    </div>
  );
}

function BackToSignIn({ onClick }: { onClick: () => void }) {
  const { t } = useTranslation();
  return (
    <button type="button" className="secondary" onClick={onClick}>
      {t('identity.backToSignIn')}
    </button>
  );
}
