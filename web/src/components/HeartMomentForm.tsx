import type { TFunction } from 'i18next';
import type { FormEvent } from 'react';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { HeartEmotion } from '../api/generated/models/HeartEmotion';
import type { HeartMomentDetail } from '../api/generated/models/HeartMomentDetail';
import { memoryDateInputValue } from '../client/memoryProduct';
import type { useAttachmentDrafts } from '../client/useAttachmentDrafts';
import { useTranslation } from '../i18n';
import { AttachmentDraftField } from './AttachmentDraftField';

export function heartEmotionLabel(
  emotion: HeartEmotion,
  t: TFunction,
): string {
  return t(`m5Product.heart.emotions.${emotion.toLowerCase()}`);
}

export function HeartMomentForm({
  initial,
  submitLabel,
  submitting,
  attachments,
  onSubmit,
}: {
  initial?: HeartMomentDetail;
  submitLabel: string;
  submitting: boolean;
  attachments: ReturnType<typeof useAttachmentDrafts>;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const { t } = useTranslation();
  return (
    <form className="form-grid" onSubmit={onSubmit}>
      <div className="field-group">
        <label htmlFor="heart-text">{t('m5Product.heart.textLabel')}</label>
        <textarea
          id="heart-text"
          name="text"
          rows={5}
          required
          defaultValue={initial?.text ?? ''}
          placeholder={t('m5Product.heart.textPlaceholder')}
        />
      </div>
      <div className="field-group">
        <label htmlFor="heart-emotion">{t('m5Product.heart.emotionLabel')}</label>
        <select
          id="heart-emotion"
          name="emotion"
          defaultValue={initial?.emotion ?? HeartEmotion.LOVED}
        >
          {Object.values(HeartEmotion).map((emotion) => (
            <option key={emotion} value={emotion}>
              {heartEmotionLabel(emotion, t)}
            </option>
          ))}
        </select>
      </div>
      <div className="field-group">
        <label htmlFor="heart-date">{t('m5Product.heart.dateLabel')}</label>
        <input
          id="heart-date"
          name="happenedOn"
          type="date"
          required
          defaultValue={
            initial ? memoryDateInputValue(initial.happenedOn) : undefined
          }
        />
      </div>
      {!initial ? (
        <fieldset className="visibility-fieldset">
          <legend>{t('m5Product.heart.visibilityLabel')}</legend>
          <label>
            <input
              type="radio"
              name="visibility"
              value={ContentVisibility.SHARED}
              defaultChecked
            />
            <span>{t('m5Product.heart.sharedOption')}</span>
          </label>
          <label>
            <input
              type="radio"
              name="visibility"
              value={ContentVisibility.PRIVATE}
            />
            <span>{t('m5Product.heart.privateOption')}</span>
          </label>
        </fieldset>
      ) : null}
      <AttachmentDraftField
        controller={attachments}
        inputId="heart-photo"
        label={
          initial?.attachment
            ? t('m5Product.heart.replacePhoto')
            : t('m5Product.heart.photoLabel')
        }
        maxFiles={1}
      />
      <div className="form-actions">
        <button type="submit" disabled={submitting || attachments.hasPending}>
          {submitting ? t('m5Product.common.saving') : submitLabel}
        </button>
      </div>
    </form>
  );
}
