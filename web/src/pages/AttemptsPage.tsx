import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { summarise } from "../components/AttemptHistory";
import { ErrorMessage } from "../components/ErrorMessage";

/** The student's own recent attempts across every problem, newest first. */
export function AttemptsPage() {
  const attempts = useQuery({ queryKey: ["submissions", "all"], queryFn: api.listAllSubmissions });
  const problems = useQuery({ queryKey: ["problems"], queryFn: api.listProblems });
  if (attempts.isPending) return <p>Loading attempts…</p>;
  if (attempts.isError) return <ErrorMessage error={attempts.error} />;
  const titles = new Map((problems.data ?? []).map((p) => [p.slug, p.title]));
  return (
    <section>
      <h1>My attempts</h1>
      {attempts.data.length === 0 ? (
        <p className="muted">
          No attempts yet. <Link to="/problems">Pick a problem</Link> to start.
        </p>
      ) : (
        <>
          <p className="muted">Your {attempts.data.length} most recent attempts, newest first.</p>
          <table className="tests">
            <thead>
              <tr>
                <th>When</th>
                <th>Problem</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {attempts.data.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/practice/${a.problem_slug}?attempt=${encodeURIComponent(a.id)}`}>
                      {new Date(a.created_at).toLocaleString()}
                    </Link>
                  </td>
                  <td>{titles.get(a.problem_slug) ?? a.problem_slug}</td>
                  <td>{summarise(a)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
