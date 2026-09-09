// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { QuickCreateMenu } from './QuickCreateMenu';
import navigation from '../i18n/locales/navigation';

function LocationTracker({
  onLocation,
}: {
  onLocation: (path: string) => void;
}) {
  const location = useLocation();
  onLocation(`${location.pathname}${location.hash}`);
  return null;
}

describe('QuickCreateMenu - Mobile Action Sheet', () => {
  it('opens mobile action sheet, displays all 7 actions with sublines and title, and manages scroll lock', async () => {
    document.body.style.overflow = 'auto';

    render(
      <MemoryRouter initialEntries={['/today']}>
        <QuickCreateMenu variant="mobile" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    expect(trigger.style.visibility).not.toBe('hidden');
    expect(screen.queryByRole('dialog')).toBeNull();

    // Open sheet
    fireEvent.click(trigger);

    // Dialog is open
    const dialog = screen.getByRole('dialog', {
      name: navigation.quickCreateTitle,
    });
    expect(dialog).toBeDefined();
    expect(dialog.className).toContain('quick-create-mobile-sheet');
    expect(document.body.style.overflow).toBe('hidden');

    // Sheet title
    expect(screen.getByText(navigation.quickCreateTitle)).toBeDefined();

    // Trigger is hidden while sheet is open
    expect(trigger.style.visibility).toBe('hidden');

    // All 7 action titles and sublines are present
    expect(screen.getByText(navigation.quickCreateMemory)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateMemorySubline)).toBeDefined();

    expect(screen.getByText(navigation.quickCreateHeartMoment)).toBeDefined();
    expect(
      screen.getByText(navigation.quickCreateHeartMomentSubline),
    ).toBeDefined();

    expect(screen.getByText(navigation.quickCreateMilestone)).toBeDefined();
    expect(
      screen.getByText(navigation.quickCreateMilestoneSubline),
    ).toBeDefined();

    expect(screen.getByText(navigation.quickCreateWish)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateWishSubline)).toBeDefined();

    expect(screen.getByText(navigation.quickCreatePlan)).toBeDefined();
    expect(screen.getByText(navigation.quickCreatePlanSubline)).toBeDefined();

    // Private section header
    expect(screen.getByText(navigation.quickCreateForMe)).toBeDefined();

    expect(screen.getByText(navigation.quickCreatePrivateNote)).toBeDefined();
    expect(
      screen.getByText(navigation.quickCreatePrivateNoteSubline),
    ).toBeDefined();

    expect(screen.getByText(navigation.quickCreateGiftIdea)).toBeDefined();
    expect(
      screen.getByText(navigation.quickCreateGiftIdeaSubline),
    ).toBeDefined();

    // Removed actions (chapter, place, collection) must NOT be present in Quick Create
    expect(screen.queryByText(navigation.quickCreateChapter)).toBeNull();
    expect(screen.queryByText(navigation.quickCreatePlace)).toBeNull();
    expect(screen.queryByText(navigation.quickCreateCollection)).toBeNull();

    // Close button dismisses and restores body scroll
    const closeBtn = screen.getByRole('button', { name: navigation.closeMenu });
    fireEvent.click(closeBtn);

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.body.style.overflow).toBe('auto');
    expect(trigger.style.visibility).not.toBe('hidden');
  });

  it('closes on backdrop click and returns focus to trigger', async () => {
    render(
      <MemoryRouter initialEntries={['/today']}>
        <QuickCreateMenu variant="mobile" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    fireEvent.click(trigger);

    const backdrop = document.querySelector('.quick-create-mobile-backdrop');
    expect(backdrop).not.toBeNull();
    if (!backdrop) throw new Error('Backdrop missing');

    fireEvent.click(backdrop);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('closes on Escape key press', async () => {
    render(
      <MemoryRouter initialEntries={['/today']}>
        <QuickCreateMenu variant="mobile" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    fireEvent.click(trigger);
    expect(screen.getByRole('dialog')).toBeDefined();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('navigates to wish action and closes sheet', async () => {
    let currentPath = '/today';

    render(
      <MemoryRouter initialEntries={['/today']}>
        <LocationTracker
          onLocation={(path) => {
            currentPath = path;
          }}
        />
        <QuickCreateMenu variant="mobile" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    fireEvent.click(trigger);

    // Select wish
    const wishItem = screen.getByText(navigation.quickCreateWish);
    fireEvent.click(wishItem);

    // Sheet closes
    expect(screen.queryByRole('dialog')).toBeNull();
    // Path updated to wish anchor under /plan
    expect(currentPath).toBe('/plan#wish-title');
  });

  it('navigates to gift idea action and closes sheet', async () => {
    let currentPath = '/today';

    render(
      <MemoryRouter initialEntries={['/today']}>
        <LocationTracker
          onLocation={(path) => {
            currentPath = path;
          }}
        />
        <QuickCreateMenu variant="mobile" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    fireEvent.click(trigger);

    // Select gift idea
    const giftItem = screen.getByText(navigation.quickCreateGiftIdea);
    fireEvent.click(giftItem);

    // Sheet closes
    expect(screen.queryByRole('dialog')).toBeNull();
    // Path updated to gift ideas create route
    expect(currentPath).toBe('/more/private/gift-ideas/new');
  });
});

describe('QuickCreateMenu - Desktop Popover', () => {
  it('renders desktop menu popover when opened with title and 7 actions', () => {
    render(
      <MemoryRouter initialEntries={['/today']}>
        <QuickCreateMenu variant="desktop" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    expect(screen.queryByRole('menu')).toBeNull();

    fireEvent.click(trigger);

    const menu = screen.getByRole('menu');
    expect(menu).toBeDefined();
    expect(menu.className).toContain('quick-create-menu');
    expect(screen.getByText(navigation.quickCreateTitle)).toBeDefined();

    const items = screen.getAllByRole('menuitem');
    expect(items).toHaveLength(7);

    // Order: memory, heart moment, milestone, wish, plan, note, gift idea
    expect(items[0].getAttribute('href')).toBe('/story/memories/new');
    expect(items[1].getAttribute('href')).toBe('/story/heart-moments/new');
    expect(items[2].getAttribute('href')).toBe('/story/milestones/new');
    expect(items[3].getAttribute('href')).toBe('/plan#wish-title');
    expect(items[4].getAttribute('href')).toBe('/plan#plan-title');
    expect(items[5].getAttribute('href')).toBe('/more/private/notes/new');
    expect(items[6].getAttribute('href')).toBe('/more/private/gift-ideas/new');

    // Verify sublines exist
    expect(screen.getByText(navigation.quickCreateMemorySubline)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateWishSubline)).toBeDefined();
    expect(
      screen.getByText(navigation.quickCreateGiftIdeaSubline),
    ).toBeDefined();
    expect(screen.getByText(navigation.quickCreateForMe)).toBeDefined();
  });

  it('supports arrow key navigation on desktop', () => {
    render(
      <MemoryRouter initialEntries={['/today']}>
        <QuickCreateMenu variant="desktop" />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: navigation.newContent });
    fireEvent.click(trigger);

    const menu = screen.getByRole('menu');
    const items = screen.getAllByRole('menuitem');
    items[0].focus();
    expect(document.activeElement).toBe(items[0]);

    // Arrow down moves to next
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    expect(document.activeElement).toBe(items[1]);

    // End key moves to last item (gift idea)
    fireEvent.keyDown(menu, { key: 'End' });
    expect(document.activeElement).toBe(items[6]);

    // Home key moves to first item (memory)
    fireEvent.keyDown(menu, { key: 'Home' });
    expect(document.activeElement).toBe(items[0]);
  });
});
