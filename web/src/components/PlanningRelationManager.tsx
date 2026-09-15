import { type FormEvent, useMemo } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import type { ChapterContentItem } from '../api/generated/models/ChapterContentItem';
import type { StoryItem } from '../api/generated/models/StoryItem';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { normalizeClientError } from '../client/problemDetails';
import {
  storyRelationTarget,
  type PlanningRelationKind,
  type PlanningRelationTarget,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { resolvedLocale, useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

const STORY_PAGE_SIZE = 50;

type RelationTargetPage = {
  items: StoryItem[];
  nextCursor: string | null;
};

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

function targetKey(kind: PlanningRelationKind, id: string): string {
  return `${kind}:${id}`;
}

async function loadRelationTargetPage(
  apis: SharedPlanningApis,
  spaceId: string,
  cursor: string | null,
): Promise<RelationTargetPage> {
  return apiCall(() =>
    apis.story.getStoryTimeline({
      spaceId,
      cursor,
      limit: STORY_PAGE_SIZE,
      order: 'DESC',
    }),
  );
}

export function nextRelationTargetCursor(
  lastPage: RelationTargetPage,
  _allPages: RelationTargetPage[],
  lastPageParam: string | null,
  allPageParams: Array<string | null>,
): string | undefined {
  const nextCursor = lastPage.nextCursor;
  if (!nextCursor) return undefined;
  if (nextCursor === lastPageParam || allPageParams.includes(nextCursor)) {
    return undefined;
  }
  return nextCursor;
}

async function loadLinkedRelationTargets(
  apis: SharedPlanningApis,
  spaceId: string,
  relations: ChapterContentItem[],
): Promise<PlanningRelationTarget[]> {
  const targets = await Promise.all(
    relations.map(async (relation): Promise<PlanningRelationTarget | null> => {
      try {
        switch (relation.targetType) {
          case 'MEMORY': {
            const memory = await apis.memories.getMemory({
              spaceId,
              memoryId: relation.targetId,
            });
            return {
              id: memory.id,
              kind: 'MEMORY',
              label: memory.title,
              effectiveDate: memory.happenedOn ?? memory.createdAt,
            };
          }
          case 'HEART_MOMENT': {
            const heartMoment = await apis.heartMoments.getHeartMoment({
              spaceId,
              heartMomentId: relation.targetId,
            });
            return {
              id: heartMoment.id,
              kind: 'HEART_MOMENT',
              label: heartMoment.text,
              effectiveDate: heartMoment.happenedOn,
            };
          }
          case 'MILESTONE': {
            const milestone = await apis.milestones.getMilestone({
              spaceId,
              milestoneId: relation.targetId,
            });
            return {
              id: milestone.id,
              kind: 'MILESTONE',
              label: milestone.title,
              effectiveDate: milestone.happenedOn,
            };
          }
        }
      } catch {
        // Detail APIs enforce authorization. An unreadable target stays an
        // opaque relation row and is never reconstructed client-side.
        return null;
      }
    }),
  );
  return targets.filter(
    (target): target is PlanningRelationTarget => target !== null,
  );
}

async function loadPlaceRelations(
  apis: SharedPlanningApis,
  spaceId: string,
  placeId: string,
): Promise<ChapterContentItem[]> {
  const [memories, heartMoments, milestones] = await Promise.all([
    apiCall(() => apis.placeRelations.listPlaceMemories({ spaceId, placeId })),
    apiCall(() =>
      apis.placeRelations.listPlaceHeartMoments({ spaceId, placeId }),
    ),
    apiCall(() =>
      apis.placeRelations.listPlaceMilestones({ spaceId, placeId }),
    ),
  ]);

  return [
    ...memories.items.map((targetId) => ({
      targetId,
      targetType: 'MEMORY' as const,
    })),
    ...heartMoments.items.map((targetId) => ({
      targetId,
      targetType: 'HEART_MOMENT' as const,
    })),
    ...milestones.items.map((targetId) => ({
      targetId,
      targetType: 'MILESTONE' as const,
    })),
  ];
}

function formatDate(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(value);
}

export function PlanningRelationManager({
  apis,
  spaceId,
  ownerKind,
  ownerId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
  ownerKind: 'place' | 'chapter';
  ownerId: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const relationKey = [
    'm5-s3',
    'relations',
    ownerKind,
    spaceId,
    ownerId,
  ] as const;

  const targetsQuery = useInfiniteQuery({
    queryKey: authorSummaryQueryKeys.relationTargets(spaceId),
    queryFn: ({ pageParam }) =>
      loadRelationTargetPage(apis, spaceId, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: nextRelationTargetCursor,
    staleTime: 60_000,
    retry: false,
  });

  const relationsQuery = useQuery({
    queryKey: relationKey,
    queryFn: () =>
      ownerKind === 'chapter'
        ? apiCall(() =>
            apis.chapterRelations.listChapterContent({
              spaceId,
              chapterId: ownerId,
            }),
          ).then((content) => content.items)
        : loadPlaceRelations(apis, spaceId, ownerId),
    retry: false,
  });

  const linkedTargetSignature = (relationsQuery.data ?? [])
    .map((relation) => targetKey(relation.targetType, relation.targetId))
    .sort()
    .join('|');
  const linkedTargetsQuery = useQuery({
    queryKey: [...relationKey, 'targets', linkedTargetSignature],
    queryFn: () =>
      loadLinkedRelationTargets(apis, spaceId, relationsQuery.data ?? []),
    enabled: relationsQuery.isSuccess && linkedTargetSignature.length > 0,
    staleTime: 60_000,
    retry: false,
  });

  const linkMutation = useMutation({
    mutationFn: async ({
      kind,
      targetId,
    }: {
      kind: PlanningRelationKind;
      targetId: string;
    }) => {
      if (ownerKind === 'chapter') {
        switch (kind) {
          case 'MEMORY':
            return apiCall(() =>
              apis.chapterRelations.linkChapterMemory({
                spaceId,
                chapterId: ownerId,
                targetId,
              }),
            );
          case 'HEART_MOMENT':
            return apiCall(() =>
              apis.chapterRelations.linkChapterHeartMoment({
                spaceId,
                chapterId: ownerId,
                targetId,
              }),
            );
          case 'MILESTONE':
            return apiCall(() =>
              apis.chapterRelations.linkChapterMilestone({
                spaceId,
                chapterId: ownerId,
                targetId,
              }),
            );
        }
      }

      switch (kind) {
        case 'MEMORY':
          return apiCall(() =>
            apis.placeRelations.linkPlaceMemory({
              spaceId,
              placeId: ownerId,
              targetId,
            }),
          );
        case 'HEART_MOMENT':
          return apiCall(() =>
            apis.placeRelations.linkPlaceHeartMoment({
              spaceId,
              placeId: ownerId,
              targetId,
            }),
          );
        case 'MILESTONE':
          return apiCall(() =>
            apis.placeRelations.linkPlaceMilestone({
              spaceId,
              placeId: ownerId,
              targetId,
            }),
          );
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: relationKey }),
  });

  const unlinkMutation = useMutation({
    mutationFn: async ({
      kind,
      targetId,
    }: {
      kind: PlanningRelationKind;
      targetId: string;
    }) => {
      if (ownerKind === 'chapter') {
        switch (kind) {
          case 'MEMORY':
            return apiCall(() =>
              apis.chapterRelations.unlinkChapterMemory({
                spaceId,
                chapterId: ownerId,
                targetId,
              }),
            );
          case 'HEART_MOMENT':
            return apiCall(() =>
              apis.chapterRelations.unlinkChapterHeartMoment({
                spaceId,
                chapterId: ownerId,
                targetId,
              }),
            );
          case 'MILESTONE':
            return apiCall(() =>
              apis.chapterRelations.unlinkChapterMilestone({
                spaceId,
                chapterId: ownerId,
                targetId,
              }),
            );
        }
      }

      switch (kind) {
        case 'MEMORY':
          return apiCall(() =>
            apis.placeRelations.unlinkPlaceMemory({
              spaceId,
              placeId: ownerId,
              targetId,
            }),
          );
        case 'HEART_MOMENT':
          return apiCall(() =>
            apis.placeRelations.unlinkPlaceHeartMoment({
              spaceId,
              placeId: ownerId,
              targetId,
            }),
          );
        case 'MILESTONE':
          return apiCall(() =>
            apis.placeRelations.unlinkPlaceMilestone({
              spaceId,
              placeId: ownerId,
              targetId,
            }),
          );
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: relationKey }),
  });

  const loadedTargets = useMemo(() => {
    const byKey = new Map<string, PlanningRelationTarget>();
    for (const page of targetsQuery.data?.pages ?? []) {
      for (const item of page.items) {
        const target = storyRelationTarget(item);
        byKey.set(targetKey(target.kind, target.id), target);
      }
    }
    for (const target of linkedTargetsQuery.data ?? []) {
      byKey.set(targetKey(target.kind, target.id), target);
    }
    return [...byKey.values()];
  }, [linkedTargetsQuery.data, targetsQuery.data?.pages]);
  const targetMap = useMemo(
    () =>
      new Map(
        loadedTargets.map((target) => [
          targetKey(target.kind, target.id),
          target,
        ]),
      ),
    [loadedTargets],
  );
  const linkedKeys = new Set(
    (relationsQuery.data ?? []).map((relation) =>
      targetKey(relation.targetType, relation.targetId),
    ),
  );
  const availableTargets = loadedTargets.filter(
    (target) => !linkedKeys.has(targetKey(target.kind, target.id)),
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const value = String(data.get('target'));
    const [kind, ...idParts] = value.split(':');
    const targetId = idParts.join(':');
    if (!targetId) return;
    linkMutation.mutate(
      { kind: kind as PlanningRelationKind, targetId },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <section
      className="planning-subsection"
      aria-labelledby={`${ownerKind}-relations-heading`}
    >
      <div className="layout-section-head">
        <div>
          <h2 id={`${ownerKind}-relations-heading`}>
            {t('m5s3.relations.heading')}
          </h2>
          <p>{t('m5s3.relations.intro')}</p>
        </div>
      </div>

      {targetsQuery.isLoading || relationsQuery.isLoading ? (
        <UiState kind="loading" title={t('m5s3.relations.loading')} />
      ) : null}
      {targetsQuery.error ? <ProblemState error={targetsQuery.error} /> : null}
      {relationsQuery.error ? (
        <ProblemState
          error={relationsQuery.error}
          onRetry={() => void relationsQuery.refetch()}
        />
      ) : null}

      {relationsQuery.data && relationsQuery.data.length > 0 ? (
        <ul className="planning-relation-list">
          {relationsQuery.data.map((relation) => {
            const target = targetMap.get(
              targetKey(relation.targetType, relation.targetId),
            );
            return (
              <li key={targetKey(relation.targetType, relation.targetId)}>
                <div>
                  <strong>
                    {target?.label || t('m5s3.relations.contentFallback')}
                  </strong>
                  <span className="planning-meta">
                    {t(`m5s3.relations.kind.${relation.targetType}`)}
                    {target ? ` · ${formatDate(target.effectiveDate)}` : ''}
                  </span>
                </div>
                <button
                  type="button"
                  className="tertiary"
                  onClick={() =>
                    unlinkMutation.mutate({
                      kind: relation.targetType,
                      targetId: relation.targetId,
                    })
                  }
                  disabled={unlinkMutation.isPending}
                >
                  {t('m5s3.relations.unlink')}
                </button>
              </li>
            );
          })}
        </ul>
      ) : relationsQuery.data ? (
        <p className="planning-empty">{t('m5s3.relations.empty')}</p>
      ) : null}

      {availableTargets.length > 0 ? (
        <form onSubmit={submit} className="planning-relation-form">
          <label htmlFor={`${ownerKind}-relation-target`}>
            {t('m5s3.relations.addLabel')}
          </label>
          <select
            id={`${ownerKind}-relation-target`}
            name="target"
            required
            defaultValue=""
          >
            <option value="" disabled>
              {t('m5s3.relations.choose')}
            </option>
            {availableTargets.map((target) => (
              <option
                key={targetKey(target.kind, target.id)}
                value={targetKey(target.kind, target.id)}
              >
                {t(`m5s3.relations.kind.${target.kind}`)} · {target.label}
              </option>
            ))}
          </select>
          <button type="submit" disabled={linkMutation.isPending}>
            {linkMutation.isPending
              ? t('m5s3.common.saving')
              : t('m5s3.relations.link')}
          </button>
        </form>
      ) : targetsQuery.data && !targetsQuery.hasNextPage ? (
        <p className="planning-meta">{t('m5s3.relations.noMoreTargets')}</p>
      ) : null}

      {targetsQuery.hasNextPage ? (
        <button
          type="button"
          className="tertiary compact-action"
          onClick={() => void targetsQuery.fetchNextPage()}
          disabled={targetsQuery.isFetchingNextPage}
        >
          {targetsQuery.isFetchingNextPage
            ? t('m5s3.common.loadingMore')
            : t('m5s3.common.loadMore')}
        </button>
      ) : null}

      {linkMutation.error ? <ProblemState error={linkMutation.error} /> : null}
      {unlinkMutation.error ? (
        <ProblemState error={unlinkMutation.error} />
      ) : null}
    </section>
  );
}
