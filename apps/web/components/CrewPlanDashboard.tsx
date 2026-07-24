"use client";

import { useEffect, useMemo, useState } from "react";
import {
  createScheduleRun,
  getLatestScheduleRun,
  getPlanningData,
  listProjects,
  type Crew,
  type PlanningData,
  type ProjectSummary,
  type ScheduleRun,
  type Skill,
  type Task,
  type TaskAssignment,
  type TaskDependency,
} from "@/lib/api";

type LoadState = "idle" | "loading" | "ready" | "error";

export function CrewPlanDashboard() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [planningData, setPlanningData] = useState<PlanningData | null>(null);
  const [scheduleRun, setScheduleRun] = useState<ScheduleRun | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadInitialData() {
      setLoadState("loading");
      setErrorMessage(null);

      try {
        const projectList = await listProjects();
        if (!isMounted) {
          return;
        }

        setProjects(projectList);
        const firstProject = projectList[0];
        if (!firstProject) {
          setLoadState("ready");
          return;
        }

        setSelectedProjectId(firstProject.id);
        const [data, latestRun] = await Promise.all([
          getPlanningData(firstProject.id),
          getLatestScheduleRun(firstProject.id),
        ]);

        if (!isMounted) {
          return;
        }

        setPlanningData(data);
        setScheduleRun(latestRun);
        setLoadState("ready");
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setErrorMessage(error instanceof Error ? error.message : "Nie udało się pobrać danych.");
        setLoadState("error");
      }
    }

    loadInitialData();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleRunOptimization() {
    if (!selectedProjectId) {
      return;
    }

    setIsOptimizing(true);
    setErrorMessage(null);

    try {
      const run = await createScheduleRun(selectedProjectId);
      setScheduleRun(run);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Nie udało się uruchomić optymalizacji.");
    } finally {
      setIsOptimizing(false);
    }
  }

  const skillNamesByCode = useMemo(() => {
    return new Map(planningData?.skills.map((skill) => [skill.code, skill.name]) ?? []);
  }, [planningData]);

  const taskNamesByCode = useMemo(() => {
    return new Map(planningData?.tasks.map((task) => [task.code, task.name]) ?? []);
  }, [planningData]);

  const crewNamesByCode = useMemo(() => {
    return new Map(planningData?.crews.map((crew) => [crew.code, crew.name]) ?? []);
  }, [planningData]);

  if (loadState === "loading" || loadState === "idle") {
    return (
      <main className="app-shell">
        <section className="empty-state">
          <p className="eyebrow">CrewPlan Lite</p>
          <h1>Ładowanie danych planistycznych</h1>
        </section>
      </main>
    );
  }

  if (loadState === "error") {
    return (
      <main className="app-shell">
        <section className="empty-state">
          <p className="eyebrow">CrewPlan Lite</p>
          <h1>Nie udało się połączyć z API</h1>
          <p>{errorMessage}</p>
        </section>
      </main>
    );
  }

  if (!planningData || projects.length === 0) {
    return (
      <main className="app-shell">
        <section className="empty-state">
          <p className="eyebrow">CrewPlan Lite</p>
          <h1>Brak danych demo</h1>
          <p>Uruchom migracje i seed danych demo w kontenerze API.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CrewPlan Lite</p>
          <h1>{planningData.project.name}</h1>
          <p className="lead">{planningData.project.description}</p>
        </div>
        <button className="primary-button" onClick={handleRunOptimization} disabled={isOptimizing}>
          <span aria-hidden="true">▶</span>
          {isOptimizing ? "Optymalizacja trwa" : "Uruchom optymalizację"}
        </button>
      </header>

      {errorMessage ? <p className="inline-error">{errorMessage}</p> : null}

      <section className="metric-strip" aria-label="Wynik solvera">
        <Metric label="Status solvera" value={scheduleRun?.status ?? "Brak wyniku"} />
        <Metric label="Czas działania" value={formatRuntime(scheduleRun?.runtime_ms)} />
        <Metric label="Wartość celu" value={formatNullable(scheduleRun?.objective_value)} />
        <Metric label="Całkowite opóźnienie" value={`${scheduleRun?.total_lateness_days ?? 0} dni`} />
        <Metric label="Koniec projektu" value={formatFinishDay(planningData.project.start_date, scheduleRun?.project_finish_day)} />
      </section>

      <section className="workspace-grid">
        <div className="panel">
          <div className="section-heading">
            <h2>Zadania</h2>
            <span>{planningData.tasks.length}</span>
          </div>
          <TasksTable tasks={planningData.tasks} skillNamesByCode={skillNamesByCode} />
        </div>

        <div className="panel">
          <div className="section-heading">
            <h2>Ekipy</h2>
            <span>{planningData.crews.length}</span>
          </div>
          <CrewsTable crews={planningData.crews} skillNamesByCode={skillNamesByCode} />
        </div>
      </section>

      <section className="workspace-grid secondary-grid">
        <div className="panel">
          <div className="section-heading">
            <h2>Zależności</h2>
            <span>{planningData.dependencies.length}</span>
          </div>
          <DependenciesList dependencies={planningData.dependencies} taskNamesByCode={taskNamesByCode} />
        </div>

        <div className="panel">
          <div className="section-heading">
            <h2>Kwalifikacje</h2>
            <span>{planningData.skills.length}</span>
          </div>
          <SkillsList skills={planningData.skills} />
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Harmonogram</h2>
          <span>{scheduleRun?.assignments.length ?? 0}</span>
        </div>
        <ScheduleTable
          assignments={scheduleRun?.assignments ?? []}
          projectStartDate={planningData.project.start_date}
          taskNamesByCode={taskNamesByCode}
          crewNamesByCode={crewNamesByCode}
        />
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TasksTable({ tasks, skillNamesByCode }: { tasks: Task[]; skillNamesByCode: Map<string, string> }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Kod</th>
            <th>Zadanie</th>
            <th>Czas</th>
            <th>Termin</th>
            <th>Kwalifikacje</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.code}>
              <td>{task.code}</td>
              <td>{task.name}</td>
              <td>{task.duration_days} dni</td>
              <td>Dzień {task.due_day}</td>
              <td>{formatSkillCodes(task.required_skill_codes, skillNamesByCode)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CrewsTable({ crews, skillNamesByCode }: { crews: Crew[]; skillNamesByCode: Map<string, string> }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Kod</th>
            <th>Ekipa</th>
            <th>Dostępność</th>
            <th>Kwalifikacje</th>
          </tr>
        </thead>
        <tbody>
          {crews.map((crew) => (
            <tr key={crew.code}>
              <td>{crew.code}</td>
              <td>{crew.name}</td>
              <td>Od dnia {crew.available_from_day}</td>
              <td>{formatSkillCodes(crew.skill_codes, skillNamesByCode)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DependenciesList({
  dependencies,
  taskNamesByCode,
}: {
  dependencies: TaskDependency[];
  taskNamesByCode: Map<string, string>;
}) {
  return (
    <ul className="dependency-list">
      {dependencies.map((dependency) => (
        <li key={dependency.id}>
          <span>{taskNamesByCode.get(dependency.predecessor_task_code) ?? dependency.predecessor_task_code}</span>
          <strong>→</strong>
          <span>{taskNamesByCode.get(dependency.successor_task_code) ?? dependency.successor_task_code}</span>
        </li>
      ))}
    </ul>
  );
}

function SkillsList({ skills }: { skills: Skill[] }) {
  return (
    <ul className="skill-list">
      {skills.map((skill) => (
        <li key={skill.code}>
          <span>{skill.code}</span>
          {skill.name}
        </li>
      ))}
    </ul>
  );
}

function ScheduleTable({
  assignments,
  projectStartDate,
  taskNamesByCode,
  crewNamesByCode,
}: {
  assignments: TaskAssignment[];
  projectStartDate: string;
  taskNamesByCode: Map<string, string>;
  crewNamesByCode: Map<string, string>;
}) {
  if (assignments.length === 0) {
    return <p className="muted-text">Brak zapisanego harmonogramu. Uruchom optymalizację.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Zadanie</th>
            <th>Ekipa</th>
            <th>Start</th>
            <th>Koniec</th>
            <th>Opóźnienie</th>
          </tr>
        </thead>
        <tbody>
          {assignments.map((assignment) => (
            <tr key={assignment.id}>
              <td>{taskNamesByCode.get(assignment.task_code) ?? assignment.task_code}</td>
              <td>{crewNamesByCode.get(assignment.crew_code) ?? assignment.crew_code}</td>
              <td>{formatDay(projectStartDate, assignment.start_day)}</td>
              <td>{formatDay(projectStartDate, assignment.end_day)}</td>
              <td>{assignment.lateness_days} dni</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatSkillCodes(skillCodes: string[], skillNamesByCode: Map<string, string>): string {
  return skillCodes.map((code) => skillNamesByCode.get(code) ?? code).join(", ");
}

function formatRuntime(runtimeMs: number | null | undefined): string {
  if (runtimeMs === null || runtimeMs === undefined) {
    return "Brak wyniku";
  }

  return `${runtimeMs} ms`;
}

function formatNullable(value: number | null | undefined): string {
  return value === null || value === undefined ? "Brak wyniku" : String(value);
}

function formatFinishDay(projectStartDate: string, finishDay: number | null | undefined): string {
  if (finishDay === null || finishDay === undefined) {
    return "Brak wyniku";
  }

  return formatDay(projectStartDate, finishDay);
}

function formatDay(projectStartDate: string, dayOffset: number): string {
  const [year, month, day] = projectStartDate.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day + dayOffset));

  return new Intl.DateTimeFormat("pl-PL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}
