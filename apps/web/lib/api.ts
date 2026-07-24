export type ProjectSummary = {
  id: number;
  name: string;
  start_date: string;
  description: string | null;
};

export type Skill = {
  id: number;
  code: string;
  name: string;
};

export type Task = {
  id: number;
  code: string;
  name: string;
  duration_days: number;
  due_day: number;
  description: string | null;
  required_skill_codes: string[];
};

export type Crew = {
  id: number;
  code: string;
  name: string;
  skill_codes: string[];
  available_from_day: number;
};

export type TaskDependency = {
  id: number;
  predecessor_task_code: string;
  successor_task_code: string;
};

export type PlanningLock = {
  id: number;
  task_code: string;
  locked_crew_code: string | null;
  locked_start_day: number | null;
  is_active: boolean;
};

export type PlanningData = {
  project: ProjectSummary;
  skills: Skill[];
  tasks: Task[];
  dependencies: TaskDependency[];
  crews: Crew[];
  planning_locks: PlanningLock[];
};

export type TaskAssignment = {
  id: number;
  task_code: string;
  crew_code: string;
  start_day: number;
  end_day: number;
  lateness_days: number;
};

export type ScheduleRun = {
  id: number;
  project_id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  runtime_ms: number | null;
  objective_value: number | null;
  total_lateness_days: number | null;
  project_finish_day: number | null;
  assignments: TaskAssignment[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function listProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>("/api/projects");
}

export async function getPlanningData(projectId: number): Promise<PlanningData> {
  return request<PlanningData>(`/api/projects/${projectId}/planning-data`);
}

export async function getLatestScheduleRun(projectId: number): Promise<ScheduleRun | null> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/schedule-runs/latest`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`API zwróciło status ${response.status}`);
  }

  return response.json() as Promise<ScheduleRun>;
}

export async function createScheduleRun(projectId: number): Promise<ScheduleRun> {
  return request<ScheduleRun>(`/api/projects/${projectId}/schedule-runs`, {
    method: "POST",
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API zwróciło status ${response.status}`);
  }

  return response.json() as Promise<T>;
}
