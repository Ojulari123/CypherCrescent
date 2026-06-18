from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    NPGUSER: str
    NPGPASSWORD: str
    NPGDB: str
    NPGHOST: str
    NPGPORT: int = 5432

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str = ""
    EMAIL_VERIFY_EXPIRE_MINUTES: int = 60
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60
    OTP_EXPIRE_MINUTES: int = 10

    CYPHER_CRESCENT_CLOUDINARY_CLOUD_NAME: str
    CYPHER_CRESCENT_CLOUDINARY_API_KEY: str
    CYPHER_CRESCENT_CLOUDINARY_API_SECRET: str

    COINGECKO_API_KEY: str
    COINGECKO_BASE_URL: str
    REDIS_URL: str
    MARKET_CACHE_TTL: int = 60
    SEARCH_CACHE_TTL: int = 600
    CHART_CACHE_TTL: int = 300

    FRONTEND_URL: str = "http://localhost:3000"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.NPGUSER}:"
            f"{self.NPGPASSWORD}@"
            f"{self.NPGHOST}:"
            f"{self.NPGPORT}/"
            f"{self.NPGDB}"
            "?sslmode=require"
        )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()