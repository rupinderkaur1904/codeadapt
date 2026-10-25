import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import {
  RESEARCH_PAGE_SIZE,
  type LearnerModelView,
  type ResearchMetrics,
  type ResearchSubmissionRow,
  type TraceView,
} from "../api/client";
import { setDevRole } from "../devRole";
import { supported } from "../test/fixtures";
import { AttemptsPage } from "./AttemptsPage";
import { LearnerModelPage } from "./LearnerModelPage";
import { LearnersPage } from "./LearnersPage";
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

function observation(id: string, problem: string, value: "correct" | "incorrect") {
  return {
    skill: "equality_handling",
    value,
    basis: "every reliable test probing the skill passed",
    submission_id: id,
    problem_slug: problem,
    problem_version: `${problem}-v1`,
    created_at: "2026-10-15T05:00:00Z",
    test_keys: ["equal_first"],
    attempt_ordinal: 1,
  };
}

const learnerModel: LearnerModelView = {
  username: "synthetic-a",
  data_class: "synthetic",
  attempts: 3,
  estimate: {
    model: "bkt-standard",
    model_version: "1",
    parameter_set: "bkt-params-assumed-1",
    label: "estimated under assumed parameters",
    assumptions: ["no forgetting"],
    min_observations: 3,
    min_problems: 2,
    skills: [
      {
        skill: "equality_handling",
        state: "insufficient_data",
        p_known: null,
        counted: 1,
        distinct_problems: 1,
        observations: [
          {
            observation: observation("s1", "lower-bound", "incorrect"),
            counted: true,
            reason: null,
            p_known_after: 0.146,
          },
          {
            observation: observation("s2", "lower-bound", "correct"),
            counted: false,
            reason: "retry: not the first reliably evaluated attempt on this problem version",
            p_known_after: null,
          },
        ],
      },
    ],
  },
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
      if (url.endsWith("/submissions?limit=50"))
        return json([supported, { ...supported, id: "s9", problem_slug: "lower-bound" }]);
      if (url.includes("/research/metrics")) return json(metrics);
      if (url.includes("/research/learner-model?username=synthetic-a")) return json(learnerModel);
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

  it("shows learner-model estimates with their label and uncounted retries", async () => {
    renderAt(
      "/research/learners/synthetic-a",
      <LearnerModelPage />,
      "/research/learners/:username",
    );
    expect(await screen.findByText(/Insufficient data/)).toBeInTheDocument();
    expect(screen.getAllByText(/estimated under assumed parameters/).length).toBeGreaterThan(0);
    expect(screen.getByText("0.146")).toBeInTheDocument();
    expect(screen.getByText(/no \(retry/)).toBeInTheDocument();
    expect(screen.queryByText(/master/i)).toBeNull();
  });

  it("marks problems with an attempt that had no failing tests", async () => {
    setDevRole("student");
    renderAt("/", <ProblemListPage />, "/");
    expect(await screen.findByText(/all tests passed/)).toBeInTheDocument();
    expect(screen.getAllByText(/all tests passed/)).toHaveLength(1);
  });

  it("shows outcomes per problem on the overview", async () => {
    renderAt("/research", <ResearchPage />, "/research");
    expect(await screen.findByRole("heading", { name: "Outcomes by problem" })).toBeInTheDocument();
  });

  it("starts the submission filters from the URL", async () => {
    renderAt("/research?outcome=ambiguous", <ResearchPage />, "/research");
    expect(await screen.findByText("synthetic-a")).toBeInTheDocument();
    expect(requests.some((r) => r.url.includes("outcome=ambiguous"))).toBe(true);
  });

  it("lists learners seen in submissions, linked to their learner model", async () => {
    renderAt("/research/learners", <LearnersPage />, "/research/learners");
    const link = await screen.findByRole("link", { name: "synthetic-a" });
    expect(link).toHaveAttribute("href", "/research/learners/synthetic-a");
    expect(requests.some((r) => r.url.includes("/research/submissions?limit=200"))).toBe(true);
    expect(screen.getByText(/activity, not learning/)).toBeInTheDocument();
  });

  it("shows a student's attempts across problems with links back to each attempt", async () => {
    setDevRole("student");
    renderAt("/attempts", <AttemptsPage />, "/attempts");
    const links = await screen.findAllByRole("link", { name: /\d/ });
    expect(links[0]).toHaveAttribute("href", "/practice/lower-bound?attempt=s1");
    expect(screen.getAllByText("1/2 tests passed")).toHaveLength(2);
  });

  it("shows each problem's status and attempt count", async () => {
    setDevRole("student");
    renderAt("/problems", <ProblemListPage />, "/problems");
    expect(await screen.findByText(/2 attempts/)).toBeInTheDocument();
    expect(screen.getByText("Not started")).toBeInTheDocument();
  });

  it("labels exactly the eight provisional problems as unreviewed", async () => {
    setDevRole("student");
    const provisional = [
      "integer-sqrt",
      "min-capacity",
      "upper-bound",
      "exact-search",
      "last-occurrence",
      "rotated-min",
      "rotated-search",
      "peak-index",
    ];
    const others = [
      "lower-bound",
      "count-occurrences",
      "last-less-than",
      "first-true",
      "first-max-index",
      "second-largest",
      "stock-profit",
      "longest-run",
      "plus-one",
      "closest-pair-sum",
      "container-water",
      "dedup-sorted",
      "max-window-sum",
      "longest-sum-at-most",
      "distinct-in-windows",
      "pivot-index",
      "range-sum-queries",
    ];
    const bank = [...provisional, ...others].map((slug) => ({
      slug,
      title: `Title ${slug}`,
      family: "binary-search",
      no_failure_observed: false,
    }));
    vi.mocked(globalThis.fetch).mockImplementation(async (input) =>
      String(input).endsWith("/problems") ? json(bank) : json([]),
    );
    renderAt("/problems", <ProblemListPage />, "/problems");
    await screen.findByRole("link", { name: "Title lower-bound" });
    const labelled = screen
      .getAllByText("Unreviewed", { exact: true })
      .map((label) => label.closest("li")?.querySelector("a")?.textContent);
    expect(labelled.sort()).toEqual(provisional.map((s) => `Title ${s}`).sort());
    // The explanation is about review status, not about wrong solutions.
    expect(screen.getByText(/not yet reviewed by the project owner/)).toBeInTheDocument();
    expect(screen.queryByText(/incorrect|wrong/i)).toBeNull();
  });

  it("groups a larger bank by family, binary search first, and lists every problem", async () => {
    setDevRole("student");
    const families = ["prefix-sums", "arrays", "binary-search", "sliding-window", "two-pointers"];
    const bank = Array.from({ length: 25 }, (_, i) => ({
      slug: `p${i}`,
      title: `Problem ${i}`,
      family: families[i % families.length],
      no_failure_observed: false,
    }));
    vi.mocked(globalThis.fetch).mockImplementation(async (input) =>
      String(input).endsWith("/problems") ? json(bank) : json([]),
    );
    renderAt("/problems", <ProblemListPage />, "/problems");
    const headings = await screen.findAllByRole("heading", { level: 2 });
    expect(headings.map((h) => h.textContent)).toEqual([
      "Binary search · 5",
      "Arrays · 5",
      "Two pointers · 5",
      "Sliding window · 5",
      "Prefix sums · 5",
    ]);
    expect(screen.getAllByRole("link", { name: /^Problem \d+$/ })).toHaveLength(25);
  });
  it("pages through submissions and returns to the first page when a filter changes", async () => {
    const page = Array.from({ length: RESEARCH_PAGE_SIZE }, (_, i) => ({
      ...row,
      id: `p${i}`,
      username: `learner-${i}`,
    }));
    vi.mocked(globalThis.fetch).mockImplementation(async (input) => {
      const url = String(input);
      requests.push({ url, role: null });
      if (url.includes("/research/submissions?offset=100")) return json([row]);
      if (url.includes("/research/submissions")) return json(page);
      if (url.includes("/research/metrics")) return json(metrics);
      if (url.endsWith("/problems")) return json([]);
      throw new Error(`unexpected request ${url}`);
    });
    renderAt("/research", <ResearchPage />, "/research");
    expect(await screen.findByText("learner-0")).toBeInTheDocument();
    expect(screen.getByText(`Rows 1–${RESEARCH_PAGE_SIZE}`)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Newer" })).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "Older" }));
    expect(await screen.findByText("synthetic-a")).toBeInTheDocument();
    expect(
      screen.getByText(`Rows ${RESEARCH_PAGE_SIZE + 1}–${RESEARCH_PAGE_SIZE + 1}`),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Older" })).toBeDisabled();

    // A new filter starts again from the newest rows.
    await userEvent.selectOptions(screen.getByLabelText("Outcome"), "ambiguous");
    expect(await screen.findByText("learner-0")).toBeInTheDocument();
    const last = requests.filter((r) => r.url.includes("/research/submissions")).at(-1);
    expect(last?.url).toContain("outcome=ambiguous");
    expect(last?.url).not.toContain("offset=");
  });

  it("says when no submission matches", async () => {
    vi.mocked(globalThis.fetch).mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/research/submissions")) return json([]);
      if (url.includes("/research/metrics")) return json(metrics);
      if (url.endsWith("/problems")) return json([]);
      throw new Error(`unexpected request ${url}`);
    });
    renderAt("/research", <ResearchPage />, "/research");
    expect(await screen.findByText("No submissions match.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Older" })).toBeNull();
  });

  it("shows API errors on the trace and learner-model pages instead of a blank page", async () => {
    vi.mocked(globalThis.fetch).mockImplementation(async () =>
      json({ detail: "submission not found" }, 404),
    );
    renderAt("/research/submissions/nope", <TracePage />, "/research/submissions/:id");
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("shows an error, not an empty model, when the learner model is refused", async () => {
    vi.mocked(globalThis.fetch).mockImplementation(async () =>
      json({ detail: "researcher role required" }, 403),
    );
    renderAt("/research/learners/x", <LearnerModelPage />, "/research/learners/:username");
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.queryByText(/No skill observations yet/)).toBeNull();
  });
});
