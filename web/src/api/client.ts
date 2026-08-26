import {
  AttachmentsApi,
  AuthApi,
  Configuration,
  MemoriesApi,
  StoryApi,
} from './generated';

export interface ApiSet {
  attachments: AttachmentsApi;
  auth: AuthApi;
  memories: MemoriesApi;
  story: StoryApi;
}

export function createApiSet(basePath: string, accessToken?: string): ApiSet {
  const configuration = new Configuration({
    basePath,
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
  });

  return {
    attachments: new AttachmentsApi(configuration),
    auth: new AuthApi(configuration),
    memories: new MemoriesApi(configuration),
    story: new StoryApi(configuration),
  };
}

export function absoluteApiUrl(basePath: string, url: string): string {
  if (/^https?:\/\//i.test(url)) return url;
  if (!basePath) return url;
  return `${basePath}${url.startsWith('/') ? '' : '/'}${url}`;
}
