import {
  type FormEvent,
  type KeyboardEvent,
  type RefObject,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { PersonRelationship } from '../api/generated/models/PersonRelationship';
import { RelatedPersonDeletePolicy } from '../api/generated/models/RelatedPersonDeletePolicy';
import type { RelatedPersonFields } from '../api/generated/models/RelatedPersonFields';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import {
  birthdayFromInput,
  birthdayInputParts,
  daysInMonth,
} from '../client/relatedPersonBirthday';
import {
  canConfirmRelatedPersonDelete,
  INITIAL_RELATED_PERSON_DELETE_CHOICE,
  type RelatedPersonDeleteChoice,
  type RelatedPersonDeletePolicyValue,
  relatedPersonDeleteReducer,
} from '../client/relatedPersonDelete';
import { normalizeClientError } from '../client/problemDetails';
import { useTranslation } from '../i18n';
import { ImportantDatesPanel } from './ImportantDatesPanel';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

const RELATIONSHIPS = Object.values(PersonRelationship);
const VISIBILITIES = Object.values(ContentVisibility);

function dateInputValue(value: Date | null): string {
  if (!value) return '';
  return value.toISOString().slice(0, 10);
}

function personFields(form: FormData): RelatedPersonFields {
  const birthdayYearKnown = form.get('birthdayYearKnown') === 'on';
  const birthday = birthdayFromInput({
    yearKnown: birthdayYearKnown,
    dateValue: String(form.get('birthday') || ''),
    monthValue: String(form.get('birthdayMonth') || ''),
    dayValue: String(form.get('birthdayDay') || ''),
  });
  return {
    displayName: String(form.get('displayName') || '').trim(),
    relationship: String(
      form.get('relationship'),
    ) as RelatedPersonFields['relationship'],
    visibility: String(
      form.get('visibility'),
    ) as RelatedPersonFields['visibility'],
    birthday,
    birthdayYearKnown: Boolean(birthday && birthdayYearKnown),
  };
}

function RelatedPersonForm({
  person,
  pending,
  onCancel,
  onSubmit,
}: {
  person: RelatedPersonView | null;
  pending: boolean;
  onCancel: () => void;
  onSubmit: (fields: RelatedPersonFields) => void;
}) {
  const { t, i18n } = useTranslation();
  const initialBirthdayParts = birthdayInputParts(person?.birthday ?? null);
  const [birthdayYearKnown, setBirthdayYearKnown] = useState(
    person?.birthday ? person.birthdayYearKnown : true,
  );
  const [knownBirthday, setKnownBirthday] = useState(
    person?.birthday && person.birthdayYearKnown
      ? dateInputValue(person.birthday)
      : '',
  );
  const [birthdayMonth, setBirthdayMonth] = useState(
    initialBirthdayParts.monthValue,
  );
  const [birthdayDay, setBirthdayDay] = useState(initialBirthdayParts.dayValue);
  const monthOptions = useMemo(
    () =>
      Array.from({ length: 12 }, (_, index) => ({
        value: String(index + 1),
        label: new Intl.DateTimeFormat(i18n.language, {
          month: 'long',
          timeZone: 'UTC',
        }).format(new Date(Date.UTC(2000, index, 1))),
      })),
    [i18n.language],
  );
  const birthdayPartRequired = Boolean(birthdayMonth || birthdayDay);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(personFields(new FormData(event.currentTarget)));
  }

  return (
    <section className="form-card" aria-labelledby="related-person-form-title">
      <h2 id="related-person-form-title">
        {person ? t('people.editTitle') : t('people.createTitle')}
      </h2>
      <form key={person?.id ?? 'new'} className="form-grid" onSubmit={submit}>
        <div className="field-group">
          <label htmlFor="related-person-name">{t('people.nameLabel')}</label>
          <input
            id="related-person-name"
            name="displayName"
            required
            maxLength={120}
            defaultValue={person?.displayName ?? ''}
            autoComplete="off"
          />
        </div>

        <div className="field-group">
          <label htmlFor="related-person-relationship">
            {t('people.relationshipLabel')}
          </label>
          <select
            id="related-person-relationship"
            name="relationship"
            defaultValue={person?.relationship ?? PersonRelationship.OTHER}
          >
            {RELATIONSHIPS.map((relationship) => (
              <option key={relationship} value={relationship}>
                {t(`people.relationship.${relationship}`)}
              </option>
            ))}
          </select>
        </div>

        <div className="field-group">
          <span>{t('people.birthdayLabel')}</span>
          <label
            className="choice-row"
            htmlFor="related-person-birthday-year-known"
          >
            <input
              id="related-person-birthday-year-known"
              name="birthdayYearKnown"
              type="checkbox"
              checked={birthdayYearKnown}
              onChange={(event) => {
                const nextYearKnown = event.currentTarget.checked;
                if (!nextYearKnown && knownBirthday) {
                  const knownDate = new Date(`${knownBirthday}T00:00:00.000Z`);
                  setBirthdayMonth(String(knownDate.getUTCMonth() + 1));
                  setBirthdayDay(String(knownDate.getUTCDate()));
                }
                setBirthdayYearKnown(nextYearKnown);
              }}
            />
            <span>{t('people.birthdayYearKnown')}</span>
          </label>

          {birthdayYearKnown ? (
            <input
              id="related-person-birthday"
              name="birthday"
              type="date"
              value={knownBirthday}
              onChange={(event) => setKnownBirthday(event.currentTarget.value)}
            />
          ) : (
            <>
              <div className="form-actions">
                <div className="field-group">
                  <label htmlFor="related-person-birthday-day">
                    {t('people.birthdayDayLabel')}
                  </label>
                  <input
                    id="related-person-birthday-day"
                    name="birthdayDay"
                    type="number"
                    inputMode="numeric"
                    min={1}
                    max={daysInMonth(Number(birthdayMonth))}
                    required={birthdayPartRequired}
                    value={birthdayDay}
                    onChange={(event) =>
                      setBirthdayDay(event.currentTarget.value)
                    }
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="related-person-birthday-month">
                    {t('people.birthdayMonthLabel')}
                  </label>
                  <select
                    id="related-person-birthday-month"
                    name="birthdayMonth"
                    required={birthdayPartRequired}
                    value={birthdayMonth}
                    onChange={(event) =>
                      setBirthdayMonth(event.currentTarget.value)
                    }
                  >
                    <option value="">
                      {t('people.birthdayMonthPlaceholder')}
                    </option>
                    {monthOptions.map((month) => (
                      <option key={month.value} value={month.value}>
                        {month.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="field-help">
                {t('people.birthdayUnknownYearHelp')}
              </p>
            </>
          )}
        </div>

        <div className="field-group">
          <label htmlFor="related-person-visibility">
            {t('people.visibilityLabel')}
          </label>
          <select
            id="related-person-visibility"
            name="visibility"
            defaultValue={person?.visibility ?? ContentVisibility.SHARED}
          >
            {VISIBILITIES.map((visibility) => (
              <option key={visibility} value={visibility}>
                {t(`people.visibility.${visibility}`)}
              </option>
            ))}
          </select>
          <p className="field-help">{t('people.visibilityHelp')}</p>
        </div>

        <div className="form-actions">
          {person ? (
            <button type="button" className="secondary" onClick={onCancel}>
              {t('common.cancel')}
            </button>
          ) : null}
          <button type="submit" disabled={pending}>
            {pending
              ? t('people.saving')
              : person
                ? t('people.saveChanges')
                : t('people.create')}
          </button>
        </div>
      </form>
    </section>
  );
}

export function DeleteRelatedPersonDialogContent({
  person,
  pending,
  error,
  choice,
  onSelectPolicy,
  onCascadeConfirmed,
  onCancel,
  onDelete,
  dialogRef,
  cancelButtonRef,
  onKeyDown,
}: {
  person: RelatedPersonView;
  pending: boolean;
  error: Error | null;
  choice: RelatedPersonDeleteChoice;
  onSelectPolicy: (policy: RelatedPersonDeletePolicyValue) => void;
  onCascadeConfirmed: (confirmed: boolean) => void;
  onCancel: () => void;
  onDelete: (policy: RelatedPersonDeletePolicyValue) => void;
  dialogRef?: RefObject<HTMLElement | null>;
  cancelButtonRef?: RefObject<HTMLButtonElement | null>;
  onKeyDown?: (event: KeyboardEvent<HTMLElement>) => void;
}) {
  const { t } = useTranslation();
  const canDelete = canConfirmRelatedPersonDelete(choice);

  return (
    <section
      ref={dialogRef}
      className="modal-card"
      role="dialog"
      aria-modal="true"
      aria-labelledby="related-person-delete-title"
      aria-describedby="related-person-delete-description related-person-delete-privacy"
      onKeyDown={onKeyDown}
    >
      <h2 id="related-person-delete-title">{t('people.deleteTitle')}</h2>
      <p id="related-person-delete-description">
        {t('people.deleteBody', { name: person.displayName })}
      </p>
      <p id="related-person-delete-privacy" className="field-help">
        {t('people.deletePrivacyNote')}
      </p>

      <fieldset className="form-grid">
        <legend>{t('people.deletePolicyLegend')}</legend>
        <label className="choice-card">
          <input
            type="radio"
            name="deletePolicy"
            value={RelatedPersonDeletePolicy.preserve}
            checked={choice.policy === RelatedPersonDeletePolicy.preserve}
            onChange={() => onSelectPolicy(RelatedPersonDeletePolicy.preserve)}
          />
          <span>
            <strong>{t('people.deletePreserveTitle')}</strong>
            <small>{t('people.deletePreserveBody')}</small>
          </span>
        </label>
        <label className="choice-card choice-card-danger">
          <input
            type="radio"
            name="deletePolicy"
            value={RelatedPersonDeletePolicy.cascade}
            checked={choice.policy === RelatedPersonDeletePolicy.cascade}
            onChange={() => onSelectPolicy(RelatedPersonDeletePolicy.cascade)}
          />
          <span>
            <strong>{t('people.deleteCascadeTitle')}</strong>
            <small>{t('people.deleteCascadeBody')}</small>
          </span>
        </label>
      </fieldset>

      {choice.policy === RelatedPersonDeletePolicy.cascade ? (
        <div className="inline-message inline-message-danger" role="alert">
          <strong>{t('people.deleteCascadeWarningTitle')}</strong>
          <span>{t('people.deleteCascadeWarningBody')}</span>
          <label className="choice-row">
            <input
              type="checkbox"
              checked={choice.cascadeConfirmed}
              onChange={(event) =>
                onCascadeConfirmed(event.currentTarget.checked)
              }
            />
            <span>{t('people.deleteCascadeConfirm')}</span>
          </label>
        </div>
      ) : null}

      {error ? <ProblemState error={error} /> : null}

      <div className="form-actions">
        <button
          ref={cancelButtonRef}
          type="button"
          className="secondary"
          onClick={onCancel}
          disabled={pending}
        >
          {t('common.cancel')}
        </button>
        <button
          type="button"
          className={
            choice.policy === RelatedPersonDeletePolicy.cascade
              ? 'danger'
              : undefined
          }
          disabled={!canDelete || pending}
          onClick={() => {
            if (choice.policy && canDelete) onDelete(choice.policy);
          }}
        >
          {pending ? t('people.deleting') : t('people.deleteConfirm')}
        </button>
      </div>
    </section>
  );
}

function DeleteRelatedPersonDialog({
  person,
  pending,
  error,
  onCancel,
  onDelete,
}: {
  person: RelatedPersonView;
  pending: boolean;
  error: Error | null;
  onCancel: () => void;
  onDelete: (policy: RelatedPersonDeletePolicyValue) => void;
}) {
  const [choice, dispatch] = useReducer(
    relatedPersonDeleteReducer,
    INITIAL_RELATED_PERSON_DELETE_CHOICE,
  );
  const dialogRef = useRef<HTMLElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    cancelButtonRef.current?.focus();
    return () => previousFocus?.focus();
  }, []);

  function handleDialogKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !pending) {
      event.preventDefault();
      onCancel();
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

  return (
    <div className="modal-backdrop" role="presentation">
      <DeleteRelatedPersonDialogContent
        person={person}
        pending={pending}
        error={error}
        choice={choice}
        onSelectPolicy={(policy) => dispatch({ type: 'select', policy })}
        onCascadeConfirmed={(confirmed) =>
          dispatch({ type: 'confirmCascade', confirmed })
        }
        onCancel={onCancel}
        onDelete={onDelete}
        dialogRef={dialogRef}
        cancelButtonRef={cancelButtonRef}
        onKeyDown={handleDialogKeyDown}
      />
    </div>
  );
}

export function RelatedPeoplePage({
  peopleApi,
  spaceId,
}: {
  peopleApi: PeopleApi;
  spaceId: string;
}) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<RelatedPersonView | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<RelatedPersonView | null>(
    null,
  );
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const birthdayFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(i18n.language, {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
        timeZone: 'UTC',
      }),
    [i18n.language],
  );
  const birthdayWithoutYearFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(i18n.language, {
        day: '2-digit',
        month: 'long',
        timeZone: 'UTC',
      }),
    [i18n.language],
  );

  const peopleQuery = useQuery({
    queryKey: ['related-people', spaceId],
    queryFn: async () => {
      try {
        return await peopleApi.listRelatedPersonsApiV1SpacesSpaceIdRelatedPersonsGet(
          { spaceId },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const saveMutation = useMutation({
    mutationFn: async (fields: RelatedPersonFields) => {
      try {
        if (editing) {
          return await peopleApi.updateRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdPut(
            {
              personId: editing.id,
              spaceId,
              ifMatch: String(editing.version),
              relatedPersonFields: fields,
            },
          );
        }
        return await peopleApi.createRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPost(
          {
            spaceId,
            relatedPersonFields: fields,
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setSavedMessage(editing ? t('people.updated') : t('people.created'));
      setEditing(null);
      await queryClient.invalidateQueries({
        queryKey: ['related-people', spaceId],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (policy: RelatedPersonDeletePolicyValue) => {
      if (!deleteTarget) return;
      try {
        await peopleApi.deleteRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdDelete(
          {
            personId: deleteTarget.id,
            spaceId,
            deletePolicy: policy,
            ifMatch: String(deleteTarget.version),
          },
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setDeleteTarget(null);
      setSavedMessage(t('people.deleted'));
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['related-people', spaceId],
        }),
        queryClient.invalidateQueries({
          queryKey: ['important-dates', spaceId],
        }),
      ]);
    },
  });

  return (
    <div className="page">
      <PageHeader
        eyebrow={t('people.eyebrow')}
        title={t('people.title')}
        description={t('people.intro')}
      />

      {savedMessage ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{savedMessage}</span>
        </div>
      ) : null}

      <RelatedPersonForm
        key={editing?.id ?? 'new'}
        person={editing}
        pending={saveMutation.isPending}
        onCancel={() => {
          setEditing(null);
          saveMutation.reset();
        }}
        onSubmit={(fields) => {
          setSavedMessage(null);
          saveMutation.mutate(fields);
        }}
      />
      {saveMutation.error ? <ProblemState error={saveMutation.error} /> : null}

      <section
        className="story-surface"
        aria-labelledby="related-people-list-title"
      >
        <div className="section-head">
          <div>
            <p className="section-kicker">{t('people.listKicker')}</p>
            <h2 id="related-people-list-title">{t('people.listTitle')}</h2>
          </div>
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => void peopleQuery.refetch()}
            disabled={peopleQuery.isFetching}
          >
            {peopleQuery.isFetching
              ? t('common.refreshing')
              : t('common.refresh')}
          </button>
        </div>

        {peopleQuery.isLoading ? (
          <UiState kind="loading" title={t('people.loading')} />
        ) : null}
        {peopleQuery.error ? (
          <ProblemState
            error={peopleQuery.error}
            onRetry={() => void peopleQuery.refetch()}
          />
        ) : null}
        {peopleQuery.data?.length === 0 ? (
          <UiState
            kind="empty"
            title={t('people.emptyTitle')}
            body={t('people.emptyBody')}
          />
        ) : null}
        {peopleQuery.data?.length ? (
          <ul className="story-list" aria-label={t('people.listAria')}>
            {peopleQuery.data.map((person) => (
              <li key={person.id} className="story-card">
                <div className="section-head">
                  <div>
                    <h3>{person.displayName}</h3>
                    <p>
                      {t(`people.relationship.${person.relationship}`)} ·{' '}
                      {t(`people.visibility.${person.visibility}`)}
                    </p>
                    {person.birthday ? (
                      <p>
                        {t('people.birthdayValue', {
                          date: person.birthdayYearKnown
                            ? birthdayFormatter.format(person.birthday)
                            : birthdayWithoutYearFormatter.format(
                                person.birthday,
                              ),
                        })}
                      </p>
                    ) : null}
                  </div>
                  <div className="form-actions">
                    <button
                      type="button"
                      className="secondary compact-action"
                      onClick={() => {
                        setEditing(person);
                        saveMutation.reset();
                        setSavedMessage(null);
                      }}
                    >
                      {t('people.edit')}
                    </button>
                    <button
                      type="button"
                      className="tertiary compact-action"
                      onClick={() => {
                        setDeleteTarget(person);
                        deleteMutation.reset();
                      }}
                    >
                      {t('people.delete')}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <ImportantDatesPanel
        peopleApi={peopleApi}
        spaceId={spaceId}
        people={peopleQuery.data ?? []}
      />

      {deleteTarget ? (
        <DeleteRelatedPersonDialog
          key={deleteTarget.id}
          person={deleteTarget}
          pending={deleteMutation.isPending}
          error={deleteMutation.error}
          onCancel={() => {
            setDeleteTarget(null);
            deleteMutation.reset();
          }}
          onDelete={(policy) => deleteMutation.mutate(policy)}
        />
      ) : null}
    </div>
  );
}
