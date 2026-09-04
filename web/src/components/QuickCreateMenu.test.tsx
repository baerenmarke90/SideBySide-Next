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
  it('opens mobile action sheet, displays all 9 actions, and manages scroll lock', async () => {
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
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeDefined();
    expect(dialog.className).toContain('quick-create-mobile-sheet');
    expect(document.body.style.overflow).toBe('hidden');

    // Trigger is hidden while sheet is open
    expect(trigger.style.visibility).toBe('hidden');

    // All 9 action labels are present without clipping
    expect(screen.getByText(navigation.quickCreateMemory)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateHeartMoment)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateMilestone)).toBeDefined();
    expect(screen.getByText(navigation.quickCreatePlan)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateWish)).toBeDefined();
    expect(screen.getByText(navigation.quickCreatePlace)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateChapter)).toBeDefined();
    expect(screen.getByText(navigation.quickCreateCollection)).toBeDefined();
    expect(screen.getByText(navigation.quickCreatePrivateNote)).toBeDefined();

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

  it('navigates to selected action and closes sheet', async () => {
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

    // Select "Gemeinsame Liste"
    const collectionItem = screen.getByText(navigation.quickCreateCollection);
    fireEvent.click(collectionItem);

    // Sheet closes
    expect(screen.queryByRole('dialog')).toBeNull();
    // Path updated to plan anchor
    expect(currentPath).toBe('/plan#collection-title');
  });
});

describe('QuickCreateMenu - Desktop Popover', () => {
  it('renders desktop menu popover when opened', () => {
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
    expect(screen.getByText(navigation.quickCreateShared)).toBeDefined();
  });
});
