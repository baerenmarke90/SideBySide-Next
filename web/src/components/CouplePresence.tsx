import { useId, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
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
  durationLinkTo?: string;
  durationTitle?: string;
  onDurationClick?: () => void;
  onInviteClick?: () => void;
  actions?: ReactNode;
  headingLevel?: 'h1' | 'h2';
  className?: string;
}

export function CouplePresence({
  spaceTitle,
  primaryPerson,
  secondaryPerson = null,
  status = 'connected',
  statusText,
  relationshipDuration,
  durationLinkTo,
  durationTitle,
  onDurationClick,
  onInviteClick,
  actions,
  headingLevel = 'h2',
  className = '',
}: CouplePresenceProps) {
  const generatedId = useId();
  const titleId = `couple-presence-title-${generatedId}`;

  const defaultStatusText =
    status === 'connected'
      ? relationshipComponents.couplePresenceConnected
      : status === 'waiting'
        ? relationshipComponents.couplePresenceWaiting
        : relationshipComponents.couplePresenceOffline;

  const HeadingTag = headingLevel;

  return (
    <section
      className={`couple-presence-card ${className}`}
      aria-labelledby={titleId}
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
          <HeadingTag id={titleId} className="couple-presence-title">
            {spaceTitle}
          </HeadingTag>

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
                {durationLinkTo ? (
                  <Link
                    to={durationLinkTo}
                    className="couple-presence-duration-btn today-hero-duration-link"
                    title={
                      durationTitle ||
                      relationshipComponents.couplePresenceDurationAction
                    }
                  >
                    <span className="today-hero-pill-icon" aria-hidden="true">
                      <svg
                        viewBox="0 0 24 24"
                        width="12"
                        height="12"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path d="M12 2l2.4 7.4h7.6l-6.1 4.5 2.3 7.1-6.2-4.5-6.2 4.5 2.3-7.1-6.1-4.5h7.6z" />
                      </svg>
                    </span>
                    <span>{relationshipDuration}</span>
                  </Link>
                ) : onDurationClick ? (
                  <button
                    type="button"
                    className="couple-presence-duration-btn"
                    onClick={onDurationClick}
                    title={
                      durationTitle ||
                      relationshipComponents.couplePresenceDurationAction
                    }
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
