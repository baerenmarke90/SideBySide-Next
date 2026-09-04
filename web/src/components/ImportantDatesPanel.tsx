import {
  type ChangeEvent,
  type FormEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { DateRepeat } from '../api/generated/models/DateRepeat';
import type { ImportantDateView } from '../api/generated/models/ImportantDateView';
import { ImportantDateType } from '../api/generated/models/ImportantDateType';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import {
  EMPTY_IMPORTANT_DATE_DRAFT,
  type ImportantDateDraft,
  importantDateFieldsFromDraft,
} from '../client/importantDateDraft';
import { normalizeClientError } from '../client/problemDetails';
import { invalidateDashboard } from '../client/dashboardQueries';
import { useTranslation } from '../i18n';
import { AddIcon } from './DestinationIcon';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

const DATE_TYPES = Object.values(ImportantDateType);
const DATE_REPEATS = Object.values(DateRepeat);
const VISIBILITIES = Object.values(ContentVisibility);

function dateInputValue(value: Date | null | undefined): string {
  if (!value) return '';
  return value.toISOString().slice(0, 10);
}

function ImportantDateModalDialog({
  date,
  people,
  pending,
  error,
  deletePending,
  deleteError,
  onClose,
  onSubmit,
  onDelete,
}: {
  date: ImportantDateView | null;
  people: RelatedPersonView[];
  pending: boolean;
  error: unknown;
  deletePending: boolean;
  deleteError: unknown;
  onClose: () => void;
  onSubmit: (draft: ImportantDateDraft) => void;
  onDelete: (target: ImportantDateView) => void;
}) {
  const { t } = useTranslation();
  const backdropRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const initialInputRef = useRef<HTMLInputElement>(null);

  const initialDraft = useMemo<ImportantDateDraft>(() => {
    if (!date) return EMPTY_IMPORTANT_DATE_DRAFT;
    return {
      date: dateInputValue(date.date),
      label: date.label,
      relatedPersonId: date.relatedPersonId ?? '',
      repeats: date.repeats,
      type: date.type,
      visibility: date.visibility,
    };
  }, [date]);

  const [label, setLabel] = useState(initialDraft.label);
  const [dateVal, setDateVal] = useState(initialDraft.date);
  const [type, setType] = useState<ImportantDateDraft['type']>(
    initialDraft.type,
  );
  const [repeats, setRepeats] = useState<ImportantDateDraft['repeats']>(
    initialDraft.repeats,
  );
  const [relatedPersonId, setRelatedPersonId] = useState(
    initialDraft.relatedPersonId,
  );
  const [visibility, setVisibility] = useState<
    ImportantDateDraft['visibility']
  >(initialDraft.visibility);

  const [showDiscardConfirm, setShowDiscardConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isDirty = useMemo(() => {
    return (
      label !== initialDraft.label ||
      dateVal !== initialDraft.date ||
      type !== initialDraft.type ||
      repeats !== initialDraft.repeats ||
      relatedPersonId !== initialDraft.relatedPersonId ||
      visibility !== initialDraft.visibility
    );
  }, [
    label,
    dateVal,
    type,
    repeats,
    relatedPersonId,
    visibility,
    initialDraft,
  ]);

  const handleCloseAttempt = useCallback(() => {
    if (pending || deletePending) return;
    if (isDirty) {
      setShowDiscardConfirm(true);
    } else {
      onClose();
    }
  }, [pending, deletePending, isDirty, onClose]);

  useEffect(() => {
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    initialInputRef.current?.focus();
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalOverflow;
      previousFocus?.focus();
    };
  }, []);

  useEffect(() => {
    const backdropEl = backdropRef.current;
    if (!backdropEl) return;
    function handleBackdropClick(e: MouseEvent) {
      if (e.target === backdropEl && !pending && !deletePending) {
        handleCloseAttempt();
      }
    }
    backdropEl.addEventListener('click', handleBackdropClick);
    return () => backdropEl.removeEventListener('click', handleBackdropClick);
  }, [pending, deletePending, handleCloseAttempt]);

  function handleDialogKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !pending && !deletePending) {
      event.preventDefault();
      if (showDeleteConfirm) {
        setShowDeleteConfirm(false);
      } else if (showDiscardConfirm) {
        setShowDiscardConfirm(false);
      } else {
        handleCloseAttempt();
      }
      return;
    }
    if (event.key !== 'Tab' || !dialogRef.current) return;

    const focusable = Array.from(
      dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      ),
    );
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({
      date: dateVal,
      label,
      relatedPersonId,
      repeats,
      type,
      visibility,
    });
  }

  return (
    <div ref={backdropRef} className="modal-backdrop" role="presentation">
      <section
        ref={dialogRef}
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="important-date-modal-title"
        onKeyDown={handleDialogKeyDown}
      >
        <div className="people-modal-header">
          <h2 id="important-date-modal-title">
            {date
              ? t('importantDates.editTitle')
              : t('importantDates.createTitle')}
          </h2>
          <button
            type="button"
            className="people-modal-close"
            onClick={handleCloseAttempt}
            aria-label={t('importantDates.closeDialogAria')}
            disabled={pending || deletePending}
          >
            ✕
          </button>
        </div>

        {showDeleteConfirm && date ? (
          <div className="inline-message inline-message-danger" role="alert">
            <strong>{t('importantDates.deleteQuestion')}</strong>
            <span>{t('importantDates.deleteBody')}</span>
            {deleteError ? <ProblemState error={deleteError} /> : null}
            <div className="form-actions choice-row">
              <button
                type="button"
                className="secondary compact-action"
                disabled={deletePending}
                onClick={() => setShowDeleteConfirm(false)}
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                className="danger compact-action"
                disabled={deletePending}
                onClick={() => onDelete(date)}
              >
                {deletePending
                  ? t('importantDates.deleting')
                  : t('importantDates.deleteConfirm')}
              </button>
            </div>
          </div>
        ) : null}

        {showDiscardConfirm ? (
          <div className="inline-message inline-message-danger" role="alert">
            <strong>{t('importantDates.discardTitle')}</strong>
            <span>{t('importantDates.discardBody')}</span>
            <div className="form-actions choice-row">
              <button
                type="button"
                className="secondary compact-action"
                onClick={() => setShowDiscardConfirm(false)}
              >
                {t('importantDates.keepEditing')}
              </button>
              <button
                type="button"
                className="danger compact-action"
                onClick={onClose}
              >
                {t('importantDates.discardConfirm')}
              </button>
            </div>
          </div>
        ) : null}

        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="important-date-label">
              {t('importantDates.labelLabel')}
            </label>
            <input
              ref={initialInputRef}
              id="important-date-label"
              name="label"
              required
              maxLength={160}
              value={label}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setLabel(e.target.value)
              }
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
              value={dateVal}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setDateVal(e.target.value)
              }
            />
          </div>

          <div className="field-group">
            <label htmlFor="important-date-type">
              {t('importantDates.typeLabel')}
            </label>
            <select
              id="important-date-type"
              name="type"
              value={type}
              onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                setType(e.target.value as ImportantDateDraft['type'])
              }
            >
              {DATE_TYPES.map((tVal) => (
                <option key={tVal} value={tVal}>
                  {t(`importantDates.type.${tVal}`)}
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
              value={repeats}
              onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                setRepeats(e.target.value as ImportantDateDraft['repeats'])
              }
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
              value={relatedPersonId}
              onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                setRelatedPersonId(e.target.value)
              }
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
              value={visibility}
              onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                setVisibility(
                  e.target.value as ImportantDateDraft['visibility'],
                )
              }
            >
              {VISIBILITIES.map((vVal) => (
                <option key={vVal} value={vVal}>
                  {t(`importantDates.visibility.${vVal}`)}
                </option>
              ))}
            </select>
            <p className="field-help">{t('importantDates.visibilityHelp')}</p>
          </div>

          {error ? <ProblemState error={error} /> : null}

          <div className="important-dates-modal-actions">
            {date ? (
              <button
                type="button"
                className="danger"
                disabled={pending || deletePending}
                onClick={() => setShowDeleteConfirm(true)}
              >
                {t('importantDates.delete')}
              </button>
            ) : (
              <div />
            )}
            <div className="form-actions-end">
              <button
                type="button"
                className="secondary"
                disabled={pending || deletePending}
                onClick={handleCloseAttempt}
              >
                {t('common.cancel')}
              </button>
              <button type="submit" disabled={pending || deletePending}>
                {pending
                  ? t('importantDates.saving')
                  : date
                    ? t('importantDates.saveChanges')
                    : t('importantDates.create')}
              </button>
            </div>
          </div>
        </form>
      </section>
    </div>
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
  const [isCreating, setIsCreating] = useState(false);
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
      setIsCreating(false);
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
      setEditing(null);
      setIsCreating(false);
      setSavedMessage(t('importantDates.deleted'));
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['important-dates', spaceId],
        }),
        invalidateDashboard(queryClient, spaceId),
      ]);
    },
  });

  const isModalOpen = isCreating || Boolean(editing);

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
          className="primary compact-action"
          onClick={() => {
            setEditing(null);
            setIsCreating(true);
            saveMutation.reset();
            deleteMutation.reset();
            setSavedMessage(null);
          }}
        >
          <AddIcon />
          <span>{t('importantDates.create')}</span>
        </button>
      </div>

      {savedMessage ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{savedMessage}</span>
        </div>
      ) : null}

      {isModalOpen ? (
        <ImportantDateModalDialog
          date={editing}
          people={people}
          pending={saveMutation.isPending}
          error={saveMutation.error}
          deletePending={deleteMutation.isPending}
          deleteError={deleteMutation.error}
          onClose={() => {
            setEditing(null);
            setIsCreating(false);
            saveMutation.reset();
            deleteMutation.reset();
          }}
          onSubmit={(draft) => {
            setSavedMessage(null);
            saveMutation.mutate(draft);
          }}
          onDelete={(target) => {
            setSavedMessage(null);
            deleteMutation.mutate(target);
          }}
        />
      ) : null}

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
          <ul className="important-dates-list">
            {datesQuery.data.map((date) => {
              const linkedPersonName = date.relatedPersonId
                ? personNames.get(date.relatedPersonId)
                : undefined;
              return (
                <li key={date.id} className="important-date-item">
                  <button
                    type="button"
                    className="important-date-card"
                    onClick={() => {
                      setEditing(date);
                      setIsCreating(false);
                      saveMutation.reset();
                      deleteMutation.reset();
                      setSavedMessage(null);
                    }}
                    aria-label={`${date.label} – ${t('importantDates.edit')}`}
                  >
                    <div className="important-date-card-header">
                      <div className="important-date-title-group">
                        <h4 className="important-date-title">{date.label}</h4>
                        {linkedPersonName ? (
                          <span className="important-date-person">
                            {t('importantDates.linkedPerson', {
                              name: linkedPersonName,
                            })}
                          </span>
                        ) : null}
                      </div>
                      <span className="important-date-date">
                        {dateFormatter.format(date.date)}
                      </span>
                    </div>
                    <div className="important-date-chips">
                      <span className="important-date-chip">
                        {t(`importantDates.type.${date.type}`)}
                      </span>
                      <span className="important-date-chip">
                        {t(`importantDates.repeats.${date.repeats}`)}
                      </span>
                      <span
                        className={`important-date-chip ${
                          date.visibility === ContentVisibility.PRIVATE
                            ? 'important-date-chip-private'
                            : 'important-date-chip-shared'
                        }`}
                      >
                        {t(`importantDates.visibility.${date.visibility}`)}
                      </span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        ) : null}
      </section>
    </section>
  );
}
