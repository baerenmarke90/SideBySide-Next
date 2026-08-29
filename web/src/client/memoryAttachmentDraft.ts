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
): Promise<void> {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
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

export async function uploadMemoryDraftAttachment(
  apis: ReferenceApis,
  apiBaseUrl: string,
  accessToken: string,
  spaceId: string,
  file: File,
  onPhase?: (phase: DraftUploadPhase) => void,
  fetchApi: typeof fetch = fetch,
): Promise<ReadyDraftAttachment> {
  if (!file.type.startsWith('image/'))
    throw new ReferenceFlowError(i18n.t('flow.imageOnly'));
  if (file.size === 0)
    throw new ReferenceFlowError(i18n.t('flow.imageEmpty'));

  try {
    onPhase?.('uploading');
    const upload = await apis.attachments.createAttachmentUpload({
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
    );
    onPhase?.('validating');
    await apis.attachments.finalizeAttachmentUpload({
      spaceId,
      attachmentId: upload.attachment.id,
      body: {},
    });
    await waitUntilReady(apis, spaceId, upload.attachment.id);

    return { attachmentId: upload.attachment.id };
  } catch (error) {
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
