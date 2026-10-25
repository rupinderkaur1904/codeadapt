import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api, type ProblemSummary, type SubmissionView } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";
import { RecommendationCard } from "../components/RecommendationCard";

const RECENT_LIMIT = 50;
// The eight binary-search problems added on 2026-10-24 that the owner keeps provisionally until
// their review (decision 2026-10-25 07:50). The label is about review status only: the problems
// work and their reference solutions pass every test.
const UNREVIEWED = new Set([
  "integer-sqrt",
  "min-capacity",
  "upper-bound",
  "exact-search",
  "last-occurrence",
  "rotated-min",
  "rotated-search",
  "peak-index",
]);
const UNREVIEWED_NOTE =
  "Added for the research prototype and not yet reviewed by the project owner. The problem " +
  "works and can be practised; its tests and hints have not been accepted for research use.";
// Families in teaching order; a family not listed here follows them in the order the API sends.
const FAMILY_ORDER = ["binary-search", "arrays", "two-pointers", "sliding-window", "prefix-sums"];

function familyLabel(family: string): string {
  const words = family.replace(/-/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function byFamily(problems: ProblemSummary[]): [string, ProblemSummary[]][] {
  const groups = new Map<string, ProblemSummary[]>();
  for (const p of problems) groups.set(p.family, [...(groups.get(p.family) ?? []), p]);
  const rank = (f: string) => {
    const i = FAMILY_ORDER.indexOf(f);
    return i === -1 ? FAMILY_ORDER.length : i;
  };
  return [...groups].sort(([a], [b]) => rank(a) - rank(b));
}

function status(p: ProblemSummary, attempts: number | undefined) {
  if (p.no_failure_observed) {
    return (
      <span className="status status-pass" title="You have an attempt with no failing tests">
        ✓ all tests passed
      </span>
    );
  }
  if (attempts === undefined) return null;
  if (attempts === 0) return <span className="status">Not started</span>;
  return <span className="status status-tried">In progress</span>;
}

function countAttempts(recent: SubmissionView[] | undefined): Map<string, number> | undefined {
  if (!recent) return undefined;
  const counts = new Map<string, number>();
  for (const s of recent) counts.set(s.problem_slug, (counts.get(s.problem_slug) ?? 0) + 1);
  return counts;
}

export function ProblemListPage() {
  const problems = useQuery({ queryKey: ["problems"], queryFn: api.listProblems });
  // Attempt counts come from the most recent submissions; with more than the API's cap,
  // older attempts are not counted and the count reads "50+".
  const recent = useQuery({ queryKey: ["submissions", "all"], queryFn: api.listAllSubmissions });
  if (problems.isPending) return <p>Loading problems…</p>;
  if (problems.isError) return <ErrorMessage error={problems.error} />;
  const counts = countAttempts(recent.data);
  const capped = (recent.data?.length ?? 0) >= RECENT_LIMIT;
  return (
    <section>
      <h1>Problems</h1>
      <RecommendationCard />
      {byFamily(problems.data).map(([family, list]) => (
        <section key={family} aria-labelledby={`family-${family}`}>
          <h2 id={`family-${family}`} className="family-heading">
            {familyLabel(family)} <span className="muted">· {list.length}</span>
          </h2>
          <ul className="problem-list">
            {list.map((p) => {
              const attempts = counts ? (counts.get(p.slug) ?? 0) : undefined;
              return (
                <li key={p.slug}>
                  <Link to={`/practice/${p.slug}`}>{p.title}</Link>
                  {UNREVIEWED.has(p.slug) && (
                    <span className="status status-unreviewed" title={UNREVIEWED_NOTE}>
                      Unreviewed
                    </span>
                  )}
                  <p className="problem-meta">
                    {status(p, attempts)}
                    {attempts !== undefined && attempts > 0 && (
                      <span className="muted">
                        {" "}
                        · {attempts}
                        {capped ? "+" : ""} attempt{attempts === 1 && !capped ? "" : "s"}
                      </span>
                    )}
                  </p>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
      {problems.data.some((p) => UNREVIEWED.has(p.slug)) && (
        <p className="muted unreviewed-note">Unreviewed: {UNREVIEWED_NOTE}</p>
      )}
    </section>
  );
}
