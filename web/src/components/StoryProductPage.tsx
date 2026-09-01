import type { FormEvent } from 'react';
import { useEffect, useMemo } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useLocation, useSearchParams } from 'react-router-dom';
import {
  StoryKind,
  type StoryKind as StoryKindValue,
} from '../api/generated/models/StoryKind';
import {
  StoryOrder,
  type StoryOrder as StoryOrderValue,
} from '../api/generated/models/StoryOrder';
import {
  StoryPageFromJSON,
  StoryPageToJSON,
} from '../api/generated/models/StoryPage';
import {
  loadProductWithReadCache,
  saveProductReadCacheEntry,
  type ProductReadResult,
} from '../client/productReadCache';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  aggregateStoryPages,
  parseStoryFilters,
  storyCacheResourceId,
  storyFiltersToSearch,
  storyRequest,
  type StoryFilters,
} from '../client/storyProduct';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { StoryList } from './StoryList';
import { UiState } from './UiState';

function selectedKind(value: FormDataEntryValue | null): StoryKindValue | null {
  const text = String(value ?? '');
  return Object.values(StoryKind).includes(text as StoryKindValue)
    ? (text as StoryKindValue)
    : null;
}

function selectedOrder(value: FormDataEntryValue | null): StoryOrderValue {
  return String(value ?? '') === StoryOrder.ASC
    ? StoryOrder.ASC
    : StoryOrder.DESC;
}

function selectedYear(value: FormDataEntryValue | null): number | null {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const year = Number(text);
  return Number.isInteger(year) && year > 0 ? year : null;
}

