import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import type { HeartMomentDetail } from '../api/generated/models/HeartMomentDetail';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  appRoutePath,
  heartMomentEditPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { CommentsSection } from './CommentsSection';
import { heartEmotionLabel } from './HeartMomentForm';
import { MemoryPreview } from './MemoryPreview';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';

function formatDate(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(value);
}

export function HeartMomentDetailView({
  heartMoment,
  apis,
  spaceId,
  currentAccountId,
  loadHeartMomentImage,
  visibilityPending,
  visibilityError,
  onVisibilityChange,
  deletePending,
  deleteError,
  onDelete,
  onRetry,
}: {
  heartMoment: HeartMomentDetail;
  apis: ReferenceApis;
  spaceId: string;
  currentAccountId: string;
  loadHeartMomentImage: (
    heartMomentId: string,
    attachmentId: string,
  ) => Promise<string>;
  visibilityPending: boolean;
  visibilityError: unknown;
  onVisibilityChange: (visibility: ContentVisibility) => void;
  deletePending: boolean;
  deleteError: unknown;
  onDelete: () => void;
  onRetry: () => void;
}) {
  const { t } = useTranslation();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [visibilityTarget, setVisibilityTarget] =
    useState<ContentVisibility | null>(null);
  const privateMoment = heartMoment.visibility === ContentVisibility.PRIVATE;
  const targetVisibility = privateMoment
    ? ContentVisibility.SHARED
    : ContentVisibility.PRIVATE;

  return (
    <div className="page m5-product-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('heartMoments')}>
            {t('m5Product.heart.backToList')}
          </Link>
        }
        eyebrow={t('m5Product.heart.detailEyebrow')}
        title={heartEmotionLabel(heartMoment.emotion, t)}
        description={
          privateMoment
            ? t('m5Product.heart.privateDetailIntro')
            : t('m5Product.heart.sharedDetailIntro')
        }
        action={
          heartMoment.capabilities.canEdit ? (
            <Link
              className="button-link secondary-link"
              to={heartMomentEditPath(heartMoment.id)}
            >
              {t('m5Product.heart.edit')}
            </Link>
          ) : undefined
        }
      />

      <article className="story-surface memory-detail-card">
        <div className="story-card-meta">
          <span className="kind-badge">
            {privateMoment
              ? t('m5Product.heart.privateBadge')
              : t('m5Product.heart.sharedBadge')}
          </span>
          <time dateTime={heartMoment.happenedOn.toISOString().slice(0, 10)}>
            {formatDate(heartMoment.happenedOn)}
          </time>
        </div>
        <p className="heart-moment-text">{heartMoment.text}</p>
        <p className="muted">
          {t('m5Product.heart.byAuthor', {
            author: heartMoment.author.displayName,
          })}
        </p>

        {heartMoment.attachment ? (
          <div className="heart-moment-photo">
            <MemoryPreview
              memoryId={heartMoment.id}
              attachmentId={heartMoment.attachment.id}
              loadImage={loadHeartMomentImage}
            />
          </div>
        ) : null}

        {heartMoment.capabilities.canEdit ? (
          <section className="visibility-control" aria-labelledby="visibility-heading">
            <h2 id="visibility-heading">{t('m5Product.heart.visibilityHeading')}</h2>
            <p>
              {privateMoment
                ? t('m5Product.heart.privateVisibilityBody')
                : t('m5Product.heart.sharedVisibilityBody')}
            </p>
            {visibilityTarget === targetVisibility ? (
              <div className="memory-delete-confirmation" role="alert">
                <p>
                  {targetVisibility === ContentVisibility.PRIVATE
                    ? t('m5Product.heart.makePrivateWarning')
                    : t('m5Product.heart.makeSharedWarning')}
                </p>
                <div className="memory-actions">
                  <button
                    type="button"
                    className="tertiary"
                    onClick={() => setVisibilityTarget(null)}
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="button"
                    disabled={visibilityPending}
                    onClick={() => {
                      onVisibilityChange(targetVisibility);
                      setVisibilityTarget(null);
                    }}
                  >
                    {t('m5Product.heart.confirmVisibility')}
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                className="secondary"
                onClick={() => setVisibilityTarget(targetVisibility)}
              >
                {privateMoment
                  ? t('m5Product.heart.makeShared')
                  : t('m5Product.heart.makePrivate')}
              </button>
            )}
            {visibilityError ? (
              <ProblemState error={visibilityError} onRetry={onRetry} />
            ) : null}
          </section>
        ) : null}

        <CommentsSection
          apis={apis}
          spaceId={spaceId}
          parentKind="HEART_MOMENT"
          parentId={heartMoment.id}
          parentVisibility={heartMoment.visibility}
          canComment={heartMoment.capabilities.canComment}
          currentAccountId={currentAccountId}
        />

        {heartMoment.capabilities.canDelete ? (
          <section className="memory-danger-zone">
            {!confirmDelete ? (
              <button
                type="button"
                className="secondary"
                onClick={() => setConfirmDelete(true)}
              >
                {t('m5Product.heart.delete')}
              </button>
            ) : (
              <div className="memory-delete-confirmation" role="alert">
                <p>{t('m5Product.heart.deleteWarning')}</p>
                <div className="memory-actions">
                  <button
                    type="button"
                    className="tertiary"
                    onClick={() => setConfirmDelete(false)}
                  >
                    {t('common.cancel')}
                  </button>
                  <button type="button" disabled={deletePending} onClick={onDelete}>
                    {t('m5Product.heart.confirmDelete')}
                  </button>
                </div>
              </div>
            )}
            {deleteError ? (
              <ProblemState error={deleteError} onRetry={onRetry} />
            ) : null}
          </section>
        ) : null}
      </article>
    </div>
  );
}
