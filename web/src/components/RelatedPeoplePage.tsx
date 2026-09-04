import {
  type ChangeEvent,
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
import type { AttachmentsApi } from '../api/generated/apis/AttachmentsApi';
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
import { invalidateDashboard } from '../client/dashboardQueries';
import { createReferenceApis } from '../client/referenceFlow';
import {
  type DraftUploadPhase,
  uploadMemoryDraftAttachment,
} from '../client/memoryAttachmentDraft';
import { useRelatedPersonAvatarUrl } from '../client/useRelatedPersonAvatarUrl';
import { personInitials } from './PersonIdentity';
import { useTranslation } from '../i18n';
import { ImportantDatesPanel } from './ImportantDatesPanel';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './RelatedPeoplePage.css';

const RELATIONSHIPS = Object.values(PersonRelationship);
const VISIBILITIES = Object.values(ContentVisibility);

function dateInputValue(value: Date | null): string {
  if (!value) return '';
  return value.toISOString().slice(0, 10);
}

function personFields(
  form: FormData,
  avatarAttachmentId: string | null,
): RelatedPersonFields {
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
    avatarAttachmentId: avatarAttachmentId || undefined,
  };
}

function PersonCardAvatar({
  person,
  attachmentsApi,
  spaceId,
}: {
  person: RelatedPersonView;
  attachmentsApi: AttachmentsApi | undefined | null;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const { avatarUrl } = useRelatedPersonAvatarUrl(
    attachmentsApi,
    spaceId,
    person.avatarAttachmentId,
  );
  const initials = useMemo(
    () => personInitials(person.displayName),
    [person.displayName],
  );

  return (
    <div className="people-avatar-circle" aria-hidden="true">
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={t('people.avatarAlt', { name: person.displayName })}
        />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  );
}

function RelatedPersonModalDialog({
  person,
  pending,
  error,
  spaceId,
  apiBaseUrl,
  accessToken,
  attachmentsApi,
  onCancel,
  onSubmit,
  onDeleteRequest,
}: {
  person: RelatedPersonView | null;
  pending: boolean;
  error: Error | null;
  spaceId: string;
  apiBaseUrl?: string;
  accessToken?: string;
  attachmentsApi?: AttachmentsApi | null;
  onCancel: () => void;
  onSubmit: (fields: RelatedPersonFields) => void;
  onDeleteRequest?: () => void;
}) {
  const { t, i18n } = useTranslation();
  const dialogRef = useRef<HTMLElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const [currentAvatarId, setCurrentAvatarId] = useState<string | null>(
    person?.avatarAttachmentId ?? null,
  );
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState<string | null>(null);
  const [uploadPhase, setUploadPhase] = useState<DraftUploadPhase | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { avatarUrl: existingAvatarUrl } = useRelatedPersonAvatarUrl(
    attachmentsApi,
    spaceId,
    person?.avatarAttachmentId,
  );

  const displayedAvatarUrl = avatarPreviewUrl || (currentAvatarId ? existingAvatarUrl : null);
  const initials = useMemo(
    () => (person ? personInitials(person.displayName) : '?'),
    [person],
  );

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

  useEffect(() => {
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    cancelButtonRef.current?.focus();
    return () => previousFocus?.focus();
  }, []);

  function handleDialogKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !pending && !uploadPhase) {
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

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    if (!file.type.startsWith('image/')) {
      setUploadError(t('flow.imageOnly'));
      return;
    }
    if (apiBaseUrl && accessToken) {
      try {
        const referenceApis = createReferenceApis(apiBaseUrl, accessToken);
        const ready = await uploadMemoryDraftAttachment(
          referenceApis,
          apiBaseUrl,
          accessToken,
          spaceId,
          file,
          setUploadPhase,
        );
        setCurrentAvatarId(ready.attachmentId);
        setAvatarPreviewUrl(URL.createObjectURL(file));
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : t('flow.uploadFailed'));
      } finally {
        setUploadPhase(null);
      }
    } else {
      setAvatarPreviewUrl(URL.createObjectURL(file));
    }
  }

  function handleAvatarRemove() {
    setCurrentAvatarId(null);
    setAvatarPreviewUrl(null);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(personFields(new FormData(event.currentTarget), currentAvatarId));
  }

  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const backdropEl = backdropRef.current;
    if (!backdropEl) return;
    function handleBackdropClick(e: MouseEvent) {
      if (e.target === backdropEl && !pending && !uploadPhase) {
        onCancel();
      }
    }
    backdropEl.addEventListener('click', handleBackdropClick);
    return () => backdropEl.removeEventListener('click', handleBackdropClick);
  }, [pending, uploadPhase, onCancel]);

  return (
    <div
      ref={backdropRef}
      className="modal-backdrop"
      role="presentation"
    >
      <section
        ref={dialogRef}
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="related-person-modal-title"
        onKeyDown={handleDialogKeyDown}
      >
        <div className="people-modal-header">
          <h2 id="related-person-modal-title">
            {person ? t('people.editTitle') : t('people.createTitle')}
          </h2>
          <button
            type="button"
            className="people-modal-close"
            onClick={onCancel}
            aria-label={t('people.closeDialogAria')}
            disabled={pending || Boolean(uploadPhase)}
          >
            ✕
          </button>
        </div>

        <form key={person?.id ?? 'new'} className="form-grid" onSubmit={submit}>
          <div className="field-group">
            <span id="related-person-avatar-label">{t('people.avatarLabel')}</span>
            <div className="people-modal-avatar-row">
              <div className="people-modal-avatar-preview" aria-hidden="true">
                {displayedAvatarUrl ? (
                  <img
                    src={displayedAvatarUrl}
                    alt=""
                  />
                ) : (
                  <span>{initials}</span>
                )}
              </div>
              <div className="people-modal-avatar-actions">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  aria-label={t('people.avatarLabel')}
                />
                <button
                  type="button"
                  className="secondary compact-action"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={pending || Boolean(uploadPhase)}
                >
                  {displayedAvatarUrl
                    ? t('people.avatarChange')
                    : t('people.avatarUpload')}
                </button>
                {displayedAvatarUrl ? (
                  <button
                    type="button"
                    className="tertiary compact-action"
                    onClick={handleAvatarRemove}
                    disabled={pending || Boolean(uploadPhase)}
                  >
                    {t('people.avatarRemove')}
                  </button>
                ) : null}
                {uploadPhase ? (
                  <small className="field-help">
                    {uploadPhase === 'validating'
                      ? t('people.avatarValidating')
                      : t('people.avatarUploading')}
                  </small>
                ) : null}
              </div>
            </div>
            {uploadError ? (
              <p className="field-help" style={{ color: 'var(--color-error)' }}>
                {uploadError}
              </p>
            ) : null}
          </div>

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

          {error ? <ProblemState error={error} /> : null}

          <div className="form-actions">
            <button
              ref={cancelButtonRef}
              type="button"
              className="secondary"
              onClick={onCancel}
              disabled={pending || Boolean(uploadPhase)}
            >
              {t('common.cancel')}
            </button>
            <button type="submit" disabled={pending || Boolean(uploadPhase)}>
              {pending
                ? t('people.saving')
                : person
                  ? t('people.saveChanges')
                  : t('people.create')}
            </button>
          </div>

          {person && onDeleteRequest ? (
            <div className="people-modal-danger-zone">
              <button
                type="button"
                className="secondary danger compact-action"
                onClick={onDeleteRequest}
                disabled={pending || Boolean(uploadPhase)}
              >
                {t('people.delete')}
              </button>
            </div>
          ) : null}
        </form>
      </section>
    </div>
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
  apiBaseUrl,
  accessToken,
  attachmentsApi,
}: {
  peopleApi: PeopleApi;
  spaceId: string;
  apiBaseUrl?: string;
  accessToken?: string;
  attachmentsApi?: AttachmentsApi;
}) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [editingPerson, setEditingPerson] = useState<RelatedPersonView | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<RelatedPersonView | null>(null);
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
        if (editingPerson) {
          return await peopleApi.updateRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdPut(
            {
              personId: editingPerson.id,
              spaceId,
              ifMatch: String(editingPerson.version),
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
      setSavedMessage(editingPerson ? t('people.updated') : t('people.created'));
      setEditingPerson(null);
      setIsCreating(false);
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['related-people', spaceId],
        }),
        invalidateDashboard(queryClient, spaceId),
      ]);
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
        invalidateDashboard(queryClient, spaceId),
      ]);
    },
  });

  return (
    <div className="page">
      <PageHeader
        eyebrow={t('people.eyebrow')}
        title={t('people.title')}
        description={t('people.intro')}
        action={
          <button
            type="button"
            className="primary compact-action"
            onClick={() => {
              setIsCreating(true);
              setEditingPerson(null);
              saveMutation.reset();
              setSavedMessage(null);
            }}
          >
            + {t('people.addPersonAction')}
          </button>
        }
      />

      {savedMessage ? (
        <div className="inline-message inline-message-success" role="status">
          <span>{savedMessage}</span>
        </div>
      ) : null}

      <section
        className="story-surface"
        aria-labelledby="related-people-list-title"
      >
        <div className="section-head">
          <div>
            <p className="section-kicker">{t('people.listKicker')}</p>
            <h2 id="related-people-list-title">{t('people.listTitle')}</h2>
          </div>
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
          <ul className="people-grid" aria-label={t('people.listAria')}>
            {peopleQuery.data.map((person) => (
              <li key={person.id} className="people-card-item">
                <button
                  type="button"
                  className="people-card"
                  onClick={() => {
                    setEditingPerson(person);
                    setIsCreating(false);
                    saveMutation.reset();
                    setSavedMessage(null);
                  }}
                >
                  <PersonCardAvatar
                    person={person}
                    attachmentsApi={attachmentsApi}
                    spaceId={spaceId}
                  />
                  <div className="people-card-body">
                  <h3 className="people-card-name">{person.displayName}</h3>
                  <p className="people-card-relationship">
                    {t(`people.relationship.${person.relationship}`)}
                  </p>
                  {person.birthday ? (
                    <p className="people-card-birthday">
                      <span aria-hidden="true">🎂</span>
                      <span>
                        {person.birthdayYearKnown
                          ? birthdayFormatter.format(person.birthday)
                          : birthdayWithoutYearFormatter.format(
                              person.birthday,
                            )}
                      </span>
                    </p>
                  ) : null}
                  <span
                    className={`people-card-badge ${
                      person.visibility === ContentVisibility.PRIVATE
                        ? 'people-card-badge-private'
                        : ''
                    }`.trim()}
                  >
                    {t(`people.visibility.${person.visibility}`)}
                  </span>
                </div>
              </button>
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

      {(isCreating || editingPerson) ? (
        <RelatedPersonModalDialog
          key={editingPerson?.id ?? 'create'}
          person={editingPerson}
          pending={saveMutation.isPending}
          error={saveMutation.error}
          spaceId={spaceId}
          apiBaseUrl={apiBaseUrl}
          accessToken={accessToken}
          attachmentsApi={attachmentsApi}
          onCancel={() => {
            setIsCreating(false);
            setEditingPerson(null);
            saveMutation.reset();
          }}
          onSubmit={(fields) => {
            setSavedMessage(null);
            saveMutation.mutate(fields);
          }}
          onDeleteRequest={
            editingPerson
              ? () => {
                  const target = editingPerson;
                  setIsCreating(false);
                  setEditingPerson(null);
                  setDeleteTarget(target);
                }
              : undefined
          }
        />
      ) : null}

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
