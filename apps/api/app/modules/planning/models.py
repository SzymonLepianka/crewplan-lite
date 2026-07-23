from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    crews: Mapped[list["Crew"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    schedule_runs: Mapped[list["ScheduleRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    planning_locks: Mapped[list["PlanningLock"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    task_requirements: Mapped[list["TaskRequiredSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    crew_skills: Mapped[list["CrewSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_tasks_project_code"),
        CheckConstraint("duration_days > 0", name="ck_tasks_duration_days_positive"),
        CheckConstraint("due_day >= 0", name="ck_tasks_due_day_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_days: Mapped[int] = mapped_column(nullable=False)
    due_day: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    project: Mapped[Project] = relationship(back_populates="tasks")
    required_skills: Mapped[list["TaskRequiredSkill"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    predecessor_dependencies: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.predecessor_task_id",
        back_populates="predecessor_task",
        cascade="all, delete-orphan",
    )
    successor_dependencies: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.successor_task_id",
        back_populates="successor_task",
        cascade="all, delete-orphan",
    )
    planning_locks: Mapped[list["PlanningLock"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    assignments: Mapped[list["TaskAssignment"]] = relationship(back_populates="task")


class TaskRequiredSkill(Base):
    __tablename__ = "task_required_skills"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

    task: Mapped[Task] = relationship(back_populates="required_skills")
    skill: Mapped[Skill] = relationship(back_populates="task_requirements")


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint("predecessor_task_id", "successor_task_id", name="uq_task_dependencies_pair"),
        CheckConstraint("predecessor_task_id <> successor_task_id", name="ck_task_dependencies_distinct_tasks"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    predecessor_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    successor_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    predecessor_task: Mapped[Task] = relationship(foreign_keys=[predecessor_task_id], back_populates="predecessor_dependencies")
    successor_task: Mapped[Task] = relationship(foreign_keys=[successor_task_id], back_populates="successor_dependencies")


class Crew(Base):
    __tablename__ = "crews"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_crews_project_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    project: Mapped[Project] = relationship(back_populates="crews")
    skills: Mapped[list["CrewSkill"]] = relationship(back_populates="crew", cascade="all, delete-orphan")
    availability: Mapped["CrewAvailability | None"] = relationship(
        back_populates="crew",
        cascade="all, delete-orphan",
        uselist=False,
    )
    planning_locks: Mapped[list["PlanningLock"]] = relationship(back_populates="locked_crew")
    assignments: Mapped[list["TaskAssignment"]] = relationship(back_populates="crew")


class CrewSkill(Base):
    __tablename__ = "crew_skills"

    crew_id: Mapped[int] = mapped_column(ForeignKey("crews.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

    crew: Mapped[Crew] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="crew_skills")


class CrewAvailability(Base):
    __tablename__ = "crew_availabilities"
    __table_args__ = (
        UniqueConstraint("crew_id", name="uq_crew_availabilities_crew_id"),
        CheckConstraint("available_from_day >= 0", name="ck_crew_availabilities_from_day_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    crew_id: Mapped[int] = mapped_column(ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    available_from_day: Mapped[int] = mapped_column(nullable=False)

    crew: Mapped[Crew] = relationship(back_populates="availability")


class PlanningLock(Base):
    __tablename__ = "planning_locks"
    __table_args__ = (
        UniqueConstraint("project_id", "task_id", name="uq_planning_locks_project_task"),
        CheckConstraint("locked_start_day IS NULL OR locked_start_day >= 0", name="ck_planning_locks_start_day_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    locked_crew_id: Mapped[int | None] = mapped_column(ForeignKey("crews.id", ondelete="SET NULL"))
    locked_start_day: Mapped[int | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    project: Mapped[Project] = relationship(back_populates="planning_locks")
    task: Mapped[Task] = relationship(back_populates="planning_locks")
    locked_crew: Mapped[Crew | None] = relationship(back_populates="planning_locks")


class ScheduleRun(Base):
    __tablename__ = "schedule_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    runtime_ms: Mapped[int | None] = mapped_column()
    objective_value: Mapped[int | None] = mapped_column()
    total_lateness_days: Mapped[int | None] = mapped_column()
    project_finish_day: Mapped[int | None] = mapped_column()

    project: Mapped[Project] = relationship(back_populates="schedule_runs")
    assignments: Mapped[list["TaskAssignment"]] = relationship(back_populates="schedule_run", cascade="all, delete-orphan")


class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    __table_args__ = (
        UniqueConstraint("schedule_run_id", "task_id", name="uq_task_assignments_run_task"),
        CheckConstraint("start_day >= 0", name="ck_task_assignments_start_day_non_negative"),
        CheckConstraint("end_day > start_day", name="ck_task_assignments_end_after_start"),
        CheckConstraint("lateness_days >= 0", name="ck_task_assignments_lateness_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_run_id: Mapped[int] = mapped_column(ForeignKey("schedule_runs.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    crew_id: Mapped[int] = mapped_column(ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    start_day: Mapped[int] = mapped_column(nullable=False)
    end_day: Mapped[int] = mapped_column(nullable=False)
    lateness_days: Mapped[int] = mapped_column(nullable=False)

    schedule_run: Mapped[ScheduleRun] = relationship(back_populates="assignments")
    task: Mapped[Task] = relationship(back_populates="assignments")
    crew: Mapped[Crew] = relationship(back_populates="assignments")
