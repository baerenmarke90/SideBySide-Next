import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { PreferenceCategory } from '../api/generated/models/PreferenceCategory';
import { PreferenceSentiment } from '../api/generated/models/PreferenceSentiment';
import { ProfileVisibility } from '../api/generated/models/ProfileVisibility';
import { ProfilePage } from './ProfilePage';

const SPACE_ID = 'space-1';
const ACCOUNT_ID = 'account-1';

function renderProfilePageFixture(
  preferences: unknown[] = [],
  partnerPreferences: unknown[] = [],
  spaceProfileOverrides: Record<string, unknown> = {},
): string {
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

  queryClient.setQueryData(['partner-profile', SPACE_ID, 'account-2'], {
    accountId: 'account-2',
    displayName: 'Sam',
    profileAttachmentId: null,
    preferences: partnerPreferences,
    version: 1,
  });

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
    ...spaceProfileOverrides,
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

  it('focuses strictly on personal identity, partner identity, and read-only relationship summary', () => {
    const html = renderProfilePageFixture();

    // Contains personal identity, partner identity, and read-only relationship summary
    expect(html).toContain('profile-identity-hero-card');
    expect(html).toContain('partner-identity-title');
    expect(html).toContain('relationship-summary-title');

    // Does NOT contain editable relationship settings form in Profile
    expect(html).not.toContain('relationship-profile-title');
    expect(html).not.toContain('name="relationshipStartedOn"');

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
    expect(html).not.toContain('href="/more/private');
    expect(html).not.toContain('/more/private/notes');
  });

  it('differentiates + Vorliebe for own profile vs + Notiz with privacy badge for private partner notes', () => {
    const html = renderProfilePageFixture([
      {
        id: 'pref-self',
        accountId: ACCOUNT_ID,
        category: PreferenceCategory.FOOD,
        sentiment: PreferenceSentiment.LOVE,
        topic: 'Pasta',
        value: 'Al dente mit Salbei',
        visibility: ProfileVisibility.SELF_PROFILE,
        version: 1,
      },
      {
        id: 'pref-note',
        accountId: 'account-2',
        category: PreferenceCategory.FLOWERS,
        sentiment: PreferenceSentiment.LOVE,
        topic: 'Lieblingsblumen',
        value: 'Pfingstrosen im Juni',
        visibility: ProfileVisibility.PRIVATE_PARTNER_NOTE,
        version: 1,
      },
    ]);

    // Self preferences use + Vorliebe
    expect(html).toContain('+ Vorliebe');
    expect(html).toContain('Pasta');

    // Private partner notes use + Notiz and carry privacy indicator
    expect(html).toContain('+ Notiz');
    expect(html).toContain('Lieblingsblumen');
    expect(html).toContain('private-partner-notes-badge');
  });

  it('filters self preferences strictly by current account ID and shows partner preferences only in read-only section', () => {
    const html = renderProfilePageFixture(
      [
        {
          id: 'pref-self',
          accountId: ACCOUNT_ID,
          category: PreferenceCategory.FOOD,
          sentiment: PreferenceSentiment.LOVE,
          topic: 'Pasta',
          value: 'Al dente mit Salbei',
          visibility: ProfileVisibility.SELF_PROFILE,
          version: 1,
        },
        {
          id: 'pref-partner-shared',
          accountId: 'account-2',
          category: PreferenceCategory.DRINK,
          sentiment: PreferenceSentiment.LIKE,
          topic: 'Matcha Tea',
          value: 'Zeremoniell',
          visibility: ProfileVisibility.SELF_PROFILE,
          version: 1,
        },
      ],
      [
        {
          id: 'pref-partner-shared',
          accountId: 'account-2',
          category: PreferenceCategory.DRINK,
          sentiment: PreferenceSentiment.LIKE,
          topic: 'Matcha Tea',
          value: 'Zeremoniell',
          visibility: ProfileVisibility.SELF_PROFILE,
          version: 1,
        },
      ],
    );

    // Current account's preference appears in "Meine Vorlieben" as an editable chip
    expect(html).toContain('Pasta');
    expect(html).toContain('Al dente mit Salbei');

    // Partner preference is NOT rendered as an editable chip in self preferences
    expect(html).not.toContain(
      'profile-preference-chip" type="button"><span aria-hidden="true" class="profile-preference-chip-sentiment" data-sentiment="LIKE">👍</span><span class="profile-preference-chip-topic">Matcha Tea',
    );

    // Partner preference appears exclusively in the read-only partner profile section as a card
    expect(html).toContain('Profil von Sam');
    expect(html).toContain('profile-preference-card');
    expect(html).toContain('Matcha Tea');
    expect(html).toContain('Zeremoniell');
  });

  it('renders both anniversary date and duration in read-only relationship summary when configured', () => {
    const html = renderProfilePageFixture([], [], {
      relationshipStartedOn: new Date('2022-02-14T00:00:00.000Z'),
      showRelationshipDuration: true,
      durationDisplayMode: 'YEARS_MONTHS',
      relationshipYears: 4,
      relationshipMonths: 6,
    });

    expect(html).toContain('relationship-summary-section');
    expect(html).toContain('profile-relationship-start');
    expect(html).toContain('Zusammen seit');
    expect(html).toContain('profile-duration');
    expect(html).toContain('Eure Zeit');
    expect(html).toContain('4 Jahre, 6 Monate');
  });
});
