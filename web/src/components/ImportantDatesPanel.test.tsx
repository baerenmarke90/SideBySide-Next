// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { DateRepeat } from '../api/generated/models/DateRepeat';
import type { ImportantDateView } from '../api/generated/models/ImportantDateView';
import { ImportantDateType } from '../api/generated/models/ImportantDateType';
import { PersonRelationship } from '../api/generated/models/PersonRelationship';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import importantDates from '../i18n/locales/importantDates';
import { ImportantDatesPanel } from './ImportantDatesPanel';

afterEach(() => cleanup());

const person: RelatedPersonView = {
  id: 'person-1',
  displayName: 'Lisa Beispielname',
  relationship: PersonRelationship.FRIEND,
  birthday: null,
  birthdayYearKnown: false,
  visibility: ContentVisibility.SHARED,
  showBirthdayOnDashboard: false,
  avatarAttachmentId: null,
  version: 2,
  createdAt: new Date('2026-01-01T00:00:00Z'),
  updatedAt: new Date('2026-01-02T00:00:00Z'),
};

const date: ImportantDateView = {
  id: 'date-1',
  label: 'Unser erster gemeinsamer Urlaub am Meer',
  date: new Date('2026-09-21T00:00:00Z'),
  relatedPersonId: person.id,
  repeats: DateRepeat.ANNUALLY,
  type: ImportantDateType.ANNIVERSARY,
  visibility: ContentVisibility.SHARED,
  version: 3,
  createdAt: new Date('2026-01-01T00:00:00Z'),
  updatedAt: new Date('2026-01-02T00:00:00Z'),
};

function createMockPeopleApi(
  dates: ImportantDateView[] = [date],
): PeopleApi {
  return {
    listImportantDatesApiV1SpacesSpaceIdImportantDatesGet: vi
      .fn()
      .mockResolvedValue(dates),
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
          version: 4,
          createdAt: new Date(),
          updatedAt: new Date(),
        }),
      ),
    deleteImportantDateApiV1SpacesSpaceIdImportantDatesDateIdDelete: vi
      .fn()
      .mockResolvedValue(undefined),
  } as unknown as PeopleApi;
}

function renderPanel(peopleApi = createMockPeopleApi()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ImportantDatesPanel
        peopleApi={peopleApi}
        spaceId="space-1"
        people={[person]}
      />
    </QueryClientProvider>,
  );
}

