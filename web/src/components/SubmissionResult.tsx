import type { FeedbackView, SubmissionView, TestResultView } from "../api/client";

const VERDICT_LABEL: Record<TestResultView["verdict"], string> = {
  passed: "Passed",
  wrong_output: "Wrong output",
  runtime_error: "Runtime error",
  time_limit: "Time limit exceeded",
  memory_limit: "Memory limit exceeded",
  output_limit: "Output limit exceeded",
  not_evaluated: "Not evaluated",
};

const STATUS_LABEL: Record<SubmissionView["status"], string> = {
  queued: "Waiting to run…",
  running: "Running your code…",
  completed: "Finished",
  failed: "We could not evaluate this submission because of a problem on our side.",
};

export function SubmissionResult({ submission }: { submission: SubmissionView }) {
  if (submission.status !== "completed") {
    return (
      <section className="result" aria-live="polite">
        <p className={submission.status === "failed" ? "error" : "muted"}>
          {STATUS_LABEL[submission.status]}
        </p>
      </section>
    );
  }
  const passed = submission.tests?.filter((t) => t.verdict === "passed").length ?? 0;
  const total = submission.tests?.length ?? 0;
  return (
    <section className="result" aria-live="polite">
      {submission.feedback && <Feedback feedback={submission.feedback} />}
      {submission.compile && !submission.compile.ok && (
        <>
          <h3>Compiler output</h3>
          <pre className="compiler-output">{submission.compile.diagnostics}</pre>
        </>
      )}
      {total > 0 && (
        <>
          <h3>
            Tests: {passed} of {total} passed
          </h3>
          <table className="tests">
            <thead>
              <tr>
                <th>#</th>
                <th>Case</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {submission.tests?.map((t) => (
                <TestRow key={t.number} test={t} />
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}

function Feedback({ feedback }: { feedback: FeedbackView }) {
  return (
    <div className={`feedback feedback-${feedback.kind}`} data-testid="feedback">
      <p>{feedback.message}</p>
      {feedback.hint && (
        <p className="hint">
          <strong>Hint:</strong> {feedback.hint}
        </p>
      )}
      {feedback.related_cases && feedback.related_cases.length > 0 && (
        <>
          <p>Cases that show it:</p>
          <ul>
            {feedback.related_cases.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function TestRow({ test }: { test: TestResultView }) {
  return (
    <tr className={test.verdict === "passed" ? "pass" : "fail"}>
      <td>{test.number}</td>
      <td>
        {test.description}
        {test.visibility === "sample" && (
          <dl className="sample">
            <dt>Input</dt>
            <dd>
              <code>{test.input}</code>
            </dd>
            <dt>Expected</dt>
            <dd>
              <code>{test.expected_output}</code>
            </dd>
            <dt>Your output</dt>
            <dd>
              <code>{test.actual_output?.trim() || "(none)"}</code>
            </dd>
          </dl>
        )}
      </td>
      <td>{VERDICT_LABEL[test.verdict]}</td>
    </tr>
  );
}
