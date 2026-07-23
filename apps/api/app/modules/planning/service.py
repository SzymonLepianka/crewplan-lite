from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.planning import models, repository, schemas
from app.modules.planning.solver import (
    SolverCrew,
    SolverDependency,
    SolverInput,
    SolverPlanningLock,
    SolverTask,
    solve_schedule,
)


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


def create_schedule_run(session: Session, project_id: int) -> schemas.ScheduleRunRead:
    project = repository.get_project_planning_data(session, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nie istnieje")

    dependencies = repository.list_project_dependencies(session, project_id)
    solver_result = solve_schedule(_map_solver_input(project, dependencies))

    task_by_code = {task.code: task for task in project.tasks}
    crew_by_code = {crew.code: crew for crew in project.crews}
    now = datetime.now(UTC)

    schedule_run = models.ScheduleRun(
        project_id=project.id,
        status=solver_result.status.value,
        started_at=now,
        finished_at=now,
        runtime_ms=solver_result.runtime_ms,
        objective_value=solver_result.objective_value,
        total_lateness_days=solver_result.total_lateness_days,
        project_finish_day=solver_result.project_finish_day,
    )
    assignments = [
        models.TaskAssignment(
            schedule_run_id=0,
            task_id=task_by_code[assignment.task_code].id,
            crew_id=crew_by_code[assignment.crew_code].id,
            start_day=assignment.start_day,
            end_day=assignment.end_day,
            lateness_days=assignment.lateness_days,
        )
        for assignment in solver_result.assignments
    ]

    saved_run = repository.save_schedule_run(session, schedule_run, assignments)
    return _map_schedule_run(saved_run)


def get_schedule_run(session: Session, project_id: int, run_id: int) -> schemas.ScheduleRunRead:
    _ensure_project_exists(session, project_id)
    schedule_run = repository.get_schedule_run(session, project_id, run_id)
    if schedule_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uruchomienie harmonogramu nie istnieje")

    return _map_schedule_run(schedule_run)


def get_latest_schedule_run(session: Session, project_id: int) -> schemas.ScheduleRunRead:
    _ensure_project_exists(session, project_id)
    schedule_run = repository.get_latest_schedule_run(session, project_id)
    if schedule_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brak uruchomień harmonogramu dla projektu")

    return _map_schedule_run(schedule_run)


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


def _map_solver_input(project: models.Project, dependencies: list[models.TaskDependency]) -> SolverInput:
    return SolverInput(
        tasks=tuple(
            SolverTask(
                code=task.code,
                duration_days=task.duration_days,
                due_day=task.due_day,
                required_skill_codes=frozenset(requirement.skill.code for requirement in task.required_skills),
            )
            for task in sorted(project.tasks, key=lambda item: item.code)
        ),
        crews=tuple(
            SolverCrew(
                code=crew.code,
                skill_codes=frozenset(crew_skill.skill.code for crew_skill in crew.skills),
                available_from_day=crew.availability.available_from_day if crew.availability else 0,
            )
            for crew in sorted(project.crews, key=lambda item: item.code)
        ),
        dependencies=tuple(
            SolverDependency(
                predecessor_task_code=dependency.predecessor_task.code,
                successor_task_code=dependency.successor_task.code,
            )
            for dependency in dependencies
        ),
        planning_locks=tuple(
            SolverPlanningLock(
                task_code=lock.task.code,
                locked_crew_code=lock.locked_crew.code if lock.locked_crew else None,
                locked_start_day=lock.locked_start_day,
            )
            for lock in project.planning_locks
            if lock.is_active
        ),
    )


def _map_schedule_run(schedule_run: models.ScheduleRun) -> schemas.ScheduleRunRead:
    return schemas.ScheduleRunRead(
        id=schedule_run.id,
        project_id=schedule_run.project_id,
        status=schedule_run.status,
        started_at=schedule_run.started_at,
        finished_at=schedule_run.finished_at,
        runtime_ms=schedule_run.runtime_ms,
        objective_value=schedule_run.objective_value,
        total_lateness_days=schedule_run.total_lateness_days,
        project_finish_day=schedule_run.project_finish_day,
        assignments=[
            schemas.TaskAssignmentRead(
                id=assignment.id,
                task_code=assignment.task.code,
                crew_code=assignment.crew.code,
                start_day=assignment.start_day,
                end_day=assignment.end_day,
                lateness_days=assignment.lateness_days,
            )
            for assignment in sorted(schedule_run.assignments, key=lambda item: (item.start_day, item.task.code))
        ],
    )


def _ensure_project_exists(session: Session, project_id: int) -> None:
    if repository.get_project(session, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nie istnieje")
