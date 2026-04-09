from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://affluence:affluence_secret@db:5432/affluence"
    openagenda_key: str = ""
    datatourisme_key: str = ""
    openweathermap_key: str = ""
    rapidapi_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    refresh_secret: str = "change-me-in-production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
