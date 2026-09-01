import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import de from '../i18n/locales/de';
import { ProfileSettingsIndex } from './ProfileSettingsIndex';

describe('ProfileSettingsIndex', () => {
  it('exposes appearance inside the centralized profile settings hierarchy', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <ProfileSettingsIndex />
      </MemoryRouter>,
    );

    expect(html).toContain('href="#profile-appearance-settings"');
    expect(html).toContain(`>${de.theme.label}<`);
  });
});
