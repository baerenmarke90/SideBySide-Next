const de = {
  common: {
    cancel: 'Abbrechen',
    retry: 'Erneut versuchen',
    refresh: 'Aktualisieren',
    refreshing: 'Aktualisiert …',
  },
  navigation: {
    skipToContent: 'Zum Inhalt springen',
    primary: 'Hauptnavigation',
    story: 'Story',
    newMemory: 'Neue Erinnerung',
  },
  states: {
    validation: {
      title: 'Einige Angaben passen noch nicht.',
      body: 'Bitte prüfe deine Eingaben und versuche es erneut.',
    },
    session: {
      title: 'Deine Sitzung ist nicht mehr gültig.',
      body: 'Bitte melde dich erneut an.',
    },
    permission: {
      title: 'Dieser Inhalt ist nicht verfügbar.',
      body: 'Du kannst diesen Inhalt mit deinem aktuellen Zugriff nicht öffnen.',
    },
    conflict: {
      title: 'Die Daten haben sich inzwischen geändert.',
      body: 'Lade den aktuellen Stand neu und wiederhole deine Änderung.',
    },
    rateLimit: {
      title: 'Das waren zu viele Anfragen in kurzer Zeit.',
      body: 'Warte einen Moment und versuche es dann erneut.',
    },
    offline: {
      title: 'Du bist gerade offline.',
      body: 'Stelle die Verbindung wieder her und versuche es erneut.',
      banner:
        'Offline – Änderungen und neue Inhalte benötigen eine Verbindung.',
    },
    server: {
      title: 'SideBySide ist gerade nicht erreichbar.',
      body: 'Versuche es in einem Moment erneut.',
    },
    unknown: {
      title: 'Etwas ist schiefgegangen.',
      body: 'Bitte versuche es erneut.',
    },
    unexpected: {
      title: 'Diese Ansicht konnte nicht angezeigt werden.',
      body: 'Öffne die Ansicht erneut. Deine gespeicherten Inhalte bleiben unverändert.',
    },
  },
  theme: {
    label: 'Darstellung',
    system: 'System',
    light: 'Hell',
    dark: 'Dunkel',
  },
  brand: {
    suffix: 'Next',
    storyAria: 'SideBySide – zur Story',
  },
  setup: {
    eyebrow: 'Fast bereit',
    heading: 'Diese Installation ist noch nicht vollständig eingerichtet.',
    body: 'Bitte wende dich an die Person, die diese SideBySide-Instanz betreibt.',
    operatorSummary: 'Hinweis für Betreiber',
    operatorPrefix:
      'Für den aktuellen Story-Flow muss beim Web-Build eine vorhandene Space-ID als',
    operatorSuffix: 'gesetzt sein.',
  },
  login: {
    introHeading: 'Euer gemeinsamer Raum für die Dinge, die bleiben.',
    introBody:
      'Erinnerungen, Wünsche und Pläne an einem ruhigen Ort – nur für euch zwei.',
    eyebrow: 'Willkommen zurück',
    heading: 'Anmelden',
    body: 'Melde dich mit deinem SideBySide-Konto an.',
    email: 'E-Mail',
    password: 'Passwort',
    submit: 'Anmelden',
    pending: 'Anmeldung läuft …',
    errorFallback:
      'Anmeldung fehlgeschlagen. Bitte prüfe deine Zugangsdaten und versuche es erneut.',
    assurance: 'Euer gemeinsamer Space bleibt nur für euch bestimmt.',
  },
  story: {
    savedTitle: 'Erinnerung gespeichert.',
    savedBody: 'Sie ist jetzt Teil eurer gemeinsamen Story.',
    eyebrow: 'Gemeinsam erinnern',
    title: 'Eure Story',
    intro:
      'Erinnerungen, Herzmomente und Meilensteine – chronologisch an einem Ort.',
    addMemory: 'Erinnerung hinzufügen',
    timelineKicker: 'Zeitleiste',
    timelineHeading: 'Gemeinsame Geschichte',
    loadingAria: 'Story wird geladen',
    loadErrorTitle: 'Die Story konnte nicht geladen werden.',
    loadErrorFallback: 'Bitte versuche es erneut.',
    emptyTitle: 'Eure Story beginnt hier.',
    emptyBody: 'Haltet euren ersten gemeinsamen Moment fest.',
    aria: 'Gemeinsame Story',
    byAuthor: 'von {{author}}',
    kind: {
      memory: 'Erinnerung',
      heartMoment: 'Herzmoment',
      milestone: 'Meilenstein',
    },
    emotion: {
      loved: 'Geliebt',
      seen: 'Gesehen',
      appreciated: 'Wertgeschätzt',
      supported: 'Unterstützt',
      grateful: 'Dankbar',
      happy: 'Glücklich',
      fallback: 'Herzmoment',
    },
    shared: 'Geteilt',
    photos_one: '{{count}} Foto',
    photos_other: '{{count}} Fotos',
  },
  memory: {
    backToStory: '← Zurück zur Story',
    eyebrow: 'Moment festhalten',
    heading: 'Neue Erinnerung',
    intro:
      'Ein Titel genügt. Fotos und weitere Details könnt ihr optional ergänzen.',
    formAria: 'Erinnerung erstellen',
    titleLabel: 'Titel',
    titlePlaceholder: 'Zum Beispiel: Unser Tag am See',
    bodyLabel: 'Erinnerung',
    bodyPlaceholder: 'Was möchtet ihr von diesem Moment behalten?',
    dateLabel: 'Datum',
    dateHelp: 'Optional – wenn der Moment an einem bestimmten Tag war.',
    photoLabel: 'Fotos',
    photoSelected: 'Foto ausgewählt',
    photoSelect: 'Fotos auswählen',
    photoAddMore: 'Weitere Fotos auswählen',
    photoFormats: 'JPG, PNG, WebP, HEIC oder HEIF',
    photoDraftsAria: 'Ausgewählte Fotos',
    photoLocalPreview: 'Lokale Vorschau',
    photoPreviewAlt: 'Lokale Vorschau für {{name}}',
    photoUploading: 'Wird hochgeladen …',
    photoValidating: 'Wird geprüft …',
    photoReady: 'Bereit zum Speichern',
    photoFailed: 'Upload fehlgeschlagen',
    photoFailedNotSaved:
      'Dieses Foto wird nicht gespeichert, solange der Upload fehlgeschlagen ist.',
    photoRemove: 'Entfernen',
    photoPendingSave:
      'Warte, bis alle laufenden Foto-Uploads abgeschlossen sind.',
    visibilityAria: 'Sichtbarkeit',
    sharedTitle: 'Mit Partner geteilt',
    sharedBody:
      'Diese Erinnerung ist für beide Personen in eurem gemeinsamen Space sichtbar.',
    save: 'Erinnerung speichern',
    saving: 'Wird gespeichert …',
    processing: 'Erinnerung wird gespeichert und die Story aktualisiert …',
    saveErrorTitle: 'Die Erinnerung konnte nicht gespeichert werden.',
    saveErrorFallback: 'Bitte prüfe deine Verbindung und versuche es erneut.',
    imageRequired: 'Bitte wähle ein Bild aus.',
  },
  header: {
    sharedArea: 'Gemeinsamer Bereich',
    logout: 'Abmelden',
  },
  media: {
    unavailable: 'Foto derzeit nicht verfügbar',
    loading: 'Foto wird geladen',
    alt: 'Foto zu dieser Erinnerung',
  },
  flow: {
    uploadFailed: 'Bild-Upload fehlgeschlagen',
    processingStatus: 'Medienverarbeitung beendet mit Status {{status}}.',
    processingTimeout:
      'Medienverarbeitung hat das READY-Fenster nicht rechtzeitig erreicht.',
    imageLoadFailed: 'Bild konnte nicht geladen werden',
    signInFailed: 'Anmeldung fehlgeschlagen.',
    imageOnly: 'S8 akzeptiert ausschließlich Bilder.',
    imageEmpty: 'Das ausgewählte Bild ist leer.',
    saveFailed: 'Erinnerung konnte nicht gespeichert werden.',
  },
} as const;

export default de;
