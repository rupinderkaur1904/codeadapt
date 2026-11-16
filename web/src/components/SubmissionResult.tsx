import type { FeedbackView, SubmissionView, TestResultView } from "../api/client";

const VERDICT_LABEL: Record<TestResultView["verdict"], string> = {
  passed: "Passed",
  wrong_output: "Wrong output",
  runtime_error: "Runtime error",
  time_limit: "Time limit exceeded",
  memory_limit: "Memory limit exceeded",
  output_limit: "Output limit exceeded",
  undefined_behaviour: "Undefined behaviour",
  inconsistent: "Inconsistent between runs",
  not_evaluated: "Not evaluated",
};

const STATUS_LABEL: Record<SubmissionView["status"], string> = {
  queued: "Waiting to run…",
  running: "Running your code…",
  completed: "Finished",
  failed: "We could not evaluate this submission because of a problem on our side.",
};

/** A plain-words name for each feedback kind the API sends; the message itself is unchanged. */
const FEEDBACK_TITLE: Record<FeedbackView["kind"], string> = {
  compile_error: "Compilation error",
  system_error: "Evaluation problem",
  inconsistent_behaviour: "Unsafe or inconsistent behaviour",
  all_tests_passed: "All tests passed",
  recognised_pattern: "Diagnosis",
  failing_cases: "Failing cases",
};

type Tone = "pass" | "fail" | "warn" | "neutral";

function verdictTone(verdict: TestResultView["verdict"]): Tone {
  if (verdict === "passed") return "pass";
  if (verdict === "not_evaluated") return "neutral";
  if (verdict === "undefined_behaviour" || verdict === "inconsistent") return "warn";
  return "fail";
}

function feedbackTone(kind: FeedbackView["kind"]): Tone {
  if (kind === "all_tests_passed") return "pass";
  if (kind === "compile_error" || kind === "system_error") return "fail";
  return "warn";
}

export function SubmissionResult({ submission }: { submission: SubmissionView }) {
  if (submission.status !== "completed") {
    return (
      <section className="result" aria-live="polite">
        <p
          className={`run-status run-status-${submission.status} ${
            submission.status === "failed" ? "error" : "muted"
          }`}
        >
          <span className="status-dot" aria-hidden="true" />
          {STATUS_LABEL[submission.status]}
        </p>
      </section>
    );
  }
  const tests = submission.tests ?? [];
  const passed = tests.filter((t) => t.verdict === "passed").length;
  const total = tests.length;
  const compileFailed = submission.compile != null && !submission.compile.ok;
  const tone: Tone = compileFailed
    ? "fail"
    : submission.feedback?.kind === "inconsistent_behaviour"
      ? "warn"
      : total > 0 && passed === total
        ? "pass"
        : total > 0
          ? "fail"
          : "neutral";
  return (
    <section className="result" aria-live="polite">
      {(compileFailed || total > 0) && (
        <div className={`result-summary tone-${tone}`}>
          <p className="result-headline">
            {compileFailed ? "Did not compile" : `Tests: ${passed} of ${total} passed`}
          </p>
          <p className="result-meta muted">
            Submitted {new Date(submission.created_at).toLocaleString()}
          </p>
          {!compileFailed && (
            <div className="pass-bar" aria-hidden="true">
              <span style={{ width: `${(passed / total) * 100}%` }} />
            </div>
          )}
        </div>
      )}
      {submission.feedback && <Feedback feedback={submission.feedback} />}
      {compileFailed && (
        <div className="output-block">
          <h3>Compiler output</h3>
          <pre className="compiler-output">{submission.compile?.diagnostics}</pre>
        </div>
      )}
      {total > 0 && (
        <div className="output-block">
          <h3>Test cases</h3>
          <div className="table-scroll">
            <table className="tests">
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Case</th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((t) => (
                  <TestRow key={t.number} test={t} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

function Feedback({ feedback }: { feedback: FeedbackView }) {
  return (
    <div
      className={`feedback feedback-${feedback.kind} tone-${feedbackTone(feedback.kind)}`}
      data-testid="feedback"
    >
      <p className="feedback-title">{FEEDBACK_TITLE[feedback.kind]}</p>
      <p className="feedback-message">{feedback.message}</p>
      {feedback.safety_findings && feedback.safety_findings.length > 0 && (
        <ul className="safety" aria-label="Safety problems">
          {feedback.safety_findings.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}
      {feedback.hint && (
        <p className="hint">
          <strong>Hint:</strong> {feedback.hint}
        </p>
      )}
      {feedback.related_cases && feedback.related_cases.length > 0 && (
        <div className="related-cases">
          <p>Cases that show it:</p>
          <ul>
            {feedback.related_cases.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function TestRow({ test }: { test: TestResultView }) {
  const tone = verdictTone(test.verdict);
  return (
    <tr className={test.verdict === "passed" ? "pass" : "fail"}>
      <td className="test-number">{test.number}</td>
      <td>
        <span className="test-description">{test.description}</span>
        {test.visibility === "sample" ? (
          <span className="visibility-tag">Sample</span>
        ) : (
          <span className="visibility-tag hidden-tag">Hidden</span>
        )}
        {test.visibility === "sample" && (
          <dl className="sample io-grid">
            <dt>Input</dt>
            <dd>
              <code>{test.input}</code>
            </dd>
            <dt>Expected</dt>
            <dd>
              <code>{test.expected_output}</code>
            </dd>
            <dt>Your output</dt>
            <dd className={test.verdict === "passed" ? undefined : "mismatch"}>
              <code>{test.actual_output?.trim() || "(none)"}</code>
            </dd>
          </dl>
        )}
      </td>
      <td>
        <span className={`verdict tone-${tone}`}>{VERDICT_LABEL[test.verdict]}</span>
      </td>
    </tr>
  );
}
