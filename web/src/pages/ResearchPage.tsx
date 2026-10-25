import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api, RESEARCH_PAGE_SIZE, type ResearchFilters, type ResearchMetrics } from "../api/client";
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
  "non_termination_observed",
];
const DATA_CLASSES = ["real", "synthetic", "dev"];

function OutcomesByProblem({ table }: { table: ResearchMetrics["outcomes_by_problem"] }) {
  const problems = Object.keys(table);
  if (problems.length === 0) return null;
  const outcomes = OUTCOMES.filter((o) => problems.some((p) => table[p]?.[o]));
  return (
    <div className="table-scroll">
      <h3>Outcomes by problem</h3>
      <table className="tests research-matrix">
        <thead>
          <tr>
            <th>Problem</th>
            {outcomes.map((o) => (
              <th key={o}>{o}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {problems.map((p) => (
            <tr key={p}>
              <td>{p}</td>
              {outcomes.map((o) => (
                <td key={o}>{table[p]?.[o] ?? 0}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

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
      <OutcomesByProblem table={metrics.outcomes_by_problem} />
    </section>
  );
}

export function ResearchPage() {
  // Filters start from the URL, so other pages can link to a filtered list.
  const [params] = useSearchParams();
  const [filters, setFiltersState] = useState<ResearchFilters>(() => ({
    problem_slug: params.get("problem_slug") ?? undefined,
    outcome: params.get("outcome") ?? undefined,
    data_class: params.get("data_class") ?? undefined,
  }));
  const [offset, setOffset] = useState(0);
  const [reviewOnly, setReviewOnly] = useState(false);
  const setFilters = (next: ResearchFilters) => {
    setFiltersState(next);
    setOffset(0);
  };
  const problems = useQuery({ queryKey: ["problems"], queryFn: api.listProblems });
  const rows = useQuery({
    queryKey: ["research", "submissions", filters, offset],
    queryFn: () => api.researchSubmissions(filters, offset),
  });
  const shown = rows.data?.filter((r) => !reviewOnly || r.review_flag);
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
        <label>
          <input
            type="checkbox"
            checked={reviewOnly}
            onChange={(e) => setReviewOnly(e.target.checked)}
          />{" "}
          Flagged for review only (this page)
        </label>
      </div>
      {metrics.isError && <ErrorMessage error={metrics.error} />}
      {metrics.data && <MetricsPanel metrics={metrics.data} />}
      <h2>Submissions</h2>
      {rows.isError && <ErrorMessage error={rows.error} />}
      {rows.isPending && <p>Loading submissions…</p>}
      {shown && shown.length === 0 && <p className="muted">No submissions match.</p>}
      {shown && shown.length > 0 && (
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
            {shown.map((r) => (
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
      {rows.data && (offset > 0 || rows.data.length === RESEARCH_PAGE_SIZE) && (
        <div className="actions">
          <button
            type="button"
            className="secondary"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - RESEARCH_PAGE_SIZE))}
          >
            Newer
          </button>
          <span className="muted">
            Rows {offset + 1}–{offset + rows.data.length}
          </span>
          <button
            type="button"
            className="secondary"
            disabled={rows.data.length < RESEARCH_PAGE_SIZE}
            onClick={() => setOffset(offset + RESEARCH_PAGE_SIZE)}
          >
            Older
          </button>
        </div>
      )}
    </section>
  );
}
