from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    POSTGRES_DB: str = 'url_shortener'
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_HOST: str = 'db'
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = 'postgresql+psycopg2://postgres:postgres@db:5432/url_shortener'

    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379
    REDIS_URL: str = 'redis://redis:6379/0'

    SECRET_KEY: str = 'super-secret-key-change-me'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    BASE_SHORT_URL: str = 'http://localhost:8088'
    UNUSED_LINKS_RETENTION_DAYS: int = 30


settings = Settings()
