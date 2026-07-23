from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
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
