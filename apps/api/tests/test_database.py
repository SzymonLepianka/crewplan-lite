from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine
from app.modules.planning import models  # noqa: F401


EXPECTED_TABLES = {
    "projects",
    "skills",
    "tasks",
    "task_required_skills",
    "task_dependencies",
    "crews",
    "crew_skills",
    "crew_availabilities",
    "planning_locks",
    "schedule_runs",
    "task_assignments",
}


def test_database_connection_is_available() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("select 1"))

    assert result.scalar_one() == 1


def test_planning_tables_are_registered_in_metadata() -> None:
    assert EXPECTED_TABLES.issubset(Base.metadata.tables)


def test_planning_tables_exist_after_migrations() -> None:
    inspector = inspect(engine)

    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
