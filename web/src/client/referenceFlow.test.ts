import { UploadDescriptorMethodEnum } from '../api/generated/models/UploadDescriptor';
import { uploadAttachmentBytes } from './referenceFlow';

describe('uploadAttachmentBytes', () => {
  it('adds bearer authorization only for the authenticated STREAM transport', async () => {
    const fetchApi = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      expect(new Headers(init?.headers).get('Authorization')).toBe('Bearer token');
      expect(init?.body).toBeInstanceOf(File);
      return new Response(null, { status: 204 });
    }) as unknown as typeof fetch;

    await uploadAttachmentBytes(
      'https://example.invalid',
      'token',
      {
        attachment: { id: 'a', createdAt: new Date(), durationSeconds: null, hasThumbnail: false, height: null, mediaType: 'IMAGE', mimeType: null, size: null, status: 'UPLOADING', version: 1, width: null },
        method: UploadDescriptorMethodEnum.STREAM,
        requiredHeaders: { 'Content-Type': 'image/jpeg' },
        uploadUrl: '/api/v1/spaces/s/attachments/a/content',
      },
      new File(['image'], 'test.jpg', { type: 'image/jpeg' }),
      fetchApi,
    );

    expect(fetchApi).toHaveBeenCalledOnce();
  });

  it('does not leak the bearer token to a signed upload URL', async () => {
    const fetchApi = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      expect(new Headers(init?.headers).has('Authorization')).toBe(false);
      return new Response(null, { status: 200 });
    }) as unknown as typeof fetch;

    await uploadAttachmentBytes(
      'https://api.example.invalid',
      'secret-token',
      {
        attachment: { id: 'a', createdAt: new Date(), durationSeconds: null, hasThumbnail: false, height: null, mediaType: 'IMAGE', mimeType: null, size: null, status: 'UPLOADING', version: 1, width: null },
        method: UploadDescriptorMethodEnum.SIGNED_UPLOAD,
        requiredHeaders: {},
        uploadUrl: 'https://storage.example.invalid/signed',
      },
      new File(['image'], 'test.jpg', { type: 'image/jpeg' }),
      fetchApi,
    );
  });
});
