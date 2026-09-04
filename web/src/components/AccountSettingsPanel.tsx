import {
  type FormEvent,
  type KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccountApi } from '../api/generated/apis/AccountApi';
import { AccountDeletionRequestConfirmationEnum } from '../api/generated/models/AccountDeletionRequest';
import { Configuration } from '../api/generated/runtime';
import { normalizeClientError } from '../client/problemDetails';
import { clearProductReadCache } from '../client/productReadCache';
import { clearStoredSession } from '../client/sessionPersistence';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';
import './AccountSettingsPanel.css';

type DeletionStep = 'consequences' | 'confirm' | null;

export interface AccountSettingsPanelProps {
  apiBaseUrl: string;
  accessToken: string;
  demoMode: boolean;
  /** Test/host override. Production uses the existing local logout/cache boundary. */
  onDeletionAccepted?: () => void | Promise<void>;
}

export function AccountSettingsPanel({
  apiBaseUrl,
  accessToken,
  demoMode,
  onDeletionAccepted,
}: AccountSettingsPanelProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [step, setStep] = useState<DeletionStep>(null);
  const [confirmation, setConfirmation] = useState('');
  const dialogRef = useRef<HTMLElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  const accountApi = useMemo(
    () =>
      new AccountApi(
        new Configuration({
          basePath: apiBaseUrl,
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
      ),
    [accessToken, apiBaseUrl],
  );

  const mutation = useMutation({
    mutationFn: async () => {
      try {
        return await accountApi.deleteOwnAccountApiV1AccountDeletionPost({
          accountDeletionRequest: {
            confirmation: AccountDeletionRequestConfirmationEnum.DELETE_ACCOUNT,
          },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setStep(null);
      setConfirmation('');

      if (onDeletionAccepted) {
        await onDeletionAccepted();
        return;
      }

      // The server has already crossed the irreversible tombstone boundary and
      // revoked the session. Reuse the normal Web logout/cache primitives, then
      // force a clean signed-out navigation so no stale in-memory mutation can
      // continue as the deleted Account.
      clearStoredSession();
      queryClient.clear();
      try {
        await clearProductReadCache();
      } finally {
        window.location.replace('/');
      }
    },
  });

  useEffect(() => {
    if (!step) return;
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    cancelButtonRef.current?.focus();

    return () => {
      document.body.style.overflow = originalOverflow;
      previousFocus?.focus();
    };
  }, [step]);

  function closeDialog() {
    if (mutation.isPending) return;
    setStep(null);
    setConfirmation('');
    mutation.reset();
  }

  function goToDataExport() {
    if (mutation.isPending) return;
    closeDialog();
    window.location.hash = 'settings-data';
  }

  function handleDialogKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !mutation.isPending) {
      event.preventDefault();
      closeDialog();
      return;
    }
    if (event.key !== 'Tab' || !dialogRef.current) return;

    const focusable = Array.from(
      dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      ),
    );
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function submitDeletion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const phrase = t('accountSettings.confirmPhrase');
    if (confirmation !== phrase || mutation.isPending || demoMode) return;
    mutation.mutate();
  }

  const confirmationPhrase = t('accountSettings.confirmPhrase');
  const confirmationMatches = confirmation === confirmationPhrase;

  return (
    <>
      <section
        className="form-card account-settings-panel"
        aria-labelledby="account-settings-title"
      >
        <p className="eyebrow">{t('accountSettings.title')}</p>
        <h2 id="account-settings-title">{t('accountSettings.title')}</h2>
        <p>{t('accountSettings.intro')}</p>

        <div className="account-danger-zone">
          <div className="account-danger-copy">
            <p className="eyebrow">{t('accountSettings.dangerEyebrow')}</p>
            <h3>{t('accountSettings.dangerTitle')}</h3>
            <p>{t('accountSettings.dangerIntro')}</p>
          </div>

          {demoMode ? (
            <div className="account-demo-delete-note" role="note">
              <strong>{t('accountSettings.demoTitle')}</strong>
              <span>{t('accountSettings.demoBody')}</span>
              <button
                type="button"
                className="account-delete-button"
                disabled
              >
                {t('accountSettings.deleteAction')}
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="account-delete-button"
              onClick={() => {
                mutation.reset();
                setStep('consequences');
              }}
            >
              {t('accountSettings.deleteAction')}
            </button>
          )}
        </div>
      </section>

      {step ? (
        <div className="account-deletion-backdrop" role="presentation">
          <section
            ref={dialogRef}
            className="modal-card account-deletion-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="account-deletion-dialog-title"
            aria-describedby="account-deletion-dialog-description"
            onKeyDown={handleDialogKeyDown}
          >
            {step === 'consequences' ? (
              <>
                <div className="account-deletion-dialog-head">
                  <div>
                    <p className="eyebrow">
                      {t('accountSettings.dangerEyebrow')}
                    </p>
                    <h2 id="account-deletion-dialog-title">
                      {t('accountSettings.consequencesTitle')}
                    </h2>
                  </div>
                </div>
                <p id="account-deletion-dialog-description">
                  {t('accountSettings.consequencesIntro')}
                </p>
                <ul className="account-deletion-consequences">
                  <li>{t('accountSettings.consequenceAccess')}</li>
                  <li>{t('accountSettings.consequencePrivate')}</li>
                  <li>{t('accountSettings.consequenceShared')}</li>
                  <li>{t('accountSettings.consequenceIrreversible')}</li>
                </ul>
                <div className="form-actions account-deletion-actions">
                  <button
                    type="button"
                    className="secondary"
                    onClick={goToDataExport}
                  >
                    {t('accountSettings.exportBefore')}
                  </button>
                  <button
                    ref={cancelButtonRef}
                    type="button"
                    className="secondary"
                    onClick={closeDialog}
                  >
                    {t('accountSettings.cancelAction')}
                  </button>
                  <button
                    type="button"
                    className="account-delete-button"
                    onClick={() => {
                      setConfirmation('');
                      mutation.reset();
                      setStep('confirm');
                    }}
                  >
                    {t('accountSettings.continueAction')}
                  </button>
                </div>
              </>
            ) : (
              <form onSubmit={submitDeletion} className="form-grid">
                <div className="account-deletion-dialog-head">
                  <div>
                    <p className="eyebrow">
                      {t('accountSettings.dangerEyebrow')}
                    </p>
                    <h2 id="account-deletion-dialog-title">
                      {t('accountSettings.finalTitle')}
                    </h2>
                  </div>
                </div>
                <p id="account-deletion-dialog-description">
                  {t('accountSettings.finalIntro')}
                </p>
                <p>
                  {t('accountSettings.confirmInstruction', {
                    phrase: confirmationPhrase,
                  })}
                </p>
                <p className="account-confirmation-phrase" aria-hidden="true">
                  <code>{confirmationPhrase}</code>
                </p>
                <div className="field-group">
                  <label htmlFor="account-deletion-confirmation">
                    {t('accountSettings.confirmLabel')}
                  </label>
                  <input
                    id="account-deletion-confirmation"
                    value={confirmation}
                    onChange={(event) => setConfirmation(event.currentTarget.value)}
                    autoComplete="off"
                    spellCheck={false}
                    disabled={mutation.isPending}
                    aria-describedby="account-deletion-confirmation-help"
                  />
                  <p
                    id="account-deletion-confirmation-help"
                    className="field-help"
                  >
                    {t('accountSettings.confirmHelp')}
                  </p>
                </div>

                {mutation.error ? <ProblemState error={mutation.error} /> : null}
                {mutation.isPending ? (
                  <p className="status" role="status" aria-live="polite">
                    {t('accountSettings.submitting')}
                  </p>
                ) : null}

                <div className="form-actions account-deletion-actions">
                  <button
                    ref={cancelButtonRef}
                    type="button"
                    className="secondary"
                    onClick={() => {
                      if (mutation.isPending) return;
                      setConfirmation('');
                      mutation.reset();
                      setStep('consequences');
                    }}
                    disabled={mutation.isPending}
                  >
                    {t('accountSettings.backAction')}
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={closeDialog}
                    disabled={mutation.isPending}
                  >
                    {t('accountSettings.cancelAction')}
                  </button>
                  <button
                    type="submit"
                    className="account-delete-button"
                    disabled={!confirmationMatches || mutation.isPending}
                  >
                    {mutation.isPending
                      ? t('accountSettings.submitting')
                      : t('accountSettings.submitAction')}
                  </button>
                </div>
              </form>
            )}
          </section>
        </div>
      ) : null}
    </>
  );
}
