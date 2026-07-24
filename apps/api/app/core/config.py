import os


DEFAULT_DATABASE_URL = "postgresql+psycopg://crewplan:crewplan@postgres:5432/crewplan_lite"
DEFAULT_FRONTEND_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_frontend_origins() -> list[str]:
    origins = os.getenv("FRONTEND_ORIGINS", DEFAULT_FRONTEND_ORIGINS)
    return [origin.strip() for origin in origins.split(",") if origin.strip()]
