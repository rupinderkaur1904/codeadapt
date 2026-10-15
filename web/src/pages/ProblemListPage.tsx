import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

export function ProblemListPage() {
  const problems = useQuery({ queryKey: ["problems"], queryFn: api.listProblems });
  if (problems.isPending) return <p>Loading problems…</p>;
  if (problems.isError) return <ErrorMessage error={problems.error} />;
  return (
    <section>
      <h1>Problems</h1>
      <ul className="problem-list">
        {problems.data.map((p) => (
          <li key={p.slug}>
            <Link to={`/practice/${p.slug}`}>{p.title}</Link>
            <span className="muted"> · {p.family}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
