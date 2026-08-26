import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { StoryItem } from './api/generated';
import { StoryCard } from './App';
import { ReferenceFlow } from './referenceFlow';

const inertFlow = {} as ReferenceFlow;

describe('StoryCard', () => {
  it('renders a generated MEMORY item as a labelled semantic article', () => {
    const item = {
      kind: 'MEMORY',
      effectiveDate: new Date('2026-08-26T00:00:00Z'),
      memory: {
        id: 'memory-1',
        title: 'Sonnenuntergang am See',
        attachments: [],
        author: { id: 'account-1', displayName: 'Alex' },
      },
    } as StoryItem;

    render(<StoryCard item={item} flow={inertFlow} spaceId="space-1" />);

    expect(screen.getByRole('article', { name: 'Sonnenuntergang am See' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Sonnenuntergang am See' })).toBeInTheDocument();
    expect(screen.getByText('Erinnerung')).toBeInTheDocument();
  });
});
