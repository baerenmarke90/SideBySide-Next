// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import type { ImportantDateView } from '../api/generated/models/ImportantDateView';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import { ImportantDateType } from '../api/generated/models/ImportantDateType';
import { DateRepeat } from '../api/generated/models/DateRepeat';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { PersonRelationship } from '../api/generated/models/PersonRelationship';
import { ImportantDatesPanel } from './ImportantDatesPanel';

describe('ImportantDatesPanel', () => {
  const samplePerson: RelatedPersonView = {
    id: 'person-1',
    displayName: 'Alex',
    relationship: PersonRelationship.FRIEND,
    birthday: new Date('1990-05-15T00:00:00Z'),
    birthdayYearKnown: true,
    avatarAttachmentId: null,
    visibility: ContentVisibility.SHARED,
    version: 1,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  const sampleDate: ImportantDateView = {
    id: 'date-1',
    label: 'Unser Jahrestag',
    date: new Date('2024-06-20T00:00:00Z'),
    type: ImportantDateType.ANNIVERSARY,
    repeats: DateRepeat.ANNUALLY,
    relatedPersonId: 'person-1',
    visibility: ContentVisibility.SHARED,
    version: 1,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  let mockPeopleApi: PeopleApi;

  beforeEach(() => {
    mockPeopleApi = {
      listImportantDatesApiV1SpacesSpaceIdImportantDatesGet: vi
        .fn()
        .mockResolvedValue([sampleDate]),
      createImportantDateApiV1SpacesSpaceIdImportantDatesPost: vi
        .fn()
        .mockImplementation(({ importantDateFields }) =>
          Promise.resolve({
            id: 'date-new',
            ...importantDateFields,
            version: 1,
            createdAt: new Date(),
            updatedAt: new Date(),
          }),
        ),
      updateImportantDateApiV1SpacesSpaceIdImportantDatesDateIdPut: vi
        .fn()
        .mockImplementation(({ dateId, importantDateFields }) =>
          Promise.resolve({
            id: dateId,
            ...importantDateFields,
            version: 2,
            createdAt: new Date(),
            updatedAt: new Date(),
          }),
        ),
      deleteImportantDateApiV1SpacesSpaceIdImportantDatesDateIdDelete: vi
        .fn()
        .mockResolvedValue(undefined),
    } as unknown as PeopleApi;
  });

  function renderPanel(dates = [sampleDate]) {
    mockPeopleApi.listImportantDatesApiV1SpacesSpaceIdImportantDatesGet = vi
      .fn()
      .mockResolvedValue(dates);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Infinity } },
    });
    return render(
      <QueryClientProvider client={queryClient}>
        <ImportantDatesPanel
          peopleApi={mockPeopleApi}
          spaceId="space-1"
          people={[samplePerson]}
        />
      </QueryClientProvider>,
    );
  }

  it('renders heading Besondere Tage and top add button without manual refresh', async () => {
    renderPanel();

    expect(
      await screen.findByRole('heading', { level: 2, name: /Besondere Tage/i }),
    ).toBeTruthy();
    expect(
      screen.getByRole('button', { name: /Besonderen Tag festhalten/i }),
    ).toBeTruthy();
    // Manual refresh button must not exist
    expect(screen.queryByRole('button', { name: /aktualisieren/i })).toBeNull();
  });

  it('displays dates in clickable cards without inline edit/delete buttons', async () => {
    renderPanel();

    const card = await screen.findByRole('button', {
      name: /Unser Jahrestag/i,
    });
    expect(card).toBeTruthy();

    // No inline edit or delete buttons on card
    expect(screen.queryByRole('button', { name: /^Bearbeiten$/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /^Löschen$/i })).toBeNull();
  });

  it('opens create modal when clicking + button, dirty checks on cancel', async () => {
    const user = userEvent.setup();
    renderPanel();

    const addBtn = await screen.findByRole('button', {
      name: /Besonderen Tag festhalten/i,
    });
    await user.click(addBtn);

    // Dialog title
    expect(
      screen.getByRole('heading', {
        level: 2,
        name: /Besonderen Tag festhalten/i,
      }),
    ).toBeTruthy();

    // Type into label
    const labelInput = screen.getByLabelText(/Anlass/i);
    await user.type(labelInput, 'Konzert');

    // Click close/cancel - should show discard confirmation
    const cancelBtn = screen.getByRole('button', { name: /Abbrechen/i });
    await user.click(cancelBtn);

    expect(
      screen.getByText(/Ungespeicherte Änderungen verwerfen\?/i),
    ).toBeTruthy();

    // Click Weiter bearbeiten
    await user.click(
      screen.getByRole('button', { name: /Weiter bearbeiten/i }),
    );
    expect(
      screen.queryByText(/Ungespeicherte Änderungen verwerfen\?/i),
    ).toBeNull();

    // Click cancel again and confirm discard
    await user.click(cancelBtn);
    await user.click(
      screen.getByRole('button', { name: /Änderungen verwerfen/i }),
    );

    // Dialog closed
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('clicking a card opens edit dialog with delete capability inside', async () => {
    const user = userEvent.setup();
    renderPanel();

    const card = await screen.findByRole('button', {
      name: /Unser Jahrestag/i,
    });
    await user.click(card);

    expect(
      screen.getByRole('heading', { level: 2, name: /Besonderen Tag ändern/i }),
    ).toBeTruthy();
    expect(screen.getByDisplayValue('Unser Jahrestag')).toBeTruthy();

    // Delete button inside modal
    const deleteBtn = screen.getByRole('button', { name: /Löschen/i });
    await user.click(deleteBtn);

    // Delete confirmation prompt
    expect(
      screen.getByText(/Diesen besonderen Tag wirklich löschen\?/i),
    ).toBeTruthy();
    const confirmDeleteBtn = screen.getByRole('button', {
      name: /Besonderen Tag löschen/i,
    });
    await user.click(confirmDeleteBtn);

    await waitFor(() => {
      expect(
        mockPeopleApi.deleteImportantDateApiV1SpacesSpaceIdImportantDatesDateIdDelete,
      ).toHaveBeenCalledWith({
        dateId: 'date-1',
        spaceId: 'space-1',
        ifMatch: '1',
      });
    });
  });
});
