import { type FormEvent, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { createMemoryWithReadyAttachments } from '../client/memoryAttachmentDraft';
import { normalizeClientError } from '../client/problemDetails';
import { createReferenceApis } from '../client/referenceFlow';
import { appRoutePath } from '../client/routes';
import { useAttachmentDrafts } from '../client/useAttachmentDrafts';
import { useTranslation } from '../i18n';
import { AttachmentDraftField } from './AttachmentDraftField';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';

export function MemoryCreatePage({
  accessToken,
  apiBaseUrl,
  spaceId,
  onSaved,
}: {
  accessToken: string;
  apiBaseUrl: string;
  spaceId: string;
  onSaved: () => Promise<void>;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const apis = useMemo(
    () => createReferenceApis(apiBaseUrl, accessToken),
    [apiBaseUrl, accessToken],
  );
  const attachments = useAttachmentDrafts({
    apis,
    apiBaseUrl,
    accessToken,
    spaceId,
  });

  const mutation = useMutation({
    mutationFn: async ({
      title,
      body,
      happenedOn,
    }: {
      title: string;
      body: string;
      happenedOn?: Date;
    }) => {
      try {
        return await createMemoryWithReadyAttachments(
          apis,
          spaceId,
          { title, body, happenedOn },
          attachments.readyIds,
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      attachments.clear();
      await onSaved();
      navigate(appRoutePath('story'), { replace: true });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (attachments.hasPending) return;
    const data = new FormData(event.currentTarget);
    const happenedOnValue = String(data.get('happenedOn') || '');
    mutation.mutate({
      title: String(data.get('title') || '').trim(),
      body: String(data.get('body') || ''),
      happenedOn: happenedOnValue
        ? new Date(`${happenedOnValue}T00:00:00Z`)
        : undefined,
    });
  }

  return (
    <div className="page create-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('memory.backToStory')}
          </Link>
        }
        eyebrow={t('memory.eyebrow')}
        title={t('memory.heading')}
        description={t('memory.intro')}
        className="create-heading"
      />

      <section className="form-card" aria-labelledby="memory-form-heading">
        <h2 id="memory-form-heading" className="sr-only">
          {t('memory.formAria')}
        </h2>
        <form onSubmit={submit} className="form-grid memory-form">
          <div className="field-group">
            <label htmlFor="title">{t('memory.titleLabel')}</label>
            <input
              id="title"
              name="title"
              required
              maxLength={200}
              placeholder={t('memory.titlePlaceholder')}
            />
          </div>
          <div className="field-group">
            <label htmlFor="body">{t('memory.bodyLabel')}</label>
            <textarea
              id="body"
              name="body"
              rows={5}
              placeholder={t('memory.bodyPlaceholder')}
            />
          </div>
          <div className="field-group">
            <label htmlFor="happenedOn">{t('memory.dateLabel')}</label>
            <input id="happenedOn" name="happenedOn" type="date" />
            <p className="field-help">{t('memory.dateHelp')}</p>
          </div>
          <AttachmentDraftField
            controller={attachments}
            inputId="memory-images"
            label={t('memory.photoLabel')}
          />

          <div
            className="sharing-note"
            role="note"
            aria-label={t('memory.visibilityAria')}
          >
            <span className="sharing-icon" aria-hidden="true">
              ♥
            </span>
            <div>
              <strong>{t('memory.sharedTitle')}</strong>
              <p>{t('memory.sharedBody')}</p>
            </div>
          </div>

          <div className="form-actions">
            <Link className="button-link secondary-link" to={appRoutePath('story')}>
              {t('common.cancel')}
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending || attachments.hasPending}
            >
              {mutation.isPending ? t('memory.saving') : t('memory.save')}
            </button>
          </div>
        </form>
        {mutation.isPending ? (
          <p className="status" role="status" aria-live="polite">
            {t('memory.processing')}
          </p>
        ) : null}
        {mutation.error ? <ProblemState error={mutation.error} /> : null}
      </section>
    </div>
  );
}
