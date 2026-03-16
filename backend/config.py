from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./shortener.db"

    class Config:
        env_file = ".env"


settings = Settings()
