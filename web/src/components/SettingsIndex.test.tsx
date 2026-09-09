import { renderToStaticMarkup } from 'react-dom/server';
import de from '../i18n/locales/de';
import profileIdentity from '../i18n/locales/profileIdentity';
import { SettingsIndex } from './SettingsIndex';

describe('SettingsIndex', () => {
  it('exposes all consumer settings sections in human-first order and excludes privacy', () => {
    const html = renderToStaticMarkup(<SettingsIndex />);

    expect(html).toContain('href="#settings-connection"');
    expect(html).toContain(`>${profileIdentity.settingsRelationship}<`);

    expect(html).toContain('href="#settings-dashboard"');
    expect(html).toContain(`>${profileIdentity.settingsDashboard}<`);

    expect(html).toContain('href="#settings-notifications"');
    expect(html).toContain(`>${profileIdentity.settingsNotifications}<`);

    expect(html).toContain('href="#settings-appearance"');
    expect(html).toContain(`>${de.theme.label}<`);

    expect(html).toContain('href="#settings-data"');
    expect(html).toContain(`>${profileIdentity.settingsData}<`);

    expect(html).toContain('href="#settings-account"');
    expect(html).toContain(`>${profileIdentity.settingsSensitiveTitle}<`);

    expect(html.indexOf('href="#settings-connection"')).toBeLessThan(
      html.indexOf('href="#settings-dashboard"'),
    );
    expect(html.indexOf('href="#settings-dashboard"')).toBeLessThan(
      html.indexOf('href="#settings-notifications"'),
    );
    expect(html.indexOf('href="#settings-notifications"')).toBeLessThan(
      html.indexOf('href="#settings-appearance"'),
    );
    expect(html.indexOf('href="#settings-data"')).toBeLessThan(
      html.indexOf('href="#settings-account"'),
    );
    expect(html).not.toContain('href="#settings-privacy"');
  });
});
