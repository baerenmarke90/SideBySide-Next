from pathlib import Path
import re

app_path = Path("web/src/App.tsx")
app = app_path.read_text(encoding="utf-8")

config_import = "import { loadReferenceClientConfig } from './client/config';\n"
entry_import = "import {\n  readSensitiveEntryToken,\n  stripSensitiveEntryToken,\n} from './client/entryToken';\n"
if "./client/entryToken" not in app:
    if config_import not in app:
        raise SystemExit("Config import anchor not found")
    app = app.replace(config_import, config_import + entry_import, 1)

old_reference_import = "import {\n  createReferenceApis,\n  loadAuthorizedImage,\n  signIn,\n} from './client/referenceFlow';\n"
new_reference_import = "import {\n  createReferenceApis,\n  loadAuthorizedImage,\n} from './client/referenceFlow';\n"
app = app.replace(old_reference_import, new_reference_import, 1)

brand_import = "import { Brand } from './components/Brand';\n"
identity_import = "import { IdentityEntry } from './components/IdentityEntry';\n"
if identity_import not in app:
    if brand_import not in app:
        raise SystemExit("Brand import anchor not found")
    app = app.replace(brand_import, brand_import + identity_import, 1)

app = re.sub(
    r"function readableError\(error: unknown, fallback: string\): string \{.*?\n\}\n\n(?=function SpaceContextGate)",
    "",
    app,
    count=1,
    flags=re.S,
)
app, login_count = re.subn(
    r"function LoginScreen\(\{.*?\n\}\n\n(?=function StoryPage)",
    "",
    app,
    count=1,
    flags=re.S,
)
if login_count != 1 and "function LoginScreen" in app:
    raise SystemExit("LoginScreen removal failed")

state_anchor = "  const [spaceId, setSpaceId] = useState<string | null>(null);\n"
state_replacement = state_anchor + """  const [entryToken] = useState(() =>
    readSensitiveEntryToken(window.location.pathname, window.location.search),
  );

  useEffect(() => {
    if (!entryToken) return;
    window.history.replaceState(
      window.history.state,
      '',
      stripSensitiveEntryToken(window.location.search),
    );
  }, [entryToken]);
"""
if "const [entryToken]" not in app:
    if state_anchor not in app:
        raise SystemExit("App state anchor not found")
    app = app.replace(state_anchor, state_replacement, 1)

app, mutation_count = re.subn(
    r"  const loginMutation = useMutation\(\{.*?\n  \}\);\n\n(?=  function logout)",
    "",
    app,
    count=1,
    flags=re.S,
)
if mutation_count != 1 and "const loginMutation" in app:
    raise SystemExit("Login mutation removal failed")

old_signed_out = """  if (!tokens) {
    return (
      <>
        <ThemeControl />
        <LoginScreen
          onLogin={(email, password) =>
            loginMutation.mutate({ email, password })
          }
          pending={loginMutation.isPending}
          error={loginMutation.error}
        />
      </>
    );
  }
"""
new_signed_out = """  if (!tokens) {
    return (
      <>
        <ThemeControl />
        <IdentityEntry
          apiBaseUrl={config.apiBaseUrl}
          entryToken={entryToken}
          onSession={(session) => {
            setSpaceId(null);
            setTokens(session.tokens);
            queryClient.clear();
          }}
        />
      </>
    );
  }
"""
if old_signed_out in app:
    app = app.replace(old_signed_out, new_signed_out, 1)
elif "<IdentityEntry" not in app:
    raise SystemExit("Signed-out render anchor not found")

app_path.write_text(app, encoding="utf-8")

component_path = Path("web/src/components/IdentityEntry.tsx")
component = component_path.read_text(encoding="utf-8")
component = component.replace(
    '<section className="login-card" aria-labelledby="identity-entry-heading">',
    '<section className="login-card" aria-label={t(\'identity.entryAria\')}>',
    1,
)
old_success = """              <>
                <UiState
                  kind="success"
                  title={t('identity.verificationCompleteTitle')}
                  body={t('identity.verificationCompleteBody')}
                />
                <button
                  type="button"
                  onClick={() => setVerificationDismissed(true)}
                >
                  {t('identity.backToSignIn')}
                </button>
              </>"""
new_success = """              <>
                <div className="inline-message inline-message-success" role="status">
                  <strong>{t('identity.verificationCompleteTitle')}</strong>
                  <span>{t('identity.verificationCompleteBody')}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setVerificationDismissed(true)}
                >
                  {t('identity.backToSignIn')}
                </button>
              </>"""
