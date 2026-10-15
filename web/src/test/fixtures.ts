import type { ProblemDetail, SubmissionView } from "../api/client";

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
