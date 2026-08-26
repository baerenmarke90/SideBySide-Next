import {
  AttachmentReadRequestParentTypeEnum,
  MediaType,
  type MemoryDetail,
  type StoryItem,
  UploadDescriptorMethodEnum,
} from './api/generated';
import { absoluteApiUrl, type ApiSet } from './api/client';

const ALLOWED_IMAGE_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/heic',
  'image/heif',
]);

export interface CreateMemoryInput {
  title: string;
  body: string;
  happenedOn?: Date;
  image?: File;
}

export interface ReferenceFlowDependencies {
  api: ApiSet;
  apiBaseUrl: string;
  accessToken: string;
  fetchFn?: typeof fetch;
  sleep?: (milliseconds: number) => Promise<void>;
}

export function storyItemTitle(item: StoryItem): string {
  switch (item.kind) {
    case 'MEMORY':
      return item.memory.title;
    case 'MILESTONE':
      return item.milestone.title;
    case 'HEART_MOMENT':
      return item.heartMoment.text;
  }
}

export function validateImage(file: File): void {
  if (!ALLOWED_IMAGE_TYPES.has(file.type.toLowerCase())) {
    throw new Error('Bitte ein JPEG-, PNG-, WebP-, HEIC- oder HEIF-Bild auswählen.');
  }
}

export class ReferenceFlow {
  private readonly fetchFn: typeof fetch;
  private readonly sleep: (milliseconds: number) => Promise<void>;

  constructor(private readonly dependencies: ReferenceFlowDependencies) {
    this.fetchFn = dependencies.fetchFn ?? fetch;
    this.sleep = dependencies.sleep ?? ((milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)));
  }

  async createMemoryWithImage(spaceId: string, input: CreateMemoryInput): Promise<MemoryDetail> {
    const memory = await this.dependencies.api.memories.createMemory({
      spaceId,
      memoryCreate: {
        title: input.title,
        body: input.body,
        happenedOn: input.happenedOn ?? null,
      },
    });

    if (!input.image) return memory;
    validateImage(input.image);

    const upload = await this.dependencies.api.attachments.createAttachmentUpload({
      spaceId,
      attachmentUploadCreate: {
        expectedMimeType: input.image.type,
        expectedSize: input.image.size,
        mediaType: MediaType.IMAGE,
        originalName: input.image.name,
      },
    });

    if (upload.method === UploadDescriptorMethodEnum.STREAM) {
      await this.dependencies.api.attachments.uploadAttachmentContent(
        { attachmentId: upload.attachment.id, spaceId },
        async ({ init }) => ({
          ...init,
          headers: {
            ...(init.headers as Record<string, string> | undefined),
            'Content-Type': input.image!.type,
          },
          body: input.image,
        }),
      );
    } else {
      const response = await this.fetchFn(upload.uploadUrl, {
        method: 'PUT',
        headers: upload.requiredHeaders,
        body: input.image,
      });
      if (!response.ok) {
        throw new Error(`Bild-Upload fehlgeschlagen (${response.status}).`);
      }
    }

    await this.dependencies.api.attachments.finalizeAttachmentUpload({
      attachmentId: upload.attachment.id,
      spaceId,
      body: {},
    });

    await this.waitUntilReady(spaceId, upload.attachment.id);

    return this.dependencies.api.memories.replaceMemoryAttachments({
      memoryId: memory.id,
      spaceId,
      ifMatch: String(memory.version),
      memoryAttachmentSet: {
        attachments: [{ attachmentId: upload.attachment.id, position: 0 }],
      },
    });
  }

  async loadMemoryImage(spaceId: string, memoryId: string, attachmentId: string): Promise<string> {
    const descriptor = await this.dependencies.api.attachments.createAttachmentReadAccess({
      attachmentId,
      spaceId,
      attachmentReadRequest: {
        parentId: memoryId,
        parentType: AttachmentReadRequestParentTypeEnum.MEMORY,
      },
    });

    if (descriptor.method === 'SIGNED_URL') return descriptor.url;

    const response = await this.fetchFn(
      absoluteApiUrl(this.dependencies.apiBaseUrl, descriptor.url),
      { headers: { Authorization: `Bearer ${this.dependencies.accessToken}` } },
    );
    if (!response.ok) {
      throw new Error(`Bild konnte nicht geladen werden (${response.status}).`);
    }
    return URL.createObjectURL(await response.blob());
  }

  private async waitUntilReady(spaceId: string, attachmentId: string): Promise<void> {
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const attachment = await this.dependencies.api.attachments.getAttachment({ attachmentId, spaceId });
      if (attachment.status === 'READY') return;
      if (attachment.status === 'FAILED' || attachment.status === 'DELETE_FAILED') {
        throw new Error('Das Bild konnte serverseitig nicht verarbeitet werden.');
      }
      await this.sleep(500);
    }
    throw new Error('Die Bildverarbeitung hat das Zeitlimit überschritten.');
  }
}
