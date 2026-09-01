import { renderToStaticMarkup } from 'react-dom/server';
import {
  ServerAdminActivityPanel,
  ServerAdminSettingsPanel,
} from './ServerAdminPage';

describe('ServerAdmin controls', () => {
  it('shows stored and effective registration state separately', () => {
    const html = renderToStaticMarkup(
      <ServerAdminSettingsPanel
        settings={{
          effectiveRegistrationEnabled: false,
          maintenanceMode: true,
          registrationEnabled: true,
          version: 3,
        }}
        registrationPending={false}
        maintenancePending={false}
        mutationError={null}
        onRegistrationChange={() => undefined}
        onMaintenanceChange={() => undefined}
      />,
    );

    expect(html.match(/server-admin-setting-row/g)).toHaveLength(2);
    expect(html).toContain('server-admin-effective-state');
    expect(html.match(/aria-pressed="true"/g)).toHaveLength(2);
  });

  it('renders privacy-safe audit changes without exposing actor ids', () => {
    const actorId = '00000000-0000-0000-0000-000000000099';
    const html = renderToStaticMarkup(
      <ServerAdminActivityPanel
        activity={[
          {
            actorId,
            createdAt: new Date('2026-09-01T12:00:00Z'),
            id: '00000000-0000-0000-0000-000000000100',
            newValue: true,
            previousValue: false,
            setting: 'maintenance_mode',
          },
        ]}
      />,
    );

    expect(html).toContain('server-admin-table');
    expect(html.match(/<td>/g)).toHaveLength(3);
    expect(html).not.toContain(actorId);
  });
});
