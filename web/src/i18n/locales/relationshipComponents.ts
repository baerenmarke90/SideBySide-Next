const relationshipComponents = {
  partnerAvatarConnected: '{{user}} und {{partner}}',
  partnerAvatarWaiting: '{{user}} (Wartet auf Partner)',
  partnerAvatarInvite: 'Partner einladen',

  couplePresenceConnected: 'Zusammen verbunden',
  couplePresenceWaiting: 'Wartet auf Partner',
  couplePresenceOffline: 'Offline',
  couplePresenceDurationAction: 'Beziehungsdetails ansehen',
  couplePresenceYouFallback: 'Du',
  couplePresencePartnerFallback: 'Dein Partner',

  thinkingOfYouSendToPartner: 'Lieben Gruß an {{partner}} senden',
  thinkingOfYouAction: 'Ich denk an dich',
  thinkingOfYouSending: 'Wird gesendet …',
  thinkingOfYouSent: 'Gesendet!',

  visibilityShared: 'Mit Partner geteilt',
  visibilityPrivate: 'Nur für mich',
  visibilityTemporary: 'Zeitlich geteilt',
} as const;

export default relationshipComponents;
