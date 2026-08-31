import type { FormEvent } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { PrivateAreaApi } from '../api/generated/apis/PrivateAreaApi';
import type { PrivateCollectionDetail } from '../api/generated/models/PrivateCollectionDetail';
import type { PrivateCollectionItemDetail } from '../api/generated/models/PrivateCollectionItemDetail';
import {
  PRIVATE_COLLECTIONS_PATH,
  privateApiCall,
  privateAreaQueryKeys,
  privateCollectionEditPath,
  privateCollectionPath,
} from '../client/privateArea';
import { useTranslation } from '../i18n';
import {
  ListEntryIconButton,
  useListItemReorder,
} from './ListEntryActions';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import {
  DeleteConfirmation,
  LoadMoreButton,
  PrivateAreaBackToProfile,
} from './PrivateAreaLayout';
import { UiState } from './UiState';

const PAGE_SIZE = 20;

type Props = {
  api: PrivateAreaApi;
  accountId: string;
  spaceId: string;
};

function usePrivateCollection(
  api: PrivateAreaApi,
  accountId: string,
  spaceId: string,
) {
  const { collectionId } = useParams();
  const query = useQuery({
    queryKey: privateAreaQueryKeys.collection(
      accountId,
      spaceId,
      collectionId ?? 'missing',
    ),
    queryFn: () => {
      if (!collectionId)
        throw new Error('Missing private collection route parameter.');
      return privateApiCall(() =>
        api.getPrivateCollection({ spaceId, collectionId }),
      );
    },
    enabled: Boolean(collectionId),
    retry: false,
  });
  return { collectionId, query };
}

function CollectionFields({
  collection,
}: {
  collection?: PrivateCollectionDetail;
}) {
  const { t } = useTranslation();
  return (
    <div className="field-group">
      <label htmlFor="private-collection-title">
        {t('privateArea.collections.titleLabel')}
      </label>
      <input
        id="private-collection-title"
        name="title"
        required
        maxLength={200}
        defaultValue={collection?.title ?? ''}
      />
    </div>
  );
}

