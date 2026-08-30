import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" focusable="false">
        <title>SideBySide</title>
        <circle cx="12" cy="16" r="6.75" />
        <circle cx="20" cy="16" r="6.75" />
      </svg>
    </span>
  );
}

function BrandContent({ suffix }: { suffix?: ReactNode }) {
  return (
    <>
      <BrandMark />
      <span className="brand-name">
        <strong>SideBySide</strong>
        {suffix}
      </span>
    </>
  );
}

export function Brand({
  to,
  ariaLabel,
  inverse = false,
  suffix,
}: {
  to?: string;
  ariaLabel?: string;
  inverse?: boolean;
  suffix?: ReactNode;
}) {
  const className = `brand${inverse ? ' brand-inverse' : ''}`;

  if (to) {
    return (
      <Link className={className} to={to} aria-label={ariaLabel}>
        <BrandContent suffix={suffix} />
      </Link>
    );
  }

  return (
    <div className={`${className} brand-static`}>
      <BrandContent suffix={suffix} />
    </div>
  );
}
