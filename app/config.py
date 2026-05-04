from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    llm_model: str = "gemini/gemini-2.5-flash"

    pubmed_api_key: str = ""
    pubmed_email: str = ""

    log_level: str = "INFO"


settings = Settings()
