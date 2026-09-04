const importantDates = {
  heading: 'Besondere Tage',
  intro:
    'Geburtstage, Jahrestage und andere besondere Tage könnt ihr hier gemeinsam oder nur für euch festhalten.',
  createTitle: 'Besonderen Tag festhalten',
  editTitle: 'Besonderen Tag ändern',
  labelLabel: 'Was ist der Anlass?',
  dateLabel: 'Wann ist es soweit?',
  typeLabel: 'Art',
  repeatLabel: 'Wiederholung',
  personLabel: 'Für wen ist dieser Tag?',
  personNone: 'Für niemand Bestimmten',
  visibilityLabel: 'Wer kann das sehen?',
  visibilityHelp:
    'Geteilte Tage sind für euch beide sichtbar. Private Tage bleiben nur bei dir.',
  create: 'Besonderen Tag festhalten',
  saveChanges: 'Änderungen speichern',
  saving: 'Wird gespeichert …',
  created: 'Besonderer Tag wurde festgehalten.',
  updated: 'Änderungen wurden gespeichert.',
  deleted: 'Besonderer Tag wurde gelöscht.',
  loading: 'Besondere Tage werden geladen …',
  listTitle: 'Eure besonderen Tage',
  emptyTitle: 'Noch kein besonderer Tag festgehalten',
  emptyBody:
    'Haltet hier Tage fest, an die ihr euch erinnern oder die ihr gemeinsam im Blick behalten möchtet.',
  dateValue: '{{date}}',
  linkedPerson: 'Für {{name}}',
  edit: 'Bearbeiten',
  delete: 'Löschen',
  deleteQuestion: 'Diesen besonderen Tag wirklich löschen?',
  deleteBody:
    'Dieser Tag wird dauerhaft entfernt. Verknüpfte Personen bleiben erhalten.',
  deleteConfirm: 'Besonderen Tag löschen',
  deleting: 'Wird gelöscht …',
  discardTitle: 'Ungespeicherte Änderungen verwerfen?',
  discardBody:
    'Möchtest du den Editor wirklich schließen? Deine Änderungen gehen verloren.',
  discardConfirm: 'Änderungen verwerfen',
  keepEditing: 'Weiter bearbeiten',
  closeDialogAria: 'Dialog schließen',
  type: {
    BIRTHDAY: 'Geburtstag',
    ANNIVERSARY: 'Jahrestag',
    CUSTOM: 'Besonderer Tag',
  },
  repeats: {
    NONE: 'Keine Wiederholung',
    ANNUALLY: 'Jährlich',
  },
  visibility: {
    SHARED: 'Für uns beide',
    PRIVATE: 'Nur für mich',
  },
} as const;

export default importantDates;

