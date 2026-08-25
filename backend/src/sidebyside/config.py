"""Konfiguration aus der Umgebung.

Kein Geheimnis steht im Quellcode oder in einer eingecheckten Datei. Die
Vorgabewerte hier sind Entwicklungswerte; in Produktion müssen sie gesetzt
werden, und wo das sicherheitsrelevant ist, verweigert der Start.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Self
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Deployment(StrEnum):
    """Betriebsform. Derselbe Core, unterschiedliche Adapter."""

    CLOUD = "cloud"
    SELF_HOSTED = "self_hosted"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class MediaStoreBackend(StrEnum):
    """Welcher Infrastrukturadapter Medien physisch ablegt."""

    LOCAL = "local"
    S3 = "s3"


class MailTransport(StrEnum):
    """Wie ausgehende Post das Haus verlaesst.

    `LOG` ist der Entwicklungsweg und schreibt die Nachricht ins Log -
    mitsamt Einmal-Token. In Produktion ist er deshalb nicht zulaessig.
    """

    LOG = "log"
    SMTP = "smtp"


class OidcConnection(BaseModel):
    """Eine konfigurierte OIDC-Verbindung.

    Der `id` waehlt sie im Pfad aus; er ist frei vergeben und hat keine
    Bedeutung fuer das Protokoll. Ein Anbieter ist damit eine Zeile
    Konfiguration und kein Sonderfall im Code - Pocket ID ebenso wie jeder
    andere.
    """

    id: str = Field(min_length=1, max_length=64)
    issuer: str = Field(min_length=1, max_length=512)
    client_id: str = Field(min_length=1, max_length=256)
    client_secret: SecretStr | None = None
    redirect_uri: str = Field(min_length=1, max_length=512)
    scopes: str = "openid email profile"

    @field_validator("issuer")
    @classmethod
    def issuer_is_https(cls, value: str) -> str:
        """Ohne TLS waere die gesamte Pruefkette wertlos.

        Discovery-Dokument, JWKS und Token-Endpunkt kaemen dann von einem
        Gegenueber, das jeder auf dem Weg ersetzen kann.
        """
        adresse = value.rstrip("/")
        if not adresse.startswith("https://"):
            raise ValueError("Ein OIDC-Issuer muss mit https:// beginnen.")
        return adresse


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SBS_", env_file=".env", extra="ignore")

    environment: Environment = Environment.DEVELOPMENT
    deployment: Deployment = Deployment.SELF_HOSTED

    # Kein SQLite-Rückfall: das Datenmodell nutzt PostgreSQL-Eigenschaften,
    # und ein zweiter Dialekt im Test prüft nicht, was in Produktion läuft.
    database_url: str = Field(
        default="postgresql+psycopg://sidebyside:sidebyside@localhost:5432/sidebyside"
    )
    database_echo: bool = False

    media_store: MediaStoreBackend = MediaStoreBackend.LOCAL
    media_root: str = "./data/media"
    s3_endpoint: str = ""
    s3_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_session_token: SecretStr | None = None

    # Runtime-Killswitch fuer den Video-Slice. Das reproduzierbare Docker-
    # Image behaelt ffmpeg/ffprobe installiert; false garantiert aber, dass
    # die Anwendung keine Videoverarbeitung startet und neue Video-Uploads
    # fail-closed ablehnt. Bilder und der restliche Dienst bleiben nutzbar.
    ffmpeg_enabled: bool = True

    # Keyset-Cursor verlassen den Server als opake, HMAC-geschuetzte Tokens.
    # Ein installationsspezifischer Schluessel verhindert Manipulation und
    # darf nicht aus DB-Passwort, Bootstrap-Token oder anderen Secrets
    # abgeleitet werden. Entwicklung/Test nutzen nur einen lokalen Fallback.
    cursor_signing_key: SecretStr | None = None

    # In Produktion entscheidet der Host-Header mit darueber, fuer welche
    # oeffentliche Adresse eine Antwort bestimmt ist. Ein offenes "*" wuerde
    # DNS-Rebinding und versehentlich erreichbare Nebenadressen zulassen.
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    # Nur fuer die einmalige Inbetriebnahme einer frischen Self-Hosted-
    # Instanz. SecretStr verhindert, dass ein Settings-Repr den Wert zeigt.
    bootstrap_token: SecretStr | None = None

    # Die oeffentliche Adresse dieser Instanz. Sie steht in jedem Magic
    # Link; aus einem Request-Header darf sie nicht kommen, sonst baut ein
    # gefaelschter Host-Header den Link auf einen fremden Server um.
    public_base_url: str = "http://localhost:8000"

    # Als JSON-Liste in einer Umgebungsvariablen, damit mehrere Anbieter
    # ohne Codeaenderung nebeneinander stehen koennen.
    oidc_connections: list[OidcConnection] = Field(default_factory=list)

    # Die Relying Party ist die Anwendung, fuer die ein Passkey gilt. Ohne
    # eigenen Wert wird sie aus der oeffentlichen Adresse abgeleitet - ein
    # Passkey fuer "app.example" darf auf "boese.example" nicht gelten.
    webauthn_rp_id: str = ""
    webauthn_rp_name: str = "SideBySide"
    webauthn_origins: list[str] = Field(default_factory=list)

    mail_transport: MailTransport = MailTransport.LOG
    mail_from: str = "no-reply@localhost"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = True

    @field_validator(
        "bootstrap_token",
        "cursor_signing_key",
        "s3_access_key_id",
        "s3_secret_access_key",
        "s3_session_token",
        mode="before",
    )
    @classmethod
    def empty_secret_is_unset(cls, value: object) -> object | None:
        return None if value == "" else value

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    @property
    def cursor_signing_secret(self) -> bytes:
        if self.cursor_signing_key is not None:
            return self.cursor_signing_key.get_secret_value().encode("utf-8")
        if self.is_production:
            raise RuntimeError("Production cursor signing key is missing.")
        return b"sidebyside-development-only-cursor-signing-key"

    @property
    def relying_party_id(self) -> str:
        """Die RP ID: der Host der oeffentlichen Adresse, sofern nicht gesetzt."""
        if self.webauthn_rp_id:
            return self.webauthn_rp_id
        return urlsplit(self.public_base_url).hostname or "localhost"

    @property
    def relying_party_origins(self) -> list[str]:
        """Die Herkuenfte, die eine Ceremony vorweisen darf."""
        if self.webauthn_origins:
            return self.webauthn_origins
        return [self.public_base_url.rstrip("/")]

    def oidc_connection(self, connection_id: str) -> OidcConnection | None:
        for verbindung in self.oidc_connections:
            if verbindung.id == connection_id:
                return verbindung
        return None

    @model_validator(mode="after")
    def media_store_is_complete(self) -> Self:
        if self.media_store is MediaStoreBackend.LOCAL:
            return self

        required = {
            "SBS_S3_ENDPOINT": self.s3_endpoint,
            "SBS_S3_REGION": self.s3_region,
            "SBS_S3_BUCKET": self.s3_bucket,
            "SBS_S3_ACCESS_KEY_ID": self.s3_access_key_id,
            "SBS_S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"S3 media store requires: {', '.join(missing)}.")

        endpoint = urlsplit(self.s3_endpoint.rstrip("/"))
        if (
            endpoint.scheme not in {"http", "https"}
            or not endpoint.hostname
            or endpoint.username is not None
            or endpoint.password is not None
            or endpoint.query
            or endpoint.fragment
            or endpoint.path not in {"", "/"}
        ):
            raise ValueError(
                "SBS_S3_ENDPOINT must be an http(s) origin without credentials or path."
            )
        if "/" in self.s3_bucket:
            raise ValueError("SBS_S3_BUCKET must be a bucket name, not a path.")
        return self

    @model_validator(mode="after")
    def production_hosts_are_restricted(self) -> Self:
        if self.is_production and (not self.allowed_hosts or "*" in self.allowed_hosts):
            raise ValueError("Production requires an explicit SBS_ALLOWED_HOSTS list without '*'.")
        if self.bootstrap_token is not None:
            secret = self.bootstrap_token.get_secret_value()
            if len(secret) < 32:
                raise ValueError("SBS_BOOTSTRAP_TOKEN must contain at least 32 characters.")
        if self.cursor_signing_key is not None:
            cursor_secret = self.cursor_signing_key.get_secret_value()
            if len(cursor_secret) < 32:
                raise ValueError("SBS_CURSOR_SIGNING_KEY must contain at least 32 characters.")
        if self.is_production and self.cursor_signing_key is None:
            raise ValueError("Production requires SBS_CURSOR_SIGNING_KEY.")
        return self

    @model_validator(mode="after")
    def production_sends_real_mail(self) -> Self:
        """In Produktion kein Log-Versand und keine Klartext-Links im Log.

        Ein Fehlstart ist hier die freundlichere Antwort: der stille
        Gegenentwurf waere eine Instanz, die Anmeldenachweise ins Log
        schreibt, und das faellt niemandem auf.
        """
        if self.is_production and self.mail_transport is not MailTransport.SMTP:
            raise ValueError("Production requires SBS_MAIL_TRANSPORT=smtp.")
        if self.is_production and not self.public_base_url.startswith("https://"):
            raise ValueError("Production requires an https SBS_PUBLIC_BASE_URL.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