if old_success in component:
    component = component.replace(old_success, new_success, 1)
component_path.write_text(component, encoding="utf-8")

locale_path = Path("web/src/i18n/locales/de.ts")
locale = locale_path.read_text(encoding="utf-8")
if "  identity: {" not in locale:
    anchor = "  login: {\n"
    identity = """  identity: {
    entryAria: 'Zugang zu SideBySide',
    invitationEyebrow: 'Einladung zu SideBySide',
    invitationTitle: 'Ihr möchtet SideBySide gemeinsam nutzen',
    invitationBody:
      'Melde dich mit deinem bestehenden Konto an oder erstelle über diese Einladung ein neues Konto.',
    createAccount: 'Neues Konto erstellen',
    registerTitle: 'Dein Konto erstellen',
    registerBody:
      'Dein neues Konto wird direkt mit dem eingeladenen gemeinsamen Bereich verbunden.',
    displayName: 'Anzeigename',
    registerSubmit: 'Konto erstellen und beitreten',
    registerPending: 'Konto wird erstellt …',
    haveAccount: 'Ich habe bereits ein Konto',
    invitationMissing: 'Diese Einladung ist nicht mehr verfügbar.',
    forgotPassword: 'Passwort vergessen?',
    newPassword: 'Neues Passwort',
    passwordConfirmation: 'Passwort wiederholen',
    passwordMismatch: 'Die beiden Passwörter stimmen nicht überein.',
    recoveryEyebrow: 'Kontozugang wiederherstellen',
    recoveryTitle: 'Neues Passwort festlegen',
    recoveryBody:
      'Lege ein neues Passwort fest. Aus Sicherheitsgründen werden deine bisherigen Sitzungen beendet.',
    recoverySave: 'Passwort speichern und anmelden',
    recoverySaving: 'Passwort wird gespeichert …',
    recoveryMissing: 'Dieser Wiederherstellungslink ist nicht mehr verfügbar.',
    recoveryRequestEyebrow: 'Kontozugang wiederherstellen',
    recoveryRequestTitle: 'Passwort zurücksetzen',
    recoveryRequestBody:
      'Gib deine E-Mail-Adresse ein. Wenn dafür ein lokales SideBySide-Konto existiert, erhältst du einen zeitlich begrenzten Link.',
    recoveryRequestSubmit: 'Wiederherstellungslink anfordern',
    recoveryRequestPending: 'Anfrage wird gesendet …',
    mailRequestedTitle: 'Prüfe dein Postfach',
    mailRequestedBody:
      'Wenn die Adresse für diesen Zugang verwendet werden kann, wurde ein zeitlich begrenzter Link gesendet.',
    backToSignIn: 'Zur Anmeldung',
    useMagicLink: 'Anmeldelink per E-Mail',
    magicLinkEyebrow: 'Anmelden ohne Passwort',
    magicLinkTitle: 'Anmeldelink anfordern',
    magicLinkBody:
      'Wir senden dir einen einmal verwendbaren, zeitlich begrenzten Link, sofern die Adresse für diese Anmeldeart verwendet werden kann.',
    magicLinkRequestSubmit: 'Anmeldelink anfordern',
    magicLinkRequestPending: 'Anfrage wird gesendet …',
    magicLinkOpening: 'Anmeldelink wird geprüft …',
    magicLinkFailedTitle: 'Dieser Anmeldelink funktioniert nicht mehr.',
    magicLinkFailedBody:
      'Fordere bei Bedarf einen neuen Anmeldelink an oder melde dich mit deinem Passwort an.',
    verificationOpening: 'E-Mail-Adresse wird bestätigt …',
    verificationCompleteTitle: 'E-Mail-Adresse bestätigt',
    verificationCompleteBody: 'Deine E-Mail-Adresse ist jetzt bestätigt.',
    verificationFailedTitle: 'Die E-Mail-Adresse konnte nicht bestätigt werden.',
    verificationFailedBody:
      'Der Bestätigungslink ist möglicherweise abgelaufen oder wurde bereits verwendet.',
  },
"""
    if anchor not in locale:
        raise SystemExit("Login locale anchor not found")
    locale = locale.replace(anchor, identity + anchor, 1)
locale_path.write_text(locale, encoding="utf-8")
