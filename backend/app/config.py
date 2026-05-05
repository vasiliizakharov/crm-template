from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Service CRM"
    app_env: str = "production"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7
    cors_origins: str = "*"
    admin_email: str = "admin@example.com"
    # No default password — must be supplied via env, otherwise bootstrap will fail loudly.
    admin_password: str = ""
    admin_full_name: str = "Administrator"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
