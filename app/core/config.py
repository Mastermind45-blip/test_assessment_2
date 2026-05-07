from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Database
    database_url: str = Field(default="DATABASE_URL")

    # API Keys
    openweather_api_key: str = Field(default="", alias="OPENWEATHER_API_KEY")
    weatherapi_key: str = Field(default="", alias="WEATHERAPI_KEY")

    # Application
    app_name: str = "Weather Assessment API"
    debug: bool = Field(default=False, alias="DEBUG")

    # Rate limiting
    rate_limit_per_minute: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
