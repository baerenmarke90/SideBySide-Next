import {
  attachmentDraftReducer,
  readyAttachmentIds,
  type AttachmentDraft,
} from './attachmentDraftState';

function draft(id: string): AttachmentDraft {
  return {
    id,
    file: new File(['image'], `${id}.jpg`, { type: 'image/jpeg' }),
    previewUrl: `blob:${id}`,
    status: 'uploading',
    attempt: 0,
  };
}

describe('attachmentDraftReducer', () => {
  it('ignores a late READY result after the draft was removed', () => {
    let state = attachmentDraftReducer([], { type: 'add', draft: draft('one') });
    state = attachmentDraftReducer(state, {
      type: 'start',
      id: 'one',
      attempt: 1,
    });
    state = attachmentDraftReducer(state, { type: 'remove', id: 'one' });
    state = attachmentDraftReducer(state, {
      type: 'ready',
      id: 'one',
      attempt: 1,
      attachmentId: 'attachment-old',
    });

    expect(state).toEqual([]);
  });

  it('ignores a stale retry result and keeps the latest attempt authoritative', () => {
    let state = attachmentDraftReducer([], { type: 'add', draft: draft('one') });
    state = attachmentDraftReducer(state, {
      type: 'start',
      id: 'one',
      attempt: 1,
    });
    state = attachmentDraftReducer(state, {
      type: 'start',
      id: 'one',
      attempt: 2,
    });
    state = attachmentDraftReducer(state, {
      type: 'ready',
      id: 'one',
      attempt: 1,
      attachmentId: 'attachment-stale',
    });
    expect(state[0]).toMatchObject({ status: 'uploading', attempt: 2 });

    state = attachmentDraftReducer(state, {
      type: 'ready',
      id: 'one',
      attempt: 2,
      attachmentId: 'attachment-current',
    });
    expect(state[0]).toMatchObject({
      status: 'ready',
      attempt: 2,
      attachmentId: 'attachment-current',
    });
  });

  it('returns only READY attachments in stable user-visible order', () => {
    let state = [draft('one'), draft('two'), draft('three')];
    state = attachmentDraftReducer(state, {
      type: 'start',
      id: 'one',
      attempt: 1,
    });
    state = attachmentDraftReducer(state, {
      type: 'ready',
      id: 'one',
      attempt: 1,
      attachmentId: 'attachment-1',
    });
    state = attachmentDraftReducer(state, {
      type: 'start',
      id: 'two',
      attempt: 2,
    });
    state = attachmentDraftReducer(state, {
      type: 'failed',
      id: 'two',
      attempt: 2,
      error: 'failed',
    });
    state = attachmentDraftReducer(state, {
      type: 'start',
      id: 'three',
      attempt: 3,
    });
    state = attachmentDraftReducer(state, {
      type: 'ready',
      id: 'three',
      attempt: 3,
      attachmentId: 'attachment-3',
    });

    expect(readyAttachmentIds(state)).toEqual([
      'attachment-1',
      'attachment-3',
    ]);
  });
});
