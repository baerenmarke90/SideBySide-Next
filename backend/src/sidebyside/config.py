"""Load configuration from the environment.

No secret is stored in source code or a committed file. The defaults here are
development values; production must override them, and startup fails closed
where a missing value would be security-relevant.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Deployment(StrEnum):
    """Deployment mode. The same core uses different adapters."""

    CLOUD = "cloud"
    SELF_HOSTED = "self_hosted"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class MediaStoreBackend(StrEnum):
    """Infrastructure adapter used to store media physically."""

    LOCAL = "local"
    S3 = "s3"


class MailTransport(StrEnum):
    """How outgoing mail leaves the application.

    ``LOG`` is the development path and writes the message to the log,
    including its one-time token. It is therefore forbidden in production.

    ``NONE`` explicitly disables mail delivery. Mail-dependent authentication
    flows are then unavailable and report that condition instead of issuing a
    link that can never be delivered. Password, passkey, and OIDC sign-in remain
    available. The distinction from ``LOG`` is critical: ``NONE`` never lets a
    token leave the system, while ``LOG`` writes valid one-time tokens to every
    configured log sink.
    """

    LOG = "log"
    SMTP = "smtp"
    NONE = "none"


class OidcConnection(BaseModel):
    """A configured OIDC connection.

    ``id`` selects the connection in the path; it is freely assigned and has no
    protocol meaning. A provider is therefore configuration rather than a code
    special case, including Pocket ID.
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
        """Without TLS the entire verification chain would be worthless.

        The discovery document, JWKS, and token endpoint would otherwise come
        from a peer that anyone on the path could replace.
        """
        address = value.rstrip("/")
        if not address.startswith("https://"):
            raise ValueError("An OIDC issuer must start with https://.")
        return address


# The default points to the database from ``deploy/docker-compose.dev.yml``.
# It lives here once because two configurations need it and divergence between
# the two would otherwise be easy to miss.
DEFAULT_DATABASE_URL = "postgresql+psycopg://sidebyside:sidebyside@localhost:5432/sidebyside"


def _database_url_is_usable(value: str) -> str:
    """An empty environment value is an error, not a request for the default."""
    if not value.strip():
        raise ValueError("SBS_DATABASE_URL is empty.")
    return value


_DatabaseUrl = Annotated[str, AfterValidator(_database_url_is_usable)]


class DatabaseSettings(BaseSettings):
    """Database connection only, for paths that do not run the application.

    A migration needs the database and nothing else. Loading the full
    ``Settings`` would make ``alembic upgrade head`` depend on cursor-key,
    SMTP, and public-URL validation that has nothing to do with the schema,
    potentially failing before the first revision runs.

    Deliberately neither a base class nor subtype of ``Settings``: inheritance
    would make both configurations converge again after the next extension.
    """

    model_config = SettingsConfigDict(env_prefix="SBS_", env_file=".env", extra="ignore")

    database_url: _DatabaseUrl = Field(default=DEFAULT_DATABASE_URL)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SBS_", env_file=".env", extra="ignore")

    environment: Environment = Environment.DEVELOPMENT
    deployment: Deployment = Deployment.SELF_HOSTED

    # No SQLite fallback: the data model uses PostgreSQL properties, and a
    # second test dialect would not verify what actually runs in production.
    database_url: _DatabaseUrl = Field(default=DEFAULT_DATABASE_URL)
    database_echo: bool = False

    media_store: MediaStoreBackend = MediaStoreBackend.LOCAL
    media_root: str = "./data/media"
    s3_endpoint: str = ""
    s3_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_session_token: SecretStr | None = None

    # Keyset cursors leave the server as opaque HMAC-protected tokens. An
    # installation-specific key prevents manipulation and must not be derived
    # from the database password, bootstrap token, or other secrets.
    # Development and test use a local fallback only.
    cursor_signing_key: SecretStr | None = None

    # In production the Host header helps determine the public address for a
    # response. An open "*" would allow DNS rebinding and accidentally
    # reachable alternate addresses.
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    # Used only for one-time initialization of a fresh self-hosted instance.
    # SecretStr prevents a Settings repr from exposing the value.
    bootstrap_token: SecretStr | None = None

    # Public address of this instance. It appears in every magic link and must
    # not come from a request header; otherwise a forged Host header could make
    # the link point to an attacker-controlled server.
    public_base_url: str = "http://localhost:8000"

    # JSON list in an environment variable so multiple providers can coexist
    # without code changes.
    oidc_connections: list[OidcConnection] = Field(default_factory=list)

    # The relying party is the application for which a passkey is valid. When
    # unset it is derived from the public address; a passkey for "app.example"
    # must not be valid for "evil.example".
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
        """RP ID, defaulting to the host of the public address."""
        if self.webauthn_rp_id:
            return self.webauthn_rp_id
        return urlsplit(self.public_base_url).hostname or "localhost"

    @property
    def relying_party_origins(self) -> list[str]:
        """Origins that may prove a ceremony."""
        if self.webauthn_origins:
            return self.webauthn_origins
        return [self.public_base_url.rstrip("/")]

    def oidc_connection(self, connection_id: str) -> OidcConnection | None:
        for connection in self.oidc_connections:
            if connection.id == connection_id:
                return connection
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
        """Forbid log delivery and plaintext links in production logs.

        Failing startup is safer than silently running an instance that writes
        authentication proofs to logs.

        Only ``LOG`` is forbidden. An instance without mail delivery is a valid
        deployment mode: it sets ``NONE`` and explicitly gives up the
        mail-dependent sign-in paths. Production must not write valid one-time
        tokens to a log.
        """
        if self.is_production and self.mail_transport is MailTransport.LOG:
            raise ValueError(
                "Production requires SBS_MAIL_TRANSPORT=smtp or SBS_MAIL_TRANSPORT=none."
            )
        if self.is_production and not self.public_base_url.startswith("https://"):
            raise ValueError("Production requires an https SBS_PUBLIC_BASE_URL.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
