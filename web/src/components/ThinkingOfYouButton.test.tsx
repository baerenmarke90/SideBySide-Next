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

  it('uses only the partner first name in the personalized idle label', () => {
    render(<ThinkingOfYouButton partnerName="Lea Winter" />);

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    });
    expect(btn.getAttribute('aria-label')).toBe(expectedPartnerLabel);
    expect(btn.getAttribute('title')).toBe(expectedPartnerLabel);
    expect(btn.getAttribute('aria-label')).not.toContain('Winter');
    expect(btn.getAttribute('title')).not.toContain('Winter');
    expect(
      screen.getByText(relationshipComponents.thinkingOfYouAction),
    ).toBeDefined();
  });

  it('transitions to sending and then sent on click with proper aria-busy and label semantics', async () => {
    let resolveSend!: () => void;
    const sendPromise = new Promise<void>((resolve) => {
      resolveSend = resolve;
    });
    const onSend = vi.fn().mockReturnValue(sendPromise);
    render(<ThinkingOfYouButton partnerName="Lea" onSend={onSend} />);

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    });
    fireEvent.click(btn);

    expect(onSend).toHaveBeenCalledTimes(1);
    expect(btn.getAttribute('aria-busy')).toBe('true');
    expect(btn.getAttribute('aria-label')).toBe(
      relationshipComponents.thinkingOfYouSending,
    );

    resolveSend();

    await waitFor(() => {
      expect(btn.getAttribute('aria-busy')).toBeNull();
      expect(btn.getAttribute('aria-label')).toBe(
        relationshipComponents.thinkingOfYouSent,
      );
      expect(btn.className).toContain('state-sent');
    });
  });

  it('handles error in onSend gracefully and restores idle state', async () => {
    const onSend = vi.fn().mockRejectedValue(new Error('Network error'));
    render(<ThinkingOfYouButton partnerName="Lea" onSend={onSend} />);

    const btn = screen.getByRole('button', {
      name: expectedPartnerLabel,
    });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(btn.getAttribute('aria-busy')).toBeNull();
      expect(btn.getAttribute('aria-label')).toBe(expectedPartnerLabel);
      expect(btn.className).toContain('state-idle');
    });
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
