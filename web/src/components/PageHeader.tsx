import type { ReactNode } from 'react';

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
  before,
  className = '',
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  before?: ReactNode;
  className?: string;
}) {
  return (
    <>
      {before}
      <header className={`page-heading ${className}`.trim()}>
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
          {description ? <p>{description}</p> : null}
        </div>
        {action ? <div className="page-heading-action">{action}</div> : null}
      </header>
    </>
  );
}
