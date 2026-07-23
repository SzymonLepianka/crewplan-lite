from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    description: str | None


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class TaskRead(BaseModel):
    id: int
    code: str
    name: str
    duration_days: int
    due_day: int
    description: str | None
    required_skill_codes: list[str]


class TaskDependencyRead(BaseModel):
    id: int
    predecessor_task_code: str
    successor_task_code: str


class CrewRead(BaseModel):
    id: int
    code: str
    name: str
    skill_codes: list[str]
    available_from_day: int


class PlanningLockRead(BaseModel):
    id: int
    task_code: str
    locked_crew_code: str | None
    locked_start_day: int | None
    is_active: bool


class PlanningDataRead(BaseModel):
    project: ProjectSummary
    skills: list[SkillRead]
    tasks: list[TaskRead]
    dependencies: list[TaskDependencyRead]
    crews: list[CrewRead]
    planning_locks: list[PlanningLockRead]


class TaskAssignmentRead(BaseModel):
    id: int
    task_code: str
    crew_code: str
    start_day: int
    end_day: int
    lateness_days: int


class ScheduleRunRead(BaseModel):
    id: int
    project_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    runtime_ms: int | None
    objective_value: int | None
    total_lateness_days: int | None
    project_finish_day: int | None
    assignments: list[TaskAssignmentRead]
