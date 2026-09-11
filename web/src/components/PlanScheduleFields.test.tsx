import '../i18n';
// @vitest-environment jsdom
import { cleanup, fireEvent, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { PlanScheduleFields } from './PlanScheduleFields';

describe('PlanScheduleFields', () => {
  afterEach(() => {
    cleanup();
  });

  it('clearing time preserves the chosen day, while clearing the day clears and disables wall-clock fields', () => {
    const { container } = render(
      <form>
        <PlanScheduleFields
          idPrefix="plan-schedule-test"
          defaultDate="2026-09-05"
          defaultTime="10:00"
          defaultEnd="2026-09-05T11:00"
          includeEnd
        />
      </form>,
    );

    const dateInput = container.querySelector(
      '#plan-schedule-test-date',
    ) as HTMLInputElement;
    const timeInput = container.querySelector(
      '#plan-schedule-test-time',
    ) as HTMLInputElement;
    const endInput = container.querySelector(
      '#plan-schedule-test-end',
    ) as HTMLInputElement;

    expect(dateInput.value).toBe('2026-09-05');
    expect(timeInput.value).toBe('10:00');
    expect(endInput.value).toBe('2026-09-05T11:00');

    fireEvent.change(timeInput, { target: { value: '' } });

    expect(dateInput.value).toBe('2026-09-05');
    expect(timeInput.value).toBe('');
    expect(endInput.value).toBe('');
    expect(endInput.disabled).toBe(true);

    fireEvent.change(timeInput, { target: { value: '09:30' } });
    expect(timeInput.disabled).toBe(false);
    expect(endInput.disabled).toBe(false);

    fireEvent.change(dateInput, { target: { value: '' } });

    expect(dateInput.value).toBe('');
    expect(timeInput.value).toBe('');
    expect(timeInput.disabled).toBe(true);
    expect(endInput.value).toBe('');
    expect(endInput.disabled).toBe(true);
  });
});
