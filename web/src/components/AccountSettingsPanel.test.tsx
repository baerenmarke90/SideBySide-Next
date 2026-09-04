// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AccountApi } from '../api/generated/apis/AccountApi';
import { AccountDeletionStatus } from '../api/generated/models/AccountDeletionStatus';
import { AccountSettingsPanel } from './AccountSettingsPanel';

function renderPanel({
  demoMode = false,
  onDeletionAccepted = vi.fn(),
}: {
  demoMode?: boolean;
  onDeletionAccepted?: () => void | Promise<void>;
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <AccountSettingsPanel
        apiBaseUrl="http://api.example.test"
        accessToken="test-token"
        demoMode={demoMode}
        onDeletionAccepted={onDeletionAccepted}
      />
    </QueryClientProvider>,
  );

  return { onDeletionAccepted };
}

function advanceToFinalConfirmation() {
  fireEvent.click(screen.getByRole('button', { name: 'Konto löschen' }));
  expect(screen.getByRole('dialog')).toBeDefined();
  expect(screen.getByText('Folgen der Kontolöschung')).toBeDefined();
  expect(
    screen.getByRole('link', { name: 'Vorher Daten exportieren' }),
  ).toHaveAttribute('href', '#settings-data');

  fireEvent.click(screen.getByRole('button', { name: 'Weiter' }));
  expect(screen.getByText('Kontolöschung bestätigen')).toBeDefined();
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('AccountSettingsPanel', () => {
  it('keeps self-service deletion unavailable for Demo Accounts', () => {
    const deleteSpy = vi.spyOn(
      AccountApi.prototype,
      'deleteOwnAccountApiV1AccountDeletionPost',
    );
    renderPanel({ demoMode: true });

    expect(
      screen.getByText('Kontolöschung in der Demo nicht verfügbar'),
    ).toBeDefined();
    expect(
      screen.getByText(
        'Demo-Konten werden von der Demo-Umgebung verwaltet und können hier nicht selbst gelöscht werden.',
      ),
    ).toBeDefined();
    const deleteButton = screen.getByRole('button', { name: 'Konto löschen' });
    expect(deleteButton).toBeDisabled();
    fireEvent.click(deleteButton);
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(deleteSpy).not.toHaveBeenCalled();
  });

  it('requires consequences review and exact typed confirmation before using the generated Account API', async () => {
    const deleteSpy = vi
      .spyOn(AccountApi.prototype, 'deleteOwnAccountApiV1AccountDeletionPost')
      .mockResolvedValue({
        acceptedAt: new Date('2026-09-05T00:00:00Z'),
        status: AccountDeletionStatus.PENDING,
      });
    const onDeletionAccepted = vi.fn();
    renderPanel({ onDeletionAccepted });

    advanceToFinalConfirmation();

    const submit = screen.getByRole('button', {
      name: 'Konto endgültig löschen',
    }) as HTMLButtonElement;
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Bestätigung'), {
      target: { value: 'KONTO LOSCHEN' },
    });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Bestätigung'), {
      target: { value: 'KONTO LÖSCHEN' },
    });
    expect(submit).not.toBeDisabled();
    fireEvent.click(submit);

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith({
        accountDeletionRequest: { confirmation: 'DELETE_ACCOUNT' },
      });
      expect(onDeletionAccepted).toHaveBeenCalledTimes(1);
    });
  });

  it('keeps the confirmation flow open when the server rejects deletion', async () => {
    vi.spyOn(
      AccountApi.prototype,
      'deleteOwnAccountApiV1AccountDeletionPost',
    ).mockRejectedValue({
      status: 503,
      code: 'ACCOUNT_DELETION_AUTHORITY_UNAVAILABLE',
    });
    const onDeletionAccepted = vi.fn();
    renderPanel({ onDeletionAccepted });

    advanceToFinalConfirmation();
    fireEvent.change(screen.getByLabelText('Bestätigung'), {
      target: { value: 'KONTO LÖSCHEN' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: 'Konto endgültig löschen' }),
    );

    await waitFor(() => {
      expect(onDeletionAccepted).not.toHaveBeenCalled();
      expect(screen.getByRole('dialog')).toBeDefined();
      expect(screen.getByText('Etwas ist schiefgelaufen')).toBeDefined();
    });
  });
});
