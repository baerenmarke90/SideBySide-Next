import type { StoryItem } from '../api/generated/models/StoryItem';
import { resolvedLocale, useTranslation } from '../i18n';
import { MemoryPreview } from './MemoryPreview';
import {
  formatStoryDate,
  groupStoryItems,
  storyItemKey,
  storyItemPresentation,
} from './storyPresentation';

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
      <div className="story-empty" role="status">
        <span className="story-empty-mark" aria-hidden="true">
          ♥
        </span>
        <h3>{t('story.emptyTitle')}</h3>
        <p>{t('story.emptyBody')}</p>
      </div>
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
              return (
                <li key={storyItemKey(item)}>
                  <article
                    className={`story-card story-card-${item.kind.toLowerCase().replace('_', '-')}`}
                  >
                    <div className="story-card-meta">
                      <span className="kind-badge">
                        {presentation.kindLabel}
                      </span>
                      {presentation.sharedLabel && (
                        <span className="shared-badge">
                          {presentation.sharedLabel}
                        </span>
                      )}
                      <time
                        dateTime={item.effectiveDate.toISOString().slice(0, 10)}
                      >
                        {formatStoryDate(item.effectiveDate, locale)}
                      </time>
                    </div>
                    {item.kind === 'MEMORY' && firstMemoryAttachment && (
                      <MemoryPreview
                        memoryId={item.memory.id}
                        attachmentId={firstMemoryAttachment.id}
                        loadImage={loadMemoryImage}
                      />
                    )}
                    <h4>{presentation.title}</h4>
                    {presentation.preview && (
                      <p className="story-preview">{presentation.preview}</p>
                    )}
                    <div className="story-card-footer">
                      <span>
                        {t('story.byAuthor', { author: presentation.author })}
                      </span>
                      {presentation.mediaLabel && (
                        <span className="media-label">
                          ▧ {presentation.mediaLabel}
                        </span>
                      )}
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
