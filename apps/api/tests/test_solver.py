from app.modules.planning.solver import (
    SolverCrew,
    SolverDependency,
    SolverInput,
    SolverPlanningLock,
    SolverStatus,
    SolverTask,
    solve_schedule,
)


def test_solver_assigns_each_task_to_qualified_crew() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(
                SolverTask("T-001", duration_days=1, due_day=2, required_skill_codes=frozenset({"safety"})),
                SolverTask("T-002", duration_days=2, due_day=4, required_skill_codes=frozenset({"electrical"})),
            ),
            crews=(
                SolverCrew("C-001", skill_codes=frozenset({"safety"}), available_from_day=0),
                SolverCrew("C-002", skill_codes=frozenset({"electrical"}), available_from_day=0),
            ),
        )
    )

    assert result.status == SolverStatus.OPTIMAL
    assert {assignment.task_code for assignment in result.assignments} == {"T-001", "T-002"}
    assert _assignment_for(result, "T-001").crew_code == "C-001"
    assert _assignment_for(result, "T-002").crew_code == "C-002"


def test_solver_respects_task_dependencies() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(
                SolverTask("T-001", duration_days=2, due_day=10, required_skill_codes=frozenset({"earthworks"})),
                SolverTask("T-002", duration_days=1, due_day=10, required_skill_codes=frozenset({"earthworks"})),
            ),
            crews=(
                SolverCrew("C-001", skill_codes=frozenset({"earthworks"}), available_from_day=0),
                SolverCrew("C-002", skill_codes=frozenset({"earthworks"}), available_from_day=0),
            ),
            dependencies=(SolverDependency("T-001", "T-002"),),
        )
    )

    predecessor = _assignment_for(result, "T-001")
    successor = _assignment_for(result, "T-002")

    assert result.status == SolverStatus.OPTIMAL
    assert predecessor.end_day <= successor.start_day


def test_solver_prevents_overlapping_tasks_for_one_crew() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(
                SolverTask("T-001", duration_days=3, due_day=10, required_skill_codes=frozenset({"safety"})),
                SolverTask("T-002", duration_days=2, due_day=10, required_skill_codes=frozenset({"safety"})),
            ),
            crews=(SolverCrew("C-001", skill_codes=frozenset({"safety"}), available_from_day=0),),
        )
    )

    first = _assignment_for(result, "T-001")
    second = _assignment_for(result, "T-002")

    assert result.status == SolverStatus.OPTIMAL
    assert first.end_day <= second.start_day or second.end_day <= first.start_day


def test_solver_respects_crew_availability() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(SolverTask("T-001", duration_days=2, due_day=10, required_skill_codes=frozenset({"asphalt"})),),
            crews=(SolverCrew("C-001", skill_codes=frozenset({"asphalt"}), available_from_day=4),),
        )
    )

    assignment = _assignment_for(result, "T-001")

    assert result.status == SolverStatus.OPTIMAL
    assert assignment.start_day >= 4


def test_solver_respects_locked_crew_and_locked_start() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(SolverTask("T-001", duration_days=2, due_day=10, required_skill_codes=frozenset({"safety"})),),
            crews=(
                SolverCrew("C-001", skill_codes=frozenset({"safety"}), available_from_day=0),
                SolverCrew("C-002", skill_codes=frozenset({"safety"}), available_from_day=0),
            ),
            planning_locks=(SolverPlanningLock("T-001", locked_crew_code="C-002", locked_start_day=3),),
        )
    )

    assignment = _assignment_for(result, "T-001")

    assert result.status == SolverStatus.OPTIMAL
    assert assignment.crew_code == "C-002"
    assert assignment.start_day == 3
    assert assignment.end_day == 5


def test_solver_reports_lateness_and_project_finish_day() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(SolverTask("T-001", duration_days=3, due_day=1, required_skill_codes=frozenset({"safety"})),),
            crews=(SolverCrew("C-001", skill_codes=frozenset({"safety"}), available_from_day=0),),
        )
    )

    assignment = _assignment_for(result, "T-001")

    assert result.status == SolverStatus.OPTIMAL
    assert assignment.start_day == 0
    assert assignment.end_day == 3
    assert assignment.lateness_days == 2
    assert result.total_lateness_days == 2
    assert result.project_finish_day == 3


def test_solver_returns_model_invalid_when_no_crew_has_required_skills() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(SolverTask("T-001", duration_days=1, due_day=1, required_skill_codes=frozenset({"electrical"})),),
            crews=(SolverCrew("C-001", skill_codes=frozenset({"safety"}), available_from_day=0),),
        )
    )

    assert result.status == SolverStatus.MODEL_INVALID
    assert result.assignments == ()
    assert result.message == "Zadanie T-001 nie ma żadnej ekipy z wymaganymi kwalifikacjami"


def test_solver_returns_infeasible_for_conflicting_locks() -> None:
    result = solve_schedule(
        SolverInput(
            tasks=(
                SolverTask("T-001", duration_days=2, due_day=10, required_skill_codes=frozenset({"safety"})),
                SolverTask("T-002", duration_days=2, due_day=10, required_skill_codes=frozenset({"safety"})),
            ),
            crews=(SolverCrew("C-001", skill_codes=frozenset({"safety"}), available_from_day=0),),
            planning_locks=(
                SolverPlanningLock("T-001", locked_crew_code="C-001", locked_start_day=0),
                SolverPlanningLock("T-002", locked_crew_code="C-001", locked_start_day=0),
            ),
        )
    )

    assert result.status == SolverStatus.INFEASIBLE
    assert result.assignments == ()


def _assignment_for(result, task_code: str):
    return next(assignment for assignment in result.assignments if assignment.task_code == task_code)
