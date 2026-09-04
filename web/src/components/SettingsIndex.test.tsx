import { renderToStaticMarkup } from 'react-dom/server';
import de from '../i18n/locales/de';
import profileIdentity from '../i18n/locales/profileIdentity';
import { SettingsIndex } from './SettingsIndex';

describe('SettingsIndex', () => {
  it('exposes navigation links to all four settings sections and excludes privacy', () => {
    const html = renderToStaticMarkup(<SettingsIndex />);

    expect(html).toContain('href="#settings-appearance"');
    expect(html).toContain(`>${de.theme.label}<`);

    expect(html).toContain('href="#settings-notifications"');
    expect(html).toContain(`>${profileIdentity.settingsNotifications}<`);

    expect(html).toContain('href="#settings-connection"');
    expect(html).toContain(`>${profileIdentity.settingsRelationship}<`);

    expect(html).toContain('href="#settings-data"');
    expect(html).toContain(`>${profileIdentity.settingsData}<`);

    expect(html).not.toContain('href="#settings-privacy"');
  });
});
