import os


DEFAULT_DATABASE_URL = "postgresql+psycopg://crewplan:crewplan@postgres:5432/crewplan_lite"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
