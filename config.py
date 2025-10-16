from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str
    FAQ_ENDPOINT: str

    class Config:
        env_file = ".env"

settings = Settings()
