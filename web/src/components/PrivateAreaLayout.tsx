import { type ReactNode, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import {
  PRIVATE_COLLECTIONS_PATH,
  PRIVATE_GIFT_IDEAS_PATH,
  PRIVATE_NOTES_PATH,
} from '../client/privateArea';
import { appRoutePath } from '../client/routes';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';

export function PrivateAreaFrame({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  return (
    <div className="page private-area-page">
      <section
        className="private-area-context"
        aria-label={t('privateArea.privacyLabel')}
      >
        <div className="private-area-header-info">
          <h1 className="private-area-title-row">
            {t('privateArea.eyebrow')}
          </h1>
          <p className="private-area-intro-text">{t('privateArea.intro')}</p>
        </div>
      </section>
      <nav
        className="private-area-nav"
        aria-label={t('privateArea.navigation.aria')}
      >
        <NavLink to={PRIVATE_NOTES_PATH}>
          {t('privateArea.navigation.notes')}
        </NavLink>
        <NavLink to={PRIVATE_GIFT_IDEAS_PATH}>
          {t('privateArea.navigation.gifts')}
        </NavLink>
        <NavLink to={PRIVATE_COLLECTIONS_PATH}>
          {t('privateArea.navigation.collections')}
        </NavLink>
      </nav>
      {children}
    </div>
  );
}

export function PrivateAreaBackToMore() {
  const { t } = useTranslation();
  return (
    <Link className="back-link" to={appRoutePath('more')}>
      {t('privateArea.backToMore')}
    </Link>
  );
}

export function DeleteConfirmation({
  onDelete,
  pending,
  error,
}: {
  onDelete: () => void;
  pending: boolean;
  error: Error | null;
}) {
  const { t } = useTranslation();
  const [confirming, setConfirming] = useState(false);
  return (
    <section
      className="private-area-danger"
      aria-label={t('privateArea.delete')}
    >
      {!confirming ? (
        <button
          type="button"
          className="secondary"
          onClick={() => setConfirming(true)}
        >
          {t('privateArea.delete')}
        </button>
      ) : (
        <div className="private-area-delete-confirmation" role="alert">
          <div>
            <h2>{t('privateArea.deleteConfirmTitle')}</h2>
            <p>{t('privateArea.deleteConfirmBody')}</p>
          </div>
          <div className="private-area-actions">
            <button
              type="button"
              className="tertiary"
              onClick={() => setConfirming(false)}
              disabled={pending}
            >
              {t('privateArea.deleteCancel')}
            </button>
            <button type="button" onClick={onDelete} disabled={pending}>
              {pending
                ? t('privateArea.deleting')
                : t('privateArea.deleteConfirm')}
            </button>
          </div>
        </div>
      )}
      {error ? <ProblemState error={error} /> : null}
    </section>
  );
}

export function LoadMoreButton({
  hasMore,
  loading,
  onLoadMore,
}: {
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
}) {
  const { t } = useTranslation();
  if (!hasMore) return null;
  return (
    <button
      type="button"
      className="secondary"
      onClick={onLoadMore}
      disabled={loading}
    >
      {loading ? t('privateArea.loadingMore') : t('privateArea.loadMore')}
    </button>
  );
}
