import { type FormEvent, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import type { ChapterDetail } from '../api/generated/models/ChapterDetail';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import { invalidateDashboard } from '../client/dashboardQueries';
import { formatDateInputValue } from '../client/dateInput';
import { normalizeClientError } from '../client/problemDetails';
import {
  chapterDetailPath,
  memoryDetailPath,
  milestoneDetailPath,
} from '../client/routes';
import {
  dateFromInput,
  dateOnlyInput,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { resolvedLocale, useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './PlanStoryContinuation.css';

type StoryKind = 'MEMORY' | 'MILESTONE';

type CreatedStory = {
  kind: StoryKind;
  id: string;
  title: string;
};

const NEW_CHAPTER = '__new__';
const CHAPTER_PAGE_SIZE = 50;
const MAX_CHAPTER_PAGES = 20;

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

async function loadAllChapters(
  apis: SharedPlanningApis,
  spaceId: string,
): Promise<ChapterDetail[]> {
  const items: ChapterDetail[] = [];
  const seenCursors = new Set<string>();
  let cursor: string | null | undefined = null;
  let pages = 0;

  do {
    const page = await apiCall(() =>
      apis.chapters.listChapters({
        spaceId,
        cursor,
        limit: CHAPTER_PAGE_SIZE,
      }),
    );
    items.push(...page.items);
    cursor = page.nextCursor;
    pages += 1;
    if (cursor) {
      if (seenCursors.has(cursor)) {
        throw new Error('Chapter pagination returned a repeated cursor.');
      }
      seenCursors.add(cursor);
    }
  } while (cursor && pages < MAX_CHAPTER_PAGES);

  if (cursor) throw new Error('Chapter pagination exceeded the safety limit.');
  return items;
}

function storyDetailPath(story: CreatedStory): string {
  return story.kind === 'MEMORY'
    ? memoryDetailPath(story.id)
    : milestoneDetailPath(story.id);
}

function ChapterContinuation({
  apis,
  spaceId,
  story,
  preferred,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
  story: CreatedStory;
  preferred: boolean;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [choice, setChoice] = useState('');
  const [createdChapterId, setCreatedChapterId] = useState<string | null>(null);

  const chaptersQuery = useQuery({
    queryKey: ['m5-s3', 'plan-story-chapters', spaceId],
    queryFn: () => loadAllChapters(apis, spaceId),
    staleTime: 30_000,
    retry: false,
  });

  const linkMutation = useMutation({
    mutationFn: (chapterId: string) =>
      story.kind === 'MEMORY'
        ? apiCall(() =>
            apis.chapterRelations.linkChapterMemory({
              spaceId,
              chapterId,
              targetId: story.id,
            }),
          )
        : apiCall(() =>
            apis.chapterRelations.linkChapterMilestone({
              spaceId,
              chapterId,
              targetId: story.id,
            }),
          ),
    onSuccess: async (_result, chapterId) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['m5-s3', 'chapters', spaceId],
        }),
        queryClient.invalidateQueries({
          queryKey: ['m5-s3', 'relations', 'chapter', spaceId, chapterId],
        }),
      ]);
      navigate(chapterDetailPath(chapterId), {
        replace: true,
        state: { linkedFromCompletedPlan: true },
      });
    },
  });

  const createChapterMutation = useMutation({
    mutationFn: (title: string) =>
      apiCall(() =>
        apis.chapters.createChapter({
          spaceId,
          chapterCreate: { title },
        }),
      ),
    onSuccess: async (chapter) => {
      setCreatedChapterId(chapter.id);
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'chapters', spaceId],
      });
      linkMutation.mutate(chapter.id);
    },
  });

  function submitExisting(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!choice || choice === NEW_CHAPTER) return;
    linkMutation.mutate(choice);
  }

  function submitNew(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (createdChapterId) {
      linkMutation.mutate(createdChapterId);
      return;
    }
    const data = new FormData(event.currentTarget);
    const title = String(data.get('chapterTitle') || '').trim();
    if (!title) return;
    createChapterMutation.mutate(title);
  }

  return (
    <section
      className="plan-story-chapter-step"
      aria-labelledby="plan-story-chapter-heading"
    >
      <h3 id="plan-story-chapter-heading">
        {preferred
          ? t('m5s3.planStory.chapterPreferredHeading')
          : t('m5s3.planStory.chapterOptionalHeading')}
      </h3>
      <p>{t('m5s3.planStory.chapterIntro')}</p>

      {chaptersQuery.isLoading ? (
        <UiState kind="loading" title={t('m5s3.planStory.chaptersLoading')} />
      ) : null}
      {chaptersQuery.error ? (
        <ProblemState
          error={chaptersQuery.error}
          onRetry={() => void chaptersQuery.refetch()}
        />
      ) : null}

      {chaptersQuery.data ? (
        <>
          <form className="plan-story-chapter-form" onSubmit={submitExisting}>
            <label htmlFor="plan-story-chapter-choice">
              {t('m5s3.planStory.chapterChoiceLabel')}
            </label>
            <select
              id="plan-story-chapter-choice"
              value={choice}
              onChange={(event) => setChoice(event.target.value)}
            >
              <option value="">
                {t('m5s3.planStory.chapterChoicePlaceholder')}
              </option>
              {chaptersQuery.data.map((chapter) => (
                <option key={chapter.id} value={chapter.id}>
                  {chapter.title}
                </option>
              ))}
              <option value={NEW_CHAPTER}>
                {t('m5s3.planStory.chapterNew')}
              </option>
            </select>
            {choice && choice !== NEW_CHAPTER ? (
              <button type="submit" disabled={linkMutation.isPending}>
                {linkMutation.isPending
                  ? t('m5s3.planStory.chapterLinking')
                  : t('m5s3.planStory.chapterLink')}
              </button>
            ) : null}
          </form>

          {choice === NEW_CHAPTER ? (
            <form className="plan-story-chapter-form" onSubmit={submitNew}>
              <label htmlFor="plan-story-new-chapter-title">
                {t('m5s3.planStory.chapterNewTitle')}
              </label>
              <input
                id="plan-story-new-chapter-title"
                name="chapterTitle"
                required
                maxLength={200}
                disabled={Boolean(createdChapterId)}
              />
              <button
                type="submit"
                disabled={
                  createChapterMutation.isPending || linkMutation.isPending
                }
              >
                {createdChapterId
                  ? t('m5s3.planStory.chapterRetryLink')
                  : createChapterMutation.isPending
                    ? t('m5s3.planStory.chapterCreating')
                    : t('m5s3.planStory.chapterCreateAndLink')}
              </button>
            </form>
          ) : null}
        </>
      ) : null}

      {createChapterMutation.error ? (
        <ProblemState error={createChapterMutation.error} />
      ) : null}
      {linkMutation.error ? <ProblemState error={linkMutation.error} /> : null}

      <button
        type="button"
        className="tertiary"
        onClick={() => navigate(storyDetailPath(story), { replace: true })}
      >
        {t('m5s3.planStory.chapterSkip')}
      </button>
    </section>
  );
}

