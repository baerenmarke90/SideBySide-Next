const people = {
  eyebrow: 'Wichtige Menschen',
  title: 'Menschen in eurem Leben',
  intro:
    'Haltet Personen fest, die für euch wichtig sind. Sichtbarkeit und persönliche Angaben bleiben bewusst unter eurer Kontrolle.',
  formRailAria: 'Person anlegen oder bearbeiten',
  createTitle: 'Person hinzufügen',
  editTitle: 'Person bearbeiten',
  nameLabel: 'Name',
  relationshipLabel: 'Beziehung',
  birthdayLabel: 'Geburtstag',
  birthdayYearKnown: 'Das Geburtsjahr ist bekannt',
  birthdayDayLabel: 'Tag',
  birthdayMonthLabel: 'Monat',
  birthdayMonthPlaceholder: 'Monat auswählen',
  birthdayUnknownYearHelp:
    'Wenn das Geburtsjahr unbekannt ist, speichert und zeigt SideBySide nur Tag und Monat.',
  visibilityLabel: 'Sichtbarkeit',
  visibilityHelp:
    'Geteilte Personen sind für euch beide sichtbar. Private Personen bleiben nur bei dir.',
  create: 'Person hinzufügen',
  saveChanges: 'Änderungen speichern',
  saving: 'Wird gespeichert …',
  created: 'Person wurde hinzugefügt.',
  updated: 'Änderungen wurden gespeichert.',
  deleted: 'Person wurde gelöscht.',
  loading: 'Wichtige Menschen werden geladen …',
  listKicker: 'Euer Umfeld',
  listTitle: 'Gespeicherte Personen',
  listAria: 'Wichtige Menschen',
  emptyTitle: 'Noch keine Person gespeichert',
  emptyBody:
    'Fügt hier Menschen hinzu, die in eurem gemeinsamen Leben wichtig sind.',
  birthdayValue: 'Geburtstag: {{date}}',
  edit: 'Bearbeiten',
  delete: 'Löschen',
  deleteTitle: 'Person löschen',
  deleteBody:
    'Wie sollen verknüpfte Termine behandelt werden, wenn du {{name}} löschst?',
  deletePrivacyNote:
    'Mit dieser Person verknüpfte Termine können auch Einträge deines Partners enthalten. Deshalb zeigen wir hier bewusst keine Anzahl oder Details.',
  deletePolicyLegend: 'Verknüpfte Termine',
  deletePreserveTitle: 'Termine erhalten',
  deletePreserveBody:
    'Die Person wird gelöscht. Verknüpfte Termine bleiben erhalten und werden von der Person gelöst.',
  deleteCascadeTitle: 'Termine mit löschen',
  deleteCascadeBody:
    'Die Person und alle mit ihr verknüpften Termine werden gemeinsam gelöscht.',
  deleteCascadeWarningTitle: 'Dauerhaft löschen',
  deleteCascadeWarningBody:
    'Diese Auswahl kann auch verknüpfte Termine entfernen, die du nicht sehen kannst. Die Löschung lässt sich nicht rückgängig machen.',
  deleteCascadeConfirm:
    'Ich möchte die Person und die verknüpften Termine wirklich löschen.',
  deleteConfirm: 'Person löschen',
  deleting: 'Wird gelöscht …',
  relationship: {
    CHILD: 'Kind',
    PARENT: 'Elternteil',
    SIBLING: 'Geschwister',
    FRIEND: 'Freund oder Freundin',
    OTHER: 'Andere Beziehung',
  },
  visibility: {
    SHARED: 'Mit Partner geteilt',
    PRIVATE: 'Nur für mich',
  },
} as const;

export default people;
