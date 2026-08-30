import { type FormEvent, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { StoryKind } from '../api/generated/models/StoryKind';
import { StoryOrder } from '../api/generated/models/StoryOrder';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  appRoutePath,
  HEART_MOMENT_CREATE_ROUTE,
  MILESTONE_CREATE_ROUTE,
} from '../client/routes';
import {
  InvalidStoryYearError,
  storyTimelineRequest,
  type StoryFilters,
} from '../client/storyFilters';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { StoryList } from './StoryList';
import { UiState } from './UiState';

const DEFAULT_FILTERS: StoryFilters = {
  kinds: [],
  year: '',
  order: StoryOrder.DESC,
};

function toggleKind(kinds: StoryKind[], kind: StoryKind): StoryKind[] {
  return kinds.includes(kind)
    ? kinds.filter((candidate) => candidate !== kind)
    : [...kinds, kind];
}

export function StoryProductPage({
  apis,
  spaceId,
  loadMemoryImage,
}: {
  apis: ReferenceApis;
  spaceId: string;
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<StoryFilters>(DEFAULT_FILTERS);
  const [filters, setFilters] = useState<StoryFilters>(DEFAULT_FILTERS);
  const [filterError, setFilterError] = useState<string | null>(null);

  const storyQuery = useInfiniteQuery({
    queryKey: [
      'story',
      spaceId,
      filters.kinds.join(','),
      filters.year,
      filters.order,
    ],
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) => {
      try {
        return await apis.story.getStoryTimeline(
          storyTimelineRequest(spaceId, filters, pageParam),
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor || undefined,
    retry: false,
  });

  const items = storyQuery.data?.pages.flatMap((page) => page.items) ?? [];

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      storyTimelineRequest(spaceId, draft);
      setFilterError(null);
      setFilters({ ...draft, kinds: [...draft.kinds] });
    } catch (error) {
      if (error instanceof InvalidStoryYearError) {
        setFilterError(t('m5Product.story.invalidYear'));
        return;
      }
      throw error;
    }
  }

  function resetFilters() {
    setDraft(DEFAULT_FILTERS);
    setFilters(DEFAULT_FILTERS);
    setFilterError(null);
  }

  return (
    <div className="page story-page">
      <PageHeader
        eyebrow={t('story.eyebrow')}
        title={t('story.title')}
        description={t('story.intro')}
        className="story-heading"
        action={
          <div className="story-create-actions">
            <Link
              className="button-link primary-action"
              to={appRoutePath('memoryCreate')}
            >
              {t('m5Product.story.addMemory')}
            </Link>
            <Link
              className="button-link secondary-link"
              to={HEART_MOMENT_CREATE_ROUTE}
            >
              {t('m5Product.story.addHeartMoment')}
            </Link>
            <Link
              className="button-link secondary-link"
              to={MILESTONE_CREATE_ROUTE}
            >
              {t('m5Product.story.addMilestone')}
            </Link>
          </div>
        }
      />

      <section
        className="story-filter-card"
        aria-labelledby="story-filter-heading"
      >
        <div className="section-head">
          <div>
            <p className="section-kicker">
              {t('m5Product.story.filterKicker')}
            </p>
            <h2 id="story-filter-heading">
              {t('m5Product.story.filterHeading')}
            </h2>
          </div>
        </div>
        <form className="story-filter-form" onSubmit={applyFilters}>
          <fieldset>
            <legend>{t('m5Product.story.kindLegend')}</legend>
            <div className="filter-checkboxes">
              {[
                [StoryKind.MEMORY, t('story.kind.memory')],
                [StoryKind.HEART_MOMENT, t('story.kind.heartMoment')],
                [StoryKind.MILESTONE, t('story.kind.milestone')],
              ].map(([kind, label]) => (
                <label key={kind}>
                  <input
                    type="checkbox"
                    checked={draft.kinds.includes(kind as StoryKind)}
                    onChange={() =>
                      setDraft((current) => ({
                        ...current,
                        kinds: toggleKind(current.kinds, kind as StoryKind),
                      }))
                    }
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="field-group compact-field">
            <label htmlFor="story-year">{t('m5Product.story.yearLabel')}</label>
            <input
              id="story-year"
              inputMode="numeric"
              value={draft.year}
              placeholder={t('m5Product.story.yearPlaceholder')}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  year: event.currentTarget.value,
                }))
              }
            />
          </div>

          <div className="field-group compact-field">
            <label htmlFor="story-order">
              {t('m5Product.story.orderLabel')}
            </label>
            <select
              id="story-order"
              value={draft.order}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  order: event.currentTarget.value as StoryOrder,
                }))
              }
            >
              <option value={StoryOrder.DESC}>
                {t('m5Product.story.orderNewest')}
              </option>
              <option value={StoryOrder.ASC}>
                {t('m5Product.story.orderOldest')}
              </option>
            </select>
          </div>

          <div className="story-filter-actions">
            <button type="submit">{t('m5Product.story.applyFilters')}</button>
            <button type="button" className="tertiary" onClick={resetFilters}>
              {t('m5Product.story.resetFilters')}
            </button>
          </div>
        </form>
        {filterError ? (
          <p className="inline-message" role="alert">
            {filterError}
          </p>
        ) : null}
      </section>

      <section className="story-surface" aria-labelledby="timeline-heading">
        <div className="section-head">
          <div>
            <p className="section-kicker">{t('story.timelineKicker')}</p>
            <h2 id="timeline-heading">{t('story.timelineHeading')}</h2>
          </div>
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => storyQuery.refetch()}
            disabled={storyQuery.isFetching}
          >
            {storyQuery.isFetching && !storyQuery.isFetchingNextPage
              ? t('common.refreshing')
              : t('common.refresh')}
          </button>
        </div>

        {storyQuery.isLoading ? (
          <UiState kind="loading" title={t('story.loadingAria')} />
        ) : null}
        {storyQuery.error ? (
          <ProblemState
            error={storyQuery.error}
            onRetry={() => void storyQuery.refetch()}
          />
        ) : null}
        {!storyQuery.error && !storyQuery.isLoading ? (
          <StoryList items={items} loadMemoryImage={loadMemoryImage} />
        ) : null}

        {storyQuery.hasNextPage ? (
          <div className="pagination-actions">
            <button
              type="button"
              className="secondary"
              disabled={storyQuery.isFetchingNextPage}
              onClick={() => void storyQuery.fetchNextPage()}
            >
              {storyQuery.isFetchingNextPage
                ? t('m5Product.story.loadingMore')
                : t('m5Product.story.loadMore')}
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
