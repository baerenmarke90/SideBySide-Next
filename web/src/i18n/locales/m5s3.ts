const m5s3 = {
  common: {
    back: '← Zurück zu Planen',
    title: 'Titel',
    description: 'Beschreibung',
    place: 'Ort',
    noPlace: 'Kein Ort verknüpft',
    open: 'Öffnen',
    edit: 'Bearbeiten',
    save: 'Speichern',
    saveChanges: 'Änderungen speichern',
    saving: 'Wird gespeichert …',
    loading: 'Inhalte werden geladen …',
    loadMore: 'Weitere laden',
    loadingMore: 'Weitere werden geladen …',
    empty: 'Hier gibt es noch keine Einträge.',
    readOnly:
      'Dieser Eintrag kann mit deinem aktuellen Zugriff nur gelesen werden.',
    deleteHeading: 'Löschen',
    delete: 'Löschen',
    deleting: 'Wird gelöscht …',
    confirmDelete: 'Endgültig löschen',
  },
  overview: {
    eyebrow: 'Unsere Abenteuer & Pläne',
    title: 'Erlebnisse, Träume & Geheimnisse',
    intro:
      'Alles, was wir noch gemeinsam erleben wollen, unsere größten Abenteuer, Orte, die wir entdecken möchten, und kleine Geheimnisse.',
  },
  wish: {
    heading: 'Träume & Wünsche',
    intro:
      'Die kleinen und großen Träume, die wir eines Tages wahr machen wollen.',
    create: 'Neuen Traum festhalten',
    loading: 'Wunsch wird geladen …',
    detailEyebrow: 'Gemeinsamer Wunsch',
    planTitle: 'Titel des Plans (optional)',
    convertHeading: 'Daraus einen Plan machen',
    convertIntro:
      'Die Umwandlung erfolgt auf dem Server. Ohne eigenen Plantitel wird der Wunschtitel übernommen.',
    convert: 'In Plan umwandeln',
    converting: 'Wird umgewandelt …',
    deleteConsequence:
      'Der Wunsch wird gelöscht. Bereits separat vorhandene Inhalte werden dadurch nicht verändert.',
    status: {
      OPEN: 'Offen',
      PLANNED: 'Als Plan weitergeführt',
      COMPLETED: 'Erledigt',
    },
  },
  plan: {
    heading: 'Unsere Abenteuer',
    intro:
      'Aus Träumen werden Erlebnisse. Unsere konkreten Vorhaben und gemeinsamen Abenteuer.',
    create: 'Neues Abenteuer planen',
    loading: 'Plan wird geladen …',
    detailEyebrow: 'Gemeinsamer Plan',
    lifecycleHeading: 'Planstatus ändern',
    scheduleFacts: 'Termin und Erlebnisdatum',
    plannedStart: 'Geplanter Beginn',
    plannedEnd: 'Geplantes Ende',
    experiencedOn: 'Erlebt am',
    schedule: 'Termin festlegen',
    unschedule: 'Termin wieder entfernen',
    complete: 'Als erlebt abschließen',
    returnToWish: 'Zurück zum Wunsch',
    deleteConsequence:
      'Der Plan wird gelöscht. Ein verknüpfter Ort oder andere eigenständige Inhalte bleiben erhalten.',
    status: {
      IDEA: 'Idee',
      PLANNED: 'Geplant',
      COMPLETED: 'Erlebt',
    },
  },
  place: {
    heading: 'Entdeckungen & Orte',
    intro:
      'Besondere Orte, Lieblingscafés, Traumziele oder unser kleines Geheimversteck.',
    create: 'Ort hinzufügen',
    loading: 'Ort wird geladen …',
    detailEyebrow: 'Gemeinsamer Ort',
    name: 'Name',
    address: 'Adresse',
    latitude: 'Breitengrad',
    longitude: 'Längengrad',
    coordinateHelp:
      'Koordinaten sind optional. Wenn du sie angibst, müssen Breitengrad und Längengrad gemeinsam gesetzt sein.',
    coordinatePairError:
      'Bitte gib Breitengrad und Längengrad gemeinsam an oder lasse beide Felder leer.',
    locationHeading: 'Ortsangaben',
    coordinates: '{{latitude}}, {{longitude}}',
    nameOnly: 'Dieser Ort ist bewusst ohne Koordinaten gespeichert.',
    noMap:
      'SidebySide verwendet hier keine Karten- oder Geocoding-Dienste. Der gespeicherte Ort bleibt unabhängig davon nutzbar.',
    noAddress: 'Keine Adresse hinterlegt',
    deleteConsequence:
      'Der Ort und seine Verknüpfungen werden gelöscht. Erinnerungen, Herzmomente und Meilensteine selbst bleiben erhalten.',
  },
  chapter: {
    heading: 'Lebenskapitel',
    intro: 'Fasst zusammen, was in bestimmten Lebensabschnitten passiert ist.',
    create: 'Kapitel hinzufügen',
    loading: 'Kapitel wird geladen …',
    detailEyebrow: 'Gemeinsames Kapitel',
    startOn: 'Beginn',
    endOn: 'Ende',
    noDescription: 'Noch keine Beschreibung.',
    deleteConsequence:
      'Nur das Kapitel und seine Verknüpfungen werden gelöscht. Die enthaltenen Erinnerungen, Herzmomente und Meilensteine bleiben unverändert erhalten.',
  },
  relations: {
    heading: 'Verknüpfte gemeinsame Inhalte',
    intro:
      'Auswählbar sind ausschließlich Inhalte aus eurer gemeinsamen Story. Private Herzmomente erscheinen hier nicht.',
    loading: 'Verknüpfungen werden geladen …',
    empty: 'Noch keine Inhalte verknüpft.',
    contentFallback: 'Verknüpfter Inhalt',
    addLabel: 'Gemeinsamen Inhalt verknüpfen',
    choose: 'Inhalt auswählen',
    link: 'Verknüpfen',
    unlink: 'Verknüpfung lösen',
    noMoreTargets:
      'Alle aktuell verfügbaren gemeinsamen Story-Inhalte sind bereits verknüpft.',
    kind: {
      MEMORY: 'Erinnerung',
      HEART_MOMENT: 'Herzmoment',
      MILESTONE: 'Meilenstein',
    },
  },
  collection: {
    heading: 'Bucket Lists & Listen',
    intro:
      'Unsere Bucket Lists, kleine Geheimnisse oder Dinge, die wir nicht vergessen wollen.',
    create: 'Liste hinzufügen',
    loading: 'Liste wird geladen …',
    detailEyebrow: 'Gemeinsame Liste',
    itemCount_one: '{{count}} Eintrag',
    itemCount_other: '{{count}} Einträge',
    itemsHeading: 'Einträge',
    itemsIntro:
      'Änderungen an der Reihenfolge werden vollständig und atomar mit der aktuellen Listen-Version gespeichert.',
    newItem: 'Neuer Listeneintrag',
    newItemPlaceholder: 'Neuen Eintrag hinzufügen',
    addItem: 'Hinzufügen',
    itemTitle: 'Titel des Eintrags',
    itemsEmpty: 'Die Liste ist noch leer.',
    markDone: '„{{title}}“ als erledigt markieren',
    markOpen: '„{{title}}“ wieder als offen markieren',
    saveItem: '„{{title}}“ speichern',
    reorderItem:
      '„{{title}}“ verschieben. Ziehen oder mit den Pfeiltasten neu anordnen.',
    deleteItem: '„{{title}}“ löschen',
    reordering: 'Reihenfolge wird gespeichert …',
    deleteConsequence:
      'Die Liste und ihre eigenen Listeneinträge werden gelöscht. Andere SidebySide-Inhalte werden nicht gelöscht.',
  },
} as const;

export default m5s3;
