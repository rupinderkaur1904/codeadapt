import type { SubmissionView } from "../api/client";

export function summarise(view: SubmissionView): string {
  if (view.status !== "completed") return view.status === "failed" ? "System error" : "Pending";
  if (view.compile && !view.compile.ok) return "Did not compile";
  const tests = view.tests ?? [];
  const passed = tests.filter((t) => t.verdict === "passed").length;
  return `${passed}/${tests.length} tests passed`;
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
            className={a.id === selectedId ? "link selected" : "link"}
            onClick={() => onSelect(a.id)}
          >
            {new Date(a.created_at).toLocaleTimeString()} · {summarise(a)}
          </button>
        </li>
      ))}
    </ol>
  );
}
