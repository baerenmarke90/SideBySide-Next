import { useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  HEART_MOMENT_CREATE_ROUTE,
  heartMomentDetailPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

function formatDate(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(value);
}

export function HeartMomentsPage({
  apis,
  spaceId,
}: {
  apis: ReferenceApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const [visibility, setVisibility] = useState<ContentVisibility>(
    ContentVisibility.SHARED,
  );

  const query = useInfiniteQuery({
    queryKey: ['heart-moments', spaceId, visibility],
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) => {
      try {
        return await apis.heartMoments.listHeartMoments({
          spaceId,
          visibility,
          cursor: pageParam || undefined,
          limit: 25,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor || undefined,
    retry: false,
  });

  const items = query.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <div className="page m5-product-page">
      <PageHeader
        eyebrow={t('m5Product.heart.listEyebrow')}
        title={t('m5Product.heart.listTitle')}
        description={t('m5Product.heart.listIntro')}
        action={
          <Link
            className="button-link primary-action"
            to={HEART_MOMENT_CREATE_ROUTE}
          >
            {t('m5Product.heart.create')}
          </Link>
        }
      />

      <div
        className="visibility-tabs"
        role="tablist"
        aria-label={t('m5Product.heart.visibilityTabs')}
      >
        <button
          type="button"
          role="tab"
          aria-selected={visibility === ContentVisibility.SHARED}
          className={
            visibility === ContentVisibility.SHARED ? 'active' : 'secondary'
          }
          onClick={() => setVisibility(ContentVisibility.SHARED)}
        >
          {t('m5Product.heart.sharedTab')}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={visibility === ContentVisibility.PRIVATE}
          className={
            visibility === ContentVisibility.PRIVATE ? 'active' : 'secondary'
          }
          onClick={() => setVisibility(ContentVisibility.PRIVATE)}
        >
          {t('m5Product.heart.privateTab')}
        </button>
      </div>

      <section className="story-surface">
        {query.isLoading ? (
          <UiState kind="loading" title={t('m5Product.heart.loadingList')} />
        ) : null}
        {query.error ? (
          <ProblemState
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        ) : null}
        {!query.isLoading && !query.error && items.length === 0 ? (
          <UiState
            kind="empty"
            title={
              visibility === ContentVisibility.PRIVATE
                ? t('m5Product.heart.privateEmptyTitle')
                : t('m5Product.heart.sharedEmptyTitle')
            }
            body={t('m5Product.heart.emptyBody')}
          />
        ) : null}

        {items.length > 0 ? (
          <ol className="heart-moment-list">
            {items.map((heartMoment) => (
              <li key={heartMoment.id}>
                <article className="heart-moment-list-card">
                  <div className="story-card-meta">
                    <span className="kind-badge">
                      {heartMoment.visibility === ContentVisibility.PRIVATE
                        ? t('m5Product.heart.privateBadge')
                        : t('m5Product.heart.sharedBadge')}
                    </span>
                    <time
                      dateTime={heartMoment.happenedOn
                        .toISOString()
                        .slice(0, 10)}
                    >
                      {formatDate(heartMoment.happenedOn)}
                    </time>
                  </div>
                  <p>{heartMoment.text}</p>
                  <div className="story-card-footer">
                    <span>{heartMoment.author.displayName}</span>
                    <Link
                      className="story-memory-link"
                      to={heartMomentDetailPath(heartMoment.id)}
                    >
                      {t('m5Product.heart.open')}
                    </Link>
                  </div>
                </article>
              </li>
            ))}
          </ol>
        ) : null}

        {query.hasNextPage ? (
          <div className="pagination-actions">
            <button
              type="button"
              className="secondary"
              disabled={query.isFetchingNextPage}
              onClick={() => void query.fetchNextPage()}
            >
              {query.isFetchingNextPage
                ? t('m5Product.common.loadingMore')
                : t('m5Product.common.loadMore')}
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
