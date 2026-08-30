import type { AttachmentDraft } from '../client/attachmentDraftState';
import { useTranslation } from '../i18n';

export interface AttachmentDraftController {
  items: AttachmentDraft[];
  addFiles: (files: FileList | null) => void;
  remove: (id: string) => void;
  retry: (draft: AttachmentDraft) => void;
  readyIds: string[];
  hasPending: boolean;
}

export function AttachmentDraftField({
  controller,
  inputId,
  label,
  maxFiles,
}: {
  controller: AttachmentDraftController;
  inputId: string;
  label: string;
  maxFiles?: number;
}) {
  const { t } = useTranslation();
  const atLimit = maxFiles !== undefined && controller.items.length >= maxFiles;

  return (
    <div className="field-group">
      <label htmlFor={inputId}>{label}</label>
      <input
        className="visually-hidden-input"
        id={inputId}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
        multiple={maxFiles !== 1}
        disabled={atLimit}
        onChange={(event) => {
          controller.addFiles(event.currentTarget.files);
          event.currentTarget.value = '';
        }}
      />
      {!atLimit ? (
        <label className="file-picker" htmlFor={inputId}>
          <span className="file-picker-icon" aria-hidden="true">
            ＋
          </span>
          <span>
            <strong>
              {controller.items.length
                ? t('m5Product.upload.addMore')
                : t('m5Product.upload.select')}
            </strong>
            <small>{t('m5Product.upload.formats')}</small>
          </span>
        </label>
      ) : (
        <p className="field-help">{t('m5Product.upload.limitReached')}</p>
      )}

      {controller.items.length > 0 ? (
        <ul
          className="attachment-draft-list"
          aria-label={t('m5Product.upload.draftsAria')}
        >
          {controller.items.map((attachment) => {
            const statusText =
              attachment.status === 'uploading'
                ? t('m5Product.upload.uploading')
                : attachment.status === 'validating'
                  ? t('m5Product.upload.validating')
                  : attachment.status === 'ready'
                    ? t('m5Product.upload.ready')
                    : t('m5Product.upload.failed');
            const pending =
              attachment.status === 'uploading' ||
              attachment.status === 'validating';

            return (
              <li className="attachment-draft-item" key={attachment.id}>
                <div className="attachment-preview-wrap">
                  <img
                    className="attachment-preview"
                    src={attachment.previewUrl}
                    alt={t('m5Product.upload.previewAlt', {
                      name: attachment.file.name,
                    })}
                  />
                  <span className="attachment-preview-label">
                    {t('m5Product.upload.localPreview')}
                  </span>
                </div>
                <div className="attachment-draft-meta">
                  <strong>{attachment.file.name}</strong>
                  <span
                    className={`attachment-status attachment-status-${attachment.status}`}
                    role={attachment.status === 'failed' ? 'alert' : 'status'}
                    aria-live="polite"
                  >
                    {statusText}
                  </span>
                  {pending ? (
                    <progress
                      className="attachment-progress"
                      aria-label={statusText}
                    />
                  ) : null}
                  {attachment.status === 'failed' ? (
                    <small className="attachment-draft-error">
                      {attachment.error}
                    </small>
                  ) : null}
                </div>
                <div className="attachment-draft-actions">
                  {attachment.status === 'failed' ? (
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => controller.retry(attachment)}
                    >
                      {t('common.retry')}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="tertiary"
                    onClick={() => controller.remove(attachment.id)}
                  >
                    {pending
                      ? t('m5Product.upload.cancel')
                      : t('m5Product.upload.remove')}
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}

      {controller.hasPending ? (
        <p className="field-help" role="status" aria-live="polite">
          {t('m5Product.upload.pendingSave')}
        </p>
      ) : null}
    </div>
  );
}
