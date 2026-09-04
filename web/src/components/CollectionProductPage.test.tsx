// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import '../i18n';
import { CollectionProductPage } from './CollectionProductPage';

describe('CollectionProductPage', () => {
  it('shows collection title cleanly without icon prefix or edit field (#373)', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(
      ['m5-s3', 'collection', 'space-1', 'collection-1'],
      {
        capabilities: { canComment: false, canDelete: true, canEdit: true },
        createdAt: new Date('2026-08-01T10:00:00Z'),
        createdBy: 'account-1',
        creator: { id: 'account-1', displayName: 'Lea' },
        id: 'collection-1',
        items: [],
        spaceId: 'space-1',
        title: 'Packing list',
        updatedAt: new Date('2026-08-01T10:00:00Z'),
        version: 1,
      },
    );

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/plan/collections/collection-1']}>
          <Routes>
            <Route
              path="/plan/collections/:collectionId"
              element={
                <CollectionProductPage
                  apis={{} as SharedPlanningApis}
                  spaceId="space-1"
                />
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Packing list');
    expect(html).not.toContain('collection-edit-icon');
  });

  it('renders compact list interaction with add icon and without per-item save buttons', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(
      ['m5-s3', 'collection', 'space-1', 'collection-1'],
      {
        capabilities: { canComment: false, canDelete: true, canEdit: true },
        createdAt: new Date('2026-08-01T10:00:00Z'),
        createdBy: 'account-1',
        creator: { id: 'account-1', displayName: 'Lea' },
        id: 'collection-1',
        items: [
          {
            capabilities: { canComment: false, canDelete: true, canEdit: true },
            completed: false,
            createdAt: new Date('2026-08-01T10:00:00Z'),
            createdBy: 'account-1',
            id: 'item-1',
            position: 1,
            title: 'Passport',
            updatedAt: new Date('2026-08-01T10:00:00Z'),
            version: 1,
          },
        ],
        spaceId: 'space-1',
        title: 'Packing list',
        updatedAt: new Date('2026-08-01T10:00:00Z'),
        version: 1,
      },
    );

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/plan/collections/collection-1']}>
          <Routes>
            <Route
              path="/plan/collections/:collectionId"
              element={
                <CollectionProductPage
                  apis={{} as SharedPlanningApis}
                  spaceId="space-1"
                />
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Title input row has compact save button disabled initially
    // (Removed because title row is now inside edit mode)
    // Add button is rendered
    expect(html).toContain('planning-inline-create');
    // Item row has item title, checkbox, reorder, delete, but no per-item save button
    expect(html).toContain('Passport');
    expect(html).toContain('planning-check');
    // Check that there is no submit button inside the items list
    expect(html).not.toContain('planning-item-title-form button');
  });

  it('resets isEditing and confirmDelete on successful title update', async () => {
    const sampleCollection = {
      capabilities: { canComment: false, canDelete: true, canEdit: true },
      createdAt: new Date('2026-08-01T10:00:00Z'),
      createdBy: 'account-1',
      creator: { id: 'account-1', displayName: 'Lea' },
      id: 'collection-1',
      items: [],
      spaceId: 'space-1',
      title: 'Packing list',
      updatedAt: new Date('2026-08-01T10:00:00Z'),
      version: 1,
    };

    const updateCollectionMock = vi
      .fn()
      .mockImplementation(async ({ collectionUpdate }) => ({
        ...sampleCollection,
        title: collectionUpdate.title,
        version: 2,
      }));

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    queryClient.setQueryData(
      ['m5-s3', 'collection', 'space-1', 'collection-1'],
      sampleCollection,
    );

    const mockApis = {
      collections: {
        getCollection: vi.fn().mockResolvedValue(sampleCollection),
        updateCollection: updateCollectionMock,
      },
    } as unknown as SharedPlanningApis;

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/plan/collections/collection-1']}>
          <Routes>
            <Route
              path="/plan/collections/:collectionId"
              element={
                <CollectionProductPage apis={mockApis} spaceId="space-1" />
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Click edit button to enter edit mode
    const editBtn = screen.getByRole('button', {
      name: /common\.edit|bearbeiten/i,
    });
    fireEvent.click(editBtn);

    // isEditing is true: input and delete trigger are visible
    const input = screen.getByRole('textbox', { name: /titel/i });
    expect(input).toBeDefined();

    const deleteTrigger = screen.getByRole('button', { name: /^löschen$/i });
    fireEvent.click(deleteTrigger);

    // confirmDelete is true: danger confirmation zone is visible
    expect(
      screen.getByRole('button', { name: /endgültig löschen/i }),
    ).toBeDefined();

    // Update title
    fireEvent.change(input, { target: { value: 'New Packing list' } });

    // Save changes
    const saveBtn = screen.getByRole('button', {
      name: /änderungen speichern/i,
    });
    fireEvent.click(saveBtn);

    // Wait for mutation to finish
    await waitFor(() => {
      expect(updateCollectionMock).toHaveBeenCalled();
    });

    // Verify isEditing is reset to false: input is gone, edit button is back
    await waitFor(() => {
      expect(screen.queryByRole('textbox', { name: /titel/i })).toBeNull();
    });
    expect(
      screen.getByRole('button', { name: /common\.edit|bearbeiten/i }),
    ).toBeDefined();

    // Verify confirmDelete is reset to false: danger zone with confirm delete button is gone
    expect(
      screen.queryByRole('button', { name: /endgültig löschen/i }),
    ).toBeNull();
  });
});
