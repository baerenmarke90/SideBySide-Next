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

  queryClient.setQueryData(['space-profile', SPACE_ID], {
    relationshipStartedOn: '2022-02-14',
    showRelationshipDuration: true,
    durationDisplayMode: 'YEARS_MONTHS',
    relationshipYears: 3,
    relationshipMonths: 0,
    relationshipDays: null,
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
  it('renders settings header, index, and four dedicated configuration sections', () => {
    const html = renderSettingsPageFixture();

    // Page header
    expect(html).toContain('settings-page');
    expect(html).toContain('Einstellungen');

    // Quick Index
    expect(html).toContain('settings-index');

    // Section 1: Appearance
    expect(html).toContain('id="settings-appearance"');
    expect(html).toContain('theme-control');

    // Section 2: Notifications (retained with inbox link and clear distinction)
    expect(html).toContain('id="settings-notifications"');
    expect(html).toContain('href="/more/notifications"');

    // Section 3: Connection & Relationship configuration form
    expect(html).toContain('id="settings-connection"');
    expect(html).toContain('relationship-settings-title');
    expect(html).toContain('name="relationshipStartedOn"');
    expect(html).toContain('name="showRelationshipDuration"');

    // Section 4: Data & Portability
    expect(html).toContain('id="settings-data"');
    expect(html).toContain('id="data-transfer"');
  });

  it('verifies strict settings information architecture: no private area and partner identity only in profile', () => {
    const html = renderSettingsPageFixture();

    // No Private Area in Settings
    expect(html).not.toContain('id="settings-privacy"');
    expect(html).not.toContain('/more/private');
    expect(html).not.toContain('Mein Bereich');

    // Partner identity belongs strictly in Profile, not Settings
    expect(html).not.toContain('partner-identity-title');
  });
});
