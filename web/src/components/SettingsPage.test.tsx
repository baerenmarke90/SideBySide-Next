import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { SettingsPage } from './SettingsPage';

const SPACE_ID = 'space-1';
const ACCOUNT_ID = 'account-1';

function renderSettingsPageFixture(): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  queryClient.setQueryData(['space', SPACE_ID], {
    id: SPACE_ID,
    partners: [
      { id: ACCOUNT_ID, displayName: 'Alex' },
      { id: 'account-2', displayName: 'Sam' },
    ],
  });

  queryClient.setQueryData(['profile-identity', SPACE_ID, 'account-2'], {
    accountId: 'account-2',
    displayName: 'Sam',
    profileAttachmentId: null,
    version: 1,
  });

  queryClient.setQueryData(['instance-status'], {
    registrationOpen: false,
    invitationsOpen: false,
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SettingsPage
          apiBaseUrl="http://api.example.test"
          accessToken="test-token"
          account={{ id: ACCOUNT_ID, displayName: 'Alex' }}
          spaceId={SPACE_ID}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('SettingsPage', () => {
  it('renders settings header and all five dedicated configuration sections', () => {
    const html = renderSettingsPageFixture();

    // Page header
    expect(html).toContain('settings-page');
    expect(html).toContain('Einstellungen');

    // Quick Index
    expect(html).toContain('settings-index');

    // Section 1: Appearance
    expect(html).toContain('id="settings-appearance"');
    expect(html).toContain('theme-control');

    // Section 2: Notifications
    expect(html).toContain('id="settings-notifications"');
    expect(html).toContain('href="/more/notifications"');

    // Section 3: Connection
    expect(html).toContain('id="settings-connection"');
    expect(html).toContain('partner-identity-title');

    // Section 4: Privacy / Mein Bereich
    expect(html).toContain('id="settings-privacy"');
    expect(html).toContain('href="/more/private/notes"');

    // Section 5: Data & Portability
    expect(html).toContain('id="settings-data"');
    expect(html).toContain('id="data-transfer"');
  });
});
