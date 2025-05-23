from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_name: str
    endpoint_url: str
    region: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
