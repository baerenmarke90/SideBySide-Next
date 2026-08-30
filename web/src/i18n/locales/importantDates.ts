const importantDates = {
  heading: 'Wichtige Termine',
  intro:
    'Geburtstage, Jahrestage und andere wichtige Daten könnt ihr hier gemeinsam oder nur für euch selbst festhalten.',
  createTitle: 'Termin hinzufügen',
  editTitle: 'Termin bearbeiten',
  labelLabel: 'Bezeichnung',
  dateLabel: 'Datum',
  typeLabel: 'Art',
  repeatLabel: 'Wiederholung',
  personLabel: 'Verknüpfte Person',
  personNone: 'Keine Person verknüpfen',
  visibilityLabel: 'Sichtbarkeit',
  visibilityHelp:
    'Geteilte Termine sind für euch beide sichtbar. Private Termine bleiben nur bei dir.',
  create: 'Termin hinzufügen',
  saveChanges: 'Änderungen speichern',
  saving: 'Wird gespeichert …',
  created: 'Termin wurde hinzugefügt.',
  updated: 'Änderungen wurden gespeichert.',
  deleted: 'Termin wurde gelöscht.',
  loading: 'Wichtige Termine werden geladen …',
  listTitle: 'Gespeicherte Termine',
  emptyTitle: 'Noch kein wichtiger Termin gespeichert',
  emptyBody:
    'Fügt hier Daten hinzu, an die ihr euch erinnern oder die ihr gemeinsam im Blick behalten möchtet.',
  dateValue: '{{date}}',
  linkedPerson: 'Für {{name}}',
  edit: 'Bearbeiten',
  delete: 'Löschen',
  deleteQuestion: 'Diesen Termin wirklich löschen?',
  deleteBody:
    'Der Termin wird dauerhaft entfernt. Andere Personen oder Termine werden dadurch nicht gelöscht.',
  deleteConfirm: 'Termin löschen',
  deleting: 'Wird gelöscht …',
  type: {
    BIRTHDAY: 'Geburtstag',
    ANNIVERSARY: 'Jahrestag',
    CUSTOM: 'Anderer Termin',
  },
  repeats: {
    NONE: 'Keine Wiederholung',
    ANNUALLY: 'Jährlich',
  },
  visibility: {
    SHARED: 'Mit Partner geteilt',
    PRIVATE: 'Nur für mich',
  },
} as const;

export default importantDates;