export function PlanStoryContinuation({
  apis,
  spaceId,
  plan,
  focusOnMount = false,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
  plan: PlanDetail;
  focusOnMount?: boolean;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [dismissed, setDismissed] = useState(false);
  const [captureMode, setCaptureMode] = useState<StoryKind | null>(null);
  const [chapterPreferred, setChapterPreferred] = useState(false);
  const [createdStory, setCreatedStory] = useState<CreatedStory | null>(null);

  useEffect(() => {
    if (focusOnMount) headingRef.current?.focus();
  }, [focusOnMount]);

  const createMutation = useMutation({
    mutationFn: async ({
      kind,
      title,
      body,
      happenedOn,
    }: {
      kind: StoryKind;
      title: string;
      body?: string;
      happenedOn: Date;
    }): Promise<CreatedStory> => {
      if (kind === 'MEMORY') {
        const memory = await apiCall(() =>
          apis.memories.createMemory({
            spaceId,
            memoryCreate: {
              title,
              body: body || undefined,
              happenedOn,
            },
          }),
        );
        return { kind, id: memory.id, title: memory.title };
      }

      const milestone = await apiCall(() =>
        apis.milestones.createMilestone({
          spaceId,
          milestoneCreate: {
            title,
            body: body || undefined,
            happenedOn,
          },
        }),
      );
      return { kind, id: milestone.id, title: milestone.title };
    },
    onSuccess: async (story) => {
      setCreatedStory(story);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['story', spaceId] }),
        invalidateDashboard(queryClient, spaceId),
      ]);
    },
  });

  function selectCapture(kind: StoryKind, preferChapter = false) {
    createMutation.reset();
    setCreatedStory(null);
    setChapterPreferred(preferChapter);
    setCaptureMode(kind);
  }

  function submitCapture(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!captureMode) return;
    const data = new FormData(event.currentTarget);
    const authoredTitle = String(data.get('title') || '').trim();
    const happenedOnValue = String(data.get('happenedOn') || '');
    const happenedOn = dateFromInput(happenedOnValue);
    const body = String(data.get('body') || '').trim();
    if (!happenedOn) return;
    const title =
      captureMode === 'MEMORY' && !authoredTitle
        ? t('memoryProduct.createFallbackTitle', {
            date: formatDateInputValue(happenedOnValue, resolvedLocale()),
          })
        : authoredTitle;
    if (!title) return;
    createMutation.mutate({
      kind: captureMode,
      title,
      body: body || undefined,
      happenedOn,
    });
  }

  function dismissContinuation() {
    const focusTarget = headingRef.current
      ?.closest('.planning-page')
      ?.querySelector<HTMLAnchorElement>('.back-link');
    focusTarget?.focus();
    setDismissed(true);
  }

  if (dismissed) return null;

  return (
    <section
      className="plan-completed-celebration plan-story-continuation sbs-motion-reveal"
      aria-labelledby="plan-completed-heading"
    >
      <h2
        id="plan-completed-heading"
        ref={headingRef}
        tabIndex={focusOnMount ? -1 : undefined}
      >
        {t('m5s3.plan.completedTitle')}
      </h2>
      <p className="plan-completed-intro">{t('m5s3.planStory.intro')}</p>

      {!captureMode && !createdStory ? (
        <>
          <div className="plan-story-actions">
            <button type="button" onClick={() => selectCapture('MEMORY')}>
              {t('m5s3.planStory.memoryAction')}
            </button>
            <button type="button" onClick={() => selectCapture('MILESTONE')}>
              {t('m5s3.planStory.milestoneAction')}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => setChapterPreferred(true)}
            >
              {t('m5s3.planStory.chapterAction')}
            </button>
            <button
              type="button"
              className="tertiary"
              onClick={dismissContinuation}
            >
              {t('m5s3.planStory.later')}
            </button>
          </div>

          {chapterPreferred ? (
            <div className="plan-story-kind-choice">
              <p>{t('m5s3.planStory.chapterNeedsStory')}</p>
              <div className="plan-story-actions">
                <button
                  type="button"
                  onClick={() => selectCapture('MEMORY', true)}
                >
                  {t('m5s3.planStory.chapterViaMemory')}
                </button>
                <button
                  type="button"
                  onClick={() => selectCapture('MILESTONE', true)}
                >
                  {t('m5s3.planStory.chapterViaMilestone')}
                </button>
              </div>
            </div>
          ) : null}
        </>
      ) : null}

      {captureMode && !createdStory ? (
        <form className="plan-story-capture-form" onSubmit={submitCapture}>
          <h3>
            {captureMode === 'MEMORY'
              ? t('m5s3.planStory.memoryHeading')
              : t('m5s3.planStory.milestoneHeading')}
          </h3>
          <label htmlFor="plan-story-title">{t('m5s3.common.title')}</label>
          <input
            id="plan-story-title"
            name="title"
            required={captureMode === 'MILESTONE'}
            maxLength={200}
            defaultValue={plan.title}
          />
          <label htmlFor="plan-story-date">
            {t('m5s3.plan.experiencedOn')}
          </label>
          <input
            id="plan-story-date"
            name="happenedOn"
            type="date"
            required
            defaultValue={dateOnlyInput(plan.experiencedOn)}
          />
          <label htmlFor="plan-story-body">
            {t('m5s3.planStory.noteLabel')}
          </label>
          <textarea
            id="plan-story-body"
            name="body"
            rows={3}
            defaultValue={plan.description ?? ''}
          />
          <div className="form-actions">
            <button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending
                ? t('m5s3.common.saving')
                : t('m5s3.planStory.saveStory')}
            </button>
            <button
              type="button"
              className="tertiary"
              onClick={() => {
                createMutation.reset();
                setCaptureMode(null);
                setChapterPreferred(false);
              }}
            >
              {t('common.cancel')}
            </button>
          </div>
          {createMutation.error ? (
            <ProblemState error={createMutation.error} />
          ) : null}
        </form>
      ) : null}

      {createdStory ? (
        <>
          <p className="status" role="status" aria-live="polite">
            {createdStory.kind === 'MEMORY'
              ? t('m5s3.planStory.memorySaved')
              : t('m5s3.planStory.milestoneSaved')}
          </p>
          <ChapterContinuation
            apis={apis}
            spaceId={spaceId}
            story={createdStory}
            preferred={chapterPreferred}
          />
        </>
      ) : null}
    </section>
  );
}