export function PrivateCollectionsListPage({ api, accountId, spaceId }: Props) {
  const { t } = useTranslation();
  const query = useInfiniteQuery({
    queryKey: privateAreaQueryKeys.collections(accountId, spaceId),
    queryFn: ({ pageParam }) =>
      privateApiCall(() =>
        api.listPrivateCollections({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    retry: false,
  });
  const collections = query.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <>
      <PageHeader
        before={<PrivateAreaBackToProfile />}
        title={t('privateArea.collections.title')}
        description={t('privateArea.collections.intro')}
        action={
          <Link className="button-link" to={`${PRIVATE_COLLECTIONS_PATH}/new`}>
            {t('privateArea.collections.add')}
          </Link>
        }
      />
      {query.isLoading ? (
        <UiState kind="loading" title={t('privateArea.collections.loading')} />
      ) : null}
      {query.error ? (
        <ProblemState
          error={query.error}
          onRetry={() => void query.refetch()}
        />
      ) : null}
      {query.data && collections.length === 0 ? (
        <UiState
          kind="empty"
          title={t('privateArea.collections.emptyTitle')}
          body={t('privateArea.collections.emptyBody')}
        />
      ) : null}
      {collections.length > 0 ? (
        <section className="private-area-results" aria-live="polite">
          <ul className="private-area-list layout-columns layout-columns-dense">
            {collections.map((collection) => (
              <li key={collection.id} className="private-area-card">
                <div className="private-area-card-heading">
                  <h2>{collection.title}</h2>
                </div>
                <Link
                  className="button-link secondary-link"
                  to={privateCollectionPath(collection.id)}
                >
                  {t('privateArea.edit')}
                </Link>
              </li>
            ))}
          </ul>
          <LoadMoreButton
            hasMore={Boolean(query.hasNextPage)}
            loading={query.isFetchingNextPage}
            onLoadMore={() => void query.fetchNextPage()}
          />
        </section>
      ) : null}
    </>
  );
}

export function PrivateCollectionCreatePage({
  api,
  accountId,
  spaceId,
}: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (title: string) =>
      privateApiCall(() =>
        api.createPrivateCollection({
          spaceId,
          privateCollectionCreate: { title },
        }),
      ),
    onSuccess: async (collection) => {
      await queryClient.invalidateQueries({
        queryKey: privateAreaQueryKeys.collections(accountId, spaceId),
      });
      navigate(privateCollectionPath(collection.id), { replace: true });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    mutation.mutate(String(data.get('title') || '').trim());
  }

  return (
    <>
      <PageHeader
        before={
          <Link className="back-link" to={PRIVATE_COLLECTIONS_PATH}>
            {t('privateArea.collections.detailBack')}
          </Link>
        }
        title={t('privateArea.collections.createTitle')}
        description={t('privateArea.collections.intro')}
      />
      <section className="form-card private-area-editor">
        <form className="form-grid" onSubmit={submit}>
          <CollectionFields />
          <div className="form-actions">
            <Link
              className="button-link secondary-link"
              to={PRIVATE_COLLECTIONS_PATH}
            >
              {t('common.cancel')}
            </Link>
            <button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? t('privateArea.saving')
                : t('privateArea.save')}
            </button>
          </div>
        </form>
        {mutation.error ? <ProblemState error={mutation.error} /> : null}
      </section>
    </>
  );
}

function CollectionItems({
  api,
  accountId,
  spaceId,
  collection,
}: Props & { collection: PrivateCollectionDetail }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const collectionKey = privateAreaQueryKeys.collection(
    accountId,
    spaceId,
    collection.id,
  );
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: collectionKey });
    await queryClient.invalidateQueries({
      queryKey: privateAreaQueryKeys.collections(accountId, spaceId),
    });
  };

  const createMutation = useMutation({
    mutationFn: (title: string) =>
      privateApiCall(() =>
        api.createPrivateCollectionItem({
          spaceId,
          collectionId: collection.id,
          privateCollectionItemCreate: { title },
        }),
      ),
    onSuccess: refresh,
  });
  const updateMutation = useMutation({
    mutationFn: ({
      item,
      update,
    }: {
      item: PrivateCollectionItemDetail;
      update: { title?: string; completed?: boolean };
    }) =>
      privateApiCall(() =>
        api.updatePrivateCollectionItem({
          spaceId,
          collectionId: collection.id,
          itemId: item.id,
          ifMatch: String(item.version),
          privateCollectionItemUpdate: update,
        }),
      ),
    onSuccess: refresh,
  });
  const deleteMutation = useMutation({
    mutationFn: (item: PrivateCollectionItemDetail) =>
      privateApiCall(() =>
        api.deletePrivateCollectionItem({
          spaceId,
          collectionId: collection.id,
          itemId: item.id,
          ifMatch: String(item.version),
        }),
      ),
    onSuccess: refresh,
  });
  const reorderMutation = useMutation({
    mutationFn: (itemIds: string[]) =>
      privateApiCall(() =>
        api.reorderPrivateCollectionItems({
          spaceId,
          collectionId: collection.id,
          ifMatch: String(collection.version),
          privateCollectionOrder: { itemIds },
        }),
      ),
    onSuccess: async (updated) => {
      queryClient.setQueryData(collectionKey, updated);
      await queryClient.invalidateQueries({
        queryKey: privateAreaQueryKeys.collections(accountId, spaceId),
      });
    },
  });

  const baseItems = [...collection.items].sort(
    (left, right) => left.position - right.position,
  );
  const reorder = useListItemReorder({
    itemIds: baseItems.map((item) => item.id),
    disabled: !collection.capabilities.canEdit || reorderMutation.isPending,
    onReorder: (itemIds) => reorderMutation.mutate(itemIds),
  });
  const itemById = new Map(baseItems.map((item) => [item.id, item]));
  const items = reorder.orderedItemIds
    .map((itemId) => itemById.get(itemId))
    .filter((item): item is PrivateCollectionItemDetail => Boolean(item));

  function submitItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const title = String(data.get('title') || '').trim();
    if (!title) return;
    createMutation.mutate(title, { onSuccess: () => form.reset() });
  }

  function submitRename(
    event: FormEvent<HTMLFormElement>,
    item: PrivateCollectionItemDetail,
  ) {
    event.preventDefault();
    const title = String(
      new FormData(event.currentTarget).get('title') || '',
    ).trim();
    if (!title || title === item.title) return;
    updateMutation.mutate({ item, update: { title } });
  }

  return (
    <section
      className="private-area-section"
      aria-labelledby="private-list-items-title"
    >
      <h2 id="private-list-items-title">
        {t('privateArea.collections.itemsTitle')}
      </h2>
      <form className="private-area-inline-form" onSubmit={submitItem}>
        <div className="field-group">
          <label htmlFor="private-list-new-item">
            {t('privateArea.collections.itemTitleLabel')}
          </label>
          <input
            id="private-list-new-item"
            name="title"
            required
            maxLength={200}
          />
        </div>
        <button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending
            ? t('privateArea.collections.addingItem')
            : t('privateArea.collections.addItem')}
        </button>
      </form>
      {createMutation.error ? (
        <ProblemState error={createMutation.error} />
      ) : null}
      {items.length === 0 ? (
        <p>{t('privateArea.collections.noItems')}</p>
      ) : null}
      {items.length > 0 ? (
        <ol className="private-area-item-list">
          {items.map((item) => (
            <li
              key={item.id}
              data-sortable-item-id={item.id}
              className={[
                'private-area-item',
                reorder.activeItemId === item.id ? 'list-entry-dragging' : null,
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <div className="private-area-item-main">
                <span className="private-area-badge">
                  {item.completed
                    ? t('privateArea.collections.complete')
                    : t('privateArea.collections.open')}
                </span>
                <form
                  className="private-area-item-title-form"
                  onSubmit={(event) => submitRename(event, item)}
                >
                  <label
                    className="sr-only"
                    htmlFor={`private-item-${item.id}`}
                  >
                    {t('privateArea.collections.rename')}
                  </label>
                  <input
                    id={`private-item-${item.id}`}
                    name="title"
                    defaultValue={item.title}
                    required
                    maxLength={200}
                  />
                  <ListEntryIconButton
                    type="submit"
                    icon="save"
                    className="secondary"
                    label={
                      updateMutation.isPending
                        ? t('privateArea.saving')
                        : t('privateArea.collections.saveItem')
                    }
                    disabled={updateMutation.isPending}
                  />
                </form>
              </div>
              <div className="private-area-actions">
                <button
                  type="button"
                  className="secondary compact-action"
                  onClick={() =>
                    updateMutation.mutate({
                      item,
                      update: { completed: !item.completed },
                    })
                  }
                  disabled={updateMutation.isPending}
                >
                  {item.completed
                    ? t('privateArea.collections.markOpen')
                    : t('privateArea.collections.markComplete')}
                </button>
                {collection.capabilities.canEdit ? (
                  <ListEntryIconButton
                    icon="reorder"
                    className="tertiary"
                    label={t('privateArea.collections.reorderItem')}
                    {...reorder.handleProps(item.id)}
                  />
                ) : null}
                <ListEntryIconButton
                  icon="delete"
                  className="tertiary"
                  label={t('privateArea.collections.removeItem')}
                  onClick={() => deleteMutation.mutate(item)}
                  disabled={deleteMutation.isPending}
                />
              </div>
            </li>
          ))}
        </ol>
      ) : null}
      {reorderMutation.isPending ? (
        <p role="status">{t('privateArea.collections.reordering')}</p>
      ) : null}
      {updateMutation.error ? (
        <ProblemState error={updateMutation.error} />
      ) : null}
      {deleteMutation.error ? (
        <ProblemState error={deleteMutation.error} />
      ) : null}
      {reorderMutation.error ? (
        <ProblemState error={reorderMutation.error} />
      ) : null}
    </section>
  );
}

