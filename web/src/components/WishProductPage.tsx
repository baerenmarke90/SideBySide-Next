import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { WishDetail } from '../api/generated/models/WishDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  loadAllPlaces,
  planningIfMatch,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { appRoutePath } from '../client/routes';
import { invalidateDashboard } from '../client/dashboardQueries';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ListEntryIconButton } from './ListEntryActions';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './SharedPlanningPages.css';

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

export function WishProductPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const { wishId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const key = authorSummaryQueryKeys.wishDetail(spaceId, wishId);

  const wishQuery = useQuery({
    queryKey: key,
    queryFn: () => {
      if (!wishId) throw new Error('Missing Wish route parameter.');
      return apiCall(() => apis.wishes.getWish({ spaceId, wishId }));
    },
    enabled: Boolean(wishId),
    retry: false,
  });

  const placesQuery = useQuery({
    queryKey: ['m5-s3', 'wish-conversion-places', spaceId],
    queryFn: () => apiCall(() => loadAllPlaces(apis, spaceId)),
    staleTime: 30_000,
    retry: false,
  });

  const updateMutation = useMutation({
    mutationFn: ({ wish, title }: { wish: WishDetail; title: string }) =>
      apiCall(() =>
        apis.wishes.updateWish({
          spaceId,
          wishId: wish.id,
          ifMatch: planningIfMatch(wish),
          wishUpdate: { title },
        }),
      ),
    onSuccess: async (wish) => {
      queryClient.setQueryData(key, wish);
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'wishes', spaceId],
      });
      setIsEditing(false);
      setConfirmDelete(false);
    },
  });

  const convertMutation = useMutation({
    mutationFn: ({
      wish,
      title,
      description,
      placeId,
    }: {
      wish: WishDetail;
      title?: string;
      description?: string;
      placeId?: string;
    }) =>
      apiCall(() =>
        apis.plans.convertWishToPlan({
          spaceId,
          wishId: wish.id,
          ifMatch: planningIfMatch(wish),
          wishToPlan: { title, description, placeId },
        }),
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['m5-s3', 'wishes', spaceId],
        }),
        queryClient.invalidateQueries({
          queryKey: ['m5-s3', 'plans', spaceId],
        }),
        queryClient.invalidateQueries({ queryKey: key }),
        invalidateDashboard(queryClient, spaceId),
      ]);
      navigate(appRoutePath('plan'), { replace: true });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (wish: WishDetail) =>
      apiCall(() =>
        apis.wishes.deleteWish({
          spaceId,
          wishId: wish.id,
          ifMatch: planningIfMatch(wish),
        }),
      ),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: key });
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'wishes', spaceId],
      });
      navigate(appRoutePath('plan'), { replace: true });
    },
  });

  if (!wishId) {
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  }
  if (wishQuery.isLoading) {
    return <UiState kind="loading" title={t('m5s3.wish.loading')} />;
  }
  if (wishQuery.error) {
    return (
      <ProblemState
        error={wishQuery.error}
        onRetry={() => void wishQuery.refetch()}
      />
    );
  }
  const wish = wishQuery.data;
  if (!wish) return null;

  function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!wish) return;
    const data = new FormData(event.currentTarget);
    updateMutation.mutate({ wish, title: String(data.get('title')).trim() });
  }

  function submitConvert(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!wish) return;
    const data = new FormData(event.currentTarget);
    const title = String(data.get('title')).trim();
    const description = String(data.get('description')).trim();
    const placeId = String(data.get('placeId')).trim();
    convertMutation.mutate({
      wish,
      title: title || undefined,
      description: description || undefined,
      placeId: placeId || undefined,
    });
  }

  return (
    <div className="page planning-page">
      {isEditing ? (
        <form
          id="wish-edit-form"
          onSubmit={(e) => {
            e.preventDefault();
            submitEdit(e);
          }}
        />
      ) : null}
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('plan')}>
            {t('m5s3.common.back')}
          </Link>
        }
        eyebrow={t('m5s3.wish.detailEyebrow')}
        title={wish.title}
        titleEditor={
          isEditing ? (
            <input
              form="wish-edit-form"
              name="title"
              required
              maxLength={200}
              defaultValue={wish.title}
              aria-label={t('m5s3.common.title')}
            />
          ) : undefined
        }
        description={t(`m5s3.wish.status.${wish.status}`)}
        titleAction={
          wish.capabilities.canEdit && !isEditing ? (
            <ListEntryIconButton
              icon="edit"
              className="tertiary"
              label={t('common.edit')}
              onClick={() => setIsEditing(true)}
            />
          ) : undefined
        }
      />

      <div className="planning-detail-grid">
        {isEditing ? (
          <section className="planning-subsection">
            <h2>{t('m5s3.common.edit')}</h2>
            <div className="form-grid">
              <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                <button
                  form="wish-edit-form"
                  type="submit"
                  disabled={updateMutation.isPending}
                >
                  {updateMutation.isPending
                    ? t('m5s3.common.saving')
                    : t('m5s3.common.saveChanges')}
                </button>
                <button
                  type="button"
                  className="tertiary"
                  onClick={() => {
                    setIsEditing(false);
                    setConfirmDelete(false);
                  }}
                >
                  {t('common.cancel')}
                </button>
              </div>
              {updateMutation.error ? (
                <ProblemState
                  error={updateMutation.error}
                  onRetry={() => void wishQuery.refetch()}
                />
              ) : null}
            </div>

            {wish.capabilities.canDelete ? (
              <div style={{ marginTop: 'var(--space-8)' }}>
                {!confirmDelete ? (
                  <button
                    type="button"
                    className="button-link danger-link"
                    onClick={() => setConfirmDelete(true)}
                  >
                    {t('m5s3.common.delete')}
                  </button>
                ) : (
                  <section
                    className="planning-danger-zone"
                    aria-labelledby="wish-delete-heading"
                  >
                    <h2 id="wish-delete-heading">
                      {t('m5s3.common.deleteHeading')}
                    </h2>
                    <p>{t('m5s3.wish.deleteConsequence')}</p>
                    <div className="planning-confirm-row">
                      <button
                        type="button"
                        className="danger"
                        onClick={() => deleteMutation.mutate(wish)}
                        disabled={deleteMutation.isPending}
                      >
                        {deleteMutation.isPending
                          ? t('m5s3.common.deleting')
                          : t('m5s3.common.confirmDelete')}
                      </button>
                      <button
                        type="button"
                        className="tertiary"
                        onClick={() => setConfirmDelete(false)}
                      >
                        {t('common.cancel')}
                      </button>
                    </div>
                    {deleteMutation.error ? (
                      <ProblemState
                        error={deleteMutation.error}
                        onRetry={() => void wishQuery.refetch()}
                      />
                    ) : null}
                  </section>
                )}
              </div>
            ) : null}
          </section>
        ) : null}

        {wish.status === 'OPEN' && wish.capabilities.canEdit ? (
          <section className="planning-subsection">
            <h2>{t('m5s3.wish.convertHeading')}</h2>
            <p>{t('m5s3.wish.convertIntro')}</p>
            <form className="form-grid" onSubmit={submitConvert}>
              <label htmlFor="wish-plan-title">
                {t('m5s3.wish.planTitle')}
              </label>
              <input
                id="wish-plan-title"
                name="title"
                maxLength={200}
                placeholder={wish.title}
              />
              <label htmlFor="wish-plan-description">
                {t('m5s3.common.description')}
              </label>
              <textarea
                id="wish-plan-description"
                name="description"
                rows={4}
              />
              <label htmlFor="wish-plan-place">{t('m5s3.common.place')}</label>
              <select id="wish-plan-place" name="placeId" defaultValue="">
                <option value="">{t('m5s3.common.noPlace')}</option>
                {placesQuery.data?.map((place) => (
                  <option key={place.id} value={place.id}>
                    {place.name}
                  </option>
                ))}
              </select>
              <button type="submit" disabled={convertMutation.isPending}>
                {convertMutation.isPending
                  ? t('m5s3.wish.converting')
                  : t('m5s3.wish.convert')}
              </button>
              {convertMutation.error ? (
                <ProblemState
                  error={convertMutation.error}
                  onRetry={() => void wishQuery.refetch()}
                />
              ) : null}
            </form>
          </section>
        ) : null}
      </div>
    </div>
  );
}
