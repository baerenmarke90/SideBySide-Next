// @vitest-environment jsdom
import '../i18n';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { i18n } from '../i18n';
import { PlanStoryContinuation } from './PlanStoryContinuation';

const plan: PlanDetail = {
  capabilities: { canComment: true, canDelete: true, canEdit: true },
  createdAt: new Date('2026-08-01T10:00:00Z'),
  createdBy: 'account-1',
  creator: { id: 'account-1', displayName: 'Lea' },
  description: 'Bring the picnic blanket.',
  experiencedOn: new Date('2026-09-14T00:00:00Z'),
  id: 'plan-1',
  placeId: null,
  plannedEnd: null,
  plannedOn: null,
  plannedStart: null,
  sourceWishId: null,
  spaceId: 'space-1',
  status: 'COMPLETED',
  title: 'Picnic in the park',
  updatedAt: new Date('2026-09-14T16:00:00Z'),
  version: 4,
};

function makeApis(options: { failFirstLink?: boolean } = {}) {
  const createMemory = vi.fn().mockResolvedValue({
    id: 'memory-1',
    title: plan.title,
  });
  const createMilestone = vi.fn().mockResolvedValue({
    id: 'milestone-1',
    title: plan.title,
  });
  const listChapters = vi.fn().mockResolvedValue({
    items: [{ id: 'chapter-1', title: 'Summer 2026' }],
    nextCursor: null,
  });
  const createChapter = vi.fn().mockResolvedValue({
    id: 'chapter-new',
    title: 'Our picnic summer',
  });
  const linkChapterMemory = options.failFirstLink
    ? vi
        .fn()
        .mockRejectedValueOnce(new Error('link failed'))
        .mockResolvedValueOnce(undefined)
    : vi.fn().mockResolvedValue(undefined);
  const linkChapterMilestone = vi.fn().mockResolvedValue(undefined);

  const apis = {
    memories: { createMemory },
    milestones: { createMilestone },
    chapters: { listChapters, createChapter },
    chapterRelations: { linkChapterMemory, linkChapterMilestone },
  } as unknown as SharedPlanningApis;

  return {
    apis,
    createMemory,
    createMilestone,
    listChapters,
    createChapter,
    linkChapterMemory,
    linkChapterMilestone,
  };
}

function renderContinuation(apis: SharedPlanningApis) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <PlanStoryContinuation apis={apis} spaceId="space-1" plan={plan} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => cleanup());