export function PrivateCollectionDetailPage({
  api,
  accountId,
  spaceId,
}: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { collectionId, query } = usePrivateCollection(api, accountId, spaceId);
  const deleteMutation = useMutation({
    mutationFn: (collection: PrivateCollectionDetail) =>
      privateApiCall(() =>
        api.deletePrivateCollection({
          spaceId,
          collectionId: collection.id,
          ifMatch: String(collection.version),
        }),
      ),
    onSuccess: async () => {
      if (collectionId) {
        queryClient.removeQueries({
          queryKey: privateAreaQueryKeys.collection(
            accountId,
            spaceId,
            collectionId,
          ),
        });
      }
      await queryClient.invalidateQueries({
        queryKey: privateAreaQueryKeys.collections(accountId, spaceId),
      });
      navigate(PRIVATE_COLLECTIONS_PATH, { replace: true });
    },
  });

  if (query.isLoading) {
    return (
      <UiState kind="loading" title={t('privateArea.collections.loading')} />
    );
  }
  if (query.error) {
    return (
      <ProblemState error={query.error} onRetry={() => void query.refetch()} />
    );
  }
  const collection = query.data;
  if (!collection) return null;

  return (
    <>
      <PageHeader
        before={
          <Link className="back-link" to={PRIVATE_COLLECTIONS_PATH}>
            {t('privateArea.collections.detailBack')}
          </Link>
        }
        eyebrow={t('privateArea.privacyLabel')}
        title={collection.title}
        action={
          collection.capabilities.canEdit ? (
            <Link
              className="button-link secondary-link"
              to={privateCollectionEditPath(collection.id)}
            >
              {t('privateArea.edit')}
            </Link>
          ) : undefined
        }
      />
      <CollectionItems
        api={api}
        accountId={accountId}
        spaceId={spaceId}
        collection={collection}
      />
      {collection.capabilities.canDelete ? (
        <DeleteConfirmation
          onDelete={() => deleteMutation.mutate(collection)}
          pending={deleteMutation.isPending}
          error={deleteMutation.error}
        />
      ) : null}
    </>
  );
}

