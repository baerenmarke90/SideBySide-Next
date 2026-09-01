import {
  classifyRegistrationAvailability,
  loadRegistrationAvailability,
} from './instanceStatus';

describe('instance registration availability', () => {
  it('distinguishes available, administrator-disabled and maintenance states', () => {
    expect(
      classifyRegistrationAvailability({
        maintenanceMode: false,
        registrationAvailable: true,
        registrationUnavailableReason: null,
      }),
    ).toBe('available');
    expect(
      classifyRegistrationAvailability({
        maintenanceMode: false,
        registrationAvailable: false,
        registrationUnavailableReason: 'administrator',
      }),
    ).toBe('administrator');
    expect(
      classifyRegistrationAvailability({
        maintenanceMode: true,
        registrationAvailable: false,
        registrationUnavailableReason: 'maintenance',
      }),
    ).toBe('maintenance');
  });

  it('keeps connectivity failure distinct and fails closed for registration UI', async () => {
    await expect(
      loadRegistrationAvailability('https://sidebyside.invalid', async () => {
        throw new TypeError('network unavailable');
      }),
    ).resolves.toBe('unreachable');
  });
});
