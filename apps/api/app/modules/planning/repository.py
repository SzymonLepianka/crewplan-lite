from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.planning import models


def list_projects(session: Session) -> list[models.Project]:
    statement = select(models.Project).order_by(models.Project.id)
    return list(session.scalars(statement))


def get_project(session: Session, project_id: int) -> models.Project | None:
    return session.get(models.Project, project_id)


def get_project_planning_data(session: Session, project_id: int) -> models.Project | None:
    statement = (
        select(models.Project)
        .where(models.Project.id == project_id)
        .options(
            selectinload(models.Project.tasks)
            .selectinload(models.Task.required_skills)
            .selectinload(models.TaskRequiredSkill.skill),
            selectinload(models.Project.crews)
            .selectinload(models.Crew.skills)
            .selectinload(models.CrewSkill.skill),
            selectinload(models.Project.crews).selectinload(models.Crew.availability),
            selectinload(models.Project.planning_locks).selectinload(models.PlanningLock.task),
            selectinload(models.Project.planning_locks).selectinload(models.PlanningLock.locked_crew),
        )
    )
    return session.scalars(statement).one_or_none()


def list_project_dependencies(session: Session, project_id: int) -> list[models.TaskDependency]:
    statement = (
        select(models.TaskDependency)
        .where(models.TaskDependency.project_id == project_id)
        .options(
            selectinload(models.TaskDependency.predecessor_task),
            selectinload(models.TaskDependency.successor_task),
        )
        .order_by(models.TaskDependency.id)
    )
    return list(session.scalars(statement))


def list_skills(session: Session) -> list[models.Skill]:
    statement = select(models.Skill).order_by(models.Skill.code)
    return list(session.scalars(statement))


def save_schedule_run(
    session: Session,
    schedule_run: models.ScheduleRun,
    assignments: list[models.TaskAssignment],
) -> models.ScheduleRun:
    session.add(schedule_run)
    session.flush()

    for assignment in assignments:
        assignment.schedule_run_id = schedule_run.id

    session.add_all(assignments)
    session.commit()
    return get_schedule_run(session, schedule_run.project_id, schedule_run.id) or schedule_run


def get_schedule_run(session: Session, project_id: int, run_id: int) -> models.ScheduleRun | None:
    statement = (
        select(models.ScheduleRun)
        .where(models.ScheduleRun.project_id == project_id, models.ScheduleRun.id == run_id)
        .options(
            selectinload(models.ScheduleRun.assignments).selectinload(models.TaskAssignment.task),
            selectinload(models.ScheduleRun.assignments).selectinload(models.TaskAssignment.crew),
        )
    )
    return session.scalars(statement).one_or_none()


def get_latest_schedule_run(session: Session, project_id: int) -> models.ScheduleRun | None:
    statement = (
        select(models.ScheduleRun)
        .where(models.ScheduleRun.project_id == project_id)
        .order_by(models.ScheduleRun.id.desc())
        .limit(1)
        .options(
            selectinload(models.ScheduleRun.assignments).selectinload(models.TaskAssignment.task),
            selectinload(models.ScheduleRun.assignments).selectinload(models.TaskAssignment.crew),
        )
    )
    return session.scalars(statement).one_or_none()
