from datetime import date

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