describe('ImportantDatesPanel mobile-first surface', () => {
  it('renders W50 as a date-led timeline with relationship and explicit privacy context', async () => {
    const { container } = renderPanel();

    const card = await screen.findByRole('button', {
      name: new RegExp(date.label, 'i'),
    });
    expect(card.classList.contains('important-date-card')).toBe(true);
    expect(card.querySelector('.important-date-marker')).not.toBeNull();
    expect(card.textContent).toContain(date.label);
    expect(card.textContent).toContain(person.displayName);
    expect(card.textContent).toContain(importantDates.type.ANNIVERSARY);
    expect(card.textContent).toContain(importantDates.repeats.ANNUALLY);
    expect(card.textContent).toContain(importantDates.visibility.SHARED);
    expect(card.querySelector('.important-date-visibility-icon svg')).not.toBeNull();
    expect(container.querySelector('.important-date-chip')).toBeNull();
  });

  it('opens W51 as a focused Compact-first sheet with date and meaning first', async () => {
    const { container } = renderPanel();
    await screen.findByRole('button', { name: new RegExp(date.label, 'i') });

    const trigger = screen.getByRole('button', {
      name: importantDates.create,
    });
    trigger.focus();
    fireEvent.click(trigger);

    const dialog = screen.getByRole('dialog');
    expect(dialog.classList.contains('focused-editor-sheet')).toBe(true);
    expect(dialog.classList.contains('important-date-editor')).toBe(true);
    expect(
      screen.getByRole('heading', { name: importantDates.createTitle }),
    ).not.toBeNull();

    const dateInput = screen.getByLabelText(
      importantDates.dateLabel,
    ) as HTMLInputElement;
    const labelInput = screen.getByLabelText(
      importantDates.labelLabel,
    ) as HTMLInputElement;
    expect(dateInput).toBe(document.activeElement);
    expect(dateInput.required).toBe(true);
    expect(labelInput.required).toBe(true);
    expect(labelInput.maxLength).toBe(160);

    const disclosure = container.querySelector(
      '.important-date-editor .focused-editor-disclosure',
    ) as HTMLDetailsElement | null;
    expect(disclosure).not.toBeNull();
    expect(disclosure?.open).toBe(false);
    expect(screen.getByLabelText(importantDates.visibilityLabel)).not.toBeNull();
    expect(
      within(dialog).getByRole('button', { name: importantDates.create }),
    ).not.toBeNull();

    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(trigger).toBe(document.activeElement);
  });

  it('protects W53 by confirming discard on Escape after a create draft changes', async () => {
    renderPanel();
    await screen.findByRole('button', { name: new RegExp(date.label, 'i') });

    fireEvent.click(
      screen.getByRole('button', { name: importantDates.create }),
    );
    const dialog = screen.getByRole('dialog');
    fireEvent.change(screen.getByLabelText(importantDates.labelLabel), {
      target: { value: 'Ein neuer besonderer Tag' },
    });

    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(
      screen.getByText(importantDates.discardTitle, { selector: 'strong' }),
    ).not.toBeNull();
    expect(screen.getByRole('dialog')).not.toBeNull();

    fireEvent.click(
      screen.getByRole('button', { name: importantDates.keepEditing }),
    );
    expect(screen.queryByText(importantDates.discardTitle)).toBeNull();
    expect(screen.getByRole('dialog')).not.toBeNull();
  });

  it('opens W52 from the full timeline item and separates delete from Save', async () => {
    const { container } = renderPanel();
    const card = await screen.findByRole('button', {
      name: new RegExp(date.label, 'i'),
    });
    fireEvent.click(card);

    const dialog = screen.getByRole('dialog');
    expect(
      screen.getByRole('heading', { name: importantDates.editTitle }),
    ).not.toBeNull();
    expect(screen.getByDisplayValue(date.label)).not.toBeNull();

    const disclosure = container.querySelector(
      '.important-date-editor .focused-editor-disclosure',
    ) as HTMLDetailsElement;
    expect(disclosure.open).toBe(true);
    expect(screen.getByDisplayValue(person.displayName)).not.toBeNull();

    const deleteButton = within(dialog).getByRole('button', {
      name: importantDates.delete,
    });
    expect(deleteButton.closest('.focused-editor-danger-zone')).not.toBeNull();
    expect(
      within(dialog).getByRole('button', { name: importantDates.saveChanges }),
    ).not.toBeNull();
  });

  it('protects W53 delete confirmation before invoking the delete mutation', async () => {
    const peopleApi = createMockPeopleApi();
    renderPanel(peopleApi);
    const card = await screen.findByRole('button', {
      name: new RegExp(date.label, 'i'),
    });
    fireEvent.click(card);

    fireEvent.click(
      screen.getByRole('button', { name: importantDates.delete }),
    );
    expect(
      screen.getByText(importantDates.deleteQuestion, { selector: 'strong' }),
    ).not.toBeNull();
    expect(
      peopleApi.deleteImportantDateApiV1SpacesSpaceIdImportantDatesDateIdDelete,
    ).not.toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole('button', { name: importantDates.deleteConfirm }),
    );
    await waitFor(() => {
      expect(
        peopleApi.deleteImportantDateApiV1SpacesSpaceIdImportantDatesDateIdDelete,
      ).toHaveBeenCalledTimes(1);
    });
  });

  it('preserves API semantics when saving an edited date', async () => {
    const peopleApi = createMockPeopleApi();
    renderPanel(peopleApi);
    const card = await screen.findByRole('button', {
      name: new RegExp(date.label, 'i'),
    });
    fireEvent.click(card);

    fireEvent.change(screen.getByLabelText(importantDates.labelLabel), {
      target: { value: 'Unser Jahrestag am Meer' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: importantDates.saveChanges }),
    );

    await waitFor(() => {
      expect(
        peopleApi.updateImportantDateApiV1SpacesSpaceIdImportantDatesDateIdPut,
      ).toHaveBeenCalledTimes(1);
    });
    const call = (
      peopleApi.updateImportantDateApiV1SpacesSpaceIdImportantDatesDateIdPut as ReturnType<
        typeof vi.fn
      >
    ).mock.calls[0][0];
    expect(call.dateId).toBe(date.id);
    expect(call.ifMatch).toBe(String(date.version));
    expect(call.importantDateFields.label).toBe('Unser Jahrestag am Meer');
    expect(call.importantDateFields.relatedPersonId).toBe(person.id);
    expect(call.importantDateFields.visibility).toBe(date.visibility);
  });

  it('keeps long labels intact instead of truncating relationship content in the DOM', async () => {
    const longLabel =
      'Der sehr lange besondere Tag, an dem wir gemeinsam eine außergewöhnlich lange Reise begonnen haben';
    renderPanel(createMockPeopleApi([{ ...date, label: longLabel }]));

    const card = await screen.findByRole('button', {
      name: new RegExp('Der sehr lange besondere Tag', 'i'),
    });
    expect(card.textContent).toContain(longLabel);
    fireEvent.click(card);
    expect(screen.getByDisplayValue(longLabel)).not.toBeNull();
  });
});
