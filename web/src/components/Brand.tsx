import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

export const PRODUCT_NAME = 'SidebySide';

type BrandProps = {
  to?: string;
  ariaLabel?: string;
  inverse?: boolean;
  /**
   * Kept temporarily for call-site compatibility while the obsolete "Next"
   * suffix is removed from the product UI. Product suffixes are no longer
   * rendered.
   */
  suffix?: ReactNode;
};

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" focusable="false">
        <title>{PRODUCT_NAME}</title>
        <circle cx="12" cy="16" r="6.75" />
        <circle cx="20" cy="16" r="6.75" />
      </svg>
    </span>
  );
}

function BrandContent() {
  return (
    <>
      <BrandMark />
      <span className="brand-name">
        <strong>{PRODUCT_NAME}</strong>
      </span>
    </>
  );
}

export function Brand({ to, ariaLabel, inverse = false }: BrandProps) {
  const className = `brand${inverse ? ' brand-inverse' : ''}`;

  if (to) {
    return (
      <Link className={className} to={to} aria-label={ariaLabel}>
        <BrandContent />
      </Link>
    );
  }

  return (
    <div className={`${className} brand-static`}>
      <BrandContent />
    </div>
  );
}
