import type { StoryItem } from '../api/generated/models/StoryItem';
import {
  formatStoryDate,
  groupStoryItems,
  storyItemKey,
  storyItemPresentation,
} from './storyPresentation';

export function StoryList({ items }: { items: StoryItem[] }) {
  if (items.length === 0) {
    return (
      <div className="story-empty" role="status">
        <span className="story-empty-mark" aria-hidden="true">♥</span>
        <h3>Eure Story beginnt hier.</h3>
        <p>Haltet euren ersten gemeinsamen Moment fest.</p>
      </div>
    );
  }

  const groups = groupStoryItems(items);

  return (
    <div className="story-timeline" aria-label="Gemeinsame Story">
      {groups.map((group) => (
        <section className="story-month" key={group.key} aria-labelledby={`month-${group.key}`}>
          <div className="month-heading">
            <span className="month-dot" aria-hidden="true" />
            <h3 id={`month-${group.key}`}>{group.label}</h3>
          </div>
          <ol className="story-list">
            {group.items.map((item) => {
              const presentation = storyItemPresentation(item);
              return (
                <li key={storyItemKey(item)}>
                  <article className={`story-card story-card-${item.kind.toLowerCase().replace('_', '-')}`}>
                    <div className="story-card-meta">
                      <span className="kind-badge">{presentation.kindLabel}</span>
                      {presentation.sharedLabel && <span className="shared-badge">{presentation.sharedLabel}</span>}
                      <time dateTime={item.effectiveDate.toISOString().slice(0, 10)}>
                        {formatStoryDate(item.effectiveDate)}
                      </time>
                    </div>
                    <h4>{presentation.title}</h4>
                    {presentation.preview && <p className="story-preview">{presentation.preview}</p>}
                    <div className="story-card-footer">
                      <span>von {presentation.author}</span>
                      {presentation.mediaLabel && <span className="media-label">▧ {presentation.mediaLabel}</span>}
                    </div>
                  </article>
                </li>
              );
            })}
          </ol>
        </section>
      ))}
    </div>
  );
}
