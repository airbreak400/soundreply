from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "myinstants_bot"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    class Config:
        env_file = ".env"


settings = Settings()