import type { LearnerNext, ProblemDetail, SubmissionView } from "../api/client";

export const problem: ProblemDetail = {
  slug: "lower-bound",
  title: "Lower bound",
  version: "v1",
  statement: "# Lower bound\n\nReturn the first index.",
  interface: "int f();",
  starter_code: "int f() {\n}\n",
  sample_tests: [{ input: "L 1 1 1", expected_output: "0", description: "Sample." }],
};

export const supported: SubmissionView = {
  id: "s1",
  problem_slug: "lower-bound",
  status: "completed",
  created_at: "2026-10-15T05:00:00Z",
  compile: { ok: true, diagnostics: "" },
  tests: [
    {
      number: 1,
      visibility: "sample",
      description: "The target appears once.",
      verdict: "passed",
      input: "L 4 1 3 5 7 5",
      expected_output: "2",
      actual_output: "2\n",
    },
    {
      number: 2,
      visibility: "hidden",
      description: "The target is larger than every element.",
      verdict: "wrong_output",
      input: null,
      expected_output: null,
      actual_output: null,
    },
  ],
  feedback: {
    kind: "recognised_pattern",
    message: "Your code fails a group of cases in a pattern.",
    hint: "Can your search ever return a.size()?",
    related_cases: ["The target is larger than every element."],
    safety_findings: [],
  },
};

export const compileError: SubmissionView = {
  id: "s2",
  problem_slug: "lower-bound",
  status: "completed",
  created_at: "2026-10-15T05:01:00Z",
  compile: { ok: false, diagnostics: "solution.cpp:3: error: expected ';'" },
  tests: [],
  feedback: {
    kind: "compile_error",
    message: "Your code did not compile.",
    related_cases: [],
    safety_findings: [],
  },
};

export const next: LearnerNext = {
  recommendation: {
    action: "new_problem",
    problem_slug: "count-occurrences",
    problem_title: "Count occurrences",
    message: "Your last attempt behaved as if it had the specific error described in its feedback.",
    focus: ["Choosing the comparison so equal elements land on the correct side of the boundary."],
    based_on_submission_id: "s1",
    created_at: "2026-10-15T05:02:00Z",
  },
  last_followup: {
    verdict: "criterion_met",
    problem_slug: "lower-bound",
    problem_title: "Lower bound",
    message: "On Lower bound, your follow-up passed all 7 tests related to the recommended focus.",
    submission_id: "s0",
    created_at: "2026-10-15T05:00:00Z",
  },
};
