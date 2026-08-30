import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { MemoryDetail } from '../api/generated/models/MemoryDetail';
import {
  deleteUnboundAttachment,
} from '../client/memoryAttachmentDraft';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import { useAttachmentDrafts } from '../client/useAttachmentDrafts';
import { useTranslation } from '../i18n';
import { AttachmentDraftField } from './AttachmentDraftField';
import { MemoryPreview } from './MemoryPreview';
import { ProblemState } from './ProblemState';

interface AttachmentChange {
  attachmentIds: string[];
  cleanupId?: string;
  clearDrafts?: boolean;
}

export function MemoryAttachmentManager({
  memory,
  apis,
  apiBaseUrl,
  accessToken,
  spaceId,
  loadMemoryImage,
  onMemoryUpdated,
}: {
  memory: MemoryDetail;
  apis: ReferenceApis;
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
  onMemoryUpdated: (memory: MemoryDetail) => void;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [cleanupWarning, setCleanupWarning] = useState(false);
  const drafts = useAttachmentDrafts({
    apis,
    apiBaseUrl,
    accessToken,
    spaceId,
  });
  const ordered = [...memory.attachments].sort(
    (left, right) => left.position - right.position,
  );

  const mutation = useMutation({
    mutationFn: async (change: AttachmentChange) => {
      try {
        const updated = await apis.memories.replaceMemoryAttachments({
          spaceId,
          memoryId: memory.id,
          ifMatch: String(memory.version),
          memoryAttachmentSet: {
            attachments: change.attachmentIds.map((attachmentId, position) => ({
              attachmentId,
              position,
            })),
          },
        });
        return { updated, change };
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async ({ updated, change }) => {
      if (change.clearDrafts) drafts.clear();
      onMemoryUpdated(updated);
      setCleanupWarning(false);
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      if (change.cleanupId) {
        const cleaned = await deleteUnboundAttachment(
          apis,
          spaceId,
          change.cleanupId,
        );
        if (!cleaned) setCleanupWarning(true);
      }
    },
  });

  function addReadyDrafts() {
    if (drafts.hasPending || drafts.readyIds.length === 0) return;
    mutation.mutate({
      attachmentIds: [...ordered.map((item) => item.id), ...drafts.readyIds],
      clearDrafts: true,
    });
  }

  function move(index: number, direction: -1 | 1) {
    const next = ordered.map((item) => item.id);
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    mutation.mutate({ attachmentIds: next });
  }

  function remove(attachmentId: string) {
    mutation.mutate({
      attachmentIds: ordered
        .filter((item) => item.id !== attachmentId)
        .map((item) => item.id),
      cleanupId: attachmentId,
    });
  }

  return (
    <section className="memory-attachment-manager" aria-labelledby="attachment-manager-heading">
      <div className="section-head memory-section-head">
        <div>
          <p className="section-kicker">{t('m5Product.media.kicker')}</p>
          <h2 id="attachment-manager-heading">
            {t('m5Product.media.manageHeading')}
          </h2>
        </div>
      </div>

      {ordered.length > 0 ? (
        <ol className="managed-gallery-list">
          {ordered.map((attachment, index) => (
            <li key={attachment.id} className="managed-gallery-item">
              <MemoryPreview
                memoryId={memory.id}
                attachmentId={attachment.id}
                loadImage={loadMemoryImage}
              />
              <div className="managed-gallery-meta">
                <span>
                  {t('m5Product.media.position', { position: index + 1 })}
                </span>
                <span>{attachment.status}</span>
              </div>
              <div className="managed-gallery-actions">
                <button
                  type="button"
                  className="tertiary"
                  disabled={index === 0 || mutation.isPending}
                  onClick={() => move(index, -1)}
                >
                  {t('m5Product.media.moveUp')}
                </button>
                <button
                  type="button"
                  className="tertiary"
                  disabled={index === ordered.length - 1 || mutation.isPending}
                  onClick={() => move(index, 1)}
                >
                  {t('m5Product.media.moveDown')}
                </button>
                <button
                  type="button"
                  className="tertiary"
                  disabled={mutation.isPending}
                  onClick={() => remove(attachment.id)}
                >
                  {t('m5Product.media.remove')}
                </button>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="muted">{t('m5Product.media.noBoundImages')}</p>
      )}

      <AttachmentDraftField
        controller={drafts}
        inputId={`memory-gallery-add-${memory.id}`}
        label={t('m5Product.media.addImages')}
      />
      {drafts.readyIds.length > 0 ? (
        <button
          type="button"
          disabled={drafts.hasPending || mutation.isPending}
          onClick={addReadyDrafts}
        >
          {mutation.isPending
            ? t('m5Product.common.saving')
            : t('m5Product.media.bindImages')}
        </button>
      ) : null}

      {cleanupWarning ? (
        <div className="inline-message" role="status">
          <strong>{t('m5Product.media.cleanupWarningTitle')}</strong>
          <span>{t('m5Product.media.cleanupWarningBody')}</span>
        </div>
      ) : null}
      {mutation.error ? (
        <ProblemState
          error={mutation.error}
          onRetry={() => {
            mutation.reset();
            void queryClient.invalidateQueries({
              queryKey: ['memory', spaceId, memory.id],
            });
          }}
        />
      ) : null}
    </section>
  );
}
