import { useInfiniteQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { ChapterDetail } from '../api/generated/models/ChapterDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  appRoutePath,
  chapterDetailPath,
  CHAPTER_CREATE_ROUTE,
} from '../client/routes';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { resolvedLocale, useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './SharedPlanningPages.css';

const PAGE_SIZE = 20;

type PageShape<T> = { items: T[]; nextCursor: string | null };

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

function nextCursor<T>(page: PageShape<T>): string | undefined {
  return page.nextCursor ?? undefined;
}

function formatDate(value: Date | null): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(value);
}

export function ChaptersOverviewPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();

  const chapters = useInfiniteQuery({
    queryKey: ['m5-s3', 'chapters', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.chapters.listChapters({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<ChapterDetail>,
    retry: false,
  });

  const chapterItems = chapters.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <div className="page planning-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('m5s3.common.backToStory')}
          </Link>
        }
        eyebrow={t('navigation.story')}
        title={t('m5s3.chapter.heading')}
        description={t('m5s3.chapter.intro')}
        action={
          <Link className="button-link" to={CHAPTER_CREATE_ROUTE}>
            {t('m5s3.chapter.create')}
          </Link>
        }
      />

      <section className="planning-subsection">
        {chapters.isLoading ? (
          <UiState kind="loading" title={t('states.loading.title')} />
        ) : null}
        {chapters.error ? (
          <ProblemState
            error={chapters.error}
            onRetry={() => void chapters.refetch()}
          />
        ) : null}

        {chapterItems.length === 0 && !chapters.isLoading && !chapters.error ? (
          <p className="planning-empty">{t('m5s3.common.empty')}</p>
        ) : (
          <ul className="planning-list">
            {chapterItems.map((chapter) => (
              <li className="planning-card-item" key={chapter.id}>
                <Link
                  className="planning-card planning-card-link"
                  to={chapterDetailPath(chapter.id)}
                >
                  <div className="planning-card-copy">
                    <h3>{chapter.title}</h3>
                    {formatDate(chapter.startOn) ? (
                      <p className="planning-meta">
                        {formatDate(chapter.startOn)}
                      </p>
                    ) : null}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}

        {chapters.hasNextPage ? (
          <button
            type="button"
            className="tertiary compact-action"
            onClick={() => void chapters.fetchNextPage()}
            disabled={chapters.isFetchingNextPage}
          >
            {chapters.isFetchingNextPage
              ? t('m5s3.common.loadingMore')
              : t('m5s3.common.loadMore')}
          </button>
        ) : null}
      </section>
    </div>
  );
}
