import { ReadDescriptorMethodEnum } from '../api/generated/models/ReadDescriptor';
import { UploadDescriptorMethodEnum } from '../api/generated/models/UploadDescriptor';
import {
  createMemoryWithPreparedAttachments,
  prepareAttachment,
  type ReferenceApis,
} from './referenceFlow';

describe('prepareAttachment', () => {
  it('uploads and validates immediately without creating or binding a Memory', async () => {
    const phases: string[] = [];
    const attachment = {
      id: 'attachment-1',
      createdAt: new Date('2026-08-29T20:00:00Z'),
      durationSeconds: null,
      hasThumbnail: false,
      height: null,
      mediaType: 'IMAGE',
      mimeType: 'image/jpeg',
      size: 5,
      status: 'UPLOADING',
      version: 1,
      width: null,
    };
    const createMemory = vi.fn();
    const replaceMemoryAttachments = vi.fn();
    const apis = {
      auth: {},
      memories: { createMemory, replaceMemoryAttachments },
      attachments: {
        createAttachmentUpload: vi.fn(async () => ({
          attachment,
          method: UploadDescriptorMethodEnum.STREAM,
          requiredHeaders: { 'Content-Type': 'image/jpeg' },
          uploadUrl: '/api/v1/spaces/space-1/attachments/attachment-1/content',
        })),
        finalizeAttachmentUpload: vi.fn(async () => ({
          ...attachment,
          status: 'PROCESSING',
        })),
        getAttachment: vi.fn(async () => ({ ...attachment, status: 'READY' })),
      },
      story: {},
    } as unknown as ReferenceApis;
    const fetchApi = vi.fn(async () => new Response(null, { status: 204 })) as unknown as typeof fetch;

    const result = await prepareAttachment(
      apis,
      'https://api.example.invalid',
      'token',
      'space-1',
      new File(['image'], 'test.jpg', { type: 'image/jpeg' }),
      (phase) => phases.push(phase),
      fetchApi,
    );

    expect(phases).toEqual(['uploading', 'validating', 'ready']);
    expect(result).toEqual({ attachmentId: 'attachment-1' });
    expect(createMemory).not.toHaveBeenCalled();
    expect(replaceMemoryAttachments).not.toHaveBeenCalled();
    expect(fetchApi).toHaveBeenCalledOnce();
  });
});

describe('createMemoryWithPreparedAttachments', () => {
  it('binds only the supplied READY attachment identities in stable selection order', async () => {
    const memory = {
      id: 'memory-1',
      version: 4,
      title: 'Two photos',
      body: '',
    };
    const boundMemory = { ...memory, version: 5 };
    const story = { items: [] };
    const apis = {
      auth: {},
      memories: {
        createMemory: vi.fn(async () => memory),
        replaceMemoryAttachments: vi.fn(async () => boundMemory),
      },
      attachments: {
        createAttachmentReadAccess: vi.fn(async () => ({
          method: ReadDescriptorMethodEnum.SIGNED_URL,
          url: 'https://storage.example.invalid/read',
        })),
      },
      story: {
        getStoryTimeline: vi.fn(async () => story),
      },
    } as unknown as ReferenceApis;
    const fetchApi = vi.fn(
      async () =>
        new Response(new Blob(['image'], { type: 'image/jpeg' }), {
          status: 200,
        }),
    ) as unknown as typeof fetch;
    const createObjectUrl = vi
      .spyOn(URL, 'createObjectURL')
      .mockReturnValue('blob:prepared');

    try {
      const result = await createMemoryWithPreparedAttachments(
        apis,
        'https://api.example.invalid',
        'token',
        'space-1',
        { title: memory.title },
        [
          { attachmentId: 'attachment-first' },
          { attachmentId: 'attachment-second' },
        ],
        fetchApi,
      );

      expect(apis.memories.replaceMemoryAttachments).toHaveBeenCalledWith({
        spaceId: 'space-1',
        memoryId: 'memory-1',
        ifMatch: '4',
        memoryAttachmentSet: {
          attachments: [
            { attachmentId: 'attachment-first', position: 0 },
            { attachmentId: 'attachment-second', position: 1 },
          ],
        },
      });
      expect(apis.attachments.createAttachmentReadAccess).toHaveBeenCalledWith({
        spaceId: 'space-1',
        attachmentId: 'attachment-first',
        attachmentReadRequest: {
          parentType: 'MEMORY',
          parentId: 'memory-1',
        },
      });
      expect(result.memory).toBe(boundMemory);
      expect(result.story).toBe(story);
      expect(result.imageUrl).toBe('blob:prepared');
    } finally {
      createObjectUrl.mockRestore();
    }
  });
});
