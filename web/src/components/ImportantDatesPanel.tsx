import { type FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { DateRepeat } from '../api/generated/models/DateRepeat';
import type { ImportantDateView } from '../api/generated/models/ImportantDateView';
import { ImportantDateType } from '../api/generated/models/ImportantDateType';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import {
  type ImportantDateDraft,
  importantDateFieldsFromDraft,
} from '../client/importantDateDraft';
import { normalizeClientError } from '../client/problemDetails';
import { invalidateDashboard } from '../client/dashboardQueries';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

const DATE_TYPES = Object.values(ImportantDateType);
const DATE_REPEATS = Object.values(DateRepeat);
const VISIBILITIES = Object.values(ContentVisibility);

function dateInputValue(value: Date | null | undefined): string {
  if (!value) return '';
  return value.toISOString().slice(0, 10);
}

function draftFromForm(form: FormData): ImportantDateDraft {
  return {
    date: String(form.get('date') || ''),
    label: String(form.get('label') || ''),
    relatedPersonId: String(form.get('relatedPersonId') || ''),
    repeats: String(form.get('repeats')) as ImportantDateDraft['repeats'],
    type: String(form.get('type')) as ImportantDateDraft['type'],
    visibility: String(
      form.get('visibility'),
    ) as ImportantDateDraft['visibility'],
  };
}

function ImportantDateForm({
  date,
  people,
  pending,
  onCancel,
  onSubmit,
}: {
  date: ImportantDateView | null;
  people: RelatedPersonView[];
  pending: boolean;
  onCancel: () => void;
  onSubmit: (draft: ImportantDateDraft) => void;
}) {
  const { t } = useTranslation();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(draftFromForm(new FormData(event.currentTarget)));
  }

  return (
    <form
      key={date?.id ?? 'new'}
      className="form-grid planning-create-form"
      onSubmit={submit}
    >
      <div className="field-group">
        <label htmlFor="important-date-label">
          {t('importantDates.labelLabel')}
        </label>
        <input
          id="important-date-label"
          name="label"
          required
          maxLength={160}
          defaultValue={date?.label ?? ''}
        />
      </div>

      <div className="field-group">
        <label htmlFor="important-date-date">
          {t('importantDates.dateLabel')}
        </label>
        <input
          id="important-date-date"
          name="date"
          type="date"
          required
          defaultValue={dateInputValue(date?.date)}
        />
      </div>

      <div className="field-group">
        <label htmlFor="important-date-type">
          {t('importantDates.typeLabel')}
        </label>
        <select
          id="important-date-type"
          name="type"
          defaultValue={date?.type ?? ImportantDateType.CUSTOM}
        >
          {DATE_TYPES.map((type) => (
            <option key={type} value={type}>
              {t(`importantDates.type.${type}`)}
            </option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label htmlFor="important-date-repeat">
          {t('importantDates.repeatLabel')}
        </label>
        <select
          id="important-date-repeat"
          name="repeats"
          defaultValue={date?.repeats ?? DateRepeat.ANNUALLY}
        >
          {DATE_REPEATS.map((repeat) => (
            <option key={repeat} value={repeat}>
              {t(`importantDates.repeats.${repeat}`)}
            </option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label htmlFor="important-date-person">
          {t('importantDates.personLabel')}
        </label>
        <select
          id="important-date-person"
          name="relatedPersonId"
          defaultValue={date?.relatedPersonId ?? ''}
        >
          <option value="">{t('importantDates.personNone')}</option>
          {people.map((person) => (
            <option key={person.id} value={person.id}>
              {person.displayName}
            </option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label htmlFor="important-date-visibility">
          {t('importantDates.visibilityLabel')}
        </label>
        <select
          id="important-date-visibility"
          name="visibility"
          defaultValue={date?.visibility ?? ContentVisibility.SHARED}
        >
          {VISIBILITIES.map((visibility) => (
            <option key={visibility} value={visibility}>
              {t(`importantDates.visibility.${visibility}`)}
            </option>
          ))}
        </select>
        <p className="field-help">{t('importantDates.visibilityHelp')}</p>
      </div>

      <div className="form-actions">
        {date ? (
          <button type="button" className="secondary" onClick={onCancel}>
            {t('common.cancel')}
          </button>
        ) : null}
        <button type="submit" disabled={pending}>
          {pending
            ? t('importantDates.saving')
            : date
              ? t('importantDates.saveChanges')
              : t('importantDates.create')}
        </button>
      </div>
    </form>
  );
}

export function ImportantDatesPanel({
  peopleApi,
  spaceId,
  people,
}: {
  peopleApi: PeopleApi;
  spaceId: string;
  people: RelatedPersonView[];
}) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<ImportantDateView | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ImportantDateView | null>(
    null,
  );
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const dateFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(i18n.language, {
        dateStyle: 'long',
        timeZone: 'UTC',
      }),
    [i18n.language],
  );
  const personNames = useMemo(
    () => new Map(people.map((person) => [person.id, person.displayName])),
    [people],
  );

  const datesQuery = useQuery({
    queryKey: ['important-dates', spaceId],
    queryFn: async () => {
      try {
        return await peopleApi.listImportantDatesApiV1SpacesSpaceIdImportantDatesGet(
          { spaceId },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const saveMutation = useMutation({
    mutationFn: async (draft: ImportantDateDraft) => {
      const importantDateFields = importantDateFieldsFromDraft(draft);
      try {
        if (editing) {
          return await peopleApi.updateImportantDateApiV1SpacesSpaceIdImportantDatesDateIdPut(
            {
              dateId: editing.id,
              spaceId,
              ifMatch: String(editing.version),
              importantDateFields,
            },
          );
        }
        return await peopleApi.createImportantDateApiV1SpacesSpaceIdImportantDatesPost(
          {
            spaceId,
            importantDateFields,
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setSavedMessage(
        editing ? t('importantDates.updated') : t('importantDates.created'),
      );
      setEditing(null);
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['important-dates', spaceId],
        }),
        invalidateDashboard(queryClient, spaceId),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (target: ImportantDateView) => {
      try {
        await peopleApi.deleteImportantDateApiV1SpacesSpaceIdImportantDatesDateIdDelete(
          {
            dateId: target.id,
            spaceId,
            ifMatch: String(target.version),
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setDeleteTarget(null);
      setSavedMessage(t('importantDates.deleted'));
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['important-dates', spaceId],
        }),
        invalidateDashboard(queryClient, spaceId),
      ]);
    },
  });

  return (
    <section
      className="important-dates-section"
      aria-labelledby="important-dates-title"
    >
      <div className="section-head">
        <div>
          <h2 id="important-dates-title">{t('importantDates.heading')}</h2>
          <p className="important-dates-intro">{t('importantDates.intro')}</p>
        </div>
        <button
          type="button"
          className="secondary compact-action"
          onClick={() => void datesQuery.refetch()}
          disabled={datesQuery.isFetching}
        >
          {datesQuery.isFetching ? t('common.refreshing') : t('common.refresh')}
        </button>
      </div>

      {savedMessage ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{savedMessage}</span>
        </div>
      ) : null}

      <details
        className="planning-create important-dates-create"
        key={editing?.id ?? 'new'}
        open={Boolean(editing)}
      >
        <summary>
          {editing
            ? t('importantDates.editTitle')
            : t('importantDates.createTitle')}
        </summary>
        <ImportantDateForm
          date={editing}
          people={people}
          pending={saveMutation.isPending}
          onCancel={() => {
            setEditing(null);
            saveMutation.reset();
          }}
          onSubmit={(draft) => {
            setSavedMessage(null);
            saveMutation.mutate(draft);
          }}
        />
        {saveMutation.error ? (
          <ProblemState
            error={saveMutation.error}
            onRetry={() => {
              saveMutation.reset();
              void datesQuery.refetch();
            }}
          />
        ) : null}
      </details>

      <section aria-labelledby="important-dates-list-title">
        <div className="layout-section-head">
          <h3 id="important-dates-list-title">
            {t('importantDates.listTitle')}
          </h3>
        </div>

        {datesQuery.isLoading ? (
          <UiState kind="loading" title={t('importantDates.loading')} />
        ) : null}
        {datesQuery.error ? (
          <ProblemState
            error={datesQuery.error}
            onRetry={() => void datesQuery.refetch()}
          />
        ) : null}
        {datesQuery.data?.length === 0 ? (
          <UiState
            kind="empty"
            title={t('importantDates.emptyTitle')}
            body={t('importantDates.emptyBody')}
          />
        ) : null}
        {datesQuery.data?.length ? (
          <ul className="story-list">
            {datesQuery.data.map((date) => {
              const linkedPersonName = date.relatedPersonId
                ? personNames.get(date.relatedPersonId)
                : undefined;
              const confirmingDelete = deleteTarget?.id === date.id;
              return (
                <li key={date.id} className="story-card">
                  <div className="section-head">
                    <div>
                      <h4>{date.label}</h4>
                      <p>
                        {t('importantDates.dateValue', {
                          date: dateFormatter.format(date.date),
                        })}{' '}
                        · {t(`importantDates.type.${date.type}`)} ·{' '}
                        {t(`importantDates.repeats.${date.repeats}`)} ·{' '}
                        {t(`importantDates.visibility.${date.visibility}`)}
                      </p>
                      {linkedPersonName ? (
                        <p>
                          {t('importantDates.linkedPerson', {
                            name: linkedPersonName,
                          })}
                        </p>
                      ) : null}
                    </div>
                    {!confirmingDelete ? (
                      <div className="form-actions">
                        <button
                          type="button"
                          className="secondary compact-action"
                          onClick={() => {
                            setEditing(date);
                            saveMutation.reset();
                            setSavedMessage(null);
                          }}
                        >
                          {t('importantDates.edit')}
                        </button>
                        <button
                          type="button"
                          className="tertiary compact-action"
                          aria-expanded="false"
                          onClick={() => {
                            setDeleteTarget(date);
                            deleteMutation.reset();
                          }}
                        >
                          {t('importantDates.delete')}
                        </button>
                      </div>
                    ) : null}
                  </div>

                  {confirmingDelete ? (
                    <div className="inline-delete-confirmation" role="alert">
                      <strong>{t('importantDates.deleteQuestion')}</strong>
                      <span>{t('importantDates.deleteBody')}</span>
                      {deleteMutation.error ? (
                        <ProblemState error={deleteMutation.error} />
                      ) : null}
                      <div className="form-actions">
                        <button
                          type="button"
                          className="secondary compact-action"
                          disabled={deleteMutation.isPending}
                          onClick={() => {
                            setDeleteTarget(null);
                            deleteMutation.reset();
                          }}
                        >
                          {t('common.cancel')}
                        </button>
                        <button
                          type="button"
                          className="danger compact-action"
                          disabled={deleteMutation.isPending}
                          onClick={() => deleteMutation.mutate(date)}
                        >
                          {deleteMutation.isPending
                            ? t('importantDates.deleting')
                            : t('importantDates.deleteConfirm')}
                        </button>
                      </div>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        ) : null}
      </section>
    </section>
  );
}
