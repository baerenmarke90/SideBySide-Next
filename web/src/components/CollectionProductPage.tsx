import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { CollectionDetail } from '../api/generated/models/CollectionDetail';
import type { CollectionItemDetail } from '../api/generated/models/CollectionItemDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  planningIfMatch,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { appRoutePath } from '../client/routes';
import { useTranslation } from '../i18n';
import {
  ListEntryIconButton,
  useListItemReorder,
} from './ListEntryActions';
import { PageHeader } from './PageHeader';
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

export function CollectionProductPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const { collectionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const key = ['m5-s3', 'collection', spaceId, collectionId] as const;

  const collectionQuery = useQuery({
    queryKey: key,
    queryFn: () => {
      if (!collectionId) throw new Error('Missing Collection route parameter.');
      return apiCall(() =>
        apis.collections.getCollection({ spaceId, collectionId }),
      );
    },
    enabled: Boolean(collectionId),
    retry: false,
  });

  const commitCollection = async (collection: CollectionDetail) => {
    queryClient.setQueryData(key, collection);
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'collections', spaceId],
      }),
      queryClient.invalidateQueries({ queryKey: key }),
    ]);
  };

  const updateCollection = useMutation({
    mutationFn: ({
      collection,
      title,
    }: {
      collection: CollectionDetail;
      title: string;
    }) =>
      apiCall(() =>
        apis.collections.updateCollection({
          spaceId,
          collectionId: collection.id,
          ifMatch: planningIfMatch(collection),
          collectionUpdate: { title },
        }),
      ),
    onSuccess: commitCollection,
  });

  const createItem = useMutation({
    mutationFn: ({
      collection,
      title,
    }: {
      collection: CollectionDetail;
      title: string;
    }) =>
      apiCall(() =>
        apis.collections.createCollectionItem({
          spaceId,
          collectionId: collection.id,
          collectionItemCreate: { title },
        }),
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: key });
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'collections', spaceId],
      });
    },
  });

  const updateItem = useMutation({
    mutationFn: ({
      collection,
      item,
      title,
      completed,
    }: {
      collection: CollectionDetail;
      item: CollectionItemDetail;
      title?: string;
      completed?: boolean;
    }) =>
      apiCall(() =>
        apis.collections.updateCollectionItem({
          spaceId,
          collectionId: collection.id,
          itemId: item.id,
          ifMatch: planningIfMatch(item),
          collectionItemUpdate: { title, completed },
        }),
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: key });
    },
  });

  const deleteItem = useMutation({
    mutationFn: ({
      collection,
      item,
    }: {
      collection: CollectionDetail;
      item: CollectionItemDetail;
    }) =>
      apiCall(() =>
        apis.collections.deleteCollectionItem({
          spaceId,
          collectionId: collection.id,
          itemId: item.id,
          ifMatch: planningIfMatch(item),
        }),
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: key });
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'collections', spaceId],
      });
    },
  });

  const reorderItems = useMutation({
    mutationFn: ({
      collection,
      itemIds,
    }: {
      collection: CollectionDetail;
      itemIds: string[];
    }) =>
      apiCall(() =>
        apis.collections.reorderCollectionItems({
          spaceId,
          collectionId: collection.id,
          ifMatch: planningIfMatch(collection),
          collectionOrder: { itemIds },
        }),
      ),
    onSuccess: commitCollection,
  });

  const deleteCollection = useMutation({
    mutationFn: (collection: CollectionDetail) =>
      apiCall(() =>
        apis.collections.deleteCollection({
          spaceId,
          collectionId: collection.id,
          ifMatch: planningIfMatch(collection),
        }),
      ),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: key });
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'collections', spaceId],
      });
      navigate(appRoutePath('planning'), { replace: true });
    },
  });

  const baseItemIds = [...(collectionQuery.data?.items ?? [])]
    .sort((left, right) => left.position - right.position)
    .map((item) => item.id);
  const reorder = useListItemReorder({
    itemIds: baseItemIds,
    disabled:
      !collectionQuery.data?.capabilities.canEdit || reorderItems.isPending,
    onReorder: (itemIds) => {
      const currentCollection = collectionQuery.data;
      if (!currentCollection) return;
      reorderItems.mutate({ collection: currentCollection, itemIds });
    },
  });

  if (!collectionId)
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  if (collectionQuery.isLoading)
    return <UiState kind="loading" title={t('m5s3.collection.loading')} />;
  if (collectionQuery.error)
    return (
      <ProblemState
        error={collectionQuery.error}
        onRetry={() => void collectionQuery.refetch()}
      />
    );
  const collection = collectionQuery.data;
  if (!collection) return null;
  const itemById = new Map(collection.items.map((item) => [item.id, item]));
  const items = reorder.orderedItemIds
    .map((itemId) => itemById.get(itemId))
    .filter((item): item is CollectionItemDetail => Boolean(item));

  function submitCollection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!collection) return;
    const data = new FormData(event.currentTarget);
    updateCollection.mutate({
      collection,
      title: String(data.get('title')).trim(),
    });
  }

  function submitItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!collection) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    createItem.mutate(
      { collection, title: String(data.get('title')).trim() },
      { onSuccess: () => form.reset() },
    );
  }

  function submitItemTitle(
    event: FormEvent<HTMLFormElement>,
    item: CollectionItemDetail,
  ) {
    event.preventDefault();
    if (!collection) return;
    const data = new FormData(event.currentTarget);
    updateItem.mutate({
      collection,
      item,
      title: String(data.get('title')).trim(),
    });
  }

  const itemMutationError =
    createItem.error ||
    updateItem.error ||
    deleteItem.error ||
    reorderItems.error;

  return (
    <div className="page planning-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('planning')}>
            {t('m5s3.common.back')}
          </Link>
        }
        eyebrow={t('m5s3.collection.detailEyebrow')}
        title={collection.title}
        description={t('m5s3.collection.itemCount', { count: items.length })}
      />

      {collection.capabilities.canEdit ? (
        <section className="planning-subsection">
          <h2>{t('m5s3.common.edit')}</h2>
          <form className="form-grid" onSubmit={submitCollection}>
            <label htmlFor="collection-edit-title">
              {t('m5s3.common.title')}
            </label>
            <input
              id="collection-edit-title"
              name="title"
              required
              maxLength={200}
              defaultValue={collection.title}
            />
            <button type="submit" disabled={updateCollection.isPending}>
              {updateCollection.isPending
                ? t('m5s3.common.saving')
                : t('m5s3.common.saveChanges')}
            </button>
            {updateCollection.error ? (
              <ProblemState
                error={updateCollection.error}
                onRetry={() => void collectionQuery.refetch()}
              />
            ) : null}
          </form>
        </section>
      ) : null}

      <section
        className="planning-subsection"
        aria-labelledby="collection-items-heading"
      >
        <div className="layout-section-head">
          <div>
            <h2 id="collection-items-heading">
              {t('m5s3.collection.itemsHeading')}
            </h2>
            <p>{t('m5s3.collection.itemsIntro')}</p>
          </div>
        </div>

        {collection.capabilities.canEdit ? (
          <form className="planning-inline-create" onSubmit={submitItem}>
            <label className="sr-only" htmlFor="collection-new-item">
              {t('m5s3.collection.newItem')}
            </label>
            <input
              id="collection-new-item"
              name="title"
              required
              maxLength={200}
              placeholder={t('m5s3.collection.newItemPlaceholder')}
            />
            <button type="submit" disabled={createItem.isPending}>
              {createItem.isPending
                ? t('m5s3.common.saving')
                : t('m5s3.collection.addItem')}
            </button>
          </form>
        ) : null}

        {items.length > 0 ? (
          <ol className="planning-collection-items">
            {items.map((item) => (
              <li
                key={item.id}
                data-sortable-item-id={item.id}
                className={[
                  item.completed ? 'planning-item-completed' : null,
                  reorder.activeItemId === item.id
                    ? 'list-entry-dragging'
                    : null,
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                <button
                  type="button"
                  className="planning-check"
                  aria-pressed={item.completed}
                  aria-label={
                    item.completed
                      ? t('m5s3.collection.markOpen', { title: item.title })
                      : t('m5s3.collection.markDone', { title: item.title })
                  }
                  onClick={() =>
                    updateItem.mutate({
                      collection,
                      item,
                      completed: !item.completed,
                    })
                  }
                  disabled={!item.capabilities.canEdit || updateItem.isPending}
                >
                  {item.completed ? '✓' : ''}
                </button>
                <form
                  className="planning-item-title-form"
                  onSubmit={(event) => submitItemTitle(event, item)}
                >
                  <label
                    className="sr-only"
                    htmlFor={`collection-item-${item.id}`}
                  >
                    {t('m5s3.collection.itemTitle')}
                  </label>
                  <input
                    id={`collection-item-${item.id}`}
                    name="title"
                    defaultValue={item.title}
                    required
                    maxLength={200}
                    disabled={!item.capabilities.canEdit}
                  />
                  {item.capabilities.canEdit ? (
                    <ListEntryIconButton
                      type="submit"
                      icon="save"
                      className="tertiary"
                      label={
                        updateItem.isPending
                          ? t('m5s3.common.saving')
                          : t('m5s3.collection.saveItem', {
                              title: item.title,
                            })
                      }
                      disabled={updateItem.isPending}
                    />
                  ) : null}
                </form>
                {collection.capabilities.canEdit ? (
                  <ListEntryIconButton
                    icon="reorder"
                    className="tertiary"
                    label={t('m5s3.collection.reorderItem', {
                      title: item.title,
                    })}
                    {...reorder.handleProps(item.id)}
                  />
                ) : null}
                {item.capabilities.canDelete ? (
                  <ListEntryIconButton
                    icon="delete"
                    className="tertiary"
                    label={t('m5s3.collection.deleteItem', {
                      title: item.title,
                    })}
                    onClick={() => deleteItem.mutate({ collection, item })}
                    disabled={deleteItem.isPending}
                  />
                ) : null}
              </li>
            ))}
          </ol>
        ) : (
          <p className="planning-empty">{t('m5s3.collection.itemsEmpty')}</p>
        )}
        {reorderItems.isPending ? (
          <p role="status">{t('m5s3.collection.reordering')}</p>
        ) : null}
        {itemMutationError ? (
          <ProblemState
            error={itemMutationError}
            onRetry={() => void collectionQuery.refetch()}
          />
        ) : null}
      </section>

      {collection.capabilities.canDelete ? (
        <section
          className="planning-danger-zone"
          aria-labelledby="collection-delete-heading"
        >
          <h2 id="collection-delete-heading">
            {t('m5s3.common.deleteHeading')}
          </h2>
          <p>{t('m5s3.collection.deleteConsequence')}</p>
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
                onClick={() => deleteCollection.mutate(collection)}
                disabled={deleteCollection.isPending}
              >
                {deleteCollection.isPending
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
          {deleteCollection.error ? (
            <ProblemState
              error={deleteCollection.error}
              onRetry={() => void collectionQuery.refetch()}
            />
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
