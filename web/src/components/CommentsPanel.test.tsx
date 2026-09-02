import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import type { CommentsApi } from '../api/generated/apis/CommentsApi';
import type { CommentDetail } from '../api/generated/models/CommentDetail';
import { CommentsPanel } from './CommentsPanel';

function comment(overrides: Partial<CommentDetail>): CommentDetail {
  return {
    author: { id: 'author-1', displayName: 'Lea' },
    authorId: 'author-1',
    body: 'A first comment',
    createdAt: new Date('2026-08-01T10:00:00Z'),
    id: 'comment-1',
    spaceId: 'space-1',
    updatedAt: new Date('2026-08-01T10:00:00Z'),
    version: 1,
    ...overrides,
  };
}

function renderPanel(comments: CommentDetail[]): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['comments', 'space-1', 'memory', 'memory-1'], {
    pages: [{ items: comments, hasMore: false, nextCursor: null }],
    pageParams: [null],
  });
  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <CommentsPanel
        commentsApi={{} as CommentsApi}
        spaceId="space-1"
        parentKind="memory"
        parentId="memory-1"
        currentAccountId="me"
        canComment={true}
        offline={false}
      />
    </QueryClientProvider>,
  );
}

describe('CommentsPanel', () => {
  it('offers editing only on the caller’s own comment', () => {
    const html = renderPanel([
      comment({ id: 'own', authorId: 'me', body: 'Mine to fix' }),
      comment({ id: 'partner', authorId: 'them', body: 'Not mine' }),
    ]);

    // #604: editing was previously reachable nowhere in this markup.
    expect(html).toContain('Bearbeiten');
    // Exactly one comment is the caller's own, so exactly one edit button.
    expect(html.match(/comment-edit\b/g)?.length).toBe(1);
  });

  it('never offers editing or deleting a comment that is not the caller’s own', () => {
    const html = renderPanel([comment({ id: 'partner', authorId: 'them' })]);

    expect(html).not.toContain('comment-edit');
    expect(html).not.toContain('comment-delete');
  });

  it('shows the edited marker once updatedAt has moved past createdAt', () => {
    const html = renderPanel([
      comment({
        id: 'own',
        authorId: 'me',
        createdAt: new Date('2026-08-01T10:00:00Z'),
        updatedAt: new Date('2026-08-02T10:00:00Z'),
      }),
    ]);

    expect(html).toContain('bearbeitet');
  });
});