describe('PlanStoryContinuation', () => {
  it('prefills a Memory from the completed Plan and links the saved Memory to an existing Chapter', async () => {
    const mocks = makeApis();
    renderContinuation(mocks.apis);

    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.memoryAction'),
      }),
    );

    const title = screen.getByLabelText(
      i18n.t('m5s3.common.title'),
    ) as HTMLInputElement;
    const date = screen.getByLabelText(
      i18n.t('m5s3.plan.experiencedOn'),
    ) as HTMLInputElement;
    const note = screen.getByLabelText(
      i18n.t('m5s3.planStory.noteLabel'),
    ) as HTMLTextAreaElement;

    expect(title.value).toBe('Picnic in the park');
    expect(date.value).toBe('2026-09-14');
    expect(note.value).toBe('Bring the picnic blanket.');

    fireEvent.click(
      screen.getByRole('button', { name: i18n.t('m5s3.planStory.saveStory') }),
    );

    await waitFor(() => expect(mocks.createMemory).toHaveBeenCalledTimes(1));
    expect(mocks.createMemory).toHaveBeenCalledWith({
      spaceId: 'space-1',
      memoryCreate: {
        title: 'Picnic in the park',
        body: 'Bring the picnic blanket.',
        happenedOn: new Date('2026-09-14T00:00:00Z'),
      },
    });

    await screen.findByText(i18n.t('m5s3.planStory.memorySaved'));
    await waitFor(() => expect(mocks.listChapters).toHaveBeenCalledTimes(1));

    const chapterChoice = screen.getByLabelText(
      i18n.t('m5s3.planStory.chapterChoiceLabel'),
    ) as HTMLSelectElement;
    fireEvent.change(chapterChoice, { target: { value: 'chapter-1' } });
    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.chapterLink'),
      }),
    );

    await waitFor(() =>
      expect(mocks.linkChapterMemory).toHaveBeenCalledTimes(1),
    );
    expect(mocks.linkChapterMemory).toHaveBeenCalledWith({
      spaceId: 'space-1',
      chapterId: 'chapter-1',
      targetId: 'memory-1',
    });
  });

  it('creates a Milestone from the completed Plan and uses the typed Milestone Chapter relation', async () => {
    const mocks = makeApis();
    renderContinuation(mocks.apis);

    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.milestoneAction'),
      }),
    );
    fireEvent.click(
      screen.getByRole('button', { name: i18n.t('m5s3.planStory.saveStory') }),
    );

    await waitFor(() => expect(mocks.createMilestone).toHaveBeenCalledTimes(1));
    expect(mocks.createMilestone).toHaveBeenCalledWith({
      spaceId: 'space-1',
      milestoneCreate: {
        title: 'Picnic in the park',
        body: 'Bring the picnic blanket.',
        happenedOn: new Date('2026-09-14T00:00:00Z'),
      },
    });
    expect(mocks.createMemory).not.toHaveBeenCalled();

    await screen.findByText(i18n.t('m5s3.planStory.milestoneSaved'));
    const chapterChoice = screen.getByLabelText(
      i18n.t('m5s3.planStory.chapterChoiceLabel'),
    ) as HTMLSelectElement;
    fireEvent.change(chapterChoice, { target: { value: 'chapter-1' } });
    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.chapterLink'),
      }),
    );

    await waitFor(() =>
      expect(mocks.linkChapterMilestone).toHaveBeenCalledTimes(1),
    );
    expect(mocks.linkChapterMilestone).toHaveBeenCalledWith({
      spaceId: 'space-1',
      chapterId: 'chapter-1',
      targetId: 'milestone-1',
    });
    expect(mocks.linkChapterMemory).not.toHaveBeenCalled();
  });

  it('retries only the typed Chapter link after a new Chapter was created', async () => {
    const mocks = makeApis({ failFirstLink: true });
    renderContinuation(mocks.apis);

    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.chapterAction'),
      }),
    );
    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.chapterViaMemory'),
      }),
    );
    fireEvent.click(
      screen.getByRole('button', { name: i18n.t('m5s3.planStory.saveStory') }),
    );

    await screen.findByText(i18n.t('m5s3.planStory.memorySaved'));
    const chapterChoice = screen.getByLabelText(
      i18n.t('m5s3.planStory.chapterChoiceLabel'),
    ) as HTMLSelectElement;
    fireEvent.change(chapterChoice, { target: { value: '__new__' } });

    fireEvent.change(
      screen.getByLabelText(i18n.t('m5s3.planStory.chapterNewTitle')),
      { target: { value: 'Our picnic summer' } },
    );
    fireEvent.click(
      screen.getByRole('button', {
        name: i18n.t('m5s3.planStory.chapterCreateAndLink'),
      }),
    );

    await waitFor(() => expect(mocks.createChapter).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(mocks.linkChapterMemory).toHaveBeenCalledTimes(1),
    );

    fireEvent.click(
      await screen.findByRole('button', {
        name: i18n.t('m5s3.planStory.chapterRetryLink'),
      }),
    );

    await waitFor(() =>
      expect(mocks.linkChapterMemory).toHaveBeenCalledTimes(2),
    );
    expect(mocks.createMemory).toHaveBeenCalledTimes(1);
    expect(mocks.createChapter).toHaveBeenCalledTimes(1);
  });

  it('allows the follow-up to be dismissed without creating Story content', () => {
    const mocks = makeApis();
    renderContinuation(mocks.apis);

    fireEvent.click(
      screen.getByRole('button', { name: i18n.t('m5s3.planStory.later') }),
    );

    expect(screen.queryByText(i18n.t('m5s3.planStory.intro'))).toBeNull();
    expect(mocks.createMemory).not.toHaveBeenCalled();
    expect(mocks.createMilestone).not.toHaveBeenCalled();
  });
});
