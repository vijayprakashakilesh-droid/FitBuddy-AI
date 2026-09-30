from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_workout_model: str = "gemini-3.5-flash-lite"
    gemini_nutrition_model: str = "gemini-3.5-flash-lite"
    database_url: str = "sqlite:///./fitbuddy.db"
    APP_NAME: str = "FitBuddy - AI Fitness Plan Generator"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()