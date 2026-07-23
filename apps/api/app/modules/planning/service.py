from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.planning import models, repository, schemas


def list_projects(session: Session) -> list[schemas.ProjectSummary]:
    return [schemas.ProjectSummary.model_validate(project) for project in repository.list_projects(session)]


def get_project(session: Session, project_id: int) -> schemas.ProjectSummary:
    project = repository.get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nie istnieje")

    return schemas.ProjectSummary.model_validate(project)


def get_planning_data(session: Session, project_id: int) -> schemas.PlanningDataRead:
    project = repository.get_project_planning_data(session, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nie istnieje")

    dependencies = repository.list_project_dependencies(session, project_id)

    return schemas.PlanningDataRead(
        project=schemas.ProjectSummary.model_validate(project),
        skills=[schemas.SkillRead.model_validate(skill) for skill in repository.list_skills(session)],
        tasks=[_map_task(task) for task in sorted(project.tasks, key=lambda item: item.code)],
        dependencies=[_map_dependency(dependency) for dependency in dependencies],
        crews=[_map_crew(crew) for crew in sorted(project.crews, key=lambda item: item.code)],
        planning_locks=[_map_lock(lock) for lock in sorted(project.planning_locks, key=lambda item: item.id)],
    )


def _map_task(task: models.Task) -> schemas.TaskRead:
    return schemas.TaskRead(
        id=task.id,
        code=task.code,
        name=task.name,
        duration_days=task.duration_days,
        due_day=task.due_day,
        description=task.description,
        required_skill_codes=sorted(requirement.skill.code for requirement in task.required_skills),
    )


def _map_dependency(dependency: models.TaskDependency) -> schemas.TaskDependencyRead:
    return schemas.TaskDependencyRead(
        id=dependency.id,
        predecessor_task_code=dependency.predecessor_task.code,
        successor_task_code=dependency.successor_task.code,
    )


def _map_crew(crew: models.Crew) -> schemas.CrewRead:
    return schemas.CrewRead(
        id=crew.id,
        code=crew.code,
        name=crew.name,
        skill_codes=sorted(crew_skill.skill.code for crew_skill in crew.skills),
        available_from_day=crew.availability.available_from_day if crew.availability else 0,
    )


def _map_lock(lock: models.PlanningLock) -> schemas.PlanningLockRead:
    return schemas.PlanningLockRead(
        id=lock.id,
        task_code=lock.task.code,
        locked_crew_code=lock.locked_crew.code if lock.locked_crew else None,
        locked_start_day=lock.locked_start_day,
        is_active=lock.is_active,
    )
