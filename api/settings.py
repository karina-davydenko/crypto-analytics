from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    db_pool_min_size: int = 2
    db_pool_max_size: int = 10

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")


# type: ignore[call-arg] — ложное срабатывание Pylance:
# BaseSettings заполняет database_url из .env через метакласс,
# но статический анализатор этого не видит и требует аргумент явно.
settings = Settings()  # type: ignore[call-arg]
