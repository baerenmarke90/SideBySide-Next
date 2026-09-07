const m5s3 = {
  common: {
    saved: 'gespeichert',
    back: '← Zurück zu Planen',
    backToPlan: '← Zurück zu Planen',
    backToStory: '← Zurück zu Momente',
    backToMore: '← Zurück zu Mehr',
    backToCollections: '← Zurück zu Gemeinsamen Listen',
    backToPlaces: '← Zurück zu Orten',
    backToChapters: '← Zurück zu Kapiteln',
    title: 'Titel',
    description: 'Beschreibung',
    place: 'Ort',
    noPlace: 'Ohne Ort',
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
    soon: 'Bald & Geplant',
    soonIntro:
      'Was schon Form angenommen hat und als Nächstes auf euch wartet.',
    soonEmpty:
      'Noch nichts fest geplant. Sobald aus einer Idee ein konkretes Vorhaben wird, findet ihr es hier.',
    someday: 'Wünsche & Ideen',
    somedayIntro:
      'Ideen für später, die ihr gemeinsam festhalten und irgendwann weiterplanen könnt.',
    somedayEmpty:
      'Noch keine Wünsche festgehalten. Sammelt hier, was ihr irgendwann gemeinsam erleben möchtet.',
    others: 'Weitere gemeinsame Dinge',
    eyebrow: 'Gemeinsam planen',
    title: 'Eure Wünsche und Pläne',
    intro:
      'Was ihr gemeinsam vorhabt – von leisen Ideen bis zu Plänen mit einem festen Zeitpunkt.',
  },
  wish: {
    heading: 'Wünsche',
    intro:
      'Ideen für später, die ihr gemeinsam festhaltet und bei Bedarf in einen konkreten Plan verwandelt.',
    create: 'Wunsch hinzufügen',
    loading: 'Wunsch wird geladen …',
    detailEyebrow: 'Gemeinsamer Wunsch',
    planTitle: 'Titel des Plans (optional)',
    convertHeading: 'Daraus einen Plan machen',
    convertIntro:
      'Gebt eurem Wunsch einen konkreten Platz in eurer Planung. Ohne eigenen Plantitel wird der Wunschtitel übernommen.',
    convert: 'In Plan umwandeln',
    converting: 'Wird umgewandelt …',
    deleteConsequence:
      'Der Wunsch wird gelöscht. Bereits separat vorhandene Inhalte werden dadurch nicht verändert.',
    status: {
      OPEN: 'Offen',
      PLANNED: 'Als Plan weitergeführt',
      COMPLETED: 'Gemeinsam erlebt',
    },
  },
  plan: {
    heading: 'Pläne',
    intro:
      'Vom ersten Gedanken über einen Zeitpunkt bis zum gemeinsam Erlebten.',
    create: 'Plan hinzufügen',
    loading: 'Plan wird geladen …',
    detailEyebrow: 'Gemeinsamer Plan',
    lifecycleHeading: 'Wo steht ihr gerade?',
    scheduleFacts: 'Zeitpunkt und Erlebnisdatum',
    plannedStart: "Wann geht's los?",
    plannedEnd: 'Bis wann?',
    experiencedOn: 'Erlebt am',
    schedule: "Wann soll's sein?",
    reschedule: 'Zeitpunkt ändern',
    unschedule: 'Noch ohne festen Zeitpunkt',
    editAction: 'Plan bearbeiten',
    complete: 'Als erlebt abschließen',
    returnToWish: 'Zurück zum Wunsch',
    completedTitle: 'Gemeinsam geschafft',
    completedBody: 'Aus einem Plan wurde etwas, das ihr erlebt habt.',
    createMemoryFromPlan: 'Erinnerung daraus festhalten',
    deleteConsequence:
      'Der Plan wird gelöscht. Ein verknüpfter Ort oder andere eigenständige Inhalte bleiben erhalten.',
    addNewPlace: '+ Neuen Ort anlegen',
    newPlaceHeading: 'Neuer Ort',
    newPlaceSave: 'Ort erstellen',
    newPlaceSaving: 'Ort wird erstellt …',
    newPlaceCancel: 'Ortsauswahl behalten',
    status: {
      IDEA: 'Idee',
      PLANNED: 'Das haben wir vor',
      COMPLETED: 'Gemeinsam erlebt',
    },
  },
  place: {
    heading: 'Orte',
    intro:
      'Orte, die zu euren Plänen und gemeinsamen Momenten gehören. Ein Name reicht; Adresse und Koordinaten bleiben optional.',
    emptyOverview:
      'Noch keine gemeinsamen Orte gespeichert. Haltet hier Orte fest, die für eure Pläne oder Momente wichtig sind.',
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
      'eimir. verwendet hier keine Karten- oder Geocoding-Dienste. Der gespeicherte Ort bleibt unabhängig davon nutzbar.',
    noAddress: 'Keine Adresse hinterlegt',
    deleteConsequence:
      'Der Ort und seine Verknüpfungen werden gelöscht. Erinnerungen, Herzmomente und Meilensteine selbst bleiben erhalten.',
  },
  chapter: {
    heading: 'Kapitel',
    intro: 'Kapitel bündeln eure gemeinsamen Erinnerungen und Meilensteine.',
    create: 'Kapitel hinzufügen',
    addMoreDetails: 'Beschreibung, Zeitraum und Ort hinzufügen (optional)',
    loading: 'Kapitel wird geladen …',
    detailEyebrow: 'Gemeinsames Kapitel',
    startOn: 'Beginn',
    endOn: 'Ende',
    noDescription: 'Noch keine Beschreibung.',
    deleteConsequence:
      'Nur das Kapitel und seine Verknüpfungen werden gelöscht. Die enthaltenen Erinnerungen, Herzmomente und Meilensteine bleiben unverändert erhalten.',
  },
  relations: {
    heading: 'Was gehört zu diesem Kapitel?',
    intro:
      'Auswählbar sind ausschließlich Inhalte aus eurer gemeinsamen Story. Private Herzmomente erscheinen hier nicht.',
    loading: 'Verknüpfungen werden geladen …',
    empty: 'Hier gehört noch kein Moment dazu.',
    contentFallback: 'Verknüpfter Inhalt',
    addLabel: 'Moment hinzufügen',
    choose: 'Inhalt auswählen',
    link: 'Verknüpfen',
    unlink: 'Aus Kapitel entfernen',
    noMoreTargets:
      'Alle aktuell verfügbaren gemeinsamen Story-Inhalte sind bereits verknüpft.',
    kind: {
      MEMORY: 'Erinnerung',
      HEART_MOMENT: 'Herzmoment',
      MILESTONE: 'Meilenstein',
    },
  },
  collection: {
    heading: 'Gemeinsame Listen',
    intro:
      'Listen für Dinge, die ihr gemeinsam im Blick behalten, sortieren und abhaken möchtet.',
    emptyOverview:
      'Noch keine gemeinsame Liste. Legt eine an für Dinge, die ihr zusammen im Blick behalten möchtet.',
    create: 'Liste hinzufügen',
    loading: 'Liste wird geladen …',
    detailEyebrow: 'Gemeinsame Liste',
    itemCount_one: '{{count}} Eintrag',
    itemCount_other: '{{count}} Einträge',
    itemsHeading: 'Einträge',
    itemsIntro:
      'Gemeinsam ergänzen, abhaken und in die Reihenfolge bringen, die für euch passt.',
    newItem: 'Neuer Listeneintrag',
    newItemPlaceholder: 'Neuen Eintrag hinzufügen',
    addItem: 'Hinzufügen',
    itemTitle: 'Titel des Eintrags',
    itemsEmpty:
      'Noch nichts auf dieser Liste. Fügt den ersten gemeinsamen Eintrag hinzu.',
    markDone: '„{{title}}“ als erledigt markieren',
    markOpen: '„{{title}}“ wieder als offen markieren',
    saveItem: '„{{title}}“ speichern',
    reorderItem:
      '„{{title}}“ verschieben. Ziehen oder mit den Pfeiltasten neu anordnen.',
    deleteItem: '„{{title}}“ löschen',
    reordering: 'Reihenfolge wird gespeichert …',
    deleteConsequence:
      'Die Liste und ihre eigenen Listeneinträge werden gelöscht. Andere eimir.-Inhalte werden nicht gelöscht.',
  },
};

export default m5s3;
