import { describe, expect, it, vi } from 'vitest';
import type { StoryItem } from '../api/generated/models/StoryItem';
import {
  dateFromInput,
  dateOnlyInput,
  loadAllPlaces,
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

  it('loads every page of selectable places', async () => {
    const listPlaces = vi
      .fn()
      .mockResolvedValueOnce({
        items: [{ id: 'place-1', name: 'First place' }],
        nextCursor: 'cursor-2',
      })
      .mockResolvedValueOnce({
        items: [{ id: 'place-2', name: 'Second place' }],
        nextCursor: null,
      });
    const apis = { places: { listPlaces } } as unknown as Parameters<
      typeof loadAllPlaces
    >[0];

    const places = await loadAllPlaces(apis, 'space-1');

    expect(places.map((place) => place.id)).toEqual(['place-1', 'place-2']);
    expect(listPlaces).toHaveBeenNthCalledWith(1, {
      spaceId: 'space-1',
      cursor: null,
      limit: 50,
    });
    expect(listPlaces).toHaveBeenNthCalledWith(2, {
      spaceId: 'space-1',
      cursor: 'cursor-2',
      limit: 50,
    });
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
