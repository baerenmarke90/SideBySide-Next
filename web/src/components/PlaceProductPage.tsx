import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { PlaceDetail } from '../api/generated/models/PlaceDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  planningIfMatch,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { appRoutePath } from '../client/routes';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { PlanningRelationManager } from './PlanningRelationManager';
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

export function PlaceProductPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const { placeId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [coordinateError, setCoordinateError] = useState(false);
  const key = authorSummaryQueryKeys.placeDetail(spaceId, placeId);

  const placeQuery = useQuery({
    queryKey: key,
    queryFn: () => {
      if (!placeId) throw new Error('Missing Place route parameter.');
      return apiCall(() => apis.places.getPlace({ spaceId, placeId }));
    },
    enabled: Boolean(placeId),
    retry: false,
  });

  const updateMutation = useMutation({
    mutationFn: ({
      place,
      name,
      description,
      address,
      latitude,
      longitude,
    }: {
      place: PlaceDetail;
      name: string;
      description: string | null;
      address: string | null;
      latitude: number | null;
      longitude: number | null;
    }) =>
      apiCall(() =>
        apis.places.updatePlace({
          spaceId,
          placeId: place.id,
          ifMatch: planningIfMatch(place),
          placeUpdate: { name, description, address, latitude, longitude },
        }),
      ),
    onSuccess: async (place) => {
      queryClient.setQueryData(key, place);
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['m5-s3', 'places', spaceId],
        }),
        queryClient.invalidateQueries({ queryKey: key }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (place: PlaceDetail) =>
      apiCall(() =>
        apis.places.deletePlace({
          spaceId,
          placeId: place.id,
          ifMatch: planningIfMatch(place),
        }),
      ),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: key });
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'places', spaceId],
      });
      navigate(appRoutePath('more'), { replace: true });
    },
  });

  if (!placeId)
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  if (placeQuery.isLoading)
    return <UiState kind="loading" title={t('m5s3.place.loading')} />;
  if (placeQuery.error)
    return (
      <ProblemState
        error={placeQuery.error}
        onRetry={() => void placeQuery.refetch()}
      />
    );
  const place = placeQuery.data;
  if (!place) return null;

  function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!place) return;
    const data = new FormData(event.currentTarget);
    const latitudeRaw = String(data.get('latitude')).trim();
    const longitudeRaw = String(data.get('longitude')).trim();
    if (Boolean(latitudeRaw) !== Boolean(longitudeRaw)) {
      setCoordinateError(true);
      return;
    }
    setCoordinateError(false);
    const description = String(data.get('description')).trim();
    const address = String(data.get('address')).trim();
    updateMutation.mutate({
      place,
      name: String(data.get('name')).trim(),
      description: description || null,
      address: address || null,
      latitude: latitudeRaw ? Number(latitudeRaw) : null,
      longitude: longitudeRaw ? Number(longitudeRaw) : null,
    });
  }

  return (
    <div className="page planning-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('more')}>
            {t('m5s3.common.back')}
          </Link>
        }
        eyebrow={t('m5s3.place.detailEyebrow')}
        title={place.name}
        description={place.address || t('m5s3.place.noAddress')}
      />

      <div className="planning-detail-grid">
        <section className="planning-subsection">
          <h2>{t('m5s3.common.edit')}</h2>
          {place.capabilities.canEdit ? (
            <form className="form-grid" onSubmit={submitEdit}>
              <label htmlFor="place-edit-name">{t('m5s3.place.name')}</label>
              <input
                id="place-edit-name"
                name="name"
                required
                maxLength={200}
                defaultValue={place.name}
              />
              <label htmlFor="place-edit-description">
                {t('m5s3.common.description')}
              </label>
              <textarea
                id="place-edit-description"
                name="description"
                rows={4}
                defaultValue={place.description ?? ''}
              />
              <label htmlFor="place-edit-address">
                {t('m5s3.place.address')}
              </label>
              <input
                id="place-edit-address"
                name="address"
                defaultValue={place.address ?? ''}
              />
              <div className="planning-coordinate-grid">
                <div className="field-group">
                  <label htmlFor="place-edit-latitude">
                    {t('m5s3.place.latitude')}
                  </label>
                  <input
                    id="place-edit-latitude"
                    name="latitude"
                    type="number"
                    step="any"
                    min="-90"
                    max="90"
                    defaultValue={place.latitude ?? ''}
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="place-edit-longitude">
                    {t('m5s3.place.longitude')}
                  </label>
                  <input
                    id="place-edit-longitude"
                    name="longitude"
                    type="number"
                    step="any"
                    min="-180"
                    max="180"
                    defaultValue={place.longitude ?? ''}
                  />
                </div>
              </div>
              <p className="field-help">{t('m5s3.place.coordinateHelp')}</p>
              {coordinateError ? (
                <p className="field-error" role="alert">
                  {t('m5s3.place.coordinatePairError')}
                </p>
              ) : null}
              <button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending
                  ? t('m5s3.common.saving')
                  : t('m5s3.common.saveChanges')}
              </button>
              {updateMutation.error ? (
                <ProblemState
                  error={updateMutation.error}
                  onRetry={() => void placeQuery.refetch()}
                />
              ) : null}
            </form>
          ) : (
            <p className="planning-meta">{t('m5s3.common.readOnly')}</p>
          )}
        </section>

        <section className="planning-subsection">
          <h2>{t('m5s3.place.locationHeading')}</h2>
          {place.latitude != null && place.longitude != null ? (
            <p>
              {t('m5s3.place.coordinates', {
                latitude: place.latitude,
                longitude: place.longitude,
              })}
            </p>
          ) : (
            <p className="planning-meta">{t('m5s3.place.nameOnly')}</p>
          )}
          <p className="planning-meta">{t('m5s3.place.noMap')}</p>
        </section>
      </div>

      <PlanningRelationManager
        apis={apis}
        spaceId={spaceId}
        ownerKind="place"
        ownerId={place.id}
      />

      {place.capabilities.canDelete ? (
        <section
          className="planning-danger-zone"
          aria-labelledby="place-delete-heading"
        >
          <h2 id="place-delete-heading">{t('m5s3.common.deleteHeading')}</h2>
          <p>{t('m5s3.place.deleteConsequence')}</p>
          {!confirmDelete ? (
            <button
              type="button"
              className="danger"
              onClick={() => setConfirmDelete(true)}
            >
              {t('m5s3.common.delete')}
            </button>
          ) : (
            <div className="planning-confirm-row">
              <button
                type="button"
                className="danger"
                onClick={() => deleteMutation.mutate(place)}
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
          )}
          {deleteMutation.error ? (
            <ProblemState
              error={deleteMutation.error}
              onRetry={() => void placeQuery.refetch()}
            />
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
