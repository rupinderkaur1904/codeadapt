import type { SubmissionView } from "../api/client";

export function summarise(view: SubmissionView): string {
  if (view.status !== "completed") return view.status === "failed" ? "System error" : "Pending";
  if (view.compile && !view.compile.ok) return "Did not compile";
  const tests = view.tests ?? [];
  const passed = tests.filter((t) => t.verdict === "passed").length;
  return `${passed}/${tests.length} tests passed`;
}

function tone(view: SubmissionView): string {
  if (view.status !== "completed") return view.status === "failed" ? "fail" : "neutral";
  if (view.compile && !view.compile.ok) return "fail";
  const tests = view.tests ?? [];
  return tests.length > 0 && tests.every((t) => t.verdict === "passed") ? "pass" : "fail";
}

export function AttemptHistory({
  attempts,
  selectedId,
  onSelect,
}: {
  attempts: SubmissionView[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  if (attempts.length === 0) return <p className="muted">No attempts yet.</p>;
  return (
    <ol className="history" reversed>
      {attempts.map((a) => (
        <li key={a.id}>
          <button
            type="button"
            className={a.id === selectedId ? "attempt selected" : "attempt"}
            aria-current={a.id === selectedId ? "true" : undefined}
            onClick={() => onSelect(a.id)}
          >
            <span className={`attempt-dot tone-${tone(a)}`} aria-hidden="true" />
            <span className="attempt-time">{new Date(a.created_at).toLocaleTimeString()}</span>
            <span className="attempt-sep" aria-hidden="true">
              ·
            </span>
            <span className="attempt-summary">{summarise(a)}</span>
          </button>
        </li>
      ))}
    </ol>
  );
}
