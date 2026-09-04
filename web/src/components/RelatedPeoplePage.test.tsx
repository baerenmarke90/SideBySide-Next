// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { PersonRelationship } from '../api/generated/models/PersonRelationship';
import { RelatedPersonDeletePolicy } from '../api/generated/models/RelatedPersonDeletePolicy';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import de from '../i18n/locales/de';
import people from '../i18n/locales/people';
import { DeleteRelatedPersonDialogContent, RelatedPeoplePage } from './RelatedPeoplePage';

const person: RelatedPersonView = {
  id: 'person-1',
  displayName: 'Lisa',
  relationship: PersonRelationship.FRIEND,
  birthday: new Date('1995-05-12T00:00:00Z'),
  birthdayYearKnown: true,
  visibility: ContentVisibility.SHARED,
  avatarAttachmentId: null,
  version: 3,
  createdAt: new Date('2026-01-01T00:00:00Z'),
  updatedAt: new Date('2026-01-02T00:00:00Z'),
};

function renderChoice(
  policy:
    | typeof RelatedPersonDeletePolicy.preserve
    | typeof RelatedPersonDeletePolicy.cascade
    | null,
  cascadeConfirmed = false,
): string {
  return renderToStaticMarkup(
    <DeleteRelatedPersonDialogContent
      person={person}
      pending={false}
      error={null}
      choice={{ policy, cascadeConfirmed }}
      onSelectPolicy={() => undefined}
      onCascadeConfirmed={() => undefined}
      onCancel={() => undefined}
      onDelete={() => undefined}
    />,
  );
}

describe('RelatedPerson delete dialog', () => {
  it('starts without a delete-policy default and exposes dialog semantics', () => {
    const html = renderChoice(null);

    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
    expect(html).toContain('value="preserve"');
    expect(html).toContain('value="cascade"');
    expect(html).not.toContain('checked=""');
    expect(html).not.toContain('role="alert"');
    expect(html).toContain('disabled=""');
  });

  it('allows preserve without presenting a destructive warning', () => {
    const html = renderChoice(RelatedPersonDeletePolicy.preserve);

    expect(html).toContain('checked="" value="preserve"');
    expect(html).not.toContain('role="alert"');
    expect(html).not.toContain('disabled=""');
  });

  it('shows a privacy-safe warning and blocks unconfirmed cascade', () => {
    const html = renderChoice(RelatedPersonDeletePolicy.cascade);

    expect(html).toContain('checked="" value="cascade"');
    expect(html).toContain('role="alert"');
    expect(html).toContain(people.deletePrivacyNote);
    expect(html).toContain(people.deleteCascadeWarningBody);
    expect(html).toContain('disabled=""');
  });

  it('enables cascade only after the explicit second confirmation', () => {
    const html = renderChoice(RelatedPersonDeletePolicy.cascade, true);

    expect(html).toContain('role="alert"');
    expect(html.match(/checked=""/g)).toHaveLength(2);
    expect(html).not.toContain('disabled=""');
  });
});