export function PrivateCollectionEditPage({ api, accountId, spaceId }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { query } = usePrivateCollection(api, accountId, spaceId);
  const mutation = useMutation({
    mutationFn: ({
      collection,
      title,
    }: {
      collection: PrivateCollectionDetail;
      title: string;
    }) =>
      privateApiCall(() =>
        api.updatePrivateCollection({
          spaceId,
          collectionId: collection.id,
          ifMatch: String(collection.version),
          privateCollectionUpdate: { title },
        }),
      ),
    onSuccess: async (collection) => {
      queryClient.setQueryData(
        privateAreaQueryKeys.collection(accountId, spaceId, collection.id),
        collection,
      );
      await queryClient.invalidateQueries({
        queryKey: privateAreaQueryKeys.collections(accountId, spaceId),
      });
      navigate(privateCollectionPath(collection.id), { replace: true });
    },
  });

  if (query.isLoading) {
    return (
      <UiState kind="loading" title={t('privateArea.collections.loading')} />
    );
  }
  if (query.error) {
    return (
      <ProblemState error={query.error} onRetry={() => void query.refetch()} />
    );
  }
  const collection = query.data;
  if (!collection) return null;
  if (!collection.capabilities.canEdit) {
    return (
      <UiState
        kind="permission"
        title={t('states.permission.title')}
        body={t('states.permission.body')}
      />
    );
  }
  const editableCollection: PrivateCollectionDetail = collection;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    mutation.mutate({
      collection: editableCollection,
      title: String(data.get('title') || '').trim(),
    });
  }

  return (
    <>
      <PageHeader
        before={
          <Link className="back-link" to={privateCollectionPath(collection.id)}>
            {t('privateArea.collections.detailBack')}
          </Link>
        }
        title={t('privateArea.collections.editTitle')}
        description={t('privateArea.collections.intro')}
      />
      <section className="form-card private-area-editor">
        <form className="form-grid" onSubmit={submit}>
          <CollectionFields collection={collection} />
          <div className="form-actions">
            <Link
              className="button-link secondary-link"
              to={privateCollectionPath(collection.id)}
            >
              {t('common.cancel')}
            </Link>
            <button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? t('privateArea.saving')
                : t('privateArea.save')}
            </button>
          </div>
        </form>
        {mutation.error ? <ProblemState error={mutation.error} /> : null}
      </section>
    </>
  );
}
