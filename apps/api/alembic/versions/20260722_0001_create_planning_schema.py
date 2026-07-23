"""create planning schema

Revision ID: 20260722_0001
Revises:
Create Date: 2026-07-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "crews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_crews_project_code"),
    )
    op.create_table(
        "schedule_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.Column("objective_value", sa.Integer(), nullable=True),
        sa.Column("total_lateness_days", sa.Integer(), nullable=True),
        sa.Column("project_finish_day", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint("duration_days > 0", name="ck_tasks_duration_days_positive"),
        sa.CheckConstraint("due_day >= 0", name="ck_tasks_due_day_non_negative"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_tasks_project_code"),
    )
    op.create_table(
        "crew_availabilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crew_id", sa.Integer(), nullable=False),
        sa.Column("available_from_day", sa.Integer(), nullable=False),
        sa.CheckConstraint("available_from_day >= 0", name="ck_crew_availabilities_from_day_non_negative"),
        sa.ForeignKeyConstraint(["crew_id"], ["crews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crew_id", name="uq_crew_availabilities_crew_id"),
    )
    op.create_table(
        "crew_skills",
        sa.Column("crew_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["crew_id"], ["crews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("crew_id", "skill_id"),
    )
    op.create_table(
        "planning_locks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("locked_crew_id", sa.Integer(), nullable=True),
        sa.Column("locked_start_day", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("locked_start_day IS NULL OR locked_start_day >= 0", name="ck_planning_locks_start_day_non_negative"),
        sa.ForeignKeyConstraint(["locked_crew_id"], ["crews.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "task_id", name="uq_planning_locks_project_task"),
    )
    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("predecessor_task_id", sa.Integer(), nullable=False),
        sa.Column("successor_task_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("predecessor_task_id <> successor_task_id", name="ck_task_dependencies_distinct_tasks"),
        sa.ForeignKeyConstraint(["predecessor_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["successor_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("predecessor_task_id", "successor_task_id", name="uq_task_dependencies_pair"),
    )
    op.create_table(
        "task_required_skills",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "skill_id"),
    )
    op.create_table(
        "task_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_run_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("crew_id", sa.Integer(), nullable=False),
        sa.Column("start_day", sa.Integer(), nullable=False),
        sa.Column("end_day", sa.Integer(), nullable=False),
        sa.Column("lateness_days", sa.Integer(), nullable=False),
        sa.CheckConstraint("end_day > start_day", name="ck_task_assignments_end_after_start"),
        sa.CheckConstraint("lateness_days >= 0", name="ck_task_assignments_lateness_non_negative"),
        sa.CheckConstraint("start_day >= 0", name="ck_task_assignments_start_day_non_negative"),
        sa.ForeignKeyConstraint(["crew_id"], ["crews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_run_id"], ["schedule_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_run_id", "task_id", name="uq_task_assignments_run_task"),
    )


def downgrade() -> None:
    op.drop_table("task_assignments")
    op.drop_table("task_required_skills")
    op.drop_table("task_dependencies")
    op.drop_table("planning_locks")
    op.drop_table("crew_skills")
    op.drop_table("crew_availabilities")
    op.drop_table("tasks")
    op.drop_table("schedule_runs")
    op.drop_table("crews")
    op.drop_table("skills")
    op.drop_table("projects")
