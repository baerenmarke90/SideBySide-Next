import { AttachmentsApi } from '../api/generated/apis/AttachmentsApi';
import { AuthApi } from '../api/generated/apis/AuthApi';
import { MemoriesApi } from '../api/generated/apis/MemoriesApi';
import { StoryApi } from '../api/generated/apis/StoryApi';
import { Configuration, ResponseError } from '../api/generated/runtime';
import type { MemoryCreate } from '../api/generated/models/MemoryCreate';
import type { MemoryDetail } from '../api/generated/models/MemoryDetail';
import type { SessionView } from '../api/generated/models/SessionView';
import type { StoryPage } from '../api/generated/models/StoryPage';
import type { UploadDescriptor } from '../api/generated/models/UploadDescriptor';
import { UploadDescriptorMethodEnum } from '../api/generated/models/UploadDescriptor';
import { ReadDescriptorMethodEnum } from '../api/generated/models/ReadDescriptor';
import { AttachmentReadRequestParentTypeEnum } from '../api/generated/models/AttachmentReadRequest';
import { MediaType } from '../api/generated/models/MediaType';

export interface FlowResult {
  memory: MemoryDetail;
  story: StoryPage;
  imageUrl: string;
}

export interface ReferenceApis {
  attachments: AttachmentsApi;
  auth: AuthApi;
  memories: MemoriesApi;
  story: StoryApi;
}

interface ApiProblem {
  detail?: unknown;
  title?: unknown;
  code?: unknown;
}

export function createReferenceApis(apiBaseUrl: string, accessToken?: string): ReferenceApis {
  const configuration = new Configuration({
    basePath: apiBaseUrl,
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
  });

  return {
    attachments: new AttachmentsApi(configuration),
    auth: new AuthApi(configuration),
    memories: new MemoriesApi(configuration),
    story: new StoryApi(configuration),
  };
}

function resolveTransportUrl(apiBaseUrl: string, target: string): string {
  if (/^https?:\/\//i.test(target)) return target;
  return `${apiBaseUrl.replace(/\/+$/, '')}/${target.replace(/^\/+/, '')}`;
}

async function rethrowWithProblemDetail(error: unknown, fallback: string): Promise<never> {
  if (!(error instanceof ResponseError)) {
    if (error instanceof Error) throw error;
    throw new Error(fallback);
  }

  let message = fallback;
  try {
    const problem = (await error.response.clone().json()) as ApiProblem;
    if (typeof problem.detail === 'string' && problem.detail.trim()) {
      message = problem.detail.trim();
    } else if (typeof problem.title === 'string' && problem.title.trim()) {
      message = problem.title.trim();
    }
  } catch {
    const statusText = `${error.response.status} ${error.response.statusText}`.trim();
    if (statusText) message = `${fallback} (${statusText})`;
  }

  throw new Error(message);
}

async function assertOk(response: Response, action: string): Promise<void> {
  if (response.ok) return;
  let detail = `${response.status} ${response.statusText}`.trim();
  try {
    const problem = (await response.json()) as { detail?: string };
    if (problem.detail) detail = problem.detail;
  } catch {
    // Binary/empty error responses intentionally keep the HTTP status text.
  }
  throw new Error(`${action}: ${detail}`);
}

export async function uploadAttachmentBytes(
  apiBaseUrl: string,
  accessToken: string,
  descriptor: UploadDescriptor,
  file: File,
  fetchApi: typeof fetch = fetch,
): Promise<void> {
  const headers = new Headers(descriptor.requiredHeaders);
  if (descriptor.method === UploadDescriptorMethodEnum.STREAM) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetchApi(resolveTransportUrl(apiBaseUrl, descriptor.uploadUrl), {
    method: 'PUT',
    headers,
    body: file,
  });
  await assertOk(response, 'Bild-Upload fehlgeschlagen');
}

async function waitUntilReady(apis: ReferenceApis, spaceId: string, attachmentId: string): Promise<void> {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    const attachment = await apis.attachments.getAttachment({ spaceId, attachmentId });
    if (attachment.status === 'READY') return;
    if (attachment.status === 'FAILED' || attachment.status === 'DELETE_FAILED' || attachment.status === 'DELETING') {
      throw new Error(`Medienverarbeitung beendet mit Status ${attachment.status}.`);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error('Medienverarbeitung hat das READY-Fenster nicht rechtzeitig erreicht.');
}

export async function loadAuthorizedImage(
  apis: ReferenceApis,
  apiBaseUrl: string,
  accessToken: string,
  spaceId: string,
  memoryId: string,
  attachmentId: string,
  fetchApi: typeof fetch = fetch,
): Promise<string> {
  const descriptor = await apis.attachments.createAttachmentReadAccess({
    spaceId,
    attachmentId,
    attachmentReadRequest: {
      parentType: AttachmentReadRequestParentTypeEnum.MEMORY,
      parentId: memoryId,
    },
  });

  const headers = new Headers();
  if (descriptor.method === ReadDescriptorMethodEnum.STREAM) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  const response = await fetchApi(resolveTransportUrl(apiBaseUrl, descriptor.url), { headers });
  await assertOk(response, 'Bild konnte nicht geladen werden');
  return URL.createObjectURL(await response.blob());
}

export async function signIn(
  apiBaseUrl: string,
  email: string,
  password: string,
): Promise<SessionView> {
  const { auth } = createReferenceApis(apiBaseUrl);
  try {
    return await auth.signInApiV1AuthSignInPost({
      signInRequest: {
        email,
        password,
        deviceName: 'SideBySide Web M2 Referenzflow',
        platform: 'web',
      },
    });
  } catch (error) {
    return rethrowWithProblemDetail(error, 'Anmeldung fehlgeschlagen.');
  }
}

export async function runMemoryMediaStoryFlow(
  apis: ReferenceApis,
  apiBaseUrl: string,
  accessToken: string,
  spaceId: string,
  memoryCreate: MemoryCreate,
  file: File,
  fetchApi: typeof fetch = fetch,
): Promise<FlowResult> {
  if (!file.type.startsWith('image/')) throw new Error('S8 akzeptiert ausschließlich Bilder.');

  try {
    const memory = await apis.memories.createMemory({ spaceId, memoryCreate });
    const upload = await apis.attachments.createAttachmentUpload({
      spaceId,
      attachmentUploadCreate: {
        expectedMimeType: file.type,
        expectedSize: file.size,
        mediaType: MediaType.IMAGE,
        originalName: file.name,
      },
    });

    await uploadAttachmentBytes(apiBaseUrl, accessToken, upload, file, fetchApi);
    await apis.attachments.finalizeAttachmentUpload({
      spaceId,
      attachmentId: upload.attachment.id,
      body: {},
    });
    await waitUntilReady(apis, spaceId, upload.attachment.id);

    const boundMemory = await apis.memories.replaceMemoryAttachments({
      spaceId,
      memoryId: memory.id,
      ifMatch: String(memory.version),
      memoryAttachmentSet: {
        attachments: [{ attachmentId: upload.attachment.id, position: 0 }],
      },
    });

    const story = await apis.story.getStoryTimeline({ spaceId, limit: 25 });
    const imageUrl = await loadAuthorizedImage(
      apis,
      apiBaseUrl,
      accessToken,
      spaceId,
      boundMemory.id,
      upload.attachment.id,
      fetchApi,
    );

    return { memory: boundMemory, story, imageUrl };
  } catch (error) {
    return rethrowWithProblemDetail(error, 'Erinnerung konnte nicht gespeichert werden.');
  }
}
