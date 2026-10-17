import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { api, type ResearchFilters, type ResearchMetrics } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

const OUTCOMES = [
  "compile_error",
  "execution_error",
  "unreliable_evidence",
  "no_failure_observed",
  "unmodelled_behaviour",
  "ambiguous",
  "insufficient_evidence",
  "hypothesis_supported",
];
const DATA_CLASSES = ["real", "synthetic", "dev"];

function Counts({ title, counts }: { title: string; counts: Record<string, number> }) {
  const entries = Object.entries(counts);
  return (
    <div>
      <h3>{title}</h3>
      {entries.length === 0 ? (
        <p className="muted">None.</p>
      ) : (
        <ul className="counts">
          {entries.map(([k, v]) => (
            <li key={k}>
              {k}: <strong>{v}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function MetricsPanel({ metrics }: { metrics: ResearchMetrics }) {
  return (
    <section className="metrics" aria-label="Counts">
      <p>
        <strong>{metrics.submissions}</strong> submissions
        {metrics.data_class ? ` (data class: ${metrics.data_class})` : " (all data classes)"};{" "}
        <strong>{metrics.flagged_for_review}</strong> flagged for review. These are counts of stored
        outcomes; there is no ground truth here, so they say nothing about accuracy.
      </p>
      <div className="metrics-grid">
        <Counts title="Diagnosis outcomes" counts={metrics.outcomes} />
        <Counts title="Recommendations by rule" counts={metrics.recommendations_by_rule} />
        <Counts title="Follow-up verdicts" counts={metrics.followup_verdicts} />
      </div>
    </section>
  );
}

export function ResearchPage() {
  const [filters, setFilters] = useState<ResearchFilters>({});
  const problems = useQuery({ queryKey: ["problems"], queryFn: api.listProblems });
  const rows = useQuery({
    queryKey: ["research", "submissions", filters],
    queryFn: () => api.researchSubmissions(filters),
  });
  const metrics = useQuery({
    queryKey: ["research", "metrics", filters.data_class],
    queryFn: () => api.researchMetrics(filters.data_class),
  });

  const select = (key: keyof ResearchFilters, label: string, options: string[]) => (
    <label>
      {label}{" "}
      <select
        value={filters[key] ?? ""}
        onChange={(e) => setFilters({ ...filters, [key]: e.target.value || undefined })}
      >
        <option value="">all</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <section>
      <h1>Research</h1>
      <div className="filters">
        {select(
          "problem_slug",
          "Problem",
          (problems.data ?? []).map((p) => p.slug),
        )}
        {select("outcome", "Outcome", OUTCOMES)}
        {select("data_class", "Data class", DATA_CLASSES)}
      </div>
      {metrics.isError && <ErrorMessage error={metrics.error} />}
      {metrics.data && <MetricsPanel metrics={metrics.data} />}
      {rows.isError && <ErrorMessage error={rows.error} />}
      {rows.isPending && <p>Loading submissions…</p>}
      {rows.data && rows.data.length === 0 && <p className="muted">No submissions match.</p>}
      {rows.data && rows.data.length > 0 && (
        <table className="tests research">
          <thead>
            <tr>
              <th>When</th>
              <th>User</th>
              <th>Class</th>
              <th>Problem</th>
              <th>Outcome</th>
              <th>Model</th>
              <th>Next</th>
              <th>Follow-up</th>
            </tr>
          </thead>
          <tbody>
            {rows.data.map((r) => (
              <tr key={r.id}>
                <td>
                  <Link to={`/research/submissions/${r.id}`}>
                    {new Date(r.created_at).toLocaleString()}
                  </Link>
                </td>
                <td>
                  <Link to={`/research/learners/${encodeURIComponent(r.username)}`}>
                    {r.username}
                  </Link>
                </td>
                <td>{r.data_class}</td>
                <td>{r.problem_slug}</td>
                <td>{r.outcome ?? r.status}</td>
                <td>{r.selected_model ?? "—"}</td>
                <td>
                  {r.recommended_problem ?? "—"}
                  {r.review_flag && " (review)"}
                </td>
                <td>{r.followup_verdict ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
