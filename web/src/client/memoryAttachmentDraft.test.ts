import { UploadDescriptorMethodEnum } from '../api/generated/models/UploadDescriptor';
import {
  createMemoryWithReadyAttachments,
  uploadMemoryDraftAttachment,
} from './memoryAttachmentDraft';
import type { ReferenceApis } from './referenceFlow';

function uploadingAttachment() {
  return {
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
}

describe('uploadMemoryDraftAttachment', () => {
  it('starts upload immediately, exposes validation, and resolves only after READY', async () => {
    const phases: string[] = [];
    const attachment = uploadingAttachment();
    const apis = {
      auth: {},
      memories: {},
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
        deleteAttachment: vi.fn(),
      },
      story: {},
    } as unknown as ReferenceApis;
    const fetchApi = vi.fn(
      async () => new Response(null, { status: 204 }),
    ) as unknown as typeof fetch;

    const result = await uploadMemoryDraftAttachment(
      apis,
      'https://api.example.invalid',
      'token',
      'space-1',
      new File(['image'], 'test.jpg', { type: 'image/jpeg' }),
      (phase) => phases.push(phase),
      fetchApi,
    );

    expect(phases).toEqual(['uploading', 'validating']);
    expect(result).toEqual({ attachmentId: 'attachment-1' });
    expect(apis.attachments.finalizeAttachmentUpload).toHaveBeenCalledWith({
      spaceId: 'space-1',
      attachmentId: 'attachment-1',
      body: {},
    });
    expect(apis.attachments.getAttachment).toHaveBeenCalledWith({
      spaceId: 'space-1',
      attachmentId: 'attachment-1',
    });
    expect(apis.attachments.deleteAttachment).not.toHaveBeenCalled();
  });

  it('cleans up an unbound attachment when server-side validation rejects it', async () => {
    const phases: string[] = [];
    const attachment = uploadingAttachment();
    const getAttachment = vi
      .fn()
      .mockResolvedValueOnce({ ...attachment, status: 'FAILED', version: 2 })
      .mockResolvedValueOnce({ ...attachment, status: 'FAILED', version: 2 });
    const apis = {
      auth: {},
      memories: {},
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
        getAttachment,
        deleteAttachment: vi.fn(async () => undefined),
      },
      story: {},
    } as unknown as ReferenceApis;
    const fetchApi = vi.fn(
      async () => new Response(null, { status: 204 }),
    ) as unknown as typeof fetch;

    await expect(
      uploadMemoryDraftAttachment(
        apis,
        'https://api.example.invalid',
        'token',
        'space-1',
        new File(['image'], 'invalid.jpg', { type: 'image/jpeg' }),
        (phase) => phases.push(phase),
        fetchApi,
      ),
    ).rejects.toThrow();

    expect(phases).toEqual(['uploading', 'validating']);
    expect(apis.attachments.deleteAttachment).toHaveBeenCalledWith({
      spaceId: 'space-1',
      attachmentId: 'attachment-1',
      ifMatch: '2',
    });
  });

  it('passes cancellation to the upload transport and removes the orphan', async () => {
    const attachment = uploadingAttachment();
    const controller = new AbortController();
    const apis = {
      auth: {},
      memories: {},
      attachments: {
        createAttachmentUpload: vi.fn(async () => ({
          attachment,
          method: UploadDescriptorMethodEnum.STREAM,
          requiredHeaders: { 'Content-Type': 'image/jpeg' },
          uploadUrl: '/api/v1/spaces/space-1/attachments/attachment-1/content',
        })),
        getAttachment: vi.fn(async () => ({ ...attachment, version: 3 })),
        deleteAttachment: vi.fn(async () => undefined),
      },
      story: {},
    } as unknown as ReferenceApis;
    const fetchApi = vi.fn(
      async (_url: RequestInfo | URL, init?: RequestInit) => {
        expect(init?.signal).toBe(controller.signal);
        controller.abort();
        throw new DOMException('Aborted', 'AbortError');
      },
    ) as unknown as typeof fetch;

    await expect(
      uploadMemoryDraftAttachment(
        apis,
        'https://api.example.invalid',
        'token',
        'space-1',
        new File(['image'], 'cancel.jpg', { type: 'image/jpeg' }),
        undefined,
        fetchApi,
        controller.signal,
      ),
    ).rejects.toThrow('abgebrochen');

    expect(apis.attachments.deleteAttachment).toHaveBeenCalledWith({
      spaceId: 'space-1',
      attachmentId: 'attachment-1',
      ifMatch: '3',
    });
  });
});

describe('createMemoryWithReadyAttachments', () => {
  it('binds only the READY attachment IDs supplied by the draft state and preserves their order', async () => {
    const memory = {
      id: 'memory-1',
      version: 1,
      title: 'Lake',
      body: '',
    };
    const boundMemory = { ...memory, version: 2 };
    const story = { items: [] };
    const apis = {
      auth: {},
      attachments: {},
      memories: {
        createMemory: vi.fn(async () => memory),
        replaceMemoryAttachments: vi.fn(async () => boundMemory),
      },
      story: {
        getStoryTimeline: vi.fn(async () => story),
      },
    } as unknown as ReferenceApis;

    const result = await createMemoryWithReadyAttachments(
      apis,
      'space-1',
      { title: 'Lake', body: '' },
      ['attachment-2', 'attachment-1'],
    );

    expect(apis.memories.replaceMemoryAttachments).toHaveBeenCalledWith({
      spaceId: 'space-1',
      memoryId: 'memory-1',
      ifMatch: '1',
      memoryAttachmentSet: {
        attachments: [
          { attachmentId: 'attachment-2', position: 0 },
          { attachmentId: 'attachment-1', position: 1 },
        ],
      },
    });
    expect(result.memory).toBe(boundMemory);
    expect(result.story).toBe(story);
    expect(result.imageUrl).toBeNull();
  });

  it('does not touch attachment binding when the Memory has no READY drafts', async () => {
    const memory = {
      id: 'memory-1',
      version: 1,
      title: 'Title only',
      body: '',
    };
    const replaceMemoryAttachments = vi.fn();
    const apis = {
      auth: {},
      attachments: {},
      memories: {
        createMemory: vi.fn(async () => memory),
        replaceMemoryAttachments,
      },
      story: {
        getStoryTimeline: vi.fn(async () => ({ items: [] })),
      },
    } as unknown as ReferenceApis;

    await createMemoryWithReadyAttachments(
      apis,
      'space-1',
      { title: 'Title only', body: '' },
      [],
    );

    expect(replaceMemoryAttachments).not.toHaveBeenCalled();
  });
});