export function StoryProductPage({
  apis,
  accountId,
  spaceId,
  loadMemoryImage,
}: {
  apis: ReferenceApis;
  accountId: string;
  spaceId: string;
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const location = useLocation();
  const saved = Boolean((location.state as { saved?: boolean } | null)?.saved);
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(
    () => parseStoryFilters(searchParams),
    [searchParams],
  );
  const cacheResourceId = useMemo(
    () => storyCacheResourceId(filters),
    [filters],
  );

  const storyQuery = useInfiniteQuery({
    queryKey: ['story', spaceId, cacheResourceId],
    initialPageParam: null as string | null,
    queryFn: async ({
      pageParam,
    }): Promise<ProductReadResult<ReturnType<typeof StoryPageFromJSON>>> => {
      if (pageParam === null) {
        return loadProductWithReadCache({
          accountId,
          spaceId,
          kind: 'story',
          resourceId: cacheResourceId,
          load: () =>
            apis.story.getStoryTimeline(storyRequest(spaceId, filters, null)),
          serialize: StoryPageToJSON,
          deserialize: (payload) => StoryPageFromJSON(payload),
        });
      }

      try {
        const value = await apis.story.getStoryTimeline(
          storyRequest(spaceId, filters, pageParam),
        );
        return { value, source: 'network' };
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.source !== 'network') return undefined;
      return lastPage.value.hasMore && lastPage.value.nextCursor
        ? lastPage.value.nextCursor
        : undefined;
    },
    retry: false,
  });

  const combinedStory = useMemo(() => {
    if (!storyQuery.data) return null;
    return aggregateStoryPages(storyQuery.data.pages.map((page) => page.value));
  }, [storyQuery.data]);
  const allPagesFromNetwork =
    storyQuery.data?.pages.every((page) => page.source === 'network') ?? false;
  const offline = storyQuery.data?.pages[0]?.source === 'cache';

  useEffect(() => {
    if (!combinedStory || !allPagesFromNetwork) return;
    void saveProductReadCacheEntry({
      accountId,
      spaceId,
      kind: 'story',
      resourceId: cacheResourceId,
      value: combinedStory,
      serialize: StoryPageToJSON,
    });
  }, [accountId, allPagesFromNetwork, cacheResourceId, combinedStory, spaceId]);

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const nextFilters: StoryFilters = {
      kind: selectedKind(data.get('type')),
      year: selectedYear(data.get('year')),
      order: selectedOrder(data.get('order')),
    };
    setSearchParams(storyFiltersToSearch(nextFilters), { replace: true });
  }

  return (
    <div className="page story-page">
      {saved ? (
        <div className="inline-message inline-message-success" role="status">
          <strong>{t('story.savedTitle')}</strong>
          <span>{t('story.savedBody')}</span>
        </div>
      ) : null}
      {offline ? (
        <div className="inline-message" role="status">
          {t('offlineCache.banner')}
        </div>
      ) : null}

      <PageHeader
        eyebrow={t('story.eyebrow')}
        title={t('story.title')}
        description={t('story.intro')}
      />

      <div className="layout-split layout-split-lead-rail">
        <aside
          className="layout-rail layout-rail-sticky"
          aria-label={t('storyFilters.aria')}
        >
          <form
            className="layout-panel story-filter-panel"
            onSubmit={applyFilters}
            key={cacheResourceId}
            aria-label={t('storyFilters.aria')}
          >
            <h2 className="rail-heading">{t('storyFilters.heading')}</h2>
            <div className="field-group">
              <label htmlFor="story-filter-type">
                {t('storyFilters.type')}
              </label>
              <select
                id="story-filter-type"
                name="type"
                defaultValue={filters.kind ?? ''}
              >
                <option value="">{t('storyFilters.allTypes')}</option>
                <option value={StoryKind.MEMORY}>
                  {t('story.kind.memory')}
                </option>
                <option value={StoryKind.HEART_MOMENT}>
                  {t('story.kind.heartMoment')}
                </option>
                <option value={StoryKind.MILESTONE}>
                  {t('story.kind.milestone')}
                </option>
              </select>
            </div>
            <div className="field-group">
              <label htmlFor="story-filter-year">
                {t('storyFilters.year')}
              </label>
              <input
                id="story-filter-year"
                name="year"
                type="number"
                inputMode="numeric"
                min={1}
                defaultValue={filters.year ?? ''}
                placeholder={t('storyFilters.anyYear')}
              />
            </div>
            <div className="field-group">
              <label htmlFor="story-filter-order">
                {t('storyFilters.order')}
              </label>
              <select
                id="story-filter-order"
                name="order"
                defaultValue={filters.order}
              >
                <option value={StoryOrder.DESC}>
                  {t('storyFilters.newest')}
                </option>
                <option value={StoryOrder.ASC}>
                  {t('storyFilters.oldest')}
                </option>
              </select>
            </div>
            <div className="story-filter-actions">
              <button type="submit">{t('storyFilters.apply')}</button>
              <button
                type="button"
                className="tertiary"
                onClick={() => setSearchParams({}, { replace: true })}
              >
                {t('storyFilters.reset')}
              </button>
            </div>
          </form>
        </aside>

        <div className="layout-main">
          <section className="story-surface" aria-labelledby="timeline-heading">
            <div className="section-head">
              <div>
                <p className="section-kicker">{t('story.timelineKicker')}</p>
                <h2 id="timeline-heading">{t('story.timelineHeading')}</h2>
              </div>
              <button
                type="button"
                className="secondary compact-action"
                onClick={() => void storyQuery.refetch()}
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
            {combinedStory ? (
              <StoryList
                items={combinedStory.items}
                loadMemoryImage={loadMemoryImage}
              />
            ) : null}
            {storyQuery.hasNextPage ? (
              <div className="story-pagination">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => void storyQuery.fetchNextPage()}
                  disabled={storyQuery.isFetchingNextPage}
                >
                  {storyQuery.isFetchingNextPage
                    ? t('storyFilters.loadingMore')
                    : t('storyFilters.loadMore')}
                </button>
              </div>
            ) : null}
          </section>
        </div>
      </div>
    </div>
  );
}
