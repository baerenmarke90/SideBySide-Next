import type { UploadDescriptor } from '../api/generated/models/UploadDescriptor';
import { MediaType } from '../api/generated/models/MediaType';
import type { MemoryCreate } from '../api/generated/models/MemoryCreate';
import { i18n } from '../i18n';
import {
  ReferenceFlowError,
  uploadAttachmentBytes,
  type FlowResult,
  type ReferenceApis,
} from './referenceFlow';

export type DraftUploadPhase = 'uploading' | 'validating';

export interface ReadyDraftAttachment {
  attachmentId: string;
}

async function waitUntilReady(
  apis: ReferenceApis,
  spaceId: string,
  attachmentId: string,
  signal?: AbortSignal,
): Promise<void> {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (signal?.aborted) {
      throw new ReferenceFlowError(i18n.t('m5Product.upload.cancelled'));
    }
    const attachment = await apis.attachments.getAttachment({
      spaceId,
      attachmentId,
    });
    if (attachment.status === 'READY') return;
    if (
      attachment.status === 'FAILED' ||
      attachment.status === 'DELETE_FAILED' ||
      attachment.status === 'DELETING'
    ) {
      throw new ReferenceFlowError(
        i18n.t('flow.processingStatus', { status: attachment.status }),
      );
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new ReferenceFlowError(i18n.t('flow.processingTimeout'));
}

export async function deleteUnboundAttachment(
  apis: ReferenceApis,
  spaceId: string,
  attachmentId: string,
): Promise<boolean> {
  try {
    const attachment = await apis.attachments.getAttachment({
      spaceId,
      attachmentId,
    });
    if (attachment.status === 'DELETING') return true;
    await apis.attachments.deleteAttachment({
      spaceId,
      attachmentId: attachment.id,
      ifMatch: String(attachment.version),
    });
    return true;
  } catch {
    // Orphan cleanup is best-effort; server retention remains the fail-safe.
    return false;
  }
}

async function cleanupUnboundAttachment(
  apis: ReferenceApis,
  spaceId: string,
  upload: UploadDescriptor | undefined,
): Promise<void> {
  if (!upload) return;
  await deleteUnboundAttachment(apis, spaceId, upload.attachment.id);
}

export async function uploadMemoryDraftAttachment(
  apis: ReferenceApis,
  apiBaseUrl: string,
  accessToken: string,
  spaceId: string,
  file: File,
  onPhase?: (phase: DraftUploadPhase) => void,
  fetchApi: typeof fetch = fetch,
  signal?: AbortSignal,
): Promise<ReadyDraftAttachment> {
  if (!file.type.startsWith('image/'))
    throw new ReferenceFlowError(i18n.t('flow.imageOnly'));
  if (file.size === 0) throw new ReferenceFlowError(i18n.t('flow.imageEmpty'));

  let upload: UploadDescriptor | undefined;
  try {
    if (signal?.aborted) {
      throw new ReferenceFlowError(i18n.t('m5Product.upload.cancelled'));
    }
    onPhase?.('uploading');
    upload = await apis.attachments.createAttachmentUpload({
      spaceId,
      attachmentUploadCreate: {
        expectedMimeType: file.type,
        expectedSize: file.size,
        mediaType: MediaType.IMAGE,
        originalName: file.name,
      },
    });

    await uploadAttachmentBytes(
      apiBaseUrl,
      accessToken,
      upload,
      file,
      fetchApi,
      signal,
    );
    if (signal?.aborted) {
      throw new ReferenceFlowError(i18n.t('m5Product.upload.cancelled'));
    }
    onPhase?.('validating');
    await apis.attachments.finalizeAttachmentUpload({
      spaceId,
      attachmentId: upload.attachment.id,
      body: {},
    });
    await waitUntilReady(apis, spaceId, upload.attachment.id, signal);

    return { attachmentId: upload.attachment.id };
  } catch (error) {
    await cleanupUnboundAttachment(apis, spaceId, upload);
    if (signal?.aborted) {
      throw new ReferenceFlowError(i18n.t('m5Product.upload.cancelled'));
    }
    if (error instanceof ReferenceFlowError) throw error;
    throw new ReferenceFlowError(i18n.t('flow.uploadFailed'));
  }
}

export async function createMemoryWithReadyAttachments(
  apis: ReferenceApis,
  spaceId: string,
  memoryCreate: MemoryCreate,
  attachmentIds: string[],
): Promise<FlowResult> {
  try {
    const memory = await apis.memories.createMemory({ spaceId, memoryCreate });
    const savedMemory = attachmentIds.length
      ? await apis.memories.replaceMemoryAttachments({
          spaceId,
          memoryId: memory.id,
          ifMatch: String(memory.version),
          memoryAttachmentSet: {
            attachments: attachmentIds.map((attachmentId, position) => ({
              attachmentId,
              position,
            })),
          },
        })
      : memory;
    const story = await apis.story.getStoryTimeline({ spaceId, limit: 25 });
    return { memory: savedMemory, story, imageUrl: null };
  } catch (error) {
    if (error instanceof ReferenceFlowError) throw error;
    throw new ReferenceFlowError(i18n.t('flow.saveFailed'));
  }
}
