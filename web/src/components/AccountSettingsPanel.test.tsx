// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AccountApi } from '../api/generated/apis/AccountApi';
import { AccountDeletionStatus } from '../api/generated/models/AccountDeletionStatus';
import accountSettings from '../i18n/locales/accountSettings';
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
  fireEvent.click(
    screen.getByRole('button', { name: accountSettings.deleteAction }),
  );
  expect(screen.getByRole('dialog')).toBeDefined();
  expect(screen.getByText(accountSettings.consequencesTitle)).toBeDefined();
  expect(
    screen.getByRole('button', { name: accountSettings.exportBefore }),
  ).toBeDefined();

  fireEvent.click(
    screen.getByRole('button', { name: accountSettings.continueAction }),
  );
  expect(screen.getByText(accountSettings.finalTitle)).toBeDefined();
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

    expect(screen.getByText(accountSettings.demoTitle)).toBeDefined();
    const deleteButton = screen.getByRole('button', {
      name: accountSettings.deleteAction,
    }) as HTMLButtonElement;
    expect(deleteButton.disabled).toBe(true);
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
      name: accountSettings.submitAction,
    }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);

    fireEvent.change(screen.getByLabelText(accountSettings.confirmLabel), {
      target: { value: 'WRONG' },
    });
    expect(submit.disabled).toBe(true);

    fireEvent.change(screen.getByLabelText(accountSettings.confirmLabel), {
      target: { value: accountSettings.confirmPhrase },
    });
    expect(submit.disabled).toBe(false);
    fireEvent.click(submit);

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith({
        accountDeletionRequest: { confirmation: 'DELETE_ACCOUNT' },
      });
      expect(onDeletionAccepted).toHaveBeenCalledTimes(1);
    });
  });

  it('keeps the confirmation flow open when the server rejects the request', async () => {
    vi.spyOn(
      AccountApi.prototype,
      'deleteOwnAccountApiV1AccountDeletionPost',
    ).mockRejectedValue({ status: 503 });
    const onDeletionAccepted = vi.fn();
    renderPanel({ onDeletionAccepted });

    advanceToFinalConfirmation();
    fireEvent.change(screen.getByLabelText(accountSettings.confirmLabel), {
      target: { value: accountSettings.confirmPhrase },
    });
    fireEvent.click(
      screen.getByRole('button', { name: accountSettings.submitAction }),
    );

    await waitFor(() => {
      expect(onDeletionAccepted).not.toHaveBeenCalled();
      expect(screen.getByRole('dialog')).toBeDefined();
      expect(document.querySelector('.ui-state')).not.toBeNull();
    });
  });
});
