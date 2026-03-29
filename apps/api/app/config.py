from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = Path(__file__).resolve().parent.parent


def _resolve_sqlite_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    raw_path = Path(database_url[len(prefix) :])
    if raw_path.is_absolute():
        return database_url

    resolved = (_API_ROOT / raw_path).resolve()
    return f"sqlite:///{resolved.as_posix()}"


def _resolve_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    return str((_API_ROOT / path).resolve())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_API_ROOT / ".env"), extra="ignore")

    database_url: str = "sqlite:///./healthcareassistant.db"
    upload_dir: str = "./uploads"

    llm_base_url: str
    llm_api_key: str
    llm_model: str

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        self.database_url = _resolve_sqlite_url(self.database_url)
        self.upload_dir = _resolve_path(self.upload_dir)
        return self


settings = Settings()
