import type { ReactNode } from 'react';
import {
  PartnerAvatarPair,
  type PartnerAvatarPerson,
  type PartnerPresenceStatus,
} from './PartnerAvatarPair';
import relationshipComponents from '../i18n/locales/relationshipComponents';
import './CouplePresence.css';

export interface CouplePresenceProps {
  spaceTitle: string;
  primaryPerson: PartnerAvatarPerson;
  secondaryPerson?: PartnerAvatarPerson | null;
  status?: PartnerPresenceStatus;
  statusText?: string;
  relationshipDuration?: string;
  onDurationClick?: () => void;
  onInviteClick?: () => void;
  actions?: ReactNode;
  className?: string;
}

export function CouplePresence({
  spaceTitle,
  primaryPerson,
  secondaryPerson = null,
  status = 'connected',
  statusText,
  relationshipDuration,
  onDurationClick,
  onInviteClick,
  actions,
  className = '',
}: CouplePresenceProps) {
  const defaultStatusText =
    status === 'connected'
      ? relationshipComponents.couplePresenceConnected
      : status === 'waiting'
        ? relationshipComponents.couplePresenceWaiting
        : relationshipComponents.couplePresenceOffline;

  return (
    <section
      className={`couple-presence-card ${className}`}
      aria-labelledby="couple-presence-title"
    >
      <div className="couple-presence-main">
        <PartnerAvatarPair
          primaryPerson={primaryPerson}
          secondaryPerson={secondaryPerson}
          status={status}
          size="large"
          onInviteClick={onInviteClick}
        />

        <div className="couple-presence-details">
          <h2 id="couple-presence-title" className="couple-presence-title">
            {spaceTitle}
          </h2>

          <div className="couple-presence-meta">
            <span className={`couple-presence-indicator status-${status}`}>
              <span className="couple-presence-dot" aria-hidden="true" />
              <span className="couple-presence-status-text">
                {statusText || defaultStatusText}
              </span>
            </span>

            {relationshipDuration && (
              <>
                <span className="couple-presence-separator" aria-hidden="true">
                  ·
                </span>
                {onDurationClick ? (
                  <button
                    type="button"
                    className="couple-presence-duration-btn"
                    onClick={onDurationClick}
                    title={relationshipComponents.couplePresenceDurationAction}
                  >
                    {relationshipDuration}
                  </button>
                ) : (
                  <span className="couple-presence-duration-text">
                    {relationshipDuration}
                  </span>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {actions && <div className="couple-presence-actions">{actions}</div>}
    </section>
  );
}
