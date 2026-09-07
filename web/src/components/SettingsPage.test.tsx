import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import accountSettings from '../i18n/locales/accountSettings';
import spaceOffboarding from '../i18n/locales/spaceOffboarding';
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
  it('renders relationship context first and keeps sensitive actions at the end', () => {
    const html = renderSettingsPageFixture();

    expect(html).toContain('settings-page');
    expect(html).toContain('Einstellungen');
    expect(html).toContain('settings-index');

    expect(html).toContain('id="settings-connection"');
    expect(html).toContain('relationship-settings-title');
    expect(html).toContain('name="relationshipStartedOn"');
    expect(html).toContain('name="showRelationshipDuration"');

    expect(html).toContain('id="settings-notifications"');
    expect(html).toContain('anniversary-reminder-form');
    expect(html).toContain('name="anniversaryReminderEnabled"');
    expect(html).toContain('href="/more/notifications"');

    expect(html).toContain('id="settings-appearance"');
    expect(html).toContain('theme-control');

    expect(html).toContain('id="settings-data"');
    expect(html).toContain('id="data-transfer"');

    expect(html).toContain('id="settings-account"');
    expect(html).toContain('settings-sensitive-zone');
    expect(html).toContain('account-settings-panel');
    expect(html).toContain('account-danger-zone');
    expect(html).toContain('<h3 id="account-settings-title">Account</h3>');
    expect(html).toContain(`<h4>${accountSettings.dangerTitle}</h4>`);
    expect(html).toContain(accountSettings.deleteAction);
    expect(html).toContain('space-offboarding-panel');
    expect(html).toContain(spaceOffboarding.action);

    const connectionIndex = html.indexOf('id="settings-connection"');
    const notificationsIndex = html.indexOf('id="settings-notifications"');
    const appearanceIndex = html.indexOf('id="settings-appearance"');
    const dataIndex = html.indexOf('id="settings-data"');
    const accountIndex = html.indexOf('id="settings-account"');

    expect(connectionIndex).toBeGreaterThanOrEqual(0);
    expect(notificationsIndex).toBeGreaterThan(connectionIndex);
    expect(appearanceIndex).toBeGreaterThan(notificationsIndex);
    expect(dataIndex).toBeGreaterThan(appearanceIndex);
    expect(accountIndex).toBeGreaterThan(dataIndex);
  });

  it('keeps Account, Space, and private-area semantics separate with canonical consumer branding', () => {
    const html = renderSettingsPageFixture();

    expect(html).not.toContain('id="settings-privacy"');
    expect(html).not.toContain('/more/private');
    expect(html).not.toContain('Mein Bereich');
    expect(html).not.toContain('partner-identity-title');

    expect(html).toContain(accountSettings.deleteAction);
    expect(html).toContain(spaceOffboarding.action);
    expect(html).toContain('eimir.');
    expect(html).not.toContain('SideBySide');
  });
});
