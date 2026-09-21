import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Research Table BRIN API")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/research_table_db"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "4a45ed24253c3a895b57da197d3b86a8f249991768d808a702a056b42a5be890")
    ACCESS_TOKEN: str = os.getenv("ACCESS_TOKEN", "research_table_local_secret_2026")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    JWT_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 7 * 24 * 3600


settings = Settings()
