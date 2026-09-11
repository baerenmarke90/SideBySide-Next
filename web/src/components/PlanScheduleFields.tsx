import { useEffect, useId, useRef, useState } from 'react';
import { useTranslation } from '../i18n';

/**
 * Product-level Plan scheduling controls shared by create, Wish conversion and
 * lifecycle correction. Date is optional; time only exists in the context of
 * a date. Clearing a date also clears all wall-clock state, while clearing time
 * deliberately preserves the selected calendar day.
 */
export function PlanScheduleFields({
  idPrefix,
  defaultDate = '',
  defaultTime = '',
  defaultEnd = '',
  includeEnd = false,
}: {
  idPrefix: string;
  defaultDate?: string;
  defaultTime?: string;
  defaultEnd?: string;
  includeEnd?: boolean;
}) {
  const { t } = useTranslation();
  const hintId = useId();
  const dateRef = useRef<HTMLInputElement>(null);
  const [date, setDate] = useState(defaultDate);
  const [time, setTime] = useState(defaultDate ? defaultTime : '');
  const [end, setEnd] = useState(defaultDate && defaultTime ? defaultEnd : '');

  useEffect(() => {
    const form = dateRef.current?.form;
    if (!form) return;
    const reset = () => {
      setDate(defaultDate);
      setTime(defaultDate ? defaultTime : '');
      setEnd(defaultDate && defaultTime ? defaultEnd : '');
    };
    form.addEventListener('reset', reset);
    return () => form.removeEventListener('reset', reset);
  }, [defaultDate, defaultEnd, defaultTime]);

  return (
    <>
      <label htmlFor={`${idPrefix}-date`}>{t('m5s3.plan.plannedDate')}</label>
      <input
        ref={dateRef}
        id={`${idPrefix}-date`}
        name="plannedDate"
        type="date"
        value={date}
        onChange={(event) => {
          const nextDate = event.target.value;
          setDate(nextDate);
          if (!nextDate) {
            setTime('');
            setEnd('');
          }
        }}
      />

      <label htmlFor={`${idPrefix}-time`}>{t('m5s3.plan.plannedTime')}</label>
      <input
        id={`${idPrefix}-time`}
        name="plannedTime"
        type="time"
        value={time}
        disabled={!date}
        aria-describedby={hintId}
        onChange={(event) => {
          const nextTime = event.target.value;
          setTime(nextTime);
          if (!nextTime) setEnd('');
        }}
      />
      <small id={hintId} className="field-help">
        {t('m5s3.plan.plannedTimeHint')}
      </small>

      {includeEnd ? (
        <>
          <label htmlFor={`${idPrefix}-end`}>{t('m5s3.plan.plannedEnd')}</label>
          <input
            id={`${idPrefix}-end`}
            name="plannedEnd"
            type="datetime-local"
            value={end}
            disabled={!date || !time}
            onChange={(event) => setEnd(event.target.value)}
          />
        </>
      ) : null}
    </>
  );
}
