import { type FormEvent, useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { RulesApi } from '../api/generated/apis/RulesApi';
import type { RulePreferenceUpdate } from '../api/generated/models/RulePreferenceUpdate';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';

export interface AnniversaryReminderSettingsProps {
  rulesApi: RulesApi;
  spaceId: string;
}

const RULE_KEY = 'relationship_anniversary_reminder';

const DAY_PRESETS = [
  { days: 30, labelKey: 'profileIdentity.anniversaryReminderDay30' as const },
  { days: 7, labelKey: 'profileIdentity.anniversaryReminderDay7' as const },
  { days: 1, labelKey: 'profileIdentity.anniversaryReminderDay1' as const },
];

export function AnniversaryReminderSettings({
  rulesApi,
  spaceId,
}: AnniversaryReminderSettingsProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const queryKey = ['rules', spaceId, RULE_KEY, 'preference'];

  const {
    data: preference,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: () => rulesApi.getRulePreference({ spaceId, ruleKey: RULE_KEY }),
  });

  const [enabled, setEnabled] = useState(true);
  const [daysBefore, setDaysBefore] = useState<number[]>([30, 7, 1]);
  const [localTime, setLocalTime] = useState('09:00');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (preference) {
      setEnabled(preference.enabled);
      setDaysBefore(preference.parameters.daysBefore ?? [30, 7, 1]);
      setLocalTime(preference.parameters.localTime?.slice(0, 5) ?? '09:00');
    }
  }, [preference]);

  const mutation = useMutation({
    mutationFn: (update: RulePreferenceUpdate) =>
      rulesApi.setRulePreference({
        spaceId,
        ruleKey: RULE_KEY,
        rulePreferenceUpdate: update,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, updated);
      setSaved(true);
    },
  });

  if (isLoading) {
    return (
      <p className="form-hint">
        {t('profileIdentity.anniversaryReminderLoading')}
      </p>
    );
  }

  if (error) {
    return <ProblemState error={error} onRetry={() => void refetch()} />;
  }

  const initialEnabled = preference?.enabled ?? true;
  const initialDaysBefore = preference?.parameters.daysBefore ?? [30, 7, 1];
  const initialLocalTime =
    preference?.parameters.localTime?.slice(0, 5) ?? '09:00';

  const isDaysDirty =
    daysBefore.length !== initialDaysBefore.length ||
    daysBefore.some((d) => !initialDaysBefore.includes(d));
  const isDirty =
    enabled !== initialEnabled || localTime !== initialLocalTime || isDaysDirty;

  function toggleDay(day: number) {
    setDaysBefore((current) => {
      if (current.includes(day)) {
        return current.filter((d) => d !== day);
      }
      return [...current, day].sort((a, b) => b - a);
    });
    setSaved(false);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isDirty || mutation.isPending) return;
    mutation.mutate({
      enabled,
      parameters: {
        daysBefore: [...daysBefore].sort((a, b) => b - a),
        localTime: localTime ? `${localTime}:00` : null,
      },
    });
  }

  return (
    <form className="anniversary-reminder-form" onSubmit={handleSubmit}>
      <label
        htmlFor="anniversary-reminder-enabled"
        className="form-checkbox-label"
      >
        <input
          id="anniversary-reminder-enabled"
          name="anniversaryReminderEnabled"
          type="checkbox"
          checked={enabled}
          onChange={(e) => {
            setEnabled(e.target.checked);
            setSaved(false);
          }}
        />
        <span>
          <strong>{t('profileIdentity.anniversaryReminderToggle')}</strong>
          <small>{t('profileIdentity.anniversaryReminderToggleHelp')}</small>
        </span>
      </label>

      {enabled ? (
        <div className="anniversary-reminder-config">
          <fieldset className="field-group">
            <legend>
              {t('profileIdentity.anniversaryReminderDaysHeading')}
            </legend>
            <div className="anniversary-reminder-days">
              {DAY_PRESETS.map((preset) => {
                const isChecked = daysBefore.includes(preset.days);
                return (
                  <label
                    key={preset.days}
                    className="anniversary-reminder-day-option"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleDay(preset.days)}
                    />
                    <span>{t(preset.labelKey)}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div className="field-group">
            <label htmlFor="anniversary-reminder-time">
              {t('profileIdentity.anniversaryReminderTimeLabel')}
            </label>
            <input
              id="anniversary-reminder-time"
              name="anniversaryReminderTime"
              type="time"
              value={localTime}
              onChange={(e) => {
                setLocalTime(e.target.value);
                setSaved(false);
              }}
            />
          </div>
        </div>
      ) : null}

      <div className="form-actions">
        <button type="submit" disabled={!isDirty || mutation.isPending}>
          {mutation.isPending
            ? t('profileIdentity.anniversaryReminderSaving')
            : t('profileIdentity.anniversaryReminderSave')}
        </button>
        {saved && !isDirty ? (
          <span className="relationship-saved-feedback" role="status">
            {t('profileIdentity.anniversaryReminderSaved')}
          </span>
        ) : null}
      </div>

      {mutation.error ? <ProblemState error={mutation.error} /> : null}
    </form>
  );
}
