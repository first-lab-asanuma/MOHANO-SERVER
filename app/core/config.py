from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MOHANO_", extra="ignore")

    app_name: str = "MOHANO Server"
    environment: str = "local"
    api_v1_prefix: str = "/v1"
    database_url: str = "mysql+pymysql://mohano:0000@127.0.0.1:3306/mohano?charset=utf8mb4"
    jwt_secret_key: str = "replace-this-before-running"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    google_web_client_id: str = ""
    cors_origins_raw: str = ""
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    object_storage_endpoint: str = "http://127.0.0.1:9000"
    object_storage_public_endpoint: str = ""
    object_storage_access_key: str = "mohano"
    object_storage_secret_key: str = "00000000"
    object_storage_bucket: str = "mohano-profile-images"
    object_storage_region: str = "us-east-1"
    object_storage_upload_url_expire_seconds: int = 600
    object_storage_read_url_expire_seconds: int = 900
    profile_photo_max_bytes: int = 10 * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
