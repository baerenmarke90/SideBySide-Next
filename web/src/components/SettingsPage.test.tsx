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

  queryClient.setQueryData(
    ['rules', SPACE_ID, 'relationship_anniversary_reminder', 'preference'],
    {
      ruleKey: 'relationship_anniversary_reminder',
      enabled: true,
      parameters: {
        daysBefore: [30, 7, 1],
        localTime: '09:00:00',
      },
    },
  );

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
  it('renders settings header, index, and five dedicated configuration sections', () => {
    const html = renderSettingsPageFixture();

    // Page header
    expect(html).toContain('settings-page');
    expect(html).toContain('Einstellungen');

    // Quick Index
    expect(html).toContain('settings-index');
    expect(html).toContain('href="#settings-account"');

    // Section 1: Appearance
    expect(html).toContain('id="settings-appearance"');
    expect(html).toContain('theme-control');

    // Section 2: Notifications (retained with inbox link and real anniversary reminder configuration)
    expect(html).toContain('id="settings-notifications"');
    expect(html).toContain('anniversary-reminder-form');
    expect(html).toContain('name="anniversaryReminderEnabled"');
    expect(html).toContain('href="/more/notifications"');

    // Section 3: Account hub with a distinct Danger Zone
    expect(html).toContain('id="settings-account"');
    expect(html).toContain('account-settings-panel');
    expect(html).toContain('account-danger-zone');
    expect(html).toContain('Konto löschen');

    // Section 4: Relationship configuration remains distinct from Account deletion
    expect(html).toContain('id="settings-connection"');
    expect(html).toContain('relationship-settings-title');
    expect(html).toContain('name="relationshipStartedOn"');
    expect(html).toContain('name="showRelationshipDuration"');

    // Section 5: Data & Portability
    expect(html).toContain('id="settings-data"');
    expect(html).toContain('id="data-transfer"');
  });

  it('keeps private area and partner identity out of Settings while Account deletion stays separate from relationship actions', () => {
    const html = renderSettingsPageFixture();

    expect(html).not.toContain('id="settings-privacy"');
    expect(html).not.toContain('/more/private');
    expect(html).not.toContain('Mein Bereich');
    expect(html).not.toContain('partner-identity-title');

    expect(html).toContain('id="settings-account"');
    expect(html).toContain('id="settings-connection"');
  });
});
