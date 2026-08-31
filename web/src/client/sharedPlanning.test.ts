import { describe, expect, it } from 'vitest';
import type { StoryItem } from '../api/generated/models/StoryItem';
import {
  dateFromInput,
  dateOnlyInput,
  moveItemIds,
  planningIfMatch,
  storyRelationTarget,
} from './sharedPlanning';

describe('shared planning client helpers', () => {
  it('uses the server resource version as If-Match', () => {
    expect(planningIfMatch({ version: 7 })).toBe('7');
  });

  it('keeps date-only fields stable in UTC', () => {
    const value = dateFromInput('2026-08-31');
    expect(value?.toISOString()).toBe('2026-08-31T00:00:00.000Z');
    expect(dateOnlyInput(value)).toBe('2026-08-31');
  });

  it('moves collection ids without changing the item set', () => {
    expect(moveItemIds(['a', 'b', 'c'], 1, -1)).toEqual(['b', 'a', 'c']);
    expect(moveItemIds(['a', 'b', 'c'], 1, 1)).toEqual(['a', 'c', 'b']);
    expect(moveItemIds(['a', 'b', 'c'], 0, -1)).toEqual(['a', 'b', 'c']);
  });

  it('derives relation choices only from the shared Story contract', () => {
    const item = {
      kind: 'MEMORY',
      effectiveDate: new Date('2026-08-31T00:00:00Z'),
      memory: {
        id: 'memory-1',
        title: 'Am See',
        happenedOn: new Date('2026-08-31T00:00:00Z'),
        createdAt: new Date('2026-08-31T12:00:00Z'),
        author: { id: 'account-1', displayName: 'Alex' },
        attachments: [],
        capabilities: { canComment: true, canDelete: true, canEdit: true },
      },
    } satisfies StoryItem;

    expect(storyRelationTarget(item)).toMatchObject({
      id: 'memory-1',
      kind: 'MEMORY',
      label: 'Am See',
    });
  });
});
