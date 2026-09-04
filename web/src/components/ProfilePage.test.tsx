import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { PreferenceCategory } from '../api/generated/models/PreferenceCategory';
import { PreferenceSentiment } from '../api/generated/models/PreferenceSentiment';
import { ProfileVisibility } from '../api/generated/models/ProfileVisibility';
import { ProfilePage } from './ProfilePage';

const SPACE_ID = 'space-1';
const ACCOUNT_ID = 'account-1';

function renderProfilePageFixture(preferences: unknown[] = []): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  queryClient.setQueryData(['profile-identity', SPACE_ID, ACCOUNT_ID], {
    accountId: ACCOUNT_ID,
    displayName: 'Alex',
    profileAttachmentId: null,
    version: 1,
  });

  queryClient.setQueryData(['profile-preferences', SPACE_ID], preferences);

  queryClient.setQueryData(['space', SPACE_ID], {
    id: SPACE_ID,
    partners: [
      { id: ACCOUNT_ID, displayName: 'Alex' },
      { id: 'account-2', displayName: 'Sam' },
    ],
  });

  queryClient.setQueryData(['space-profile', SPACE_ID], {
    relationshipStartedOn: null,
    showRelationshipDuration: false,
    durationDisplayMode: 'YEARS_MONTHS',
    relationshipYears: null,
    relationshipMonths: null,
    relationshipDays: null,
  });

  queryClient.setQueryData(['instance-status'], {
    registrationOpen: false,
    invitationsOpen: false,
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProfilePage
          apiBaseUrl="http://api.example.test"
          accessToken="test-token"
          account={{ id: ACCOUNT_ID, displayName: 'Alex' }}
          spaceId={SPACE_ID}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Profile page reorganization', () => {
  it('renders personal identity hero at top with avatar, display name, partner visibility note, and action buttons', () => {
    const html = renderProfilePageFixture();

    expect(html).toContain('profile-identity-hero-card');
    expect(html).toContain('Alex');
    expect(html).toContain('Dies ist das Profil, das dein Partner sieht.');
    expect(html).toContain('Name ändern');
    expect(html).toContain('Bild ändern');
  });

  it('renders categorized preference chips and [+ Vorliebe] without a permanent empty form', () => {
    const html = renderProfilePageFixture([
      {
        id: 'pref-1',
        accountId: ACCOUNT_ID,
        category: PreferenceCategory.FOOD,
        sentiment: PreferenceSentiment.LOVE,
        topic: 'Pasta',
        value: 'Al dente mit Salbei',
        visibility: ProfileVisibility.SELF_PROFILE,
        version: 1,
      },
      {
        id: 'pref-2',
        accountId: ACCOUNT_ID,
        category: PreferenceCategory.DRINK,
        sentiment: PreferenceSentiment.LIKE,
        topic: 'Kaffee',
        value: 'Hafer-Cappuccino',
        visibility: ProfileVisibility.SELF_PROFILE,
        version: 1,
      },
    ]);

    expect(html).toContain('+ Vorliebe');
    expect(html).toContain('profile-preference-chip');
    expect(html).toContain('Pasta');
    expect(html).toContain('Al dente mit Salbei');
    expect(html).toContain('Kaffee');
    expect(html).toContain('Hafer-Cappuccino');
    // Ensure no permanent inline form is rendered on the page
    expect(html).not.toContain('preference-modal-dialog');
  });

  it('focuses strictly on personal identity and relationship, without technical settings or private area sections', () => {
    const html = renderProfilePageFixture();

    // Contains personal identity & relationship
    expect(html).toContain('profile-identity-hero-card');
    expect(html).toContain('relationship-profile-title');

    // Does not contain any settings elements or private area entry
    expect(html).not.toContain('profile-settings-separator');
    expect(html).not.toContain('profile-settings-section');
    expect(html).not.toContain('profile-settings-index');
    expect(html).not.toContain('settings-index');
    expect(html).not.toContain('id="profile-appearance-settings"');
    expect(html).not.toContain('id="settings-appearance"');
    expect(html).not.toContain('id="profile-partner-settings"');
    expect(html).not.toContain('id="profile-private-settings"');
    expect(html).not.toContain('id="profile-data-settings"');
    expect(html).not.toContain('id="data-transfer"');
    expect(html).not.toContain('href="/more/private/notes"');
  });
});
