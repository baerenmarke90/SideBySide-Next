"""Konfiguration aus der Umgebung.

Kein Geheimnis steht im Quellcode oder in einer eingecheckten Datei. Die
Vorgabewerte hier sind Entwicklungswerte; in Produktion müssen sie gesetzt
werden, und wo das sicherheitsrelevant ist, verweigert der Start.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Deployment(StrEnum):
    """Betriebsform. Derselbe Core, unterschiedliche Adapter."""

    CLOUD = "cloud"
    SELF_HOSTED = "self_hosted"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


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

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()
