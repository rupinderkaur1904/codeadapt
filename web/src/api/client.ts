/** Thin typed client over the CodeAdapt HTTP API. Types come from the generated OpenAPI schema. */
import { getDevRole } from "../devRole";
import type { components } from "./schema";

export type ProblemSummary = components["schemas"]["ProblemSummary"];
export type ProblemDetail = components["schemas"]["ProblemDetail"];
export type SubmissionView = components["schemas"]["SubmissionView"];
export type SubmissionAccepted = components["schemas"]["SubmissionAccepted"];
export type TestResultView = components["schemas"]["TestResultView"];
export type FeedbackView = components["schemas"]["FeedbackView"];
export type LearnerNext = components["schemas"]["LearnerNext"];
export type ResearchSubmissionRow = components["schemas"]["ResearchSubmissionRow"];
export type ResearchMetrics = components["schemas"]["ResearchMetrics"];
export type TraceView = components["schemas"]["TraceView"];

export interface ResearchFilters {
  problem_slug?: string;
  outcome?: string;
  data_class?: string;
}

function query(params: object): string {
  const entries = Object.entries(params).filter(
    (e): e is [string, string] => typeof e[1] === "string" && e[1] !== "",
  );
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : "";
}

/** RFC 9457 problem details returned by the API for every error. */
export class ApiError extends Error {
  readonly status: number;
  readonly type: string;
  readonly detail?: string;

  constructor(status: number, type: string, title: string, detail?: string) {
    super(detail ? `${title}: ${detail}` : title);
    this.status = status;
    this.type = type;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "X-Dev-Role": getDevRole(),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let body: { type?: string; title?: string; detail?: string } = {};
    try {
      body = (await response.json()) as typeof body;
    } catch {
      // Non-JSON error (e.g. proxy failure): fall back to the status text.
    }
    throw new ApiError(
      response.status,
      body.type ?? "about:blank",
      body.title ?? response.statusText,
      body.detail,
    );
  }
  return (await response.json()) as T;
}

export const api = {
  listProblems: () => request<ProblemSummary[]>("/problems"),
  getProblem: (slug: string) => request<ProblemDetail>(`/problems/${encodeURIComponent(slug)}`),
  submit: (problemSlug: string, source: string) =>
    request<SubmissionAccepted>("/submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_slug: problemSlug, source }),
    }),
  getSubmission: (id: string) => request<SubmissionView>(`/submissions/${encodeURIComponent(id)}`),
  listSubmissions: (problemSlug: string) =>
    request<SubmissionView[]>(`/submissions?problem_slug=${encodeURIComponent(problemSlug)}`),
  myRecommendation: () => request<LearnerNext>("/me/recommendation"),
  researchSubmissions: (filters: ResearchFilters) =>
    request<ResearchSubmissionRow[]>(`/research/submissions${query(filters)}`),
  researchMetrics: (dataClass?: string) =>
    request<ResearchMetrics>(`/research/metrics${query({ data_class: dataClass })}`),
  trace: (id: string) =>
    request<TraceView>(`/research/submissions/${encodeURIComponent(id)}/trace`),
};

export function isFinished(view: Pick<SubmissionView, "status">): boolean {
  return view.status === "completed" || view.status === "failed";
}
