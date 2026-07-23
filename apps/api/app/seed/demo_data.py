from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.planning.models import (
    Crew,
    CrewAvailability,
    CrewSkill,
    Project,
    Skill,
    Task,
    TaskDependency,
    TaskRequiredSkill,
)


DEMO_PROJECT_NAME = "Modernizacja odcinka drogi powiatowej"


def seed_demo_data(session: Session) -> Project:
    existing_project = session.scalar(select(Project).where(Project.name == DEMO_PROJECT_NAME))
    if existing_project is not None:
        return existing_project

    skills = _get_or_create_skills(session)

    project = Project(
        name=DEMO_PROJECT_NAME,
        start_date=date(2026, 8, 3),
        description="Projekt demo pokazujący zadania, kwalifikacje, ekipy i zależności planistyczne.",
    )
    session.add(project)
    session.flush()

    tasks = _create_tasks(project, skills)
    crews = _create_crews(project, skills)
    session.add_all([*tasks.values(), *crews.values()])
    session.flush()

    session.add_all(
        [
            TaskDependency(
                project_id=project.id,
                predecessor_task=tasks["T-001"],
                successor_task=tasks["T-002"],
            ),
            TaskDependency(
                project_id=project.id,
                predecessor_task=tasks["T-002"],
                successor_task=tasks["T-003"],
            ),
            TaskDependency(
                project_id=project.id,
                predecessor_task=tasks["T-003"],
                successor_task=tasks["T-004"],
            ),
            TaskDependency(
                project_id=project.id,
                predecessor_task=tasks["T-004"],
                successor_task=tasks["T-005"],
            ),
        ]
    )

    session.commit()
    session.refresh(project)
    return project


def _get_or_create_skills(session: Session) -> dict[str, Skill]:
    definitions = {
        "safety": "Zabezpieczenie robót",
        "earthworks": "Roboty ziemne",
        "electrical": "Instalacje elektryczne",
        "asphalt": "Nawierzchnie asfaltowe",
    }
    existing_skills = {
        skill.code: skill
        for skill in session.scalars(select(Skill).where(Skill.code.in_(definitions))).all()
    }

    for code, name in definitions.items():
        if code not in existing_skills:
            existing_skills[code] = Skill(code=code, name=name)
            session.add(existing_skills[code])

    session.flush()
    return existing_skills


def _create_tasks(project: Project, skills: dict[str, Skill]) -> dict[str, Task]:
    task_definitions = [
        (
            "T-001",
            "Oznakowanie i zabezpieczenie terenu",
            1,
            1,
            "Przygotowanie miejsca prac i wdrożenie organizacji ruchu.",
            ["safety"],
        ),
        (
            "T-002",
            "Wykop i przygotowanie podłoża",
            3,
            4,
            "Roboty ziemne oraz przygotowanie podłoża pod dalsze prace.",
            ["earthworks", "safety"],
        ),
        (
            "T-003",
            "Montaż kanału technologicznego",
            2,
            6,
            "Montaż elementów infrastruktury technicznej w przygotowanym wykopie.",
            ["earthworks", "electrical"],
        ),
        (
            "T-004",
            "Odtworzenie nawierzchni",
            2,
            8,
            "Ułożenie warstw asfaltowych i przywrócenie przejezdności.",
            ["asphalt"],
        ),
        (
            "T-005",
            "Odbiór techniczny i uporządkowanie terenu",
            1,
            9,
            "Kontrola końcowa, usunięcie oznakowania i przekazanie odcinka.",
            ["safety"],
        ),
    ]

    tasks: dict[str, Task] = {}
    for code, name, duration_days, due_day, description, skill_codes in task_definitions:
        task = Task(
            project=project,
            code=code,
            name=name,
            duration_days=duration_days,
            due_day=due_day,
            description=description,
        )
        task.required_skills = [TaskRequiredSkill(skill=skills[skill_code]) for skill_code in skill_codes]
        tasks[code] = task

    return tasks


def _create_crews(project: Project, skills: dict[str, Skill]) -> dict[str, Crew]:
    crew_definitions = [
        ("C-001", "Brygada drogowa Alfa", ["safety", "earthworks"], 0),
        ("C-002", "Brygada instalacyjna Beta", ["earthworks", "electrical"], 1),
        ("C-003", "Brygada nawierzchni Gamma", ["asphalt", "safety"], 3),
    ]

    crews: dict[str, Crew] = {}
    for code, name, skill_codes, available_from_day in crew_definitions:
        crew = Crew(project=project, code=code, name=name)
        crew.skills = [CrewSkill(skill=skills[skill_code]) for skill_code in skill_codes]
        crew.availability = CrewAvailability(available_from_day=available_from_day)
        crews[code] = crew

    return crews


def main() -> None:
    with SessionLocal() as session:
        project = seed_demo_data(session)
        print(f"Projekt demo gotowy: {project.id} - {project.name}")


if __name__ == "__main__":
    main()
