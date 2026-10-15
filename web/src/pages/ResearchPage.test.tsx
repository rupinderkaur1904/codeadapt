import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import type { ResearchMetrics, ResearchSubmissionRow, TraceView } from "../api/client";
import { setDevRole } from "../devRole";
import { ProblemListPage } from "./ProblemListPage";
import { ResearchPage } from "./ResearchPage";
import { TracePage } from "./TracePage";

const row: ResearchSubmissionRow = {
  id: "s1",
  created_at: "2026-10-15T05:00:00Z",
  username: "synthetic-a",
  data_class: "synthetic",
  origin: "synthetic",
  problem_slug: "lower-bound",
  status: "completed",
  outcome: "hypothesis_supported",
  selected_model: "upper_bound_confusion",
  support: 4,
  recommendation_rule: "hypothesis_supported",
  recommended_problem: "count-occurrences",
  review_flag: false,
  followup_verdict: null,
};

const metrics: ResearchMetrics = {
  data_class: null,
  submissions: 1,
  outcomes: { hypothesis_supported: 1 },
  outcomes_by_problem: { "lower-bound": { hypothesis_supported: 1 } },
  recommendations_by_rule: { hypothesis_supported: 1 },
  flagged_for_review: 0,
  followup_verdicts: {},
};

const trace: TraceView = {
  submission: { id: "s1", user_id: 3, data_class: "synthetic", origin: "synthetic" },
  job: { state: "done" },
  environment: { compiler_version: "g++ 14.2.0" },
  execution_runs: [{ id: 7, profile: "standard" }],
  observations: [
    {
      id: 1,
      run_id: 7,
      test_key: "equal_first",
      repeat_index: 0,
      signature_kind: "output",
      signature_detail: "1",
      excluded_reason: null,
      wall_ms: 310,
    },
  ],
  diagnosis: {
    method: "fingerprint_consistency",
    outcome: "hypothesis_supported",
    selected_model: "upper_bound_confusion",
    rationale: { rule: 8, supporting_tests: ["equal_first"] },
  },
  content_validation: { errors: [], warnings: [] },
  recommendation: { rule: "hypothesis_supported", problem_slug: "count-occurrences" },
  followup_evaluation: null,
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderAt(path: string, element: ReactNode, route: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={route} element={element} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("researcher pages", () => {
  const requests: { url: string; role: string | null }[] = [];
  beforeEach(() => {
    requests.length = 0;
    window.localStorage.clear();
    setDevRole("researcher");
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      requests.push({ url, role: new Headers(init?.headers).get("X-Dev-Role") });
      if (url.includes("/research/submissions/s1/trace")) return json(trace);
      if (url.includes("/research/submissions")) return json([row]);
      if (url.includes("/research/metrics")) return json(metrics);
      if (url.endsWith("/problems"))
        return json([
          {
            slug: "lower-bound",
            title: "Lower bound",
            family: "binary-search",
            no_failure_observed: true,
          },
          {
            slug: "last-less-than",
            title: "Last less than",
            family: "binary-search",
            no_failure_observed: false,
          },
        ]);
      throw new Error(`unexpected request ${url}`);
    });
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("lists submissions with counts and applies filters", async () => {
    renderAt("/research", <ResearchPage />, "/research");
    expect(await screen.findByText("synthetic-a")).toBeInTheDocument();
    expect(screen.getByText(/no ground truth here/)).toBeInTheDocument();
    expect(requests.every((r) => r.role === "researcher")).toBe(true);

    await userEvent.selectOptions(screen.getByLabelText("Outcome"), "ambiguous");
    await userEvent.selectOptions(screen.getByLabelText("Data class"), "synthetic");
    expect(
      requests.some(
        (r) =>
          r.url.includes("/research/submissions?") &&
          r.url.includes("outcome=ambiguous") &&
          r.url.includes("data_class=synthetic"),
      ),
    ).toBe(true);
    expect(requests.some((r) => r.url.endsWith("/research/metrics?data_class=synthetic"))).toBe(
      true,
    );
  });

  it("shows the evidence chain for one submission", async () => {
    renderAt("/research/submissions/s1", <TracePage />, "/research/submissions/:id");
    expect(await screen.findByText("equal_first")).toBeInTheDocument();
    expect(screen.getByText("output: 1")).toBeInTheDocument();
    expect(screen.getAllByText("upper_bound_confusion").length).toBeGreaterThan(0);
    expect(screen.getByText("count-occurrences")).toBeInTheDocument();
  });

  it("marks problems with an attempt that had no failing tests", async () => {
    setDevRole("student");
    renderAt("/", <ProblemListPage />, "/");
    expect(await screen.findByText(/all tests passed/)).toBeInTheDocument();
    expect(screen.getAllByText(/all tests passed/)).toHaveLength(1);
  });
});
