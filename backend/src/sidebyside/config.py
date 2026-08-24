"""Konfiguration aus der Umgebung.

Kein Geheimnis steht im Quellcode oder in einer eingecheckten Datei. Die
Vorgabewerte hier sind Entwicklungswerte; in Produktion müssen sie gesetzt
werden, und wo das sicherheitsrelevant ist, verweigert der Start.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Self

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

    media_root: str = "./data/media"

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

    mail_transport: MailTransport = MailTransport.LOG
    mail_from: str = "no-reply@localhost"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = True

    @field_validator("bootstrap_token", mode="before")
    @classmethod
    def empty_bootstrap_token_is_unset(cls, value: object) -> object | None:
        return None if value == "" else value

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    def oidc_connection(self, connection_id: str) -> OidcConnection | None:
        for verbindung in self.oidc_connections:
            if verbindung.id == connection_id:
                return verbindung
        return None

    @model_validator(mode="after")
    def production_hosts_are_restricted(self) -> Self:
        if self.is_production and (not self.allowed_hosts or "*" in self.allowed_hosts):
            raise ValueError("Production requires an explicit SBS_ALLOWED_HOSTS list without '*'.")
        if self.bootstrap_token is not None:
            secret = self.bootstrap_token.get_secret_value()
            if len(secret) < 32:
                raise ValueError("SBS_BOOTSTRAP_TOKEN must contain at least 32 characters.")
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
