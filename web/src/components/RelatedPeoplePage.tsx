import { type FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PeopleApi } from '../api/generated/apis/PeopleApi';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { PersonRelationship } from '../api/generated/models/PersonRelationship';
import { RelatedPersonDeletePolicy } from '../api/generated/models/RelatedPersonDeletePolicy';
import type { RelatedPersonFields } from '../api/generated/models/RelatedPersonFields';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import { normalizeClientError } from '../client/problemDetails';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

const RELATIONSHIPS = Object.values(PersonRelationship);
const VISIBILITIES = Object.values(ContentVisibility);

type DeletePolicy =
  (typeof RelatedPersonDeletePolicy)[keyof typeof RelatedPersonDeletePolicy];

function dateInputValue(value: Date | null): string {
  if (!value) return '';
  return value.toISOString().slice(0, 10);
}

function personFields(form: FormData): RelatedPersonFields {
  const birthdayValue = String(form.get('birthday') || '');
  return {
    displayName: String(form.get('displayName') || '').trim(),
    relationship: String(form.get('relationship')) as RelatedPersonFields['relationship'],
    visibility: String(form.get('visibility')) as RelatedPersonFields['visibility'],
    birthday: birthdayValue
      ? new Date(`${birthdayValue}T00:00:00.000Z`)
      : null,
    birthdayYearKnown: birthdayValue
      ? form.get('birthdayYearKnown') === 'on'
      : false,
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
  const { t } = useTranslation();

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
          <label htmlFor="related-person-birthday">
            {t('people.birthdayLabel')}
          </label>
          <input
            id="related-person-birthday"
            name="birthday"
            type="date"
            defaultValue={dateInputValue(person?.birthday ?? null)}
          />
          <label className="choice-row" htmlFor="related-person-birthday-year-known">
            <input
              id="related-person-birthday-year-known"
              name="birthdayYearKnown"
              type="checkbox"
              defaultChecked={person?.birthdayYearKnown ?? true}
            />
            <span>{t('people.birthdayYearKnown')}</span>
          </label>
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
  onDelete: (policy: DeletePolicy) => void;
}) {
  const { t } = useTranslation();
  const [policy, setPolicy] = useState<DeletePolicy | null>(null);
  const [cascadeConfirmed, setCascadeConfirmed] = useState(false);
  const canDelete =
    policy === RelatedPersonDeletePolicy.preserve ||
    (policy === RelatedPersonDeletePolicy.cascade && cascadeConfirmed);

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="related-person-delete-title"
        aria-describedby="related-person-delete-description"
      >
        <h2 id="related-person-delete-title">{t('people.deleteTitle')}</h2>
        <p id="related-person-delete-description">
          {t('people.deleteBody', { name: person.displayName })}
        </p>
        <p className="field-help">{t('people.deletePrivacyNote')}</p>

        <fieldset className="form-grid">
          <legend>{t('people.deletePolicyLegend')}</legend>
          <label className="choice-card">
            <input
              type="radio"
              name="deletePolicy"
              value={RelatedPersonDeletePolicy.preserve}
              checked={policy === RelatedPersonDeletePolicy.preserve}
              onChange={() => {
                setPolicy(RelatedPersonDeletePolicy.preserve);
                setCascadeConfirmed(false);
              }}
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
              checked={policy === RelatedPersonDeletePolicy.cascade}
              onChange={() => {
                setPolicy(RelatedPersonDeletePolicy.cascade);
                setCascadeConfirmed(false);
              }}
            />
            <span>
              <strong>{t('people.deleteCascadeTitle')}</strong>
              <small>{t('people.deleteCascadeBody')}</small>
            </span>
          </label>
        </fieldset>

        {policy === RelatedPersonDeletePolicy.cascade ? (
          <div className="inline-message inline-message-danger" role="alert">
            <strong>{t('people.deleteCascadeWarningTitle')}</strong>
            <span>{t('people.deleteCascadeWarningBody')}</span>
            <label className="choice-row">
              <input
                type="checkbox"
                checked={cascadeConfirmed}
                onChange={(event) => setCascadeConfirmed(event.currentTarget.checked)}
              />
              <span>{t('people.deleteCascadeConfirm')}</span>
            </label>
          </div>
        ) : null}

        {error ? <ProblemState error={error} /> : null}

        <div className="form-actions">
          <button type="button" className="secondary" onClick={onCancel} disabled={pending}>
            {t('common.cancel')}
          </button>
          <button
            type="button"
            className={policy === RelatedPersonDeletePolicy.cascade ? 'danger' : undefined}
            disabled={!canDelete || pending}
            onClick={() => {
              if (policy && canDelete) onDelete(policy);
            }}
          >
            {pending ? t('people.deleting') : t('people.deleteConfirm')}
          </button>
        </div>
      </section>
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
  const [deleteTarget, setDeleteTarget] = useState<RelatedPersonView | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const birthdayFormatter = useMemo(
    () => new Intl.DateTimeFormat(i18n.language, { day: '2-digit', month: 'long', year: 'numeric' }),
    [i18n.language],
  );
  const birthdayWithoutYearFormatter = useMemo(
    () => new Intl.DateTimeFormat(i18n.language, { day: '2-digit', month: 'long' }),
    [i18n.language],
  );

  const peopleQuery = useQuery({
    queryKey: ['related-people', spaceId],
    queryFn: async () => {
      try {
        return await peopleApi.listRelatedPersonsApiV1SpacesSpaceIdRelatedPersonsGet({ spaceId });
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
          return await peopleApi.updateRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdPut({
            personId: editing.id,
            spaceId,
            ifMatch: String(editing.version),
            relatedPersonFields: fields,
          });
        }
        return await peopleApi.createRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPost({
          spaceId,
          relatedPersonFields: fields,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setSavedMessage(editing ? t('people.updated') : t('people.created'));
      setEditing(null);
      await queryClient.invalidateQueries({ queryKey: ['related-people', spaceId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (policy: DeletePolicy) => {
      if (!deleteTarget) return;
      try {
        await peopleApi.deleteRelatedPersonApiV1SpacesSpaceIdRelatedPersonsPersonIdDelete({
          personId: deleteTarget.id,
          spaceId,
          deletePolicy: policy,
          ifMatch: String(deleteTarget.version),
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      setDeleteTarget(null);
      setSavedMessage(t('people.deleted'));
      await queryClient.invalidateQueries({ queryKey: ['related-people', spaceId] });
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

      <section className="story-surface" aria-labelledby="related-people-list-title">
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
            {peopleQuery.isFetching ? t('common.refreshing') : t('common.refresh')}
          </button>
        </div>

        {peopleQuery.isLoading ? <UiState kind="loading" title={t('people.loading')} /> : null}
        {peopleQuery.error ? (
          <ProblemState error={peopleQuery.error} onRetry={() => void peopleQuery.refetch()} />
        ) : null}
        {peopleQuery.data?.length === 0 ? (
          <UiState kind="empty" title={t('people.emptyTitle')} body={t('people.emptyBody')} />
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
                            : birthdayWithoutYearFormatter.format(person.birthday),
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
