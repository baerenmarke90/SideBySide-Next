import { Link } from 'react-router-dom';
import type { StoryItem } from '../api/generated/models/StoryItem';
import {
  heartMomentDetailPath,
  memoryDetailPath,
  milestoneDetailPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { MemoryPreview } from './MemoryPreview';
import {
  formatStoryDate,
  groupStoryItems,
  storyItemKey,
  storyItemPresentation,
} from './storyPresentation';
import { UiState } from './UiState';

function storyProductLink(item: StoryItem): { path: string; labelKey: string } {
  switch (item.kind) {
    case 'MEMORY':
      return {
        path: memoryDetailPath(item.memory.id),
        labelKey: 'memoryProduct.open',
      };
    case 'HEART_MOMENT':
      return {
        path: heartMomentDetailPath(item.heartMoment.id),
        labelKey: 'heartMomentProduct.open',
      };
    case 'MILESTONE':
      return {
        path: milestoneDetailPath(item.milestone.id),
        labelKey: 'milestoneProduct.open',
      };
  }
}

export function StoryList({
  items,
  loadMemoryImage,
}: {
  items: StoryItem[];
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
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
  const groups = groupStoryItems(items, locale);

  return (
    <section className="story-timeline" aria-label={t('story.aria')}>
      {groups.map((group) => (
        <section
          className="story-month"
          key={group.key}
          aria-labelledby={`month-${group.key}`}
        >
          <div className="month-heading">
            <span className="month-dot" aria-hidden="true" />
            <h3 id={`month-${group.key}`}>{group.label}</h3>
          </div>
          <ol className="story-list">
            {group.items.map((item) => {
              const presentation = storyItemPresentation(item, t);
              const firstMemoryAttachment =
                item.kind === 'MEMORY' ? item.memory.attachments[0] : undefined;
              const productLink = storyProductLink(item);
              const cardClasses = [
                'story-card',
                `story-card-${item.kind.toLowerCase().replace('_', '-')}`,
                firstMemoryAttachment ? 'has-image' : ''
              ].filter(Boolean).join(' ');

              return (
                <li key={storyItemKey(item)} className="sbs-motion-reveal">
                  <article className={cardClasses}>
                    <div className="story-card-meta">
                      <span className="kind-badge">
                        {presentation.kindLabel}
                      </span>
                      {presentation.sharedLabel ? (
                        <span className="shared-badge">
                          {presentation.sharedLabel}
                        </span>
                      ) : null}
                      <time
                        dateTime={item.effectiveDate.toISOString().slice(0, 10)}
                      >
                        {formatStoryDate(item.effectiveDate, locale)}
                      </time>
                    </div>
                    {item.kind === 'MEMORY' && firstMemoryAttachment ? (
                      <MemoryPreview
                        memoryId={item.memory.id}
                        attachmentId={firstMemoryAttachment.id}
                        loadImage={loadMemoryImage}
                      />
                    ) : null}
                    <h4>{presentation.title}</h4>
                    {presentation.preview ? (
                      <p className="story-preview">{presentation.preview}</p>
                    ) : null}
                    <div className="story-card-footer">
                      <span>
                        {t('story.byAuthor', { author: presentation.author })}
                      </span>
                      <div className="story-card-footer-actions">
                        {presentation.mediaLabel ? (
                          <span className="media-label">
                            ▧ {presentation.mediaLabel}
                          </span>
                        ) : null}
                        <Link
                          className="story-memory-link"
                          to={productLink.path}
                        >
                          {t(productLink.labelKey)}
                        </Link>
                      </div>
                    </div>
                  </article>
                </li>
              );
            })}
          </ol>
        </section>
      ))}
    </section>
  );
}
