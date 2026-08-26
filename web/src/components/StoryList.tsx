import type { StoryItem } from '../api/generated/models/StoryItem';

function kindLabel(item: StoryItem): string {
  switch (item.kind) {
    case 'MEMORY':
      return `Erinnerung: ${item.memory.title}`;
    case 'HEART_MOMENT':
      return 'Herzmoment';
    case 'MILESTONE':
      return 'Meilenstein';
  }
}

export function StoryList({ items }: { items: StoryItem[] }) {
  if (items.length === 0) {
    return <p role="status">Noch keine Einträge in eurer Story.</p>;
  }

  return (
    <ol className="story-list" aria-label="Gemeinsame Story">
      {items.map((item, index) => (
        <li className="story-item" key={`${item.kind}-${item.effectiveDate.toISOString()}-${index}`}>
          <span className="story-kind">{kindLabel(item)}</span>
          <time dateTime={item.effectiveDate.toISOString().slice(0, 10)}>
            {item.effectiveDate.toLocaleDateString('de-DE')}
          </time>
        </li>
      ))}
    </ol>
  );
}
