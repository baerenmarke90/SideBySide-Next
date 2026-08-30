import { type FormEvent, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import type { SessionView } from '../api/generated/models/SessionView';
import type { SensitiveEntryToken } from '../client/entryToken';
import {
  completePasswordRecovery,
  registerFromInvitation,
  requestPasswordRecovery,
  signInAndJoinInvitation,
} from '../client/identityFlow';
import { useTranslation } from '../i18n';
import { Brand } from './Brand';
import { ProblemState } from './ProblemState';

type EntryMode = 'signIn' | 'register' | 'recoveryRequest';

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
  const recoveryToken = entryToken?.kind === 'recovery' ? entryToken.token : null;
  const [mode, setMode] = useState<EntryMode>('signIn');
  const [recoveryRequested, setRecoveryRequested] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const signInMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      signInAndJoinInvitation(
        apiBaseUrl,
        email,
        password,
        invitationToken,
      ),
    onSuccess: onSession,
  });

  const registerMutation = useMutation({
    mutationFn: ({
      displayName,
      email,
      password,
    }: {
      displayName: string;
      email: string;
      password: string;
    }) => {
      if (!invitationToken) throw new Error(t('identity.invitationMissing'));
      return registerFromInvitation(
        apiBaseUrl,
        displayName,
        email,
        password,
        invitationToken,
      );
    },
    onSuccess: onSession,
  });

  const recoveryRequestMutation = useMutation({
    mutationFn: (email: string) => requestPasswordRecovery(apiBaseUrl, email),
    onSuccess: () => setRecoveryRequested(true),
  });

  const recoveryMutation = useMutation({
    mutationFn: (newPassword: string) => {
      if (!recoveryToken) throw new Error(t('identity.recoveryMissing'));
      return completePasswordRecovery(apiBaseUrl, recoveryToken, newPassword);
    },
    onSuccess: onSession,
  });

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
    signInMutation.mutate({
      email: String(data.get('email')),
      password: String(data.get('password')),
    });
  }

  function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const password = requireMatchingPasswords(data);
    if (!password) return;
    registerMutation.mutate({
      displayName: String(data.get('displayName')),
      email: String(data.get('email')),
      password,
    });
  }

  function submitRecoveryRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    recoveryRequestMutation.mutate(String(data.get('email')));
  }

  function submitRecovery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const password = requireMatchingPasswords(data);
    if (password) recoveryMutation.mutate(password);
  }

  const activeError =
    signInMutation.error ??
    registerMutation.error ??
    recoveryRequestMutation.error ??
    recoveryMutation.error;

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
        <section className="login-card" aria-labelledby="identity-entry-heading">
          {recoveryToken ? (
            <>
              <div>
                <p className="eyebrow">{t('identity.recoveryEyebrow')}</p>
                <h2 id="identity-entry-heading">{t('identity.recoveryTitle')}</h2>
                <p className="muted">{t('identity.recoveryBody')}</p>
              </div>
              <form onSubmit={submitRecovery} className="form-grid login-form">
                <PasswordFields />
                <button
                  type="submit"
                  disabled={recoveryMutation.isPending}
                  aria-busy={recoveryMutation.isPending}
                >
                  {recoveryMutation.isPending
                    ? t('identity.recoverySaving')
                    : t('identity.recoverySave')}
                </button>
              </form>
            </>
          ) : mode === 'register' && invitationToken ? (
            <>
              <div>
                <p className="eyebrow">{t('identity.invitationEyebrow')}</p>
                <h2 id="identity-entry-heading">{t('identity.registerTitle')}</h2>
                <p className="muted">{t('identity.registerBody')}</p>
              </div>
              <form onSubmit={submitRegistration} className="form-grid login-form">
                <div className="field-group">
                  <label htmlFor="display-name">{t('identity.displayName')}</label>
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
                  disabled={registerMutation.isPending}
                  aria-busy={registerMutation.isPending}
                >
                  {registerMutation.isPending
                    ? t('identity.registerPending')
                    : t('identity.registerSubmit')}
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setMode('signIn')}
                >
                  {t('identity.haveAccount')}
                </button>
              </form>
            </>
          ) : mode === 'recoveryRequest' ? (
            <>
              <div>
                <p className="eyebrow">{t('identity.recoveryRequestEyebrow')}</p>
                <h2 id="identity-entry-heading">
                  {t('identity.recoveryRequestTitle')}
                </h2>
                <p className="muted">{t('identity.recoveryRequestBody')}</p>
              </div>
              {recoveryRequested ? (
                <div className="inline-message inline-message-success" role="status">
                  <strong>{t('identity.recoveryRequestedTitle')}</strong>
                  <span>{t('identity.recoveryRequestedBody')}</span>
                </div>
              ) : (
                <form
                  onSubmit={submitRecoveryRequest}
                  className="form-grid login-form"
                >
                  <EmailField />
                  <button
                    type="submit"
                    disabled={recoveryRequestMutation.isPending}
                    aria-busy={recoveryRequestMutation.isPending}
                  >
                    {recoveryRequestMutation.isPending
                      ? t('identity.recoveryRequestPending')
                      : t('identity.recoveryRequestSubmit')}
                  </button>
                </form>
              )}
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setRecoveryRequested(false);
                  setMode('signIn');
                }}
              >
                {t('identity.backToSignIn')}
              </button>
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
                  {invitationToken ? t('identity.invitationBody') : t('login.body')}
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
                  disabled={signInMutation.isPending}
                  aria-busy={signInMutation.isPending}
                >
                  {signInMutation.isPending
                    ? t('login.pending')
                    : t('login.submit')}
                </button>
                {invitationToken ? (
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setMode('register')}
                  >
                    {t('identity.createAccount')}
                  </button>
                ) : null}
                <button
                  type="button"
                  className="tertiary"
                  onClick={() => setMode('recoveryRequest')}
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
          {activeError ? <ProblemState error={activeError} /> : null}
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
