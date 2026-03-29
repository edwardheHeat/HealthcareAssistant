from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./healthcareassistant.db"
    upload_dir: str = "./uploads"

    llm_base_url: str
    llm_api_key: str
    llm_model: str


settings = Settings()
