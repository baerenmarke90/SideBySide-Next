import type { FormEvent } from 'react';
import { useEffect, useMemo } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
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
import {
  heartMomentDetailPath,
  memoryDetailPath,
  milestoneDetailPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { MemoryPreview } from './MemoryPreview';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { StoryList } from './StoryList';
import {
  formatStoryDate,
  storyItemKey,
  storyItemPresentation,
} from './storyPresentation';
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

  const activeView = useMemo(() => {
    const tab = searchParams.get('tab');
    if (tab === 'timeline') return 'timeline';
    if (tab === 'discover') return 'discover';
    if (filters.kind || filters.year || filters.order !== StoryOrder.DESC) {
      return 'timeline';
    }
    return 'discover';
  }, [searchParams, filters]);

  function setView(view: 'discover' | 'timeline') {
    const next = new URLSearchParams(searchParams);
    next.set('tab', view);
    setSearchParams(next, { replace: true });
  }

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const nextFilters: StoryFilters = {
      kind: selectedKind(data.get('type')),
      year: selectedYear(data.get('year')),
      order: selectedOrder(data.get('order')),
    };
    const nextSearch = storyFiltersToSearch(nextFilters);
    nextSearch.set('tab', 'timeline');
    setSearchParams(nextSearch, { replace: true });
  }

  const items = useMemo(() => combinedStory?.items ?? [], [combinedStory]);
  const locale = resolvedLocale();

  const memoriesWithMedia = useMemo(
    () =>
      items.filter(
        (item) => item.kind === 'MEMORY' && item.memory.attachments.length > 0,
      ),
    [items],
  );
  const heartMoments = useMemo(
    () => items.filter((item) => item.kind === 'HEART_MOMENT'),
    [items],
  );
  const milestones = useMemo(
    () => items.filter((item) => item.kind === 'MILESTONE'),
    [items],
  );
  const featuredItem = useMemo(
    () => memoriesWithMedia[0] ?? heartMoments[0] ?? items[0],
    [memoriesWithMedia, heartMoments, items],
  );
  const uniqueYears = useMemo(() => {
    const years = new Set<number>();
    for (const item of items) {
      years.add(item.effectiveDate.getFullYear());
    }
    return Array.from(years).sort((a, b) => b - a);
  }, [items]);

  const featuredMedia =
    featuredItem?.kind === 'MEMORY'
      ? featuredItem.memory.attachments[0]
      : undefined;
  const featuredPresentation = featuredItem
    ? storyItemPresentation(featuredItem, t)
    : null;
  const featuredPath = featuredItem
    ? featuredItem.kind === 'MEMORY'
      ? memoryDetailPath(featuredItem.memory.id)
      : featuredItem.kind === 'HEART_MOMENT'
        ? heartMomentDetailPath(featuredItem.heartMoment.id)
        : milestoneDetailPath(featuredItem.milestone.id)
    : '';

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

      <div className="momente-tabs-container sbs-motion-reveal">
        <div
          className="momente-tabs"
          role="tablist"
          aria-label={t('story.viewToggleAria')}
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeView === 'discover'}
            className={`momente-tab-btn ${activeView === 'discover' ? 'active' : ''}`}
            onClick={() => setView('discover')}
          >
            <span aria-hidden="true">✨</span> {t('story.tabDiscover')}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeView === 'timeline'}
            className={`momente-tab-btn ${activeView === 'timeline' ? 'active' : ''}`}
            onClick={() => setView('timeline')}
          >
            <span aria-hidden="true">📖</span> {t('story.tabTimeline')}
          </button>
        </div>
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

      {combinedStory && items.length === 0 ? (
        <div className="new-space-experience sbs-motion-reveal">
          <div className="new-space-mark" aria-hidden="true">
            ❤️
          </div>
          <h2 className="new-space-title">{t('story.emptyTitle')}</h2>
          <p className="new-space-body">{t('story.emptyBody')}</p>
          <div className="new-space-actions">
            <Link
              to="/story/memories/new"
              className="button-link primary new-space-cta"
            >
              {t('story.emptyAction')}
            </Link>
          </div>
        </div>
      ) : combinedStory && activeView === 'discover' ? (
        <div className="momente-discover-page sbs-motion-reveal">
          {/* 1. Featured Editorial Highlight */}
          {featuredItem && featuredPresentation ? (
            <article className="momente-hero-highlight">
              <Link
                to={featuredPath}
                className={`momente-hero-link ${featuredMedia ? 'has-media' : ''}`}
                aria-label={`${t('story.featuredHighlight')}: ${featuredPresentation.title}`}
              >
                {featuredMedia ? (
                  <div className="momente-hero-media">
                    <MemoryPreview
                      memoryId={
                        featuredItem.kind === 'MEMORY'
                          ? featuredItem.memory.id
                          : ''
                      }
                      attachmentId={featuredMedia.id}
                      loadImage={loadMemoryImage}
                    />
                  </div>
                ) : null}
                <div className="momente-hero-body">
                  <span className="momente-hero-kicker">
                    ✨ {t('story.featuredKicker')}
                  </span>
                  {featuredItem.kind === 'HEART_MOMENT' ? (
                    <blockquote className="momente-hero-quote">
                      "{featuredPresentation.title}"
                    </blockquote>
                  ) : (
                    <h3 className="momente-hero-title">
                      {featuredPresentation.title}
                    </h3>
                  )}
                  <div className="momente-hero-meta">
                    <time
                      dateTime={featuredItem.effectiveDate
                        .toISOString()
                        .slice(0, 10)}
                    >
                      {formatStoryDate(featuredItem.effectiveDate, locale)}
                    </time>
                    {featuredPresentation.author ? (
                      <span>
                        {t('story.byAuthor', {
                          author: featuredPresentation.author,
                        })}
                      </span>
                    ) : null}
                  </div>
                </div>
              </Link>
            </article>
          ) : null}

          {/* 2. Horizontal Visual Memory Stream (#492) */}
          <section
            className="momente-stream-section"
            aria-labelledby="momente-stream-heading"
          >
            <div className="momente-section-header">
              <div>
                <h3
                  id="momente-stream-heading"
                  className="momente-section-title"
                >
                  {t('story.discoverHeading')}
                </h3>
                <p className="momente-section-subhead">
                  {t('story.discoverSubhead')}
                </p>
              </div>
              <button
                type="button"
                className="momente-stream-all-link"
                onClick={() => setView('timeline')}
              >
                {t('story.streamAll')}
              </button>
            </div>
            <div className="momente-stream-track">
              {items.slice(0, 10).map((item) => {
                const presentation = storyItemPresentation(item, t);
                const firstAttachment =
                  item.kind === 'MEMORY'
                    ? item.memory.attachments[0]
                    : undefined;
                const path =
                  item.kind === 'MEMORY'
                    ? memoryDetailPath(item.memory.id)
                    : item.kind === 'HEART_MOMENT'
                      ? heartMomentDetailPath(item.heartMoment.id)
                      : milestoneDetailPath(item.milestone.id);
                const memoryId = item.kind === 'MEMORY' ? item.memory.id : '';

                return (
                  <Link
                    key={storyItemKey(item)}
                    to={path}
                    className="momente-stream-card-link"
                    aria-label={presentation.title}
                  >
                    <article
                      className={`momente-stream-card ${firstAttachment ? 'has-media' : 'text-first'}`}
                    >
                      {firstAttachment ? (
                        <div className="momente-stream-card-media">
                          <MemoryPreview
                            memoryId={memoryId}
                            attachmentId={firstAttachment.id}
                            loadImage={loadMemoryImage}
                          />
                        </div>
                      ) : null}
                      <div className="momente-stream-card-body">
                        <span className="momente-stream-card-kind">
                          {item.kind === 'HEART_MOMENT'
                            ? '♥ '
                            : item.kind === 'MILESTONE'
                              ? '★ '
                              : ''}
                          {presentation.kindLabel}
                        </span>
                        {item.kind === 'HEART_MOMENT' ? (
                          <blockquote className="momente-stream-card-quote">
                            "{presentation.title}"
                          </blockquote>
                        ) : (
                          <h4 className="momente-stream-card-title">
                            {presentation.title}
                          </h4>
                        )}
                        <div className="momente-stream-card-meta">
                          <time
                            dateTime={item.effectiveDate
                              .toISOString()
                              .slice(0, 10)}
                          >
                            {formatStoryDate(item.effectiveDate, locale)}
                          </time>
                          {presentation.author ? (
                            <span>
                              {t('story.byAuthor', {
                                author: presentation.author,
                              })}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </article>
                  </Link>
                );
              })}
            </div>
          </section>

          {/* 3. Milestones & Chapters */}
          <div className="momente-grid-two">
            {milestones.length > 0 ? (
              <div className="momente-sub-card">
                <span className="momente-sub-card-kicker">
                  ★ {t('story.milestonesKicker')}
                </span>
                <h4 className="momente-sub-card-title">
                  {t('story.milestonesTitle')}
                </h4>
                <p className="momente-sub-card-desc">
                  {t('story.milestonesDesc')}
                </p>
              </div>
            ) : null}
            <Link to="/plan#chapter-title" className="momente-sub-card">
              <span className="momente-sub-card-kicker">
                📖 {t('story.chaptersKicker')}
              </span>
              <h4 className="momente-sub-card-title">
                {t('story.chaptersTitle')}
              </h4>
              <p className="momente-sub-card-desc">{t('story.chaptersDesc')}</p>
            </Link>
          </div>

          {/* 4. Year Archive */}
          {uniqueYears.length > 0 ? (
            <section
              className="momente-year-archive"
              aria-labelledby="momente-years-heading"
            >
              <div>
                <h3
                  id="momente-years-heading"
                  className="momente-section-title"
                >
                  {t('story.yearArchiveTitle')}
                </h3>
                <p className="momente-section-subhead">
                  {t('story.yearArchiveSubtitle')}
                </p>
              </div>
              <div className="momente-year-pills">
                {uniqueYears.map((year) => (
                  <button
                    key={year}
                    type="button"
                    className="momente-year-pill"
                    onClick={() => {
                      const next = new URLSearchParams(searchParams);
                      next.set('tab', 'timeline');
                      next.set('year', String(year));
                      setSearchParams(next, { replace: true });
                    }}
                  >
                    <span>🗓️</span>
                    <span>{year}</span>
                  </button>
                ))}
              </div>
            </section>
          ) : null}
        </div>
      ) : combinedStory && activeView === 'timeline' ? (
        <div className="layout-single-column sbs-motion-reveal">
          <div className="story-filter-container">
            <details className="story-filter-details">
              <summary className="story-filter-summary">
                {t('storyFilters.title')}
                {(filters.kind ||
                  filters.year ||
                  filters.order !== StoryOrder.DESC) && (
                  <span
                    className="story-filter-active-dot"
                    aria-hidden="true"
                  ></span>
                )}
              </summary>
              <div className="story-filter-dropdown">
                <form
                  className="story-filter-compact"
                  onSubmit={applyFilters}
                  key={cacheResourceId}
                  aria-label={t('storyFilters.aria')}
                >
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
                      list="story-year-options"
                      defaultValue={filters.year ?? ''}
                      placeholder={t('storyFilters.anyYear')}
                    />
                    <datalist id="story-year-options">
                      {[...Array(10)].map((_, i) => {
                        const year = new Date().getFullYear() - i;
                        return <option key={year} value={year} />;
                      })}
                    </datalist>
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
                    <button type="submit" className="primary compact-action">
                      {t('storyFilters.apply')}
                    </button>
                    {(filters.kind ||
                      filters.year ||
                      filters.order !== StoryOrder.DESC) && (
                      <button
                        type="button"
                        className="tertiary compact-action"
                        onClick={() =>
                          setSearchParams(
                            { tab: 'timeline' },
                            { replace: true },
                          )
                        }
                      >
                        {t('storyFilters.reset')}
                      </button>
                    )}
                  </div>
                </form>
              </div>
            </details>

            {(filters.kind ||
              filters.year ||
              filters.order !== StoryOrder.DESC) && (
              <div className="story-active-chips">
                {filters.kind && (
                  <span className="active-chip">
                    {t(`story.kind.${filters.kind}`)}
                  </span>
                )}
                {filters.year && (
                  <span className="active-chip">{filters.year}</span>
                )}
                {filters.order === StoryOrder.ASC && (
                  <span className="active-chip">
                    {t('storyFilters.oldest')}
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="layout-main">
            <section
              className="story-surface"
              aria-labelledby="timeline-heading"
            >
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

              <StoryList
                items={combinedStory.items}
                loadMemoryImage={loadMemoryImage}
              />

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
      ) : null}
    </div>
  );
}
