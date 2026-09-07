import { useState, useCallback } from 'react';
import relationshipComponents from '../i18n/locales/relationshipComponents';
import './ThinkingOfYouButton.css';

export interface ThinkingOfYouButtonProps {
  partnerName?: string;
  onSend?: () => Promise<void> | void;
  variant?: 'compact' | 'full';
  disabled?: boolean;
  className?: string;
}

export function ThinkingOfYouButton({
  partnerName,
  onSend,
  variant = 'full',
  disabled = false,
  className = '',
}: ThinkingOfYouButtonProps) {
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');

  const handleClick = useCallback(async () => {
    if (state !== 'idle' || disabled) return;
    setState('sending');
    try {
      if (onSend) {
        await onSend();
      }
      setState('sent');
      setTimeout(() => {
        setState('idle');
      }, 2500);
    } catch {
      setState('idle');
    }
  }, [state, disabled, onSend]);

  const targetLabel = partnerName
    ? relationshipComponents.thinkingOfYouSendToPartner.replace(
        '{{partner}}',
        partnerName,
      )
    : relationshipComponents.thinkingOfYouAction;

  return (
    <button
      type="button"
      className={`thinking-of-you-btn thinking-of-you-${variant} state-${state} ${className}`}
      onClick={handleClick}
      disabled={disabled || state === 'sending'}
      aria-label={targetLabel}
      title={targetLabel}
    >
      <span className="thinking-of-you-icon-wrapper" aria-hidden="true">
        {state === 'sent' ? (
          <svg
            aria-hidden="true"
            className="thinking-of-you-icon sent-icon"
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        ) : (
          <svg
            aria-hidden="true"
            className="thinking-of-you-icon heart-icon"
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="currentColor"
          >
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
          </svg>
        )}
      </span>

      {variant === 'full' && (
        <span className="thinking-of-you-label">
          {state === 'sent'
            ? relationshipComponents.thinkingOfYouSent
            : state === 'sending'
              ? relationshipComponents.thinkingOfYouSending
              : relationshipComponents.thinkingOfYouAction}
        </span>
      )}
    </button>
  );
}
