export default {
  title: 'Account',
  intro:
    'Hier verwaltest du Aktionen, die dein persönliches SideBySide-Konto betreffen. Beziehung und gemeinsamer Bereich bleiben davon getrennt.',
  dangerEyebrow: 'Danger Zone',
  dangerTitle: 'Konto löschen',
  dangerIntro:
    'Die Kontolöschung betrifft dein persönliches Konto. Sie ist nicht dasselbe wie den gemeinsamen Bereich zu verlassen oder eine Beziehung zu beenden.',
  deleteAction: 'Konto löschen',
  demoTitle: 'Kontolöschung in der Demo nicht verfügbar',
  demoBody:
    'Demo-Konten werden von der Demo-Umgebung verwaltet und können hier nicht selbst gelöscht werden.',
  consequencesTitle: 'Folgen der Kontolöschung',
  consequencesIntro:
    'Prüfe diese Folgen, bevor du mit der endgültigen Bestätigung fortfährst.',
  consequenceAccess:
    'Dein Kontozugriff endet und aktive Sitzungen sowie Anmeldedaten werden widerrufen.',
  consequencePrivate:
    'Daten, die nur deinem Konto gehören, werden nach dem verbindlichen Lösch-Lifecycle entfernt.',
  consequenceShared:
    'Gemeinsame Historie folgt den bestehenden Aufbewahrungsregeln. Der gemeinsame Bereich oder die Beziehung wird dadurch nicht automatisch gelöscht.',
  consequenceIrreversible:
    'Sobald der Server die Löschung angenommen hat, ist sie nicht mehr rückgängig zu machen. Die App muss für die weitere Bereinigung nicht geöffnet bleiben.',
  exportBefore: 'Vorher Daten exportieren',
  continueAction: 'Weiter',
  cancelAction: 'Abbrechen',
  finalTitle: 'Kontolöschung bestätigen',
  finalIntro:
    'Diese Aktion kann nach der Annahme durch den Server nicht rückgängig gemacht werden.',
  confirmInstruction:
    'Gib {{phrase}} ein, um dein Konto endgültig zur Löschung freizugeben.',
  confirmLabel: 'Bestätigung',
  confirmPhrase: 'KONTO LÖSCHEN',
  confirmHelp: 'Die Eingabe muss genau mit dem angezeigten Text übereinstimmen.',
  backAction: 'Zurück',
  submitAction: 'Konto endgültig löschen',
  submitting: 'Kontolöschung wird gestartet …',
} as const;
