// @vitest-environment jsdom
import {
  cleanup,
  render,
  screen,
  fireEvent,
  waitFor,
} from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import relationshipComponents from '../i18n/locales/relationshipComponents';
import { ThinkingOfYouButton } from './ThinkingOfYouButton';

describe('ThinkingOfYouButton', () => {
  afterEach(() => {
    cleanup();
  });

  const expectedPartnerLabel =
    relationshipComponents.thinkingOfYouSendToPartner.replace(
      '{{partner}}',
      'Lea',
    );

  it('renders default idle state with personalized partner label', () => {
    render(<ThinkingOfYouButton partnerName="Lea" />);

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    });
    expect(btn).toBeDefined();
    expect(
      screen.getByText(relationshipComponents.thinkingOfYouAction),
    ).toBeDefined();
  });

  it('transitions to sending and then sent on click', async () => {
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(<ThinkingOfYouButton partnerName="Lea" onSend={onSend} />);

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    });
    fireEvent.click(btn);

    expect(onSend).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(
        screen.getByText(relationshipComponents.thinkingOfYouSent),
      ).toBeDefined();
    });
    expect(btn.className).toContain('state-sent');
  });

  it('respects disabled state', () => {
    const onSend = vi.fn();
    render(
      <ThinkingOfYouButton partnerName="Lea" disabled={true} onSend={onSend} />,
    );

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    fireEvent.click(btn);
    expect(onSend).not.toHaveBeenCalled();
  });

  it('renders compact variant with icon only', () => {
    render(<ThinkingOfYouButton variant="compact" partnerName="Lea" />);

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    });
    expect(btn.className).toContain('thinking-of-you-compact');
    expect(
      screen.queryByText(relationshipComponents.thinkingOfYouAction),
    ).toBeNull();
  });
});
