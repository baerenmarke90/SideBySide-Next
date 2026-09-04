import { useEffect, useMemo } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import {
  StoryKind,
  type StoryKind as StoryKindValue,
} from '../api/generated/models/StoryKind';
import { StoryOrder } from '../api/generated/models/StoryOrder';
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
import type { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import type { AuthorSummary } from '../api/generated/models/AuthorSummary';
import type { StoryItem } from '../api/generated/models/StoryItem';
import { AuthorAvatar } from './PersonIdentity';
import { MemoryPreview } from './MemoryPreview';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { StoryList } from './StoryList';
import {
  formatStoryDate,
  resolveStoryKindLabel,
  storyItemKey,
  storyItemPresentation,
} from './storyPresentation';
import { UiState } from './UiState';

function storyItemAuthor(item: StoryItem): AuthorSummary {
  switch (item.kind) {
    case 'MEMORY':
      return item.memory.author;
    case 'HEART_MOMENT':
      return item.heartMoment.author;
    case 'MILESTONE':
      return item.milestone.author;
  }
}

function isStoryKind(value: string | null): value is StoryKindValue {
  return (
    value !== null && Object.values(StoryKind).includes(value as StoryKindValue)
  );
}

export function StoryProductPage({
  apis,
  accountId,
  spaceId,
  loadMemoryImage,
  profilesApi,
}: {
  apis: ReferenceApis;
  accountId: string;
  spaceId: string;
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
  profilesApi?: ProfilesApi;
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

  const hasActiveFilters = Boolean(
    filters.kind || filters.year || filters.order !== StoryOrder.DESC,
  );

  const activeView = useMemo(() => {
    const tab = searchParams.get('tab');
    if (tab === 'timeline') return 'timeline';
    if (tab === 'discover') return 'discover';
    if (hasActiveFilters) {
      return 'timeline';
    }
    return 'discover';
  }, [searchParams, hasActiveFilters]);

  function setView(view: 'discover' | 'timeline') {
    const next = new URLSearchParams(searchParams);
    next.set('tab', view);
    setSearchParams(next);
  }

  function updateFilter<K extends keyof StoryFilters>(
    key: K,
    value: StoryFilters[K],
  ) {
    const nextFilters: StoryFilters = {
      ...filters,
      [key]: value,
      ...(key === 'kind' ? { year: null } : {}),
    };
    const nextSearch = storyFiltersToSearch(nextFilters);
    nextSearch.set('tab', 'timeline');
    setSearchParams(nextSearch);
  }

  function resetAllFilters() {
    const nextSearch = new URLSearchParams();
    nextSearch.set('tab', 'timeline');
    setSearchParams(nextSearch);
  }

  const availableYears = useMemo(
    () => combinedStory?.availableYears ?? [],
    [combinedStory],
  );
  const dropdownYears = availableYears;

  useEffect(() => {
    if (!combinedStory) return;
    if (filters.year && !availableYears.includes(filters.year)) {
      const nextFilters: StoryFilters = {
        ...filters,
        year: null,
      };
      const nextSearch = storyFiltersToSearch(nextFilters);
      nextSearch.set('tab', 'timeline');
      setSearchParams(nextSearch, { replace: true });
    }
  }, [combinedStory, filters, availableYears, setSearchParams]);

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
  const featuredAuthor = featuredItem ? storyItemAuthor(featuredItem) : null;
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

      {combinedStory &&
      items.length === 0 &&
      availableYears.length === 0 &&
      !hasActiveFilters ? (
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
      ) : combinedStory && activeView === 'discover' && items.length > 0 ? (
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
                    {featuredAuthor ? (
                      <span className="momente-author-meta">
                        <AuthorAvatar
                          author={featuredAuthor}
                          profilesApi={profilesApi}
                          spaceId={spaceId}
                        />
                        <span>
                          {t('story.byAuthor', {
                            author: featuredAuthor.displayName,
                          })}
                        </span>
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
                const author = storyItemAuthor(item);

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
                        <div className="momente-stream-card-main">
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
                        </div>
                        <div className="momente-stream-card-meta">
                          <time
                            dateTime={item.effectiveDate
                              .toISOString()
                              .slice(0, 10)}
                          >
                            {formatStoryDate(item.effectiveDate, locale)}
                          </time>
                          {author ? (
                            <span className="momente-author-meta">
                              <AuthorAvatar
                                author={author}
                                profilesApi={profilesApi}
                                spaceId={spaceId}
                              />
                              <span>
                                {t('story.byAuthor', {
                                  author: author.displayName,
                                })}
                              </span>
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
              <Link
                to="/story?tab=timeline&type=MILESTONE"
                className="momente-sub-card"
              >
                <span className="momente-sub-card-kicker">
                  ★ {t('story.milestonesKicker')}
                </span>
                <h4 className="momente-sub-card-title">
                  {t('story.milestonesTitle')}
                </h4>
                <p className="momente-sub-card-desc">
                  {t('story.milestonesDesc')}
                </p>
              </Link>
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
      ) : combinedStory && (activeView === 'timeline' || hasActiveFilters) ? (
        <div className="layout-single-column sbs-motion-reveal">
          <div className="story-filter-container">
            <section
              className="story-filter-bar"
              aria-label={t('storyFilters.aria')}
            >
              <div className="story-filter-group">
                <label htmlFor="story-filter-type">
                  {t('storyFilters.type')}
                </label>
                <select
                  id="story-filter-type"
                  name="type"
                  value={filters.kind ?? ''}
                  onChange={(e) =>
                    updateFilter(
                      'kind',
                      isStoryKind(e.target.value) ? e.target.value : null,
                    )
                  }
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
              <div className="story-filter-group">
                <label htmlFor="story-filter-year">
                  {t('storyFilters.year')}
                </label>
                <select
                  id="story-filter-year"
                  name="year"
                  value={
                    filters.year && availableYears.includes(filters.year)
                      ? filters.year
                      : ''
                  }
                  onChange={(e) => {
                    const val = e.target.value;
                    updateFilter('year', val ? Number(val) : null);
                  }}
                >
                  <option value="">{t('storyFilters.anyYear')}</option>
                  {dropdownYears.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>
              <div className="story-filter-group">
                <label htmlFor="story-filter-order">
                  {t('storyFilters.order')}
                </label>
                <select
                  id="story-filter-order"
                  name="order"
                  value={filters.order}
                  onChange={(e) =>
                    updateFilter(
                      'order',
                      e.target.value === StoryOrder.ASC
                        ? StoryOrder.ASC
                        : StoryOrder.DESC,
                    )
                  }
                >
                  <option value={StoryOrder.DESC}>
                    {t('storyFilters.newest')}
                  </option>
                  <option value={StoryOrder.ASC}>
                    {t('storyFilters.oldest')}
                  </option>
                </select>
              </div>
              {hasActiveFilters && (
                <button
                  type="button"
                  className="story-filter-reset-header-action"
                  onClick={resetAllFilters}
                >
                  {t('storyFilters.reset')}
                </button>
              )}
            </section>

            {hasActiveFilters && (
              <div
                className="story-active-chips"
                role="status"
                aria-live="polite"
              >
                {filters.kind && (
                  <button
                    type="button"
                    className="active-chip"
                    onClick={() => updateFilter('kind', null)}
                    aria-label={`${t('storyFilters.removeFilter')}: ${resolveStoryKindLabel(filters.kind, t)}`}
                  >
                    <span>{resolveStoryKindLabel(filters.kind, t)}</span>
                    <span className="chip-remove" aria-hidden="true">
                      ✕
                    </span>
                  </button>
                )}
                {filters.year && availableYears.includes(filters.year) && (
                  <button
                    type="button"
                    className="active-chip"
                    onClick={() => updateFilter('year', null)}
                    aria-label={`${t('storyFilters.removeFilter')}: ${filters.year}`}
                  >
                    <span>{filters.year}</span>
                    <span className="chip-remove" aria-hidden="true">
                      ✕
                    </span>
                  </button>
                )}
                {filters.order === StoryOrder.ASC && (
                  <button
                    type="button"
                    className="active-chip"
                    onClick={() => updateFilter('order', StoryOrder.DESC)}
                    aria-label={`${t('storyFilters.removeFilter')}: ${t('storyFilters.oldest')}`}
                  >
                    <span>{t('storyFilters.oldest')}</span>
                    <span className="chip-remove" aria-hidden="true">
                      ✕
                    </span>
                  </button>
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

              {items.length === 0 ? (
                <div className="story-filter-empty-state sbs-motion-reveal">
                  <p className="story-filter-empty-text">
                    {t('storyFilters.noMatches')}
                  </p>
                  <button
                    type="button"
                    className="button secondary compact-action"
                    onClick={resetAllFilters}
                  >
                    {t('storyFilters.noMatchesAction')}
                  </button>
                </div>
              ) : (
                <>
                  <StoryList
                    items={combinedStory.items}
                    loadMemoryImage={loadMemoryImage}
                    profilesApi={profilesApi}
                    spaceId={spaceId}
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
                </>
              )}
            </section>
          </div>
        </div>
      ) : null}
    </div>
  );
}
