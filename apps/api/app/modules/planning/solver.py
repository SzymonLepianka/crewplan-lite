from dataclasses import dataclass
from enum import StrEnum

from ortools.sat.python import cp_model


class SolverStatus(StrEnum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    MODEL_INVALID = "MODEL_INVALID"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SolverTask:
    code: str
    duration_days: int
    due_day: int
    required_skill_codes: frozenset[str]


@dataclass(frozen=True)
class SolverCrew:
    code: str
    skill_codes: frozenset[str]
    available_from_day: int


@dataclass(frozen=True)
class SolverDependency:
    predecessor_task_code: str
    successor_task_code: str


@dataclass(frozen=True)
class SolverPlanningLock:
    task_code: str
    locked_crew_code: str | None = None
    locked_start_day: int | None = None


@dataclass(frozen=True)
class SolverInput:
    tasks: tuple[SolverTask, ...]
    crews: tuple[SolverCrew, ...]
    dependencies: tuple[SolverDependency, ...] = ()
    planning_locks: tuple[SolverPlanningLock, ...] = ()
    max_runtime_seconds: float = 5.0


@dataclass(frozen=True)
class SolverAssignment:
    task_code: str
    crew_code: str
    start_day: int
    end_day: int
    lateness_days: int


@dataclass(frozen=True)
class SolverResult:
    status: SolverStatus
    assignments: tuple[SolverAssignment, ...]
    objective_value: int | None
    total_lateness_days: int | None
    project_finish_day: int | None
    runtime_ms: int
    message: str | None = None


def solve_schedule(solver_input: SolverInput) -> SolverResult:
    try:
        return _solve_schedule(solver_input)
    except ValueError as error:
        return SolverResult(
            status=SolverStatus.MODEL_INVALID,
            assignments=(),
            objective_value=None,
            total_lateness_days=None,
            project_finish_day=None,
            runtime_ms=0,
            message=str(error),
        )
    except Exception as error:
        return SolverResult(
            status=SolverStatus.ERROR,
            assignments=(),
            objective_value=None,
            total_lateness_days=None,
            project_finish_day=None,
            runtime_ms=0,
            message=str(error),
        )


def _solve_schedule(solver_input: SolverInput) -> SolverResult:
    _validate_input(solver_input)

    crews_by_code = {crew.code: crew for crew in solver_input.crews}
    horizon = _calculate_horizon(solver_input)

    model = cp_model.CpModel()

    starts = {
        task.code: model.NewIntVar(0, horizon, f"start_{task.code}")
        for task in solver_input.tasks
    }
    ends = {
        task.code: model.NewIntVar(0, horizon, f"end_{task.code}")
        for task in solver_input.tasks
    }
    lateness = {
        task.code: model.NewIntVar(0, horizon, f"lateness_{task.code}")
        for task in solver_input.tasks
    }

    assigned: dict[tuple[str, str], cp_model.IntVar] = {}
    optional_intervals_by_crew: dict[str, list[cp_model.IntervalVar]] = {
        crew.code: []
        for crew in solver_input.crews
    }

    for task in solver_input.tasks:
        model.Add(ends[task.code] == starts[task.code] + task.duration_days)
        model.Add(lateness[task.code] >= ends[task.code] - task.due_day)
        model.Add(lateness[task.code] >= 0)

        allowed_crew_vars: list[cp_model.IntVar] = []
        for crew in solver_input.crews:
            if not task.required_skill_codes.issubset(crew.skill_codes):
                continue

            variable = model.NewBoolVar(f"assigned_{task.code}_{crew.code}")
            assigned[(task.code, crew.code)] = variable
            allowed_crew_vars.append(variable)

            model.Add(starts[task.code] >= crew.available_from_day).OnlyEnforceIf(variable)
            interval = model.NewOptionalIntervalVar(
                starts[task.code],
                task.duration_days,
                ends[task.code],
                variable,
                f"interval_{task.code}_{crew.code}",
            )
            optional_intervals_by_crew[crew.code].append(interval)

        if not allowed_crew_vars:
            raise ValueError(f"Zadanie {task.code} nie ma żadnej ekipy z wymaganymi kwalifikacjami")

        model.AddExactlyOne(allowed_crew_vars)

    for intervals in optional_intervals_by_crew.values():
        if intervals:
            model.AddNoOverlap(intervals)

    for dependency in solver_input.dependencies:
        model.Add(ends[dependency.predecessor_task_code] <= starts[dependency.successor_task_code])

    for lock in solver_input.planning_locks:
        if lock.locked_start_day is not None:
            model.Add(starts[lock.task_code] == lock.locked_start_day)
        if lock.locked_crew_code is not None:
            assignment_variable = assigned.get((lock.task_code, lock.locked_crew_code))
            if assignment_variable is None:
                raise ValueError(
                    f"Blokada zadania {lock.task_code} wskazuje ekipę {lock.locked_crew_code}, "
                    "która nie spełnia wymagań zadania"
                )
            model.Add(assignment_variable == 1)

    project_finish_day = model.NewIntVar(0, horizon, "project_finish_day")
    model.AddMaxEquality(project_finish_day, list(ends.values()))

    total_lateness_days = model.NewIntVar(0, horizon * len(solver_input.tasks), "total_lateness_days")
    model.Add(total_lateness_days == sum(lateness.values()))

    objective = model.NewIntVar(0, (horizon * len(solver_input.tasks) * (horizon + 1)) + horizon, "objective")
    model.Add(objective == total_lateness_days * (horizon + 1) + project_finish_day)
    model.Minimize(objective)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_input.max_runtime_seconds
    status = solver.Solve(model)
    runtime_ms = round(solver.WallTime() * 1000)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolverResult(
            status=_map_solver_status(status),
            assignments=(),
            objective_value=None,
            total_lateness_days=None,
            project_finish_day=None,
            runtime_ms=runtime_ms,
        )

    assignments = []
    for task in solver_input.tasks:
        crew_code = _selected_crew_code(solver, assigned, task.code, crews_by_code)
        assignments.append(
            SolverAssignment(
                task_code=task.code,
                crew_code=crew_code,
                start_day=solver.Value(starts[task.code]),
                end_day=solver.Value(ends[task.code]),
                lateness_days=solver.Value(lateness[task.code]),
            )
        )

    return SolverResult(
        status=_map_solver_status(status),
        assignments=tuple(sorted(assignments, key=lambda assignment: (assignment.start_day, assignment.task_code))),
        objective_value=solver.Value(objective),
        total_lateness_days=solver.Value(total_lateness_days),
        project_finish_day=solver.Value(project_finish_day),
        runtime_ms=runtime_ms,
    )


def _validate_input(solver_input: SolverInput) -> None:
    if not solver_input.tasks:
        raise ValueError("Solver wymaga co najmniej jednego zadania")
    if not solver_input.crews:
        raise ValueError("Solver wymaga co najmniej jednej ekipy")

    task_codes = [task.code for task in solver_input.tasks]
    crew_codes = [crew.code for crew in solver_input.crews]

    _ensure_unique(task_codes, "Kod zadania")
    _ensure_unique(crew_codes, "Kod ekipy")

    task_code_set = set(task_codes)
    crew_code_set = set(crew_codes)

    for task in solver_input.tasks:
        if task.duration_days <= 0:
            raise ValueError(f"Zadanie {task.code} musi mieć dodatni czas trwania")
        if task.due_day < 0:
            raise ValueError(f"Zadanie {task.code} nie może mieć ujemnego terminu")

    for crew in solver_input.crews:
        if crew.available_from_day < 0:
            raise ValueError(f"Ekipa {crew.code} nie może mieć ujemnej dostępności")

    for dependency in solver_input.dependencies:
        if dependency.predecessor_task_code not in task_code_set:
            raise ValueError(f"Nieznany poprzednik zależności: {dependency.predecessor_task_code}")
        if dependency.successor_task_code not in task_code_set:
            raise ValueError(f"Nieznany następnik zależności: {dependency.successor_task_code}")
        if dependency.predecessor_task_code == dependency.successor_task_code:
            raise ValueError(f"Zadanie {dependency.predecessor_task_code} nie może zależeć od siebie")

    for lock in solver_input.planning_locks:
        if lock.task_code not in task_code_set:
            raise ValueError(f"Blokada wskazuje nieznane zadanie: {lock.task_code}")
        if lock.locked_crew_code is not None and lock.locked_crew_code not in crew_code_set:
            raise ValueError(f"Blokada wskazuje nieznaną ekipę: {lock.locked_crew_code}")
        if lock.locked_start_day is not None and lock.locked_start_day < 0:
            raise ValueError(f"Blokada zadania {lock.task_code} ma ujemny dzień startu")


def _ensure_unique(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"{label} musi być unikalny: {', '.join(duplicates)}")


def _calculate_horizon(solver_input: SolverInput) -> int:
    total_duration = sum(task.duration_days for task in solver_input.tasks)
    latest_availability = max(crew.available_from_day for crew in solver_input.crews)
    latest_locked_start = max(
        (lock.locked_start_day or 0 for lock in solver_input.planning_locks),
        default=0,
    )
    return total_duration + max(latest_availability, latest_locked_start)


def _selected_crew_code(
    solver: cp_model.CpSolver,
    assigned: dict[tuple[str, str], cp_model.IntVar],
    task_code: str,
    crews_by_code: dict[str, SolverCrew],
) -> str:
    for crew_code in crews_by_code:
        variable = assigned.get((task_code, crew_code))
        if variable is not None and solver.Value(variable) == 1:
            return crew_code

    raise ValueError(f"Nie znaleziono przypisanej ekipy dla zadania {task_code}")


def _map_solver_status(status: int) -> SolverStatus:
    if status == cp_model.OPTIMAL:
        return SolverStatus.OPTIMAL
    if status == cp_model.FEASIBLE:
        return SolverStatus.FEASIBLE
    if status == cp_model.INFEASIBLE:
        return SolverStatus.INFEASIBLE
    if status == cp_model.MODEL_INVALID:
        return SolverStatus.MODEL_INVALID
    return SolverStatus.ERROR
