from datetime import date

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.modules.planning.models import Project
from app.seed.demo_data import DEMO_PROJECT_NAME, seed_demo_data


def _seed_demo_project() -> int:
    with SessionLocal() as session:
        project = seed_demo_data(session)
        return project.id


def test_list_projects_returns_demo_project() -> None:
    _seed_demo_project()
    client = TestClient(app)

    response = client.get("/api/projects")

    assert response.status_code == 200
    projects = response.json()
    assert any(project["name"] == DEMO_PROJECT_NAME for project in projects)


def test_get_project_returns_project_details() -> None:
    project_id = _seed_demo_project()
    client = TestClient(app)

    response = client.get(f"/api/projects/{project_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": project_id,
        "name": DEMO_PROJECT_NAME,
        "start_date": "2026-08-03",
        "description": "Projekt demo pokazujący zadania, kwalifikacje, ekipy i zależności planistyczne.",
    }


def test_get_planning_data_returns_tasks_crews_skills_and_dependencies() -> None:
    project_id = _seed_demo_project()
    client = TestClient(app)

    response = client.get(f"/api/projects/{project_id}/planning-data")

    assert response.status_code == 200
    planning_data = response.json()

    assert planning_data["project"]["name"] == DEMO_PROJECT_NAME
    assert {task["code"] for task in planning_data["tasks"]} == {"T-001", "T-002", "T-003", "T-004", "T-005"}
    assert {crew["code"] for crew in planning_data["crews"]} == {"C-001", "C-002", "C-003"}
    assert {skill["code"] for skill in planning_data["skills"]} >= {"safety", "earthworks", "electrical", "asphalt"}
    assert len(planning_data["dependencies"]) == 4
    assert planning_data["planning_locks"] == []

    installation_task = next(task for task in planning_data["tasks"] if task["code"] == "T-003")
    assert installation_task["name"] == "Montaż kanału technologicznego"
    assert installation_task["required_skill_codes"] == ["earthworks", "electrical"]


def test_get_project_returns_404_for_missing_project() -> None:
    client = TestClient(app)

    response = client.get("/api/projects/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Projekt nie istnieje"}


def test_create_schedule_run_persists_solver_result() -> None:
    project_id = _seed_demo_project()
    client = TestClient(app)

    response = client.post(f"/api/projects/{project_id}/schedule-runs")

    assert response.status_code == 201
    schedule_run = response.json()
    assert schedule_run["project_id"] == project_id
    assert schedule_run["status"] == "OPTIMAL"
    assert schedule_run["runtime_ms"] >= 0
    assert schedule_run["objective_value"] is not None
    assert schedule_run["total_lateness_days"] is not None
    assert schedule_run["project_finish_day"] is not None
    assert {assignment["task_code"] for assignment in schedule_run["assignments"]} == {
        "T-001",
        "T-002",
        "T-003",
        "T-004",
        "T-005",
    }


def test_get_schedule_run_returns_persisted_assignments() -> None:
    project_id = _seed_demo_project()
    client = TestClient(app)
    created_run = client.post(f"/api/projects/{project_id}/schedule-runs").json()

    response = client.get(f"/api/projects/{project_id}/schedule-runs/{created_run['id']}")

    assert response.status_code == 200
    schedule_run = response.json()
    assert schedule_run["id"] == created_run["id"]
    assert len(schedule_run["assignments"]) == 5
    assert all(assignment["start_day"] < assignment["end_day"] for assignment in schedule_run["assignments"])


def test_get_latest_schedule_run_returns_newest_run() -> None:
    project_id = _seed_demo_project()
    client = TestClient(app)
    first_run = client.post(f"/api/projects/{project_id}/schedule-runs").json()
    second_run = client.post(f"/api/projects/{project_id}/schedule-runs").json()

    response = client.get(f"/api/projects/{project_id}/schedule-runs/latest")

    assert response.status_code == 200
    latest_run = response.json()
    assert latest_run["id"] == second_run["id"]
    assert latest_run["id"] > first_run["id"]


def test_get_latest_schedule_run_returns_404_when_project_has_no_runs() -> None:
    with SessionLocal() as session:
        project = Project(
            name="Projekt bez harmonogramów",
            start_date=date(2026, 9, 1),
            description=None,
        )
        session.add(project)
        session.commit()
        project_id = project.id

    client = TestClient(app)

    response = client.get(f"/api/projects/{project_id}/schedule-runs/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "Brak uruchomień harmonogramu dla projektu"}


def test_create_schedule_run_returns_404_for_missing_project() -> None:
    client = TestClient(app)

    response = client.post("/api/projects/999999/schedule-runs")

    assert response.status_code == 404
    assert response.json() == {"detail": "Projekt nie istnieje"}
