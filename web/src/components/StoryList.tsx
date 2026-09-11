import { Link } from 'react-router-dom';
import type { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import type { AuthorSummary } from '../api/generated/models/AuthorSummary';
import type { StoryItem } from '../api/generated/models/StoryItem';
import {
  heartMomentDetailPath,
  memoryDetailPath,
  milestoneDetailPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { MemoryPreview } from './MemoryPreview';
import { AuthorAvatar } from './PersonIdentity';
import {
  formatStoryDate,
  storyAuthorLabel,
  storyItemKey,
  storyItemPresentation,
} from './storyPresentation';
import { UiState } from './UiState';
import './StoryListPolish.css';

function storyProductPath(item: StoryItem): string {
  switch (item.kind) {
    case 'MEMORY':
      return memoryDetailPath(item.memory.id);
    case 'HEART_MOMENT':
      return heartMomentDetailPath(item.heartMoment.id);
    case 'MILESTONE':
      return milestoneDetailPath(item.milestone.id);
  }
}

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

export function StoryList({
  items,
  loadMemoryImage,
  profilesApi,
  spaceId,
}: {
  items: StoryItem[];
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
  profilesApi?: ProfilesApi;
  spaceId?: string;
}) {
  const { t } = useTranslation();

  if (items.length === 0) {
    return (
      <UiState
        kind="empty"
        title={t('story.emptyTitle')}
        body={t('story.emptyBody')}
      />
    );
  }

  const locale = resolvedLocale();

  return (
    <section className="story-timeline" aria-label={t('story.aria')}>
      <ol className="story-list">
        {items.map((item, index) => {
          const presentation = storyItemPresentation(item, t);
          const author = storyItemAuthor(item);
          const firstMemoryAttachment =
            item.kind === 'MEMORY' ? item.memory.attachments[0] : undefined;
          const productPath = storyProductPath(item);

          const isOwnerOnly =
            (item as unknown as { visibility?: string }).visibility ===
              'OWNER_ONLY' ||
            (item as unknown as { visibility?: string }).visibility ===
              'PRIVATE' ||
            (item.kind === 'MEMORY' &&
              ((item.memory as unknown as { visibility?: string })
                ?.visibility === 'OWNER_ONLY' ||
                (item.memory as unknown as { visibility?: string })
                  ?.visibility === 'PRIVATE')) ||
            (item.kind === 'HEART_MOMENT' &&
              ((item.heartMoment as unknown as { visibility?: string })
                ?.visibility === 'OWNER_ONLY' ||
                (item.heartMoment as unknown as { visibility?: string })
                  ?.visibility === 'PRIVATE')) ||
            (item.kind === 'MILESTONE' &&
              ((item.milestone as unknown as { visibility?: string })
                ?.visibility === 'OWNER_ONLY' ||
                (item.milestone as unknown as { visibility?: string })
                  ?.visibility === 'PRIVATE'));

          const cardClasses = [
            'story-card',
            'story-card-reference',
            `story-card-${item.kind.toLowerCase().replace('_', '-')}`,
          ]
            .filter(Boolean)
            .join(' ');

          const markerClass = index % 2 === 0 ? 'marker-berry' : 'marker-teal';

          return (
            <li key={storyItemKey(item)} className="story-timeline-item">
              <span
                className={`story-timeline-marker ${markerClass}`}
                aria-hidden="true"
              />
              <Link
                className="story-card-link"
                to={productPath}
                aria-label={`${presentation.kindLabel}: ${presentation.title}`}
              >
                <article className={cardClasses}>
                  <div className="story-card-thumb">
                    {item.kind === 'MEMORY' && firstMemoryAttachment ? (
                      <MemoryPreview
                        memoryId={item.memory.id}
                        attachmentId={firstMemoryAttachment.id}
                        loadImage={loadMemoryImage}
                      />
                    ) : (
                      <div
                        className={`story-card-thumb-fallback fallback-${item.kind.toLowerCase().replace('_', '-')}`}
                        aria-hidden="true"
                      >
                        {item.kind === 'HEART_MOMENT' ? (
                          <svg
                            viewBox="0 0 24 24"
                            width="24"
                            height="24"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                          </svg>
                        ) : item.kind === 'MILESTONE' ? (
                          <svg
                            viewBox="0 0 24 24"
                            width="24"
                            height="24"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M12 2l2.4 7.4h7.6l-6.1 4.5 2.3 7.1-6.2-4.5-6.2 4.5 2.3-7.1-6.1-4.5h7.6z" />
                          </svg>
                        ) : (
                          <svg
                            viewBox="0 0 24 24"
                            width="24"
                            height="24"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
                          </svg>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="story-card-main">
                    <h4 className="story-card-title">{presentation.title}</h4>

                    <div className="story-card-footer">
                      <time
                        dateTime={item.effectiveDate.toISOString().slice(0, 10)}
                      >
                        {formatStoryDate(item.effectiveDate, locale)}
                      </time>
                      <div className="story-card-footer-author">
                        {author ? (
                          <span className="momente-author-meta">
                            <AuthorAvatar
                              author={author}
                              profilesApi={profilesApi}
                              spaceId={spaceId}
                            />
                            <span>
                              {t('story.byAuthor', {
                                author: storyAuthorLabel(author.displayName),
                              })}
                            </span>
                          </span>
                        ) : (
                          <span>
                            {t('story.byAuthor', {
                              author: presentation.author,
                            })}
                          </span>
                        )}
                        {presentation.mediaLabel ? (
                          <span className="media-label">
                            <svg
                              viewBox="0 0 24 24"
                              width="12"
                              height="12"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              aria-hidden="true"
                            >
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <circle cx="8.5" cy="8.5" r="1.5" />
                              <path d="m21 15-5-5L5 21" />
                            </svg>
                            <span>{presentation.mediaLabel}</span>
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <div className="story-card-chips">
                      {isOwnerOnly ? (
                        <span className="story-chip story-chip-private">
                          <svg
                            className="chip-glyph"
                            viewBox="0 0 24 24"
                            width="11"
                            height="11"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                          </svg>
                          <span>{t('story.visibilityPrivate')}</span>
                        </span>
                      ) : item.kind === 'MEMORY' ? (
                        <span className="story-chip story-chip-memory">
                          <svg
                            className="chip-glyph"
                            viewBox="0 0 24 24"
                            width="11"
                            height="11"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
                          </svg>
                          <span>{presentation.kindLabel}</span>
                        </span>
                      ) : item.kind === 'MILESTONE' ? (
                        <span className="story-chip story-chip-milestone">
                          <svg
                            className="chip-glyph"
                            viewBox="0 0 24 24"
                            width="11"
                            height="11"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M12 2l2.4 7.4h7.6l-6.1 4.5 2.3 7.1-6.2-4.5-6.2 4.5 2.3-7.1-6.1-4.5h7.6z" />
                          </svg>
                          <span>{presentation.kindLabel}</span>
                        </span>
                      ) : item.kind === 'HEART_MOMENT' ? (
                        <span className="story-chip story-chip-heart">
                          <svg
                            className="chip-glyph"
                            viewBox="0 0 24 24"
                            width="11"
                            height="11"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                          </svg>
                          <span>{presentation.kindLabel}</span>
                        </span>
                      ) : null}
                    </div>
                  </div>
                </article>
              </Link>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
