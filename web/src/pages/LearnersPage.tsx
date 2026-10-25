import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api, type ResearchSubmissionRow } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

const WINDOW = 200; // the API's largest page

interface Learner {
  username: string;
  dataClasses: Set<string>;
  submissions: number;
  problems: Set<string>;
  latest: string;
}

function group(rows: ResearchSubmissionRow[]): Learner[] {
  const byName = new Map<string, Learner>();
  for (const r of rows) {
    const l = byName.get(r.username) ?? {
      username: r.username,
      dataClasses: new Set<string>(),
      submissions: 0,
      problems: new Set<string>(),
      latest: r.created_at,
    };
    l.dataClasses.add(r.data_class);
    l.submissions += 1;
    l.problems.add(r.problem_slug);
    if (r.created_at > l.latest) l.latest = r.created_at;
    byName.set(r.username, l);
  }
  return [...byName.values()].sort((a, b) => b.latest.localeCompare(a.latest));
}

/** Researcher-only: learners seen in recent submissions, linked to their learner model. */
export function LearnersPage() {
  const rows = useQuery({
    queryKey: ["research", "submissions", "learners"],
    queryFn: () => api.researchSubmissions({}, 0, WINDOW),
  });
  if (rows.isPending) return <p>Loading learners…</p>;
  if (rows.isError) return <ErrorMessage error={rows.error} />;
  const learners = group(rows.data);
  return (
    <section>
      <p>
        <Link to="/research">Back to research</Link>
      </p>
      <h1>Learners</h1>
      <p className="muted">
        Built from the {rows.data.length} most recent submissions (at most {WINDOW}). Accounts with
        no submissions in that window are not listed. Counts here are activity, not learning.
      </p>
      {learners.length === 0 ? (
        <p className="muted">No submissions yet.</p>
      ) : (
        <table className="tests">
          <thead>
            <tr>
              <th>Learner</th>
              <th>Data class</th>
              <th>Submissions</th>
              <th>Problems tried</th>
              <th>Latest</th>
            </tr>
          </thead>
          <tbody>
            {learners.map((l) => (
              <tr key={l.username}>
                <td>
                  <Link to={`/research/learners/${encodeURIComponent(l.username)}`}>
                    {l.username}
                  </Link>
                </td>
                <td>{[...l.dataClasses].join(", ")}</td>
                <td>{l.submissions}</td>
                <td>{l.problems.size}</td>
                <td>{new Date(l.latest).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