describe('RelatedPeoplePage redesigned surface', () => {
  function createMockPeopleApi(initialPeople: RelatedPersonView[] = [person]): PeopleApi {
    return {
      listRelatedPersonsApiV1SpacesSpaceIdRelatedPersonsGet: vi.fn().mockResolvedValue(initialPeople),
      createRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPost: vi.fn().mockImplementation(({ relatedPersonFields }) =>
        Promise.resolve({
          id: 'person-new',
          ...relatedPersonFields,
          version: 1,
          createdAt: new Date(),
          updatedAt: new Date(),
        }),
      ),
      updateRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdPut: vi.fn().mockImplementation(({ personId, relatedPersonFields }) =>
        Promise.resolve({
          id: personId,
          ...relatedPersonFields,
          version: 2,
          createdAt: new Date(),
          updatedAt: new Date(),
        }),
      ),
      deleteRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdDelete: vi.fn().mockResolvedValue(undefined),
      listImportantDatesApiV1SpacesSpaceIdImportantDatesGet: vi.fn().mockResolvedValue([]),
    } as unknown as PeopleApi;
  }

  function renderRelatedPeoplePage(peopleApi = createMockPeopleApi()) {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Infinity } },
    });
    return render(
      <QueryClientProvider client={queryClient}>
        <RelatedPeoplePage peopleApi={peopleApi} spaceId="space-1" />
      </QueryClientProvider>,
    );
  }

  it('renders person list as primary surface without side rail form', async () => {
    const { container } = renderRelatedPeoplePage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Lisa' })).not.toBeNull();
    });

    // No permanent side rail
    expect(container.querySelector('.layout-rail')).toBeNull();
    expect(container.querySelector('.layout-split')).toBeNull();

    const card = container.querySelector('.people-card');
    expect(card).not.toBeNull();
    expect(card?.textContent).toContain(people.relationship.FRIEND);
    expect(card?.textContent).toContain(people.visibility.SHARED);
    expect(card?.textContent).toContain('LI');
  });

  it('opens create modal dialog on add person button click', async () => {
    renderRelatedPeoplePage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Lisa' })).not.toBeNull();
    });

    const addBtn = screen.getByRole('button', {
      name: new RegExp(people.addPersonAction, 'i'),
    });
    fireEvent.click(addBtn);

    const dialog = screen.getByRole('dialog');
    expect(dialog).not.toBeNull();
    expect(
      screen.getByRole('heading', { name: people.createTitle }),
    ).not.toBeNull();
    expect(screen.getByLabelText(people.nameLabel)).not.toBeNull();

    // Close via Escape key
    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('opens edit modal dialog on card click and allows deleting', async () => {
    renderRelatedPeoplePage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Lisa' })).not.toBeNull();
    });

    const card = screen.getByRole('heading', { name: 'Lisa' }).closest('.people-card');
    expect(card).not.toBeNull();
    if (!card) throw new Error('card not found');
    fireEvent.click(card);

    const editDialog = screen.getByRole('dialog');
    expect(editDialog).not.toBeNull();
    expect(
      screen.getByRole('heading', { name: people.editTitle }),
    ).not.toBeNull();
    expect(screen.getByDisplayValue('Lisa')).not.toBeNull();

    // Has delete action
    const deleteBtn = screen.getByRole('button', { name: people.delete });
    expect(deleteBtn).not.toBeNull();

    // Clicking delete opens delete confirmation dialog
    fireEvent.click(deleteBtn);
    expect(
      screen.getByRole('heading', { name: people.deleteTitle }),
    ).not.toBeNull();
    expect(
      screen.getByText(new RegExp(people.deletePreserveTitle, 'i')),
    ).not.toBeNull();

    // Cancel returns to page
    const cancelBtn = screen.getByRole('button', { name: de.common.cancel });
    fireEvent.click(cancelBtn);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('manages body scroll lock and revokes avatar object URLs on replacement and unmount', async () => {
    document.body.style.overflow = 'visible';
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    const createObjectURLSpy = vi.fn().mockReturnValue('blob:test-avatar-1');
    const revokeObjectURLSpy = vi.fn();
    URL.createObjectURL = createObjectURLSpy;
    URL.revokeObjectURL = revokeObjectURLSpy;

    renderRelatedPeoplePage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Lisa' })).not.toBeNull();
    });

    const addBtn = screen.getByRole('button', {
      name: new RegExp(people.addPersonAction, 'i'),
    });
    fireEvent.click(addBtn);

    expect(document.body.style.overflow).toBe('hidden');

    const fileInput = screen.getByLabelText(people.avatarLabel);
    const file1 = new File(['image1'], 'avatar1.png', { type: 'image/png' });
    fireEvent.change(fileInput, { target: { files: [file1] } });

    expect(createObjectURLSpy).toHaveBeenCalledWith(file1);

    // Replace with second file
    createObjectURLSpy.mockReturnValue('blob:test-avatar-2');
    const file2 = new File(['image2'], 'avatar2.png', { type: 'image/png' });
    fireEvent.change(fileInput, { target: { files: [file2] } });

    // First URL revoked
    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:test-avatar-1');

    // Close modal via close button
    const closeBtn = screen.getByRole('button', { name: people.closeDialogAria });
    fireEvent.click(closeBtn);

    // Second URL revoked on unmount
    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:test-avatar-2');
    expect(document.body.style.overflow).toBe('visible');

    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
  });
});
