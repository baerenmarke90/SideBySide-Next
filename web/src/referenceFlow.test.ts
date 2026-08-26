import { describe, expect, it, vi } from 'vitest';
import type { ApiSet } from './api/client';
import type { StoryItem } from './api/generated';
import { ReferenceFlow, storyItemTitle, validateImage } from './referenceFlow';

function apiStub(overrides: Partial<ApiSet>): ApiSet {
  return overrides as ApiSet;
}

describe('ReferenceFlow', () => {
  it('creates a memory, uploads/finalizes an image and binds it with generated clients', async () => {
    const createMemory = vi.fn().mockResolvedValue({ id: 'memory-1', title: 'See', version: 1 });
    const createAttachmentUpload = vi.fn().mockResolvedValue({
      method: 'STREAM',
      requiredHeaders: {},
      uploadUrl: '/api/v1/spaces/space-1/attachments/attachment-1/content',
      attachment: { id: 'attachment-1' },
    });
    const uploadAttachmentContent = vi.fn().mockResolvedValue(undefined);
    const finalizeAttachmentUpload = vi.fn().mockResolvedValue({ id: 'attachment-1', status: 'VALIDATING' });
    const getAttachment = vi
      .fn()
      .mockResolvedValueOnce({ id: 'attachment-1', status: 'VALIDATING' })
      .mockResolvedValueOnce({ id: 'attachment-1', status: 'READY' });
    const replaceMemoryAttachments = vi.fn().mockResolvedValue({ id: 'memory-1', title: 'See', version: 2 });

    const flow = new ReferenceFlow({
      api: apiStub({
        memories: { createMemory, replaceMemoryAttachments } as never,
        attachments: {
          createAttachmentUpload,
          uploadAttachmentContent,
          finalizeAttachmentUpload,
          getAttachment,
        } as never,
      }),
      apiBaseUrl: '',
      accessToken: 'token',
      sleep: async () => undefined,
    });

    const image = new File(['pixels'], 'see.jpg', { type: 'image/jpeg' });
    await flow.createMemoryWithImage('space-1', { title: 'See', body: 'Abend', image });

    expect(createMemory).toHaveBeenCalledOnce();
    expect(createAttachmentUpload).toHaveBeenCalledWith(expect.objectContaining({ spaceId: 'space-1' }));
    expect(uploadAttachmentContent).toHaveBeenCalledOnce();
    expect(finalizeAttachmentUpload).toHaveBeenCalledOnce();
    expect(getAttachment).toHaveBeenCalledTimes(2);
    expect(replaceMemoryAttachments).toHaveBeenCalledWith({
      memoryId: 'memory-1',
      spaceId: 'space-1',
      ifMatch: '1',
      memoryAttachmentSet: { attachments: [{ attachmentId: 'attachment-1', position: 0 }] },
    });
  });

  it('rejects video before an upload is started', () => {
    expect(() => validateImage(new File(['video'], 'clip.mp4', { type: 'video/mp4' }))).toThrow(/JPEG/);
  });
});

describe('StoryItem discriminator', () => {
  it('uses the generated kind union for memory titles', () => {
    const item = {
      kind: 'MEMORY',
      effectiveDate: new Date('2026-08-26'),
      memory: { title: 'Sonnenuntergang' },
    } as StoryItem;

    expect(storyItemTitle(item)).toBe('Sonnenuntergang');
  });
});
