import relationshipComponents from '../i18n/locales/relationshipComponents';
import './VisibilityBadge.css';

export type VisibilityType =
  | 'SPACE_SHARED'
  | 'OWNER_ONLY'
  | 'TEMPORARY_SHARED'
  | 'SHARED'
  | 'PRIVATE';

export interface VisibilityBadgeProps {
  visibility: VisibilityType;
  size?: 'small' | 'medium';
  showLabel?: boolean;
  customLabel?: string;
  className?: string;
}

function normalizeVisibility(
  visibility: VisibilityType,
): 'shared' | 'private' | 'temporary' {
  if (visibility === 'SPACE_SHARED' || visibility === 'SHARED') return 'shared';
  if (visibility === 'OWNER_ONLY' || visibility === 'PRIVATE') return 'private';
  return 'temporary';
}

export function VisibilityBadge({
  visibility,
  size = 'medium',
  showLabel = true,
  customLabel,
  className = '',
}: VisibilityBadgeProps) {
  const normalized = normalizeVisibility(visibility);

  const defaultLabel =
    normalized === 'shared'
      ? relationshipComponents.visibilityShared
      : normalized === 'private'
        ? relationshipComponents.visibilityPrivate
        : relationshipComponents.visibilityTemporary;

  const label = customLabel || defaultLabel;

  return (
    <span
      className={`visibility-badge visibility-${normalized} visibility-size-${size} ${className}`}
      role="status"
      aria-label={label}
      title={label}
    >
      <span className="visibility-badge-icon" aria-hidden="true">
        {normalized === 'shared' ? (
          // Two interlocking rings (eimir. symbol)
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <title>{label}</title>
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M9 4.5a5.5 5.5 0 103.54 9.7 5.5 5.5 0 101.92-7.4A5.47 5.47 0 009 4.5zM5.5 10a3.5 3.5 0 115.65 2.76A5.47 5.47 0 009.5 15.5a3.5 3.5 0 01-4-5.5zm9 4a3.5 3.5 0 11-1.65-2.76 5.47 5.47 0 001.65-2.74A3.5 3.5 0 0114.5 14z"
            />
          </svg>
        ) : normalized === 'private' ? (
          // Subtle lock icon
          <svg
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <title>{label}</title>
            <rect x="5" y="11" width="14" height="10" rx="2" />
            <path d="M8 11V7a4 4 0 018 0v4" />
          </svg>
        ) : (
          // Hourglass / clock icon
          <svg
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <title>{label}</title>
            <circle cx="12" cy="12" r="9" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        )}
      </span>

      {showLabel && <span className="visibility-badge-label">{label}</span>}
    </span>
  );
}
