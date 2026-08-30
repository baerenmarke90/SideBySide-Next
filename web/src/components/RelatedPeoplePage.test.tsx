import { renderToStaticMarkup } from 'react-dom/server';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { PersonRelationship } from '../api/generated/models/PersonRelationship';
import { RelatedPersonDeletePolicy } from '../api/generated/models/RelatedPersonDeletePolicy';
import type { RelatedPersonView } from '../api/generated/models/RelatedPersonView';
import { DeleteRelatedPersonDialogContent } from './RelatedPeoplePage';

const person: RelatedPersonView = {
  id: 'person-1',
  displayName: 'Lisa',
  relationship: PersonRelationship.FRIEND,
  birthday: null,
  birthdayYearKnown: false,
  visibility: ContentVisibility.SHARED,
  version: 3,
  createdAt: new Date('2026-01-01T00:00:00Z'),
  updatedAt: new Date('2026-01-02T00:00:00Z'),
};

function renderChoice(
  policy:
    | typeof RelatedPersonDeletePolicy.preserve
    | typeof RelatedPersonDeletePolicy.cascade
    | null,
  cascadeConfirmed = false,
): string {
  return renderToStaticMarkup(
    <DeleteRelatedPersonDialogContent
      person={person}
      pending={false}
      error={null}
      choice={{ policy, cascadeConfirmed }}
      onSelectPolicy={() => undefined}
      onCascadeConfirmed={() => undefined}
      onCancel={() => undefined}
      onDelete={() => undefined}
    />,
  );
}

describe('RelatedPerson delete dialog', () => {
  it('starts without a delete-policy default and exposes dialog semantics', () => {
    const html = renderChoice(null);

    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
    expect(html).toContain('value="preserve"');
    expect(html).toContain('value="cascade"');
    expect(html).not.toContain('checked=""');
    expect(html).not.toContain('role="alert"');
    expect(html).toContain('disabled=""');
  });

  it('allows preserve without presenting a destructive warning', () => {
    const html = renderChoice(RelatedPersonDeletePolicy.preserve);

    expect(html).toContain('value="preserve" checked=""');
    expect(html).not.toContain('role="alert"');
    expect(html).not.toContain('disabled=""');
  });

  it('shows a privacy-safe warning and blocks unconfirmed cascade', () => {
    const html = renderChoice(RelatedPersonDeletePolicy.cascade);

    expect(html).toContain('value="cascade" checked=""');
    expect(html).toContain('role="alert"');
    expect(html).toContain('Einträge deines Partners');
    expect(html).toContain('keine Anzahl oder Details');
    expect(html).toContain('disabled=""');
  });

  it('enables cascade only after the explicit second confirmation', () => {
    const html = renderChoice(RelatedPersonDeletePolicy.cascade, true);

    expect(html).toContain('role="alert"');
    expect(html.match(/checked=""/g)).toHaveLength(2);
    expect(html).not.toContain('disabled=""');
  });
});
