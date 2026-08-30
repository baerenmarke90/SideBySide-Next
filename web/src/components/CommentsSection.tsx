import { type FormEvent, useState } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import type { ContentVisibility } from '../api/generated/models/ContentVisibility';
import type { CommentDetail } from '../api/generated/models/CommentDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  commentsVisibleForParent,
  type CommentParentKind,
} from '../client/productPrivacy';
import type { ReferenceApis } from '../client/referenceFlow';
import { resolvedLocale, useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

async function listComments(
  apis: ReferenceApis,
  parentKind: CommentParentKind,
  spaceId: string,
  parentId: string,
  cursor: string | null,
) {
  const common = { spaceId, cursor: cursor || undefined, limit: 25 };
  if (parentKind === 'MEMORY') {
    return apis.comments.listMemoryComments({ ...common, memoryId: parentId });
  }
  if (parentKind === 'MILESTONE') {
    return apis.comments.listMilestoneComments({
      ...common,
      milestoneId: parentId,
    });
  }
  return apis.comments.listHeartMomentComments({
    ...common,
    heartMomentId: parentId,
  });
}

async function createComment(
  apis: ReferenceApis,
  parentKind: CommentParentKind,
  spaceId: string,
  parentId: string,
  body: string,
) {
  const commentCreate = { body };
  if (parentKind === 'MEMORY') {
    return apis.comments.createMemoryComment({
      spaceId,
      memoryId: parentId,
      commentCreate,
    });
  }
  if (parentKind === 'MILESTONE') {
    return apis.comments.createMilestoneComment({
      spaceId,
      milestoneId: parentId,
      commentCreate,
    });
  }
  return apis.comments.createHeartMomentComment({
    spaceId,
    heartMomentId: parentId,
    commentCreate,
  });
}

function formatCommentDate(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(value);
}

export function CommentsSection({
  apis,
  spaceId,
  parentKind,
  parentId,
  parentVisibility,
  canComment,
  currentAccountId,
}: {
  apis: ReferenceApis;
  spaceId: string;
  parentKind: CommentParentKind;
  parentId: string;
  parentVisibility?: ContentVisibility;
  canComment: boolean;
  currentAccountId: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const commentsAllowed = commentsVisibleForParent(
    parentKind,
    parentVisibility,
  );
  const queryKey = ['comments', spaceId, parentKind, parentId] as const;

  const commentsQuery = useInfiniteQuery({
    queryKey,
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) => {
      try {
        return await listComments(
          apis,
          parentKind,
          spaceId,
          parentId,
          pageParam,
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor || undefined,
    enabled: commentsAllowed,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: async (body: string) => {
      try {
        return await createComment(
          apis,
          parentKind,
          spaceId,
          parentId,
          body,
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      comment,
      body,
    }: {
      comment: CommentDetail;
      body: string;
    }) => {
      try {
        return await apis.comments.updateComment({
          spaceId,
          commentId: comment.id,
          ifMatch: String(comment.version),
          commentUpdate: { body },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setEditingId(null);
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (comment: CommentDetail) => {
      try {
        await apis.comments.deleteComment({
          spaceId,
          commentId: comment.id,
          ifMatch: String(comment.version),
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  if (!commentsAllowed) return null;

  const comments = commentsQuery.data?.pages.flatMap((page) => page.items) ?? [];

  function submitNew(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const body = String(data.get('comment') || '').trim();
    if (!body) return;
    createMutation.mutate(body, { onSuccess: () => form.reset() });
  }

  return (
    <section className="comments-section" aria-labelledby={`comments-${parentId}`}>
      <div className="section-head memory-section-head">
        <div>
          <p className="section-kicker">{t('m5Product.comments.kicker')}</p>
          <h2 id={`comments-${parentId}`}>
            {t('m5Product.comments.heading')}
          </h2>
        </div>
      </div>

      {commentsQuery.isLoading ? (
        <UiState kind="loading" title={t('m5Product.comments.loading')} />
      ) : null}
      {commentsQuery.error ? (
        <ProblemState
          error={commentsQuery.error}
          onRetry={() => void commentsQuery.refetch()}
        />
      ) : null}

      {!commentsQuery.isLoading && !commentsQuery.error && comments.length === 0 ? (
        <p className="muted">{t('m5Product.comments.empty')}</p>
      ) : null}

      {comments.length > 0 ? (
        <ol className="comment-list">
          {comments.map((comment) => {
            const own = comment.authorId === currentAccountId;
            const editing = editingId === comment.id;
            return (
              <li key={comment.id} className="comment-card">
                <div className="comment-meta">
                  <strong>{comment.author.displayName}</strong>
                  <time dateTime={comment.createdAt.toISOString()}>
                    {formatCommentDate(comment.createdAt)}
                  </time>
                </div>
                {editing ? (
                  <form
                    className="comment-edit-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      const data = new FormData(event.currentTarget);
                      const body = String(data.get('body') || '').trim();
                      if (body) updateMutation.mutate({ comment, body });
                    }}
                  >
                    <label className="sr-only" htmlFor={`comment-edit-${comment.id}`}>
                      {t('m5Product.comments.editLabel')}
                    </label>
                    <textarea
                      id={`comment-edit-${comment.id}`}
                      name="body"
                      rows={3}
                      defaultValue={comment.body}
                      required
                    />
                    <div className="memory-actions">
                      <button
                        type="button"
                        className="tertiary"
                        onClick={() => setEditingId(null)}
                      >
                        {t('common.cancel')}
                      </button>
                      <button type="submit" disabled={updateMutation.isPending}>
                        {t('m5Product.comments.save')}
                      </button>
                    </div>
                  </form>
                ) : (
                  <p>{comment.body}</p>
                )}
                {own && !editing ? (
                  <div className="comment-actions">
                    <button
                      type="button"
                      className="tertiary"
                      onClick={() => setEditingId(comment.id)}
                    >
                      {t('m5Product.comments.edit')}
                    </button>
                    <button
                      type="button"
                      className="tertiary"
                      onClick={() => deleteMutation.mutate(comment)}
                      disabled={deleteMutation.isPending}
                    >
                      {t('m5Product.comments.delete')}
                    </button>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>
      ) : null}

      {commentsQuery.hasNextPage ? (
        <button
          type="button"
          className="secondary"
          disabled={commentsQuery.isFetchingNextPage}
          onClick={() => void commentsQuery.fetchNextPage()}
        >
          {commentsQuery.isFetchingNextPage
            ? t('m5Product.comments.loadingMore')
            : t('m5Product.comments.loadMore')}
        </button>
      ) : null}

      {canComment ? (
        <form className="comment-create-form" onSubmit={submitNew}>
          <label htmlFor={`comment-new-${parentId}`}>
            {t('m5Product.comments.newLabel')}
          </label>
          <textarea
            id={`comment-new-${parentId}`}
            name="comment"
            rows={3}
            required
            placeholder={t('m5Product.comments.placeholder')}
          />
          <button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending
              ? t('m5Product.comments.sending')
              : t('m5Product.comments.send')}
          </button>
        </form>
      ) : null}

      {createMutation.error ? <ProblemState error={createMutation.error} /> : null}
      {updateMutation.error ? (
        <ProblemState
          error={updateMutation.error}
          onRetry={() => void commentsQuery.refetch()}
        />
      ) : null}
      {deleteMutation.error ? (
        <ProblemState
          error={deleteMutation.error}
          onRetry={() => void commentsQuery.refetch()}
        />
      ) : null}
    </section>
  );
}
